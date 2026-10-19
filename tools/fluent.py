#!/usr/bin/env python3
"""ZERO-UI+ Fluent design system.

Small, dependency-light drawing kit used by every texture builder. It gives us
anti-aliased shapes at Minecraft's pixel scale, the Fluent 2 colour tokens, and
the Mica / Acrylic surface recipes the whole pack is built from.

Design rules baked in here
--------------------------
* Every Minecraft GUI texture is authored at 1:1 pixel scale, so shapes are
  drawn on a supersampled canvas and box-filtered back down. This yields clean
  anti-aliased rounded corners without changing the texture's final size.
* Downsampling happens in *premultiplied* space. Straight RGBA averaging would
  pull transparent-black pixels into edges and produce dark halos.
* Surfaces use Mica (light, slightly translucent) for in-menu chrome because
  Minecraft hard codes container titles to 0x404040 - dark text needs a light
  backdrop. Overlays that sit on top of the world (HUD, tooltips) use Acrylic
  (dark, translucent) instead.
"""
import math

import numpy as np
from PIL import Image, ImageDraw


def C(hexstr, a=255):
    """Hex string -> RGBA tuple."""
    h = hexstr.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(a))


def with_a(color, a):
    return (color[0], color[1], color[2], int(a))


# --------------------------------------------------------------------------
# Fluent 2 tokens
# --------------------------------------------------------------------------
ACCENT = C("#0F6CBD")
ACCENT_HOVER = C("#115EA3")
ACCENT_PRESSED = C("#0C3B5E")
ACCENT_DARK = C("#0A4A73")
ACCENT_LIGHT = C("#2899F5")
ACCENT_PALE = C("#EFF6FC")
ACCENT_WASH = C("#DCEBF9")

MICA = C("#F3F3F3")
MICA_BRIGHT = C("#FBFBFB")
MICA_DEEP = C("#E4E4E4")
WHITE = C("#FFFFFF")
PAPER = C("#FAF6EC")
PAPER_EDGE = C("#D9CFB8")

# Text-colour lock: Minecraft hard codes most GUI text colours, so each surface
# family is bound to the text colour it will host.
#   container titles 0x404040 (dark)  -> light Mica panels
#   menu/list/tooltip/toast text      -> white  -> dark Acrylic
#   button text 0xFFFFFF              -> accent or dark fill only
#   edit box text 0xE0E0E0            -> dark field
SURFACE_DARK = C("#1C1C1C")     # menu backdrop base
SURFACE_DARKER = C("#141414")   # list backdrop base
FILL_NEUTRAL = C("#3A3A3C")     # disabled button w/ 0xA0A0A0 text
FILL_NEUTRAL_HI = C("#4A4A4E")

INK = C("#404040")
INK_SOFT = C("#5C5C5C")
INK_DISABLED = C("#9B9B9B")

STROKE = C("#000000", 34)
STROKE_SOFT = C("#000000", 20)
HAIRLINE = C("#FFFFFF", 170)
SHADOW = C("#000000", 26)

INSUCCESS = C("#C42B1C")  # Fluent error
SUCCESS = C("#0E700E")    # Fluent success
WARNING = C("#F7630C")    # Fluent warning
INFO = C("#0F6CBD")

# HUD / overlay (over the world) tokens
ACRYLIC = C("#1F1F1F", 176)
ACRYLIC_SOLID = C("#242424", 214)
ACRYLIC_EDGE = C("#FFFFFF", 38)
ACRYLIC_SHADE = C("#000000", 110)

HEALTH = C("#E8453C")
HEALTH_DEEP = C("#A81E14")
ARMOR = C("#8FA9C4")
ARMOR_DEEP = C("#55708F")
FOOD = C("#E9A13B")
FOOD_DEEP = C("#A4651B")
AIR = C("#4CC2FF")
AIR_DEEP = C("#1B6FA8")
EXP = C("#59B32E")
EXP_DEEP = C("#2A6B14")

RADIUS_PANEL = 6
RADIUS_CONTROL = 3
RADIUS_SLOT = 3


