#!/usr/bin/env python3
"""Texture builders - part 3: the remaining vanilla sprites.

Everything here is art vanilla already ships as finished bitmaps rather than
chrome the game assembles procedurally: slot hint silhouettes, machine progress
bars, container list tabs, status chips and statistic glyphs.

Almost all of them are *greyscale* in vanilla. Rather than redraw each
silhouette we remap its luminance through a Fluent ramp, which keeps the exact
shape Minecraft expects while replacing the tone. Sprites that carry real
information in colour - a furnace flame's orange, an error mark's red, the maps,
the friends illustration, the enchanting runes - either survive that remap
(saturated pixels are passed through) or are left untouched.

Paths are relative to `assets/minecraft/`, matching the vanilla manifest.
"""
import numpy as np

from fluent import (ACCENT, ACCENT_DARK, ACCENT_LIGHT, ACCENT_WASH,
                    ACRYLIC_EDGE, C, EXP, EXP_DEEP, MICA_BRIGHT, MICA_DEEP,
                    STROKE, Surface, apply_mask, bottom_line_mask,
                    fluent_button, fluent_slot, over, rounded_mask,
                    rounded_ring_mask, shade_rows, top_line_mask, with_a)

SPR = "textures/gui/sprites/"
CON = SPR + "container/"
LEG = "textures/gui/"

_reader = None


def set_reader(fn):
    global _reader
    _reader = fn


def load(path):
    return _reader(path).astype(np.uint8).copy()


# --------------------------------------------------------------------------
# recolouring helpers
# --------------------------------------------------------------------------
def luminance(a):
    return (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])


def _sat(a):
    mx = a[..., :3].max(axis=2).astype(np.float32)
    mn = a[..., :3].min(axis=2).astype(np.float32)
    return mx - mn


def _rgb(color):
    """Accept either a Fluent token tuple or a '#rrggbb' string; RGB only."""
    return C(color)[:3] if isinstance(color, str) else color[:3]


def solid(path, color):
    """Flatten a sprite to one Fluent colour, keeping the vanilla silhouette."""
    a = load(path)
    a[..., 0] = color[0]
    a[..., 1] = color[1]
    a[..., 2] = color[2]
    return a


def remap(path, dark, light, keep_sat=True, sat_thresh=46.0):
    """Map luminance onto a `dark` -> `light` Fluent ramp. Saturated pixels keep
    their own colour so the sprite does not lose meaning."""
    a = load(path)
    lum = (luminance(a) / 255.0)[..., None]
    hues = a[..., :3].astype(np.float32)
    d = np.array(_rgb(dark), np.float32)
    l = np.array(_rgb(light), np.float32)
    out = d * (1.0 - lum) + l * lum
    if keep_sat:
        m = np.clip((_sat(a) - sat_thresh) / 40.0, 0.0, 1.0)[..., None]
        out = out * (1.0 - m) + hues * m
    a[..., :3] = np.clip(out, 0, 255).astype(np.uint8)
    return a


def brighten(path, gain=1.0, lift=0.0):
    a = load(path)
    rgb = a[..., :3].astype(np.float32) * gain + lift
    a[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return a


# --------------------------------------------------------------------------
# panel recipes
# --------------------------------------------------------------------------
def field(w, h, disabled=False):
    """Dark Fluent field: EditBox text is hard coded to 0xE0E0E0."""
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=(30, 30, 33, 236 if disabled else 210), radius=2)
    a = s.array()
    apply_mask(a, rounded_ring_mask(w, h, 2, 1), (0, 0, 0, 120))
    apply_mask(a, top_line_mask(w, h, 2), (0, 0, 0, 80))
    apply_mask(a, bottom_line_mask(w, h, 2),
               (255, 255, 255, 26) if disabled else (255, 255, 255, 44))
    return a


