#!/usr/bin/env python3
"""
Build the responsive image set for the Eime Steine site.

The website itself has no build step and no runtime dependencies. This script
only prepares images when the photo collection changes. It needs Python 3 and
ImageMagick 7 (`magick`).

Usage:
    python3 tools/build-images.py            # skip files that already exist
    python3 tools/build-images.py --force    # rebuild everything

Output:
    galerij/opt/<slug>-<width>.jpg|webp       full photo, for the lightbox
    galerij/opt/<slug>-thumb-<width>.jpg|webp 4:3 crop, for the grid
    galerij/opt/hero-*.jpg|webp               home page hero (16:9 + 4:5)
    galerij/opt/banner-*.jpg|webp             thin panorama above the footer
    galerij/opt/manifest.json                 dimensions, colours and markup
    galerij/opt/gallery-fragment.html         ready-to-paste gallery markup
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "galerij" / "fotos"
OUT = ROOT / "galerij" / "opt"

# slug, source file, alt text, caption, album
PHOTOS = [
    ("huis3", "huis3.png", "Het chalet tussen de lariksen in de zomer", "Het huis in de zomer", "zomer"),
    ("huis2", "huis2.png", "Vooraanzicht van het chalet met de parkeerplaats", "Vooraanzicht", "zomer"),
    ("huis4", "huis4.png", "Zijaanzicht van het chalet met trap en blauwe luiken", "Zijaanzicht", "zomer"),
    ("tuin1", "tuin1.png", "Groene tuin met lariksen naast het chalet", "De tuin", "zomer"),
    ("tuin2", "tuin2.png", "De tuin met een grote steen en uitzicht op de bergen", "Tuin en uitzicht", "zomer"),
    ("koningsrots", "koningsrots.png", "Een grote steen in het gras bij het chalet", "De koningsrots", "zomer"),
    ("houthakken", "houthakken.png", "Gestapeld brandhout onder de overkapping", "Brandhout", "zomer"),
    ("balkon", "balkon.png", "Balkon met stoelen en uitzicht over de vallei", "Het balkon", "zomer"),
    ("huisinsneeuw", "huisinsneeuw.jpg", "Het chalet en de lariksen bedekt met sneeuw", "Winter", "winter"),
    ("uitzicht3", "uitzicht3.jpg", "Zonsondergang boven de bergen bij Bellwald", "Uitzicht bij zonsondergang", "winter"),
    ("huisinsneeuw2", "huisinsneeuw2.jpg", "Het chalet in de sneeuw met berijpte bomen", "Sneeuw op de lariksen", "winter"),
    ("huisinsneeuw3", "huisinsneeuw3.jpg", "Het chalet aan de besneeuwde weg", "Het huis in de winter", "winter"),
    ("uitzichtwinter", "uitzichtwinter.JPG", "Avondlicht boven de bergen in de winter", "Winteravond", "winter"),
    ("eetkamer", "eetkamer.png", "Eetkamer met houten tafel en grote ramen", "De eetkamer", "binnen"),
    ("slaapkamerboven1", "slaapkamerboven1.png", "Slaapkamer met twee eenpersoonsbedden", "Slaapkamer", "binnen"),
    ("slaapkamerboven2", "slaapkamerboven2.png", "Slaapkamer met een tweepersoonsbed", "Slaapkamer", "binnen"),
    ("kamerzonenmaan1", "kamerzonenmaan1.png", "Slaapkamer met stapelbed en uitzicht op de sneeuw", "Kamer zon en maan", "binnen"),
    ("kamerzonenmaan2", "kamerzonenmaan2.png", "Slaapkamer met twee bedden en houten wanden", "Kamer zon en maan", "binnen"),
    ("stapelbed", "stapelbed.png", "Stapelbed in een houten slaapkamer", "Het stapelbed", "binnen"),
    ("P8312533", "P8312533.JPG", "Keuken met inductiekookplaat, oven en vaatwasser", "De keuken", "binnen"),
    ("woonkamer2", "woonkamer2.png", "Woonkamer met banken, open haard en houten vloer", "De woonkamer", "binnen"),
    ("woonkamer3", "woonkamer3.png", "Woonkamer met open haard en uitzicht", "Woonkamer met open haard", "binnen"),
]

ALBUMS = [
    ("zomer", "Zomer"),
    ("winter", "Winter"),
    ("binnen", "Binnen"),
]

THUMB_WIDTHS = (400, 800)
FULL_WIDTHS = (800, 1200, 1800)
JPEG_ARGS = ["-interlace", "Plane", "-sampling-factor", "4:2:0", "-quality", "80"]
WEBP_ARGS = ["-quality", "78"]


def run(args: list[str], binary: bool = False):
    return subprocess.run(args, check=True, capture_output=True, text=not binary).stdout


def size(path: Path) -> tuple[int, int]:
    w, h = run(["magick", "identify", "-format", "%w %h", str(path)]).split()
    return int(w), int(h)


def colour(path: Path) -> str:
    raw = run(["magick", str(path), "-auto-orient", "-resize", "1x1!", "-format", "%[pixel:p{0,0}]", "info:"])
    numbers = raw[raw.find("(") + 1 : raw.find(")")].split(",")
    r, g, b = (int(float(n.strip().rstrip("%"))) for n in numbers[:3])
    return f"#{r:02x}{g:02x}{b:02x}"


def lqip(path: Path, width: int, height: int) -> str:
    data = run(
        [
            "magick",
            str(path),
            "-auto-orient",
            "-strip",
            "-resize",
            f"{width}x{height}^",
            "-gravity",
            "center",
            "-extent",
            f"{width}x{height}",
            "-quality",
            "35",
            "jpg:-",
        ],
        binary=True,
    )
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()


def convert(src: Path, out: Path, width: int, kind: str, force: bool) -> None:
    if out.exists() and not force:
        return
    args = ["magick", str(src), "-auto-orient", "-strip", "-colorspace", "sRGB"]
    if kind == "thumb":
        # A centred 4:3 crop keeps the grid calm while the lightbox shows the
        # complete photo.
        height = round(width * 3 / 4)
        args += ["-resize", f"{width}x{height}^", "-gravity", "center", "-extent", f"{width}x{height}"]
    else:
        args += ["-resize", f"{width}x>"]
    if out.suffix == ".jpg":
        args += JPEG_ARGS
    else:
        args += WEBP_ARGS
    args.append(str(out))
    run(args)


def build_photo(slug: str, filename: str, alt: str, caption: str, album: str, force: bool) -> dict:
    src = SRC / filename
    src_w, src_h = size(src)
    entry = {
        "slug": slug,
        "source": str(src.relative_to(ROOT)),
        "width": src_w,
        "height": src_h,
        "alt": alt,
        "caption": caption,
        "album": album,
        "colour": colour(src),
        "thumbs": [],
        "full": [],
    }

    thumb_widths = sorted(set([w for w in THUMB_WIDTHS if w <= src_w] + ([src_w] if src_w < THUMB_WIDTHS[-1] else [])))
    for width in thumb_widths:
        height = round(width * 3 / 4)
        item = {"width": width, "height": height}
        for ext in ("jpg", "webp"):
            path = OUT / f"{slug}-thumb-{width}.{ext}"
            convert(src, path, width, "thumb", force)
            item[ext] = str(path.relative_to(ROOT))
        entry["thumbs"].append(item)

    full_widths = [w for w in FULL_WIDTHS if w <= src_w] or [src_w]
    for width in full_widths:
        height = round(src_h * width / src_w)
        item = {"width": width, "height": height}
        for ext in ("jpg", "webp"):
            path = OUT / f"{slug}-{width}.{ext}"
            convert(src, path, width, "full", force)
            item[ext] = str(path.relative_to(ROOT))
        entry["full"].append(item)

    print(f"  {slug:20} {src_w}x{src_h} -> {len(entry['thumbs'])} thumbs, {len(entry['full'])} full")
    return entry


def build_hero(force: bool) -> dict:
    src = SRC / "P8302464.JPG"
    hero = {"lqip": "", "desktop": [], "mobile": []}
    for label, widths, ratio in (
        ("desktop", (800, 1400, 2200), 16 / 9),
        ("mobile", (600, 900), 4 / 5),
    ):
        for width in widths:
            height = round(width / ratio)
            item = {"width": width, "height": height}
            for ext in ("jpg", "webp"):
                path = OUT / f"hero-{label}-{width}.{ext}"
                if force or not path.exists():
                    args = [
                        "magick",
                        str(src),
                        "-auto-orient",
                        "-strip",
                        "-colorspace",
                        "sRGB",
                        "-resize",
                        f"{width}x{height}^",
                        "-gravity",
                        "center",
                        "-extent",
                        f"{width}x{height}",
                    ]
                    args += JPEG_ARGS if ext == "jpg" else WEBP_ARGS
                    args.append(str(path))
                    run(args)
                item[ext] = str(path.relative_to(ROOT))
            hero[label].append(item)
    hero["lqip"] = lqip(src, 32, 18)
    print(f"  hero                 {len(hero['desktop'])} desktop, {len(hero['mobile'])} mobile")
    return hero


def build_banner(force: bool) -> dict:
    src = ROOT / "galerij" / "headerImg.jpg"
    src_w, src_h = size(src)
    banner = {"width": src_w, "height": src_h, "variants": []}
    for width in (1200, 2400):
        height = round(src_h * width / src_w)
        item = {"width": width, "height": height}
        for ext in ("jpg", "webp"):
            path = OUT / f"banner-{width}.{ext}"
            if force or not path.exists():
                args = [
                    "magick",
                    str(src),
                    "-auto-orient",
                    "-strip",
                    "-colorspace",
                    "sRGB",
                    "-resize",
                    f"{width}x>",
                ]
                args += JPEG_ARGS if ext == "jpg" else WEBP_ARGS
                args.append(str(path))
                run(args)
            item[ext] = str(path.relative_to(ROOT))
        banner["variants"].append(item)
    print(f"  banner               {src_w}x{src_h}")
    return banner


def build_og(force: bool) -> dict:
    src = OUT / "hero-desktop-1400.jpg"
    path = OUT / "og-image.jpg"
    if force or not path.exists():
        run(
            [
                "magick",
                str(src),
                "-strip",
                "-colorspace",
                "sRGB",
                "-resize",
                "1200x630^",
                "-gravity",
                "center",
                "-extent",
                "1200x630",
                "-interlace",
                "Plane",
                "-sampling-factor",
                "4:2:0",
                "-quality",
                "82",
                str(path),
            ]
        )
    print("  og image             1200x630")
    return {"width": 1200, "height": 630, "jpg": str(path.relative_to(ROOT))}


def srcset(items: list[dict], ext: str) -> str:
    return ", ".join(f"{item[ext]} {item['width']}w" for item in items)


def gallery_fragment(photos: list[dict]) -> str:
    sizes = "(min-width: 1100px) 220px, (min-width: 700px) 30vw, 45vw"
    chunks = []
    for album, title in ALBUMS:
        items = [p for p in photos if p["album"] == album]
        figures = []
        for photo in items:
            thumbs = photo["thumbs"]
            full = photo["full"]
            largest = max(full, key=lambda item: item["width"])
            figures.append(
                f"""      <figure class="shot" style="--ph:{photo['colour']}">
        <a href="{largest['jpg']}"
           data-src="{largest['jpg']}"
           data-srcset="{srcset(full, 'jpg')}"
           data-webp-srcset="{srcset(full, 'webp')}"
           data-caption="{html.escape(photo['caption'], quote=True)}"
           data-alt="{html.escape(photo['alt'], quote=True)}"
           data-width="{largest['width']}" data-height="{largest['height']}"
           aria-label="Vergroot: {html.escape(photo['alt'], quote=True)}">
          <picture>
            <source type="image/webp" srcset="{srcset(thumbs, 'webp')}" sizes="{sizes}">
            <img src="{thumbs[0]['jpg']}"
                 srcset="{srcset(thumbs, 'jpg')}"
                 sizes="{sizes}"
                 width="{thumbs[0]['width']}" height="{thumbs[0]['height']}"
                 alt="{html.escape(photo['alt'], quote=True)}"
                 loading="lazy" decoding="async">
          </picture>
        </a>
      </figure>"""
            )
        chunks.append(
            f"""  <section id="{album}" class="album-section wrap">
    <h2>{title}</h2>
    <div class="gallery">
{chr(10).join(figures)}
    </div>
  </section>"""
        )
    return "\n\n".join(chunks) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="rebuild existing files")
    args = parser.parse_args()

    if not shutil.which("magick"):
        raise SystemExit("ImageMagick 7 is required (the `magick` command was not found).")

    OUT.mkdir(parents=True, exist_ok=True)
    print("Building responsive photos...")
    photos = [build_photo(*photo, args.force) for photo in PHOTOS]
    print("Building hero and banner...")
    hero = build_hero(args.force)
    banner = build_banner(args.force)
    og = build_og(args.force)

    manifest = {"photos": photos, "hero": hero, "banner": banner, "og": og}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (OUT / "gallery-fragment.html").write_text(gallery_fragment(photos))
    print(f"Done. Manifest and gallery fragment written to {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