# --------------------------------------------------------------------------
# Surface
# --------------------------------------------------------------------------
class Surface:
    """Supersampled RGBA canvas that resolves to exact pixel dimensions."""

    def __init__(self, w, h, ss=4):
        self.w = int(w)
        self.h = int(h)
        self.ss = ss
        self.px = Image.new("RGBA", (self.w * ss, self.h * ss), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.px)

    # -- primitives ------------------------------------------------------
    def _box(self, x, y, w, h):
        s = self.ss
        return [x * s, y * s, (x + w) * s - 1, (y + h) * s - 1]

    def rect(self, x, y, w, h, fill=None, radius=0, outline=None, ow=1):
        box = self._box(x, y, w, h)
        r = radius * self.ss
        if radius > 0:
            self.d.rounded_rectangle(box, radius=r, fill=fill)
            if outline:
                self.d.rounded_rectangle(box, radius=r, outline=outline,
                                         width=max(1, int(round(ow * self.ss))))
        else:
            self.d.rectangle(box, fill=fill)
            if outline:
                self.d.rectangle(box, outline=outline,
                                 width=max(1, int(round(ow * self.ss))))
        return self

    def pixel(self, x, y, fill):
        s = self.ss
        self.d.rectangle([x * s, y * s, x * s + s - 1, y * s + s - 1], fill=fill)
        return self

    def line(self, pts, fill, width=1):
        s = self.ss
        scaled = [(p[0] * s + s / 2.0, p[1] * s + s / 2.0) for p in pts]
        self.d.line(scaled, fill=fill, width=max(1, int(round(width * s))),
                    joint="curve")
        return self

    def poly(self, pts, fill):
        s = self.ss
        self.d.polygon([(p[0] * s, p[1] * s) for p in pts], fill=fill)
        return self

    def ellipse(self, x, y, w, h, fill=None, outline=None, ow=1):
        s = self.ss
        box = [x * s, y * s, (x + w) * s - 1, (y + h) * s - 1]
        self.d.ellipse(box, fill=fill, outline=outline,
                       width=max(1, int(round(ow * s))))
        return self

    def ring(self, cx, cy, r, fill, width=1):
        self.ellipse(cx - r, cy - r, r * 2, r * 2, outline=fill, ow=width)
        return self

    # -- compositing ----------------------------------------------------
    def blit(self, arr, x=0, y=0):
        """Composite a 1x RGBA numpy array at integer pixel coordinates."""
        if arr is None or arr.size == 0:
            return self
        img = Image.fromarray(np.ascontiguousarray(arr, dtype=np.uint8), "RGBA")
        if self.ss != 1:
            img = img.resize((img.width * self.ss, img.height * self.ss), Image.NEAREST)
        self.px.alpha_composite(img, (int(x * self.ss), int(y * self.ss)))
        return self

    # -- resolve --------------------------------------------------------
    def array(self):
        a = np.asarray(self.px, dtype=np.float32)
        s = self.ss
        if s > 1:
            al = a[..., 3:4] / 255.0
            a[..., :3] *= al
            a = a.reshape(self.h, s, self.w, s, 4).mean(axis=(1, 3))
            al = a[..., 3:4] / 255.0
            a[..., :3] /= np.maximum(al, 1e-6)
            np.clip(a, 0, 255, out=a)
        return a.astype(np.uint8)

    def image(self):
        return Image.fromarray(np.ascontiguousarray(self.array()), "RGBA")


# --------------------------------------------------------------------------
# Post processing on resolved 1x arrays
# --------------------------------------------------------------------------
def shade_rows(arr, x, y, w, h, gain, direction="down"):
    """Multiply RGB inside a rect by a linear gain ramp (subtle tonal shift)."""
    if direction == "down":
        ramp = np.linspace(gain[0], gain[1], h)
    else:
        ramp = np.linspace(gain[1], gain[0], h)
    region = arr[y:y + h, x:x + w, :3].astype(np.float32)
    region *= ramp[:, None, None]
    np.clip(region, 0, 255, out=region)
    arr[y:y + h, x:x + w, :3] = region.astype(np.uint8)
    return arr


def noise(arr, x, y, w, h, amount=2.0, seed=0):
    """Very light per-pixel grain; the Acrylic/Mica 'material' tell."""
    rng = np.random.default_rng(seed)
    region = arr[y:y + h, x:x + w, :3].astype(np.float32)
    g = rng.normal(0.0, amount, size=(h, w, 1))
    region += g
    np.clip(region, 0, 255, out=region)
    arr[y:y + h, x:x + w, :3] = region.astype(np.uint8)
    return arr


def over(dst, src, x=0, y=0):
    """Alpha-composite src (1x RGBA) onto dst in place."""
    h, w = src.shape[:2]
    region = dst[y:y + h, x:x + w].astype(np.float32)
    sa = src[..., 3:4].astype(np.float32) / 255.0
    da = region[..., 3:4] / 255.0
    out_a = sa + da * (1 - sa)
    src_rgb = src[..., :3].astype(np.float32) * sa
    dst_rgb = region[..., :3] * da
    rgb = (src_rgb + dst_rgb * (1 - sa)) / np.maximum(out_a, 1e-6)
    region[..., :3] = np.clip(rgb, 0, 255)
    region[..., 3:4] = np.clip(out_a * 255.0, 0, 255)
    dst[y:y + h, x:x + w] = region.astype(np.uint8)
    return dst


