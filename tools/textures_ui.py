#!/usr/bin/env python3
"""Texture builders - part 2: icons, menu chrome, overlays, toasts, social.

Everything in here renders on top of a *dark* backdrop because Minecraft draws
menu, list, tooltip, toast and advancement text in white. Only the written-book
screen and container screens get light surfaces (see textures.py / containers.py).
"""
import numpy as np

from fluent import (ACCENT, ACCENT_DARK, ACCENT_LIGHT, ACRYLIC, ACRYLIC_EDGE,
                    ACRYLIC_SHADE, C, HAIRLINE, INK, INSUCCESS, MICA_BRIGHT,
                    PAPER, PAPER_EDGE, SUCCESS, SURFACE_DARK, SURFACE_DARKER,
                    WARNING, WHITE, Surface, apply_mask, blank,
                    bottom_line_mask, glyph_check, glyph_chevron, glyph_plus,
                    left_line_mask, noise, over, right_line_mask, rounded_mask,
                    rounded_ring_mask, shade_rows, top_line_mask, with_a)

P = "textures/gui/sprites/"
INK_LIGHT = (255, 255, 255, 238)
INK_DIM = (255, 255, 255, 150)


def flat(w, h, color):
    return np.zeros((h, w, 4), np.uint8) + np.array(color, np.uint8)



def glyph_arrow(s, cx, cy, a, direction, color, width=1.4):
    if direction in ("up", "down"):
        sgn = -1 if direction == "up" else 1
        s.line([(cx - a, cy + sgn * a * 0.7), (cx, cy - sgn * a * 0.7),
                (cx + a, cy + sgn * a * 0.7)], color, width)
    else:
        sgn = -1 if direction == "left" else 1
        s.line([(cx + sgn * a * 0.7, cy - a), (cx - sgn * a * 0.7, cy),
                (cx + sgn * a * 0.7, cy + a)], color, width)
    return s


def glyph_person(s, cx, cy, r, color, width=1.3, shoulders=True):
    s.ellipse(cx - r * 0.5, cy - r, r, r, fill=color)
    if shoulders:
        s.line([(cx - r, cy + r * 1.15), (cx - r * 0.55, cy + r * 0.15),
                (cx + r * 0.55, cy + r * 0.15), (cx + r, cy + r * 1.15)],
               color, width)
    return s


def glyph_x(s, c, size, color, width=None):
    w = width or max(1.2, size * 0.11)
    a = size * 0.27
    s.line([(c - a, c - a), (c + a, c + a)], color, w)
    s.line([(c - a, c + a), (c + a, c - a)], color, w)
    return s


def glyph_bars(s, w, h, level, color, dim):
    """Signal strength bars; level 0..5, 5 = strongest."""
    n = 5
    gap = max(0.5, w / 24.0)
    bw = (w - gap * (n + 1)) / n
    for i in range(n):
        bh = h * (0.30 + 0.70 * (i / (n - 1)))
        x = gap + i * (bw + gap)
        y = h - bh
        col = color if i < level else dim
        s.rect(x, y, bw, bh, fill=col, radius=0.5)
    return s


# --------------------------------------------------------------------------
# icons
# --------------------------------------------------------------------------
ICON_SIZES = {
    "accessibility": (15, 15), "chat_modified": (9, 9), "checkmark": (9, 8),
    "draft_report": (15, 15), "info": (20, 20), "invite": (14, 14),
    "language": (15, 15), "link": (15, 15), "news": (14, 14),
    "new_realm": (40, 20), "ping_1": (10, 8), "ping_2": (10, 8),
    "ping_3": (10, 8), "ping_4": (10, 8), "ping_5": (10, 8),
    "ping_unknown": (10, 8), "search": (12, 12), "unseen_notification": (10, 10),
    "video_link": (15, 15),
}


def icons():
    out = {}
    out[P + "icon/checkmark.png"] = icon_checkmark(9, 8)
    out[P + "icon/search.png"] = icon_search(12)
    out[P + "icon/info.png"] = icon_info(20)
    out[P + "icon/link.png"] = icon_link(15, False)
    out[P + "icon/link_highlighted.png"] = icon_link(15, True)
    out[P + "icon/news.png"] = icon_news(14)
    out[P + "icon/accessibility.png"] = icon_accessibility(15)
    out[P + "icon/language.png"] = icon_language(15)
    out[P + "icon/invite.png"] = icon_invite(14)
    out[P + "icon/new_realm.png"] = icon_new_realm(40, 20)
    out[P + "icon/draft_report.png"] = icon_flag(15)
    out[P + "icon/chat_modified.png"] = icon_pencil(9)
    out[P + "icon/unseen_notification.png"] = icon_dot(10)
    out[P + "icon/video_link.png"] = icon_camera(15, False)
    out[P + "icon/video_link_highlighted.png"] = icon_camera(15, True)
    for i in range(1, 6):
        out[P + "icon/ping_%d.png" % i] = ping_bars(10, 8, i)
    out[P + "icon/ping_unknown.png"] = ping_unknown(10, 8)
    # notification pips
    for i in range(1, 6):
        out[P + "notification/%d.png" % i] = notif_pip(8, i)
    out[P + "notification/more.png"] = notif_pip(8, 6)
    return out


def icon_checkmark(w, h):
    """Recipe-book 'craftable' tick; white ink with a dark keyline so it reads
    over both the pale overlay and busy item icons."""
    pts = [(1.2, 4.0), (3.4, 6.4), (7.8, 0.9)]
    s = Surface(w, h, ss=4)
    s.line(pts, (0, 0, 0, 180), 2.4)
    s2 = Surface(w, h, ss=4)
    s2.line(pts, (255, 255, 255, 255), 1.4)
    a = s.array()
    over(a, s2.array())
    return a


def icon_search(size):
    s = Surface(size, size, ss=4)
    s.ellipse(0.7, 0.7, size - 6.4, size - 6.4, fill=None, outline=INK_LIGHT,
              ow=1.3)
    s.line([(size - 5.4, size - 5.4), (size - 1.2, size - 1.2)], INK_LIGHT, 1.3)
    return s.array()


