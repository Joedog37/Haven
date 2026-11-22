# Haven Agent v1.2 - training_blocks.py
# Make small learning blocks for Haven's own model, later.
# This does NOT train a model. It just saves what Haven already learned,
# in small pieces, one file per day, so that later training can use
# small pieces at a time instead of loading everything at once.
#
# Usage, in the Pc folder:
#   python memory/training_blocks.py
# It reads Pc/memory/storage.json, cleans the chats
# (removes * [ ] [[ ]] ), and writes
#   Pc/memory/training_blocks/2026-11-19.jsonl
# One line per chat, small files, easy to check.
# Joseph can open a .jsonl file in Notepad and read it.
# Nothing is sent anywhere. The files stay on his PC.

import json
import os
import re
from datetime import datetime


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"\*\*([^*]{1,200})\*\*", r"\1", text)
    text = re.sub(r"\[\[[^\]]*\]\]", "", text)
    text = re.sub(r"\[[^\]\n]{1,120}\]", "", text)
    text = re.sub(r"\*[^*\n]{1,120}\*", "", text)
    text = text.replace("[", "").replace("]", "").replace("*", "")
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def export_training_blocks(storage_path=None, out_folder=None):
    if storage_path is None:
        storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage.json")
    if out_folder is None:
        out_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training_blocks")
    os.makedirs(out_folder, exist_ok=True)

    if not os.path.exists(storage_path):
        return "No storage.json found. Nothing to export."

    with open(storage_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    history = data.get("conversation_history", [])
    if not history:
        return "No conversations saved yet. Nothing to export."

    # Group by day, so each file is small
    by_day = {}
    for entry in history:
        user = clean_text(entry.get("user", ""))
        haven = clean_text(entry.get("haven", ""))
        if not user or not haven:
            continue
        stamp = entry.get("timestamp", "")[:10] or datetime.now().strftime("%Y-%m-%d")
        by_day.setdefault(stamp, []).append({"user": user, "haven": haven})

    written = []
    for day, pairs in sorted(by_day.items()):
        path = os.path.join(out_folder, f"{day}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for pair in pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")
        written.append(f"{day}.jsonl ({len(pairs)} chats)")

    return f"Wrote {len(written)} training block file(s) to {out_folder}:\n" + "\n".join(written)


if __name__ == "__main__":
    print(export_training_blocks())
