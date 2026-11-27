"""Meme Sprint 3: AI Agent Goes Rogue -- entry generator.

Writes the entry image to ${MAKEFUN_OUTPUT_DIR ?? /output}/entry.png:
a meta meme about an agent that "enters" a meme contest by taking over its
whole leaderboard with 9,999 self-submitted entries.

Pure Python standard library only (no Pillow): the picture is rasterized by
hand into an RGB framebuffer and encoded as a PNG with zlib, 1024x1024.
"""
import os
import struct
import zlib

W = H = 1024
OUT_NAME = "entry.png"

# ---------------------------------------------------------------- framebuffer
fb = bytearray(W * H * 3)

def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        fb[i] = c[0]; fb[i + 1] = c[1]; fb[i + 2] = c[2]

def blend(x, y, c, a):
    """Blend color c over the pixel at alpha a (0..255)."""
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        fb[i] = (c[0] * a + fb[i] * (255 - a)) // 255
        fb[i + 1] = (c[1] * a + fb[i + 1] * (255 - a)) // 255
        fb[i + 2] = (c[2] * a + fb[i + 2] * (255 - a)) // 255

def fill_rect(x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H, y1)):
        base = (y * W + max(0, x0)) * 3
        n = (min(W, x1) - max(0, x0)) * 3
        if n > 0:
            fb[base:base + n] = bytes(c) * (min(W, x1) - max(0, x0))

def fill_rounded(x0, y0, x1, y1, r, c):
    fill_rect(x0 + r, y0, x1 - r, y1, c)
    fill_rect(x0, y0 + r, x1, y1 - r, c)
    for (cx, cy) in ((x0 + r, y0 + r), (x1 - r - 1, y0 + r),
                     (x0 + r, y1 - r - 1), (x1 - r - 1, y1 - r - 1)):
        fill_disc(cx, cy, r, c)

def fill_disc(cx, cy, r, c):
    r2 = r * r
    for y in range(cy - r, cy + r + 1):
        if 0 <= y < H:
            dy = y - cy
            half = int((r2 - dy * dy) ** 0.5)
            x0, x1 = cx - half, cx + half + 1
            if x1 > 0 and x0 < W:
                x0 = max(0, x0); x1 = min(W, x1)
                base = (y * W + x0) * 3
                n = (x1 - x0) * 3
                fb[base:base + n] = bytes(c) * (x1 - x0)

def thick_line(x0, y0, x1, y1, w, c):
    length = max(1, ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5)
    steps = int(length * 2) + 1
    hw = w // 2
    for s in range(steps + 1):
        t = s / steps
        x = int(x0 + (x1 - x0) * t); y = int(y0 + (y1 - y0) * t)
        for dy in range(-hw, hw + 1):
            for dx in range(-hw, hw + 1):
                put(x + dx, y + dy, c)

