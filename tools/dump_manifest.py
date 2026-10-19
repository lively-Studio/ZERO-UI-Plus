#!/usr/bin/env python3
"""Dump every GUI texture path + dimension from a vanilla client jar.

Usage: python3 tools/dump_manifest.py <client.jar> [out.json]

The resulting manifest is the ground truth for the pack: GUI geometry in
Minecraft is hard coded in pixels, so every replacement texture must keep the
exact width/height of its vanilla counterpart.
"""
import io
import json
import struct
import sys
import zipfile


def png_size(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a png")
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def main():
    jar = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "tools/vanilla_manifest.json"
    z = zipfile.ZipFile(jar)
    prefix = "assets/minecraft/textures/gui/"
    entries = {}
    for name in z.namelist():
        if not (name.startswith(prefix) and name.endswith(".png")):
            continue
        w, h = png_size(z.read(name))
        entries[name[len("assets/minecraft/"):]] = [w, h]
    doc = {"source": jar, "namespace": "gui", "count": len(entries), "textures": entries}
    with open(out, "w") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
    print("wrote %s (%d entries)" % (out, len(entries)))


if __name__ == "__main__":
    main()
