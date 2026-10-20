#!/usr/bin/env python3
"""Texture builders - part 1: widgets, HUD, slots, boss bars, bundles.

Every builder returns {path_relative_to_assets/minecraft: RGBA ndarray}.
Sizes are taken from vanilla (`tools/vanilla_manifest.json`); build.py asserts
that every generated sprite matches the vanilla dimensions exactly, because
Minecraft hard codes all GUI geometry in pixels.
"""
import numpy as np

from fluent import (ACCENT, ACCENT_DARK, ACCENT_HOVER, ACCENT_LIGHT, ACCENT_PALE,
                    ACRYLIC, ACRYLIC_EDGE, AIR, AIR_DEEP, ARMOR, ARMOR_DEEP, C,
                    EXP, EXP_DEEP, FOOD, FOOD_DEEP, HAIRLINE, HEALTH, HEALTH_DEEP,
                    INK, INK_DISABLED, INK_SOFT, INFO, INSUCCESS, MICA,
                    MICA_BRIGHT, MICA_DEEP, SHADOW, STROKE, SUCCESS, WARNING,
                    WHITE, Surface, acrylic_panel, apply_mask, blank,
                    bottom_line_mask, draw_heart, fluent_button, fluent_slot,
                    glyph_check, glyph_chevron, glyph_plus, glyph_search,
                    gradient, left_line_mask, mica_panel, noise, over,
                    right_line_mask, rounded_mask, rounded_ring_mask, scale_px,
                    shade_rows, top_line_mask, with_a)

P = "textures/gui/sprites/"


# --------------------------------------------------------------------------
# generic helpers
# --------------------------------------------------------------------------
def flat(w, h, color):
    return blank(w, h, color)


def tile(w, h, base, seed=0, radius=0, noise_amt=2.4, gain=(1.06, 0.95)):
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=base, radius=radius)
    a = s.array()
    shade_rows(a, 0, 0, w, h, gain)
    noise(a, 0, 0, w, h, noise_amt, seed=seed)
    return a


def control_track(w, h, radius=1, fill=(0, 0, 0, 44), top=(0, 0, 0, 74),
                  bottom=(255, 255, 255, 128), ring=None):
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=fill, radius=radius)
    a = s.array()
    apply_mask(a, top_line_mask(w, h, radius), top)
    apply_mask(a, bottom_line_mask(w, h, radius), bottom)
    if ring:
        apply_mask(a, rounded_ring_mask(w, h, radius, 1), ring)
    return a


def icon_frame(size, glyph, state="normal", shape="circle", tint=None):
    """Round/square Fluent icon button used by the server/world list chrome."""
    s = Surface(size, size, ss=4)
    pad = max(1.0, size * 0.06)
    r = (size / 2.0) if shape == "circle" else max(2.0, size * 0.22)
    if state == "disabled":
        s.rect(pad, pad, size - 2 * pad, size - 2 * pad,
               fill=(255, 255, 255, 46), radius=r)
    elif state == "highlighted":
        s.rect(pad, pad, size - 2 * pad, size - 2 * pad, fill=tint or ACCENT, radius=r)
    else:
        s.rect(pad, pad, size - 2 * pad, size - 2 * pad,
               fill=(255, 255, 255, 60), radius=r)
    a = s.array()
    apply_mask(a, rounded_ring_mask(size, size, r, 1),
               (255, 255, 255, 120) if state == "normal" else (255, 255, 255, 70))
    apply_mask(a, top_line_mask(size, size, r), (255, 255, 255, 90))
    gs = Surface(size, size, ss=4)
    glyph(gs, size)
    over(a, gs.array())
    return a


def glyph_arrow_up(s, c, size, color, width=None):
    w = width or max(1.2, size * 0.10)
    a = size * 0.30
    s.line([(c - a, c + a * 0.85), (c, c - a * 0.85), (c + a, c + a * 0.85)],
           color, w)
    return s


def glyph_arrow_down(s, c, size, color, width=None):
    w = width or max(1.2, size * 0.10)
    a = size * 0.30
    s.line([(c - a, c - a * 0.85), (c, c + a * 0.85), (c + a, c - a * 0.85)],
           color, w)
    return s


def glyph_x(s, c, size, color, width=None):
    w = width or max(1.2, size * 0.11)
    a = size * 0.27
    s.line([(c - a, c - a), (c + a, c + a)], color, w)
    s.line([(c - a, c + a), (c + a, c - a)], color, w)
    return s


