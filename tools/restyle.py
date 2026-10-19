#!/usr/bin/env python3
"""Fluent re-tinting of vanilla artwork.

Why this module exists
----------------------
Minecraft's GUI textures fall into two classes:

  * **chrome** - nine-slice panels, buttons, bars, slots, tabs. These are big,
    flat, geometrically simple surfaces, and redrawing them is exactly how a
    resource pack modernises the interface. They are produced by the other
    builder modules.

  * **art** - hundreds of tiny glyphs: 46 heart variants, food/armour/air
    pips, drown icons, ping bars, notification badges, list action arrows,
    recipe overlays, statistic icons, the advancement tree. These are pixel art
    whose *shape* carries the meaning. Redrawing them by hand risks wrecking
    that meaning (a "glyph overlay" silently becomes a filled tile, a bubble
    loses its hollow centre), while re-tinting them cannot: the silhouette is
    copied pixel-for-pixel from vanilla and only the colour changes.

So for the art class the pack **keeps vanilla's silhouette and alpha exactly**
and maps vanilla's hues onto the Fluent palette: greys go through a cool
neutral ramp, saturated pixels through the matching Fluent family ramp
(health / food / armour / air / experience / warning). Shading inside a glyph
survives, because each family ramp is sampled by the pixel's own luminance.

Matching happens on the path relative to `textures/gui/`, in order, first
pattern wins. `mine` means "keep the redrawn texture" and is the default for
anything unmatched, so a builder's deliberate redesign is never silently
discarded. `keep` means "leave vanilla art untouched" (maps, illustrations -
art whose colour *is* the content), and `restyle:x` selects a palette family.
"""
import numpy as np

from fluent import (ACCENT, ACCENT_DARK, ACCENT_LIGHT, AIR, AIR_DEEP, ARMOR,
                    ARMOR_DEEP, C, EXP, EXP_DEEP, FOOD, FOOD_DEEP, HEALTH,
                    HEALTH_DEEP, WARNING)

# --------------------------------------------------------------------------
# palette families: (deep, base, highlight)
# --------------------------------------------------------------------------
FAMILIES = {
    "neutral": (C("#0E0E10"), C("#8A8A93"), C("#FFFFFF")),
    "accent": (ACCENT_DARK, ACCENT, ACCENT_LIGHT),
    "health": (HEALTH_DEEP, HEALTH, C("#FFA8A2")),
    "food": (FOOD_DEEP, FOOD, C("#FFD9A0")),
    "absorb": (C("#8A6A00"), C("#FFD34E"), C("#FFF0B8")),
    "armor": (ARMOR_DEEP, ARMOR, C("#D6E1EC")),
    "air": (AIR_DEEP, AIR, C("#B8E8FF")),
    "exp": (EXP_DEEP, EXP, C("#B6F09A")),
    "warning": (C("#7A2E00"), WARNING, C("#FFC98A")),
}

# hue centres (degrees) used by `auto`
HUE_CENTRES = [("health", 0), ("food", 32), ("exp", 110), ("air", 200),
               ("accent", 240), ("health", 330)]