def icon_info(size):
    s = Surface(size, size, ss=4)
    s.ellipse(0.8, 0.8, size - 1.6, size - 1.6, fill=with_a(ACCENT, 235))
    s.ellipse(0.8, 0.8, size - 1.6, size - 1.6, fill=None,
              outline=(255, 255, 255, 150), ow=1.0)
    c = size / 2.0
    s.ellipse(c - 1.0, c - 5.4, 2.0, 2.0, fill=WHITE)
    s.rect(c - 1.0, c - 1.6, 2.0, 6.2, fill=WHITE, radius=1)
    return s.array()


def icon_link(size, hover):
    s = Surface(size, size, ss=4)
    col = ACCENT_LIGHT if hover else INK_LIGHT
    s.line([(3.0, size - 3.2), (size - 3.2, 3.0)], col, 1.6)
    s.ellipse(0.6, 0.6, 5.6, 5.6, fill=None, outline=col, ow=1.3)
    s.ellipse(size - 6.2, size - 6.2, 5.6, 5.6, fill=None, outline=col, ow=1.3)
    return s.array()


def icon_news(size):
    s = Surface(size, size, ss=4)
    s.rect(0.8, 1.6, size - 1.6, size - 3.2, fill=(255, 255, 255, 235), radius=1)
    s.rect(2.6, 4.2, size - 5.0, 1.4, fill=INK)
    s.rect(2.6, 7.4, size - 5.0, 1.4, fill=INK)
    return s.array()


def icon_accessibility(size):
    s = Surface(size, size, ss=4)
    c = size / 2.0
    s.ellipse(c - 1.4, 0.4, 2.8, 2.8, fill=INK_LIGHT)
    s.line([(c, 4.4), (c, 9.4)], INK_LIGHT, 1.5)
    s.line([(c - 4.4, 6.0), (c + 4.4, 6.0)], INK_LIGHT, 1.5)
    s.line([(c, 9.4), (c - 3.4, size - 1.0)], INK_LIGHT, 1.4)
    s.line([(c, 9.4), (c + 3.4, size - 1.0)], INK_LIGHT, 1.4)
    return s.array()


def icon_language(size):
    s = Surface(size, size, ss=4)
    s.ellipse(0.7, 0.7, size - 1.4, size - 1.4, fill=None, outline=INK_LIGHT,
              ow=1.2)
    c = size / 2.0
    s.line([(0.9, c), (size - 0.9, c)], INK_LIGHT, 1.0)
    s.ellipse(c - 3.0, 0.7, 6.0, size - 1.4, fill=None, outline=INK_LIGHT, ow=1.0)
    return s.array()


def icon_invite(size):
    s = Surface(size, size, ss=4)
    s.rect(0.5, 0.5, size - 1, size - 1, fill=with_a(ACCENT, 210), radius=3)
    glyph_plus(s, size / 2.0, size / 2.0, size - 6.0, WHITE, 1.5)
    return s.array()


def icon_new_realm(w, h):
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=ACCENT, radius=3)
    a = s.array()
    apply_mask(a, rounded_ring_mask(w, h, 3, 1), with_a(ACCENT_DARK, 200))
    apply_mask(a, top_line_mask(w, h, 3), (255, 255, 255, 70))
    glyph_plus(s, w / 2.0, h / 2.0, 9.0, WHITE, 1.6)
    over(a, s.array())
    return a


def icon_flag(size):
    s = Surface(size, size, ss=4)
    s.line([(2.4, 0.8), (2.4, size - 0.8)], INK_LIGHT, 1.3)
    s.poly([(3.4, 1.2), (size - 1.2, 3.4), (3.4, 6.4)], WARNING)
    return s.array()


def icon_pencil(size):
    s = Surface(size, size, ss=4)
    s.line([(1.2, size - 1.2), (size - 1.6, 1.4)], (255, 255, 255, 225), 1.6)
    s.line([(1.2, size - 1.2), (2.6, size - 2.6)], (0, 0, 0, 140), 1.0)
    return s.array()


def icon_dot(size):
    s = Surface(size, size, ss=4)
    s.ellipse(0.6, 0.6, size - 1.2, size - 1.2, fill=WARNING)
    return s.array()


def icon_camera(size, hover):
    s = Surface(size, size, ss=4)
    col = ACCENT_LIGHT if hover else INK_LIGHT
    s.rect(0.6, 3.2, size - 1.2, 8.6, fill=col, radius=1.4)
    s.poly([(size - 3.4, 4.6), (size - 0.8, 3.0), (size - 0.8, 11.8),
            (size - 3.4, 10.2)], col)
    return s.array()


def ping_bars(w, h, level):
    s = Surface(w, h, ss=4)
    col = SUCCESS if level >= 4 else (WARNING if level >= 3 else INSUCCESS)
    glyph_bars(s, w - 0.6, h - 0.4, level, col, (255, 255, 255, 60))
    return s.array()


def ping_unknown(w, h):
    s = Surface(w, h, ss=4)
    c = w / 2.0
    s.line([(c - 2.2, 2.2), (c + 1.0, 2.2), (c + 2.2, 4.0), (c, 5.6)], 
           INK_LIGHT, 1.4)
    s.ellipse(c - 0.7, 6.4, 1.5, 1.5, fill=INK_LIGHT)
    return s.array()


def notif_pip(size, count):
    """Accent pips: count 1..5, 6 = 'more' (ellipsis)."""
    s = Surface(size, size, ss=4)
    if count == 6:
        for i in range(3):
            s.ellipse(1.0 + i * 2.2, size / 2.0 - 1.0, 1.8, 1.8, fill=WARNING)
        return s.array()
    order = [(0, 0), (1, 0), (0, 1), (1, 1), (0.5, 0.5)]
    dot = 2.6 if count < 4 else 2.2
    for i in range(count):
        cx = order[i][0] * (size / 2.0) if i < 4 else size / 4.0
        cy = order[i][1] * (size / 2.0) if i < 4 else size / 4.0
        s.ellipse(cx + 0.6, cy + 0.6, dot, dot, fill=WARNING)
    return s.array()


