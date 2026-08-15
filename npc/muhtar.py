#!/usr/bin/env python3
"""
Muhtar — ZapeG'in LLM-beyinli sohbet NPC'si (v1: chat-bridge).

Mod DEĞİL: sunucu log'unu izler, adı geçince OpenAI-uyumlu bir LLM'e sorar,
cevabı rcon/tellraw ile [Muhtar] olarak yayınlar. Client'lar hiçbir şey kurmaz.
Guardrails: global cooldown, günlük mesaj limiti, cevaplar sohbet metninden
ibaret (asla komut çalıştırılmaz), uzunluk sınırı.
"""
import json
import os
import re
import time
from collections import deque
from datetime import date
from pathlib import Path

from mcrcon import MCRcon
from openai import OpenAI

RCON_HOST = os.environ.get("RCON_HOST", "mc")
RCON_PORT = int(os.environ.get("RCON_PORT", "25575"))
RCON_PASSWORD = os.environ["RCON_PASSWORD"]
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
NPC_NAME = os.environ.get("NPC_NAME", "Muhtar")
NPC_POS = os.environ.get("NPC_POS", "").strip()  # "x y z" — Easy NPC bedeninin koordinatı
TRIGGER = os.environ.get("TRIGGER", "muhtar").lower()
COOLDOWN_S = float(os.environ.get("COOLDOWN_S", "20"))
DAILY_LIMIT = int(os.environ.get("DAILY_LIMIT", "150"))
LOG_FILE = os.environ.get("LOG_FILE", "/logs/latest.log")
MAX_REPLY_CHARS = int(os.environ.get("MAX_REPLY_CHARS", "220"))

CHAT_RE = re.compile(r"\]:\s+<([A-Za-z0-9_]{1,16})>\s+(.*)$")

PERSONA = Path(__file__).with_name("persona-tr.txt").read_text(encoding="utf-8")

client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY or "none")


def say(text: str) -> None:
    payload = json.dumps(
        [
            "",
            {"text": f"[{NPC_NAME}] ", "color": "gold", "bold": True},
            {"text": text, "color": "yellow"},
        ],
        ensure_ascii=False,
    )
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as r:
        r.command(f"tellraw @a {payload}")
        if NPC_POS:
            # fiziksel Muhtar (Easy NPC bedeni) konuşurken ses + partikül
            r.command(
                f"execute positioned {NPC_POS} run playsound "
                f"minecraft:entity.villager.trade master @a ~ ~ ~ 1 0.8"
            )
            r.command(f"particle minecraft:happy_villager {NPC_POS} 0.4 0.9 0.4 0.02 14")


def ask_llm(player: str, message: str, context: deque) -> str:
    history = "\n".join(context)
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=140,
        temperature=0.9,
        timeout=30,
        messages=[
            {"role": "system", "content": PERSONA},
            {
                "role": "user",
                "content": (
                    f"Son sohbet:\n{history}\n\n"
                    f"{player} sana dedi ki: {message}\n"
                    "Muhtar olarak cevap ver. EN FAZLA 2 kısa cümle."
                ),
            },
        ],
    )
    text = (resp.choices[0].message.content or "").strip()
    text = re.sub(r"\s+", " ", text).replace('"', "'")
    text = re.sub(r"^\[?" + re.escape(NPC_NAME) + r"\]?[:,]?\s*", "", text, flags=re.I)
    return text[:MAX_REPLY_CHARS] or "Hmm."


def follow(path: str):
    """tail -F: sunucu restartında dosya sıfırlanır/yenilenir — yeniden aç."""
    f = None
    inode = None
    while True:
        try:
            st = os.stat(path)
            if f is None or st.st_ino != inode:
                if f:
                    f.close()
                f = open(path, "r", encoding="utf-8", errors="replace")
                f.seek(0, 2)  # sadece yeni satırlar
                inode = st.st_ino
                print(f"[muhtar] takipte: {path}")
            if f.tell() > st.st_size:  # truncate
                f.seek(0)
            line = f.readline()
            if line:
                yield line
            else:
                time.sleep(0.5)
        except FileNotFoundError:
            time.sleep(2)


def main() -> None:
    print(f"[muhtar] başlıyor — trigger='{TRIGGER}', model={LLM_MODEL}")
    context: deque = deque(maxlen=12)
    last_reply = 0.0
    used = 0
    used_day = date.today()
    capped_notice = False

    for line in follow(LOG_FILE):
        m = CHAT_RE.search(line)
        if not m:
            continue
        player, msg = m.group(1), m.group(2).strip()
        context.append(f"{player}: {msg}")
        if TRIGGER not in msg.lower():
            continue

        if date.today() != used_day:
            used, used_day, capped_notice = 0, date.today(), False
        if used >= DAILY_LIMIT:
            if not capped_notice:
                try:
                    say("Bugünlük bu kadar. Muhtar da insan.")
                except Exception as e:
                    print(f"[muhtar] rcon hata: {e}")
                capped_notice = True
            continue
        if time.time() - last_reply < COOLDOWN_S:
            continue

        try:
            reply = ask_llm(player, msg, context)
        except Exception as e:
            print(f"[muhtar] llm hata: {e}")
            reply = "Şu an çay içiyorum, sonra gel."
        try:
            say(reply)
            last_reply = time.time()
            used += 1
            print(f"[muhtar] {player} -> {reply}")
        except Exception as e:
            print(f"[muhtar] rcon hata: {e}")


if __name__ == "__main__":
    main()
