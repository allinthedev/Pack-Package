from tortoise import models, fields
from .models import Player, Special

class Item(models.Model):
    name = fields.CharField(max_length=64)
    description = fields.TextField(null=True, description="An optional description for the item")
    prize = fields.BigIntField(null=True, description="The prize of the item. If blanks, it will free")
    emoji_id = fields.BigIntField(null=True, default=None)
    minimum_rarity = fields.FloatField(description="Minimum rarity range.")
    maximum_rarity = fields.FloatField(description="Maximum rarity range.")
    created_at = fields.DatetimeField(auto_now_add=True)
    special: fields.ForeignKeyNullableRelation[Special] = fields.ForeignKeyField(
        "models.Special",
        on_delete=fields.SET_NULL,
        null=True,
        default=None,
        description="The special of the item (optional)"
    )

    def __str__(self) -> str:
        return self.name

class MoneyInstance(models.Model):
    player: fields.OneToOneRelation[Player] = fields.OneToOneField(
        "models.Player",
        on_delete=fields.CASCADE
    )
    amount = fields.BigIntField(default=0)