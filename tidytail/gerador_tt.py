#!/usr/bin/env python3
"""Gera o post (1080x1350 JPG) e o Reels (1080x1920 MP4) diários da TidyTail Co.

Uso: python3 tidytail/gerador_tt.py tidytail/posts/AAAA-MM-DD-<handle>.json

Formato do JSON de entrada:
{
  "produto": "<handle de tidytail/produtos.json>",
  "post": {"img": 1, "headline": "Shedding season? Not on your couch.", "sub": "Steam Brush 3-in-1"},
  "reel": {
    "slides": [{"img": 2, "text": "POV: your dog sheds on EVERYTHING"}, ...],   # 4 a 6 slides
    "cta": "Tap the link in bio"
  }
}
Saídas: mesmo nome com -post.jpg e -reel.mp4 ao lado do JSON.
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FB = os.path.join(BASE, "fonts", "Poppins-Bold.ttf")
FM = os.path.join(BASE, "fonts", "Poppins-Medium.ttf")
CREAM, TEAL, ORANGE, WHITE, DARK = (251, 244, 232), (31, 78, 90), (232, 131, 58), (255, 255, 255), (30, 30, 30)
FPS, SLIDE_S, END_S = 30, 2.4, 2.2


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_text(draw, text, path, maxw, maxlines, start, minsize=34):
    size = start
    while size > minsize:
        f = font(path, size)
        ls = wrap(draw, text, f, maxw)
        if len(ls) <= maxlines:
            return f, ls
        size -= 4
    f = font(path, minsize)
    return f, wrap(draw, text, f, maxw)[:maxlines]


def contain(img, w, h):
    s = min(w / img.width, h / img.height)
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)


def cover(img, w, h):
    s = max(w / img.width, h / img.height)
    im = img.resize((int(img.width * s) + 1, int(img.height * s) + 1), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))


def load_img(handle, n):
    p = os.path.join(BASE, "produtos", handle, f"{int(n):02d}.jpg")
    if not os.path.exists(p):
        sys.exit(f"Imagem não existe: {p}")
    return Image.open(p).convert("RGB")


def pill(draw, xy_center, text, fnt, fill, color, padx=34, pady=16):
    tw = draw.textlength(text, font=fnt)
    asc, desc = fnt.getmetrics()
    th = asc + desc
    cx, cy = xy_center
    box = (cx - tw / 2 - padx, cy - th / 2 - pady, cx + tw / 2 + padx, cy + th / 2 + pady)
    draw.rounded_rectangle(box, radius=(box[3] - box[1]) / 2, fill=fill)
    draw.text((cx - tw / 2, cy - th / 2), text, font=fnt, fill=color)
    return box


def make_post(spec, prod, out):
    W, H = 1080, 1350
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    # cartão branco com a foto
    card = (60, 60, W - 60, 910)
    d.rounded_rectangle(card, radius=36, fill=WHITE)
    ph = contain(load_img(prod["handle"], spec["img"]), card[2] - card[0] - 40, card[3] - card[1] - 40)
    im.paste(ph, (card[0] + (card[2] - card[0] - ph.width) // 2, card[1] + (card[3] - card[1] - ph.height) // 2))
    # preço
    pill(d, (W - 200, 950), f"${prod['price']}", font(FB, 46), ORANGE, WHITE)
    # headline
    f, ls = fit_text(d, spec["headline"], FB, W - 160, 2, 64)
    y = 1010
    for l in ls:
        d.text((80, y), l, font=f, fill=TEAL)
        y += int(f.size * 1.18)
    sub = spec.get("sub") or prod["title"].replace("TidyTail ", "")
    fs, ls2 = fit_text(d, sub, FM, W - 160, 1, 38, 28)
    d.text((80, y + 6), ls2[0], font=fs, fill=DARK)
    # rodapé
    d.rectangle((0, H - 80, W, H), fill=TEAL)
    ft = font(FM, 30)
    t = "TidyTail Co.  ·  Free US shipping  ·  Link in bio"
    d.text(((W - d.textlength(t, font=ft)) / 2, H - 62), t, font=ft, fill=WHITE)
    im.save(out, "JPEG", quality=90)


def slide_frame(photo_bg, photo, text, t, dur):
    W, H = 1080, 1920
    z = 1.0 + 0.06 * (t / dur)  # zoom lento
    fr = photo_bg.copy()
    pw, phh = int(photo.width * z), int(photo.height * z)
    p = photo.resize((pw, phh), Image.BILINEAR)
    fr.paste(p, ((W - pw) // 2, (H - phh) // 2 + 120))
    d = ImageDraw.Draw(fr)
    f, ls = fit_text(d, text, FB, W - 200, 3, 76, 48)
    lh = int(f.size * 1.2)
    bh = lh * len(ls) + 60
    top = 230
    d.rounded_rectangle((70, top, W - 70, top + bh), radius=34, fill=WHITE)
    y = top + 30
    for l in ls:
        d.text(((W - d.textlength(l, font=f)) / 2, y), l, font=f, fill=TEAL)
        y += lh
    # marca
    fb = font(FB, 34)
    d.text(((W - d.textlength("TidyTail Co.", font=fb)) / 2, H - 150), "TidyTail Co.", font=fb, fill=WHITE)
    return fr


def end_frame(prod, cta):
    W, H = 1080, 1920
    im = Image.new("RGB", (W, H), TEAL)
    d = ImageDraw.Draw(im)
    ph = contain(load_img(prod["handle"], 1), 760, 760)
    card = ((W - 820) // 2, 380, (W + 820) // 2, 1200)
    d.rounded_rectangle(card, radius=40, fill=WHITE)
    im.paste(ph, ((W - ph.width) // 2, 380 + (820 - ph.height) // 2))
    name = prod["title"].replace("TidyTail ", "")
    f, ls = fit_text(d, name, FB, W - 160, 2, 58, 40)
    y = 1260
    for l in ls:
        d.text(((W - d.textlength(l, font=f)) / 2, y), l, font=f, fill=WHITE)
        y += int(f.size * 1.2)
    pill(d, (W / 2, y + 70), f"${prod['price']}  ·  Free US shipping", font(FB, 44), ORANGE, WHITE)
    fc = font(FB, 64)
    d.text(((W - d.textlength(cta, font=fc)) / 2, 200), cta, font=fc, fill=CREAM)
    return im


def make_reel(spec, prod, out):
    W, H = 1080, 1920
    slides = spec["slides"]
    if not 3 <= len(slides) <= 6:
        sys.exit("O Reels precisa de 3 a 6 slides.")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(SLIDE_S * FPS)
    for s in slides:
        src = load_img(prod["handle"], s["img"])
        bg = cover(src, W, H).filter(ImageFilter.GaussianBlur(40))
        bg = Image.blend(bg, Image.new("RGB", (W, H), (0, 0, 0)), 0.35)
        photo = contain(src, 940, 1100)
        for i in range(n):
            pr.stdin.write(slide_frame(bg, photo, s["text"], i / FPS, SLIDE_S).tobytes())
    ef = end_frame(prod, spec.get("cta", "Tap the link in bio")).tobytes()
    for _ in range(int(END_S * FPS)):
        pr.stdin.write(ef)
    pr.stdin.close()
    if pr.wait() != 0:
        sys.exit("ffmpeg falhou")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    spec_path = sys.argv[1]
    spec = json.load(open(spec_path, encoding="utf-8"))
    prods = {p["handle"]: p for p in json.load(open(os.path.join(BASE, "produtos.json"), encoding="utf-8"))}
    prod = prods.get(spec["produto"]) or sys.exit(f"Produto desconhecido: {spec['produto']}")
    stem = spec_path[:-5]
    make_post(spec["post"], prod, stem + "-post.jpg")
    make_reel(spec["reel"], prod, stem + "-reel.mp4")
    print(stem + "-post.jpg")
    print(stem + "-reel.mp4")


if __name__ == "__main__":
    main()
