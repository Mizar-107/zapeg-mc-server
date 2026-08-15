#!/usr/bin/env python3
"""
Heraldor — ZapeG'in karanlık varlığı (v1: presence engine).

Herobrine türü bir varlık ama bizimki: adı Heraldor. Kimse ondan bahsetmez,
o herkesi izler. Bu servis rastgele ve NADİR olaylar üretir:

  whisper  — rastgele bir oyuncuya, sadece onun gördüğü fısıltı (+ ürkütücü ses)
  global   — herkese kısa, şifreli bir cümle (çok nadir)
  discord  — Discord kanalına imzasız/tekinsiz mesaj (webhook; en nadiri)
  shadows  — [VARSAYILAN KAPALI] gece yarısı, rastgele bir oyuncunun yanına
             30 saniyeliğine "Heraldor'un Gölgesi" adlı 3 vex (kendiliğinden yok
             olur — korkutur, eşya/ev zararı yok)

Gece (oyun saati 13000–23000) fısıltı olasılığı 3 katına çıkar.
LLM opsiyoneldir (HERALDOR_LLM=true + LLM_* env): satırlar üretilir; kapalıysa
gömülü havuzlar kullanılır. Asla oyuncu komutu çalıştırılmaz.
"""
import json
import os
import random
import time
import urllib.request

from mcrcon import MCRcon

RCON_HOST = os.environ.get("RCON_HOST", "mc")
RCON_PORT = int(os.environ.get("RCON_PORT", "25575"))
RCON_PASSWORD = os.environ["RCON_PASSWORD"]
WEBHOOK = os.environ.get("HERALDOR_WEBHOOK", "").strip()
EVENTS = os.environ.get("HERALDOR_EVENTS", "false").lower() == "true"
USE_LLM = os.environ.get("HERALDOR_LLM", "false").lower() == "true"
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "300"))  # saniye

# Olasılıklar: her CHECK_INTERVAL'da zar atılır (gündüz değerleri)
P_WHISPER = float(os.environ.get("P_WHISPER", "0.06"))
P_GLOBAL = float(os.environ.get("P_GLOBAL", "0.015"))
P_DISCORD = float(os.environ.get("P_DISCORD", "0.008"))
P_SHADOWS = float(os.environ.get("P_SHADOWS", "0.004"))

WHISPERS = [
    "arkana bakma.",
    "kazma sesini duyuyorum. hep duyuyorum.",
    "o meşaleyi ben söndürmedim.",
    "burayı kazmamalıydın.",
    "yalnız değilsin. hiç olmadın.",
    "gölgen benim yanımda kalıyor artık.",
    "kapıyı açık bıraktın.",
    "yatağın soğuk. benimki gibi.",
    "adımı söyleme.",
    "seni sayıyorum.",
]

GLOBALS_ = [
    "O kule benimdi.",
    "Kaybettiğiniz her eşya bana geliyor.",
    "Sekiz kişisiniz. Ben dokuzuncuyum.",
    "Muhtar beni hatırlar. Sorun ona.",
    "Işıklarınız güzelmiş. Şimdilik.",
    "Uyuyunca daha sessiz oluyorsunuz.",
]

DISCORDS = [
    "sunucu hiç kapanmıyor sanıyorsunuz. ben hiç uyumuyorum.",
    "dokuzuncu oyuncu whitelist istemez.",
    "bu kanalı da görüyorum.",
    "biriniz bu gece geç saate kadar oynayacak. biliyorum.",
    "🕯",
]

OBFUS = "kelimeler kayboluyor"  # §k ile bozulan kısım


def rcon(cmd: str) -> str:
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as r:
        return r.command(cmd)


def online_players() -> list:
    try:
        out = rcon("list")
        if ":" in out:
            names = out.split(":", 1)[1].strip()
            return [n.strip() for n in names.split(",") if n.strip()]
    except Exception as e:
        print(f"[heraldor] list hata: {e}")
    return []


def is_night() -> bool:
    try:
        out = rcon("time query daytime")  # "The time is 14500"
        t = int("".join(ch for ch in out if ch.isdigit()) or 0)
        return 13000 <= t <= 23000
    except Exception:
        return False