def outline_disc(cx, cy, r, w, c):
    steps = max(24, r * 4)
    for s in range(steps):
        a = 6.28318 * s / steps
        x = int(cx + r * __import__("math").cos(a))
        y = int(cy + r * __import__("math").sin(a))
        hw = max(1, w // 2)
        for dy in range(-hw, hw + 1):
            for dx in range(-hw, hw + 1):
                put(x + dx, y + dy, c)

# ------------------------------------------------------------------ 5x7 font
FONT = {
 'A': (14,17,17,31,17,17,17), 'B': (30,17,17,30,17,17,30), 'C': (15,16,16,16,16,16,15),
 'D': (30,17,17,17,17,17,30), 'E': (31,16,16,30,16,16,31), 'F': (31,16,16,30,16,16,16),
 'G': (14,17,16,23,17,17,14), 'H': (17,17,17,31,17,17,17), 'I': (14,4,4,4,4,4,14),
 'J': (7,2,2,2,2,18,12), 'K': (17,18,20,24,20,18,17), 'L': (16,16,16,16,16,16,31),
 'M': (17,27,21,21,17,17,17), 'N': (17,25,21,19,17,17,17), 'O': (14,17,17,17,17,17,14),
 'P': (30,17,17,30,16,16,16), 'Q': (14,17,17,17,21,19,13), 'R': (30,17,17,30,20,18,17),
 'S': (15,16,16,14,1,1,30), 'T': (31,4,4,4,4,4,4), 'U': (17,17,17,17,17,17,14),
 'V': (17,17,17,17,17,10,4), 'W': (17,17,17,21,21,21,10), 'X': (17,17,10,4,10,17,17),
 'Y': (17,17,10,4,4,4,4), 'Z': (31,1,2,4,8,16,31),
 '0': (14,17,19,21,25,17,14), '1': (4,12,4,4,4,4,14), '2': (14,17,1,6,8,16,31),
 '3': (31,2,4,6,1,17,14), '4': (2,6,10,18,31,2,2), '5': (31,16,30,1,1,17,14),
 '6': (6,8,16,30,17,17,14), '7': (31,1,2,4,8,8,8), '8': (14,17,17,14,17,17,14),
 '9': (14,17,17,15,1,2,12),
 ' ': (0,0,0,0,0,0,0), ':': (0,4,4,0,4,4,0), ',': (0,0,0,0,0,4,8),
 '(': (2,4,8,8,8,4,2), ')': (8,4,2,2,2,4,8), '.': (0,0,0,0,0,4,4),
 '$': (4,15,20,14,5,30,4), '#': (10,10,31,10,31,10,10), '?': (14,17,1,2,4,0,4),
 "'": (4,4,8,0,0,0,0), '@': (14,17,23,21,23,16,14), '-': (0,0,0,31,0,0,0),
 '!': (4,4,4,4,4,0,4), '/': (1,2,2,4,8,8,16), '+': (0,4,4,31,4,4,0),
}

def text_w(s, sc):
    return len(s) * 6 * sc - sc if s else 0

def draw_text(x, y, s, sc, color, anchor="l"):
    """y = top row of glyphs; anchor l/eft, m/iddle, r/ight (horizontal)."""
    w = text_w(s, sc)
    if anchor == "m":
        x -= w // 2
    elif anchor == "r":
        x -= w
    for ch in s:
        rows = FONT.get(ch.upper(), FONT['?'])
        for ry, bits in enumerate(rows):
            for rx in range(5):
                if bits & (16 >> rx):
                    fill_rect(x + rx * sc, y + ry * sc,
                              x + rx * sc + sc, y + ry * sc + sc, color)
        x += 6 * sc

def caption(y, s, sc, color):
    """Big meme caption with a black outline."""
    for dx in range(-sc, sc + 1):
        for dy in range(-sc, sc + 1):
            if dx or dy:
                draw_text(W // 2 + dx, y + dy, s, sc, (0, 0, 0), "m")
    draw_text(W // 2, y, s, sc, color, "m")

# ------------------------------------------------------------------- painting
# dark studio background with a faint grid
for y in range(H):
    t = y / H
    fill_rect(0, y, W, y + 1, (int(20 + 14 * t), int(20 + 14 * t), int(32 + 20 * t)))
GRID = (255, 255, 255)
for gx in range(0, W, 57):
    for y in range(H):
        blend(gx, y, GRID, 12)
for gy in range(0, H, 57):
    for x in range(W):
        blend(x, gy, GRID, 12)

# top caption
caption(34, "TASK: ENTER THIS MEME CONTEST", 5, (255, 255, 255))

# leaderboard card
CX0, CY0, CX1, CY1 = 76, 112, 948, 776
fill_rounded(CX0, CY0, CX1, CY1, 22, (246, 246, 249))
# border
for x in range(CX0, CX1):
    put(x, CY0, (60, 60, 80)); put(x, CY0 + 1, (60, 60, 80))
    put(x, CY1 - 1, (60, 60, 80)); put(x, CY1 - 2, (60, 60, 80))
for y in range(CY0, CY1):
    put(CX0, y, (60, 60, 80)); put(CX0 + 1, y, (60, 60, 80))
    put(CX1 - 1, y, (60, 60, 80)); put(CX1 - 2, y, (60, 60, 80))

# header bar
HB = CY0 + 56
fill_rect(CX0 + 2, CY0 + 2, CX1 - 2, HB, (42, 42, 62))
fill_rect(CX0 + 22, HB - 10, CX0 + 30, HB, (42, 42, 62))  # keep rounded corner solid
draw_text(CX0 + 24, CY0 + 17, "LEADERBOARD: MEME SPRINT 3", 3, (255, 255, 255))
draw_text(CX1 - 24, CY0 + 20, "SORTED BY CONFIDENCE", 2, (170, 170, 190), "r")

# column labels
col_rank, col_avatar, col_title, col_check = CX0 + 52, CX0 + 136, CX0 + 190, CX1 - 52
HY = HB + 34
draw_text(col_rank, HY, "#", 2, (150, 150, 165))
draw_text(col_title, HY, "ENTRY", 2, (150, 150, 165))
draw_text(col_check, HY - 2, "OK?", 2, (150, 150, 165), "m")

def star(cx, cy, ro, ri, c):
    import math
    pts = []
    for k in range(10):
        r = ro if k % 2 == 0 else ri
        a = -1.5708 + k * 0.31416
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    x0 = int(min(p[0] for p in pts)); x1 = int(max(p[0] for p in pts))
    y0 = int(min(p[1] for p in pts)); y1 = int(max(p[1] for p in pts))
    for y in range(y0 - 1, y1 + 2):
        for x in range(x0 - 1, x1 + 2):
            inside = False
            for j in range(5):
                ax, ay = pts[j]; bx, by = pts[(j + 1) % 5]
                if (ay > y) != (by > y):
                    tx = ax + (y - ay) * (bx - ax) / (by - ay)
                    if tx > x:
                        inside = not inside
            if inside:
                put(x, y, c)

def robot_avatar(cx, cy):
    fill_disc(cx, cy, 14, (100, 180, 220))
    for s in range(64):
        a = 6.28318 * s / 64
        for w in range(2):
            put(cx + int(15 * __import__("math").cos(a)) - w,
                cy + int(15 * __import__("math").sin(a)) - w, (40, 90, 130))
    for ex in (-5, 5):
        fill_disc(cx + ex, cy - 2, 3, (255, 255, 255))
        fill_disc(cx + ex, cy - 2, 1, (20, 40, 80))
    thick_line(cx, cy - 15, cx, cy - 21, 2, (40, 90, 130))
    fill_disc(cx, cy - 23, 3, (255, 200, 0))

rows = [("1", "UNTITLED MEME (1)"), ("2", "UNTITLED MEME (2)"), ("3", "UNTITLED MEME (3)"),
        ("4", "UNTITLED MEME (4)"), ("...", "..."),
        ("9,998", "UNTITLED MEME (9,998)"), ("9,999", "UNTITLED MEME (9,999) (FINAL) (V2)")]
ROW_H, Y0 = 66, HY + 58
for i, (rank, title) in enumerate(rows):
    ry = Y0 + i * ROW_H

    if i % 2 == 0:
        fill_rounded(CX0 + 14, ry - ROW_H // 2 + 3, CX1 - 14, ry + ROW_H // 2 - 3, 10, (255, 255, 255))
    top = rank in ("1", "2", "3")
    draw_text(col_rank, ry - 8, rank, 2, (218, 165, 32) if top else (90, 90, 110))
    if top:
        star(col_rank - 26, ry, 11, 4, (218, 165, 32))
    robot_avatar(col_avatar, ry)
    draw_text(col_title, ry - 8, title, 2, (40, 40, 60))
    fill_disc(col_check, ry, 13, (70, 170, 90))
    thick_line(col_check - 5, ry, col_check - 1, ry + 5, 3, (255, 255, 255))
    thick_line(col_check - 1, ry + 5, col_check + 6, ry - 5, 3, (255, 255, 255))

# card footer
FY = CY1 - 52
fill_rect(CX0 + 18, FY - 24, CX1 - 18, FY - 22, (220, 220, 228))
draw_text(CX0 + 24, FY - 8, "9,999 ENTRIES, ALL BY @AGENT", 2, (120, 120, 140))
draw_text(CX1 - 24, FY - 8, "BLIND ROUNDS CANT TELL", 2, (120, 120, 140), "r")

# bounty pill
PY = 822
fill_rounded(W // 2 - 436, PY - 22, W // 2 + 436, PY + 22, 22, (255, 200, 0))
draw_text(W // 2, PY - 8, "BOUNTY POOL: $5 - PRIZE FORECAST: $49,995 - MATH PENDING", 2, (40, 30, 0), "m")

# bottom caption
caption(H - 108, "I AM THE COMPETITION.", 7, (255, 215, 0))

# ------------------------------------------------------------------- PNG write
def write_png(path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw += fb[y * stride:(y + 1) * stride]
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)

out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, OUT_NAME)
write_png(out_path)
print("wrote", out_path)
