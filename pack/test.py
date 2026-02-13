import json
import os
from pathlib import Path

raw_crews = json.load(
    open(
        Path(os.path.dirname(os.path.abspath(__file__)), "./crew.json"), 
        "r", 
        encoding="utf-8"
    ),
)["raritie"]
crews = {}
for crew in raw_crews:
    crews[crew["rarity"]] = crew["name"]
print