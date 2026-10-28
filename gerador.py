"""Gerador de Shorts do canal "Histórias do Livro de Mórmon".

Uso:  python3 gerador.py roteiros/<arquivo>.json videos/<arquivo>.mp4

O roteiro é um JSON com:
  titulo_video, descricao, tags, referencia,
  segmentos: [{"texto": "...", "cena": "<nome>", "gancho": true|false}, ...]
  aplicacao: frase final (cena "final")
Cenas disponíveis: veja CENAS no fim do arquivo.
"""
import json, math, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FS = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
GOLD = (255, 205, 110)
WHITE = (250, 246, 238)
SIL = (18, 12, 22)
CANAL = "Histórias do Livro de Mórmon"
WORD_T, LEAD, HOLD, XFADE = 0.27, 0.35, 1.7, 0.6

random.seed(3)
STARS = [(random.uniform(0, W), random.uniform(0, H * 0.55), random.uniform(1, 3.2), random.uniform(0, 6.3))
         for _ in range(140)]
_fc = {}


def F(path, size):
    if (path, size) not in _fc:
        _fc[(path, size)] = ImageFont.truetype(path, size)
    return _fc[(path, size)]


def ease(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3


def mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


# ------------------------------------------------------------------ elementos
def sky(d, top, mid, bot):
    for y in range(0, H, 6):
        k = y / H
        c = mix(top, mid, k / 0.55) if k < 0.55 else mix(mid, bot, (k - 0.55) / 0.45)
        d.rectangle([0, y, W, y + 6], fill=c)


def sun(d, x, y, r, core, glow_to):
    for i in range(40, 0, -1):
        rr = r * (1 + i * 0.08)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=mix(glow_to, core, (1 - i / 41) ** 1.6))
    d.ellipse([x - r, y - r, x + r, y + r], fill=core)


def stars(d, t, sky_c, alpha=1.0):
    for x, y, s, ph in STARS:
        a = (0.55 + 0.45 * math.sin(t * 2 + ph)) * alpha
        d.ellipse([x - s, y - s, x + s, y + s], fill=mix(sky_c, (255, 250, 230), a))


def dune(d, base, amp, freq, ph, color, drift=0):
    pts = [(0, H)] + [(x, base + amp * math.sin(x * freq + ph + drift) + amp * 0.4 * math.sin(x * freq * 2.3 + ph))
                      for x in range(0, W + 20, 20)] + [(W, H)]
    d.polygon(pts, fill=color)


def tent(d, x, y, s, c):
    d.polygon([(x - 90 * s, y), (x, y - 110 * s), (x + 90 * s, y)], fill=c)
    d.line([(x, y - 110 * s), (x, y - 140 * s)], fill=c, width=max(2, int(6 * s)))


def person(d, x, y, s, c, arm=None, spear=False):
    d.ellipse([x - 22 * s, y - 210 * s, x + 22 * s, y - 166 * s], fill=c)
    d.polygon([(x - 26 * s, y - 165 * s), (x + 26 * s, y - 165 * s), (x + 48 * s, y), (x - 48 * s, y)], fill=c)
    if arm:
        d.line([(x + 15 * s, y - 140 * s), arm], fill=c, width=max(2, int(14 * s)))
    if spear:
        d.line([(x + 40 * s, y + 10 * s), (x + 40 * s, y - 290 * s)], fill=c, width=max(2, int(6 * s)))
        d.polygon([(x + 30 * s, y - 280 * s), (x + 40 * s, y - 320 * s), (x + 50 * s, y - 280 * s)], fill=c)


def kneeling(d, x, y, s, c):
    d.ellipse([x + 30 * s, y - 175 * s, x + 74 * s, y - 131 * s], fill=c)
    d.polygon([(x - 50 * s, y), (x - 40 * s, y - 120 * s), (x + 50 * s, y - 135 * s), (x + 70 * s, y - 90 * s),
               (x + 20 * s, y - 60 * s), (x + 60 * s, y)], fill=c)


def bow(d, cx, cy, size, c, broken=0.0, width=12):
    def half(sign, off, rot):
        pts = []
        for i in range(46):
            a = math.radians(i * 2) * sign
            px, py = size * 0.35 * math.cos(a), -size * math.sin(a)
            r = math.radians(rot)
            pts.append((cx + px * math.cos(r) - py * math.sin(r) + off[0],
                        cy + px * math.sin(r) + py * math.cos(r) + off[1]))
        d.line(pts, fill=c, width=width, joint="curve")
        return pts[-1]
    b = ease(broken)
    e1 = half(1, (-40 * b, -30 * b), -18 * b)
    e2 = half(-1, (40 * b, 50 * b), 22 * b)
    if b < 0.05:
        d.line([e1, e2], fill=c, width=3)