def glyph_join(s, c, size, color):
    """Enter / join arrow."""
    a = size * 0.26
    s.line([(c - a, c - a), (c + a * 0.2, c)], color, max(1.2, size * 0.11))
    s.line([(c - a, c + a), (c + a * 0.2, c)], color, max(1.2, size * 0.11))
    s.line([(c + a * 0.55, c - a * 0.75), (c + a * 0.55, c + a * 0.75)],
           color, max(1.2, size * 0.11))
    return s


def glyph_warn(s, c, size, color):
    s.poly([(c, c - size * 0.34), (c + size * 0.34, c + size * 0.28),
            (c - size * 0.34, c + size * 0.28)], color)
    return s


def glyph_pickaxe(s, c, size, color):
    s.line([(c - size * 0.26, c + size * 0.30), (c + size * 0.10, c - size * 0.14)],
           color, max(1.2, size * 0.12))
    s.line([(c - size * 0.30, c - size * 0.10), (c + size * 0.10, c - size * 0.30)],
           color, max(1.0, size * 0.07))
    return s


# --------------------------------------------------------------------------
# 1. widgets
# --------------------------------------------------------------------------
def widgets():
    out = {}
    W, H = 200, 20
    # --- buttons (vanilla nine-slice border 3 / 1 for disabled) ---
    out[P + "widget/button.png"] = fluent_button(W, H, "normal")
    out[P + "widget/button_highlighted.png"] = fluent_button(W, H, "highlighted")
    out[P + "widget/button_disabled.png"] = fluent_button(W, H, "disabled", radius=1)
    out[P + "widget/realms_button.png"] = fluent_button(W, H, "normal")
    out[P + "widget/realms_button_highlighted.png"] = fluent_button(W, H, "highlighted")
    out[P + "widget/realms_button_disabled.png"] = fluent_button(W, H, "disabled",
                                                                radius=1)
    # --- slider track (border 1 => flat; label is white so the track stays dark) ---
    out[P + "widget/slider.png"] = control_track(W, H, 1, fill=(0, 0, 0, 118),
                                                 top=(0, 0, 0, 60),
                                                 bottom=(255, 255, 255, 44))
    sl = control_track(W, H, 1, fill=(15, 108, 189, 96), top=(0, 0, 0, 40),
                       bottom=(255, 255, 255, 60))
    apply_mask(sl, rounded_ring_mask(W, H, 1, 1), with_a(ACCENT_LIGHT, 170))
    out[P + "widget/slider_highlighted.png"] = sl
    # --- slider handle (slices l2 t2 r2 b3) ---
    def handle(state):
        s = Surface(8, H, ss=4)
        s.rect(0, 0, 8, H, fill=ACCENT, radius=2)
        a = s.array()
        apply_mask(a, rounded_ring_mask(8, H, 2, 1),
                   with_a(ACCENT_DARK, 210) if state == "normal" else WHITE)
        apply_mask(a, top_line_mask(8, H, 2), (255, 255, 255, 110))
        apply_mask(a, bottom_line_mask(8, H, 2), (0, 0, 0, 80))
        return a
    out[P + "widget/slider_handle.png"] = handle("normal")
    out[P + "widget/slider_handle_highlighted.png"] = handle("highlighted")
    # --- text field (EditBox text is 0xE0E0E0, so the field must stay dark) ---
    def field(state):
        s = Surface(W, H, ss=4)
        s.rect(0, 0, W, H, fill=(24, 24, 26, 214), radius=1)
        a = s.array()
        apply_mask(a, rounded_ring_mask(W, H, 1, 1), (0, 0, 0, 130))
        apply_mask(a, top_line_mask(W, H, 1), (0, 0, 0, 90))
        apply_mask(a, bottom_line_mask(W, H, 1),
                   ACCENT if state == "highlighted" else (255, 255, 255, 40))
        if state == "highlighted":
            apply_mask(a, rounded_ring_mask(W, H, 1, 1), with_a(ACCENT, 110))
        return a
    out[P + "widget/text_field.png"] = field("normal")
    out[P + "widget/text_field_highlighted.png"] = field("highlighted")
    out[P + "widget/preedit.png"] = field("highlighted")
    # --- tabs (slices l2 t2 r2 b0; unselected body is 20px tall, selected 24) ---
    def tab(selected, hover):
        s = Surface(130, 24, ss=4)
        body_h = 24 if selected else 20
        base = MICA if not selected else MICA_BRIGHT
        alpha = 236
        s.rect(0, 0, 130, body_h, fill=with_a(base, alpha), radius=2)
        a = s.array()
        shade_rows(a, 0, 0, 130, body_h, (1.02, 0.96))
        if hover:
            layer = flat(130, body_h, with_a(ACCENT, 22))
            layer[..., 3] = (layer[..., 3].astype(np.float32)
                             * (rounded_mask(130, body_h, 2) / 255.0)).astype(np.uint8)
            over(a, layer)
        # masks are authored on the visible body then padded to the full sprite,
        # so the unselected tab keeps its transparent bottom four rows
        def pad(m):
            return np.pad(m, ((0, a.shape[0] - m.shape[0]), (0, 0)))
        ring = pad(rounded_ring_mask(130, body_h, 2, 1))
        apply_mask(a, ring, STROKE)
        apply_mask(a, pad(top_line_mask(130, body_h, 2)),
                   ACCENT if selected else HAIRLINE)
        if not selected:
            apply_mask(a, pad(bottom_line_mask(130, body_h, 2)), (0, 0, 0, 60))
        else:
            apply_mask(a, pad(rounded_ring_mask(130, body_h, 2, 2)),
                       with_a(ACCENT, 70))
        return a
    out[P + "widget/tab.png"] = tab(False, False)
    out[P + "widget/tab_highlighted.png"] = tab(False, True)
    out[P + "widget/tab_selected.png"] = tab(True, False)
    out[P + "widget/tab_selected_highlighted.png"] = tab(True, True)
    # --- checkboxes ---
    out[P + "widget/checkbox.png"] = checkbox(False, False)
    out[P + "widget/checkbox_highlighted.png"] = checkbox(False, True)
    out[P + "widget/checkbox_selected.png"] = checkbox(True, False)
    out[P + "widget/checkbox_selected_highlighted.png"] = checkbox(True, True)
    # --- scrollers (accent thumb reads on both light and dark backdrops) ---
    out[P + "widget/scroller_background.png"] = control_track(6, 32, 1,
                                                             fill=(0, 0, 0, 40))
    sc = control_track(6, 32, 1, fill=ACCENT, top=(255, 255, 255, 70),
                       bottom=(0, 0, 0, 70))
    out[P + "widget/scroller.png"] = sc
    # --- lock buttons ---
    for name, locked, state in [("locked_button", True, "normal"),
                                ("locked_button_highlighted", True, "highlighted"),
                                ("locked_button_disabled", True, "disabled"),
                                ("unlocked_button", False, "normal"),
                                ("unlocked_button_highlighted", False, "highlighted"),
                                ("unlocked_button_disabled", False, "disabled")]:
        out[P + "widget/%s.png" % name] = padlock(20, locked, state)
    # --- cross button (14x14) ---
    for name, state in [("cross_button", "normal"),
                        ("cross_button_highlighted", "highlighted")]:
        out[P + "widget/%s.png" % name] = cross_button(14, state)
    # --- page back / forward (23x13) ---
    for name, direction, state in [("page_backward", "left", "normal"),
                                   ("page_backward_highlighted", "left", "highlighted"),
                                   ("page_forward", "right", "normal"),
                                   ("page_forward_highlighted", "right", "highlighted")]:
        out[P + "widget/%s.png" % name] = page_button(23, 13, direction, state)
    # --- slot frame: 3px hollow ring, sliced at 3px by vanilla ---
    out[P + "widget/slot_frame.png"] = slot_frame(80)
    return out


