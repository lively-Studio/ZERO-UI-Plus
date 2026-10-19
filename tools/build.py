#!/usr/bin/env python3
"""Assemble the ZERO-UI+ resource pack.

Pipeline
--------
1. Run every texture builder (widgets, HUD, container chrome, menus, ...).
2. Verify each generated sprite against the vanilla manifest: a sprite that
   exists in vanilla must keep its *exact* pixel dimensions, because Minecraft
   hard codes GUI geometry and would clip or smear anything else.
3. Copy vanilla's `<sprite>.png.mcmeta` nine-slice metadata for every sprite we
   replace, so the pack inherits the authoritative slice borders. Sprites that
   vanilla ships as plain blits get no metadata (matching vanilla semantics).
4. Emit pack.mcmeta, pack.png and a coverage report.

Usage
-----
    python3 tools/build.py --jar client.jar [--out pack]

`--jar` is required for the manifest/metadata step; it produces a standalone
resource pack directory ready to drop into `.minecraft/resourcepacks/`.
"""
import argparse
import io
import json
import os
import shutil
import struct
import sys
import zipfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import textures            # noqa: E402
import textures_ui         # noqa: E402
import containers          # noqa: E402
import extras              # noqa: E402
import restyle             # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = "assets/minecraft/"

# 26.3 resource pack format: the client accepts terms between min_format and
# max_format inclusive, so one pack.mcmeta covers a range of versions.
PACK_MIN_FORMAT = 63
PACK_MAX_FORMAT = 110
PACK_FORMAT = 97
PACK_DESCRIPTION = "ZERO-UI+ · a modern Fluent-style interface overhaul by lively-Studio"
PACK_NAME = "ZERO-UI+"