def choice(w, h, state, radius=3):
    """Recipe / pattern list tile. Item art is blitted on top, the label is white,
    so the tile itself stays dark; choosing one turns it accent."""
    if state == "selected":
        fill, edge = ACCENT, with_a(ACCENT_LIGHT, 200)
    elif state == "highlighted":
        fill, edge = C("#3C3C42"), (255, 255, 255, 90)
    else:
        fill, edge = C("#2A2A2E"), (255, 255, 255, 46)
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=fill, radius=radius)
    a = s.array()
    shade_rows(a, 0, 0, w, h, (1.10, 0.94))
    apply_mask(a, rounded_ring_mask(w, h, radius, 1), edge)
    apply_mask(a, top_line_mask(w, h, radius),
               (255, 255, 255, 110 if state == "selected" else 70))
    return a


def thumb(w, h):
    r = 2
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=ACCENT, radius=r)
    a = s.array()
    apply_mask(a, rounded_ring_mask(w, h, r, 1), with_a(ACCENT_DARK, 210))
    apply_mask(a, top_line_mask(w, h, r), (255, 255, 255, 90))
    apply_mask(a, bottom_line_mask(w, h, r), (0, 0, 0, 70))
    return a


def thumb_disabled(w, h):
    r = 2
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=(88, 88, 94, 220), radius=r)
    a = s.array()
    apply_mask(a, rounded_ring_mask(w, h, r, 1), (0, 0, 0, 110))
    apply_mask(a, top_line_mask(w, h, r), (255, 255, 255, 40))
    return a


def ench_row(w, h, state, radius=3):
    """Enchantment row backdrop. The enchant name is drawn in dark brown
    (0x685E4A), so these rows have to stay light."""
    if state == "highlighted":
        base, stroke = ACCENT_WASH, with_a(ACCENT, 150)
    elif state == "disabled":
        base, stroke = MICA_DEEP, STROKE
    else:
        base, stroke = MICA_BRIGHT, STROKE
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=with_a(base, 238), radius=radius)
    a = s.array()
    shade_rows(a, 0, 0, w, h, (1.03, 0.96))
    apply_mask(a, rounded_ring_mask(w, h, radius, 1), stroke)
    apply_mask(a, top_line_mask(w, h, radius), (255, 255, 255, 190))
    return a


def slot_grid(cols, rows):
    """A grid of Fluent slot wells on vanilla's 18px pitch."""
    w, h = cols * 18, rows * 18
    a = np.zeros((h, w, 4), np.uint8)
    well = fluent_slot(18, 18, surface="light")
    for j in range(rows):
        for i in range(cols):
            over(a, well, i * 18, j * 18)
    return a


def xp_bar(w, h, state):
    """Villager trade XP bar. Vanilla leaves the top and bottom rows empty, so
    the filled body is drawn into rows 1..h-2 of a full-size canvas."""
    body = h - 2
    if state == "background":
        fill, top, bottom = (0, 0, 0, 220), (0, 0, 0, 130), (255, 255, 255, 34)
    elif state == "current":
        fill, top, bottom = with_a(EXP_DEEP, 245), (0, 0, 0, 90), (0, 0, 0, 60)
    else:
        fill, top, bottom = with_a(EXP, 245), (255, 255, 255, 90), (0, 0, 0, 60)
    s = Surface(w, body, ss=4)
    s.rect(0, 0, w, body, fill=fill, radius=1)
    bar = s.array()
    apply_mask(bar, top_line_mask(w, body, 1), top)
    apply_mask(bar, bottom_line_mask(w, body, 1), bottom)
    a = np.zeros((h, w, 4), np.uint8)
    a[1:1 + body] = bar
    return a


def beacon_button(size, state):
    if state != "selected":
        return fluent_button(size, size, state)
    r = 3
    s = Surface(size, size, ss=4)
    s.rect(0, 0, size, size, fill=ACCENT_DARK, radius=r)
    a = s.array()
    shade_rows(a, 0, 0, size, size, (1.06, 0.96))
    apply_mask(a, rounded_ring_mask(size, size, r, 1), with_a(ACCENT_LIGHT, 190))
    apply_mask(a, top_line_mask(size, size, r), (255, 255, 255, 60))
    return a


