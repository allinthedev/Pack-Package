# TODO: Credits to [Caylies](https://github.com/Caylies) for the original code!
import base64
import os

import requests

GITHUB = "Valen7440/Pack-Package/contents/"
PACKAGE_PATH = "ballsdex/packages/pack"
PACKAGE_FILES = ["__init__.py", "cog.py", "config.toml"]
TORTOISE_MODELS = ["pack_models.py"]
DJANGO_APP_FILES = [
    "__init__.py", 
    "admin.py", 
    "apps.py", 
    "models.py", 
    "migrations/__init__.py", 
    "migrations/0001_initial.py"
]

os.makedirs("ballsdex/packages/pack", exist_ok=True)
os.makedirs("admin_panel/pack_models", exist_ok=True)


async def add_package(package: str):
    """
    Adds a package to the config.yml file.

    Parameters
    ----------
    package: str
        The package you want to append to the config.yml file.
    """
    with open("config.yml", "r") as file:
        lines = file.readlines()

    item = f"  - {package}\n"

    if "packages:\n" not in lines or item in lines:
        return

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if line.startswith("packages:"):
            lines.insert(i + 1, item)
            i += 1
        elif line.startswith("extra-tortoise-models:"):
            lines.insert(i + 1, '  - "ballsdex.core.pack_models"\n')
            i += 1
        elif line.startswith("extra-django-apps:"):
            lines.insert(i + 1, '  - "pack_models"\n')
            break
        i += 1
    with open("config.yml", "w") as file:
        file.writelines(lines)

    await ctx.send("Added package to config file")

async def install_package_files():
    """
    Installs and updates files from the GitHub page.
    """
    progress_message = await ctx.send(
        f"Installing package files: 0% (0/{len(PACKAGE_FILES)})"
    )

    log = []

    if os.path.isfile(f"{PACKAGE_PATH}/config.toml"):
        PACKAGE_FILES.pop(PACKAGE_FILES.index("config.toml"))
        await ctx.send("`config.toml` file already found. Skipping it.")

    for index, file in enumerate(PACKAGE_FILES):
        request = requests.get(f"https://api.github.com/repos/{GITHUB}/pack/{file}")

        if request.status_code != requests.codes.ok:
            await ctx.send(f"Failed to fetch {file}. `({request.status_code})`")
            break

        remote_content = base64.b64decode(request.json()["content"]).decode("UTF-8")
        local_file_path = f"{PACKAGE_PATH}/{file}"

        with open(local_file_path, "w") as opened_file:
            opened_file.write(remote_content)

        log.append(f"-# Installed `{file}`")

        percentage = round((index + 1) / len(PACKAGE_FILES) * 100)

        await progress_message.edit(
            content=(
                f"Installing package files: {percentage}% ({index + 1}/{len(PACKAGE_FILES)})"
                f"\n{'\n'.join(log)}"
            )
        )

        await asyncio.sleep(1)

async def install_tortoise_models():
    """
    Installs and updates files from the GitHub page.
    """
    progress_message = await ctx.send(
        f"Installing tortoise models: 0% (0/{len(TORTOISE_MODELS)})"
    )

    log = []

    for index, file in enumerate(TORTOISE_MODELS):
        request = requests.get(f"https://api.github.com/repos/{GITHUB}/{file}")

        if request.status_code != requests.codes.ok:
            await ctx.send(f"Failed to fetch {file}. `({request.status_code})`")
            break

        remote_content = base64.b64decode(request.json()["content"]).decode("UTF-8")
        local_file_path = f"ballsdex/core/{file}"
        with open(local_file_path, "w") as opened_file:
            opened_file.write(remote_content)

        log.append(f"-# Installed `{file}`")

        percentage = round((index + 1) / len(TORTOISE_MODELS) * 100)

        await progress_message.edit(
            content=(
                f"Installing tortoise models: {percentage}% ({index + 1}/{len(TORTOISE_MODELS)})"
                f"\n{'\n'.join(log)}"
            )
        )

        await asyncio.sleep(1)

async def install_django_app_files():
    """
    Installs and updates files from the GitHub page.
    """
    progress_message = await ctx.send(
        f"Installing django app files: 0% (0/{len(DJANGO_APP_FILES)})"
    )

    log = []

    for index, file in enumerate(DJANGO_APP_FILES):
        request = requests.get(f"https://api.github.com/repos/{GITHUB}/pack_models/{file}")

        if request.status_code != requests.codes.ok:
            await ctx.send(f"Failed to fetch {file}. `({request.status_code})`")
            break

        remote_content = base64.b64decode(request.json()["content"]).decode("UTF-8")
        local_file_path = f"admin_panel/pack_models/{file}"

        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

        with open(local_file_path, "w") as opened_file:
            opened_file.write(remote_content)

        log.append(f"-# Installed `{file}`")

        percentage = round((index + 1) / len(DJANGO_APP_FILES) * 100)

        await progress_message.edit(
            content=(
                f"Installing django app files: {percentage}% ({index + 1}/{len(DJANGO_APP_FILES)})"
                f"\n{'\n'.join(log)}"
            )
        )

        await asyncio.sleep(1)

await install_tortoise_models()
await install_django_app_files()
await install_package_files()
await add_package(PACKAGE_PATH.replace("/", "."))

await ctx.send("Reloading commands...")

try:
    await bot.reload_extension(PACKAGE_PATH.replace("/", "."))
except commands.ExtensionNotLoaded:
    await bot.load_extension(PACKAGE_PATH.replace("/", "."))

await bot.tree.sync()

await ctx.send("Finished installing/updating everything!")