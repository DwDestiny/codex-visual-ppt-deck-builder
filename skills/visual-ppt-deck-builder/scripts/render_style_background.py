#!/usr/bin/env python3

import argparse
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


canvas_width = 1920
canvas_height = 1080
slide_width = 13.333
slide_height = 7.5


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--style-slug", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--blueprint-json", required=True)
    return parser.parse_args()


def to_pixels(zone):
    return {
        "x0": int(zone["x"] / slide_width * canvas_width),
        "y0": int(zone["y"] / slide_height * canvas_height),
        "x1": int((zone["x"] + zone["w"]) / slide_width * canvas_width),
        "y1": int((zone["y"] + zone["h"]) / slide_height * canvas_height),
    }


def rgba(hex_color, alpha=255):
    raw = hex_color.replace("#", "")
    return tuple(int(raw[index:index + 2], 16) for index in (0, 2, 4)) + (alpha,)


def new_layer():
    return Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))


def apply_vertical_gradient(base, top_hex, bottom_hex):
    top = rgba(top_hex)
    bottom = rgba(bottom_hex)
    pixels = []
    for y_index in range(canvas_height):
        ratio = y_index / max(1, canvas_height - 1)
        pixels.extend(
            [
                (
                    int(top[0] + (bottom[0] - top[0]) * ratio),
                    int(top[1] + (bottom[1] - top[1]) * ratio),
                    int(top[2] + (bottom[2] - top[2]) * ratio),
                    255,
                )
            ]
            * canvas_width
        )
    gradient = Image.new("RGBA", (canvas_width, canvas_height))
    gradient.putdata(pixels)
    return Image.alpha_composite(base, gradient)


def add_grain(base, amount=12, seed=7):
    rng = random.Random(seed)
    noise = Image.new("L", (canvas_width, canvas_height))
    noise.putdata([rng.randint(120 - amount, 136 + amount) for _ in range(canvas_width * canvas_height)])
    rgb_noise = Image.merge("RGBA", (noise, noise, noise, Image.new("L", (canvas_width, canvas_height), 24)))
    return Image.alpha_composite(base, rgb_noise)


def draw_soft_blob(layer, bbox, color_hex, alpha=120, blur=38):
    blob = new_layer()
    draw = ImageDraw.Draw(blob)
    draw.ellipse(bbox, fill=rgba(color_hex, alpha))
    blob = blob.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(blob)


def draw_soft_rect(layer, bbox, color_hex, alpha=80, blur=24):
    rect = new_layer()
    draw = ImageDraw.Draw(rect)
    draw.rounded_rectangle(bbox, radius=32, fill=rgba(color_hex, alpha))
    rect = rect.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(rect)


def draw_line_cluster(layer, points, color_hex, alpha=90, width=3, blur=0):
    scratch = new_layer()
    draw = ImageDraw.Draw(scratch)
    draw.line(points, fill=rgba(color_hex, alpha), width=width)
    if blur:
      scratch = scratch.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(scratch)


def soften_safe_zone(base, zone, fill_hex, alpha=82, blur=26):
    expand_x = max(120, blur * 5)
    expand_y = max(90, blur * 4)
    radius = max(120, blur * 3)
    mask = Image.new("L", (canvas_width, canvas_height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        (zone["x0"] - expand_x, zone["y0"] - expand_y, zone["x1"] + expand_x, zone["y1"] + expand_y),
        radius=radius,
        fill=alpha,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(max(54, blur * 2)))
    overlay = Image.new("RGBA", (canvas_width, canvas_height), rgba(fill_hex, 0))
    overlay.putalpha(mask)
    return Image.alpha_composite(base, overlay)


def minimal_premium(base, zones):
    base = apply_vertical_gradient(base, "FFFFFF", "F3F3F3")
    layer = new_layer()
    for offset in range(0, 9):
        x_start = 1220 + offset * 80
        draw_line_cluster(layer, [(x_start, 160), (x_start - 260, 1040)], "C9CED4", alpha=86, width=2)
    draw_line_cluster(layer, [(1120, 0), (1920, 0)], "EFF2F4", alpha=220, width=220, blur=28)
    draw_line_cluster(layer, [(1240, 60), (1880, 60)], "BFC6CD", alpha=72, width=2)
    draw_soft_blob(layer, (1320, 630, 1870, 1080), "E6EBEF", alpha=150, blur=70)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "FFFFFF", alpha=112, blur=32)
    base = soften_safe_zone(base, zones["chart_zone"], "F8FAFB", alpha=64, blur=24)
    return add_grain(base, amount=5, seed=11)


