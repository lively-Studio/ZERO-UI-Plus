#!/usr/bin/env python3
"""Container GUI redraw pipeline.

Design
------
Modern Minecraft keeps every container's *functional* graphics (furnace flame,
brewing bubbles, progress arrows, maps, error marks, ghost-item hints) in
separate `gui/sprites/container/...` files. The 256x256 `gui/container/*.png`
panels therefore only contain:

  * the window chrome - a 1px outline plus the classic 6-tone grey ramp
    (0, 55, 85, 139, 198, 255)
  * 18x18 slot wells (a uniform 139 fill inside a light/dark bevel)
  * a few grey affordances drawn in that same ramp (the crafting arrow, the
    villager trade backdrop, the loom preview frame, ...)

That makes a full Fluent rebuild possible: paint a light Mica panel over the
window rect, drop the grey chrome, then re-draw the wells and the handful of
in-texture affordances Fluent style. Coloured artwork (the enchanting table's
book, the beacon beam, the cartography maps) is pixel-copied so nothing
decorative is lost.

Text colour is the hard constraint here
---------------------------------------
Minecraft hard codes container text to a dark grey (0x404040), so container
panels - and only container panels - get the *light* Mica treatment. The dark
Acrylic treatment is reserved for the screens whose text is white (menus, lists,
tooltips, toasts, HUD).

Variable-height containers
--------------------------
Chests are drawn in two pieces: the client blits texture rows 0..124 cropped to
`17 + rows*18`, then blits rows 125..221 underneath. The single rounded panel
below spans the whole 176x222 window, so both pieces join on flat interior rows
and the visible top and bottom corners stay rounded.
"""
import numpy as np

from fluent import (ACCENT, ACCENT_DARK, ACCENT_LIGHT, C, MICA, MICA_BRIGHT,
                    STROKE,
                    SURFACE_DARKER, Surface, apply_mask, bottom_line_mask,
                    fluent_slot, over, rounded_ring_mask, shade_rows,
                    top_line_mask, with_a)

PANEL_DIR = "textures/gui/container/"

# Windows whose chrome is drawn as a single crop of the top-left of the texture.
PANELS = [
    "inventory", "crafting_table", "furnace", "generic_54", "hopper",
    "dispenser", "shulker_box", "anvil", "beacon", "brewing_stand",
    "enchanting_table", "grindstone", "loom", "smithing", "smoker",
    "blast_furnace", "stonecutter", "cartography_table", "crafter", "horse",
    "villager", "nautilus", "creative_inventory/tab_inventory",
    "creative_inventory/tab_items", "creative_inventory/tab_item_search",
]

# Wells the detector cannot see because vanilla drew them merged into a taller
# run of grey. Brewing stand slot coordinates from the container layout:
# fuel (17,17), ingredient (79,17), bottles (56,51), (79,58), (102,51).
WELL_OVERRIDES = {
    "brewing_stand": [(16, 16), (78, 16), (55, 50), (100, 50), (77, 57)],
}

FILL = 139          # vanilla slot fill grey
CHROME = 3          # px of window edge treated as chrome
RADIUS = 6          # window corner radius (<= the declared nine-slice border)
BAND = 1            # border band that never carries meaningful art

_reader = None


def set_reader(fn):
    """Inject the vanilla texture loader (path -> RGBA ndarray)."""
    global _reader
    _reader = fn


def vanilla(path):
    return _reader(path)


def _ndimage():
    from scipy import ndimage
    return ndimage


CROSS = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
FULL = np.ones((3, 3), bool)