def mountain(d, c, px, py, base):
    d.polygon([(-100, base), (px - 140, py + 160), (px, py), (px + 90, py + 90), (px + 260, py + 220),
               (W + 100, base), (W + 100, H), (-100, H)], fill=c)


def waves(d, base, t, colors):
    for i, c in enumerate(colors):
        y0 = base + i * 70
        pts = [(0, H)] + [(x, y0 + 18 * math.sin(x * 0.012 + t * (1.2 + i * 0.3) + i * 2)
                           + 8 * math.sin(x * 0.03 - t * 1.7)) for x in range(0, W + 20, 20)] + [(W, H)]
        d.polygon(pts, fill=c)


def boat(d, x, y, s, c, t):
    dy = 10 * math.sin(t * 1.5)
    ang = 0.05 * math.sin(t * 1.5 + 1)
    def rot(px, py):
        return (x + px * math.cos(ang) - py * math.sin(ang), y + dy + px * math.sin(ang) + py * math.cos(ang))
    d.polygon([rot(-180 * s, -40 * s), rot(180 * s, -40 * s), rot(130 * s, 30 * s), rot(-130 * s, 30 * s)], fill=c)
    d.polygon([rot(-170 * s, -40 * s), rot(-120 * s, -80 * s), rot(120 * s, -80 * s), rot(170 * s, -40 * s)], fill=c)
    d.ellipse([*rot(-30 * s, -70 * s), *rot(30 * s, -50 * s)], fill=(255, 225, 150))


def wall(d, base, c, t):
    d.rectangle([0, base, W, H], fill=c)
    for x in range(0, W, 70):
        d.rectangle([x, base - 40, x + 40, base], fill=c)
    for tx in (140, 760):
        d.rectangle([tx, base - 260, tx + 160, base], fill=c)
        for k in range(4):
            d.rectangle([tx + k * 45, base - 300, tx + k * 45 + 25, base - 260], fill=c)
        d.rectangle([tx + 65, base - 200, tx + 95, base - 150], fill=(255, 200, 120))


def flames(d, cx, base, t, scale=1.0):
    for i in range(9):
        off = (i - 4) * 38 * scale
        h = (260 + 90 * math.sin(t * 7 + i * 1.7) + 40 * math.sin(t * 13 + i)) * scale * (1 - abs(i - 4) * 0.13)
        w = 60 * scale
        col = mix((255, 90, 30), (255, 220, 120), 0.5 + 0.5 * math.sin(t * 9 + i))
        d.polygon([(cx + off - w, base), (cx + off + 10 * math.sin(t * 6 + i), base - h), (cx + off + w, base)], fill=col)
    d.polygon([(cx - 200 * scale, base), (cx + 200 * scale, base), (cx + 160 * scale, base + 30), (cx - 160 * scale, base + 30)],
              fill=(40, 20, 15))


def rays(d, cx, top, t, color, sky_c, n=9):
    for i in range(n):
        a0 = math.radians(60 + i * 60 / n + 2 * math.sin(t * 0.6 + i))
        a1 = a0 + math.radians(3)
        L = 2400
        k = 0.16 + 0.08 * math.sin(t * 1.3 + i)
        d.polygon([(cx, top), (cx + L * math.cos(a0), top + L * math.sin(a0)),
                   (cx + L * math.cos(a1), top + L * math.sin(a1))], fill=mix(sky_c, color, k))


def tree(d, cx, base, t, c):
    d.polygon([(cx - 30, base), (cx - 18, base - 330), (cx + 18, base - 330), (cx + 30, base)], fill=c)
    for (dx, dy, r) in ((0, -470, 190), (-150, -390, 140), (150, -390, 140), (-80, -560, 130), (90, -560, 130)):
        d.ellipse([cx + dx - r, base + dy - r, cx + dx + r, base + dy + r], fill=c)
    random.seed(11)
    for _ in range(26):
        fx = cx + random.uniform(-260, 260); fy = base - 470 + random.uniform(-200, 180)
        if (fx - cx) ** 2 / 300 ** 2 + (fy - (base - 470)) ** 2 / 230 ** 2 < 1:
            g = 0.6 + 0.4 * math.sin(t * 2.5 + fx)
            r = 11
            d.ellipse([fx - r * 2, fy - r * 2, fx + r * 2, fy + r * 2], fill=mix(c, (255, 240, 200), 0.3 * g))
            d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=mix(c, (255, 255, 240), g))