def checkbox(selected, hover):
    """Checkboxes live on dark list/tab backdrops, so the unchecked box is a
    dark well with a light hairline rather than a light chip."""
    s = Surface(18, 18, ss=4)
    if selected:
        tint = ACCENT_LIGHT if hover else ACCENT
        s.rect(0, 0, 18, 18, fill=tint, radius=2)
        a = s.array()
        apply_mask(a, top_line_mask(18, 18, 2), (255, 255, 255, 90))
        apply_mask(a, rounded_ring_mask(18, 18, 2, 1), with_a(ACCENT_DARK, 200))
        g = Surface(18, 18, ss=4)
        glyph_check(g, [(4.6, 9.4), (7.5, 12.4), (13.4, 5.4)], WHITE, 2.1)
        over(a, g.array())
        return pad(a, 20)
    fill = with_a(ACCENT, 70) if hover else (0, 0, 0, 120)
    s.rect(0, 0, 18, 18, fill=fill, radius=2)
    a = s.array()
    apply_mask(a, rounded_ring_mask(18, 18, 2, 1),
               with_a(ACCENT_LIGHT, 190) if hover else (255, 255, 255, 96))
    apply_mask(a, top_line_mask(18, 18, 2), (0, 0, 0, 60))
    return pad(a, 20)


def pad(a, size):
    out = blank(size, size)
    o = out
    y = (out.shape[0] - a.shape[0]) // 2
    x = (out.shape[1] - a.shape[1]) // 2
    o[y:y + a.shape[0], x:x + a.shape[1]] = a
    return out