def gamemode_switcher():
    """The switcher's own backdrop: a 125x75 Acrylic sheet with a header band.
    Only that rect is blitted, so it is drawn into the vanilla 128x128 canvas."""
    w, h = 128, 128
    pw, ph, r = 125, 75, 6
    s = Surface(pw, ph, ss=4)
    s.rect(0, 0, pw, ph, fill=with_a(C("#1B1B1D"), 216), radius=r)
    p = s.array()
    shade_rows(p, 0, 0, pw, ph, (1.16, 0.94))
    band = np.zeros((ph, pw), np.uint8)
    band[0:20, :] = 255
    apply_mask(p, np.minimum(band, rounded_mask(pw, ph, r)),
               with_a(C("#0C0C0E"), 150))
    apply_mask(p, rounded_ring_mask(pw, ph, r, 1), ACRYLIC_EDGE)
    apply_mask(p, top_line_mask(pw, ph, r), (255, 255, 255, 46))
    hair = np.zeros((ph, pw), np.uint8)
    hair[19, :] = 255
    apply_mask(p, np.minimum(hair, rounded_mask(pw, ph, r)), (0, 0, 0, 120))
    out = np.zeros((h, w, 4), np.uint8)
    out[0:ph, 0:pw] = p
    return out


def adv_background():
    """Shared tile behind the advancement tree; dark so white text reads."""
    s = Surface(16, 16, ss=4)
    s.rect(0, 0, 16, 16, fill=with_a(C("#191A1C"), 240))
    a = s.array()
    shade_rows(a, 0, 0, 16, 16, (1.06, 0.94))
    for i in (0, 8):
        apply_mask(a, np.pad(np.ones((1, 16), np.uint8) * 255, ((i, 15 - i), (0, 0))),
                   (255, 255, 255, 10))
    return a


def advancement_window():
    """The advancement screen's frame.

    Vanilla keeps this canvas 256x256 but only ever blits the top-left 252x140
    window, and its *interior* is left transparent because the game stamps the
    tiled `advancements/backgrounds/*` art underneath. The frame itself is
    therefore reproducible by recolouring vanilla's chrome - which also keeps
    the band widths the tree layout is measured against - rather than by
    painting a fresh rectangle. Achievement captions are white, so the frame is
    dark.
    """
    a = load(LEG + "advancements/window.png")
    W, H = 252, 140
    al = a[:, :, 3].astype(np.float32) / 255.0
    band = np.zeros_like(al)
    band[1:18, 0:W] = 1.0          # tab strip
    band[128:139, 0:W] = 1.0       # bottom of the frame
    band[18:128, 0:9] = 1.0        # left frame edge
    band[18:128, 243:W] = 1.0      # right frame edge
    lum = (luminance(a) / 255.0)
    out = np.zeros_like(a)
    for ch, (lo, hi) in enumerate(zip(C("#131316"), C("#3E3E44"))):
        out[:, :, ch] = (lo + (hi - lo) * lum).astype(np.uint8)
    out[:, :, 3] = (al * 255.0 * band).astype(np.uint8)
    # accent rule separating the tab strip from the tree
    rule = np.zeros_like(al)
    rule[18, 0:W] = 1.0
    apply_mask(out, (rule * 255).astype(np.uint8), with_a(ACCENT, 200))
    # top highlight on the strip
    top = np.zeros_like(al)
    top[1, 0:W] = 1.0
    apply_mask(out, (top * 255).astype(np.uint8), (255, 255, 255, 60))
    return out


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------
GHOSTS = ("amethyst_shard", "axe", "banner", "banner_pattern", "boots",
          "brewing_fuel", "chestplate", "diamond", "dye", "emerald", "helmet",
          "hoe", "horse_armor", "ingot", "lapis_lazuli", "leggings",
          "llama_armor", "nautilus_armor", "nautilus_armor_inventory",
          "pickaxe", "potion", "quartz", "redstone_dust", "saddle", "shield",
          "shovel", "smithing_template_armor_trim",
          "smithing_template_netherite_upgrade", "spear", "sword")

# furnace-family machines share identical sprite geometry
MACHINES = ("furnace", "blast_furnace", "smoker")