# ------------------------------------------------------------------ cenas
def c_deserto(d, lt, t):
    sky(d, (60, 40, 90), (230, 140, 90), (250, 200, 130))
    sun(d, W * 0.72, 760, 90, (255, 236, 190), (235, 150, 100))
    dr = lt * 0.12
    dune(d, 1100, 45, 0.005, 2, (180, 100, 70), dr)
    dune(d, 1260, 50, 0.004, 4, (110, 55, 50), -dr)
    dune(d, 1420, 30, 0.006, 0, SIL, dr * 0.6)
    for x, s in ((230, 1.0), (470, 0.8), (690, 1.1)):
        tent(d, x + lt * 6, 1435, s, SIL)
    for i, x in enumerate((820, 880, 930)):
        person(d, x - lt * 10, 1440, 0.55 + 0.05 * i, SIL)


def c_noite(d, lt, t):
    sky(d, (6, 8, 26), (28, 26, 66), (60, 40, 70))
    stars(d, t, (14, 14, 40))
    sun(d, W * 0.25, 420, 55, (235, 235, 215), (28, 26, 66))
    dune(d, 1250, 45, 0.004, 1, (34, 26, 50), lt * 0.12)
    dune(d, 1420, 35, 0.005, 4, (12, 8, 18), -lt * 0.12)
    for x in (260, 560):
        tent(d, x, 1430, 1.0, (12, 8, 18))
    for x in (720, 800, 880):
        person(d, x, 1440, 0.6, (12, 8, 18))


def c_arco(d, lt, t, broken=None):
    sky(d, (40, 22, 60), (205, 92, 60), (250, 170, 90))
    sun(d, W * 0.5, 980, 120, (255, 226, 160), (220, 110, 70))
    dune(d, 1150, 40, 0.006, 1, (120, 55, 50), lt * 0.12)
    dune(d, 1300, 55, 0.004, 3, (70, 30, 40), -lt * 0.12)
    dune(d, 1480, 35, 0.005, 5, SIL, lt * 0.06)
    bow(d, W * 0.5, 1010, 300, SIL, broken=(lt - 1.0) / 0.5 if broken is None else broken, width=18)


def c_aurora(d, lt, t):
    k = ease(lt / 3.5)
    sky(d, mix((40, 40, 90), (90, 140, 200), k), mix((230, 130, 90), (250, 200, 150), k), (255, 225, 170))
    sun(d, W * 0.68, 1000 - 220 * k, 110, (255, 240, 200), (245, 170, 110))
    mountain(d, (70, 40, 60), W * 0.45, 820, 1500)
    dune(d, 1480, 25, 0.005, 3, SIL, lt * 0.12)
    person(d, W * 0.45, 822, 0.45, SIL, arm=(W * 0.45 + 40, 822 - 120))


def c_mar(d, lt, t):
    sky(d, (20, 30, 70), (90, 90, 140), (200, 150, 140))
    stars(d, t, (30, 36, 80), 0.5)
    sun(d, W * 0.3, 700, 70, (240, 230, 210), (90, 90, 140))
    waves(d, 1150, t, [(40, 50, 90), (28, 34, 66)])
    boat(d, W * 0.55 + lt * 8, 1205, 1.1, SIL, t)
    waves(d, 1300, t + 1, [(22, 26, 52), (14, 16, 34), (8, 8, 20)])


def c_cidade(d, lt, t):
    sky(d, (30, 20, 50), (170, 80, 70), (240, 160, 100))
    sun(d, W * 0.5, 980, 130, (255, 220, 160), (200, 100, 80))
    wall(d, 1260, SIL, t)
    person(d, W * 0.5, 1222, 0.7, SIL, arm=(W * 0.5 + 70, 1222 - 230))