# --------------------------------------------------------------------------
# menu chrome
# --------------------------------------------------------------------------
def menus():
    out = {}
    out["textures/gui/menu_background.png"] = backdrop(16, SURFACE_DARK, 218)
    out["textures/gui/menu_list_background.png"] = backdrop(16, SURFACE_DARKER, 200)
    out["textures/gui/inworld_menu_background.png"] = backdrop(16, SURFACE_DARK, 150)
    out["textures/gui/inworld_menu_list_background.png"] = backdrop(
        16, SURFACE_DARKER, 140)
    out["textures/gui/tab_header_background.png"] = backdrop(16, SURFACE_DARKER, 226)
    for name in ("header_separator", "footer_separator", "inworld_header_separator",
                 "inworld_footer_separator"):
        out["textures/gui/%s.png" % name] = separator(32, 2)
    return out


def backdrop(size, base, alpha):
    """Tileable Mica-ish backdrop: soft diagonal gradient plus fine grain.
    Minecraft blurs screen backdrops, so subtle is correct here."""
    s = Surface(size, size, ss=2)
    s.rect(0, 0, size, size, fill=with_a(base, alpha))
    a = s.array()
    ramp_x = np.linspace(0.94, 1.10, size)[None, :, None]
    ramp_y = np.linspace(0.94, 1.10, size)[:, None, None]
    body = a[..., :3].astype(np.float32) * ramp_x * ramp_y
    a[..., :3] = np.clip(body, 0, 255).astype(np.uint8)
    noise(a, 0, 0, size, size, 1.8, seed=size)
    return a


def separator(w, h):
    """Gradient hairline: bright in the middle, fading to nothing at the ends."""
    a = blank(w, h)
    ramp = 255 * (1.0 - np.abs(np.linspace(-1, 1, w)) ** 1.4)
    row = ramp.astype(np.uint16)
    a[0, :, :3] = 255
    a[0, :, 3] = np.clip(row * 0.42, 0, 255)
    a[1, :, :3] = 0
    a[1, :, 3] = np.clip(row * 0.22, 0, 255)
    return a


# --------------------------------------------------------------------------
# overlays: tooltip, popup, social chrome
# --------------------------------------------------------------------------
def overlays():
    out = {}
    out[P + "tooltip/background.png"] = acrylic_panel_tex(
        100, 100, radius=6, base=ACRYLIC, alpha=232, border=9)
    out[P + "tooltip/frame.png"] = frame_tex(100, 100, radius=8, border=1)
    out[P + "popup/background.png"] = acrylic_panel_tex(
        236, 34, radius=5, base=ACRYLIC, alpha=238, border=6)
    out[P + "social_interactions/background.png"] = acrylic_panel_tex(
        236, 34, radius=6, base=ACRYLIC, alpha=238, border=8)
    out[P + "dialog/warning_button.png"] = dialog_button(20, "normal")
    out[P + "dialog/warning_button_highlighted.png"] = dialog_button(20, "highlighted")
    out[P + "dialog/warning_button_disabled.png"] = dialog_button(20, "disabled")
    # --- social interactions buttons ---
    out[P + "social_interactions/mute_button.png"] = speaker_button(20, True, False)
    out[P + "social_interactions/mute_button_highlighted.png"] = speaker_button(
        20, True, True)
    out[P + "social_interactions/unmute_button.png"] = speaker_button(20, False, False)
    out[P + "social_interactions/unmute_button_highlighted.png"] = speaker_button(
        20, False, True)
    out[P + "social_interactions/report_button.png"] = report_button(20, False)
    out[P + "social_interactions/report_button_highlighted.png"] = report_button(
        20, True)
    out[P + "social_interactions/report_button_disabled.png"] = report_button(20, False,
                                                                             True)
    # --- friends family ---
    out[P + "friends/background.png"] = acrylic_panel_tex(
        236, 34, radius=6, base=ACRYLIC, alpha=238, border=1)
    out[P + "friends/background_dark.png"] = acrylic_panel_tex(
        236, 34, radius=5, base=C("#111111"), alpha=244, border=1)
    out[P + "friends/button.png"] = button_tex(200, 20, "normal")
    out[P + "friends/button_highlighted.png"] = button_tex(200, 20, "highlighted")
    out[P + "friends/button_disabled.png"] = button_tex(200, 20, "disabled")
    out[P + "friends/toast_background.png"] = acrylic_panel_tex(
        160, 32, radius=3, base=ACRYLIC, alpha=238, border=1)
    for name, ok, state in [("accept", True, "normal"),
                            ("accept_highlighted", True, "highlighted"),
                            ("reject", False, "normal"),
                            ("reject_highlighted", False, "highlighted")]:
        out[P + "friends/%s.png" % name] = verdict_button(18, ok, state)
        out[P + "pending_invite/%s.png" % name] = verdict_button(18, ok, state)
    out[P + "friends/cancel.png"] = small_icon(
        lambda s, w, h: glyph_x_light(s, w), 16)
    out[P + "friends/friends.png"] = small_icon(
        lambda s, w, h: two_people(s, w), 16)
    out[P + "friends/remove.png"] = small_icon(
        lambda s, w, h: person_minus(s, w), 14, 13)
    out[P + "friends/send_request.png"] = small_icon(
        lambda s, w, h: person_plus(s, w), 15)
    out[P + "friends/list_separator_top.png"] = separator(32, 2)
    out[P + "friends/loading.png"] = loading_dot(5, 6)
    return out


def acrylic_panel_tex(w, h, radius, base, alpha, border=1):
    """Acrylic panel texture that stays valid under nine-slice cropping: each
    caller passes a radius no larger than the declared nine-slice border so the
    preserved corners never cut into the rounded edge."""
    return panel_tex(w, h, radius=radius, base=base, alpha=alpha, tone="dark")


def frame_tex(w, h, radius, border=1):
    s = Surface(w, h, ss=4)
    s.rect(0.5, 0.5, w - 1, h - 1, fill=None, radius=radius,
           outline=(255, 255, 255, 70), ow=border)
    a = s.array()
    inner = Surface(w, h, ss=4)
    inner.rect(2.5, 2.5, w - 5, h - 5, fill=None, radius=radius - 2,
               outline=(0, 0, 0, 60), ow=1)
    over(a, inner.array())
    return a