def build_all(reader):
    set_reader(reader)
    out = {}

    # --- slot hint silhouettes ------------------------------------------
    # vanilla draws them in a dark grey; on our darker well they need to be
    # lighter to stay legible
    for name in GHOSTS:
        out[CON + "slot/%s.png" % name] = solid(
            CON + "slot/%s.png" % name, (176, 176, 182))

    # --- error / out-of-stock marks (grey glyph plus red text) -----------
    for base in ("anvil", "cartography_table", "grindstone", "smithing"):
        out[CON + base + "/error.png"] = remap(CON + base + "/error.png",
                                               "#2E2E33", "#8C8C94")
    out[CON + "villager/out_of_stock.png"] = remap(
        CON + "villager/out_of_stock.png", "#2E2E33", "#8C8C94")

    # --- anvil rename box ----------------------------------------------
    out[CON + "anvil/text_field.png"] = field(110, 16)
    out[CON + "anvil/text_field_disabled.png"] = field(110, 16, disabled=True)

    # --- beacon ---------------------------------------------------------
    out[CON + "beacon/button.png"] = beacon_button(22, "normal")
    out[CON + "beacon/button_highlighted.png"] = beacon_button(22, "highlighted")
    out[CON + "beacon/button_disabled.png"] = beacon_button(22, "disabled")
    out[CON + "beacon/button_selected.png"] = beacon_button(22, "selected")
    out[CON + "beacon/confirm.png"] = brighten(CON + "beacon/confirm.png", 1.2, 8)
    out[CON + "beacon/cancel.png"] = brighten(CON + "beacon/cancel.png", 1.2, 8)

    # --- smelting machines ---------------------------------------------
    for name in MACHINES:
        out[CON + name + "/burn_progress.png"] = remap(
            CON + name + "/burn_progress.png", ACCENT_DARK, ACCENT_LIGHT)
        out[CON + name + "/lit_progress.png"] = remap(
            CON + name + "/lit_progress.png", "#8A4A00", "#FFC24A")

    # --- brewing stand ---------------------------------------------------
    out[CON + "brewing_stand/brew_progress.png"] = remap(
        CON + "brewing_stand/brew_progress.png", ACCENT_DARK, ACCENT_LIGHT)
    out[CON + "brewing_stand/bubbles.png"] = remap(
        CON + "brewing_stand/bubbles.png", "#2E6E9E", "#9FD3F2")
    out[CON + "brewing_stand/fuel_length.png"] = remap(
        CON + "brewing_stand/fuel_length.png", "#7A3F00", "#FFB74D")

    # --- crafter --------------------------------------------------------
    out[CON + "crafter/disabled_slot.png"] = remap(
        CON + "crafter/disabled_slot.png", "#3A3A40", "#7E7E86")
    out[CON + "crafter/unpowered_redstone.png"] = remap(
        CON + "crafter/unpowered_redstone.png", "#4A4A50", "#9A9AA2")
    out[CON + "crafter/powered_redstone.png"] = brighten(
        CON + "crafter/powered_redstone.png", 1.15)

    # --- horse ----------------------------------------------------------
    out[CON + "horse/chest_slots.png"] = slot_grid(5, 3)

    # --- cartography ----------------------------------------------------
    # the map previews are real rendered art (and the locked padlock overlays it)
    for name in ("map", "scaled_map", "duplicated_map"):
        out[CON + "cartography_table/%s.png" % name] = load(
            CON + "cartography_table/%s.png" % name)
    out[CON + "cartography_table/locked.png"] = remap(
        CON + "cartography_table/locked.png", "#9A9AA2", "#FFFFFF")

    # --- loom -----------------------------------------------------------
    out[CON + "loom/pattern.png"] = choice(14, 14, "normal")
    out[CON + "loom/pattern_highlighted.png"] = choice(14, 14, "highlighted")
    out[CON + "loom/pattern_selected.png"] = choice(14, 14, "selected")
    out[CON + "loom/scroller.png"] = thumb(12, 15)
    out[CON + "loom/scroller_disabled.png"] = thumb_disabled(12, 15)
    out[CON + "loom/error.png"] = load(CON + "loom/error.png")  # fully empty

    # --- stonecutter ----------------------------------------------------
    out[CON + "stonecutter/recipe.png"] = choice(16, 18, "normal")
    out[CON + "stonecutter/recipe_highlighted.png"] = choice(16, 18, "highlighted")
    out[CON + "stonecutter/recipe_selected.png"] = choice(16, 18, "selected")
    out[CON + "stonecutter/scroller.png"] = thumb(12, 15)
    out[CON + "stonecutter/scroller_disabled.png"] = thumb_disabled(12, 15)

    # --- enchanting table ----------------------------------------------
    out[CON + "enchanting_table/enchantment_slot.png"] = ench_row(108, 19, "normal")
    out[CON + "enchanting_table/enchantment_slot_highlighted.png"] = ench_row(
        108, 19, "highlighted")
    out[CON + "enchanting_table/enchantment_slot_disabled.png"] = ench_row(
        108, 19, "disabled")
    for i in (1, 2, 3):
        out[CON + "enchanting_table/level_%d.png" % i] = brighten(
            CON + "enchanting_table/level_%d.png" % i, 1.15)
        out[CON + "enchanting_table/level_%d_disabled.png" % i] = load(
            CON + "enchanting_table/level_%d_disabled.png" % i)

    # --- villager -------------------------------------------------------
    out[CON + "villager/trade_arrow.png"] = remap(
        CON + "villager/trade_arrow.png", "#2E2E33", "#6E6E76")
    out[CON + "villager/trade_arrow_out_of_stock.png"] = remap(
        CON + "villager/trade_arrow_out_of_stock.png", "#2E2E33", "#6E6E76")
    out[CON + "villager/discount_strikethrough.png"] = load(
        CON + "villager/discount_strikethrough.png")
    out[CON + "villager/scroller.png"] = thumb(6, 27)
    out[CON + "villager/scroller_disabled.png"] = thumb_disabled(6, 27)
    out[CON + "villager/experience_bar_background.png"] = xp_bar(102, 5, "background")
    out[CON + "villager/experience_bar_current.png"] = xp_bar(102, 5, "current")
    out[CON + "villager/experience_bar_result.png"] = xp_bar(102, 5, "result")

    # --- gamemode switcher backdrop (legacy container path, not a sprite) -
    out[LEG + "container/gamemode_switcher.png"] = gamemode_switcher()

    # --- statistics -----------------------------------------------------
    out[SPR + "statistics/header.png"] = remap(
        SPR + "statistics/header.png", "#565660", "#9E9EA8")
    for name in ("sort_up", "sort_down"):
        out[SPR + "statistics/%s.png" % name] = remap(
            SPR + "statistics/%s.png" % name, "#9A9AA4", "#FFFFFF")
    for name in ("block_mined", "item_broken", "item_crafted", "item_dropped",
                 "item_picked_up", "item_used"):
        out[SPR + "statistics/%s.png" % name] = brighten(
            SPR + "statistics/%s.png" % name, 1.15, 8)

    # --- realm status chips ---------------------------------------------
    for name in ("open", "closed", "expired", "expires_soon"):
        out[SPR + "realm_status/%s.png" % name] = remap(
            SPR + "realm_status/%s.png" % name, "#8A8A92", "#FFFFFF")

    # --- animated icons (frame stacks recoloured uniformly) -------------
    out[SPR + "icon/music_notes.png"] = remap(
        SPR + "icon/music_notes.png", "#A6A6AE", "#FFFFFF")
    out[SPR + "icon/trial_available.png"] = brighten(
        SPR + "icon/trial_available.png", 1.1, 6)

    # --- hand-drawn art, kept verbatim ----------------------------------
    out[SPR + "friends/illustrations_00.png"] = load(
        SPR + "friends/illustrations_00.png")

    # --- advancement tree backdrop tiles --------------------------------
    out[LEG + "advancements/window.png"] = advancement_window()
    for name in ("adventure", "end", "husbandry", "nether", "stone"):
        out[LEG + "advancements/backgrounds/%s.png" % name] = adv_background()

    return out