def padlock(size, locked, state):
    s = Surface(size, size, ss=4)
    box = size - 2
    if state == "disabled":
        body_fill = (0, 0, 0, 60)
        ink = (255, 255, 255, 80)
    elif state == "highlighted":
        body_fill = with_a(ACCENT, 110)
        ink = WHITE
    else:
        body_fill = (0, 0, 0, 110)
        ink = (255, 255, 255, 235) if locked else ACCENT_LIGHT
    s.rect(1, 1, box, box, fill=body_fill, radius=2)
    a = s.array()
    apply_mask(a, rounded_ring_mask(size, size, 2, 1), (255, 255, 255, 60))
    apply_mask(a, bottom_line_mask(size, size, 2), (0, 0, 0, 70))
    g = Surface(size, size, ss=4)
    cx = size / 2.0
    # shackle
    g.line([(cx - 3.2, 8.5), (cx - 3.2, 6.6), (cx + 3.2, 6.6), (cx + 3.2, 8.5)],
           ink, 1.2)
    if locked:
        g.rect(cx - 4.4, 8.2, 8.8, 6.2, fill=ink, radius=1)
        g.pixel(cx - 0.5, 10.4, WHITE)
    else:
        g.line([(cx - 3.2, 6.6), (cx - 3.2, 5.2)], ink, 1.2)
        g.rect(cx - 0.2, 7.4, 4.6, 6.2, fill=ink, radius=1)
    over(a, g.array())
    return a


def cross_button(size, state):
    """Clear / close glyph; sits on dark text fields, so the ink is light."""
    s = Surface(size, size, ss=4)
    ink = ACCENT_LIGHT if state == "highlighted" else (255, 255, 255, 225)
    glyph_x(s, size / 2.0, size - 1.4, ink, 1.3)
    return s.array()


def page_button(w, h, direction, state):
    s = Surface(w, h, ss=4)
    ink = ACCENT_LIGHT if state == "highlighted" else (255, 255, 255, 232)
    glyph_chevron(s, w / 2.0, h / 2.0, h * 0.72, direction, ink, 1.6)
    return s.array()


def slot_frame(size):
    s = Surface(size, size, ss=4)
    s.rect(0, 0, size, size, fill=None, radius=3, outline=with_a(ACCENT_DARK, 150),
           ow=3)
    a = s.array()
    apply_mask(a, rounded_ring_mask(size, size, 3, 3), with_a(ACCENT, 40))
    return a


# --------------------------------------------------------------------------
# 2. container support sprites
# --------------------------------------------------------------------------
def container_sprites():
    out = {}
    out["textures/gui/sprites/container/slot.png"] = fluent_slot(18, 18)
    # slot highlight: soft accent wash behind / ring in front (nine-slice 4)
    out["textures/gui/sprites/container/slot_highlight_back.png"] = highlight(24, "back")
    out["textures/gui/sprites/container/slot_highlight_front.png"] = highlight(24, "front")
    out["textures/gui/sprites/container/bundle/slot_highlight_back.png"] = highlight(24, "back")
    out["textures/gui/sprites/container/bundle/slot_highlight_front.png"] = highlight(24, "front")
    out["textures/gui/sprites/container/bundle/slot_background.png"] = fluent_slot(24, 24,
                                                                                  radius=4)
    out["textures/gui/sprites/container/bundle/bundle_progressbar_border.png"] = \
        bordered_bar(12, 12)
    out["textures/gui/sprites/container/bundle/bundle_progressbar_fill.png"] = \
        filled_bar(6, 6, ACCENT_LIGHT)
    out["textures/gui/sprites/container/bundle/bundle_progressbar_full.png"] = \
        filled_bar(6, 6, ACCENT_LIGHT)
    for name, dark in [("effect_background", False), ("effect_background_ambient",
                                                      True)]:
        # the container copy is 32x32 with a 4px slice; the hud copy is 24x24
        out["textures/gui/sprites/container/inventory/%s.png" % name] = \
            effect_bg(32, dark)
        out["textures/gui/sprites/hud/%s.png" % name] = effect_bg(24, dark)
    return out


def highlight(size, layer):
    s = Surface(size, size, ss=4)
    if layer == "back":
        s.rect(0, 0, size, size, fill=(255, 255, 255, 60), radius=4)
    else:
        s.rect(0, 0, size, size, fill=(255, 255, 255, 0), radius=4,
               outline=(255, 255, 255, 150), ow=1)
    return s.array()