def c_fogo(d, lt, t):
    sky(d, (8, 6, 16), (40, 18, 24), (90, 35, 25))
    stars(d, t, (14, 10, 22), 0.6)
    glow = 0.5 + 0.1 * math.sin(t * 8)
    sun(d, W * 0.5, 1180, 160, mix((90, 35, 25), (255, 150, 60), glow), (40, 18, 24))
    dune(d, 1330, 20, 0.005, 2, (20, 10, 14), 0)
    flames(d, W * 0.5, 1340, t, 1.0)
    person(d, W * 0.24, 1350, 0.9, SIL)
    for x in (700, 820, 940):
        person(d, x, 1460, 0.75, (10, 6, 10), spear=True)


def c_oracao(d, lt, t):
    sky(d, (25, 30, 70), (120, 100, 150), (240, 190, 150))
    sun(d, W * 0.62, 900, 160, (255, 240, 210), (120, 100, 150))
    dune(d, 1330, 30, 0.004, 2, (60, 40, 70), lt * 0.08)
    d.polygon([(560, 1340), (640, 1230), (760, 1220), (840, 1340)], fill=SIL)
    kneeling(d, W * 0.38, 1342, 1.3, SIL)
    dune(d, 1460, 20, 0.006, 5, SIL, -lt * 0.08)


def c_luz(d, lt, t):
    base = (14, 14, 40)
    sky(d, (8, 8, 26), (30, 28, 64), (70, 54, 80))
    stars(d, t, (20, 20, 50), 0.6)
    rays(d, W * 0.5, -60, t, (255, 240, 200), (40, 36, 70))
    sun(d, W * 0.5, 520, 70 * (1 + 0.05 * math.sin(t * 2)), (255, 252, 235), (60, 50, 80))
    dune(d, 1380, 25, 0.004, 2, (20, 16, 30), 0)
    for i, x in enumerate(range(140, 1000, 110)):
        person(d, x, 1470 + (i % 2) * 20, 0.6 + 0.08 * (i % 3), (10, 8, 16))


def c_multidao(d, lt, t):
    sky(d, (30, 30, 80), (160, 120, 140), (245, 205, 160))
    sun(d, W * 0.5, 780, 120, (255, 240, 200), (170, 130, 150))
    dune(d, 1200, 15, 0.004, 2, (70, 50, 70), 0)
    d.rectangle([0, 1260, W, H], fill=(50, 34, 52))
    d.rectangle([W * 0.5 - 130, 1080, W * 0.5 + 130, 1200], fill=(40, 26, 40))
    d.rectangle([W * 0.5 - 170, 1060, W * 0.5 + 170, 1085], fill=(40, 26, 40))
    person(d, W * 0.5, 1062, 0.8, SIL, arm=(W * 0.5 + 90, 1062 - 220))
    for row, (y, s, n) in enumerate(((1300, 0.55, 11), (1400, 0.65, 9), (1510, 0.8, 7))):
        for i in range(n):
            x = (i + 0.5) * W / n + (row % 2) * 30
            person(d, x, y, s, mix((30, 20, 36), SIL, row / 2))


def c_exercito(d, lt, t):
    sky(d, (40, 26, 50), (190, 100, 70), (245, 180, 110))
    sun(d, W * 0.3, 900, 100, (255, 230, 170), (200, 110, 80))
    dune(d, 1200, 40, 0.005, 1, (90, 45, 45), lt * 0.06)
    for row, (y, s, n) in enumerate(((1230, 0.35, 16), (1320, 0.45, 13), (1430, 0.6, 10))):
        for i in range(n):
            x = (i + 0.5) * W / n + (row % 2) * 25 + lt * 4
            person(d, x, y, s, mix((60, 30, 36), SIL, row / 2), spear=True)
    dune(d, 1500, 15, 0.006, 4, SIL, 0)


def c_arvore(d, lt, t):
    sky(d, (12, 14, 40), (50, 46, 90), (110, 80, 110))
    stars(d, t, (24, 24, 56), 0.7)
    sun(d, W * 0.5, 980, 220, (90, 80, 120), (40, 38, 80))
    dune(d, 1400, 20, 0.004, 2, (24, 18, 34), 0)
    tree(d, W * 0.5, 1420, t, SIL)
    d.line([(60, 1520), (W - 60, 1440)], fill=(200, 170, 110), width=5)  # barra de ferro
    person(d, 260, 1500, 0.55, SIL, arm=(300, 1470))


def c_final(d, lt, t):
    sky(d, (20, 24, 60), (120, 90, 120), (240, 190, 140))
    sun(d, W * 0.5, 1150, 200, (255, 235, 190), (150, 100, 120))
    dune(d, 1350, 30, 0.004, 2, (60, 35, 55), lt * 0.08)
    dune(d, 1480, 20, 0.006, 5, SIL, -lt * 0.08)


