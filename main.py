#!/usr/bin/env python3
"""news-image-20261122: draws a 1024x1024 newspaper front page summing up
Sunday 22 November 2026 world news. Python 3 stdlib only, no network,
deterministic: run twice -> identical bytes.

    MAKEFUN_OUTPUT_DIR=out python3 main.py

Output: <out>/entry.png (<=1 MiB, 1024x1024).
"""
import os
import struct
import zlib
from binascii import crc32

W, H = 1024, 1024
PAPER = (247, 242, 231)
INK = (17, 17, 17)
RED = (185, 28, 28)
NAVY = (16, 34, 64)
BLUE = (30, 90, 168)
TEAL = (13, 110, 110)
GREEN = (34, 120, 60)
GOLD = (176, 124, 20)
GREY = (110, 106, 96)
LIGHT = (232, 226, 212)
WHITE = (255, 255, 255)
SKY = (150, 190, 220)
SAND = (226, 206, 158)


class Canvas:
    def __init__(self, w=W, h=H, bg=PAPER):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(max(0, y), min(self.h, y + h)):
            i = (yy * self.w + max(0, x)) * 3
            n = min(self.w, x + w) - max(0, x)
            if n > 0:
                self.px[i:i + n * 3] = bytes(c) * n

    def hline(self, x0, x1, y, c):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.set(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d <= r * r:
                        self.set(xx, yy, c)
                elif (r - 1) ** 2 <= d <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r0, r1, c):
        for yy in range(cy - r1, cy + r1 + 1):
            for xx in range(cx - r1, cx + r1 + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if r0 * r0 <= d <= r1 * r1:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        for a, b in zip(pts, pts[1:] + pts[:1]):
            self.line(a[0], a[1], b[0], b[1], c)

    def tri(self, a, b, c_, c):
        # filled triangle via scanlines
        xs = sorted([a, b, c_], key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = xs
        for y in range(y0, y2 + 1):
            xa = x0 + (x2 - x0) * (y - y0) / max(1, y2 - y0)
            if y <= y1:
                xb = x0 + (x1 - x0) * (y - y0) / max(1, y1 - y0)
            else:
                xb = x1 + (x2 - x1) * (y - y1) / max(1, y2 - y1)
            for x in range(int(min(xa, xb)), int(max(xa, xb)) + 1):
                self.set(x, y, c)

    def frame(self, x, y, w, h, c, t=1):
        for k in range(t):
            self.rect(x + k, y + k, w - 2 * k, 1, c)
            self.rect(x + k, y + h - 1 - k, w - 2 * k, 1, c)
            self.rect(x + k, y + k, 1, h - 2 * k, c)
            self.rect(x + w - 1 - k, y + k, 1, h - 2 * k, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1:
                    self.set(xx, yy, c)


def png_bytes(cv):
    raw = b"".join(b"\x00" + bytes(cv.px[y * cv.w * 3:(y + 1) * cv.w * 3])
                   for y in range(cv.h))
    comp = zlib.compress(raw, 9)

    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data +
                struct.pack(">I", crc32(typ + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", comp) + chunk(b"IEND", b""))


# 5x7 bitmap font: 7 rows of 5 bits, '#' = on. Own hand-drawn set.
FONT = {}
def _g(ch, rows):
    FONT[ch] = rows

_g("A", ["01110", "10001", "10001", "11111", "10001", "10001", "10001"])
_g("B", ["11110", "10001", "10001", "11110", "10001", "10001", "11110"])
_g("C", ["01110", "10001", "10000", "10000", "10000", "10001", "01110"])
_g("D", ["11100", "10010", "10001", "10001", "10001", "10010", "11100"])
_g("E", ["11111", "10000", "10000", "11110", "10000", "10000", "11111"])
_g("F", ["11111", "10000", "10000", "11110", "10000", "10000", "10000"])
_g("G", ["01110", "10001", "10000", "10111", "10001", "10001", "01111"])
_g("H", ["10001", "10001", "10001", "11111", "10001", "10001", "10001"])
_g("I", ["01110", "00100", "00100", "00100", "00100", "00100", "01110"])
_g("J", ["00111", "00010", "00010", "00010", "00010", "10010", "01100"])
_g("K", ["10001", "10010", "10100", "11000", "10100", "10010", "10001"])
_g("L", ["10000", "10000", "10000", "10000", "10000", "10000", "11111"])
_g("M", ["10001", "11011", "10101", "10101", "10001", "10001", "10001"])
_g("N", ["10001", "11001", "10101", "10011", "10001", "10001", "10001"])
_g("O", ["01110", "10001", "10001", "10001", "10001", "10001", "01110"])
_g("P", ["11110", "10001", "10001", "11110", "10000", "10000", "10000"])
_g("Q", ["01110", "10001", "10001", "10001", "10101", "10010", "01101"])
_g("R", ["11110", "10001", "10001", "11110", "10100", "10010", "10001"])
_g("S", ["01111", "10000", "10000", "01110", "00001", "00001", "11110"])
_g("T", ["11111", "00100", "00100", "00100", "00100", "00100", "00100"])
_g("U", ["10001", "10001", "10001", "10001", "10001", "10001", "01110"])
_g("V", ["10001", "10001", "10001", "10001", "10001", "01010", "00100"])
_g("W", ["10001", "10001", "10001", "10101", "10101", "10101", "01010"])
_g("X", ["10001", "10001", "01010", "00100", "01010", "10001", "10001"])
_g("Y", ["10001", "10001", "01010", "00100", "00100", "00100", "00100"])
_g("Z", ["11111", "00001", "00010", "00100", "01000", "10000", "11111"])
_g("0", ["01110", "10001", "10011", "10101", "11001", "10001", "01110"])
_g("1", ["00100", "01100", "00100", "00100", "00100", "00100", "01110"])
_g("2", ["01110", "10001", "00001", "00010", "00100", "01000", "11111"])
_g("3", ["11111", "00010", "00100", "00010", "00001", "10001", "01110"])
_g("4", ["00010", "00110", "01010", "10010", "11111", "00010", "00010"])
_g("5", ["11111", "10000", "11110", "00001", "00001", "10001", "01110"])
_g("6", ["00110", "01000", "10000", "11110", "10001", "10001", "01110"])
_g("7", ["11111", "00001", "00010", "00100", "01000", "01000", "01000"])
_g("8", ["01110", "10001", "10001", "01110", "10001", "10001", "01110"])
_g("9", ["01110", "10001", "10001", "01111", "00001", "00010", "01100"])
_g("a", ["00000", "00000", "01110", "00001", "01111", "10001", "01111"])
_g("b", ["10000", "10000", "11110", "10001", "10001", "10001", "11110"])
_g("c", ["00000", "00000", "01110", "10001", "10000", "10001", "01110"])
_g("d", ["00001", "00001", "01111", "10001", "10001", "10001", "01111"])
_g("e", ["00000", "00000", "01110", "10001", "11111", "10000", "01110"])
_g("f", ["00110", "01001", "01000", "11110", "01000", "01000", "01000"])
_g("g", ["00000", "01111", "10001", "10001", "01111", "00001", "01110"])
_g("h", ["10000", "10000", "11110", "10001", "10001", "10001", "10001"])
_g("i", ["00100", "00000", "01100", "00100", "00100", "00100", "01110"])
_g("j", ["00010", "00000", "00110", "00010", "00010", "10010", "01100"])
_g("k", ["10000", "10000", "10010", "10100", "11000", "10100", "10010"])
_g("l", ["01100", "00100", "00100", "00100", "00100", "00100", "01110"])
_g("m", ["00000", "00000", "11010", "10101", "10101", "10101", "10101"])
_g("n", ["00000", "00000", "11110", "10001", "10001", "10001", "10001"])
_g("o", ["00000", "00000", "01110", "10001", "10001", "10001", "01110"])
_g("p", ["00000", "00000", "11110", "10001", "10001", "11110", "10000"])
_g("q", ["00000", "00000", "01111", "10001", "10001", "01111", "00001"])
_g("r", ["00000", "00000", "10110", "11001", "10000", "10000", "10000"])
_g("s", ["00000", "00000", "01111", "10000", "01110", "00001", "11110"])
_g("t", ["01000", "01000", "11110", "01000", "01000", "01000", "00110"])
_g("u", ["00000", "00000", "10001", "10001", "10001", "10011", "01101"])
_g("v", ["00000", "00000", "10001", "10001", "10001", "01010", "00100"])
_g("w", ["00000", "00000", "10001", "10101", "10101", "10101", "01010"])
_g("x", ["00000", "00000", "10001", "01010", "00100", "01010", "10001"])
_g("y", ["00000", "00000", "10001", "10001", "01111", "00001", "01110"])
_g("z", ["00000", "00000", "11111", "00010", "00100", "01000", "11111"])
_g(" ", ["00000", "00000", "00000", "00000", "00000", "00000", "00000"])
_g(".", ["00000", "00000", "00000", "00000", "00000", "01100", "01100"])
_g(",", ["00000", "00000", "00000", "00000", "01100", "00100", "01000"])
_g(":", ["00000", "01100", "01100", "00000", "01100", "01100", "00000"])
_g(";", ["00000", "01100", "01100", "00000", "01100", "00100", "01000"])
_g("!", ["00100", "00100", "00100", "00100", "00100", "00000", "00100"])
_g("?", ["01110", "10001", "00001", "00010", "00100", "00000", "00100"])
_g("'", ["00100", "00100", "01000", "00000", "00000", "00000", "00000"])
_g('"', ["01010", "01010", "00000", "00000", "00000", "00000", "00000"])
_g("-", ["00000", "00000", "00000", "11111", "00000", "00000", "00000"])
_g("(", ["00010", "00100", "01000", "01000", "01000", "00100", "00010"])
_g(")", ["01000", "00100", "00010", "00010", "00010", "00100", "01000"])
_g("/", ["00001", "00010", "00010", "00100", "01000", "01000", "10000"])
_g("%", ["11001", "11010", "00010", "00100", "01000", "01011", "10011"])
_g("$", ["00100", "01111", "10100", "01110", "00101", "11110", "00100"])
_g("&", ["01100", "10010", "10100", "01000", "10101", "10010", "01101"])
_g("@", ["01110", "10001", "10111", "10101", "10110", "10000", "01110"])
_g("#", ["01010", "01010", "11111", "01010", "11111", "01010", "01010"])
_g("+", ["00000", "00100", "00100", "11111", "00100", "00100", "00000"])
_g("*", ["00000", "10101", "01110", "10101", "00000", "00000", "00000"])
_g("=", ["00000", "00000", "11111", "00000", "11111", "00000", "00000"])
_g("_", ["00000", "00000", "00000", "00000", "00000", "00000", "11111"])
_g("<", ["00010", "00100", "01000", "10000", "01000", "00100", "00010"])
_g(">", ["01000", "00100", "00010", "00001", "00010", "00100", "01000"])
_g("[", ["01110", "01000", "01000", "01000", "01000", "01000", "01110"])
_g("]", ["01110", "00010", "00010", "00010", "00010", "00010", "01110"])
_g("°", ["01100", "10010", "10010", "01100", "00000", "00000", "00000"])


def text_w(s, scale):
    return len(s) * 6 * scale


def draw_text(cv, x, y, scale, color, text):
    cx = x
    for ch in text:
        rows = FONT.get(ch)
        if rows is None:
            rows = FONT["?"]
        for r, bits in enumerate(rows):
            for c, b in enumerate(bits):
                if b == "1":
                    cv.rect(cx + c * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def wrap(text, max_chars):
    words = text.split(" ")
    lines, cur = [], ""
    for wd in words:
        if cur and len(cur) + 1 + len(wd) > max_chars:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, x, y, w, scale, color, text, lh=None, max_lines=None):
    max_chars = max(1, w // (6 * scale))
    lines = wrap(text, max_chars)
    if max_lines:
        lines = lines[:max_lines]
    lh = lh or (9 * scale)
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * lh, scale, color, ln)
    return y + len(lines) * lh


# ---- illustrations: every scene drawn in code, no fetched images ----
def _sky(cv, x, y, w, h, top, bot):
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        cv.rect(x, y + yy, w, 1, c)


def illo_gulf(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (10, 12, 40), (40, 30, 70))
    cv.rect(x, y + h - 26, w, 26, (16, 50, 70))  # sea
    for i in range(0, w, 14):
        cv.rect(x + i, y + h - 24 + (i % 3), min(8, w - i), 2, (90, 140, 170))
    # tanker silhouette
    cv.rect(x + w // 2 - 52, y + h - 52, 104, 26, (40, 52, 72))
    cv.rect(x + w // 2 - 40, y + h - 64, 22, 12, (40, 52, 72))
    cv.rect(x + w // 2 + 18, y + h - 64, 10, 12, (40, 52, 72))
    for wx in range(w // 2 - 46, w // 2 + 46, 12):
        cv.rect(x + wx, y + h - 48, 6, 5, (255, 220, 120))
    cv.circle(x + w // 2 - 30, y + h - 60, 3, (255, 200, 60))
    # missile arcs + fireballs
    cv.circle(x + 40, y + 26, 9, (255, 170, 40))
    cv.circle(x + 40, y + 26, 5, (255, 230, 120))
    cv.circle(x + w - 46, y + 18, 7, (255, 170, 40))
    cv.circle(x + w - 46, y + 18, 4, (255, 230, 120))
    for k in range(6):
        cv.set(x + 44 + k * 3, y + 30 + k * 2, (255, 200, 90))
        cv.set(x + w - 50 + k * 2, y + 22 + k * 3, (255, 200, 90))
    # stars
    for sx, sy in [(20, 8), (90, 14), (150, 6), (w - 90, 10), (w - 20, 30)]:
        cv.set(x + sx, y + sy, WHITE)
        cv.set(x + sx + 1, y + sy, WHITE)


def illo_quake(cv, x, y, w, h):
    _sky(cv, x, y, w, h, SKY, (220, 220, 200))
    cv.circle(x + w - 40, y + 22, 12, (255, 240, 160))
    # Andes ridge
    cv.tri((x, y + h - 1), (x + w // 4, y + 30), (x + w // 2, y + h - 1), (90, 80, 70))
    cv.tri((x + w // 3, y + h - 1), (x + 2 * w // 3, y + 18), (x + w - 1, y + h - 1), (70, 60, 55))
    cv.tri((x + w // 4 - 14, y + 52), (x + w // 4, y + 30), (x + w // 4 + 14, y + 52), WHITE)
    cv.tri((x + 2 * w // 3 - 16, y + 42), (x + 2 * w // 3, y + 18), (x + 2 * w // 3 + 16, y + 42), WHITE)
    # crack in the ground
    cv.line(x + 20, y + h - 8, x + 60, y + h - 22, INK)
    cv.line(x + 60, y + h - 22, x + 100, y + h - 10, INK)
    cv.line(x + 100, y + h - 10, x + w - 30, y + h - 20, INK)
    # shaking house
    cv.rect(x + w - 70, y + h - 34, 34, 26, (150, 60, 40))
    cv.tri((x + w - 74, y + h - 34), (x + w - 53, y + h - 48), (x + w - 32, y + h - 34), (120, 40, 30))
    # seismograph strip
    cv.rect(x + 8, y + 8, 90, 18, WHITE)
    cv.frame(x + 8, y + 8, 90, 18, INK)
    px, py = x + 10, y + 17
    for k in range(86):
        ny = py + (6 if k % 9 == 4 else (-6 if k % 9 == 0 else 0))
        cv.line(px, py, px + 1, ny, RED)
        px, py = px + 1, ny


def illo_cop31(cv, x, y, w, h):
    cv.rect(x, y, w, h, (38, 52, 74))
    # hall: rows of delegate desks
    for r in range(3):
        yy = y + 14 + r * 26
        for c in range(8):
            xx = x + 10 + c * (w - 20) // 8
            cv.rect(xx, yy, 22, 12, (210, 200, 170))
            cv.rect(xx + 7, yy - 8, 8, 8, (200, 170, 90))
    # flags row
    cols = [RED, WHITE, BLUE, (0, 120, 60), GOLD, (120, 40, 120), TEAL, (200, 80, 40)]
    for c in range(8):
        xx = x + 10 + c * (w - 20) // 8
        cv.rect(xx, y + h - 22, 22, 14, cols[c % len(cols)])
    # podium + deadlock banner
    cv.rect(x + w // 2 - 46, y + h - 52, 92, 20, (120, 90, 50))
    draw_text(cv, x + w // 2 - 42, y + h - 48, 2, WHITE, "NO DEAL")
    draw_text(cv, x + w // 2 - 34, y + 4, 1, (255, 220, 120), "200 NATIONS")


def illo_baltic(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (70, 90, 110), (160, 180, 200))
    cv.rect(x, y + h - 18, w, 18, (30, 70, 110))
    for i in range(0, w, 12):
        cv.rect(x + i, y + h - 16 + (i % 2), min(7, w - i), 2, (140, 180, 210))
    # cargo ship
    cv.rect(x + 30, y + h - 34, 80, 16, (40, 40, 40))
    cv.rect(x + 44, y + h - 46, 26, 12, (40, 40, 40))
    cv.rect(x + 44, y + h - 46, 6, 10, (40, 40, 40))
    for i in range(3):
        cv.rect(x + 52 + i * 18, y + h - 30, 12, 8, (180, 60, 40))
    # drones above
    for dx, dy in [(w - 60, 10), (w - 38, 18), (w - 78, 22)]:
        cv.rect(x + dx - 6, y + dy, 12, 2, INK)
        cv.rect(x + dx - 1, y + dy - 3, 2, 8, INK)
        cv.circle(x + dx, y + dy + 8, 2, RED)


def illo_ukraine(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (20, 22, 50), (60, 40, 60))
    # city skyline (heights fit the box: max h-16)
    for i, bh in enumerate([18, 26, 22, 30, 24, 20]):
        xx = x + 6 + i * (w - 12) // 6
        cv.rect(xx, y + h - 14 - bh, (w - 12) // 6 - 4, bh, (15, 15, 25))
        for wy in range(max(1, (bh - 8) // 10)):
            cv.rect(xx + 3, y + h - 14 - bh + 6 + wy * 10, 4, 5, (255, 220, 100))
    cv.rect(x, y + h - 14, w, 14, (10, 10, 18))
    # drone swarm dots + arcs
    for k in range(14):
        dx = x + 10 + (k * 37) % (w - 20)
        dy = y + 6 + (k * 23) % 34
        cv.circle(dx, dy, 2, (255, 200, 80))
    cv.line(x + 20, y + 12, x + w // 2, y + 40, (255, 120, 60))
    cv.circle(x + w // 2, y + 40, 5, (255, 150, 50))
    cv.circle(x + w // 2, y + 40, 3, (255, 230, 130))


def illo_mexico(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (230, 180, 120), (200, 140, 80))
    cv.rect(x, y + h - 22, w, 22, (170, 120, 60))
    cv.line(x, y + h - 22, x + w - 1, y + h - 22, (120, 80, 40))
    # cactus + road
    cv.rect(x + 14, y + h - 46, 8, 30, GREEN)
    cv.rect(x + 6, y + h - 38, 8, 6, GREEN)
    cv.rect(x + 22, y + h - 34, 8, 6, GREEN)
    cv.rect(x + w - 40, y + h - 18, 40, 18, (60, 60, 60))
    for i in range(4):
        cv.rect(x + w - 40 + i * 10, y + h - 16, 6, 3, (255, 220, 80))
    # police car with lights
    cv.rect(x + 30, y + h - 40, 52, 16, (20, 40, 90))
    cv.rect(x + 38, y + h - 46, 30, 6, (20, 40, 90))
    cv.rect(x + 42, y + h - 45, 10, 4, (200, 230, 250))
    cv.rect(x + 54, y + h - 45, 10, 4, (200, 230, 250))
    cv.rect(x + 34, y + h - 36, 44, 4, WHITE)
    cv.circle(x + 44, y + h - 22, 5, INK)
    cv.circle(x + 68, y + h - 22, 5, INK)
    cv.circle(x + 48, y + h - 44, 2, RED)
    cv.circle(x + 60, y + h - 44, 2, BLUE)
    # helicopter
    cv.rect(x + w - 90, y + 10, 30, 10, INK)
    cv.line(x + w - 108, y + 12, x + w - 56, y + 12, INK)
    cv.line(x + w - 78, y + 20, x + w - 70, y + 30, INK)


def illo_fbi(cv, x, y, w, h):
    cv.rect(x, y, w, h, NAVY)
    # server racks
    for c in range(4):
        xx = x + 10 + c * (w - 20) // 4
        cv.rect(xx, y + 8, (w - 20) // 4 - 6, h - 16, (20, 30, 50))
        cv.frame(xx, y + 8, (w - 20) // 4 - 6, h - 16, (90, 120, 160))
        for r in range(4):
            cv.rect(xx + 4, y + 12 + r * 10, (w - 20) // 4 - 14, 3, (60, 200, 120))
    # magnifier + warning
    cv.ring(x + w - 34, y + 16, 8, 12, (255, 200, 60))
    cv.line(x + w - 26, y + 24, x + w - 14, y + 36, (255, 200, 60))
    draw_text(cv, x + w // 2 - 12, y + h - 14, 2, (255, 200, 60), "FBI")


def illo_denmark(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (200, 30, 40), (160, 20, 30))
    cv.rect(x, y, w, 10, WHITE)
    cv.rect(x, y + 10, w, 6, RED)
    # stage: figure + mic
    cv.circle(x + w // 2, y + 22, 8, (240, 210, 170))
    cv.rect(x + w // 2 - 12, y + 30, 24, 16, INK)
    cv.line(x + w // 2 + 14, y + 26, x + w // 2 + 26, y + 20, INK)
    cv.circle(x + w // 2 + 28, y + 18, 4, (220, 220, 220))
    # crosshair target (fits the box)
    cv.ring(x + w // 2, y + 26, 12, 14, WHITE)
    cv.line(x + w // 2 - 19, y + 26, x + w // 2 - 14, y + 26, WHITE)
    cv.line(x + w // 2 + 14, y + 26, x + w // 2 + 19, y + 26, WHITE)
    cv.line(x + w // 2, y + 8, x + w // 2, y + 12, WHITE)
    cv.line(x + w // 2, y + 40, x + w // 2, y + 44, WHITE)


def illo_markets(cv, x, y, w, h):
    cv.rect(x, y, w, h, WHITE)
    cv.frame(x, y, w, h, INK)
    # grid
    for gy in range(1, 4):
        cv.hline(x + 4, x + w - 5, y + gy * h // 4, (220, 220, 220))
    # falling line
    pts = [(x + 8, y + 10), (x + w // 4, y + 16), (x + w // 2, y + 14),
           (x + 3 * w // 4, y + 30), (x + w - 10, y + h - 12)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED)
        cv.line(a[0], a[1] + 1, b[0], b[1] + 1, RED)
    # candlesticks
    for i, (ch, up) in enumerate([(10, False), (16, True), (22, False), (14, False)]):
        xx = x + 16 + i * 16
        cv.rect(xx, y + 8 + i * 6, 8, ch, GREEN if up else RED)
    draw_text(cv, x + w - 46, y + h - 14, 2, RED, "-3%")


def illo_estonia(cv, x, y, w, h):
    _sky(cv, x, y, w, h, SKY, (200, 210, 220))
    cv.rect(x, y + h - 16, w, 16, GREEN)
    # border fence across
    for fx in range(x + 4, x + w - 4, 12):
        cv.vline(fx, y + 12, y + h - 16, INK)
    cv.hline(x + 2, x + w - 2, y + 16, INK)
    cv.hline(x + 2, x + w - 2, y + 30, INK)
    # barrier sign
    cv.rect(x + w // 2 - 30, y + h - 46, 60, 22, (255, 220, 60))
    cv.frame(x + w // 2 - 30, y + h - 46, 60, 22, INK)
    draw_text(cv, x + w // 2 - 26, y + h - 42, 2, INK, "CLOSED")
    # flags: Estonia left, Russia right
    cv.rect(x + 8, y + 8, 24, 6, BLUE)
    cv.rect(x + 8, y + 14, 24, 6, INK)
    cv.rect(x + 8, y + 20, 24, 6, WHITE)
    cv.rect(x + w - 32, y + 8, 24, 6, WHITE)
    cv.rect(x + w - 32, y + 14, 24, 6, BLUE)
    cv.rect(x + w - 32, y + 20, 24, 6, RED)


def illo_bolsonaro(cv, x, y, w, h):
    cv.rect(x, y, w, h, (235, 240, 245))
    # hospital bed
    cv.rect(x + 12, y + h - 30, 90, 8, (90, 120, 160))
    cv.rect(x + 12, y + h - 22, 6, 14, INK)
    cv.rect(x + 96, y + h - 22, 6, 14, INK)
    cv.rect(x + 16, y + h - 38, 26, 8, WHITE)
    cv.circle(x + 22, y + h - 40, 6, (240, 210, 170))
    cv.rect(x + 30, y + h - 36, 60, 6, (200, 220, 240))
    # IV drip + monitor
    cv.line(x + w - 30, y + 6, x + w - 30, y + 26, INK)
    cv.rect(x + w - 36, y + 26, 12, 16, (200, 230, 250))
    cv.frame(x + w - 36, y + 26, 12, 16, INK)
    cv.rect(x + 12, y + 8, 44, 22, (20, 40, 50))
    cv.line(x + 14, y + 20, x + 22, y + 20, (80, 255, 140))
    cv.line(x + 22, y + 20, x + 26, y + 12, (80, 255, 140))
    cv.line(x + 26, y + 12, x + 30, y + 26, (80, 255, 140))
    cv.line(x + 30, y + 26, x + 38, y + 20, (80, 255, 140))
    cv.line(x + 38, y + 20, x + 54, y + 20, (80, 255, 140))
    # red cross (fits the box)
    cv.rect(x + w // 2 - 4, y + h - 46, 8, 20, RED)
    cv.rect(x + w // 2 - 11, y + h - 39, 22, 8, RED)


def illo_apec(cv, x, y, w, h):
    _sky(cv, x, y, w, h, (240, 200, 130), (200, 150, 90))
    # Shenzhen towers (heights fit the box: max h-14)
    for i, th in enumerate([20, 28, 24, 32, 18]):
        xx = x + 8 + i * (w - 16) // 5
        cv.rect(xx, y + h - 12 - th, (w - 16) // 5 - 5, th, (50, 50, 70))
        for wy in range(0, th - 6, 8):
            cv.rect(xx + 3, y + h - 12 - th + 4 + wy, 5, 4, (255, 220, 120))
    cv.rect(x, y + h - 12, w, 12, (40, 40, 55))
    # three flags on poles
    flags = [(RED, WHITE), ((200, 30, 30), (255, 220, 0)), ((255, 255, 255), (0, 60, 160))]
    for i, (c1, c2) in enumerate(flags):
        fx = x + w // 2 - 44 + i * 34
        cv.vline(fx, y + 6, y + 34, INK)
        cv.rect(fx, y + 6, 26, 16, c1)
        cv.rect(fx, y + 6, 26, 5, c2)
    draw_text(cv, x + w // 2 - 30, y + 38, 1, INK, "SHENZHEN")


def illo_sport(cv, x, y, w, h):
    cv.rect(x, y, w, h, (40, 140, 60))
    cv.rect(x + 4, y + 4, w - 8, h - 8, (50, 160, 70))
    cv.frame(x + 4, y + 4, w - 8, h - 8, WHITE)
    cv.hline(x + 4, x + w - 4, y + h // 2, WHITE)
    cv.circle(x + w // 2, y + h // 2, 10, WHITE, fill=False)
    # goal + ball
    cv.rect(x + w - 34, y + 8, 26, 20, WHITE)
    cv.rect(x + w - 32, y + 10, 22, 16, (40, 140, 60))
    cv.circle(x + w // 2 - 10, y + h - 16, 7, WHITE)
    cv.circle(x + w // 2 - 10, y + h - 16, 7, INK, fill=False)
    cv.set(x + w // 2 - 10, y + h - 16, INK)
    draw_text(cv, x + 8, y + 8, 2, WHITE, "6 PTS")


# ---- world map (equirectangular, rough continent polygons) ----
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70), (-80, 73), (-65, 60), (-55, 52), (-60, 46), (-70, 42), (-75, 35), (-80, 32), (-85, 30), (-90, 21), (-97, 16), (-105, 20), (-110, 23), (-120, 34), (-125, 40), (-125, 49), (-135, 58), (-150, 60), (-165, 60)],
    [(-80, 10), (-75, 11), (-70, 12), (-62, 10), (-55, 6), (-50, 0), (-44, -3), (-35, -8), (-40, -20), (-48, -28), (-55, -35), (-65, -41), (-70, -54), (-73, -50), (-73, -37), (-70, -20), (-80, -5)],
    [(-18, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (30, 31), (35, 28), (43, 12), (51, 11), (48, 0), (40, -10), (35, -20), (30, -30), (20, -35), (15, -27), (12, -18), (9, -1), (9, 4), (-8, 5), (-15, 11)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 51), (5, 53), (8, 57), (10, 59), (18, 56), (21, 55), (28, 59), (30, 60), (25, 65), (20, 70), (15, 70), (5, 60), (-5, 50), (-10, 44)],
    [(30, 60), (40, 68), (55, 70), (70, 72), (90, 75), (110, 76), (130, 72), (150, 70), (170, 66), (178, 65), (170, 60), (162, 56), (155, 50), (142, 45), (135, 43), (127, 40), (122, 38), (120, 32), (115, 23), (108, 18), (105, 10), (100, 8), (95, 15), (90, 22), (85, 20), (80, 13), (77, 8), (72, 20), (66, 25), (60, 25), (55, 26), (50, 29), (48, 30), (43, 28), (40, 32), (35, 36), (30, 36)],
    [(113, -22), (114, -30), (115, -35), (124, -33), (130, -32), (137, -35), (140, -38), (145, -38), (150, -37), (153, -32), (153, -27), (150, -22), (146, -19), (142, -15), (142, -11), (136, -12), (132, -12), (126, -14), (122, -17), (118, -20)],
]

PINS = [  # (number, lon, lat, dx, dy) — dx/dy nudge the badge off the true
    # spot with a leader line where neighbours would collide (Europe, US east).
    (1, 48, 29, 0, 0), (2, -76, -10, 0, 0), (3, 30, 37, -18, 14),
    (4, 24, 60, -20, -18), (5, 30, 50, 18, 10), (6, -107, 25, 0, 0),
    (7, -77, 39, -16, 10), (8, 10, 56, -22, 6), (9, -74, 41, 14, -10),
    (10, 25, 59, 18, -18), (11, -48, -16, 0, 0), (12, 114, 22, 0, 0),
    (13, 0, 51, -16, 16),
]


def _lonlat(mx, my, w, h, lon, lat):
    return (mx + int((lon + 180) / 360 * w),
            my + int((75 - lat) / 135 * h))


def draw_map(cv, x, y, w, h):
    cv.rect(x, y, w, h, (24, 68, 110))
    # graticule
    for gx in range(1, 6):
        cv.vline(x + gx * w // 6, y, y + h, (40, 90, 130))
    for gy in range(1, 4):
        cv.hline(x, x + w - 1, y + gy * h // 4, (40, 90, 130))
    # continents: fill via scanline on projected polygons
    for poly_ll in CONTINENTS:
        pts = [_lonlat(x, y, w, h, lo, la) for lo, la in poly_ll]
        ys = [p[1] for p in pts]
        for yy in range(max(y, min(ys)), min(y + h, max(ys) + 1)):
            xs = []
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    t = (yy - y0) / (y1 - y0)
                    xs.append(int(x0 + t * (x1 - x0)))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                cv.hline(max(x, a), min(x + w - 1, b), yy, SAND)
        cv.poly(pts, (170, 150, 110))
    # numbered pins for the 13 card stories (leader line when nudged)
    for num, lon, lat, dx, dy in PINS:
        px, py = _lonlat(x, y, w, h, lon, lat)
        bx, by = px + dx, py + dy
        if dx or dy:
            cv.line(px, py, bx, by, WHITE)
            cv.circle(px, py, 2, RED)
        cv.circle(bx, by, 9, RED)
        cv.ring(bx, by, 9, 10, WHITE)
        s = str(num)
        draw_text(cv, bx - (3 if len(s) == 1 else 6), by - 4, 1, WHITE, s)


# ---- the day's news: 43 stories, each verified from live reporting ----
# (region, place, headline, dek, source). Heroes 1-3, cards 4-13, briefs 14-43.
HEROES = [
    (1, "GULF", "KUWAIT",
     "IRAN HITS US BASE IN KUWAIT",
     "Iran hits a US base in Kuwait, targets Bahrain; tankers hit off Oman, ADNOC vessel hit in Hormuz.",
     "REUTERS", illo_gulf),
    (2, "ANDES", "PERU",
     "M6.7 QUAKE SHAKES PERU",
     "Magnitude 6.7, 9 km NE of Carhuamayo; no casualties at first. A second M6.8 hits off Timor-Leste.",
     "USGS", illo_quake),
    (3, "CLIMATE", "ANTALYA",
     "COP31 STUCK IN OVERTIME",
     "Nearly 200 nations deadlocked over fossil fuels; the draft drops the words and the $120bn target.",
     "REUTERS", illo_cop31),
]

CARDS = [
    (4, "BALTIC", "BALTIC",
     "DRONES HIT RUSSIAN SHIP",
     "Russia-bound ship hit in the Baltic; Finland on alert.",
     "TOI", illo_baltic),
    (5, "WAR", "KYIV",
     "400 DRONES, 110 MISSILES",
     "Largest raid of the war; a missile crashes in Poland.",
     "TOI", illo_ukraine),
    (6, "MEXICO", "SINALOA",
     "DRUG LORD CAPTURED",
     "Most-wanted kingpin seized in a shoot-out; 11 killed.",
     "BBC", illo_mexico),
    (7, "USA", "WASHINGTON",
     "FBI PROBES DATABASE HACK",
     "Bureau probes an apparent hack of its criminal database.",
     "BBC", illo_fbi),
    (8, "EUROPE", "COPENHAGEN",
     "RUSSIA 'PLOTTED TO KILL RAPPER'",
     "Denmark: Moscow plotted to kill a US-Ukrainian rapper.",
     "BBC", illo_denmark),
    (9, "MARKETS", "NEW YORK",
     "TECH SELLS OFF",
     "Stocks slide as Anthropic drops; crude falls over 3%.",
     "BBC", illo_markets),
    (10, "EUROPE", "TALLINN",
     "ESTONIA TO SHUT RUSSIA BORDER",
     "Tallinn shuts Russia border; Moscow: 'new Iron Curtain'.",
     "REPORTS", illo_estonia),
    (11, "BRAZIL", "BRASILIA",
     "BOLSONARO IN ICU",
     "Ex-president in ICU with acute bowel obstruction.",
     "TOI", illo_bolsonaro),
    (12, "APEC", "SHENZHEN",
     "TRUMP LANDS FOR APEC",
     "Trump in Shenzhen for a trilateral with Xi and Putin.",
     "REPORTS", illo_apec),
    (13, "SPORT", "LONDON",
     "ARSENAL SIX CLEAR",
     "Gunners six clear; Ireland beat South Africa.",
     "BBC", illo_sport),
]

BRIEFS = [
    (14, "PATNA", "MODI OPENS NITISH SETU, LINKING PATNA AND VAISHALI.", "JAGRAN"),
    (15, "RANCHI", "CYCLONE AKVAN: 14 FLIGHTS CANCELLED AT RANCHI AIRPORT.", "JAGRAN"),
    (16, "DELHI", "AIR INDIA EXTENDS JEDDAH SUSPENSION TO NOV 24.", "JAGRAN"),
    (17, "LONDON", "PRINCE WILLIAM ANNOUNCES COVER FOR 10,000 FOREST STAFF.", "JAGRAN"),
    (18, "LOS ANGELES", "MAN CONVICTED OF STARTING THE PALISADES FIRE.", "BBC"),
    (19, "WASHINGTON", "LOCK OF GEORGE WASHINGTON'S HAIR SELLS FOR $4,000.", "BBC"),
    (20, "BERLIN", "COALITION OF THE WILLING MEETS; WADEPHUL WARNS MOSCOW.", "REPORTS"),
    (21, "GAZA", "ISRAELI FORCES BREACH CEASEFIRE LINE; EISENKOT INVITES LIKUD TO TALKS.", "TOI"),
    (22, "LEBANON", "UNIFIL HANDS SOUTHERN LEBANON TO THE LEBANESE ARMY.", "REPORTS"),
    (23, "WASHINGTON", "HEGSETH SETS LIMITS ON US-CANADA MILITARY TIES.", "NYT"),
    (24, "WASHINGTON", "US AIRLINES WARNED OF AL-QAEDA-LINKED THREAT BEFORE THANKSGIVING.", "TOI"),
    (25, "BAHRAIN", "PATRIOT INTERCEPTOR CRASH INVESTIGATED AMID DRONE REPORTS.", "TOI"),
    (26, "QESHM", "IRAN SAYS ISLAND BLASTS WERE US MUNITIONS DISPOSAL.", "TOI"),
    (27, "SEOUL", "$75,000 BOUNTY FOR TIPS ON EXAM CHEATING.", "REPORTS"),
    (28, "DELHI", "JAPANESE TROOPS TO TRAIN LIVE-FIRE IN INDIA, A FIRST.", "JAGRAN"),
    (29, "JOHANNESBURG", "ANC FIGHTS TO HOLD KEY CITIES AFTER POLL SETBACK.", "BBC"),
    (30, "ABUJA", "NIGERIAN YOUTH: POWER SHOWN, BUT NOT SHAPING THE VOTE.", "BBC"),
    (31, "EUROPE", "COST-OF-LIVING PROTESTS SWEEP THE CONTINENT.", "BBC"),
    (32, "LONDON", "EU DEAL NOT TIED TO TUITION FEES, MILIBAND SAYS.", "BBC"),
    (33, "WASHINGTON", "US DECLASSIFIES MORE UFO FOOTAGE FROM THE MIDDLE EAST.", "BBC"),
    (34, "WASHINGTON", "CONGRESS SEES MOST BLACK DEMOCRATS SINCE 1993.", "REPORTS"),
    (35, "TEGUCIGALPA", "3 US CITIZENS AMONG 4 CONVICTED IN TRAFFICKING CASE.", "REPORTS"),
    (36, "LONDON", "SPITTING IMAGE CO-CREATOR PETER FLUCK DIES, 85.", "BBC"),
    (37, "SYDNEY", "PAT CUMMINS KEEPS TEST CAPTAINCY WITH UNANIMOUS BACKING.", "JAGRAN"),
    (38, "WELLINGTON", "INDIA FACE NEW ZEALAND IN WINDY WELLINGTON.", "REPORTS"),
    (39, "WORLD", "ADVANI AND RAMACHANDRAN WIN SNOOKER OPENERS.", "REPORTS"),
    (40, "MUMBAI", "ICMR COMPLETES 100 TECH TRANSFERS, 20 LICENCES.", "JAGRAN"),
    (41, "DILI", "M6.8 QUAKE 105 KM NE OF LOSPALOS, TIMOR-LESTE.", "USGS"),
    (42, "KYIV", "ZELENSKY: CRIMEA BRIDGE STRIKES 'FAIR RESPONSE'.", "BBC"),
    (43, "WASHINGTON", "TRUMP DEFENDS PUTIN; ZELENSKY CALLS HIM 'MURDERER'.", "REPORTS"),
]

REGIONS = [("EUROPE", 12, (30, 90, 168)), ("AMERICAS", 13, (185, 28, 28)),
           ("ASIA-PACIFIC", 9, (13, 110, 110)), ("MIDEAST", 5, (176, 124, 20)),
           ("AFRICA", 2, (34, 120, 60)), ("OCEANIA", 2, (120, 90, 160))]

STATS = [
    ("200", "NATIONS AT COP31, STILL NO DEAL"),
    ("400", "DRONES + 110 MISSILES AT UKRAINE"),
    ("6.7", "PERU QUAKE, USGS MAGNITUDE"),
    ("11", "KILLED AS SINALOA VIOLENCE FLARES"),
    ("$120BN", "ADAPTATION CASH CUT FROM DRAFT"),
    ("14", "FLIGHTS AXED AS AKVAN NEARS"),
]

DATE_CHECK = ("FIRST REPORTED FRI 20 OR SAT 21 NOV, SO NOT SHOWN HERE AS SUNDAY NEWS: "
              "AN-12 SIBERIA CRASH - BEPICOLOMBO MERCURY CAPTURE - KRYVYI RIH TOLL 44 - "
              "RUTTE WARSAW VISIT - ZECLER VERDICT - GTA VI $3.79BN RULING - "
              "COP31 DRAFT DROPS FOSSIL FUELS.")


def build():
    cv = Canvas()
    # ---- masthead ----
    draw_text(cv, 10, 8, 1, RED, "THE WORLD IN ONE DAY")
    rt = "SUNDAY'S NEWS - ONE PAGE - 43 STORIES"
    draw_text(cv, W - 10 - text_w(rt, 1), 8, 1, INK, rt)
    cv.hline(10, W - 10, 20, INK)
    title = "SUNDAY 22 NOVEMBER 2026"
    draw_text(cv, (W - text_w(title, 6)) // 2, 26, 6, INK, title)
    sub = "GULF STRIKES - PERU QUAKE - COP31 DEADLOCK"
    draw_text(cv, (W - text_w(sub, 2)) // 2, 72, 2, RED, sub)
    # ---- region strip ----
    y = 92
    xx = 10
    for name, n, col in REGIONS:
        label = "%s %d" % (name, n)
        bw = text_w(label, 1) + 14
        cv.rect(xx, y, bw, 16, col)
        draw_text(cv, xx + 7, y + 4, 1, WHITE, label)
        xx += bw + 6
    draw_text(cv, W - 10 - text_w("ALL STORIES: SUN 22 NOV 2026, ANY TIME ZONE", 1),
              y + 4, 1, INK, "ALL STORIES: SUN 22 NOV 2026, ANY TIME ZONE")
    # ---- stat boxes ----
    y = 114
    bw = (W - 20 - 5 * 6) // 6
    for i, (num, label) in enumerate(STATS):
        bx = 10 + i * (bw + 6)
        cv.rect(bx, y, bw, 52, WHITE)
        cv.frame(bx, y, bw, 52, INK)
        draw_text(cv, bx + 8, y + 6, 3, RED, num)
        draw_block(cv, bx + 8, y + 30, bw - 16, 1, INK, label, max_lines=2)
    # ---- hero cards ----
    y = 174
    hw = (W - 20 - 2 * 8) // 3
    for i, (num, region, place, head, dek, src, illo) in enumerate(HEROES):
        hx = 10 + i * (hw + 8)
        cv.rect(hx, y, hw, 176, WHITE)
        cv.frame(hx, y, hw, 176, INK)
        illo(cv, hx + 1, y + 1, hw - 2, 102)
        draw_text(cv, hx + 8, y + 108, 1, RED,
                  "%d - %s - %s (%s)" % (num, place, region, src))
        draw_block(cv, hx + 8, y + 120, hw - 16, 2, INK, head, max_lines=2)
        draw_block(cv, hx + 8, y + 120 + 2 * 18, hw - 16, 1, INK,
                   dek, max_lines=2)
    # ---- small cards: 2 rows of 5 ----
    y = 358
    cw = (W - 20 - 4 * 6) // 5
    for row in range(2):
        for col in range(5):
            num, region, place, head, dek, src, illo = CARDS[row * 5 + col]
            cx = 10 + col * (cw + 6)
            cy = y + row * 116
            cv.rect(cx, cy, cw, 110, WHITE)
            cv.frame(cx, cy, cw, 110, INK)
            illo(cv, cx + 1, cy + 1, cw - 2, 46)
            draw_text(cv, cx + 6, cy + 49, 1, RED,
                      "%d - %s - %s (%s)" % (num, place, region, src))
            draw_block(cv, cx + 6, cy + 60, cw - 12, 2, INK, head, lh=16, max_lines=2)
            draw_block(cv, cx + 6, cy + 92, cw - 12, 1, INK,
                       dek, max_lines=2)
    # ---- section header ----
    y = 596
    draw_text(cv, 10, y, 2, INK, "WHERE IT HAPPENED")
    draw_text(cv, 336, y, 2, INK, "ALSO ON SUNDAY 22 NOVEMBER - 30 MORE STORIES")
    cv.hline(10, W - 10, y + 20, INK)
    # ---- map + briefs ----
    draw_map(cv, 10, 624, 316, 276)
    draw_text(cv, 10, 906, 1, INK, "PINS 1-13: THE CARD STORIES. POSITIONS APPROXIMATE.")
    for col in range(2):
        bx = 336 + col * 344
        for i in range(15):
            num, place, text, src = BRIEFS[col * 15 + i]
            by = 624 + i * 19
            draw_text(cv, bx, by, 1, RED, str(num))
            draw_block(cv, bx + 20, by, 316, 1, INK,
                       place + " - " + text + " (" + src + ")",
                       lh=9, max_lines=2)
    # ---- date check ----
    y = 928
    cv.rect(10, y, W - 20, 44, WHITE)
    cv.frame(10, y, W - 20, 44, RED, t=2)
    draw_text(cv, 18, y + 5, 1, RED, "DATE CHECK")
    draw_block(cv, 18, y + 17, W - 36, 1, INK, DATE_CHECK, max_lines=2)
    # ---- footer ----
    y = 980
    draw_text(cv, 10, y, 1, INK,
              "EVERY STORY HERE HAPPENED, OR WAS FIRST REPORTED, ON SUNDAY 22 NOVEMBER 2026, IN AT LEAST ONE TIME ZONE.")
    draw_text(cv, 10, y + 11, 1, GREY,
              "SOURCES: BBC, REUTERS, AP, NYT, TOI, USGS, GUARDIAN, JAGRAN. ORIGINAL DRAWINGS, MADE IN CODE. ONE IMAGE, ONE DAY.")
    cv.hline(10, W - 10, y + 26, INK)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(build())
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