def panel_tex(w, h, radius, base, alpha, tone="dark"):
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=with_a(base, alpha), radius=radius)
    a = s.array()
    if tone == "dark":
        shade_rows(a, 0, 0, w, h, (1.14, 0.94))
        apply_mask(a, rounded_ring_mask(w, h, radius, 1), ACRYLIC_EDGE)
        apply_mask(a, top_line_mask(w, h, radius), (255, 255, 255, 42))
        apply_mask(a, bottom_line_mask(w, h, radius), ACRYLIC_SHADE)
    else:
        shade_rows(a, 0, 0, w, h, (1.04, 0.96))
        apply_mask(a, rounded_ring_mask(w, h, radius, 1), (0, 0, 0, 30))
        apply_mask(a, top_line_mask(w, h, radius), HAIRLINE)
        apply_mask(a, bottom_line_mask(w, h, radius), (0, 0, 0, 30))
    noise(a, 0, 0, w, h, 1.8, seed=(w * 7 + h * 3) & 0xFF)
    return a


def button_tex(w, h, state):
    s = Surface(w, h, ss=4)
    r = 3 if state != "disabled" else 1
    if state == "disabled":
        fill, edge, top = C("#3A3A3C"), (0, 0, 0, 150), (255, 255, 255, 30)
    else:
        fill = ACCENT
        edge = with_a(ACCENT_DARK, 210)
        top = (255, 255, 255, 96 if state == "highlighted" else 70)
    s.rect(0, 0, w, h, fill=fill, radius=r)
    a = s.array()
    shade_rows(a, 0, 0, w, h, (1.10, 0.90))
    apply_mask(a, rounded_ring_mask(w, h, r, 1), edge)
    apply_mask(a, top_line_mask(w, h, r), top)
    apply_mask(a, bottom_line_mask(w, h, r), (0, 0, 0, 70))
    return a


def dialog_button(size, state):
    s = Surface(size, size, ss=4)
    if state == "disabled":
        fill, ink = C("#3A3A3C"), (255, 255, 255, 90)
    else:
        fill = ACCENT
        ink = WHITE
    s.rect(0.5, 0.5, size - 1, size - 1, fill=fill, radius=3)
    a = s.array()
    apply_mask(a, rounded_ring_mask(size, size, 3, 1),
               with_a(ACCENT_DARK, 200) if state != "disabled" else (0, 0, 0, 140))
    g = Surface(size, size, ss=4)
    c = size / 2.0
    g.poly([(c, c - 5.0), (c + 5.0, c + 4.0), (c - 5.0, c + 4.0)], ink)
    g.rect(c - 0.8, c - 1.6, 1.6, 3.0, fill=fill if state != "disabled"
           else C("#3A3A3C"))
    g.rect(c - 0.8, c + 2.4, 1.6, 1.6, fill=fill if state != "disabled"
           else C("#3A3A3C"))
    over(a, g.array())
    return a


def speaker_button(size, muted, hover):
    def draw(s, w, h):
        c = h / 2.0
        col = ACCENT_LIGHT if hover else INK_LIGHT
        s.poly([(4.0, c - 2.0), (c - 2.6, c - 2.0), (c - 2.6, c + 2.0),
                (4.0, c + 2.0)], col)
        if not muted:
            s.line([(c + 0.6, c - 2.6), (c + 3.2, c)], col, 1.2)
            s.line([(c + 0.6, c - 2.6), (c + 0.6, c + 2.6)], col, 1.2)
        else:
            glyph_x(s, c + 2.0, h - 2.0, col, 1.3)
    return small_icon(draw, size)


def report_button(size, hover, disabled=False):
    def draw(s, w, h):
        col = (255, 255, 255, 90) if disabled else (
            ACCENT_LIGHT if hover else INK_LIGHT)
        c = h / 2.0
        s.line([(c - 4.0, 2.0), (c - 4.0, h - 2.0)], col, 1.3)
        s.poly([(c - 3.0, 2.4), (c + 4.6, 4.6), (c - 3.0, 7.4)], col)
    return small_icon(draw, size)


