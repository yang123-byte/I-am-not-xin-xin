#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把 assets/fruits/NN-*.png 转成游戏真正加载的 WebP，并顺手按「这一级最大能画多大」缩图。

为什么要缩：
  棋盘逻辑宽度 420，dpr 封顶 2 —— 也就是说画到屏幕上的最大倍率就是 2 倍。
  第 i 级的直径是 2*r 逻辑像素，画的时候还要按 ASSET_FILL 除以 0.92 换算成贴图边长，
  所以这一级真正需要的贴图像素 = 4*r/0.92。
  葡萄 r=17 只需要 74px，塞一张 512 的图纯属浪费带宽（那 3.2MB 就是这么来的）。

产物：assets/fruits/NN-<tier>.webp
     PNG 原图保留不动 —— 一是 build_parts.py 还要拿 512 的轮廓算碰撞箱，
     二是老旧浏览器加载 .webp 失败时 game.js 会回退到 .png。

用法：
  python tools/make_webp.py                # 按 TIER_SIZES 缩图并转 WebP
  python tools/make_webp.py --quality 92   # 换质量（默认 88）
  python tools/make_webp.py --keep-size    # 不缩图，只转格式
"""
import argparse
import os
import sys

from PIL import Image

OUT = os.path.join("assets", "fruits")
TIERS = ["grape", "cherry", "orange", "lemon", "kiwi",
         "tomato", "peach", "pineapple", "coconut", "halfmelon", "watermelon"]

# 每一级的贴图边长（必须 ≥ 4*r/0.92，往上取整到好记的数；512 是上限）
TIER_SIZES = [96, 128, 160, 192, 224, 256, 320, 384, 416, 480, 512]


def convert(i, size, quality, keep_size):
    src = os.path.join(OUT, "%02d-%s.png" % (i, TIERS[i - 1]))
    if not os.path.exists(src):
        raise RuntimeError("缺少 %s，先跑 tools/normalize_assets.py 或 photo_assets.py" % src)

    im = Image.open(src).convert("RGBA")
    if not keep_size and im.width > size:
        im = im.resize((size, size), Image.LANCZOS)
    # 棋盘上不会拿去做半透明叠加，alpha 用快一点的编码方式即可
    dst = os.path.join(OUT, "%02d-%s.webp" % (i, TIERS[i - 1]))
    im.save(dst, "WEBP", quality=quality, method=6, exact=False)

    return os.path.getsize(src), os.path.getsize(dst), im.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", type=int, default=88, help="WebP 质量，默认 88")
    ap.add_argument("--keep-size", action="store_true", help="不缩图，只转格式")
    args = ap.parse_args()

    if not os.path.isdir(OUT):
        print("找不到 %s" % OUT, file=sys.stderr)
        return 1

    print("WebP quality=%d   %s\n" % (
        args.quality, "保持原尺寸" if args.keep_size else "按级缩图"))
    print("%-18s %8s %8s %8s %7s  %s" % ("贴图", "PNG", "WebP", "省下", "边长", "压缩比"))

    png_total = webp_total = 0
    for i in range(1, 12):
        png, webp, size = convert(i, TIER_SIZES[i - 1], args.quality, args.keep_size)
        png_total += png
        webp_total += webp
        print("%-18s %7.1fK %7.1fK %7.1fK %7d  %5.1fx" % (
            "%02d-%s" % (i, TIERS[i - 1]), png / 1024, webp / 1024,
            (png - webp) / 1024, size[0], png / max(webp, 1)))

    print("\n合计  %.2f MB → %.2f MB   （%.1f 倍）" % (
        png_total / 1048576, webp_total / 1048576, png_total / max(webp_total, 1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