def playful_anime(base, zones):
    base = apply_vertical_gradient(base, "FFF6E6", "FFF0D6")
    layer = new_layer()
    draw_soft_blob(layer, (-180, 760, 420, 1260), "8FD3FF", alpha=150, blur=96)
    draw_soft_blob(layer, (1420, -150, 2040, 340), "FFD76B", alpha=168, blur=92)
    draw_soft_blob(layer, (1500, 760, 2060, 1220), "FFB7CF", alpha=150, blur=98)
    draw_soft_blob(layer, (-160, -80, 300, 220), "9AD8FF", alpha=92, blur=80)
    draw_soft_blob(layer, (420, 80, 980, 420), "FFF9EF", alpha=84, blur=72)
    for dot_x, dot_y, dot_color in [(1560, 100, "FFC93C"), (1640, 180, "FF9EB5"), (1720, 120, "8FD3FF"), (1520, 760, "7BDDC8")]:
        blob = new_layer()
        draw = ImageDraw.Draw(blob)
        draw.ellipse((dot_x, dot_y, dot_x + 22, dot_y + 22), fill=rgba(dot_color, 210))
        layer.alpha_composite(blob)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "FFF9ED", alpha=184, blur=38)
    base = soften_safe_zone(base, zones["chart_zone"], "FFF6E8", alpha=168, blur=34)
    return add_grain(base, amount=2, seed=17)


def data_analytics(base, zones):
    base = apply_vertical_gradient(base, "031022", "020814")
    layer = new_layer()
    draw_soft_blob(layer, (1080, 80, 1980, 980), "0B4F86", alpha=82, blur=110)
    draw_soft_blob(layer, (980, 520, 1980, 1260), "12C7D6", alpha=42, blur=130)
    for step in range(5):
        y_bias = 820 + step * 26
        points = []
        for x_index in range(0, canvas_width + 1, 36):
            wave = math.sin((x_index / 150.0) + step * 0.8) * (18 + step * 4)
            points.append((x_index, int(y_bias + wave)))
        draw_line_cluster(layer, points, "0DA2C9", alpha=58 - step * 8, width=2)
    for radius in range(340, 760, 92):
        arc = new_layer()
        draw = ImageDraw.Draw(arc)
        draw.arc((1160 - radius, 540 - radius, 1160 + radius, 540 + radius), start=282, end=345, fill=rgba("5B5FF0", 42), width=2)
        layer.alpha_composite(arc.filter(ImageFilter.GaussianBlur(0)))
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "031022", alpha=116, blur=34)
    base = soften_safe_zone(base, zones["chart_zone"], "03162A", alpha=86, blur=28)
    return add_grain(base, amount=5, seed=23)


def oriental_heritage(base, zones):
    base = apply_vertical_gradient(base, "FAF5ED", "F2EBDD")
    layer = new_layer()
    draw_soft_blob(layer, (-120, 760, 520, 1220), "D9C6AA", alpha=84, blur=110)
    draw_soft_blob(layer, (1460, 620, 1980, 1140), "C72B2B", alpha=46, blur=130)
    draw_soft_blob(layer, (-40, 40, 360, 340), "B91C1C", alpha=34, blur=88)
    draw_line_cluster(layer, [(124, 780), (270, 640), (440, 680), (590, 520)], "171717", alpha=34, width=6, blur=6)
    draw_line_cluster(layer, [(40, 940), (240, 840), (480, 880), (640, 760)], "171717", alpha=24, width=14, blur=12)
    seal = new_layer()
    draw = ImageDraw.Draw(seal)
    draw.rectangle((1670, 140, 1738, 208), fill=rgba("B91C1C", 220))
    draw.line((1630, 120, 1755, 120), fill=rgba("B91C1C", 110), width=2)
    layer.alpha_composite(seal.filter(ImageFilter.GaussianBlur(1)))
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "FAF5ED", alpha=160, blur=34)
    base = soften_safe_zone(base, zones["chart_zone"], "F7F2E8", alpha=132, blur=30)
    return add_grain(base, amount=8, seed=29)