def verdict_button(size, ok, state):
    s = Surface(size, size, ss=4)
    col = SUCCESS if ok else INSUCCESS
    if state == "highlighted":
        col = C("#3FB950") if ok else C("#E76B5E")
    s.ellipse(0.5, 0.5, size - 1, size - 1, fill=col)
    a = s.array()
    apply_mask(a, rounded_ring_mask(size, size, size // 2, 1), (0, 0, 0, 110))
    apply_mask(a, top_line_mask(size, size, size // 2), (255, 255, 255, 80))
    g = Surface(size, size, ss=4)
    if ok:
        glyph_check(g, [(5.0, 9.2), (7.6, 12.0), (13.0, 5.4)], WHITE, 2.0)
    else:
        glyph_x(g, size / 2.0, size / 2.0, WHITE, 1.8)
    over(a, g.array())
    return a


def glyph_x_light(s, n, col=None):
    col = col or INK_LIGHT
    a = n * 0.27
    c = n / 2.0
    s.line([(c - a, c - a), (c + a, c + a)], col, 1.5)
    s.line([(c - a, c + a), (c + a, c - a)], col, 1.5)
    return s


def two_people(s, n):
    glyph_person(s, n * 0.36, n * 0.40, 2.6, (255, 255, 255, 190))
    glyph_person(s, n * 0.64, n * 0.40, 2.6, (255, 255, 255, 235))
    return s


def person_minus(s, n):
    glyph_person(s, n * 0.42, n * 0.40, 2.8, INK_LIGHT)
    s.rect(n * 0.62, n * 0.55, 4.0, 1.5, fill=INK_LIGHT)
    return s


def person_plus(s, n):
    glyph_person(s, n * 0.42, n * 0.42, 2.8, INK_LIGHT)
    glyph_plus(s, n * 0.74, n * 0.62, 5.0, (255, 255, 255, 235), 1.4)
    return s


def small_icon(draw, w, h=None):
    """Draw a single glyph on a transparent canvas. `draw` receives
    (surface, width, height) so callers can stay size-agnostic."""
    h = h or w
    s = Surface(w, h, ss=4)
    draw(s, w, h)
    return s.array()


def loading_dot(w, h):
    s = Surface(w, h, ss=4)
    s.ellipse(0.6, 0.6, w - 1.2, h - 1.2, fill=(255, 255, 255, 200))
    return s.array()


# --------------------------------------------------------------------------
# list chrome (32x32 buttons + ping glyphs)
# --------------------------------------------------------------------------
LIST_GLYPHS = {
    "join": lambda s, n: glyph_join_light(s, n),
    "marked_join": lambda s, n: glyph_join_light(s, n),
    "move_up": lambda s, n: glyph_arrow(s, n / 2.0, n / 2.0, n * 0.30, "up",
                                        (255, 255, 255, 235), 1.8),
    "move_down": lambda s, n: glyph_arrow(s, n / 2.0, n / 2.0, n * 0.30, "down",
                                          (255, 255, 255, 235), 1.8),
    "select": lambda s, n: glyph_check(s, [(n * 0.34, n * 0.52), (n * 0.45,
                                                                  n * 0.64),
                                           (n * 0.68, n * 0.34)], WHITE, 2.2),
    "unselect": lambda s, n: glyph_x_n(s, n, WHITE),
    "warning": lambda s, n: glyph_warn_light(s, n),
    "error": lambda s, n: glyph_x_n(s, n, WHITE),
}


def glyph_x_n(s, n, col):
    a = n * 0.22
    c = n / 2.0
    s.line([(c - a, c - a), (c + a, c + a)], col, 1.8)
    s.line([(c - a, c + a), (c + a, c - a)], col, 1.8)
    return s


def glyph_join_light(s, n):
    c = n / 2.0
    glyph_arrow(s, c - 1.0, c, n * 0.26, "right", (255, 255, 255, 240), 1.8)
    s.line([(c + 4.2, c - 4.6), (c + 4.2, c + 4.6)], (255, 255, 255, 240), 1.8)
    return s


def glyph_warn_light(s, n):
    c = n / 2.0
    s.poly([(c, c - 6.0), (c + 6.2, c + 5.0), (c - 6.2, c + 5.0)], WARNING)
    s.rect(c - 0.9, c - 1.8, 1.8, 3.6, fill=WHITE)
    s.rect(c - 0.9, c + 2.6, 1.8, 1.8, fill=WHITE)
    return s


def list_chrome():
    out = {}
    for family, names in (("server_list", ("join", "move_up", "move_down")),
                          ("world_list", ("join", "marked_join", "warning", "error")),
                          ("transferable_list", ("move_up", "move_down", "select",
                                                 "unselect"))):
        for name in names:
            for sel in ("", "_highlighted"):
                state = "highlighted" if sel else "normal"
                out[P + "%s/%s%s.png" % (family, name, sel)] = list_button(
                    name, state)
    for i in range(1, 6):
        out[P + "server_list/ping_%d.png" % i] = ping_bars(10, 8, i)
        out[P + "server_list/pinging_%d.png" % i] = ping_bars(10, 8, i)
    out[P + "server_list/unreachable.png"] = ping_unknown(10, 8)
    out[P + "server_list/incompatible.png"] = ping_unknown(10, 8)
    return out


def list_button(name, state):
    size = 32
    s = Surface(size, size, ss=4)
    pad = 2.0
    r = size / 2.0 - pad
    if state == "highlighted":
        fill = with_a(ACCENT, 190)
    else:
        fill = (0, 0, 0, 130)
    s.rect(pad, pad, size - 2 * pad, size - 2 * pad, fill=fill, radius=r)
    a = s.array()
    apply_mask(a, rounded_ring_mask(size, size, r, 1),
               (255, 255, 255, 110) if state == "normal" else (255, 255, 255, 70))
    apply_mask(a, top_line_mask(size, size, r), (255, 255, 255, 70))
    g = Surface(size, size, ss=4)
    LIST_GLYPHS[name](g, size)
    over(a, g.array())
    return a


# --------------------------------------------------------------------------
# HUD-adjacent chrome
# --------------------------------------------------------------------------
def hud_chrome():
    out = {}
    out[P + "gamemode_switcher/slot.png"] = fluent_dark_slot(26, radius=4)
    out[P + "gamemode_switcher/selection.png"] = gamemode_selection(26)
    out[P + "spectator/close.png"] = small_icon(lambda s, w, h: glyph_x_light(s, w), 16)
    out[P + "spectator/scroll_left.png"] = small_icon(
        lambda s, w, h: glyph_chevron(s, w / 2.0, h / 2.0, 9.0, "left", INK_LIGHT, 1.6),
        16)
    out[P + "spectator/scroll_right.png"] = small_icon(
        lambda s, w, h: glyph_chevron(s, w / 2.0, h / 2.0, 9.0, "right",
                                      INK_LIGHT, 1.6), 16)
    for name in ("teleport_to_player", "teleport_to_team"):
        out[P + "spectator/%s.png" % name] = small_icon(
            lambda s, w, h: two_people(s, w), 16)
    out[P + "pause_menu/bug.png"] = small_icon(
        lambda s, w, h: glyph_warn_small(s, w), 13)
    out[P + "pause_menu/player_reporting.png"] = small_icon(
        lambda s, w, h: glyph_person(s, w * 0.45, h * 0.42, 3.0, INK_LIGHT), 15, 14)
    out[P + "pause_menu/social_interactions.png"] = small_icon(
        lambda s, w, h: two_people(s, w), 20)
    out[P + "player_list/make_operator.png"] = small_icon(
        lambda s, w, h: glyph_plus(s, w / 2.0, h / 2.0, h - 1.0, WARNING, 1.4),
        8, 7)
    out[P + "player_list/remove_operator.png"] = small_icon(
        lambda s, w, h: glyph_minus(s, w), 8, 7)
    out[P + "player_list/remove_player.png"] = small_icon(
        lambda s, w, h: glyph_x_n(s, w, INSUCCESS), 8, 7)
    return out


def glyph_minus(s, n):
    s.rect(n / 2.0 - 3.0, n / 2.0 - 0.8, 6.0, 1.6, fill=INSUCCESS)
    return s


def glyph_warn_small(s, n):
    c = n / 2.0
    s.poly([(c, 0.6), (n - 0.8, n - 1.2), (0.8, n - 1.2)], WARNING)
    s.rect(c - 0.7, c - 1.6, 1.4, 3.0, fill=(0, 0, 0, 190))
    s.rect(c - 0.7, c + 2.2, 1.4, 1.4, fill=(0, 0, 0, 190))
    return s


def gamemode_slot(size):
    return fluent_dark_slot(size, radius=4)


def gamemode_selection(size):
    s = Surface(size, size, ss=4)
    s.rect(0.5, 0.5, size - 1, size - 1, fill=None, radius=4,
           outline=(255, 255, 255, 235), ow=1)
    a = s.array()
    glow = Surface(size, size, ss=4)
    glow.rect(0, 0, size, size, fill=None, radius=5,
              outline=(255, 255, 255, 60), ow=3)
    over(a, glow.array())
    return a


def fluent_dark_slot(size, radius=4):
    s = Surface(size, size, ss=4)
    s.rect(0, 0, size, size, fill=(0, 0, 0, 120), radius=radius)
    a = s.array()
    apply_mask(a, rounded_ring_mask(size, size, radius, 1), (0, 0, 0, 130))
    apply_mask(a, bottom_line_mask(size, size, radius), (255, 255, 255, 30))
    return a


# --------------------------------------------------------------------------
# toasts
# --------------------------------------------------------------------------
TOAST_SIZES = {
    "advancement": (160, 32), "now_playing": (160, 32), "recipe": (160, 32),
    "tutorial": (160, 32), "system": (160, 64),
}


def toasts():
    out = {}
    for name, (w, h) in TOAST_SIZES.items():
        out[P + "toast/%s.png" % name] = acrylic_panel_tex(
            w, h, radius=4 if name != "system" else 5, base=ACRYLIC,
            alpha=244, border=1)
    for name in ("mouse", "movement_keys", "recipe_book", "right_click",
                 "social_interactions", "tree", "wooden_planks"):
        out[P + "toast/%s.png" % name] = tutorial_key(20)
    return out


def tutorial_key(size):
    """Tutorial hint keycaps (mouse / keys / icons) drawn as Fluent keycaps."""
    return fluent_dark_slot(size, radius=5)


# --------------------------------------------------------------------------
# advancements
# --------------------------------------------------------------------------
def advancements():
    # the window frame is the one advancement sprite still addressed through the
    # legacy (non-sprite) path, so it has to be emitted there
    out = {}
    for name in ("box_obtained", "box_unobtained", "title_box"):
        out[P + "advancements/%s.png" % name] = advancement_box(
            200, 26, obtained=name == "box_obtained")
    for kind in ("task", "goal", "challenge"):
        for ob in ("obtained", "unobtained"):
            out[P + "advancements/%s_frame_%s.png" % (kind, ob)] = adv_frame(
                26, kind, ob == "obtained")
    for side in ("above", "below"):
        for pos in ("left", "middle", "right"):
            for sel in ("", "_selected"):
                name = "tab_%s_%s%s" % (side, pos, sel)
                out[P + "advancements/%s.png" % name] = adv_tab(
                    28, 32, "up" if side == "above" else "down", bool(sel))
    for side in ("left", "right"):
        for pos in ("top", "middle", "bottom"):
            for sel in ("", "_selected"):
                name = "tab_%s_%s%s" % (side, pos, sel)
                out[P + "advancements/%s.png" % name] = adv_tab(
                    32, 28, "left" if side == "left" else "right", bool(sel))
    return out


def advancement_box(w, h, obtained):
    base = ACCENT if obtained else (0, 0, 0, 0)
    tex = panel_tex(w, h, radius=6, base=base if obtained else C("#1A1A1A"),
                    alpha=236 if obtained else 210, tone="dark")
    return tex


def adv_frame(size, kind, obtained):
    s = Surface(size, size, ss=4)
    col = ACCENT_LIGHT if obtained else (255, 255, 255, 90)
    fill = with_a(ACCENT, 120) if obtained else (0, 0, 0, 120)
    if kind == "challenge":
        s.ellipse(1.5, 1.5, size - 3, size - 3, fill=fill)
        s.ellipse(1.5, 1.5, size - 3, size - 3, fill=None, outline=col, ow=2)
        s.ellipse(5.5, 5.5, size - 11, size - 11, fill=None,
                  outline=with_a(col, 120), ow=1)
    else:
        r = 4 if kind == "task" else 5
        s.rect(1.5, 1.5, size - 3, size - 3, fill=fill, radius=r)
        s.rect(1.5, 1.5, size - 3, size - 3, fill=None, radius=r,
               outline=col, ow=2)
        inset = 4.5 if kind == "task" else 5.5
        s.rect(inset, inset, size - 2 * inset, size - 2 * inset,
               fill=None, radius=max(1, r - 2), outline=with_a(col, 110), ow=1)
    return s.array()


def adv_tab(w, h, free_edge, selected):
    base = with_a(ACRYLIC, 224) if not selected else with_a(ACRYLIC, 246)
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=base, radius=5)
    a = s.array()
    shade_rows(a, 0, 0, w, h, (1.10, 0.95))
    apply_mask(a, rounded_ring_mask(w, h, 5, 1), ACRYLIC_EDGE)
    # square off the edge that docks into the advancement window
    attach = {"up": h - 4, "down": 0, "left": 0, "right": w - 4}[free_edge]
    if free_edge in ("up", "down"):
        over(a, flat(w, 4, base), 0, attach)
    else:
        lay = flat(4, h, base)
        over(a, lay, attach, 0)
    ind = {"up": top_line_mask, "down": bottom_line_mask,
           "left": left_line_mask, "right": right_line_mask}[free_edge]
    apply_mask(a, ind(w, h, 5), ACCENT_LIGHT if selected else HAIRLINE)
    return a


# --------------------------------------------------------------------------
# recipe book
# --------------------------------------------------------------------------
def recipe_book():
    out = {}
    out["textures/gui/recipe_book.png"] = recipe_book_panel(256, 256)
    out["textures/gui/book.png"] = written_book_panel(256, 256)
    out[P + "recipe_book/button.png"] = small_cta(20, 18, False)
    out[P + "recipe_book/button_highlighted.png"] = small_cta(20, 18, True)
    for kind in ("", "furnace_"):
        for state in ("enabled", "disabled"):
            for hl in ("", "_highlighted"):
                name = "recipe_book/%sfilter_%s%s.png" % (kind, state, hl)
                out[P + name] = filter_chip(26, 16, state == "enabled", bool(hl))
    for kind in ("crafting", "furnace"):
        for state in ("", "_disabled", "_highlighted", "_disabled_highlighted"):
            name = "recipe_book/%s_overlay%s.png" % (kind, state)
            out[P + name] = recipe_overlay(
                24, kind == "crafting", "disabled" in state, "highlighted" in state)
    out[P + "recipe_book/overlay_recipe.png"] = recipe_slot_overlay(32, "normal")
    for name, craftable, many in (("slot_craftable", True, False),
                                  ("slot_many_craftable", True, True),
                                  ("slot_uncraftable", False, False),
                                  ("slot_many_uncraftable", False, True)):
        out[P + "recipe_book/%s.png" % name] = recipe_slot_overlay(
            25, "craftable" if craftable else "uncraftable", many, border=4)
    for direction in ("backward", "forward"):
        for hl in ("", "_highlighted"):
            out[P + "recipe_book/page_%s%s.png" % (direction, hl)] = page_arrow(
                12, 17, "left" if direction == "backward" else "right", bool(hl))
    out[P + "recipe_book/tab.png"] = rb_tab(35, 27, False)
    out[P + "recipe_book/tab_selected.png"] = rb_tab(35, 27, True)
    return out


def recipe_book_panel(w, h):
    """Panel for the recipe book GUI (dark: its labels are white)."""
    bbox = (1, 1, 147, 166)
    a = blank(w, h)
    panel = panel_tex(150, 169, radius=8, base=ACRYLIC, alpha=238, tone="dark")
    over(a, panel, bbox[0] - 1, bbox[1] - 1)
    return a


def written_book_panel(w, h):
    """Panel for the written book screen (light paper: its text is dark)."""
    bbox = (20, 1, 165, 180)
    a = blank(w, h)
    s = Surface(146, 180, ss=4)
    s.rect(0, 0, 146, 180, fill=with_a(PAPER, 250), radius=6)
    body = s.array()
    shade_rows(body, 0, 0, 146, 180, (1.03, 0.96))
    apply_mask(body, rounded_ring_mask(146, 180, 6, 1), PAPER_EDGE)
    apply_mask(body, top_line_mask(146, 180, 6), HAIRLINE)
    noise(body, 0, 0, 146, 180, 1.6, seed=33)
    # centre spine: the book renders two text pages side by side
    apply_mask(body, rounded_ring_mask(146, 180, 6, 1), (0, 0, 0, 26))
    spine = flat(2, 158, with_a(PAPER_EDGE, 210))
    over(body, spine, 72, 11)
    gloss = flat(1, 158, (0, 0, 0, 40))
    over(body, gloss, 70, 11)
    over(a, body, bbox[0], bbox[1])
    return a


def small_cta(w, h, hover):
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=ACCENT, radius=3)
    a = s.array()
    shade_rows(a, 0, 0, w, h, (1.10, 0.90))
    apply_mask(a, rounded_ring_mask(w, h, 3, 1), with_a(ACCENT_DARK, 200))
    apply_mask(a, top_line_mask(w, h, 3), (255, 255, 255, 80 if hover else 60))
    return a


def filter_chip(w, h, enabled, hover):
    s = Surface(w, h, ss=4)
    if enabled:
        fill = ACCENT_LIGHT if hover else ACCENT
        ink = WHITE
    else:
        fill = (0, 0, 0, 150)
        ink = (255, 255, 255, 120)
    s.rect(0, 0, w, h, fill=fill, radius=3)
    a = s.array()
    apply_mask(a, rounded_ring_mask(w, h, 3, 1), (0, 0, 0, 110))
    apply_mask(a, top_line_mask(w, h, 3), (255, 255, 255, 60))
    return a


def recipe_overlay(size, crafting, disabled, hover):
    """Arrow / plus hint drawn between the grid and the result slot."""
    s = Surface(size, size, ss=4)
    if disabled:
        col = (255, 255, 255, 90)
    else:
        col = ACCENT_LIGHT if hover else (255, 255, 255, 225)
    c = size / 2.0
    if crafting:
        s.poly([(c - 4.0, c - 5.0), (c + 3.6, c), (c - 4.0, c + 5.0)], col)
    else:
        glyph_arrow(s, c, c, size * 0.30, "right", col, 1.8)
    return s.array()


def recipe_slot_overlay(size, state, many=False, border=0):
    s = Surface(size, size, ss=4)
    r = max(2, border)
    if state == "normal":
        s.rect(0, 0, size, size, fill=(255, 255, 255, 40), radius=r)
        a = s.array()
        apply_mask(a, rounded_ring_mask(size, size, r, 1), (255, 255, 255, 110))
        return a
    ok = state == "craftable"
    fill = with_a(ACCENT, 90) if ok else (0, 0, 0, 120)
    s.rect(0, 0, size, size, fill=fill, radius=r)
    if many:
        for i in range(3):
            s.ellipse(size / 2.0 - 3.4 + i * 2.8, size - 5.0, 2.0, 2.0,
                      fill=ACCENT_LIGHT if ok else (255, 255, 255, 150))
    a = s.array()
    apply_mask(a, rounded_ring_mask(size, size, r, 1),
               ACCENT_LIGHT if ok else (255, 255, 255, 70))
    return a


def page_arrow(w, h, direction, hover):
    s = Surface(w, h, ss=4)
    col = ACCENT_LIGHT if hover else (255, 255, 255, 232)
    glyph_chevron(s, w / 2.0, h / 2.0, h * 0.5, direction, col, 1.8)
    return s.array()


def rb_tab(w, h, selected):
    base = with_a(ACRYLIC, 232) if not selected else ACCENT
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=base, radius=4)
    a = s.array()
    shade_rows(a, 0, 0, w, h, (1.10, 0.94))
    apply_mask(a, rounded_ring_mask(w, h, 4, 1), ACRYLIC_EDGE)
    if selected:
        apply_mask(a, top_line_mask(w, h, 4), (255, 255, 255, 80))
    over(a, flat(w, 4, base), 0, h - 4)
    return a


def pack_icon(size=512):
    """The icon Minecraft lists in the resource-pack browser.

    Drawn natively at 512x512 rather than upscaled from a small tile: the pack
    list renders the icon at arbitrary sizes, so the extra resolution buys real
    detail - a three-stop accent gradient, a radial sheen, a soft cast shadow
    under the window glyph and hairline rim lighting - instead of interpolated
    mush.
    """
    px = float(size)
    r = int(round(px * 0.2227))

    s = Surface(size, size, ss=4)
    s.rect(0, 0, size, size, fill=ACCENT, radius=r)
    a = s.array()

    # three-stop diagonal gradient: light at the top-left, deep at the bottom
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    t = np.clip((xx + yy) / (2.0 * (size - 1)), 0, 1)
    stops = (0.0, 0.46, 1.0)
    ramp = (np.array(ACCENT_LIGHT[:3], np.float32),
            np.array(ACCENT[:3], np.float32),
            np.array(ACCENT_DARK[:3], np.float32))
    body = np.empty((size, size, 3), np.float32)
    lo = t <= stops[1]
    f = (t - stops[0]) / (stops[1] - stops[0])
    body[lo] = (ramp[0] * (1 - f[lo, None]) + ramp[1] * f[lo, None])
    hi = ~lo
    f = (t - stops[1]) / (stops[2] - stops[1])
    body[hi] = (ramp[1] * (1 - f[hi, None]) + ramp[2] * f[hi, None])

    # radial sheen, as if a soft light sits above the top-left corner
    sx, sy = px * 0.30, px * 0.16
    rr = (px * 0.46) ** 2
    glow = np.exp(-(((xx - sx) ** 2 + (yy - sy) ** 2) / (2.0 * rr)))
    body += glow[..., None] * np.array((30, 30, 34), np.float32) * 0.5
    # settle the bottom edge into shadow so the tile has weight
    body *= (1.0 - 0.10 * np.clip((t - 0.55) / 0.45, 0, 1))[..., None]
    a[..., :3] = np.clip(body, 0, 255).astype(np.uint8)

    # rim lighting: a wide inner glow line plus a crisp lit top edge
    apply_mask(a, rounded_ring_mask(size, size, r, max(1, int(px * 0.005))),
               (255, 255, 255, 64))
    apply_mask(a, rounded_ring_mask(size, size, r, max(1, int(px * 0.011))),
               (255, 255, 255, 30))
    apply_mask(a, top_line_mask(size, size, r, max(1, int(px * 0.006))),
               (255, 255, 255, 104))
    apply_mask(a, bottom_line_mask(size, size, r, max(1, int(px * 0.008))),
               (0, 0, 0, 58))

    # ---- Mica window glyph ------------------------------------------------
    gw = int(round(px * 0.582))
    gh = int(round(px * 0.462))
    gr = max(4, int(round(px * 0.0455)))
    gx = (size - gw) // 2
    gy = (size - gh) // 2 + int(round(px * 0.014))
    bar = int(round(gh * 0.236))

    # cast shadow: overlapping translucent rects, each a little wider, so the
    # falloff reads as a blur at 512 without a Gaussian pass
    pad = int(round(px * 0.055))
    sh = Surface(gw + 2 * pad, gh + 2 * pad, ss=4)
    for i in range(7):
        g = i * 0.9
        sh.rect(pad - g, pad + px * 0.016 - g * 0.6, gw + 2 * g, gh + 2 * g,
                fill=(6, 20, 34, 13), radius=gr + int(round(g)))
    over(a, sh.array(), gx - pad, gy - pad)

    w = Surface(gw, gh, ss=4)
    w.rect(0, 0, gw, gh, fill=MICA_BRIGHT, radius=gr)
    # title bar, clipped to the frame afterwards
    sep = max(1, int(round(px * 0.004)))
    w.rect(0, 0, gw, bar, fill=ACCENT_DARK)
    w.rect(0, bar - sep, gw, sep, fill=with_a(ACCENT_LIGHT, 190))
    # window controls, top right
    dot = max(2, int(round(px * 0.0114)))
    gap = int(round(px * 0.0255))
    for i in range(3):
        cx = gw - int(round(gw * 0.055)) - i * gap
        cy = bar // 2
        w.ellipse(cx - dot, cy - dot, dot * 2, dot * 2,
                  fill=with_a(ACCENT_LIGHT, 210 if i else 255))
    # content: an accent avatar tile and three rounded text bars
    av = int(round(gh * 0.300))
    ax = int(round(gw * 0.072))
    ay = bar + int(round((gh - bar - av) * 0.42))
    w.rect(ax, ay, av, av, fill=with_a(ACCENT, 235), radius=int(round(av * 0.28)))
    w.ellipse(ax + av * 0.32, ay + av * 0.24, av * 0.36, av * 0.36,
              fill=(255, 255, 255, 236))
    w.rect(ax + av * 0.22, ay + av * 0.62, av * 0.56, av * 0.34,
           fill=(255, 255, 255, 236), radius=int(round(av * 0.20)))
    lx = ax + av + int(round(gw * 0.062))
    lw = gw - lx - int(round(gw * 0.075))
    lh = max(2, int(round(gh * 0.058)))
    for i, frac in enumerate((1.00, 0.74, 0.46)):
        ly = ay + int(round(i * (lh * 2.30)))
        w.rect(lx, ly, max(lh, int(round(lw * frac))), lh,
               fill=with_a(INK, 92 if i == 0 else 64), radius=lh // 2)

    wa = w.array()
    wa[..., 3] = np.minimum(wa[..., 3], rounded_mask(gw, gh, gr))
    apply_mask(wa, rounded_ring_mask(gw, gh, gr, 1), (24, 34, 46, 44))
    over(a, wa, gx, gy)
    return a


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------
BUILDERS = (icons, menus, overlays, list_chrome, hud_chrome, toasts, advancements,
            recipe_book)


def build_all():
    out = {}
    for fn in BUILDERS:
        part = fn()
        clash = set(part) & set(out)
        if clash:
            raise SystemExit("duplicate texture keys: %s" % sorted(clash))
        out.update(part)
    return out