def bordered_bar(w, h):
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=(0, 0, 0, 60), radius=2)
    a = s.array()
    apply_mask(a, rounded_ring_mask(w, h, 2, 1), (0, 0, 0, 110))
    apply_mask(a, bottom_line_mask(w, h, 2), (255, 255, 255, 120))
    return a


def filled_bar(w, h, tint):
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=tint, radius=2)
    a = s.array()
    shade_rows(a, 0, 0, w, h, (1.15, 0.92))
    apply_mask(a, top_line_mask(w, h, 2), (255, 255, 255, 120))
    return a


def effect_bg(size, dark):
    base = (0, 0, 0, 120) if dark else (0, 0, 0, 58)
    s = Surface(size, size, ss=4)
    s.rect(0, 0, size, size, fill=base, radius=4)
    a = s.array()
    apply_mask(a, rounded_ring_mask(size, size, 4, 1), (255, 255, 255, 30))
    return a


# --------------------------------------------------------------------------
# 3. HUD
# --------------------------------------------------------------------------
def hud():
    out = {}
    out[P + "hud/hotbar.png"] = hotbar(182, 22)
    out[P + "hud/hotbar_selection.png"] = hotbar_selection(24, 23)
    out[P + "hud/hotbar_offhand_left.png"] = offhand(29, 24, "left")
    out[P + "hud/hotbar_offhand_right.png"] = offhand(29, 24, "right")
    out[P + "hud/hotbar_attack_indicator_background.png"] = attack_bar(18, 18, False)
    out[P + "hud/hotbar_attack_indicator_progress.png"] = attack_bar(18, 18, True)
    out[P + "hud/crosshair.png"] = crosshair(15)
    out[P + "hud/crosshair_attack_indicator_background.png"] = attack_bar(16, 4, False)
    out[P + "hud/crosshair_attack_indicator_progress.png"] = attack_bar(16, 4, True)
    out[P + "hud/crosshair_attack_indicator_full.png"] = attack_full(16)
    out[P + "hud/experience_bar_background.png"] = xp_bar(182, 5, None)
    out[P + "hud/experience_bar_progress.png"] = xp_bar(182, 5, EXP)
    out[P + "hud/jump_bar_background.png"] = xp_bar(182, 5, None)
    out[P + "hud/jump_bar_progress.png"] = xp_bar(182, 5, AIR)
    out[P + "hud/jump_bar_cooldown.png"] = xp_bar(182, 5, (120, 120, 120))
    for name, spec in HEARTS.items():
        out[P + "hud/heart/%s.png" % name] = heart_sprite(spec)
    for name, spec in FOODSTATES.items():
        out[P + "hud/%s.png" % name] = food_sprite(spec)
    for name, spec in ARMORSTATES.items():
        out[P + "hud/%s.png" % name] = armor_sprite(spec)
    for name, spec in AIRSTATES.items():
        out[P + "hud/%s.png" % name] = air_sprite(spec)
    out[P + "hud/locator_bar_background.png"] = locator_bg(12, 5)
    out[P + "hud/locator_bar_arrow_up.png"] = locator_arrow(7, 10, "up")
    out[P + "hud/locator_bar_arrow_down.png"] = locator_arrow(7, 10, "down")
    for i in range(4):
        out[P + "hud/locator_bar_dot/default_%d.png" % i] = locator_dot(9)
    out[P + "hud/locator_bar_dot/bowtie.png"] = locator_dot(9)
    return out


def hotbar(w, h):
    a = blank(w, h)
    acrylic_panel(a, 0, 0, w, h, radius=5, base=ACRYLIC, alpha=182)
    for i in range(9):
        over(a, fluent_slot(20, 20, surface="dark"), 1 + i * 20, 1)
    return a


def hotbar_selection(w, h):
    s = Surface(w, h, ss=4)
    s.rect(0.5, 0.5, w - 1, h - 1, fill=None, radius=5,
           outline=(255, 255, 255, 240), ow=2)
    a = s.array()
    glow = Surface(w, h, ss=4)
    glow.rect(0, 0, w, h, fill=None, radius=6,
              outline=(255, 255, 255, 70), ow=4)
    over(a, glow.array())
    return a


def offhand(w, h, side):
    a = blank(w, h)
    x0 = 0 if side == "left" else w - 22
    acrylic_panel(a, x0, 1, 22, 22, radius=4, base=ACRYLIC, alpha=182)
    over(a, fluent_slot(20, 20, surface="dark"), x0 + 1, 2)
    return a


def crosshair(size):
    s = Surface(size, size, ss=4)
    c = size / 2.0
    arm = size / 2.0 - 1.0
    col = (255, 255, 255, 235)
    s.line([(c, c - arm), (c, c + arm)], col, 1)
    s.line([(c - arm, c), (c + arm, c)], col, 1)
    s.pixel(c, c, (255, 255, 255, 255))
    return s.array()


