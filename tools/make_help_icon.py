#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把 src/3.1.jpg 做成「老公助你」按钮上的圆形小头像。

和 tools/photo_assets.py 的区别：那个产出的是棋盘上的水果贴图（512 画布、烤暗边、
由 canvas 绘制）；这个是 DOM 按钮里的一个 <img>，只在 20px 上下显示，
所以直接按显示尺寸出图，不带烤边 —— 那圈描边交给 CSS 的 box-shadow，
在任意 dpr 下都是干净的 1 物理像素，比烤进图里再缩放靠谱。

产物：assets/help-icon.webp （页面实际加载）
     assets/help-icon.png  （不认 WebP 时的回退，<picture> 里挂的）

用法：
  python tools/make_help_icon.py                 # 按下面 CROP 出图
  python tools/make_help_icon.py --cx .5 --cy .35 --size .5   # 临时换个取景框试试
  python tools/make_help_icon.py --preview       # 出一张放大对比图，先看再定
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

SRC = os.path.join("src", "3.1.jpg")
OUT_DIR = "assets"
NAME = "help-icon"
OUT_PX = 96           # 出图边长。按钮上最大约 22px（手机端）× dpr 3 ≈ 66px，96 够用
FEATHER = 1.0         # 圆形边缘羽化（在 OUT_PX 尺度上），抗锯齿用
SS = 4                # 蒙版超采样倍数
QUALITY = 88          # 与 tools/make_webp.py 保持一致

# 取景框：(圆心 x / 图宽, 圆心 y / 图高, 正方形边长 / 图宽)
# 原图 940×940 是张半张脸埋在衣领里的自拍，整张裁圆的话头只占中间一小条、
# 缩到 20px 就糊成一团，所以框到眉眼这一带。
CROP = (0.50, 0.41, 0.60)


def square_box(im, cx, cy, size):
    w, h = im.size
    side = size * w
    x, y = cx * w, cy * h
    box = (int(round(x - side / 2)), int(round(y - side / 2)),
           int(round(x + side / 2)), int(round(y + side / 2)))
    # 越界就整体平移回画面内，避免裁出黑边
    dx = max(0, -box[0]) - max(0, box[2] - w)
    dy = max(0, -box[1]) - max(0, box[3] - h)
    return (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)


def circular_mask(px, feather=FEATHER):
    """抗锯齿的圆形蒙版：先按 4 倍画圆再缩下来，最后轻微羽化"""
    big = Image.new("L", (px * SS, px * SS), 0)
    ImageDraw.Draw(big).ellipse((0, 0, px * SS - 1, px * SS - 1), fill=255)
    m = big.resize((px, px), Image.LANCZOS)
    if feather > 0:
        m = m.filter(ImageFilter.GaussianBlur(feather))
    return m


def build(crop, px=OUT_PX):
    im = Image.open(SRC).convert("RGB")
    face = im.crop(square_box(im, *crop)).resize((px, px), Image.LANCZOS)

    out = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    out.paste(face, (0, 0), circular_mask(px))
    return out


def save(icon, out_dir=OUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, NAME + ".png")
    webp = os.path.join(out_dir, NAME + ".webp")
    icon.save(png, "PNG", optimize=True)
    icon.save(webp, "WEBP", quality=QUALITY, method=6)
    return png, webp


def preview(crop, px=OUT_PX):
    """出一张对比图：左边真尺寸（1x/2x/3x），右边放大到 240px 看细节"""
    icon = build(crop, px)
    Z = 240
    sheet = Image.new("RGB", (Z + 200, Z + 40), "#fffaea")
    d = ImageDraw.Draw(sheet)
    for j, size in enumerate((22, 44, 66)):
        small = icon.resize((size, size), Image.LANCZOS)
        sheet.paste(small, (20 + j * 50, 20), small)
    up = icon.resize((Z, Z), Image.LANCZOS)
    sheet.paste(up, (190, 20), up)
    d.text((20, 4), "1x / 2x / 3x 真尺寸", fill="#8a5a00")
    d.text((195, 4), "放大 %dx" % (Z // px), fill="#8a5a00")
    dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_help_icon_preview.png")
    sheet.save(dist)
    return os.path.normpath(dist)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cx", type=float, default=CROP[0], help="圆心 x / 图宽")
    ap.add_argument("--cy", type=float, default=CROP[1], help="圆心 y / 图高")
    ap.add_argument("--size", type=float, default=CROP[2], help="正方形边长 / 图宽")
    ap.add_argument("--px", type=int, default=OUT_PX, help="出图边长，默认 %d" % OUT_PX)
    ap.add_argument("--preview", action="store_true", help="只出预览图，不写素材")
    args = ap.parse_args()

    if not os.path.exists(SRC):
        print("找不到 %s" % SRC, file=sys.stderr)
        return 1

    crop = (args.cx, args.cy, args.size)
    if args.preview:
        print("预览已写出：%s" % preview(crop, args.px))
        return 0

    icon = build(crop, args.px)
    png, webp = save(icon)
    print("取景框  圆心 (%.2f, %.2f)  边长 %.2f" % crop)
    print("%-24s %6.1f KB" % (png, os.path.getsize(png) / 1024))
    print("%-24s %6.1f KB  ← 页面实际加载" % (webp, os.path.getsize(webp) / 1024))
    print("\n改了取景框记得同步 assets/help-icon.*，再跑 node physics.test.js 自检")
    return 0


if __name__ == "__main__":
    sys.exit(main())