def label(mask, structure):
    """Connected components as (labels, count), scipy-backed with a BFS
    fallback so the toolchain still runs without scipy installed."""
    try:
        return _ndimage().label(mask, structure=structure)
    except Exception:  # pragma: no cover - dev has scipy, shipping does not need it
        h, w = mask.shape
        lab = np.zeros((h, w), np.int32)
        n = 0
        offsets = ([(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                    if (dy, dx) != (0, 0) and structure[dy + 1, dx + 1]]
                   if structure.shape == (3, 3) else [(0, -1), (-1, 0), (1, 0), (0, 1)])
        for sy in range(h):
            for sx in range(w):
                if not mask[sy, sx] or lab[sy, sx]:
                    continue
                n += 1
                stack = [(sy, sx)]
                lab[sy, sx] = n
                while stack:
                    cy, cx = stack.pop()
                    for dy, dx in offsets:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                            lab[ny, nx] = n
                            stack.append((ny, nx))
        return lab, n


# --------------------------------------------------------------------------
# panel analysis
# --------------------------------------------------------------------------
def panel_bbox(a):
    ys, xs = np.where(a[:, :, 3] > 0)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def is_grey(a):
    r, g, b = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    return (np.abs(r - g) <= 2) & (np.abs(g - b) <= 2)


def fill_mask(a):
    return (a[:, :, 0] == FILL) & (a[:, :, 1] == FILL) & \
        (a[:, :, 2] == FILL) & (a[:, :, 3] > 0)


def bbox_of(comp):
    ys, xs = np.where(comp)
    x0, y0 = int(xs.min()), int(ys.min())
    return x0, y0, int(xs.max()) - x0 + 1, int(ys.max()) - y0 + 1


def bevel_wells(a, blocked):
    """16x16 uniform 139 blocks whose surrounding ring is *not* also 139 - i.e.
    wells enclosed by a bevel. Catches wells vanilla drew inside a taller grey
    run, where component analysis alone would merge them into a blob."""
    h, w = a.shape[:2]
    inner = fill_mask(a)
    out = []
    for y in range(1, h - 17):
        for x in range(1, w - 17):
            if not inner[y:y + 16, x:x + 16].all():
                continue
            if blocked[y + 8, x + 8]:
                continue
            ring = np.concatenate([a[y - 1, x:x + 16, 0], a[y + 16, x:x + 16, 0],
                                   a[y:y + 16, x - 1, 0], a[y:y + 16, x + 16, 0]])
            if (ring == FILL).all():
                continue
            out.append((x - 1, y - 1))
    return out


def flat_boxes(a, region):
    """Rectangles vanilla walls off from the panel face with a 1px bevel.

    Two of these have no slot fill to key on, so component analysis over the
    139 grey alone misses them:

      * entity preview paddocks - a solid black pane (horse, nautilus, creative
        player preview) the client draws a live 3D model over
      * the horse's inventory preview - a face-grey box ringed by a bevel

    Both read as their own flat component once the bevel merges in, and both
    have a uniform interior, which is what makes them recognisable here.
    """
    out = []
    solid = a[:, :, 3] > 0
    grey = solid & region & is_grey(a)
    for tone in np.unique(a[:, :, 0][grey]):
        m = grey & (a[:, :, 0] == tone) & (a[:, :, 1] == tone) & \
            (a[:, :, 2] == tone)
        lab, n = label(m, CROSS)
        sizes = np.bincount(lab.ravel(), minlength=n + 1)
        for i in range(1, n + 1):
            area = int(sizes[i])
            if area < 300:
                continue
            comp = lab == i
            bx, by, w, h = bbox_of(comp)
            if w < 8 or h < 8 or w > 120 or h > 120:
                continue
            # a pane is a solid rect: anything with bites taken out of it is
            # the panel face, not a box
            if area < 0.9 * w * h:
                continue
            if int(tone) == FILL:
                continue  # already collected as a slot slab
            out.append((bx, by, w, h, int(tone)))
    return out


def black_panes(a, region):
    """Solid near-black rectangles: the paddocks vanilla reserves for a live
    3D model (player preview, horse, nautilus). Pure black punches a hole in a
    light panel, so they are found here and re-toned instead."""
    dark = region & (a[:, :, 3] > 0) & (a[:, :, :3].max(axis=2) < 24)
    lab, n = label(dark, CROSS)
    out = []
    for i in range(1, n + 1):
        comp = lab == i
        area = int(comp.sum())
        if area < 500:
            continue
        bx, by, w, h = bbox_of(comp)
        if w < 20 or h < 20 or w > 120 or h > 120:
            continue
        if area < 0.85 * w * h:
            continue
        out.append((bx, by, w, h))
    return out


def long_runs(mask, min_len):
    """Pixels sitting in a horizontal or vertical run of at least `min_len`.
    Vanilla chrome is made of long straight 1px lines (window frames, slot grid
    outlines), so this separates "frame" grey from compact grey artwork."""
    out = np.zeros_like(mask)
    for m, dst in ((mask, out), (mask.T, out.T)):
        pad = np.zeros((m.shape[0], m.shape[1] + 2), bool)
        pad[:, 1:-1] = m
        d = np.diff(pad.astype(np.int8), axis=1)
        for y in range(m.shape[0]):
            starts = np.where(d[y] == 1)[0]
            ends = np.where(d[y] == -1)[0]
            for s, e in zip(starts, ends):
                if e - s >= min_len:
                    dst[y, s - 1:e - 1] = True
    return out


def face_color(a, bbox, occupied):
    """The panel's flat backdrop - i.e. the grey vanilla leaves empty.

    Measured over the pixels that no known feature owns: taking the plain mode
    of the whole window instead would let a large list backdrop (the villager's
    88x140 trade slab) outvote the actual face, which then hides in-texture
    artwork drawn in that same grey (the villager's trade arrow)."""
    x0, y0, x1, y1 = bbox
    win = a[y0:y1 + 1, x0:x1 + 1]
    flat = (win[:, :, 3] > 0) & is_grey(win) & ~occupied[y0:y1 + 1, x0:x1 + 1]
    vals = win[:, :, 0][flat]
    if len(vals) == 0:
        return 198
    return int(np.bincount(vals, minlength=256).argmax())


def dedupe(points, gap=18):
    """Collapse scan hits that describe the same well, first-come-first-served
    in reading order so the top-left corner of a run wins."""
    keep = []
    for x, y in sorted(points, key=lambda t: (t[1], t[0])):
        if any(abs(x - ox) < gap and abs(y - oy) < gap for ox, oy in keep):
            continue
        keep.append((x, y))
    return keep


def analyze(a, bbox, extra_wells=()):
    """Classify a panel into wells / big slots / insets / arrows / keep.

    Everything is derived from the 139 slot fill (the only solid geometry
    vanilla rasterises into these textures); the remaining grey is chrome,
    bevels or hand-placed affordances, and each of those is either dropped or
    preserved verbatim.
    """
    x0, y0, x1, y1 = bbox
    region = np.zeros(a.shape[:2], dtype=bool)
    region[y0:y1 + 1, x0:x1 + 1] = True
    solid = a[:, :, 3] > 0

    wells, bigs, insets, arrows, vaults = [], [], [], [], []
    blocked = np.zeros(a.shape[:2], dtype=bool)

    # panes with no slot fill to key on: entity previews, the horse's inventory
    # box, the beacon's effect lists. Dark ones become dark insets, the rest
    # join the ordinary recessed insets; a 20..30px square is an oversized slot
    # (the crafter's result box is a face-grey pane in a 139 ring).
    for bx, by, w, h, tone in flat_boxes(a, region):
        if 20 <= w <= 30 and 20 <= h <= 30:
            bigs.append((bx, by, w, h))
        elif tone <= 40:
            vaults.append((bx, by, w, h))
        else:
            insets.append((bx, by, w, h))
        blocked[by:by + h, bx:bx + w] = True

    lab, n = label(fill_mask(a), CROSS)
    sizes = np.bincount(lab.ravel(), minlength=n + 1)
    for i in range(1, n + 1):
        if sizes[i] < 8:
            continue
        comp = lab == i
        bx, by, w, h = bbox_of(comp)
        area = int(sizes[i])
        ratio = area / float(w * h)
        if 15 <= w <= 19 and 15 <= h <= 19 and 180 <= area <= 400 and ratio >= 0.75:
            wells.append((bx - 1, by - 1))
            continue
        if 13 <= w <= 14 and 13 <= h <= 14 and area >= 150 and ratio >= 0.9:
            # the crafter's 3x3 grid is baked in the old slot art: a 14px fill
            # inside an 18px cell, so its border is 2px and not 1px
            wells.append((bx - 2, by - 2))
            continue
        if 20 <= w <= 30 and 20 <= h <= 30 and area >= 420:
            # oversized result wells; their interior must not be re-scanned for
            # hidden slots (the bevel scan would report a phantom 16x16 inside)
            bigs.append((bx, by, w, h))
            blocked[by:by + h, bx:bx + w] = True
            continue
        if area >= 420 and ratio >= 0.85:
            # flat grey slabs: list backdrops, scroll tracks, search fields.
            # Villager's trade list (88x140) and scroll track (6x140) live here.
            insets.append((bx, by, w, h))
            blocked[by:by + h, bx:bx + w] = True
            continue
        # a flat grey slab is a list/preview backdrop; wells vanilla merged into
        # one of these can only be re-found by scanning its bevels
        if ratio >= 0.8 and w * h >= 400:
            blocked[by:by + h, bx:bx + w] = True

    # a well can also be an 18px window inside a bigger grey run
    for x, y in bevel_wells(a, blocked):
        wells.append((x, y))
    wells.extend(extra_wells)
    wells = dedupe(wells)

    # geometry the Fluent re-draw already covers: nothing left of vanilla's
    # grey should be copied back on top of it
    explain = np.zeros(a.shape[:2], dtype=bool)
    for x, y in wells:
        explain[y:y + 18, x:x + 18] = True
    for bx, by, w, h in bigs:
        explain[by - 1:by + h + 1, bx - 1:bx + w + 1] = True
    for bx, by, w, h in insets:
        # +1px bevel: vanilla caps slabs with a highlight line that must not be
        # copied back on top of the Fluent inset drawn in its place
        explain[max(0, by - 1):by + h + 1, max(0, bx - 1):bx + w + 1] = True
    for bx, by, w, h in vaults:
        # +1px bevel ring, same as the insets. Inside, only the pane's own flat
        # dark fill is replaced by the Fluent inset - anything coloured vanilla
        # baked into it (the beacon's green list arrows) has to survive the
        # wipe, so it is left out of `explain` and lands in `keep` instead.
        explain[max(0, by - 1):by + h + 1, max(0, bx - 1):bx + w + 1] = True
        inner = a[by:by + h, bx:bx + w]
        explain[by:by + h, bx:bx + w] = ~((inner[:, :, 3] > 0) & ~is_grey(inner))

    band = np.zeros(a.shape[:2], dtype=bool)
    band[y0:y0 + CHROME, x0:x1 + 1] = True
    band[y1 - CHROME + 1:y1 + 1, x0:x1 + 1] = True
    band[y0:y1 + 1, x0:x0 + CHROME] = True
    band[y0:y1 + 1, x1 - CHROME + 1:x1 + 1] = True

    art = solid & region & ~band & ~explain
    grey = is_grey(a)

    # everything coloured inside the window is real artwork (the enchanting
    # table's book, the cartography maps, the crafting previews): keep it all
    keep = art & ~grey

    # grey artwork is whatever is NOT vanilla's frame: the flat backdrop is
    # irrelevant, long straight runs are chrome, and a 22x12 glyph is the
    # in-texture progress arrow
    candidate = art & grey & (a[:, :, 0] != face_color(a, (x0, y0, x1, y1),
                                                        explain))
    grey_art = candidate & ~long_runs(candidate, 24)
    lab2, n2 = label(grey_art, FULL)
    for i in range(1, n2 + 1):
        comp = lab2 == i
        area = int(comp.sum())
        if area < 6:
            continue
        bx, by, w, h = bbox_of(comp)
        if 14 <= w <= 26 and 8 <= h <= 20 and area <= 170:
            arrows.append((bx, by, w, h))
            continue
        if h <= 2 or w <= 2:
            # hairline leftovers of a vanilla border whose long runs were
            # stripped above (the grindstone's frame caps, the loom's hatch
            # ticks). They carry nothing on their own and read as stray ticks
            # sitting on the Fluent panel.
            continue
        keep |= comp

    return {"wells": wells, "bigs": bigs, "insets": insets, "arrows": arrows,
            "vaults": vaults, "keep": keep, "solid": solid, "region": region}


# --------------------------------------------------------------------------
# fluent re-draw
# --------------------------------------------------------------------------
def redraw(name):
    src = vanilla(PANEL_DIR + name + ".png")
    x0, y0, x1, y1 = panel_bbox(src)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    info = analyze(src, (x0, y0, x1, y1), WELL_OVERRIDES.get(name, ()))

    # window region = the window rect minus any interior transparent cut-outs
    region = np.ones((h, w), dtype=bool)
    holes = label(~info["solid"][y0:y1 + 1, x0:x1 + 1], FULL)[0]
    nh = label(~info["solid"][y0:y1 + 1, x0:x1 + 1], FULL)[1]
    border_touch = np.zeros((h, w), dtype=bool)
    border_touch[0, :] = border_touch[-1, :] = True
    border_touch[:, 0] = border_touch[:, -1] = True
    for i in range(1, nh + 1):
        comp = holes == i
        if (comp & border_touch).any():
            continue  # outside the window (or an open corner)
        region &= ~comp

    out = np.zeros(src.shape, dtype=np.uint8)

    # 1. solid ZeroUI window: one flat tone, square corners, no stroke
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=with_a(MICA, 255), radius=0)
    panel = s.array()
    panel[..., 3] = (panel[..., 3].astype(np.float32)
                     * region.astype(np.float32)).astype(np.uint8)
    over(out, panel, x0, y0)

    # 2. list / preview / scroll-track backdrops become inset Fluent wells, and
    #    panes the client renders a live model or icon list into go dark
    for bx, by, bw, bh in info["insets"]:
        over(out, inset_panel(bw, bh), bx, by)
    for bx, by, bw, bh in info["vaults"]:
        over(out, dark_pane(bw, bh), bx, by)

    # 3. hand-placed affordances vanilla drew in flat grey survive verbatim
    #    (coloured art wins over the inset backdrop it may sit on)
    keep = info["keep"].copy()
    for bx, by, bw, bh in black_panes(src, info["region"]):
        over(out, preview_pane(bw, bh), bx, by)
        keep[by:by + bh, bx:bx + bw] = False
    if keep.any():
        layer = np.zeros_like(src)
        layer[keep] = src[keep]
        over(out, layer)

    # 4. slot wells - including the oversized crafting result wells
    for sx, sy in info["wells"]:
        over(out, fluent_slot(18, 18, surface="light"), sx, sy)
    for bx, by, bw, bh in info["bigs"]:
        over(out, fluent_slot(bw + 2, bh + 2, surface="light"), bx - 1, by - 1)

    # 5. in-texture progress arrows become Fluent chevrons
    for bx, by, bw, bh in info["arrows"]:
        over(out, flow_arrow(bw, bh), bx, by)

    return out