def load_manifest(jar):
    z = zipfile.ZipFile(jar)
    out = {}
    for name in z.namelist():
        if name.startswith(ASSETS + "textures/gui/") and name.endswith(".png"):
            raw = z.read(name)
            w, h = struct.unpack(">II", raw[16:24])
            out[name[len(ASSETS):]] = (w, h)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jar", required=True, help="vanilla client jar")
    ap.add_argument("--out", default=os.path.join(ROOT, "pack"))
    ap.add_argument("--strict", action="store_true",
                    help="fail on missing coverage instead of reporting it")
    args = ap.parse_args()

    manifest = load_manifest(args.jar)
    jar = zipfile.ZipFile(args.jar)

    def read_vanilla(rel):
        """path (relative to assets/minecraft/) -> RGBA ndarray, for the
        container pipeline that re-draws on top of the vanilla art."""
        return np.array(Image.open(io.BytesIO(jar.read(ASSETS + rel))).convert("RGBA"))

    print("building textures ...")
    built = {}
    for label, part in (("widgets", textures.widgets()),
                        ("hud", textures.hud()),
                        ("boss bars", textures.boss_bars()),
                        ("creative tabs", textures.creative_tabs()),
                        ("container sprites", textures.container_sprites()),
                        ("container panels", containers.build_all(read_vanilla)),
                        ("remaining sprites", extras.build_all(read_vanilla)),
                        ("ui chrome", textures_ui.build_all())):
        clash = set(part) & set(built)
        if clash:
            raise SystemExit("duplicate texture keys in %s: %s" % (label,
                                                                   sorted(clash)))
        print("  %-20s %4d sprites" % (label, len(part)))
        built.update(part)

    # ---- dimension validation ------------------------------------------
    errors = []
    additions = []
    for path, arr in built.items():
        if path not in manifest:
            additions.append(path)
            continue
        want = manifest[path]
        got = (arr.shape[1], arr.shape[0])
        if want != got:
            errors.append("%s: generated %s but vanilla is %s" % (path, got, want))
    if errors:
        print("\nDIMENSION MISMATCHES (%d):" % len(errors))
        for e in errors[:60]:
            print("   " + e)
        raise SystemExit("aborting: fix dimensions before shipping")

    # ---- art-class re-tint ---------------------------------------------
    # Glyphs whose shape carries the meaning keep vanilla's silhouette and get
    # the Fluent palette; only the redrawn chrome survives from the builders.
    restyled = 0
    kept = 0
    for path in list(built):
        if path not in manifest:
            continue
        vanilla = read_vanilla(path)
        out = restyle.restyle(path, vanilla)
        if out is None:
            continue
        if np.array_equal(out, vanilla):
            kept += 1
        else:
            restyled += 1
        built[path] = out
    print("re-tinted %d vanilla glyphs (%d left verbatim)"
          % (restyled, kept))

    # ---- silhouette audit ----------------------------------------------
    # A redrawn sprite whose alpha mask disagrees with vanilla's is a bug
    # waiting to happen (a glyph overlay turned into a filled tile hides the
    # button behind it). Report every disagreement so it gets reviewed.
    # The threshold allows for corner rounding - a Fluent panel squares off
    # ~30% of its mask against vanilla's hard-cornered one - so anything below
    # that is a change of geometry, not of corner treatment.
    suspects = []
    for path, arr in built.items():
        if path not in manifest:
            continue
        vanilla = read_vanilla(path)
        if vanilla.shape != arr.shape:
            continue
        ma, mb = vanilla[:, :, 3] > 48, arr[:, :, 3] > 48
        union = int((ma | mb).sum())
        if union < 12:
            continue
        iou = int((ma & mb).sum()) / union
        if iou < 0.70:
            suspects.append((round(iou, 2), path))
    suspects.sort()

    # ---- write files ---------------------------------------------------
    pack_root = args.out
    if os.path.isdir(pack_root):
        shutil.rmtree(pack_root)
    written = 0
    for path, arr in sorted(built.items()):
        dst = os.path.join(pack_root, ASSETS, path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        Image.fromarray(np.ascontiguousarray(arr, dtype=np.uint8), "RGBA").save(
            dst, optimize=True)
        written += 1
        # inherit vanilla nine-slice metadata (keeps slice borders authoritative)
        meta = ASSETS + path + ".mcmeta"
        if meta in jar.namelist():
            with open(dst + ".mcmeta", "wb") as f:
                f.write(jar.read(meta))

    # ---- pack.mcmeta / pack.png ---------------------------------------
    with open(os.path.join(pack_root, "pack.mcmeta"), "w") as f:
        json.dump({
            "pack": {
                "description": PACK_DESCRIPTION,
                "pack_format": PACK_FORMAT,
                "min_format": PACK_MIN_FORMAT,
                "max_format": PACK_MAX_FORMAT,
            }
        }, f, indent=2)
    Image.fromarray(np.ascontiguousarray(textures_ui.pack_icon(128),
                                         dtype=np.uint8), "RGBA").save(
        os.path.join(pack_root, "pack.png"))

    # ---- coverage report ----------------------------------------------
    covered = sorted(built)
    gui_all = sorted(k for k in manifest if k.startswith("textures/gui/"))
    sprites_all = sorted(k for k in gui_all
                         if k.startswith("textures/gui/sprites/"))
    containers_all = sorted(k for k in gui_all
                            if k.startswith("textures/gui/container/"))
    remaining = [k for k in sprites_all if k not in built]
    report = {
        "pack": PACK_NAME,
        "generated": len(built),
        "additions_not_in_vanilla": additions,
        "sprites_total": len(sprites_all),
        "sprites_covered": len([k for k in sprites_all if k in built]),
        "containers_total": len(containers_all),
        "containers_covered": len([k for k in containers_all if k in built]),
        "covered": covered,
        "shape_suspects": [{"iou": i, "sprite": p} for i, p in suspects],
        "sprites_not_covered": remaining,
        "containers_not_covered": [k for k in containers_all if k not in built],
    }
    os.makedirs(os.path.join(ROOT, "tools"), exist_ok=True)
    with open(os.path.join(ROOT, "tools", "coverage.json"), "w") as f:
        json.dump(report, f, indent=1)

    print("\nwrote %d sprites to %s" % (written, pack_root))
    print("sprites covered: %d/%d  container guis: %d/%d"
          % (report["sprites_covered"], report["sprites_total"],
             report["containers_covered"], report["containers_total"]))
    if additions:
        print("new sprites not present in vanilla: %d" % len(additions))
    if remaining:
        print("sprites still on vanilla art: %d" % len(remaining))
    if suspects:
        print("redrawn sprites whose silhouette differs from vanilla: %d"
              % len(suspects))
        for iou, p in suspects[:25]:
            print("   %.2f  %s" % (iou, p.replace("textures/gui/", "")))
        if len(suspects) > 25:
            print("   ... %d more" % (len(suspects) - 25))
    if args.strict and (remaining or additions):
        raise SystemExit("strict mode: incomplete coverage")


if __name__ == "__main__":
    main()
