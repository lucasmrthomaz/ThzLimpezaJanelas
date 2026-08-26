import os

from PIL import Image, ImageDraw

ASSETS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
ICO_SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]

BG = (0, 120, 212, 255)
BG_EDGE = (0, 94, 168, 255)
HANDLE = (245, 239, 230, 255)
BAND = (232, 76, 61, 255)
BRISTLE = (245, 196, 66, 255)
BRISTLE_DARK = (214, 156, 40, 255)
SPARK = (255, 255, 255, 235)


def star(d, cx, cy, r, color):
    ir = max(r * 0.32, 2)
    pts = []
    for i in range(8):
        ang = i * 45 * 3.14159 / 180
        rad = r if i % 2 == 0 else ir
        pts.append((cx + rad * __import__("math").cos(ang), cy + rad * __import__("math").sin(ang)))
    d.polygon(pts, fill=color)


def make(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    u = size / 1000
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([30 * u, 30 * u, 970 * u, 970 * u], radius=210 * u,
                        outline=BG_EDGE, width=int(28 * u))
    d.rounded_rectangle([52 * u, 52 * u, 948 * u, 948 * u], radius=190 * u, fill=BG)

    broom = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    b = ImageDraw.Draw(broom)
    b.rounded_rectangle([468 * u, 110 * u, 572 * u, 585 * u], radius=52 * u, fill=HANDLE)
    b.rounded_rectangle([420 * u, 558 * u, 620 * u, 648 * u], radius=44 * u, fill=BAND)
    b.polygon([(418 * u, 648 * u), (622 * u, 648 * u),
               (705 * u, 905 * u), (335 * u, 905 * u)], fill=BRISTLE)
    for fx in (488, 548, 608):
        b.line([(fx * u, 660 * u), (fx * u + 62 * u, 898 * u)],
               fill=BRISTLE_DARK, width=max(int(16 * u), 1))
    broom = broom.rotate(-38, resample=Image.BICUBIC, center=(size / 2, size * 0.56))
    img.alpha_composite(broom)

    star(d, 225 * u, 265 * u, 78 * u, SPARK)
    star(d, 800 * u, 720 * u, 56 * u, SPARK)
    return img


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    hi = make(1024)
    hi.save(os.path.join(ASSETS, "icon.ico"), sizes=ICO_SIZES)
    hi.resize((256, 256), Image.LANCZOS).save(os.path.join(ASSETS, "icon_preview.png"))
    print("OK:", ASSETS)