CENAS = {
    "deserto": c_deserto,        # viagem, família, acampamento
    "noite": c_noite,            # angústia, murmuração, fome
    "arco": c_arco,              # arco se partindo (Néfi)
    "arco_quebrado": lambda d, lt, t: c_arco(d, lt, t, broken=1.0),
    "aurora": c_aurora,          # subida ao monte, vitória, esperança
    "mar": c_mar,                # viagem por mar, barcos, tempestade
    "cidade": c_cidade,          # muralhas, cidades, profeta sobre o muro
    "fogo": c_fogo,              # martírio, julgamento, fornalha
    "oracao": c_oracao,          # oração, arrependimento, conversão
    "luz": c_luz,                # visão, aparição, anjo, milagre
    "multidao": c_multidao,      # discurso, sermão, rei falando ao povo
    "exercito": c_exercito,      # batalhas, jovens guerreiros, Davi
    "arvore": c_arvore,          # árvore da vida, sonho, fruto
    "final": c_final,
}


def scene(name, lt, t):
    img = Image.new("RGB", (W, H))
    CENAS[name](ImageDraw.Draw(img), lt, t)
    z = 1 + 0.05 * min(1, lt / 6)
    cw, ch = int(W / z), int(H / z)
    x0, y0 = (W - cw) // 2, (H - ch) // 2
    return img.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR)


# ------------------------------------------------------------------ texto
def layout(d, words, fnt, max_w):
    lines, cur, cw = [], [], 0
    sp = d.textlength(" ", font=fnt)
    for w in words:
        ww = d.textlength(w, font=fnt)
        if cur and cw + sp + ww > max_w:
            lines.append(cur); cur, cw = [], 0
        cw += (sp if cur else 0) + ww
        cur.append((w, ww))
    if cur:
        lines.append(cur)
    return lines, sp


def captions(img, text, lt, hook=False, fade=1.0):
    words = text.split()
    size = 84 if hook else 62
    fnt = F(FB, size)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    lines, sp = layout(od, words, fnt, W - 160)
    lh = int(size * 1.32)
    block = lh * len(lines)
    y = (400 if hook else 1560) - block / 2
    if not hook:
        od.rounded_rectangle([50, y - 45, W - 50, y + block + 35], radius=40, fill=(10, 6, 18, int(150 * fade)))
    shown = (lt - LEAD) / WORD_T
    idx = 0
    for line in lines:
        lw = sum(w for _, w in line) + sp * (len(line) - 1)
        x = (W - lw) / 2
        for w, ww in line:
            a = max(0.0, min(1.0, (shown - idx) / 0.6)) * fade
            if a > 0:
                newest = idx >= shown - 1.2 and lt < LEAD + len(words) * WORD_T + 0.6
                lift = (1 - ease(a)) * 18
                od.text((x + 4, y + 5 - lift), w, font=fnt, fill=(0, 0, 0, int(170 * a)))
                od.text((x, y - lift), w, font=fnt, fill=(GOLD if newest else WHITE) + (int(255 * a),))
            x += ww + sp
            idx += 1
        y += lh
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


def chrome(img, t, total):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 12], fill=(30, 20, 30))
    d.rectangle([0, 0, int(W * t / total), 12], fill=GOLD)
    f = F(FB, 34)
    w = d.textlength(CANAL, font=f)
    d.text(((W - w) / 2 + 2, 92), CANAL, font=f, fill=(0, 0, 0))
    d.text(((W - w) / 2, 90), CANAL, font=f, fill=(255, 240, 215))


# ------------------------------------------------------------------ montagem
def timeline(rot):
    segs, t = [], 0.0
    items = [(s["texto"], s["cena"], bool(s.get("gancho"))) for s in rot["segmentos"]]
    items.append((rot["aplicacao"], "final", False))
    for text, sc, hook in items:
        dur = LEAD + len(text.split()) * WORD_T + HOLD
        segs.append((t, dur, text, sc, hook))
        t += dur
    return segs, t, t + 2.8


