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
import contextlib
import math

import numpy as np
from PIL import Image, ImageDraw

# --------------------------------------------------------------------------
# Resolution
# --------------------------------------------------------------------------
# GUI sprites are drawn on their own sprite atlas and the client maps whatever
# resolution the PNG has onto the logical GUI size, so they can ship at 4x and
# render sharp on high-DPI / high GUI-scale displays. Everything below draws in
# *logical* pixels; Surface multiplies by this factor when it resolves.
#
# Two things must stay at 1x and are handled outside this switch:
#   * container panels - 26.3 blits them as plain textures (u,v,w,h in texels),
#     so a bigger PNG would only show its top-left quarter;
#   * nine-slice sprites - the metadata border doubles as a screen-pixel size,
#     so scaling the art makes the corners render at the wrong thickness.
SCALE = 4


@contextlib.contextmanager
def logical():
    """Force 1x output for code that must stay on vanilla's pixel grid."""
    global SCALE
    prev = SCALE
    SCALE = 1
    try:
        yield
    finally:
        SCALE = prev


def pixels(v):
    """Logical pixels -> texture pixels at the current scale."""
    return int(round(v * SCALE))


scale_px = pixels


def upscale(arr, factor=None, smooth=True):
    """Resize an RGBA array by `factor`, premultiplied so edges don't fringe."""
    factor = factor or SCALE
    if factor == 1 or arr.size == 0:
        return arr
    h, w = arr.shape[:2]
    a = arr.astype(np.float32)
    al = a[..., 3:4] / 255.0
    a[..., :3] *= al
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    im = im.resize((w * factor, h * factor),
                   Image.LANCZOS if smooth else Image.NEAREST)
    a = np.asarray(im, np.float32)
    al = a[..., 3:4] / 255.0
    a[..., :3] /= np.maximum(al, 1e-6)
    return np.clip(a, 0, 255).astype(np.uint8)


def gradient(n, lo, hi):
    """Horizontal tonal ramp across `n` logical pixels, at the current scale."""
    return np.linspace(lo, hi, n * SCALE)[None, :, None]


def downscale(arr, factor=None):
    """Box-filter an RGBA array down by `factor`, premultiplied."""
    factor = factor or SCALE
    if factor == 1 or arr.size == 0:
        return arr
    h, w = arr.shape[:2]
    a = arr.astype(np.float32)
    al = a[..., 3:4] / 255.0
    a[..., :3] *= al
    a = a.reshape(h // factor, factor, w // factor, factor, 4).mean(axis=(1, 3))
    al = a[..., 3:4] / 255.0
    a[..., :3] /= np.maximum(al, 1e-6)
    return np.clip(a, 0, 255).astype(np.uint8)



def C(hexstr, a=255):
    """Hex string -> RGBA tuple."""
    h = hexstr.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(a))


def with_a(color, a):
    return (color[0], color[1], color[2], int(a))


# --------------------------------------------------------------------------
# ZeroUI tokens
# --------------------------------------------------------------------------
# Palette lifted from the user's own ZeroUI pack: one calm lavender-grey family
# plus a single green accent. Surfaces stay light and low-contrast; slots are a
# flat fill with a hairline, never a hard black well.
ACCENT = C("#4AA26F")
ACCENT_HOVER = C("#57B37C")
ACCENT_PRESSED = C("#357A52")
ACCENT_DARK = C("#3A8459")
ACCENT_LIGHT = C("#8CCFA9")
ACCENT_PALE = C("#EAF5EE")
ACCENT_WASH = C("#D9ECDF")

