"""Bake the locked test register and the test window's small impact mark."""

from pathlib import Path
from math import sin, pi
from PIL import Image, ImageDraw, ImageFont


TEXTURES = Path(__file__).resolve().parent / "Textures"
REGISTER_WIDTH, REGISTER_HEIGHT = 1024, 256


def counter():
    # The digits are painted on six individually recessed number wheels.
    image = Image.new("RGB", (REGISTER_WIDTH, REGISTER_HEIGHT), (18, 22, 22))
    draw = ImageDraw.Draw(image)
    digit_font = ImageFont.truetype("bahnschrift.ttf", 196)
    margin, step = 37, 159
    for wheel, number in enumerate("172408"):
        left = margin + wheel * step
        right = left + step - 7
        draw.rounded_rectangle((left, 13, right, 243), radius=10, fill=(55, 59, 58))
        draw.rounded_rectangle((left + 2, 15, right - 2, 241), radius=9, fill=(13, 16, 15))
        for y in range(22, 234):
            arc = sin(pi * (y - 22) / 211)
            shade = round(19 + 26 * arc)
            draw.line((left + 7, y, right - 7, y), fill=(shade, shade + 2, shade))
        cx = (left + right) / 2
        text_box = draw.textbbox((0, 0), number, font=digit_font)
        x = cx - (text_box[0] + text_box[2]) / 2
        y = 127 - (text_box[1] + text_box[3]) / 2
        draw.text((x + 1, y + 2), number, font=digit_font, fill=(13, 17, 16))
        draw.text((x, y), number, font=digit_font, fill=(223, 223, 202))
    image.save(TEXTURES / "T_TC_StorageCounter.png", optimize=True)


def fracture():
    # Coordinates refer to the transparent front aperture, UV0 from its top left.
    size = (512, 1024)
    scale = 4
    image = Image.new("L", (size[0] * scale, size[1] * scale))
    draw = ImageDraw.Draw(image)
    lines = [
        ([(.979, .018), (.947, .048), (.911, .068), (.874, .109), (.831, .132),
          (.788, .170)], 1.8, 245),
        ([(.947, .048), (.928, .051), (.909, .041), (.889, .043)], 1.1, 204),
        ([(.911, .068), (.910, .095), (.893, .109)], 1.0, 197),
        ([(.979, .018), (.965, .015), (.941, .022)], 1.0, 216),
    ]
    for points, width, value in lines:
        coords = [(round(x * size[0] * scale), round(y * size[1] * scale)) for x, y in points]
        draw.line(coords, fill=value, width=round(width * scale), joint="curve")
    image.resize(size, Image.Resampling.LANCZOS).save(
        TEXTURES / "T_TC_StorageWindowFracture.png", optimize=True)


if __name__ == "__main__":
    TEXTURES.mkdir(exist_ok=True)
    counter()
    fracture()