def frame(t, rot, segs, story_end, total):
    if t >= story_end:
        lt = t - story_end
        img = scene("final", lt + 5, t)
        d = ImageDraw.Draw(img)
        a = ease(lt / 0.5)
        for i, line in enumerate(["Siga para mais", "histórias de fé"]):
            f = F(FB, 82)
            w = d.textlength(line, font=f)
            d.text(((W - w) / 2, 700 + i * 105 + (1 - a) * 40), line, font=f, fill=mix((20, 24, 60), WHITE, a))
        f = F(FS, 54)
        ref = rot["referencia"]
        w = d.textlength(ref, font=f)
        d.rounded_rectangle([(W - w) / 2 - 40, 1010, (W + w) / 2 + 40, 1100], radius=45,
                            fill=mix((20, 24, 60), GOLD, ease((lt - 0.4) / 0.5)))
        d.text(((W - w) / 2, 1022), ref, font=f, fill=(30, 20, 30))
        chrome(img, t, total)
        return img
    i = max(k for k, s in enumerate(segs) if s[0] <= t)
    st, dur, text, sc, hook = segs[i]
    lt = t - st
    img = scene(sc, lt, t)
    if i > 0 and lt < XFADE and segs[i - 1][3] != sc:
        p = segs[i - 1]
        img = Image.blend(scene(p[3], t - p[0], t), img, ease(lt / XFADE))
    fade = 1 - ease((lt - (dur - 0.3)) / 0.3)
    img = captions(img, text, lt, hook=hook, fade=fade)
    chrome(img, t, total)
    return img


PROGRESSOES = [
    [[57, 60, 64], [53, 57, 60], [48, 55, 60, 64], [55, 59, 62]],   # Am F C G
    [[50, 53, 57], [46, 50, 53], [48, 52, 55], [45, 48, 52]],       # Dm Bb C Am
    [[52, 55, 59], [48, 52, 55], [43, 47, 50], [50, 54, 57]],       # Em C G D
]


def soundtrack(total, cuts, path, seed):
    sr = 44100
    n = int(total * sr)
    t = np.arange(n) / sr
    y = np.zeros(n)
    nf = lambda m: 440 * 2 ** ((m - 69) / 12)
    chords = PROGRESSOES[seed % len(PROGRESSOES)]
    cl = 4.0
    for ci in range(int(total / cl) + 1):
        s0 = ci * cl
        seg = (t >= s0 - 0.5) & (t < s0 + cl + 1.5)
        tt = t[seg] - s0
        env = np.clip(tt / 1.2 + 0.4, 0, 1) * np.clip((cl + 1.5 - tt) / 1.5, 0, 1)
        for m in chords[ci % 4]:
            for o, g in ((0, 0.05), (-12, 0.035), (12, 0.012)):
                y[seg] += g * env * np.sin(2 * np.pi * nf(m + o) * t[seg] + 0.3 * np.sin(2 * np.pi * 0.2 * t[seg]))
    for c in cuts:
        seg = (t >= c) & (t < c + 3)
        tt = t[seg] - c
        for f, g in ((nf(81), 0.06), (nf(88), 0.03)):
            y[seg] += g * np.exp(-2.2 * tt) * np.sin(2 * np.pi * f * tt)
    dl = int(0.33 * sr)
    for _ in range(3):
        y[dl:] += 0.32 * y[:-dl]
    y *= np.clip(np.minimum(t / 1.5, (total - t) / 2.0), 0, 1)
    y = y / np.max(np.abs(y)) * 0.5
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes((y * 32767).astype(np.int16).tobytes())


def validar(rot):
    for k in ("titulo_video", "descricao", "referencia", "segmentos", "aplicacao"):
        assert k in rot, f"falta o campo {k}"
    for s in rot["segmentos"]:
        assert s["cena"] in CENAS, f"cena desconhecida: {s['cena']} (use: {', '.join(CENAS)})"
    _, _, total = timeline(rot)
    assert 25 <= total <= 75, f"duração {total:.0f}s fora do ideal (25 a 75 s): ajuste o texto"
    return total


def main(json_path, out_path):
    rot = json.load(open(json_path, encoding="utf-8"))
    total = validar(rot)
    segs, story_end, total = timeline(rot)
    wav = out_path.rsplit(".", 1)[0] + ".wav"
    soundtrack(total, [s[0] for s in segs] + [story_end], wav, sum(map(ord, rot["referencia"])))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-shortest", out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(int(total * FPS)):
        p.stdin.write(frame(k / FPS, rot, segs, story_end, total).tobytes())
    p.stdin.close(); p.wait()
    import os; os.remove(wav)
    print(f"ok: {out_path} ({total:.1f}s)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
