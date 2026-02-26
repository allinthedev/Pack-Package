import os
import random
import json
import tomllib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import format_dt

from ballsdex.core.models import Ball, BallInstance, Player
from ballsdex.core.pack_models import PackResource
from ballsdex.core.currency_models import Item as ItemModel, MoneyInstance
from ballsdex.packages.admin.cog import FieldPageSource, Pages
from ballsdex.settings import settings

from .item_types import Item, ItemType
from .transformers import ItemTransform

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

class PackageSettings:
    """
    Settings for the Pack package.
    """
    def __init__(self, path):
        with open(path, "rb") as f:
            data = tomllib.load(f)
        
        if data is None:
            return

        daily = data.get("daily", {})
        weekly = data.get("weekly", {})
        
        self.min_rarity_daily: float | None = daily.get("min_rarity_daily", None)
        self.max_rarity_daily: float | None = daily.get("max_rarity_daily", None)

        self.min_rarity_weekly: float | None = weekly.get("min_rarity_weekly", None)
        self.max_rarity_weekly: float | None = weekly.get("max_rarity_weekly", None)

pack_settings = PackageSettings(Path(os.path.dirname(os.path.abspath(__file__)), "./config.toml"))

def load_rarity_json(path: Path) -> list[Item]:
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)["rarities"]
        except KeyError:
            raise ValueError("Invalid rarity JSON format: 'rarities' key not found.")
    return data

items = load_rarity_json(Path(os.path.dirname(os.path.abspath(__file__)), "./items.json"))