def llm_line(kind: str) -> str | None:
    if not USE_LLM:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.environ.get("LLM_API_KEY", "none"),
        )
        resp = client.chat.completions.create(
            model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
            max_tokens=40,
            temperature=1.1,
            timeout=20,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Heraldor adında, Minecraft sunucusunda yaşayan Herobrine türü "
                        "tekinsiz bir varlıksın. Türkçe, TEK cümlelik, kısa ve rahatsız "
                        f"edici bir {kind} cümlesi yaz. Şiddet/tehdit yok — tekinsizlik var. "
                        "Tırnak kullanma."
                    ),
                }
            ],
        )
        line = (resp.choices[0].message.content or "").strip().replace('"', "'")
        return line[:140] or None
    except Exception as e:
        print(f"[heraldor] llm hata (havuz kullanılacak): {e}")
        return None


def whisper(player: str) -> None:
    line = llm_line("fısıltı") or random.choice(WHISPERS)
    payload = json.dumps(
        [
            "",
            {"text": line + " ", "color": "dark_gray", "italic": True},
            {"text": OBFUS, "color": "dark_gray", "obfuscated": True},
        ],
        ensure_ascii=False,
    )
    rcon(f"tellraw {player} {payload}")
    snd = random.choice(
        ["minecraft:ambient.cave", "minecraft:entity.enderman.stare", "minecraft:block.sculk_sensor.clicking"]
    )
    rcon(f"execute at {player} run playsound {snd} hostile {player} ~ ~ ~ 0.7 0.5")
    print(f"[heraldor] whisper -> {player}: {line}")


def global_msg() -> None:
    line = llm_line("herkese açık kısa mesaj") or random.choice(GLOBALS_)
    payload = json.dumps(
        [
            "",
            {"text": "Heraldor", "color": "dark_red", "bold": True},
            {"text": " " + line, "color": "gray", "italic": True},
        ],
        ensure_ascii=False,
    )
    rcon(f"tellraw @a {payload}")
    rcon("playsound minecraft:ambient.basalt_deltas.mood hostile @a ~ ~ ~ 0.5 0.6")
    print(f"[heraldor] global: {line}")


def discord_msg() -> None:
    if not WEBHOOK:
        return
    line = llm_line("Discord kanalına yazılmış tekinsiz mesaj") or random.choice(DISCORDS)
    try:
        req = urllib.request.Request(
            WEBHOOK,
            data=json.dumps({"content": line, "username": "Heraldor"}).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "heraldor/1.0"},
        )
        urllib.request.urlopen(req, timeout=15).read()
        print(f"[heraldor] discord: {line}")
    except Exception as e:
        print(f"[heraldor] webhook hata: {e}")


def shadows(player: str) -> None:
    """Gece yarısı 30 sn'lik vex tacizi — kendiliğinden yok olur, grief yok."""
    name = json.dumps({"text": "Heraldor'un Gölgesi", "color": "dark_gray"}, ensure_ascii=False)
    for _ in range(3):
        rcon(
            f"execute at {player} run summon minecraft:vex ~ ~1 ~ "
            f'{{CustomName:\'{name}\',LifeTicks:600,Silent:1b}}'
        )
    rcon(f"execute at {player} run playsound minecraft:entity.vex.charge hostile {player} ~ ~ ~ 1 0.6")
    payload = json.dumps(
        [{"text": "gölgelerim seni buldu.", "color": "dark_gray", "italic": True}],
        ensure_ascii=False,
    )
    rcon(f"tellraw {player} {payload}")
    print(f"[heraldor] shadows -> {player}")


def main() -> None:
    print(
        f"[heraldor] uyanıyor — interval={CHECK_INTERVAL}s, "
        f"webhook={'var' if WEBHOOK else 'yok'}, events={EVENTS}, llm={USE_LLM}"
    )
    while True:
        time.sleep(CHECK_INTERVAL)
        try:
            players = online_players()
            night = is_night() if players else False
            mult = 3.0 if night else 1.0

            if players and random.random() < P_WHISPER * mult:
                whisper(random.choice(players))
            if players and random.random() < P_GLOBAL * mult:
                global_msg()
            if random.random() < P_DISCORD:
                discord_msg()  # oyuncu yokken de yazabilir — daha da tekinsiz
            if EVENTS and players and night and random.random() < P_SHADOWS:
                shadows(random.choice(players))
        except Exception as e:
            print(f"[heraldor] döngü hata: {e}")


if __name__ == "__main__":
    main()