POLICY = [
    # ---- art whose colour is its content: untouched ----------------------
    ("sprites/friends/illustrations", "keep"),
    ("sprites/container/cartography_table/map", "keep"),
    ("sprites/container/cartography_table/scaled_map", "keep"),
    ("sprites/container/cartography_table/duplicated_map", "keep"),
    ("sprites/container/enchanting_table/level_", "keep"),
    ("sprites/recipe_book/crafting_overlay", "keep"),
    ("sprites/recipe_book/overlay_recipe", "keep"),
    ("sprites/toast/wooden_planks", "keep"),

    # ---- surfaces worth redrawing ----------------------------------------
    # Big, flat, geometric: panels, bars, wells, buttons. Redrawing these is
    # what makes the interface read as Fluent rather than merely recoloured.
    ("sprites/widget/button", "mine"),
    ("sprites/widget/slider", "mine"),
    ("sprites/widget/text_field", "mine"),
    ("sprites/widget/checkbox", "mine"),
    ("sprites/widget/locked_button", "mine"),
    ("sprites/widget/unlocked_button", "mine"),
    ("sprites/widget/slot_frame", "mine"),
    ("sprites/widget/scroller.png", "mine"),

    ("sprites/hud/hotbar.png", "mine"),
    ("sprites/hud/hotbar_selection", "mine"),
    ("sprites/hud/hotbar_offhand", "mine"),
    ("sprites/hud/experience_bar", "mine"),
    ("sprites/hud/jump_bar", "mine"),
    ("sprites/hud/effect_background", "mine"),

    ("sprites/container/slot.png", "mine"),
    ("sprites/container/horse/chest_slots", "mine"),
    ("sprites/container/loom/pattern", "mine"),
    ("sprites/container/loom/scroller", "mine"),
    ("sprites/container/stonecutter/recipe", "mine"),
    ("sprites/container/stonecutter/scroller", "mine"),
    ("sprites/container/enchanting_table/enchantment_slot", "mine"),

    ("sprites/tooltip/background", "mine"),
    ("sprites/popup", "mine"),
    ("sprites/menu_background", "mine"),
    ("sprites/menu_list_background", "mine"),
    ("sprites/social_interactions/background", "mine"),
    ("sprites/dialog/", "mine"),
    ("sprites/friends/background", "mine"),
    ("sprites/friends/button", "mine"),
    ("sprites/friends/toast_background", "mine"),
    ("sprites/toast/advancement", "mine"),
    ("sprites/toast/system", "mine"),
    ("sprites/toast/tutorial", "mine"),
    ("sprites/toast/now_playing", "mine"),
    ("sprites/boss_bar/notched_", "restyle:auto"),
    ("sprites/boss_bar/", "mine"),
    ("sprites/advancements/", "mine"),

    # ---- HUD glyphs: hearts, food, armour and air -------------------------
    ("sprites/hud/heart/frozen", "restyle:air"),
    ("sprites/hud/heart/poisoned", "restyle:exp"),
    ("sprites/hud/heart/withered", "restyle:neutral"),
    ("sprites/hud/heart/absorbing", "restyle:absorb"),
    ("sprites/hud/heart/vehicle", "restyle:armor"),
    ("sprites/hud/heart/container", "restyle:neutral"),
    ("sprites/hud/heart/", "restyle:health"),
    ("sprites/hud/food_", "restyle:food"),
    ("sprites/hud/armor_", "restyle:armor"),
    ("sprites/hud/air", "restyle:air"),
    ("sprites/hud/locator_bar_dot", "restyle:auto"),
    ("sprites/hud/locator_bar_arrow", "restyle:auto"),
    ("sprites/hud/crosshair", "restyle:neutral"),
    ("sprites/hud/hotbar_attack_indicator", "restyle:accent"),

    # ---- icon libraries: shape is the message -----------------------------
    # Redrawing these bought nothing (they sit on padded canvases, or are
    # outlines the game measures against) and cost silhouette fidelity.
    ("sprites/icon/", "restyle:neutral"),
    ("sprites/pause_menu/", "restyle:neutral"),
    ("sprites/statistics/", "restyle:neutral"),
    ("sprites/spectator/", "restyle:auto"),
    ("sprites/server_list/", "restyle:auto"),
    ("sprites/transferable_list/", "restyle:auto"),
    ("sprites/world_list/", "restyle:auto"),
    ("sprites/player_list/", "restyle:auto"),
    ("sprites/realm_status/", "restyle:auto"),
    ("sprites/recipe_book/", "restyle:auto"),
    ("sprites/notification/", "restyle:health"),
    ("sprites/friends/", "restyle:auto"),
    ("sprites/pending_invite/", "restyle:auto"),
    ("sprites/social_interactions/", "restyle:auto"),
    ("sprites/toast/mouse", "restyle:neutral"),
    ("sprites/toast/right_click", "restyle:neutral"),
    ("sprites/toast/social_interactions", "restyle:neutral"),
    ("sprites/toast/recipe_book", "restyle:neutral"),
    ("sprites/toast/tree", "restyle:neutral"),

    # ---- overlays and misc chrome ----------------------------------------
    ("sprites/widget/cross_button", "restyle:neutral"),
    ("sprites/widget/page_", "restyle:neutral"),
    ("sprites/widget/tab", "restyle:neutral"),
    ("sprites/widget/scroller_background", "restyle:neutral"),
    ("sprites/container/slot_highlight_front", "restyle:accent"),
    ("sprites/container/slot_highlight", "restyle:neutral"),
    ("sprites/container/bundle", "restyle:neutral"),
    ("sprites/container/creative_inventory/scroller_disabled", "restyle:neutral"),
    ("sprites/container/villager/experience_bar", "restyle:auto"),
    ("sprites/tooltip/frame", "restyle:neutral"),
    ("header_separator.png", "restyle:neutral"),
    ("footer_separator.png", "restyle:neutral"),
    ("inworld_header_separator.png", "restyle:neutral"),
    ("inworld_footer_separator.png", "restyle:neutral"),
    ("tab_header_background.png", "restyle:neutral"),

    # ---- anything else keeps whatever the builders drew --------------------
    ("sprites/", "mine"),
]



