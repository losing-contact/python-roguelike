import os, sys

BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
LEVELS_DIR = os.path.join(BASE, "levels")

def load_map(level=1):
    path = os.path.join(LEVELS_DIR, f"map{level}.txt")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return [list(line.rstrip("\n")) for line in f]

def load_items(level=1):
    path = os.path.join(LEVELS_DIR, f"map{level}_items.txt")
    if not os.path.exists(path):
        return []
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.endswith(":"):
                items.append({"name": line[:-1]})
            elif "=" in line:
                key, value = line.split("=", 1)
                items[-1][key.strip()] = value.strip()
    return items