def blank(w, h, fill=(0, 0, 0, 0)):
    return np.zeros((h, w, 4), dtype=np.uint8) + np.array(fill, dtype=np.uint8)


def rounded_mask(w, h, radius, ss=4):
    """Alpha-only rounded rect as a 1x uint8 array (255 inside, 0 outside)."""
    s = Surface(w, h, ss=ss)
    s.rect(0, 0, w, h, fill=(255, 255, 255, 255), radius=radius)
    return s.array()[..., 3]


def apply_mask(arr, mask, color):
    """Tint-composite `color` through an alpha mask onto arr."""
    layer = np.zeros_like(arr)
    layer[..., 0] = color[0]
    layer[..., 1] = color[1]
    layer[..., 2] = color[2]
    layer[..., 3] = (mask.astype(np.float32) * (color[3] / 255.0)).astype(np.uint8)
    return over(arr, layer)


# --------------------------------------------------------------------------
# Material recipes
# --------------------------------------------------------------------------
def mica_panel(arr, x, y, w, h, radius=RADIUS_PANEL, base=MICA, alpha=232,
               shadow=True):
    """Fluent Mica surface: translucent light fill, hairline stroke, reveal
    highlight on the top edge and a soft shade along the bottom."""
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=with_a(base, alpha), radius=radius)
    panel = s.array()
    shade_rows(panel, 0, 0, w, h, (1.035, 0.955))
    noise(panel, 0, 0, w, h, 1.6, seed=(x * 31 + y * 17) & 0xFFFF)
    if shadow:
        # 1px hairline stroke, then a brighter reveal line along the top edge
        apply_mask(panel, rounded_ring_mask(w, h, radius, 1), STROKE)
        apply_mask(panel, top_line_mask(w, h, radius), HAIRLINE)
        apply_mask(panel, bottom_line_mask(w, h, radius), SHADOW)
    over(arr, panel, x, y)
    return arr


def acrylic_panel(arr, x, y, w, h, radius=RADIUS_PANEL, base=ACRYLIC,
                  alpha=None, shadow=True, grain=2.0):
    """Fluent Acrylic surface for overlay chrome: dark, translucent, with a
    soft inner highlight on the top edge (mimics light hitting the layer)."""
    a = alpha if alpha is not None else base[3]
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=(base[0], base[1], base[2], a), radius=radius)
    panel = s.array()
    shade_rows(panel, 0, 0, w, h, (1.18, 0.92))
    noise(panel, 0, 0, w, h, grain, seed=(x * 13 + y * 7) & 0xFFFF)
    if shadow:
        apply_mask(panel, rounded_ring_mask(w, h, radius, 1), ACRYLIC_EDGE)
        apply_mask(panel, top_line_mask(w, h, radius),
                   C("#FFFFFF", 46))
        apply_mask(panel, bottom_line_mask(w, h, radius), ACRYLIC_SHADE)
    over(arr, panel, x, y)
    return arr


def fluent_button(w, h, state="normal", radius=RADIUS_CONTROL, accent=ACCENT):
    """Fluent button: accent fill, 3px nine-slice safe corners, hover lift,
    pressed sink, disabled neutral.

    Minecraft draws button labels in white (0xFFFFFF) and disabled labels in
    0xA0A0A0, so the fill has to stay dark enough for those to read.
    """
    s = Surface(w, h, ss=4)
    if state == "disabled":
        fill = FILL_NEUTRAL
        edge = with_a(C("#000000"), 150)
        top = C("#FFFFFF", 30)
    elif state == "highlighted":
        fill = accent
        edge = with_a(C("#0A4A73"), 220)
        top = C("#FFFFFF", 96)
    else:
        fill = accent
        edge = with_a(C("#0A4A73"), 190)
        top = C("#FFFFFF", 70)
    s.rect(0, 0, w, h, fill=fill, radius=radius)
    body = s.array()
    shade_rows(body, 0, 0, w, h, (1.10, 0.90))
    apply_mask(body, rounded_ring_mask(w, h, radius, 1), edge)
    apply_mask(body, top_line_mask(w, h, radius), top)
    apply_mask(body, bottom_line_mask(w, h, radius),
               C("#000000", 70 if state != "highlighted" else 100))
    return body


