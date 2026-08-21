#!/usr/bin/env python3
"""Generate data/zapeg/structures/harabe_1.nbt for the zapeg-lore datapack.

A small vanilla-only ruin: broken stone-brick walls, two surviving corner
pillars, a lectern on a chiseled base, a ring of eight unlit white candles
with a single black candle behind the lectern (sekiz hane + dokuzuncu — the
deniable wink; never explained to players).

Placement in game (OP):  /place template zapeg:harabe_1
Then put the "kayip_sayfa" book on the lectern by hand
(/zapeg-kitap ver <op> kayip_sayfa → right-click the lectern).

Deterministic output: fixed RNG seed, sorted block order — rerunning the
script must produce a byte-identical file so git diffs stay honest.

Requires: pip install nbtlib   (any 2.x)
Run from repo root:  python3 tools/gen-harabe-structure.py
"""

import random
from pathlib import Path

import nbtlib
from nbtlib import tag

DATA_VERSION = 3465  # 1.20.1
SIZE = (9, 5, 9)
OUT = (
    Path(__file__).resolve().parent.parent
    / "overrides/world/datapacks/zapeg-lore/data/zapeg/structures/harabe_1.nbt"
)

rng = random.Random(20260821)


def state(name, **props):
    """Palette key: canonical (name, sorted-props) tuple."""
    return (name, tuple(sorted((k, str(v)) for k, v in props.items())))


FLOOR_CHOICES = [
    state("minecraft:cobblestone"),
    state("minecraft:mossy_cobblestone"),
    state("minecraft:cracked_stone_bricks"),
    state("minecraft:stone_bricks"),
]
WALL_CHOICES = [
    state("minecraft:stone_bricks"),
    state("minecraft:mossy_stone_bricks"),
    state("minecraft:cracked_stone_bricks"),
]

blocks = {}  # (x,y,z) -> state


def put(x, y, z, st):
    blocks[(x, y, z)] = st


# --- floor: irregular 7x7 patch centred at (4, _, 4) ------------------------
for x in range(1, 8):
    for z in range(1, 8):
        d = max(abs(x - 4), abs(z - 4))
        if d == 3 and rng.random() < 0.35:
            continue  # eaten edge
        put(x, 0, z, rng.choice(FLOOR_CHOICES))

# --- walls: broken ring on the floor edge (y1..y3), with door gap south -----
def wall_height(x, z):
    if (x, z) in ((1, 1), (7, 1)):  # two surviving north pillars
        return 3
    if (x, z) in ((1, 7), (7, 7)):
        return rng.choice((1, 2))
    return rng.choice((0, 1, 1, 2))


for x in range(1, 8):
    for z in (1, 7):
        if z == 7 and x in (4,):  # south doorway gap
            continue
        if (x, 0, z) not in blocks:
            continue
        for y in range(1, 1 + wall_height(x, z)):
            put(x, y, z, rng.choice(WALL_CHOICES))
for z in range(2, 7):
    for x in (1, 7):
        if (x, 0, z) not in blocks:
            continue
        for y in range(1, 1 + wall_height(x, z)):
            put(x, y, z, rng.choice(WALL_CHOICES))

# pillar caps: mossy slabs on the two tall north pillars
put(1, 4, 1, state("minecraft:mossy_stone_brick_slab", type="bottom", waterlogged="false"))
put(7, 4, 1, state("minecraft:mossy_stone_brick_slab", type="bottom", waterlogged="false"))

# --- centre: chiseled base + lectern facing the south doorway ---------------
put(4, 0, 4, state("minecraft:chiseled_stone_bricks"))
put(4, 1, 4, state("minecraft:lectern", facing="south", has_book="false", powered="false"))

# --- candles: ring of 8 white around the lectern, 1 black behind it ---------
CANDLE_RING = [(2, 2), (4, 2), (6, 2), (2, 4), (6, 4), (2, 6), (4, 6), (6, 6)]
for cx, cz in CANDLE_RING:
    if (cx, 0, cz) in blocks:
        put(cx, 1, cz, state(
            "minecraft:white_candle", candles=rng.choice((1, 1, 2)),
            lit="false", waterlogged="false",
        ))
# dokuzuncu: black, directly north of the lectern, always a single candle
put(4, 1, 3, state("minecraft:black_candle", candles=1, lit="false", waterlogged="false"))

# --- decay accents ----------------------------------------------------------
put(1, 3, 2, state("minecraft:cobweb"))
put(6, 1, 7, state("minecraft:cobweb"))
put(7, 1, 2, state("minecraft:vine", east="false", north="true", south="false", up="false", west="false"))

# --- clear the interior air so grass/leaves don't poke through --------------
for x in range(2, 7):
    for z in range(2, 7):
        for y in range(1, 4):
            if (x, y, z) not in blocks:
                put(x, y, z, state("minecraft:air"))

# --- emit -------------------------------------------------------------------
palette_order = []
palette_index = {}
for st in blocks.values():
    if st not in palette_index:
        palette_index[st] = len(palette_order)
        palette_order.append(st)


def palette_entry(st):
    name, props = st
    entry = tag.Compound({"Name": tag.String(name)})
    if props:
        entry["Properties"] = tag.Compound({k: tag.String(v) for k, v in props})
    return entry


structure_root = (
    tag.Compound(
        {
            "size": tag.List[tag.Int]([tag.Int(s) for s in SIZE]),
            "entities": tag.List[tag.Compound]([]),
            "blocks": tag.List[tag.Compound](
                [
                    tag.Compound(
                        {
                            "pos": tag.List[tag.Int](
                                [tag.Int(x), tag.Int(y), tag.Int(z)]
                            ),
                            "state": tag.Int(palette_index[st]),
                        }
                    )
                    for (x, y, z), st in sorted(blocks.items())
                ]
            ),
            "palette": tag.List[tag.Compound](
                [palette_entry(st) for st in palette_order]
            ),
            "DataVersion": tag.Int(DATA_VERSION),
        }
    )
)

OUT.parent.mkdir(parents=True, exist_ok=True)
# gzip with mtime=0 so reruns are byte-identical (honest git diffs).
import gzip
import io

buf = io.BytesIO()
nbtlib.File(structure_root).write(buf)
with open(OUT, "wb") as fh:
    with gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
        gz.write(buf.getvalue())
print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(blocks)} blocks, "
      f"{len(palette_order)} palette states)")
