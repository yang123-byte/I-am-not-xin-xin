#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把 src/2.N.jpg 的实拍照片做成游戏用的「圆形头像」贴图：
  · 按 CROPS 里逐张指定的取景框裁成正方形
  · 套抗锯齿的圆形蒙版（四角透明），边缘轻微羽化
  · 缩放到统一画布、居中、烤一圈柔和暗边（和 normalize_assets.py 同一套）
  · 输出 assets/fruits/NN-<tier>.png，并打印主体平均色（填 FRUITS 的 pc1/pc2）

和 normalize_assets.py 的区别：那个是给白底商品图做「自动抠底 + 保留轮廓」的，
实拍照片背景太杂抠不动，所以这里不抠底，改成整张裁圆。

用法：
  python tools/photo_assets.py              # 出贴图
  python tools/photo_assets.py --preview    # 只出预览图 _crop_preview.png / _icon_preview.png
"""
import os
import sys
import argparse

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalize_assets import bake_rim          # 复用同一套烤暗边

SRC = "src"
OUT = os.path.join("assets", "fruits")
SIZE = 512            # 输出画布边长
FILL = 0.92           # 圆形直径占画布比例（必须与 game.js 的 ASSET_FILL 一致）
FEATHER = 1.6         # 圆形边缘羽化像素（在 512 画布上）
SS = 4                # 蒙版超采样倍数（抗锯齿）

TIERS = ["grape", "cherry", "orange", "lemon", "kiwi",
         "tomato", "peach", "pineapple", "coconut", "halfmelon", "watermelon"]

# 每张的取景：(中心 x / 图宽, 中心 y / 图高, 正方形边长 / 图宽)
CROPS = {
    1:  (0.42, 0.38, 0.78),   # 餐厅里坐着的女孩：脸居中（头本身在原图偏上，靠下压取景框）
    2:  (0.50, 0.36, 1.00),   # 脸部特写：眼睛到嘴唇
    3:  (0.50, 0.45, 1.00),   # 更近的特写：整张脸
    4:  (0.55, 0.36, 0.78),   # 举手撩头发：头 + 手臂 + 条纹衫
    5:  (0.50, 0.50, 0.85),   # 低头看圣诞礼盒：人和盒子都在
    6:  (0.47, 0.42, 0.95),   # 情侣合照：两张脸（往左让开女生的额头）
    7:  (0.47, 0.45, 0.62),   # 餐厅里托腮：以她为主，右侧半张脸
    8:  (0.50, 0.35, 0.80),   # 手摊开 + 一桌菜（收紧，让脸大一点）
    9:  (0.42, 0.38, 1.00),   # 镜子自拍：两个人
    10: (0.50, 0.38, 0.70),   # 玫瑰花前的两个人
    11: (0.50, 0.36, 0.95),   # 地铁上戴熊耳朵滤镜的两个人
}


def src_path(i):
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = os.path.join(SRC, "2.%d.%s" % (i, ext))
        if os.path.exists(p):
            return p
    raise RuntimeError("找不到 src/2.%d.*" % i)


def crop_box(i, w, h):
    """把 CROPS 的比例换算成像素方框，越界就整体推回图内"""
    fx, fy, fs = CROPS[i]
    side = max(8, int(round(fs * w)))
    side = min(side, w, h)
    x = int(round(fx * w - side / 2.0))
    y = int(round(fy * h - side / 2.0))
    x = max(0, min(x, w - side))
    y = max(0, min(y, h - side))
    return (x, y, x + side, y + side)


def circle_mask(size, d, feather):
    """抗锯齿圆蒙版：直径 d，居中，边缘 feather 像素羽化"""
    big = size * SS
    m = Image.new("L", (big, big), 0)
    r = d * SS / 2.0
    c = (big - 1) / 2.0
    ImageDraw.Draw(m).ellipse((c - r, c - r, c + r, c + r), fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    if feather > 0:
        from PIL import ImageFilter
        m = m.filter(ImageFilter.GaussianBlur(feather))
        a = np.asarray(m).astype(np.float32)
        a[a < 6] = 0.0                     # 掐掉羽化拖出来的极淡外圈
        m = Image.fromarray(a.astype(np.uint8), "L")
    return m


def process(i):
    im = Image.open(src_path(i)).convert("RGB")
    w, h = im.size
    box = crop_box(i, w, h)
    sq = im.crop(box)

    d = int(round(SIZE * FILL))
    sq = sq.resize((d, d), Image.LANCZOS)

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    off = (SIZE - d) // 2
    canvas.paste(sq, (off, off))
    canvas.putalpha(circle_mask(SIZE, d, FEATHER))
    canvas = bake_rim(canvas)

    name = "%02d-%s.png" % (i, TIERS[i - 1])
    dst = os.path.join(OUT, name)
    canvas.save(dst, "PNG", optimize=True)

    px = np.asarray(canvas).astype(np.float32)
    solid = px[:, :, 3] > 200
    mean = px[:, :, :3][solid].mean(axis=0) if solid.any() else np.array([200., 200., 200.])
    hexc = "#%02x%02x%02x" % tuple(int(v) for v in mean)

    print("2.%-3d %-4s -> %-22s 裁 %s  主体 %s  %5.1f%%  %6.1f KB"
          % (i, "%dx%d" % (w, h), name, "%dx%d@(%d,%d)" % (box[2] - box[0], box[3] - box[1], box[0], box[1]),
             hexc, solid.mean() * 100, os.path.getsize(dst) / 1024))
    return hexc


def write_parts():
    """写 assets/fruits/parts.js

    贴图是圆形照片，主体直径 = 2r（见 ASSET_FILL 的换算），所以碰撞形状就是
    「一个半径 r 的圆」，IoU 恰好 1.0 —— 不要拿 tools/build_parts.py 去跑这组
    素材：那个脚本是给不规则轮廓做内接小圆逼近的，对整圆反而只有 0.46。
    """
    import json
    one = {"parts": [[0.0, 0.0, 1.0]], "rb": 1.0}
    body = json.dumps([one] * 11, separators=(",", ":"))
    js = ("/* 自动生成，请勿手改 —— 由 tools/photo_assets.py 生成\n"
          "   贴图是圆形照片，碰撞形状 = 单个半径 r 的圆（与视觉完全一致，IoU 1.0）\n"
          "   parts: [ox, oy, s]，单位是「以 r 为 1」；rb: 碰撞包围圆半径 */\n"
          "window.SUIKA_PARTS = %s;\n" % body)
    dst = os.path.join(OUT, "parts.js")
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(js)
    print("-> %s（11 级全部单圆）" % dst)


def preview():
    """两张预览：左=原图上的取景框，右=裁圆后的实际效果"""
    from PIL import ImageFilter

    # —— 取景框总览 ——
    CW, CH = 300, 400
    cols, rows = 4, 3
    sheet = Image.new("RGB", (CW * cols, CH * rows), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for i in range(1, 12):
        im = Image.open(src_path(i)).convert("RGB")
        w, h = im.size
        box = crop_box(i, w, h)
        im.thumbnail((CW - 8, CH - 30), Image.LANCZOS)
        k = im.width / w
        c, r = (i - 1) % cols, (i - 1) // cols
        x = c * CW + (CW - im.width) // 2
        y = r * CH + 24 + (CH - 30 - im.height) // 2
        sheet.paste(im, (x, y))
        d.rectangle((x + box[0] * k, y + box[1] * k, x + box[2] * k, y + box[3] * k),
                    outline=(255, 60, 60), width=3)
        d.text((c * CW + 8, r * CH + 6), "tier %d   red = crop" % i, fill=(255, 255, 0))
    sheet.save("_crop_preview.png")
    print("-> _crop_preview.png")

    # —— 裁圆效果（放在奶油色棋盘上，带几种实际尺寸）——
    W, H = 1180, 1180
    bg = Image.new("RGB", (W, H), (252, 246, 232))
    d = ImageDraw.Draw(bg)
    d.text((16, 10), "circular icons on the game board (cream) - top row big, bottom row at real game sizes",
           fill=(90, 70, 50))
    d.text((16, 30), "top = 124px (watermelon size)   bottom = 17/23/31/39/48/58/69/81/94/108/124 px (real relative sizes)",
           fill=(140, 120, 100))
    for i in range(1, 12):
        icon = Image.open(os.path.join(OUT, "%02d-%s.png" % (i, TIERS[i - 1]))).convert("RGBA")
        c, r = (i - 1) % 4, (i - 1) // 4
        big = icon.resize((260, 260), Image.LANCZOS)
        x = 20 + c * 290 + (260 - big.width) // 2
        y = 60 + r * 380
        bg.paste(big, (x, y), big)

    RAD = [17, 23, 31, 39, 48, 58, 69, 81, 94, 108, 124]
    x = 40
    base = 1040
    for i in range(1, 12):
        icon = Image.open(os.path.join(OUT, "%02d-%s.png" % (i, TIERS[i - 1]))).convert("RGBA")
        s = RAD[i - 1] * 2
        if s < 20:
            s = 20
        small = icon.resize((s, s), Image.LANCZOS)
        bg.paste(small, (x, base + (124 - small.height) // 2 + 20), small)
        x += max(s, 26) + 12
    bg.save("_icon_preview.png")
    print("-> _icon_preview.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="只出预览，不写 assets")
    args = ap.parse_args()

    if args.preview:
        for i in range(1, 12):          # 预览也要先有成品图
            process(i)
        write_parts()
        preview()
        return

    os.makedirs(OUT, exist_ok=True)
    print("画布 %dx%d  圆直径 %.0f%%\n" % (SIZE, SIZE, FILL * 100))
    colors = [process(i) for i in range(1, 12)]
    write_parts()
    print("\n各级圆形主体平均色（想换粒子色可以参考；都是照片平均下来的灰褐色，")
    print("  直接当粒子色会发闷，现行 FRUITS 的 pc1/pc2 是一套金色，别动更好）:")
    for i, c in enumerate(colors):
        print("  tier %2d  %-10s %s" % (i, TIERS[i], c))


if __name__ == "__main__":
    main()