def inset_panel(w, h, radius=0):
    """A recessed surface for lists, previews and scroll tracks: the same flat
    lift the slots use, so lists and grids read as one family."""
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=with_a(MICA_BRIGHT, 255), radius=radius)
    return s.array()


def dark_pane(w, h, radius=0):
    """Panes the client paints itself (live entity previews, beacon effect
    lists). The reference pack backs these with (150,145,155), dark enough for
    a model silhouette yet still part of the lavender family."""
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=(150, 145, 155, 245), radius=radius)
    return s.array()


def preview_pane(w, h, radius=0):
    """Backing for the player-model paddock - same tone as dark_pane, no
    rounding, so it sits flush with the flat window around it."""
    s = Surface(w, h, ss=4)
    s.rect(0, 0, w, h, fill=(150, 145, 155, 245), radius=radius)
    return s.array()


def flow_arrow(w, h):
    """Fluent replacement for vanilla's in-texture progress arrow: a soft
    accent chevron that reads clearly on the light panel."""
    s = Surface(w, h, ss=4)
    cy = h / 2.0
    tip = w - 1.2
    back = max(1.2, tip - min(w * 0.6, h * 0.66))
    s.line([(back, 1.4), (tip, cy), (back, h - 1.4)], ACCENT,
           max(1.8, h * 0.2))
    return s.array()


def build_all(reader):
    set_reader(reader)
    out = {}
    for name in PANELS:
        out[PANEL_DIR + name + ".png"] = redraw(name)
    return out