def attack_bar(w, h, fill):
    s = Surface(w, h, ss=4)
    if fill:
        s.rect(0, 0, w, h, fill=ACCENT_LIGHT, radius=2)
        a = s.array()
        shade_rows(a, 0, 0, w, h, (1.12, 0.94))
        return a
    s.rect(0, 0, w, h, fill=(0, 0, 0, 130), radius=2)
    a = s.array()
    apply_mask(a, rounded_ring_mask(w, h, 2, 1), (255, 255, 255, 30))
    return a


def attack_full(size):
    s = Surface(size, size, ss=4)
    s.rect(0, 0, size, size, fill=(0, 0, 0, 130), radius=3)
    a = s.array()
    glyph_plus(s, size / 2.0, size / 2.0, size - 5.5, ACCENT_LIGHT, 1.4)
    over(a, s.array())
    return a


def xp_bar(w, h, tint):
    s = Surface(w, h, ss=4)
    if tint is None:
        s.rect(0, 0, w, h, fill=(0, 0, 0, 150), radius=1)
        a = s.array()
        apply_mask(a, rounded_ring_mask(w, h, 1, 1), (255, 255, 255, 34))
        return a
    s.rect(0, 0, w, h, fill=tint, radius=1)
    a = s.array()
    # left-to-right gradient so the cropped fill keeps a tonal ramp
    body = a[..., :3].astype(np.float32) * gradient(w, 0.86, 1.16)
    a[..., :3] = np.clip(body, 0, 255).astype(np.uint8)
    apply_mask(a, rounded_ring_mask(w, h, 1, 1), with_a(_deep(tint), 200))
    apply_mask(a, top_line_mask(w, h, 1), (255, 255, 255, 60))
    return a


def _deep(tint):
    return (max(0, tint[0] - 60), max(0, tint[1] - 60), max(0, tint[2] - 60), 255)


def locator_bg(w, h):
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=(0, 0, 0, 120), radius=1)
    a = s.array()
    apply_mask(a, top_line_mask(w, h, 1), (255, 255, 255, 40))
    return a


def locator_arrow(w, h, direction):
    s = Surface(w, h, ss=4)
    if direction == "up":
        pts = [(1, h * 0.75), (w / 2.0, h * 0.20), (w - 1, h * 0.75)]
    else:
        pts = [(1, h * 0.25), (w / 2.0, h * 0.80), (w - 1, h * 0.25)]
    s.line(pts, (255, 255, 255, 225), 1.6)
    return s.array()