def future_tech(base, zones):
    base = apply_vertical_gradient(base, "03112A", "07122F")
    layer = new_layer()
    draw_soft_blob(layer, (980, 700, 1760, 1320), "00D4D8", alpha=72, blur=140)
    draw_soft_blob(layer, (1180, 620, 1920, 1240), "7C4DFF", alpha=58, blur=160)
    draw_soft_blob(layer, (1360, 160, 1880, 760), "2F80ED", alpha=28, blur=120)
    for radius, color_hex, alpha in [(260, "00D4D8", 62), (360, "2F80ED", 42), (470, "7C4DFF", 28)]:
        ring = new_layer()
        draw = ImageDraw.Draw(ring)
        draw.ellipse((1380 - radius, 860 - radius, 1380 + radius, 860 + radius), outline=rgba(color_hex, alpha), width=4)
        layer.alpha_composite(ring.filter(ImageFilter.GaussianBlur(2)))
    draw_line_cluster(layer, [(1540, 140,),(1740, 280)], "7C4DFF", alpha=86, width=2)
    draw_line_cluster(layer, [(1660, 900),(1840, 1020)], "00D4D8", alpha=72, width=2)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "061730", alpha=118, blur=34)
    base = soften_safe_zone(base, zones["chart_zone"], "04142E", alpha=96, blur=30)
    return add_grain(base, amount=5, seed=31)


def editorial_magazine(base, zones):
    base = apply_vertical_gradient(base, "FFFEFB", "F5F0E8")
    layer = new_layer()
    draw_soft_blob(layer, (1400, 20, 1980, 520), "D8C6B0", alpha=42, blur=128)
    draw_soft_blob(layer, (-60, 460, 320, 1180), "D4C8BA", alpha=24, blur=82)
    draw_line_cluster(layer, [(108, 0), (108, 1080)], "1F2937", alpha=118, width=6)
    draw_line_cluster(layer, [(1480, 150), (1820, 150)], "D72638", alpha=44, width=2)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "FFFDF9", alpha=178, blur=38)
    base = soften_safe_zone(base, zones["chart_zone"], "FFF9F2", alpha=152, blur=34)
    return add_grain(base, amount=3, seed=37)


def saas_product(base, zones):
    base = apply_vertical_gradient(base, "F8FBFF", "EEF5FB")
    layer = new_layer()
    draw_soft_blob(layer, (1320, 140, 1940, 820), "BFE8FF", alpha=60, blur=120)
    draw_soft_blob(layer, (980, 660, 1880, 1180), "B8F1D4", alpha=54, blur=130)
    for panel in [(1480, 180, 1820, 340), (1530, 380, 1880, 580), (1420, 620, 1800, 860)]:
        draw_soft_rect(layer, panel, "FFFFFF", alpha=46, blur=18)
    draw_line_cluster(layer, [(0, 0), (0, 1080)], "2563EB", alpha=220, width=14)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "FBFDFF", alpha=144, blur=30)
    base = soften_safe_zone(base, zones["chart_zone"], "F6FBFF", alpha=132, blur=28)
    return add_grain(base, amount=4, seed=41)


def investor_narrative(base, zones):
    base = apply_vertical_gradient(base, "07101D", "0A1323")
    layer = new_layer()
    draw_soft_blob(layer, (1280, 120, 1980, 920), "F6C85F", alpha=20, blur=150)
    draw_line_cluster(layer, [(1520, 100), (1800, 300)], "F6C85F", alpha=92, width=2)
    draw_line_cluster(layer, [(1610, 220), (1870, 460)], "F6C85F", alpha=56, width=2)
    draw_line_cluster(layer, [(1710, 700), (1870, 870)], "F6C85F", alpha=46, width=2)
    for y_line in [220, 440, 660, 880]:
        draw_line_cluster(layer, [(1420, y_line), (1910, y_line)], "1A2C43", alpha=36, width=1)
    base = Image.alpha_composite(base, layer)
    base = soften_safe_zone(base, zones["text_zone"], "07111F", alpha=124, blur=34)
    base = soften_safe_zone(base, zones["chart_zone"], "081522", alpha=98, blur=30)
    return add_grain(base, amount=5, seed=47)


style_renderers = {
    "minimal-premium": minimal_premium,
    "playful-anime": playful_anime,
    "data-analytics": data_analytics,
    "oriental-heritage": oriental_heritage,
    "future-tech": future_tech,
    "editorial-magazine": editorial_magazine,
    "saas-product": saas_product,
    "investor-narrative": investor_narrative,
}


def main():
    args = parse_args()
    blueprint = json.loads(args.blueprint_json)
    zones = {name: to_pixels(zone) for name, zone in blueprint["zones"].items()}
    base = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 255))
    renderer = style_renderers[args.style_slug]
    image = renderer(base, zones).convert("RGB")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=96)


if __name__ == "__main__":
    main()
