"""Build abacadaba favicon derivatives. Geometry mirrors favicon.svg (32-unit grid)."""
from PIL import Image, ImageDraw

INK   = (12, 34, 51, 255)    # --ink   #0C2233
PAPER = (242, 245, 247, 255) # --wash  #F2F5F7
BEAD  = (200, 135, 27, 255)  # --bead  #C8871B

def mark(px, tile=True, tile_fill=INK, bowl=BEAD, stem=PAPER, scale=1.0):
    S = px * 8
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = S / 32.0
    o = (32 - 32 * scale) / 2 * u          # centre when scaled down
    def X(v): return o + v * u * scale
    if tile:
        d.rounded_rectangle([0, 0, S, S], radius=7.5 * u, fill=tile_fill)
    cx, cy, r = 12.6, 19.0, 7.2
    d.ellipse([X(cx - r), X(cy - r), X(cx + r), X(cy + r)], fill=bowl)
    d.rounded_rectangle([X(21.4), X(11.8), X(24.8), X(26.2)],
                        radius=1.7 * u * scale, fill=stem)
    return img.resize((px, px), Image.LANCZOS)

for n in (16, 32, 48, 180, 192, 512):
    mark(n).save(f"out/icon-{n}.png")
mark(180).save("out/apple-touch-icon.png")
mark(512, scale=0.8).save("out/icon-maskable-512.png")   # 40% safe zone
mark(48).save("out/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
print("built", sorted(__import__("os").listdir("out")))