def locator_dot(size):
    s = Surface(size, size, ss=4)
    s.ellipse(2, 2, size - 3, size - 3, fill=(255, 255, 255, 230))
    a = s.array()
    apply_mask(a, rounded_ring_mask(size, size, size // 2, 1), (0, 0, 0, 90))
    return a


# ---- hearts -------------------------------------------------------------
VARIANTS = {
    "": HEALTH,
    "absorbing_": C("#E8B93C"),
    "frozen_": AIR,
    "poisoned_": C("#8CD04A"),
    "withered_": C("#4A4A4A"),
    "vehicle_": C("#D96A3B"),
}
HEARTS = {}
for _prefix, _col in VARIANTS.items():
    if _prefix == "vehicle_":
        HEARTS["vehicle_container"] = ("container", _col, False, False)
        HEARTS["vehicle_full"] = ("full", _col, False, False)
        HEARTS["vehicle_half"] = ("half", _col, False, False)
        continue
    for _hard in (False, True):
        for _mode in ("full", "half"):
            for _blink in (False, True):
                key = "%s%s%s%s%s" % (_prefix, "hardcore_" if _hard else "", _mode,
                                      "_blinking" if _blink else "", "")
                HEARTS[key.replace("__", "_")] = (_mode, _col, _hard, _blink)
for _hard in (False, True):
    for _blink in (False, True):
        key = "container%s%s" % ("_hardcore" if _hard else "",
                                 "_blinking" if _blink else "")
        HEARTS[key] = ("container", HEALTH, _hard, _blink)


def heart_sprite(spec):
    mode, col, hard, blink = spec
    s = Surface(9, 9, ss=4)
    out = blank(9, 9)
    if mode == "container":
        draw_heart(s, 4.5, 4.35, 1.0, None,
                   (0, 0, 0, 190) if not hard else HEALTH_DEEP, 1.0)
        a = s.array()
        if hard:
            inner = Surface(9, 9, ss=4)
            draw_heart(inner, 4.5, 4.35, 0.46, HEALTH_DEEP, None, 0)
            over(a, inner.array())
        over(out, a)
        return out
    fill = col
    deep = _deep(col)
    if hard:
        fill = col
    draw_heart(s, 4.5, 4.35, 1.0, fill, (0, 0, 0, 130) if not hard else deep, 0.9)
    a = s.array()
    # specular highlight for a flat, modern read
    hl = Surface(9, 9, ss=4)
    hl.ellipse(2.0, 1.7, 2.2, 1.5, fill=(255, 255, 255, 110))
    hl.ellipse(6.6, 2.1, 1.4, 1.0, fill=(255, 255, 255, 70))
    over(a, hl.array())
    if hard:
        core = Surface(9, 9, ss=4)
        draw_heart(core, 4.5, 4.35, 0.42, deep, None, 0)
        over(a, core.array())
    if blink:
        flash = flat(9, 9, (255, 255, 255, 80))
        over(a, flash)
    a[:, 5:] = 0 if mode == "half" else a[:, 5:]
    over(out, a)
    return out


FOODSTATES = {}
for _mode in ("full", "half", "empty"):
    for _h in ("", "_hunger"):
        FOODSTATES["food_%s%s" % (_mode, _h)] = (_mode, _h == "_hunger")

ARMORSTATES = {"armor_%s" % m: m for m in ("full", "half", "empty")}
AIRSTATES = {"air": "full", "air_empty": "empty", "air_bursting": "burst"}


def food_sprite(spec):
    mode, hunger = spec
    out = blank(9, 9)
    s = Surface(9, 9, ss=4)
    col = FOOD_DEEP if hunger else FOOD
    deep = _deep(col)
    if mode == "empty":
        draw_food(s, 4.6, 4.6, None, (0, 0, 0, 170), 0.9)
    else:
        draw_food(s, 4.6, 4.6, col, (0, 0, 0, 120), 0.9)
        if mode == "full":
            hl = Surface(9, 9, ss=4)
            hl.ellipse(2.2, 1.8, 2.0, 1.4, fill=(255, 255, 255, 100))
            over(s.array(), hl.array())
            s = Surface(9, 9, ss=4)
            draw_food(s, 4.6, 4.6, None, None, 0.9)
            draw_food(s, 4.6, 4.6, col, (0, 0, 0, 120), 0.9)
            a = s.array()
            hl2 = Surface(9, 9, ss=4)
            hl2.ellipse(2.2, 1.8, 2.0, 1.4, fill=(255, 255, 255, 100))
            over(a, hl2.array())
            a[:, 5:] = 0 if mode == "half" else a[:, 5:]
            over(out, a)
            return out
    a = s.array()
    a[:, 5:] = 0 if mode == "half" else a[:, 5:]
    over(out, a)
    return out


def draw_food(s, cx, cy, fill, outline, w):
    """Modern rounded 'meat on the bone' glyph."""
    pts = [(cx - 3.6, cy - 3.4), (cx + 0.4, cy - 3.9), (cx + 3.4, cy - 1.0),
           (cx + 2.0, cy + 3.6), (cx - 1.6, cy + 3.4), (cx - 3.9, cy + 0.6)]
    s.poly(pts, fill)
    if outline is not None:
        s.line(pts + [pts[0]], outline, w)
    s.ellipse(cx + 1.4, cy - 3.6, 2.6, 2.4, fill=fill)
    return s


def armor_sprite(mode):
    out = blank(9, 9)
    s = Surface(9, 9, ss=4)
    pts = [(1.6, 1.6), (7.4, 1.6), (7.9, 4.4), (6.4, 7.8), (4.5, 8.3),
           (2.6, 7.8), (1.1, 4.4)]
    if mode == "empty":
        s.poly(pts, None)
        s.line(pts + [pts[0]], (0, 0, 0, 175), 0.9)
    else:
        s.poly(pts, ARMOR)
        s.line(pts + [pts[0]], (0, 0, 0, 130), 0.9)
        inner = Surface(9, 9, ss=4)
        inner.poly([(4.5, 2.2), (6.6, 2.2), (7.0, 4.4), (4.5, 7.2), (2.0, 4.4),
                    (2.4, 2.2)], ARMOR_DEEP)
        over(s.array(), inner.array())
        s2 = Surface(9, 9, ss=4)
        s2.poly(pts, ARMOR)
        s2.line(pts + [pts[0]], (0, 0, 0, 130), 0.9)
        a = s2.array()
        over(a, inner.array())
        s = None
        a[:, 5:] = 0 if mode == "half" else a[:, 5:]
        over(out, a)
        return out
    a = s.array()
    a[:, 5:] = 0 if mode == "half" else a[:, 5:]
    over(out, a)
    return out


def air_sprite(mode):
    out = blank(9, 9)
    s = Surface(9, 9, ss=4)
    if mode == "empty":
        s.ellipse(0.8, 0.8, 7.4, 7.4, fill=None, outline=(0, 0, 0, 175), ow=0.9)
    else:
        s.ellipse(0.8, 0.8, 7.4, 7.4, fill=AIR)
        a = s.array()
        apply_mask(a, rounded_ring_mask(9, 9, 5, 1), with_a(AIR_DEEP, 190))
        hl = Surface(9, 9, ss=4)
        hl.ellipse(2.0, 1.8, 2.4, 1.8, fill=(255, 255, 255, 190))
        over(a, hl.array())
        if mode == "burst":
            b = Surface(9, 9, ss=4)
            glyph_plus(b, 7.2, 2.0, 3.2, (255, 255, 255, 200), 1.0)
            over(a, b.array())
        over(out, a)
        return out
    over(out, s.array())
    return out


# --------------------------------------------------------------------------
# 4. boss bars
# --------------------------------------------------------------------------
BOSS_COLORS = {
    "blue": C("#1F6FEB"),
    "green": C("#107C10"),
    "pink": C("#E3008C"),
    "purple": C("#8764B8"),
    "red": INSUCCESS,
    "white": C("#E5E5E5"),
    "yellow": C("#F2C811"),
}


def boss_bars():
    out = {}
    for name, col in BOSS_COLORS.items():
        out[P + "boss_bar/%s_background.png" % name] = boss_bar(182, 5, None)
        out[P + "boss_bar/%s_progress.png" % name] = boss_bar(182, 5, col)
    for n in (6, 10, 12, 20):
        out[P + "boss_bar/notched_%d_background.png" % n] = \
            boss_bar(182, 5, None, notches=n)
        out[P + "boss_bar/notched_%d_progress.png" % n] = \
            boss_bar(182, 5, C("#E3008C"), notches=n)
    return out


def boss_bar(w, h, tint, notches=0):
    s = Surface(w, h, ss=4)
    if tint is None:
        s.rect(0, 0, w, h, fill=(0, 0, 0, 150), radius=1)
        a = s.array()
        apply_mask(a, rounded_ring_mask(w, h, 1, 1), (255, 255, 255, 40))
        apply_mask(a, top_line_mask(w, h, 1), (0, 0, 0, 60))
    else:
        s.rect(0, 0, w, h, fill=tint, radius=1)
        a = s.array()
        body = a[..., :3].astype(np.float32) * gradient(w, 0.92, 1.10)
        a[..., :3] = np.clip(body, 0, 255).astype(np.uint8)
        apply_mask(a, top_line_mask(w, h, 1), (255, 255, 255, 70))
    if notches:
        for i in range(1, notches):
            a[:, scale_px(i * w / notches)] = (0, 0, 0, 0)
    return a


# --------------------------------------------------------------------------
# 5. creative inventory tabs
# --------------------------------------------------------------------------
def creative_tabs():
    out = {}
    for i in range(1, 8):
        for pos in ("top", "bottom"):
            for sel in ("selected", "unselected"):
                name = ("textures/gui/sprites/container/creative_inventory/"
                        "tab_%s_%s_%d.png" % (pos, sel, i))
                out[name] = creative_tab(pos, sel == "selected")
    out["textures/gui/sprites/container/creative_inventory/scroller.png"] = \
        control_track(12, 15, 1, fill=(0, 0, 0, 108), top=(255, 255, 255, 46))
    out["textures/gui/sprites/container/creative_inventory/scroller_disabled.png"] = \
        control_track(12, 15, 1, fill=(0, 0, 0, 40))
    return out


def creative_tab(pos, selected):
    """26x32 creative tab; the free edge carries the accent indicator and the
    attaching edge is squared so the tab reads as docked to the panel."""
    w, h = 26, 32
    r = 4
    fill = with_a(MICA_BRIGHT, 242) if selected else with_a(MICA_DEEP, 208)
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=fill, radius=r)
    a = s.array()
    shade_rows(a, 0, 0, w, h, (1.03, 0.96))
    apply_mask(a, rounded_ring_mask(w, h, r, 1), STROKE)
    free_top = pos == "top"
    over(a, flat(w, 4, fill), 0, h - 4 if free_top else 0)
    apply_mask(a, (top_line_mask if free_top else bottom_line_mask)(w, h, r),
               ACCENT if selected else HAIRLINE)
    if selected:
        apply_mask(a, rounded_ring_mask(w, h, r, 2), with_a(ACCENT, 60))
    return a
