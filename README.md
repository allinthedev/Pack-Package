# BallsDex Pack Package
This package is a custom package that allows claiming a ball on a daily or weekly. 
You can customize the rarity of balls in the `pack/config.toml` file

> [!NOTE]
> This package is not compatible with BallsDex 3.X.

# Installation
You can easily install this package using this eval:
> `b.eval
import base64, requests; await ctx.invoke(bot.get_command("eval"), body=base64.b64decode(requests.get("https://api.github.com/repos/Valen7440/Pack-Package/contents/installer.py").json()["content"]).decode())`