MICA = C("#B4AFB9")
MICA_BRIGHT = C("#C3BEC8")
MICA_DEEP = C("#A09BA5")
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
    """Supersampled RGBA canvas that resolves to SCALE x pixel dimensions."""

    def __init__(self, w, h, ss=4):
        self.w = int(w)
        self.h = int(h)
        # Drawing happens in logical units; the canvas is SCALE times denser and
        # then supersampled on top of that for anti-aliasing. Cap the extra
        # supersampling as the scale grows so big panels stay affordable.
        self.ss = min(int(ss), max(1, 8 // max(1, SCALE)))
        self.s = self.ss * SCALE
        self.px = Image.new("RGBA", (self.w * self.s, self.h * self.s),
                            (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.px)

    # -- primitives ------------------------------------------------------
    def _box(self, x, y, w, h):
        s = self.s
        return [x * s, y * s, (x + w) * s - 1, (y + h) * s - 1]

    def rect(self, x, y, w, h, fill=None, radius=0, outline=None, ow=1):
        box = self._box(x, y, w, h)
        r = radius * self.s
        if radius > 0:
            self.d.rounded_rectangle(box, radius=r, fill=fill)
            if outline:
                self.d.rounded_rectangle(box, radius=r, outline=outline,
                                         width=max(1, int(round(ow * self.s))))
        else:
            self.d.rectangle(box, fill=fill)
            if outline:
                self.d.rectangle(box, outline=outline,
                                 width=max(1, int(round(ow * self.s))))
        return self

    def pixel(self, x, y, fill):
        s = self.s
        self.d.rectangle([x * s, y * s, x * s + s - 1, y * s + s - 1], fill=fill)
        return self

    def line(self, pts, fill, width=1):
        s = self.s
        scaled = [(p[0] * s + s / 2.0, p[1] * s + s / 2.0) for p in pts]
        self.d.line(scaled, fill=fill, width=max(1, int(round(width * s))),
                    joint="curve")
        return self

    def poly(self, pts, fill):
        s = self.s
        self.d.polygon([(p[0] * s, p[1] * s) for p in pts], fill=fill)
        return self

    def ellipse(self, x, y, w, h, fill=None, outline=None, ow=1):
        s = self.s
        box = [x * s, y * s, (x + w) * s - 1, (y + h) * s - 1]
        self.d.ellipse(box, fill=fill, outline=outline,
                       width=max(1, int(round(ow * s))))
        return self

    def ring(self, cx, cy, r, fill, width=1):
        self.ellipse(cx - r, cy - r, r * 2, r * 2, outline=fill, ow=width)
        return self

    # -- compositing ----------------------------------------------------
    def blit(self, arr, x=0, y=0):
        """Composite a 1x RGBA numpy array at integer logical coordinates."""
        if arr is None or arr.size == 0:
            return self
        img = Image.fromarray(np.ascontiguousarray(arr, dtype=np.uint8), "RGBA")
        if self.s != 1:
            img = img.resize((img.width * self.s, img.height * self.s),
                             Image.NEAREST)
        self.px.alpha_composite(img, (int(x * self.s), int(y * self.s)))
        return self

    # -- resolve --------------------------------------------------------
    def array(self):
        a = np.asarray(self.px, dtype=np.float32)
        s = self.ss
        if s > 1:
            al = a[..., 3:4] / 255.0
            a[..., :3] *= al
            a = a.reshape(self.h * SCALE, s, self.w * SCALE, s, 4).mean(
                axis=(1, 3))
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
    x, y, w, h = x * SCALE, y * SCALE, w * SCALE, h * SCALE
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
    x, y, w, h = x * SCALE, y * SCALE, w * SCALE, h * SCALE
    rng = np.random.default_rng(seed)
    region = arr[y:y + h, x:x + w, :3].astype(np.float32)
    g = rng.normal(0.0, amount, size=(h, w, 1))
    region += g
    np.clip(region, 0, 255, out=region)
    arr[y:y + h, x:x + w, :3] = region.astype(np.uint8)
    return arr


def over(dst, src, x=0, y=0):
    """Alpha-composite src (RGBA at the current scale) onto dst in place."""
    x, y = int(round(x * SCALE)), int(round(y * SCALE))
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
    return np.zeros((h * SCALE, w * SCALE, 4), dtype=np.uint8) + \
        np.array(fill, dtype=np.uint8)


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
def mica_panel(arr, x, y, w, h, radius=0, base=MICA, alpha=232, shadow=False):
    """ZeroUI surface: one flat tonal fill, square corners, no stroke.

    The reference pack draws every panel as a single colour with a 1px darker
    frame at most. Gradients, hairlines and noise read as dirt at GUI scale 3,
    so the surface is deliberately bare.
    """
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=with_a(base, alpha), radius=radius)
    over(arr, s.array(), x, y)
    return arr


def acrylic_panel(arr, x, y, w, h, radius=0, base=ACRYLIC, alpha=None,
                  shadow=False, grain=0):
    """Same flat treatment for dark overlay chrome (tooltips, toasts, HUD)."""
    a = alpha if alpha is not None else base[3]
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=(base[0], base[1], base[2], a), radius=radius)
    over(arr, s.array(), x, y)
    return arr


def fluent_button(w, h, state="normal", radius=0, accent=ACCENT):
    """ZeroUI button: a flat rectangle. Neutral lavender at rest, accent only
    while focused, muted grey when disabled - matching (180,175,185) /
    (74,162,111) / (130,125,135) in the reference pack."""
    s = Surface(w, h, ss=4)
    if state == "disabled":
        fill = with_a(C("#827D87"), 160)
    elif state == "highlighted":
        fill = with_a(accent, 220)
    else:
        fill = with_a(MICA, 240)
    s.rect(0, 0, w, h, fill=fill, radius=radius)
    return s.array()


def fluent_slot(w=18, h=18, radius=0, surface="light"):
    """ZeroUI slot: the panel tone lifted one step, flat, square, no stroke.

    The reference pack reads (195,190,200) slots on a (180,175,185) panel; the
    lighter fill carries the "well" without a dark hole or inner shadow.
    """
    s = Surface(w, h, ss=4)
    alpha = 255 if surface == "light" else 200
    s.rect(0, 0, w, h, fill=with_a(MICA_BRIGHT, alpha), radius=radius)
    return s.array()


# ---- line masks ---------------------------------------------------------
def rounded_ring_mask(w, h, radius, inset=0):
    mask = rounded_mask(w, h, radius)
    inner = np.zeros_like(mask)
    i = inset * SCALE
    if w * SCALE - 2 * i > 0 and h * SCALE - 2 * i > 0:
        inner[i:h * SCALE - i, i:w * SCALE - i] = rounded_mask(
            w - 2 * inset, h - 2 * inset, max(0, radius - inset))
    out = np.clip(mask.astype(np.int16) - inner.astype(np.int16), 0, 255)
    return out.astype(np.uint8)


def top_line_mask(w, h, radius, thick=1):
    m = np.zeros((h * SCALE, w * SCALE), dtype=np.uint8)
    m[0:thick * SCALE, :] = 255
    return np.minimum(m, rounded_mask(w, h, radius))


def bottom_line_mask(w, h, radius, thick=1):
    m = np.zeros((h * SCALE, w * SCALE), dtype=np.uint8)
    m[h * SCALE - thick * SCALE:h * SCALE, :] = 255
    return np.minimum(m, rounded_mask(w, h, radius))


def left_line_mask(w, h, radius, thick=1):
    m = np.zeros((h * SCALE, w * SCALE), dtype=np.uint8)
    m[:, 0:thick * SCALE] = 255
    return np.minimum(m, rounded_mask(w, h, radius))


def right_line_mask(w, h, radius, thick=1):
    m = np.zeros((h * SCALE, w * SCALE), dtype=np.uint8)
    m[:, w * SCALE - thick * SCALE:w * SCALE] = 255
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