def fluent_slot(w=18, h=18, radius=RADIUS_SLOT, surface="light"):
    """Inset slot well.

    The fill resolves to roughly mid grey (vanilla uses 139,139,139) because
    item stack counts are drawn in white and need a dark enough well to read.
    """
    s = Surface(w, h, ss=4)
    if surface == "light":
        base = C("#000000", 96)
        edge_top = C("#000000", 118)
        edge_bottom = C("#FFFFFF", 150)
    else:
        base = C("#000000", 118)
        edge_top = C("#000000", 130)
        edge_bottom = C("#FFFFFF", 30)
    s.rect(0, 0, w, h, fill=base, radius=radius)
    slot = s.array()
    apply_mask(slot, top_line_mask(w, h, radius), edge_top)
    apply_mask(slot, left_line_mask(w, h, radius), edge_top)
    apply_mask(slot, bottom_line_mask(w, h, radius), edge_bottom)
    apply_mask(slot, right_line_mask(w, h, radius), edge_bottom)
    return slot


# ---- line masks ---------------------------------------------------------
def rounded_ring_mask(w, h, radius, inset=0):
    mask = rounded_mask(w, h, radius)
    inner = np.zeros_like(mask)
    if w - 2 * inset > 0 and h - 2 * inset > 0:
        inner[inset:h - inset, inset:w - inset] = rounded_mask(
            w - 2 * inset, h - 2 * inset, max(0, radius - inset))
    out = np.clip(mask.astype(np.int16) - inner.astype(np.int16), 0, 255)
    return out.astype(np.uint8)


def top_line_mask(w, h, radius, thick=1):
    m = np.zeros((h, w), dtype=np.uint8)
    m[0:thick, :] = 255
    return np.minimum(m, rounded_mask(w, h, radius))


def bottom_line_mask(w, h, radius, thick=1):
    m = np.zeros((h, w), dtype=np.uint8)
    m[h - thick:h, :] = 255
    return np.minimum(m, rounded_mask(w, h, radius))


def left_line_mask(w, h, radius, thick=1):
    m = np.zeros((h, w), dtype=np.uint8)
    m[:, 0:thick] = 255
    return np.minimum(m, rounded_mask(w, h, radius))


def right_line_mask(w, h, radius, thick=1):
    m = np.zeros((h, w), dtype=np.uint8)
    m[:, w - thick:w] = 255
    return np.minimum(m, rounded_mask(w, h, radius))


# --------------------------------------------------------------------------
# Icons / glyph helpers (drawn with shapes so they stay crisp at tiny sizes)
# --------------------------------------------------------------------------
def glyph_chevron(s, cx, cy, size, direction, color, width=1.5):
    a = size / 2.0
    if direction in ("right", "left"):
        pts = [(cx - a * (1 if direction == "right" else -1), cy - a),
               (cx + a * (1 if direction == "right" else -1), cy),
               (cx - a * (1 if direction == "right" else -1), cy + a)]
    else:
        pts = [(cx - a, cy - a * (1 if direction == "down" else -1)),
               (cx, cy + a * (1 if direction == "down" else -1)),
               (cx + a, cy - a * (1 if direction == "down" else -1))]
    s.line(pts, color, width)
    return s


def glyph_check(s, pts, color, width=2.0):
    s.line(pts, color, width)
    return s


def glyph_plus(s, cx, cy, size, color, width=1.0):
    a = size / 2.0
    s.line([(cx - a, cy), (cx + a, cy)], color, width)
    s.line([(cx, cy - a), (cx, cy + a)], color, width)
    return s


def glyph_search(s, cx, cy, r, color, width=1.0):
    s.ring(cx, cy, r - 1, color, width)
    d = (r - 1) * 0.72
    s.line([(cx + d, cy + d), (cx + r + 0.6, cy + r + 0.6)], color, width)
    return s


def heart_points(cx, cy, scale=1.0):
    """Symmetric heart outline as a point list, tailored for a 9x9 sprite."""
    pts = []
    for i in range(41):
        t = math.pi * (1.0 + i / 40.0)
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x / 16.0 * 4.05 * scale, cy - y / 16.0 * 3.55 * scale))
    return pts


def draw_heart(s, cx, cy, scale=1.0, fill=None, outline=None, ow=1.0):
    pts = heart_points(cx, cy, scale)
    s.poly(pts, fill)
    if outline is not None:
        s.line(pts + [pts[0]], outline, ow)
    return s


def save(img, path):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(img, np.ndarray):
        img = Image.fromarray(np.ascontiguousarray(img, dtype=np.uint8), "RGBA")
    img.save(path, optimize=True)
    return path


def save_arr(arr, path):
    return save(arr, path)