def _rgb(color):
    return np.array(C(color)[:3] if isinstance(color, str) else color[:3], np.float32)


def mode(path):
    """Resolve the policy for a path relative to `assets/minecraft/`."""
    key = path[len("textures/gui/"):] if path.startswith("textures/gui/") else path
    for prefix, action in POLICY:
        if key.startswith(prefix):
            return action
    return "mine"


# --------------------------------------------------------------------------
# recolouring
# --------------------------------------------------------------------------
def _ramp(family, t):
    """Sample a family ramp at luminance `t` (0..1): deep -> base -> highlight."""
    deep, base, high = (_rgb(c) for c in FAMILIES[family])
    t = np.clip(t, 0, 1)[..., None]
    lo = deep * (1 - t / 0.5) + base * (t / 0.5)
    hi = base * (1 - (t - 0.5) / 0.5) + high * ((t - 0.5) / 0.5)
    return np.where(t < 0.5, lo, hi)


def dominant_family(a):
    """Pick the Fluent family matching a sprite's prevailing hue."""
    op = a[:, :, 3] > 100
    if op.sum() == 0:
        return "neutral"
    px = a[op][:, :3].astype(np.int32) / 255.0
    mx, mn = px.max(axis=1), px.min(axis=1)
    sat = mx - mn
    if np.median(sat) < 0.16:
        return "neutral"
    hue = _hue(px)
    h = float(np.median(hue[sat > 0.16]))
    best, dist = "neutral", 1e9
    for fam, centre in HUE_CENTRES:
        d = abs((h - centre + 180) % 360 - 180)
        if d < dist:
            best, dist = fam, d
    return best


def _hue(px):
    mx = px.max(axis=1)
    mn = px.min(axis=1)
    d = np.where(mx - mn == 0, 1, mx - mn)
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    h = np.zeros_like(r)
    m = mx == r
    h[m] = ((g[m] - b[m]) / d[m]) % 6
    m = mx == g
    h[m] = ((b[m] - r[m]) / d[m]) + 2
    m = mx == b
    h[m] = ((r[m] - g[m]) / d[m]) + 4
    return (h * 60) % 360


def restyle(path, a, action=None):
    """Return a Fluent re-tint of `a` (vanilla art) with an identical alpha
    mask. `action` overrides the policy lookup when supplied."""
    action = action or mode(path)
    if action == "mine":
        return None
    if action == "keep":
        return a.copy()
    family = action.split(":", 1)[1]
    if family == "auto":
        family = dominant_family(a)

    out = a.copy()
    px = a[:, :, :3].astype(np.float32) / 255.0
    luma = 0.299 * px[..., 0] + 0.587 * px[..., 1] + 0.114 * px[..., 2]
    sat = px.max(axis=2) - px.min(axis=2)

    # greys keep their relative shading through the cool Fluent neutral ramp;
    # saturated pixels go through the chosen family ramp
    tinted = _ramp(family, luma)
    grey = _ramp("neutral", luma)
    mask = (sat < 0.16)[..., None]
    rgb = np.where(mask, grey, tinted)
    # a saturated-but-family-lost (e.g. white highlight) pixel stays bright
    out[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return out