class Pack(commands.GroupCog):
    """
    Claim a daily/weekly pack!
    """
    
    def __init__(self, bot: "BallsDexBot") -> None:
        self.bot = bot

    @app_commands.command(name="daily")
    async def daily(self, interaction: discord.Interaction["BallsDexBot"]):
        """
        Claim your daily pack! (3 uses)
        """
        player, _ = await Player.get_or_create(discord_id=interaction.user.id)
        resource, _ = await PackResource.get_or_create(player=player)
        if await resource.is_daily_on_cooldown():
            await interaction.response.send_message(
                f"You've used all daily packs. "
                f"Come back {format_dt(resource.daily_cooldown + timedelta(days=1), style='R')}!", # type: ignore
                ephemeral=True
            )
            return
        if not pack_settings.min_rarity_daily or not pack_settings.max_rarity_daily:
            await interaction.response.send_message(
                "Daily packs are not configured. Contact support if this persists.",
                ephemeral=True
            )
            return

        if resource.daily_cooldown is not None:
            await resource.remove_daily_cooldown()
        resource.uses += 1
        await resource.save(update_fields=("uses",))
        if resource.uses >= 3:
            await resource.set_daily_cooldown()
        await interaction.response.defer()
        balls = await Ball.filter(
            enabled=True,
            tradeable=True,
            rarity__range=(pack_settings.min_rarity_daily, pack_settings.max_rarity_daily)
        )
        ball = await self._get_random_countryball(balls)
        rarity = ball.rarity
        instance = await BallInstance.create(
            player=player,
            ball=ball,
            health_bonus=random.randint(-settings.max_health_bonus, settings.max_health_bonus),
            attack_bonus=random.randint(-settings.max_attack_bonus, settings.max_attack_bonus),
        )
        embed = discord.Embed(title=f"🎁 You got {ball.country}!", color=discord.Color.gold())
        desc = f"📖 **Rarity:** {rarity}\n"
        rarities = [x for x in items if x["name"] == ball.country]
        for item in rarities:
            if item["type"] == ItemType.Crew:
                desc +=  f"🏴‍☠️ **Crew Rarity:** {item["rarity"]}\n"
            elif item["type"] == ItemType.Fruit:
                desc += f"🍎 **Fruit Rarity:** {item["rarity"]}\n"
            elif item["type"] == ItemType.Ship:
                desc += f"🚢 **Ship Rarity:** {item["rarity"]}\n"
            elif item["type"] == ItemType.Weapon:
                desc += f"⚔️ **Weapon Rarity:** {item["rarity"]}\n"
        desc += (
            f"❤️ **Health:** {ball.health}\n"
            f"⚔️ **Attack:** {ball.attack}\n"
        )
        embed.description = desc
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        footer_text = (
            f"Uses: {resource.uses}/3. Come back tomorrow." 
            if resource.uses >= 3 
            else f"Uses: {resource.uses}/3."
        )
        embed.set_footer(text=footer_text)
        with ThreadPoolExecutor() as pool:
            buffer = await interaction.client.loop.run_in_executor(pool, instance.draw_card)
        file = discord.File(buffer, "card.webp")
        embed.set_image(url="attachment://card.webp")
        await interaction.followup.send(embed=embed, file=file)
    
    @app_commands.command(name="weekly")
    async def weekly(self, interaction: discord.Interaction["BallsDexBot"]):
        """
        Claim your weekly pack!
        """
        player, _ = await Player.get_or_create(discord_id=interaction.user.id)
        resource, _ = await PackResource.get_or_create(player=player)
        if await resource.is_weekly_on_cooldown():
            await interaction.response.send_message(
                f"You've used all weekly packs. "
                f"Come back {format_dt(resource.weekly_cooldown + timedelta(days=7), style='R')}!", # type: ignore
                ephemeral=True
            )
            return
        if not pack_settings.min_rarity_weekly or not pack_settings.max_rarity_weekly:
            await interaction.response.send_message(
                "Weekly packs are not configured. Contact support if this persists.",
                ephemeral=True
            )
            return

        if resource.weekly_cooldown is not None:
            await resource.remove_weekly_cooldown()
        resource.uses += 1
        await resource.save(update_fields=("uses",))
        if resource.uses >= 3:
            await resource.set_weekly_cooldown()
        await interaction.response.defer()
        balls = await Ball.filter(
            enabled=True,
            tradeable=True,
            rarity__range=(pack_settings.min_rarity_weekly, pack_settings.max_rarity_weekly)
        )
        ball = await self._get_random_countryball(balls)
        rarity = ball.rarity
        instance = await BallInstance.create(
            player=player,
            ball=ball,
            health_bonus=random.randint(-settings.max_health_bonus, settings.max_health_bonus),
            attack_bonus=random.randint(-settings.max_attack_bonus, settings.max_attack_bonus),
        )
        embed = discord.Embed(title=f"🎁 You got {ball.country}!", color=discord.Color.gold())
        desc = f"📖 **Rarity:** {rarity}\n"
        rarities = [x for x in items if x["name"] == ball.country]
        for item in rarities:
            if item["type"] == ItemType.Crew:
                desc +=  f"🏴‍☠️ **Crew Rarity:** {item["rarity"]}\n"
            elif item["type"] == ItemType.Fruit:
                desc += f"🍎 **Fruit Rarity:** {item["rarity"]}\n"
            elif item["type"] == ItemType.Ship:
                desc += f"🚢 **Ship Rarity:** {item["rarity"]}\n"
            elif item["type"] == ItemType.Weapon:
                desc += f"⚔️ **Weapon Rarity:** {item["rarity"]}\n"
        desc += (
            f"❤️ **Health:** {ball.health}\n"
            f"⚔️ **Attack:** {ball.attack}\n"
        )
        embed.description = desc
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Come back next week for another pack!")
        with ThreadPoolExecutor() as pool:
            buffer = await interaction.client.loop.run_in_executor(pool, instance.draw_card)
        file = discord.File(buffer, "card.webp")
        embed.set_image(url="attachment://card.webp")
        await interaction.followup.send(embed=embed, file=file)

    @app_commands.command()
    async def shop(self, interaction: discord.Interaction["BallsDexBot"]):
        """
        Check available packs in the shop.
        """
        await interaction.response.defer(thinking=True)
        packs = await ItemModel.all().order_by("prize").prefetch_related("special")
        
        entries: list[tuple[str, str]] = []
        for pack in packs:
            if pack.emoji_id:
                emoji = str(self.bot.get_emoji(pack.emoji_id))
            else:
                emoji = ""
            
            description = (
                f"Price: **{pack.prize:,}**\n"
                f"Minimum Rarity: **{pack.minimum_rarity}**\n"
                f"Maximum Rarity: **{pack.maximum_rarity}**\n"
                f"Special: **{pack.special.name if pack.special else 'Any'}**\n"
            )
            
            entries.append(
                (
                    f"{emoji} {pack.name}",
                    description
                )
            )
        
        source = FieldPageSource(entries, per_page=5)
        source.embed.title = "Available Packs"

        pages = Pages(source, interaction=interaction, compact=True)
        await pages.start()
    
    @app_commands.command()
    async def buy(
        self, interaction: discord.Interaction["BallsDexBot"], pack: ItemTransform
    ):
        """
        Buy a pack.

        Parameters
        ----------
        pack: Item
            The item to buy.
        """
        await interaction.response.defer(thinking=True, ephemeral=True)
        player, _ = await Player.get_or_create(discord_id=interaction.user.id)
        instance, _ = await MoneyInstance.get_or_create(player=player)
        if instance.amount < pack.prize:
            if pack.emoji_id:
                emoji = self.bot.get_emoji(pack.emoji_id)
            else:
                emoji = ""
            await interaction.followup.send(
                f"You don't enough money to buy **{emoji} {pack.name}**\n"
                f"Your actual balance: **{instance.amount:,}**"
            )
            return
        
        instance.amount -= pack.prize
        await instance.save(update_fields=("amount",))

        balls = await Ball.filter(
            enabled=True,
            tradeable=True,
            rarity__range=(pack.minimum_rarity, pack.maximum_rarity)
        )
        ball = await self._get_random_countryball(balls)
        rarity = ball.rarity
        instance = await BallInstance.create(
            player=player,
            ball=ball,
            health_bonus=random.randint(-settings.max_health_bonus, settings.max_health_bonus),
            attack_bonus=random.randint(-settings.max_attack_bonus, settings.max_attack_bonus),
        )
        embed = discord.Embed(title=f"🎁 You got {ball.country}!", color=discord.Color.gold())
        desc = f"📖 **Rarity:** {rarity}\n"
        rarities = [x for x in items if x["name"] == ball.country]
        for item in rarities:
            if item["type"] == ItemType.Crew:
                desc +=  f"🏴‍☠️ **Crew Rarity:** {item["rarity"]}\n"
            elif item["type"] == ItemType.Fruit:
                desc += f"🍎 **Fruit Rarity:** {item["rarity"]}\n"
            elif item["type"] == ItemType.Ship:
                desc += f"🚢 **Ship Rarity:** {item["rarity"]}\n"
            elif item["type"] == ItemType.Weapon:
                desc += f"⚔️ **Weapon Rarity:** {item["rarity"]}\n"
        desc += (
            f"❤️ **Health:** {ball.health}\n"
            f"⚔️ **Attack:** {ball.attack}\n"
        )
        embed.description = desc
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        with ThreadPoolExecutor() as pool:
            buffer = await interaction.client.loop.run_in_executor(pool, instance.draw_card)
        file = discord.File(buffer, "card.webp")
        embed.set_image(url="attachment://card.webp")
        await interaction.followup.send(embed=embed, file=file)

    @app_commands.command()
    @app_commands.checks.cooldown(1, 86400, key=lambda i: i.user.id)
    async def coin_daily(self, interaction: discord.Interaction["BallsDexBot"]):
        """
        Claim your daily payment.
        """
        await interaction.response.defer(thinking=True, ephemeral=True)
        player, _ = await Player.get_or_create(discord_id=interaction.user.id)
        instance, _ = await MoneyInstance.get_or_create(player=player)

        instance.amount += 1500
        await instance.save(update_fields=("amount",))

        await interaction.followup.send(
            f"You've claimed **1,500** coins! Now you have **{instance.amount:,}**. "
            "Come back tomorrow!"
        )
    
    @app_commands.command()
    async def coin_balance(self, interaction: discord.Interaction["BallsDexBot"]):
        """
        Check your actual coin balance.
        """
        await interaction.response.defer(thinking=True, ephemeral=True)
        player, _ = await Player.get_or_create(discord_id=interaction.user.id)
        instance, _ = await MoneyInstance.get_or_create(player=player)

        await interaction.followup.send(f"You have **{instance.amount:,}** coins.")
        return


    async def _get_random_countryball(self, countryballs: list[Ball]) -> Ball:
        if not countryballs:
            raise RuntimeError("No ball to spawn")
        rarities = [x.rarity for x in countryballs]
        cb = random.choices(population=countryballs, weights=rarities, k=1)[0]
        return cb