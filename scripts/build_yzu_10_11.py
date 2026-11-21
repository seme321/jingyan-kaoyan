# -*- coding: utf-8 -*-
"""
Generate stem figures (q*_orig.png), solution schematic figures (q*_sol.png),
standardized exam packs in `扬州大学已整理数据/{2011,2010}/`, and web-ready JSON + WebP
assets in `web/public/data/yzu-849/` for Yangzhou University 849 Hydraulics (2011 & 2010).
"""

import copy
import json
import math
from collections import deque
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "扬州大学待处理数据"
PACK_ROOT = ROOT / "扬州大学已整理数据"
WEB_COURSE_DIR = ROOT / "web" / "public" / "data" / "yzu-849"


def clean_scan_crop(img: Image.Image, pad: int = 16, thresh: int = 190, bg_clean: int = 225, min_blob: int = 28) -> Image.Image:
    """Remove tiny isolated scan dust specks, whiten paper background, trim tightly, and add pure white margin."""
    rgb = np.array(img.convert("RGB")).copy()
    gray = np.array(img.convert("L"))
    dark = gray < thresh
    h, w = dark.shape
    visited = np.zeros_like(dark, dtype=bool)

    for y in range(h):
        for x in range(w):
            if dark[y, x] and not visited[y, x]:
                q = deque([(y, x)])
                visited[y, x] = True
                comp = [(y, x)]
                while q:
                    cy, cx = q.popleft()
                    for ny in range(max(0, cy - 1), min(h, cy + 2)):
                        for nx in range(max(0, cx - 1), min(w, cx + 2)):
                            if dark[ny, nx] and not visited[ny, nx]:
                                visited[ny, nx] = True
                                q.append((ny, nx))
                                comp.append((ny, nx))
                if len(comp) < min_blob:
                    for py, px in comp:
                        rgb[py, px] = 255
                        gray[py, px] = 255
                        dark[py, px] = False

    rgb[gray > bg_clean] = 255
    mask = np.any(rgb < 250, axis=2)
    if not np.any(mask):
        return Image.fromarray(rgb)
    ys, xs = np.where(mask)
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    cropped = rgb[y0:y1, x0:x1]
    ch, cw, _ = cropped.shape
    canvas = np.full((ch + 2 * pad, cw + 2 * pad, 3), 255, dtype=np.uint8)
    canvas[pad:pad + ch, pad:pad + cw] = cropped
    return Image.fromarray(canvas)


# ==============================================================================
# 2011 STEM FIGURES & SOLUTION DIAGRAMS
# ==============================================================================

def build_2011_figures(fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(RAW_DIR / "849-水力学（水）2011.pdf")
    pages = []
    for pno in range(len(doc)):
        pix = doc[pno].get_pixmap(dpi=300)
        pages.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))

    # Crisp 300-DPI scan crops (with dust-speck cleaning) for q01, q05, q07, q09, q10, q11
    scan_crops = [
        ("q01_orig.png", pages[0], (730, 1178, 1760, 1445), 35),
        ("q05_orig.png", pages[0], (760, 2245, 1730, 2765), 35),
        ("q07_orig.png", pages[1], (900, 1110, 1600, 1560), 28),
        ("q09_orig.png", pages[1], (980, 2710, 1500, 3055), 28),
        ("q10_orig.png", pages[2], (810, 785, 1660, 1340), 28),
        ("q11_orig.png", pages[2], (740, 1930, 1740, 2505), 30),
    ]
    for fname, im, box, min_b in scan_crops:
        sub = im.crop(box)
        if fname == "q11_orig.png":
            arr_sub = np.array(sub.convert("RGB")).copy()
            arr_sub[470:, :160] = 255  # remove isolated scan blotch in bottom-left margin without touching subscripts
            sub = Image.fromarray(arr_sub)
        clean_scan_crop(sub, pad=16, min_blob=min_b).save(fig_dir / fname)

    # q06_orig and q08_orig had merged ink on small subscripts in the scan -> redraw cleanly in matplotlib!
    draw_2011_q06_orig(fig_dir / "q06_orig.png")
    draw_2011_q08_orig(fig_dir / "q08_orig.png")

    # Solution figures for 2011
    draw_2011_q02_sol(fig_dir / "q02_sol.png")
    draw_2011_q07_sol(fig_dir / "q07_sol.png")
    draw_2011_q08_sol(fig_dir / "q08_sol.png")
    draw_2011_q09_sol(fig_dir / "q09_sol.png")
    draw_2011_q10_sol(fig_dir / "q10_sol.png")


def draw_2011_q06_orig(out_path: Path) -> None:
    """Clean redraw of 2011 题6图 (Piston oil chamber + mercury U-tube manometer)."""
    fig, ax = plt.subplots(figsize=(5.6, 5.2))
    fig.patch.set_facecolor("white")

    # Oil chamber: x in [0.5, 3.1], y in [1.1, 3.6]; neck x in [1.45, 2.15], y in [3.6, 4.15]
    ax.plot([1.35, 1.48, 1.48, 0.5, 0.5, 3.1, 3.1, 3.62, 3.62],
            [4.15, 4.15, 3.6, 3.6, 1.1, 1.1, 1.75, 1.75, 0.72], color="#0f172a", lw=2.2)
    ax.plot([2.25, 2.12, 2.12, 3.1, 3.1, 3.78, 3.78],
            [4.15, 4.15, 3.6, 3.6, 1.92, 1.92, 0.72], color="#0f172a", lw=2.2)

    # U-tube bottom & right leg at x in [4.42, 4.58] up to y=3.85
    th = np.linspace(np.pi, 2 * np.pi, 60)
    # Outer arc center (4.10, 0.72), radius 0.48 (from 3.62 to 4.58); inner arc radius 0.32 (from 3.78 to 4.42)
    ax.plot(4.10 + 0.48 * np.cos(th), 0.72 + 0.48 * np.sin(th), color="#0f172a", lw=2.2)
    ax.plot(4.10 + 0.32 * np.cos(th), 0.72 + 0.32 * np.sin(th), color="#0f172a", lw=2.2)
    ax.plot([4.42, 4.42], [0.72, 3.85], color="#0f172a", lw=2.2)
    ax.plot([4.58, 4.58], [0.72, 3.85], color="#0f172a", lw=2.2)

    # Mercury fill: left interface at y=0.85 (plane 1-1), right meniscus at y=1.80
    xs_out = 4.10 + 0.47 * np.cos(th)
    ys_out = 0.72 + 0.47 * np.sin(th)
    xs_in = 4.10 + 0.33 * np.cos(th[::-1])
    ys_in = 0.72 + 0.33 * np.sin(th[::-1])
    hg_pts = ([[3.63, 0.85], [3.63, 0.72]] + list(zip(xs_out, ys_out))
              + [[4.57, 0.72], [4.57, 1.80], [4.43, 1.80], [4.43, 0.72]]
              + list(zip(xs_in, ys_in)) + [[3.77, 0.72], [3.77, 0.85]])
    ax.add_patch(patches.Polygon(hg_pts, closed=True, facecolor="#1e293b", edgecolor="#0f172a", lw=1.0, zorder=4))

    # T-shaped hatched piston in neck (stem x in [1.54, 2.06], bottom at y=3.90, cap y in [4.60, 5.05])
    piston_pts = [[1.54, 3.90], [2.06, 3.90], [2.06, 4.60], [2.62, 4.60], [2.62, 5.05], [0.98, 5.05], [0.98, 4.60], [1.54, 4.60]]
    ax.add_patch(patches.Polygon(piston_pts, closed=True, facecolor="white", edgecolor="#0f172a", lw=2.0, hatch="////", zorder=5))

    # Dimension d on piston stem
    ax.annotate("", xy=(1.54, 4.35), xytext=(1.05, 4.35), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.6))
    ax.annotate("", xy=(2.06, 4.35), xytext=(2.55, 4.35), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.6))
    ax.text(1.80, 4.35, r"$d$", fontsize=12, ha="center", va="center", fontweight="bold",
            bbox=dict(boxstyle="square,pad=0.04", fc="white", ec="none"), zorder=6)

    # Plane 1-1 & dimensions h and Delta h
    ax.plot([3.05, 5.05], [0.85, 0.85], color="#0f172a", lw=1.5)
    ax.text(2.96, 0.85, "1", fontsize=11, ha="right", va="center", fontweight="bold")
    ax.text(5.12, 0.85, "1", fontsize=11, ha="left", va="center", fontweight="bold")

    ax.plot([2.10, 3.65], [3.90, 3.90], color="#0f172a", lw=1.4)
    ax.annotate("", xy=(3.35, 3.90), xytext=(3.35, 0.85), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.5))
    ax.text(3.35, 2.48, r"$h$", fontsize=12, ha="center", va="center",
            bbox=dict(boxstyle="square,pad=0.06", fc="white", ec="none"))

    ax.plot([3.95, 4.43], [1.80, 1.80], color="#0f172a", lw=1.4)
    ax.annotate("", xy=(4.12, 1.80), xytext=(4.12, 0.85), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.4))
    ax.text(4.12, 1.32, r"$\Delta h$", fontsize=11, ha="center", va="center",
            bbox=dict(boxstyle="square,pad=0.04", fc="white", ec="none"))

    # Atmospheric pressure pa arrow at right tube top
    ax.annotate("", xy=(4.50, 3.82), xytext=(4.50, 4.35), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.8))
    ax.text(4.65, 4.22, r"$p_a$", fontsize=12, va="center")

    # Relative density labels (Chinese strictly outside $...$)
    ax.text(1.75, 2.35, "油 " + r"$S = 0.92$", fontsize=11.5, ha="center", fontweight="bold")
    ax.plot([2.90, 3.68], [0.35, 0.52], color="#0f172a", lw=1.3)
    ax.text(2.82, 0.32, "水银 " + r"$S = 13.60$", fontsize=11, ha="right", va="center", fontweight="bold")

    ax.set_xlim(0.25, 5.45)
    ax.set_ylim(0.05, 5.30)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2011_q08_orig(out_path: Path) -> None:
    """Clean redraw of 2011 题8图 (Cylindrical float tethered to bottom circular valve in gasoline)."""
    fig, ax = plt.subplots(figsize=(5.8, 4.6))
    fig.patch.set_facecolor("white")

    # Tank walls with bottom opening d2 at x in [2.32, 2.68]
    ax.plot([0.6, 0.6, 2.32], [3.8, 0.7, 0.7], color="#0f172a", lw=2.2)
    ax.plot([2.68, 4.4, 4.4], [0.7, 0.7, 3.8], color="#0f172a", lw=2.2)

    # Liquid surface at y = 3.10
    ax.plot([0.6, 2.0], [3.10, 3.10], color="#0f172a", lw=1.8)
    ax.plot([3.0, 4.85], [3.10, 3.10], color="#0f172a", lw=1.8)
    for sx in [1.25, 3.75]:
        ax.plot([sx - 0.25, sx + 0.25], [2.98, 2.98], color="#0f172a", lw=1.3)
        ax.plot([sx - 0.14, sx + 0.14], [2.88, 2.88], color="#0f172a", lw=1.2)
        ax.plot([sx - 0.05, sx + 0.05], [2.78, 2.78], color="#0f172a", lw=1.2)

    # Cylindrical float x in [2.0, 3.0], y in [2.62, 3.60] with vertical shading lines
    ax.add_patch(patches.Rectangle((2.0, 2.62), 1.0, 0.98, facecolor="white", edgecolor="#0f172a", lw=2.0, zorder=4))
    for vx in [2.08, 2.16, 2.26, 2.38, 2.62, 2.74, 2.84, 2.92]:
        dy = 0.12 * abs(vx - 2.5)
        ax.plot([vx, vx], [2.70 + dy, 3.52 - dy], color="#334155", lw=1.1, zorder=5)

    # Tether cord z from y=0.75 to y=2.62 + flat circular valve disk at bottom (x in [2.22, 2.78], y in [0.70, 0.77])
    ax.plot([2.5, 2.5], [0.77, 2.62], color="#0f172a", lw=1.8, zorder=4)
    ax.add_patch(patches.Rectangle((2.20, 0.70), 0.60, 0.07, facecolor="#1e293b", edgecolor="#0f172a", lw=1.5, zorder=5))

    # Diameter d1 at top of float
    ax.plot([2.0, 2.0], [3.63, 4.05], color="#0f172a", lw=1.4)
    ax.plot([3.0, 3.0], [3.63, 4.05], color="#0f172a", lw=1.4)
    ax.annotate("", xy=(3.0, 3.92), xytext=(2.0, 3.92), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.5))
    ax.text(2.5, 4.00, r"$d_1$", fontsize=12, ha="center", va="bottom")

    # Diameter d2 at bottom opening
    ax.plot([2.32, 2.32], [0.28, 0.68], color="#0f172a", lw=1.4)
    ax.plot([2.68, 2.68], [0.28, 0.68], color="#0f172a", lw=1.4)
    ax.annotate("", xy=(2.32, 0.40), xytext=(1.85, 0.40), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.5))
    ax.annotate("", xy=(2.68, 0.40), xytext=(3.15, 0.40), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.5))
    ax.text(2.5, 0.40, r"$d_2$", fontsize=11.5, ha="center", va="center")

    # Vertical dimensions h, z, H
    ax.plot([3.02, 3.55], [2.62, 2.62], color="#0f172a", lw=1.3)
    ax.annotate("", xy=(3.38, 3.10), xytext=(3.38, 3.52), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.4))
    ax.text(3.38, 2.86, r"$h$", fontsize=11.5, ha="center", va="center")

    ax.annotate("", xy=(3.38, 2.62), xytext=(3.38, 0.70), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.4))
    ax.text(3.25, 1.66, r"$z$", fontsize=12, ha="right", va="center")

    ax.plot([4.40, 4.85], [0.70, 0.70], color="#0f172a", lw=1.4)
    ax.annotate("", xy=(4.70, 3.10), xytext=(4.70, 0.70), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.5))
    ax.text(4.58, 1.90, r"$H$", fontsize=12, ha="right", va="center")

    ax.set_xlim(0.35, 5.05)
    ax.set_ylim(0.15, 4.35)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2011_q02_sol(out_path: Path) -> None:
    """Force equilibrium diagram of open-channel uniform flow segment on positive slope."""
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    fig.patch.set_facecolor("white")

    th = np.radians(12.0)
    ex = np.array([np.cos(th), -np.sin(th)])   # downstream along bed
    en = np.array([np.sin(th), np.cos(th)])    # upward normal to bed
    p0 = np.array([0.8, 2.3])
    bed_end = p0 + 5.8 * ex

    # Channel bed & parallel free water surface
    h_w = 1.15
    ax.plot([p0[0], bed_end[0]], [p0[1], bed_end[1]], color="#0f172a", lw=2.4)
    ws_0, ws_1 = p0 + h_w * en, bed_end + h_w * en
    ax.plot([ws_0[0], ws_1[0]], [ws_0[1], ws_1[1]], color="#0284c7", lw=2.0)

    # Control volume between s1=1.5 and s2=4.3
    b1, b2 = p0 + 1.5 * ex, p0 + 4.3 * ex
    t1, t2 = b1 + h_w * en, b2 + h_w * en
    ax.add_patch(patches.Polygon([b1, b2, t2, t1], closed=True, facecolor="#bae6fd", edgecolor="#0284c7", lw=1.8, alpha=0.7))

    # Equal hydrostatic pressure triangles P1 and P2
    p1_mid = b1 + 0.35 * h_w * en
    p2_mid = b2 + 0.35 * h_w * en
    ax.annotate("", xy=p1_mid, xytext=p1_mid - 0.95 * ex, arrowprops=dict(arrowstyle="->", color="#b45309", lw=2.2))
    ax.text(*(p1_mid - 1.02 * ex + np.array([0.0, 0.22])), r"$P_1 = \frac{1}{2}\rho g h_0^2 b$", fontsize=9.2, ha="center", color="#92400e")

    ax.annotate("", xy=p2_mid, xytext=p2_mid + 0.95 * ex, arrowprops=dict(arrowstyle="->", color="#b45309", lw=2.2))
    ax.text(*(p2_mid + 1.02 * ex + np.array([0.0, 0.22])), r"$P_2 = P_1$", fontsize=9.5, ha="center", color="#92400e", fontweight="bold")

    # Gravity G (vertical) and component G sin(theta) along +ex
    cm = 0.5 * (b1 + t2)
    ax.annotate("", xy=(cm[0], cm[1] - 1.25), xytext=cm, arrowprops=dict(arrowstyle="->", color="#ea580c", lw=2.1))
    ax.text(cm[0] - 0.10, cm[1] - 1.08, r"$G$", fontsize=10.5, ha="right", color="#c2410c", fontweight="bold")
    ax.annotate("", xy=cm + 1.05 * ex, xytext=cm, arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.4))
    ax.text(*(cm + 1.08 * ex + 0.18 * en), r"重力推进分力 $G\sin\theta$", fontsize=9.5, color="#15803d", fontweight="bold")

    # Boundary shear resistance Ff along -ex at bed (label placed clearly left of orange G arrow)
    bed_mid = 0.5 * (b1 + b2)
    ax.annotate("", xy=bed_mid - 0.85 * ex - 0.12 * en, xytext=bed_mid + 0.45 * ex - 0.12 * en,
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.3))
    ax.text(*(bed_mid - 1.15 * ex - 0.34 * en), r"边界摩阻力 $F_f = \tau_0 \chi L$", fontsize=9.5, ha="center", color="#dc2626", fontweight="bold")

    # Horizontal reference line at right end showing slope angle theta (label below dashed line)
    ax.plot([bed_end[0] - 1.8, bed_end[0] + 0.2], [bed_end[1], bed_end[1]], color="#475569", ls="--", lw=1.2)
    ax.text(bed_end[0] - 1.25, bed_end[1] - 0.18, r"$\theta$ ($i=\sin\theta>0$)", fontsize=9.2, ha="center", color="#334155")

    ax.text(4.8, 3.25, "均匀流等速平衡条件：\n" + r"$P_1 - P_2 + G\sin\theta - F_f = 0$" + "\n" + r"$\Rightarrow G\sin\theta = F_f > 0 \Rightarrow i > 0$",
            fontsize=9.3, ha="center", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.32", fc="#f8fafc", ec="#94a3b8", lw=1.1))

    ax.set_xlim(0.2, 7.2)
    ax.set_ylim(0.55, 3.95)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2011_q07_sol(out_path: Path) -> None:
    """Moment equilibrium diagram for automatic hinged gate (alpha = 60 deg)."""
    fig, ax = plt.subplots(figsize=(6.8, 4.5))
    fig.patch.set_facecolor("white")

    al = np.radians(60.0)
    eg = np.array([np.cos(al), np.sin(al)])     # up along gate
    en = np.array([np.sin(al), -np.cos(al)])    # normal down-right (direction of P1)
    toe = np.array([2.4, 0.6])
    L_tot = 3.4
    top = toe + L_tot * eg

    # Ground, upstream water H=2m (y_ws1 = 0.6 + 2.6*sin60 = 2.85), downstream water h=0.4m (y_ws2 = 0.6 + 0.55*sin60 = 1.08)
    ax.plot([0.3, 6.2], [0.6, 0.6], color="#0f172a", lw=2.3)
    L1_vis, L2_vis = 2.70, 0.72
    ws1_y = toe[1] + L1_vis * np.sin(al)
    ws2_y = toe[1] + L2_vis * np.sin(al)
    ax.plot([0.4, (toe + L1_vis * eg)[0]], [ws1_y, ws1_y], color="#0284c7", lw=2.0)
    ax.plot([(toe + L2_vis * eg)[0], 6.0], [ws2_y, ws2_y], color="#0284c7", lw=2.0)

    # Gate bar & hinge O at x_vis = 1.08 along gate
    ax.plot([toe[0], top[0]], [toe[1], top[1]], color="#0f172a", lw=4.8, solid_capstyle="round", zorder=5)
    hinge = toe + 1.08 * eg
    ax.scatter([hinge[0]], [hinge[1]], s=95, facecolor="#fef08a", edgecolor="#0f172a", lw=2.0, zorder=7)
    ax.text(hinge[0] + 0.22, hinge[1] + 0.04, r"铰轴 $O$ ($x=0.795\,\mathrm{m}$)", fontsize=9.5, fontweight="bold", color="#0f172a")

    # Left pressure prism & resultant P1 at L1_vis/3 = 0.90
    p1_pt = toe + (L1_vis / 3.0) * eg
    prism1 = [toe, toe + L1_vis * eg, toe - 1.35 * en]
    ax.add_patch(patches.Polygon(prism1, closed=True, facecolor="#fde68a", edgecolor="#d97706", lw=1.4, alpha=0.65))
    ax.annotate("", xy=p1_pt, xytext=p1_pt - 1.15 * en, arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.4), zorder=6)
    ax.text(p1_pt[0] - 1.25, p1_pt[1] + 0.62, r"左侧总压力 $P_1$" + "\n" + r"作用点距底 $L_1/3$", fontsize=9.2, ha="center", color="#b91c1c", fontweight="bold")

    # Right pressure prism & resultant P2 at L2_vis/3 = 0.24
    p2_pt = toe + (L2_vis / 3.0) * eg
    prism2 = [toe, toe + L2_vis * eg, toe + 0.65 * en]
    ax.add_patch(patches.Polygon(prism2, closed=True, facecolor="#bae6fd", edgecolor="#0284c7", lw=1.3, alpha=0.7))
    ax.annotate("", xy=p2_pt, xytext=p2_pt + 0.95 * en, arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.1), zorder=6)
    ax.text(p2_pt[0] + 1.65, 0.80, r"右侧压力 $P_2$（距底 $L_2/3$）", fontsize=9.2, ha="center", color="#0369a1", fontweight="bold")

    ax.text(0.85, 3.35, r"临界开启力矩平衡（对 $O$ 取矩）：" + "\n" + r"$P_1(x - L_1/3) = P_2(x - L_2/3)$",
            fontsize=9.3, color="#0f172a", bbox=dict(boxstyle="round,pad=0.3", fc="#f8fafc", ec="#94a3b8", lw=1.0))

    ax.set_xlim(0.2, 6.3)
    ax.set_ylim(0.15, 3.95)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2011_q08_sol(out_path: Path) -> None:
    """Vertical force equilibrium diagram for 2011 Q8 gasoline float + bottom valve."""
    fig, ax = plt.subplots(figsize=(5.8, 4.6))
    fig.patch.set_facecolor("white")

    ax.plot([0.7, 0.7, 2.25], [3.7, 0.8, 0.8], color="#334155", lw=1.8)
    ax.plot([2.75, 4.3, 4.3], [0.8, 0.8, 3.7], color="#334155", lw=1.8)
    ax.add_patch(patches.Rectangle((0.72, 0.82), 3.56, 2.30, facecolor="#fef3c7", alpha=0.55))
    ax.plot([0.7, 1.9], [3.12, 3.12], color="#d97706", lw=1.8)
    ax.plot([3.1, 4.3], [3.12, 3.12], color="#d97706", lw=1.8)

    # Float & cord & bottom valve
    ax.add_patch(patches.Rectangle((1.9, 2.55), 1.2, 1.15, facecolor="white", edgecolor="#0f172a", lw=2.0, zorder=4))
    ax.add_patch(patches.Rectangle((1.92, 2.57), 1.16, 0.55, facecolor="#fde68a", alpha=0.7, zorder=4))
    ax.plot([2.5, 2.5], [0.87, 2.55], color="#0f172a", lw=2.0, zorder=4)
    ax.add_patch(patches.Rectangle((2.15, 0.80), 0.70, 0.08, facecolor="#334155", edgecolor="#0f172a", lw=1.6, zorder=5))

    # Upward buoyancy Fb
    ax.annotate("", xy=(2.5, 4.55), xytext=(2.5, 3.45), arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.5), zorder=6)
    ax.text(2.60, 4.25, r"浮力 $F_b = \rho g h \cdot \frac{\pi}{4}d_1^2$", fontsize=10, color="#15803d", fontweight="bold")

    # Total self-weight G
    ax.annotate("", xy=(2.10, 1.45), xytext=(2.10, 2.25), arrowprops=dict(arrowstyle="->", color="#ea580c", lw=2.2), zorder=6)
    ax.text(2.00, 1.85, r"总重 $G=0.981\,\mathrm{N}$", fontsize=9.5, ha="right", color="#c2410c", fontweight="bold")

    # Downward hydrostatic force P1 on bottom circular valve
    ax.annotate("", xy=(2.5, 0.10), xytext=(2.5, 0.80), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.4), zorder=6)
    ax.text(2.62, 0.30, r"阀面油压 $P_v = \rho g H \cdot \frac{\pi}{4}d_2^2$", fontsize=9.8, color="#b91c1c", fontweight="bold")

    # Depth H = z + h = 17.40 cm
    ax.annotate("", xy=(3.95, 3.12), xytext=(3.95, 0.80), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.3))
    ax.text(3.85, 1.96, r"$H = z + h$" + "\n" + r"$= 17.40\,\mathrm{cm}$", fontsize=9.2, ha="right", va="center")

    ax.set_xlim(0.35, 5.15)
    ax.set_ylim(-0.05, 4.80)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2011_q09_sol(out_path: Path) -> None:
    """Whole-system control volume diagram for water tank on platform scale (2011 Q9)."""
    fig, ax = plt.subplots(figsize=(6.8, 4.5))
    fig.patch.set_facecolor("white")

    # Tank + water
    ax.plot([1.6, 1.6, 4.6, 4.6], [3.2, 1.1, 1.1, 3.2], color="#0f172a", lw=2.2)
    ax.add_patch(patches.Rectangle((1.62, 1.12), 2.96, 1.55, facecolor="#bae6fd", alpha=0.65))
    ax.plot([1.6, 4.6], [2.67, 2.67], color="#0284c7", lw=2.0)

    # Control volume dashed box enclosing tank + water
    cv_box = patches.Rectangle((1.35, 1.02), 3.45, 2.55, fill=False, edgecolor="#dc2626", ls="--", lw=1.6)
    ax.add_patch(cv_box)
    ax.text(4.88, 3.35, "整体控制体\n（水箱 + 箱内水）", fontsize=9.2, color="#dc2626", fontweight="bold")

    # Vertical inlet jet at top (v1 downward)
    ax.plot([2.98, 2.98], [3.30, 4.05], color="#0f172a", lw=1.8)
    ax.plot([3.22, 3.22], [3.30, 4.05], color="#0f172a", lw=1.8)
    ax.annotate("", xy=(3.10, 2.80), xytext=(3.10, 3.90), arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.3))
    ax.text(3.32, 3.82, r"铅直入流 $v_1 = 30.56\,\mathrm{m/s}$" + "\n" + r"附加动量力 $\rho Q v_1 = 1.83\,\mathrm{kN}$",
            fontsize=9.2, color="#0369a1", va="center")

    # Horizontal outlet jet at left side (v2y = 0)
    ax.plot([1.05, 1.60], [1.45, 1.45], color="#0f172a", lw=1.8)
    ax.plot([1.05, 1.60], [1.25, 1.25], color="#0f172a", lw=1.8)
    ax.annotate("", xy=(0.55, 1.35), xytext=(1.45, 1.35), arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.0))
    ax.text(0.85, 1.68, "水平出流\n" + r"$v_{2y} = 0$", fontsize=9.0, ha="center", color="#0369a1")

    # Gravity (m_tank + m_water)g & Platform upward normal reaction N
    ax.annotate("", xy=(2.25, 1.35), xytext=(2.25, 2.35), arrowprops=dict(arrowstyle="->", color="#ea580c", lw=2.3))
    ax.text(2.38, 1.98, r"总重 $(m_0 + \rho V)g$" + "\n" + r"$= 10.76\,\mathrm{kN}$", fontsize=9.0, ha="left", color="#c2410c", fontweight="bold")

    ax.add_patch(patches.Rectangle((1.85, 0.72), 2.50, 0.30, facecolor="#e2e8f0", edgecolor="#0f172a", lw=1.6))
    ax.annotate("", xy=(3.55, 1.65), xytext=(3.55, 0.58), arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.5))
    ax.text(4.52, 0.62, r"磅秤支反力 $N = 12.59\,\mathrm{kN}$" + "\n" + r"（折合质量读数 $1284.7\,\mathrm{kg}$）",
            fontsize=9.2, color="#15803d", ha="left", va="center", fontweight="bold")

    ax.set_xlim(0.25, 6.75)
    ax.set_ylim(0.25, 4.30)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2011_q10_sol(out_path: Path) -> None:
    """Head balance schematic for 2011 Q10 pump-to-pressurized-tower diameter calculation."""
    fig, ax = plt.subplots(figsize=(7.6, 4.1))
    fig.patch.set_facecolor("white")

    categories = ["地形高差\n" + r"$\Delta z$", "水塔表压头\n" + r"$p_M/(\rho g)$", "管道总损失\n" + r"$h_f + \sum h_j$"]
    vals = [25.00, 15.31, 20.92]
    colors = ["#38bdf8", "#818cf8", "#f87171"]

    left = 0.0
    for cat, v, col in zip(categories, vals, colors):
        ax.barh([0.6], [v], left=left, height=0.42, color=col, edgecolor="#0f172a", lw=1.4)
        ax.text(left + 0.5 * v, 0.6, f"{cat}\n" + rf"${v:.2f}\,\mathrm{{m}}$",
                ha="center", va="center", fontsize=9.5, color="#0f172a", fontweight="bold")
        left += v

    ax.annotate("", xy=(61.22, 1.02), xytext=(0.0, 1.02), arrowprops=dict(arrowstyle="<->", color="#15803d", lw=2.0))
    ax.text(30.6, 1.15, r"水泵总扬程 $H_p = \dfrac{1000\,\eta N}{\rho g Q} = 61.22\,\mathrm{m}$",
            ha="center", va="bottom", fontsize=10.5, color="#15803d", fontweight="bold")

    ax.text(30.6, -0.02, r"由 $h_w = \left(\lambda\dfrac{l}{d} + \sum\zeta\right)\dfrac{8Q^2}{\pi^2 g d^4} = 20.92\,\mathrm{m}$ 迭代解得管径 $d \approx 94.0\,\mathrm{mm}$（即 $0.094\,\mathrm{m}$）",
            ha="center", va="top", fontsize=9.8, color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.32", fc="#f8fafc", ec="#94a3b8", lw=1.1))

    ax.set_xlim(-2.0, 64.0)
    ax.set_ylim(-0.38, 1.50)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# 2010 STEM FIGURES & SOLUTION DIAGRAMS
# ==============================================================================

def build_2010_figures(fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(RAW_DIR / "849-水力学（水）2010.pdf")
    pages = []
    for pno in range(len(doc)):
        pix = doc[pno].get_pixmap(dpi=300)
        pages.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))

    scan_crops = [
        ("q03_orig.png", pages[0], (1420, 1495, 2165, 1915), 28),
        ("q04_orig.png", pages[0], (1540, 2270, 2100, 3005), 28),
        ("q05_orig.png", pages[1], (1540, 520, 2135, 1165), 32),
        ("q06_orig.png", pages[1], (1540, 1330, 2150, 2000), 28),
        ("q07_orig.png", pages[1], (1460, 2160, 2155, 2710), 28),
        ("q08_orig.png", pages[2], (1320, 480, 2030, 1085), 28),
        ("q09_orig.png", pages[2], (1010, 1350, 2065, 1895), 28),
        ("q10_orig.png", pages[2], (980, 2105, 2095, 2575), 28),
    ]
    for fname, im, box, min_b in scan_crops:
        clean_scan_crop(im.crop(box), pad=16, min_blob=min_b).save(fig_dir / fname)

    # Solution figures for 2010
    draw_2010_q02_sol(fig_dir / "q02_sol.png")
    draw_2010_q04_sol(fig_dir / "q04_sol.png")
    draw_2010_q05_sol(fig_dir / "q05_sol.png")
    draw_2010_q06_sol(fig_dir / "q06_sol.png")
    draw_2010_q09_sol(fig_dir / "q09_sol.png")


def draw_2010_q02_sol(out_path: Path) -> None:
    """Discharge-depth curve Q(h) at constant specific energy Es showing Qmax at h = hk."""
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    fig.patch.set_facecolor("white")

    Es = 1.5
    h = np.linspace(0.0, Es, 300)
    Q = h * np.sqrt(np.maximum(0.0, 2.0 * 9.8 * (Es - h)))  # unit rectangular channel
    hk = (2.0 / 3.0) * Es
    Qmax = hk * np.sqrt(2.0 * 9.8 * (Es - hk))

    ax.plot(Q, h, color="#0284c7", lw=2.5)
    ax.plot([0, Qmax], [hk, hk], color="#dc2626", ls="--", lw=1.5)
    ax.plot([Qmax, Qmax], [0, hk], color="#dc2626", ls="--", lw=1.5)
    ax.scatter([Qmax], [hk], color="#dc2626", s=45, zorder=6)

    ax.text(Qmax + 0.12, hk, r"极值点：$h = h_k$，$Q = Q_{\max}$" + "\n" + r"$\dfrac{\mathrm{d}Q}{\mathrm{d}h}=0 \Leftrightarrow \dfrac{\alpha Q^2 B}{g A^3}=1$",
            fontsize=9.5, va="center", color="#b91c1c", fontweight="bold")
    ax.text(1.05, 1.26, "缓流支 ($h > h_k$)", fontsize=9.2, color="#0369a1")
    ax.text(0.62, 0.44, "急流支 ($h < h_k$)", fontsize=9.2, color="#0369a1")
    ax.text(0.12, Es + 0.04, r"$h = E_s$ ($Q=0$)", fontsize=9.2, color="#334155")

    ax.set_xlabel(r"流量 $Q$（给定 $E_s = \mathrm{const}$）", fontsize=10.5)
    ax.set_ylabel(r"水深 $h$", fontsize=10.5)
    ax.set_xlim(0.0, Qmax * 1.68)
    ax.set_ylim(0.0, Es * 1.15)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2010_q04_sol(out_path: Path) -> None:
    """Two-reservoir U-tube differential manometer displacement schematic for 2010 Q4."""
    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    fig.patch.set_facecolor("white")

    # Left & right wide cylinders (A=50a) + narrow U-tube (a)
    # Left wide: x in [1.0, 2.2], y in [2.7, 3.9]; narrow left: x in [1.52, 1.68], y in [0.9, 2.7]
    # Right wide: x in [3.8, 5.0], y in [2.7, 3.9]; narrow right: x in [4.32, 4.48], y in [0.9, 2.7]
    ax.plot([1.0, 1.0, 1.52, 1.52], [3.9, 2.7, 2.7, 0.9], color="#0f172a", lw=1.8)
    ax.plot([2.2, 2.2, 1.68, 1.68], [3.9, 2.7, 2.7, 0.9], color="#0f172a", lw=1.8)
    ax.plot([3.8, 3.8, 4.32, 4.32], [3.9, 2.7, 2.7, 0.9], color="#0f172a", lw=1.8)
    ax.plot([5.0, 5.0, 4.48, 4.48], [3.9, 2.7, 2.7, 0.9], color="#0f172a", lw=1.8)

    th = np.linspace(np.pi, 2 * np.pi, 80)
    xo, yo = 3.0 + 1.48 * np.cos(th), 0.9 + 0.65 * np.sin(th)
    xi, yi = 3.0 + 1.32 * np.cos(th[::-1]), 0.9 + 0.49 * np.sin(th[::-1])
    ax.add_patch(patches.Polygon(list(zip(xo, yo)) + list(zip(xi, yi)), closed=True, facecolor="#bae6fd", edgecolor="none", alpha=0.65))
    ax.plot(xo, yo, color="#0f172a", lw=1.8)
    ax.plot(xi, yi, color="#0f172a", lw=1.8)

    # Water (blue) and oil (amber) after p2 > p1:
    # Initial interface x-x at y=2.05; new interface 1-1 at y=1.35 (dropped by h = 0.25 m)
    ax.add_patch(patches.Rectangle((1.02, 2.72), 1.16, 0.62, facecolor="#bae6fd", alpha=0.65))
    ax.add_patch(patches.Rectangle((1.53, 0.90), 0.14, 1.82, facecolor="#bae6fd", alpha=0.65))
    ax.add_patch(patches.Rectangle((4.33, 0.90), 0.14, 0.45, facecolor="#bae6fd", alpha=0.65))
    # Oil in right side from y=1.35 up to y=3.38
    ax.add_patch(patches.Rectangle((4.33, 1.35), 0.14, 1.37, facecolor="#fde68a", alpha=0.85))
    ax.add_patch(patches.Rectangle((3.82, 2.72), 1.16, 0.66, facecolor="#fde68a", alpha=0.85))

    # Initial & new levels
    ax.plot([0.75, 5.35], [2.05, 2.05], color="#64748b", ls="-.", lw=1.3)
    ax.text(0.70, 2.05, r"初始 $x$—$x$", fontsize=9.0, ha="right", va="center", color="#475569")

    ax.plot([1.25, 5.35], [1.35, 1.35], color="#dc2626", ls="--", lw=1.5)
    ax.text(5.40, 1.35, "新等压面 1—1", fontsize=9.0, va="center", color="#dc2626", fontweight="bold")

    ax.annotate("", xy=(4.75, 2.05), xytext=(4.75, 1.35), arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.6))
    ax.text(4.85, 1.70, r"下降 $\Delta h = 0.25\,\mathrm{m}$", fontsize=9.5, va="center", color="#b91c1c", fontweight="bold")

    # Wide cylinder level shifts +Delta h/50 and -Delta h/50
    ax.plot([1.0, 2.2], [3.22, 3.22], color="#64748b", ls=":", lw=1.2)
    ax.plot([1.0, 2.2], [3.34, 3.34], color="#0284c7", lw=1.8)
    ax.text(0.92, 3.28, r"上升 $\frac{\Delta h}{50}$", fontsize=8.8, ha="right", va="center", color="#0369a1")

    ax.plot([3.8, 5.0], [3.50, 3.50], color="#64748b", ls=":", lw=1.2)
    ax.plot([3.8, 5.0], [3.38, 3.38], color="#d97706", lw=1.8)
    ax.text(5.08, 3.44, r"下降 $\frac{\Delta h}{50}$", fontsize=8.8, va="center", color="#b45309")

    ax.annotate("", xy=(1.6, 3.40), xytext=(1.6, 3.92), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.6))
    ax.text(1.6, 3.98, r"$p_1$", fontsize=11, ha="center")
    ax.annotate("", xy=(4.4, 3.44), xytext=(4.4, 3.92), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.6))
    ax.text(4.4, 3.98, r"$p_2$", fontsize=11, ha="center")

    ax.set_xlim(-0.15, 6.45)
    ax.set_ylim(0.15, 4.25)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2010_q05_sol(out_path: Path) -> None:
    """Annular virtual pressure body above conical wall ABCD (2010 Q5)."""
    fig, ax = plt.subplots(figsize=(6.4, 4.5))
    fig.patch.set_facecolor("white")

    # Center x=0; r1=1 -> [-1, 1], r2=3 -> [-3, 3]; y_top=6 (free surface), y_AC=3, y_BD=2, y_bot=0
    # Virtual pressure body polygons on left [-3..-1] and right [1..3] from ABCD up to y=6!
    vp_left = [[-3, 2], [-1, 3], [-1, 6], [-3, 6]]
    vp_right = [[1, 3], [3, 2], [3, 6], [1, 6]]
    ax.add_patch(patches.Polygon(vp_left, closed=True, facecolor="#fde68a", edgecolor="#d97706", lw=1.5, hatch="///", alpha=0.7))
    ax.add_patch(patches.Polygon(vp_right, closed=True, facecolor="#fde68a", edgecolor="#d97706", lw=1.5, hatch="///", alpha=0.7))

    # Water inside container
    water_poly = [[-1, 6], [1, 6], [1, 3], [3, 2], [3, 0], [-3, 0], [-3, 2], [-1, 3]]
    ax.add_patch(patches.Polygon(water_poly, closed=True, facecolor="#bae6fd", edgecolor="#0f172a", lw=2.0, alpha=0.65))
    ax.plot([-3.4, 3.4], [6, 6], color="#0284c7", ls="--", lw=1.5)
    ax.text(0.0, 6.18, "自由液面（虚压力体上顶面）", fontsize=9.5, ha="center", color="#0369a1", fontweight="bold")

    # Upward vertical force arrows on AB and CD
    for xx in [-2.0, 2.0]:
        ax.annotate("", xy=(xx, 5.1), xytext=(xx, 3.2), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.4))

    ax.text(-1.05, 2.70, r"$A$", fontsize=11, fontweight="bold")
    ax.text(-3.32, 1.95, r"$B$", fontsize=11, fontweight="bold")
    ax.text(0.82, 2.70, r"$C$", fontsize=11, fontweight="bold")
    ax.text(3.12, 1.95, r"$D$", fontsize=11, fontweight="bold")

    ax.text(0.0, 1.05, "环形虚压力体体积：\n" + r"$V_z = \frac{86}{3}\pi \approx 90.06\,\mathrm{m^3}$" + "\n"
            + r"$P_z = 882.58\,\mathrm{kN}$（竖直向上）",
            fontsize=9.5, ha="center", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.32", fc="white", ec="#dc2626", lw=1.2))

    ax.set_xlim(-3.9, 3.9)
    ax.set_ylim(-0.3, 6.75)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2010_q06_sol(out_path: Path) -> None:
    """Moment equilibrium diagram for 2010 Q6 L-shaped automatic spill valve."""
    fig, ax = plt.subplots(figsize=(6.6, 4.5))
    fig.patch.set_facecolor("white")

    # Corner hinge O at (2.8, 1.5); vertical leg up to (2.8, 4.1); horizontal leg right to (4.8, 1.5)
    ax.plot([0.5, 2.8], [3.7, 3.7], color="#0284c7", lw=2.0)
    ax.text(1.4, 3.82, "上游临界水位", fontsize=9.5, ha="center", color="#0369a1", fontweight="bold")

    # L-gate
    ax.plot([2.8, 2.8], [1.5, 4.05], color="#0f172a", lw=4.5)
    ax.plot([2.8, 4.8], [1.5, 1.5], color="#0f172a", lw=4.5)
    ax.scatter([2.8], [1.5], s=85, facecolor="#fef08a", edgecolor="#0f172a", lw=2.0, zorder=7)
    ax.text(2.65, 1.25, r"铰 $O$", fontsize=10, ha="right", fontweight="bold")

    # Spillway crest arc of radius L=2.0 centered at (2.8, 1.5) from 0 deg to -90 deg
    th = np.linspace(-0.5 * np.pi, 0.0, 60)
    ax.plot(2.8 + 2.0 * np.cos(th), 1.5 + 2.0 * np.sin(th), color="#475569", lw=1.8)

    # Triangular horizontal pressure load Fx on vertical leg (y in [1.5, 3.7], arm h/3 = 0.73 above O)
    ax.add_patch(patches.Polygon([[2.8, 3.7], [2.8, 1.5], [1.35, 1.5]], closed=True,
                                 facecolor="#fde68a", edgecolor="#d97706", lw=1.4, alpha=0.65))
    y_fx = 1.5 + (3.7 - 1.5) / 3.0
    ax.annotate("", xy=(2.76, y_fx), xytext=(1.45, y_fx), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.4))
    ax.text(1.38, y_fx + 0.25, r"$F_x = \frac{1}{2}\rho g h^2 b$" + "\n" + r"（力臂 $h/3$）",
            fontsize=9.3, ha="center", color="#b91c1c", fontweight="bold")

    # Rectangular vertical upward pressure load Fz on horizontal leg (x in [2.8, 4.8], arm L/2 at x=3.8)
    ax.add_patch(patches.Rectangle((2.8, 0.88), 2.0, 0.60, facecolor="#bae6fd", edgecolor="#0284c7", lw=1.4, alpha=0.7))
    ax.annotate("", xy=(3.8, 1.48), xytext=(3.8, 0.52), arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.4))
    ax.text(3.92, 0.58, r"$F_z = \rho g h L b$" + "\n" + r"（力臂 $L/2$）",
            fontsize=9.3, va="center", color="#0369a1", fontweight="bold")

    ax.text(4.35, 3.25, "对铰轴 $O$ 力矩平衡：\n" + r"$F_x \cdot \frac{h}{3} = F_z \cdot \frac{L}{2}$" + "\n" + r"$\Rightarrow h = \sqrt{3}\,L$",
            fontsize=9.5, ha="center", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.32", fc="#f8fafc", ec="#94a3b8", lw=1.1))

    ax.set_xlim(0.3, 5.75)
    ax.set_ylim(-0.65, 4.30)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2010_q09_sol(out_path: Path) -> None:
    """Two-reservoir pipe E.G.L. & H.G.L. diagram showing midpoint piezometer head H = 1.00 m."""
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    fig.patch.set_facecolor("white")

    # Upstream tank (x in [0.4, 1.8], water level y=3.50); Downstream tank (x in [6.6, 8.0], water level y=1.40 -> Z = 3.5 m scaled by 0.6)
    sc = 0.60  # 1 m head = 0.60 plot units; downstream water surface z=0 -> y0 = 1.40; upstream Z=3.5m -> y = 1.40 + 2.10 = 3.50
    y_dn = 1.40
    y_up = y_dn + 3.5 * sc  # 3.50

    ax.add_patch(patches.Rectangle((0.4, 0.4), 1.4, 3.10, facecolor="#bae6fd", alpha=0.55))
    ax.plot([0.4, 1.8], [y_up, y_up], color="#0284c7", lw=2.0)
    ax.plot([1.8, 1.8], [0.85, 3.75], color="#0f172a", lw=2.0)
    ax.plot([1.8, 1.8], [0.4, 0.65], color="#0f172a", lw=2.0)

    ax.add_patch(patches.Rectangle((6.6, 0.4), 1.4, 1.00, facecolor="#bae6fd", alpha=0.55))
    ax.plot([6.6, 8.0], [y_dn, y_dn], color="#0284c7", lw=2.0)
    ax.plot([6.6, 6.6], [0.85, 2.10], color="#0f172a", lw=2.0)
    ax.plot([6.6, 6.6], [0.4, 0.65], color="#0f172a", lw=2.0)

    # Pipe x in [1.8, 6.6], y in [0.65, 0.85]; midpoint piezometer at x = 4.2
    ax.add_patch(patches.Rectangle((1.8, 0.65), 4.8, 0.20, facecolor="#e0f2fe", edgecolor="none"))
    ax.plot([1.8, 6.6], [0.85, 0.85], color="#0f172a", lw=1.8)
    ax.plot([1.8, 6.6], [0.65, 0.65], color="#0f172a", lw=1.8)

    px = 4.2
    y_H = y_dn + 1.0 * sc  # H = 1.00 m -> y = 2.00
    ax.plot([px - 0.06, px - 0.06], [0.85, 2.45], color="#0f172a", lw=1.5)
    ax.plot([px + 0.06, px + 0.06], [0.85, 2.45], color="#0f172a", lw=1.5)
    ax.add_patch(patches.Rectangle((px - 0.05, 0.85), 0.10, y_H - 0.85, facecolor="#38bdf8", alpha=0.8))

    # E.G.L. (red): drops at entrance by 0.5 m (to 3.0 m -> y=3.20), slopes linearly to 2.0 m at midpoint (y=2.60) and 1.0 m at exit (y=2.00), then drops by 1.0 m at exit to y_dn=1.40!
    ax.plot([1.8, 1.8], [y_up, y_dn + 3.0 * sc], color="#dc2626", lw=2.0)
    ax.plot([1.8, 6.6], [y_dn + 3.0 * sc, y_dn + 1.0 * sc], color="#dc2626", lw=2.0, label="总水头线 (E.G.L.)")
    ax.plot([6.6, 6.6], [y_dn + 1.0 * sc, y_dn], color="#dc2626", lw=2.0)

    # H.G.L. (blue dashed): exactly 1.0 m below E.G.L., so starts at 2.0 m (y=2.60), passes through 1.0 m at midpoint (y=2.00 = y_H!), and meets downstream surface 0.0 m (y_dn=1.40) smoothly!
    ax.plot([1.8, 6.6], [y_dn + 2.0 * sc, y_dn], color="#0284c7", ls="--", lw=2.0, label="测压管水头线 (H.G.L.)")

    # Dimension H = 1.00 m above downstream surface (shifted cleanly below dashed H.G.L.)
    ax.plot([4.26, 6.6], [y_dn, y_dn], color="#64748b", ls=":", lw=1.2)
    ax.annotate("", xy=(4.42, y_H), xytext=(4.42, y_dn), arrowprops=dict(arrowstyle="<->", color="#0369a1", lw=1.6))
    ax.text(4.52, y_dn + 0.22, r"$H = 1.00\,\mathrm{m}$", fontsize=10, va="center", color="#0369a1", fontweight="bold")

    # Dimension Z = 3.5 m
    ax.plot([1.8, 7.35], [y_up, y_up], color="#64748b", ls=":", lw=1.1)
    ax.annotate("", xy=(7.25, y_up), xytext=(7.25, y_dn), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.4))
    ax.text(7.35, 0.5 * (y_up + y_dn), r"$Z = 3.5\,\mathrm{m}$", fontsize=10, va="center")

    ax.legend(loc="upper right", bbox_to_anchor=(0.82, 0.98), frameon=True, fontsize=9)
    ax.set_xlim(0.2, 8.25)
    ax.set_ylim(0.25, 3.95)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# 2011 EXAM DATA (12 questions, totalScore = 150)
# ==============================================================================

def build_2011_paper() -> dict:
    return {
        "year": 2011,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "全卷共 12 道大题：第 1～5 题为机理分析与简答题（8 + 10 + 10 + 8 + 10 = 46 分），第 6～12 题为综合计算与公式推导题（15×4 + 20×1 + 12×2 = 104 分）。",
            "除特别说明外，计算统一取重力加速度 $g = 9.80\\,\\mathrm{m/s^2}$，水的密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$（解析同步附 $g = 9.81\\,\\mathrm{m/s^2}$ 对照结果）。"
        ],
        "sections": [
            {
                "id": "short",
                "title": "一、机理分析与简答题",
                "description": "第 1～5 题（8 + 10 + 10 + 8 + 10 分），共 46 分。",
                "range": [1, 5],
                "totalScore": 46
            },
            {
                "id": "calc",
                "title": "二、计算与推导题",
                "description": "第 6～12 题（15×4 + 20×1 + 12×2 分），共 104 分。",
                "range": [6, 12],
                "totalScore": 104
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2011-01",
                "year": 2011,
                "no": 1,
                "type": "short",
                "score": 8,
                "title": "静水奇象：异形等底等水深容器底面静水总压力大小比较",
                "stem": "设有四个容器，容器的形状不同，底面积都相同，均为 $A$，容器中液体的高度均为 $h$，如图所示。试比较四个容器底面所受到的总压力大小。",
                "note": "",
                "figures": [
                    {"src": "figures/q01_orig.png", "caption": "题 1 图　四种不同形状等底面积等液深容器"}
                ],
                "shortAnswer": "四个容器底面所受到的静水总压力大小完全相等，均等于 P = ρghA。因为水平池底各点相对压强均为 p = ρgh，总压力仅取决于液体重度 ρg、自由液面至底面的水深 h 及底面积 A，而与容器侧壁形状和盛液总重量无关。",
                "judgeAnswer": None,
                "answer": "**结论**：四个容器 `a)`、`b)`、`c)`、`d)` 底面所受到的液体静水总压力**大小完全相等**，均为：\n\n$$\nP_a = P_b = P_c = P_d = \\rho g h A\n$$\n\n**理由**：\n1. 四个容器均盛装同种连通静止液体，液面均通大气（表压为零），根据水静力学基本方程，各容器水平底面上任意一点的静水相对压强均为 $p = \\rho g h$；\n2. 水平平面上的静水总压力等于底面压强与底面积的乘积：$P = p A = \\rho g h A$。由于四容器液体密度 $\\rho$、液面高度 $h$ 和底面积 $A$ 均相同，故底面所受静水总压力必然完全相同，而与容器侧壁的几何形状及容器内盛液总重量无关（此即著名的帕斯卡“静水奇象”）。",
                "analysis": "**从竖向整体平衡进一步阐明“底面压力为何不等于液体总重量”**\n\n- 图 `a)` 直立柱形容器：侧壁铅直，壁面无竖向反力，故底面总压力 $P_a = G_a = \\rho g h A$ 恰好等于水重；\n- 图 `b)` 口大底小容器：倾斜侧壁对水体有竖直向上的支撑分力，分担了外扩部分的水重，故 $P_b = \\rho g h A < G_b$；\n- 图 `c)` 口小底大及图 `d)` 弯曲细颈容器：内倾侧壁对水体施加**竖直向下**的附加壁面压力，该向下反力与水重叠加后恰好使底面总压力仍维持 $P_c = P_d = \\rho g h A > G_{c,d}$。",
                "analysisFigures": [],
                "pitfalls": "切忌受日常固体称重直觉误导而写成 $P_b > P_a > P_c > P_d$！流体与固体的本质区别在于静水压强各向同性传递且受倾斜器壁竖向反力调节，底面静水总压力只认 $\\rho g h A$，绝不等于液体总重力 $G$。",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力", "静水压强基本方程", "帕斯卡静水奇象"],
                "method": "水静力学基本方程与器壁竖向反力辨析法",
                "difficulty": 1,
                "rubric": [
                    {"label": "明确得出四个容器底面所受静水总压力大小完全相等的结论", "pts": 3},
                    {"label": "写出水平底面压强 p = ρgh 与总压力公式 P = ρghA，阐明其仅与 ρ、h、A 有关而与容器形状无关", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2011-02",
                "year": 2011,
                "no": 2,
                "type": "short",
                "score": 10,
                "title": "从受力平衡角度解释明渠均匀流只能在顺坡渠道中形成的原因",
                "stem": "试从受力角度解释为什么说只有在顺坡渠道中有可能形成均匀流，在平坡和逆坡渠道中不可能形成均匀流？",
                "note": "",
                "figures": [],
                "shortAnswer": "沿流向取长 L 的均匀流水体隔离体，因水深与流速沿程不变，上下游断面静水压力相等抵消（P1=P2）且流向加速度为零，故沿流向合力平衡必有水体重力流向分力与边界摩阻力平衡：G·sinθ - Ff = 0。实际黏性水流运动必受逆流向摩阻力 Ff > 0，故必须有 G·sinθ = Ff > 0（即 sinθ = i > 0 顺坡）；平坡（i=0）无重力分力，逆坡（i<0）重力分力与摩阻力同向阻流，均无法平衡。",
                "judgeAnswer": None,
                "answer": "**从流段水体沿流向受力平衡证明（受力图见解图 2）**：\n\n设想在产生恒定均匀流的明渠中截取一段长度为 $L$ 的水体控制段，设渠底与水平面夹角为 $\\theta$（渠底坡度 $i = \\sin\\theta$），沿水流方向（平行于渠底向下游）对隔离体作受力分析：\n1. **上下游过水断面动水总压力 $P_1$、$P_2$**：均匀流水深沿程不变（$h_1 = h_2 = h_0$），断面服从静水压强分布，故上下游断面动水总压力大小严格相等、方向相反，彼此完全抵消（$P_1 - P_2 = 0$）；\n2. **边界摩擦阻力 $F_f$**：实际液体具有黏滞性，水流运动时渠底与渠壁必然对水体施加**逆水流方向**的摩擦阻力 $F_f = \\tau_0 \\chi L > 0$；\n3. **水体重力沿流向分力 $G_s$**：流段水体自重 $G = \\rho g A L$ 在流向上的投影分力为 $G_s = G\\sin\\theta = \\rho g A L i$。\n\n因均匀流断面平均流速沿程不变（流向加速度为零，动量通量差 $\\rho Q(v_2 - v_1) = 0$），沿流向合力必须为零：\n\n$$\nP_1 - P_2 + G\\sin\\theta - F_f = 0 \\implies G\\sin\\theta = F_f\n$$\n\n**分底坡类型讨论**：\n- **顺坡渠道（$i = \\sin\\theta > 0$）**：重力沿流向分力 $G\\sin\\theta > 0$ 指向下游（推进力），与逆流向的边界摩阻力 $F_f > 0$ 方向相反，当水深调整至正常水深 $h_0$ 使 $G\\sin\\theta = F_f$ 时，水体达到受力平衡，可以形成均匀流；\n- **平坡渠道（$i = 0$）**：$G\\sin\\theta = 0$，而水流运动必有向后的摩阻力 $F_f > 0$，流向合力为 $-F_f < 0$，无法平衡，不可能形成均匀流；\n- **逆坡渠道（$i < 0$）**：重力沿流向分力指向**上游**（阻滞力），与摩阻力 $F_f$ 同向阻碍流动，合力恒逆流向而不为零，更不可能形成均匀流。",
                "analysis": "**由力学平衡直接导出谢才公式（深化理解）**\n\n将 $G\\sin\\theta = \\rho g A L i$ 与壁面阻力 $F_f = \\tau_0 \\chi L$ 代入平衡式 $G\\sin\\theta = F_f$，立得明渠均匀流基本方程：\n\n$$\n\\tau_0 = \\rho g \\frac{A}{\\chi} i = \\rho g R i\n$$\n\n这正是谢才公式 $v = C\\sqrt{R i}$ 的力学根基：根号内的底坡 $i$ 必须严格为正（$i > 0$）方有实数均匀流流速解。",
                "analysisFigures": [
                    {"src": "figures/q02_sol.png", "caption": "解图 2　顺坡明渠均匀流隔离体沿流向四力平衡关系图"}
                ],
                "pitfalls": "注意审题！本题明确限定“**试从受力角度解释**”（区别于另一高频问法“试用能量方程解释”），因此必须取长度为 $L$ 的水体隔离体，列出沿流向的四力平衡方程 $P_1 - P_2 + G\\sin\\theta - F_f = 0$，切忌只写伯努利能量方程而漏掉受力分解！",
                "chapter": 7,
                "kps": ["明渠均匀流形成条件", "明渠均匀流特点", "重力分力与摩阻力平衡"],
                "method": "明渠隔离体沿流向重力与摩阻力平衡法",
                "difficulty": 2,
                "rubric": [
                    {"label": "取明渠流段隔离体，正确分析上下游静水压力抵消（P1 = P2）、重力分力 G·sinθ 与边界摩阻力 Ff", "pts": 4},
                    {"label": "由均匀流等速无加速度列出沿流向受力平衡方程 G·sinθ = Ff > 0", "pts": 3},
                    {"label": "分别对比顺坡（i>0 可平衡）、平坡（i=0 合力为 -Ff≠0）与逆坡（i<0 两阻力叠加≠0）得出结论", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2011-03",
                "year": 2011,
                "no": 3,
                "type": "short",
                "score": 10,
                "title": "应用能量方程解释河中航行船只被迫向急流侧河岸靠拢现象",
                "stem": "试用能量方程式分析解释现象：在河里行走的船只，总是被迫向水流较急的一侧河岸靠拢。",
                "note": "",
                "figures": [],
                "shortAnswer": "船只两侧同处于自由水面附近同一高程（z1 = z2），由伯努利能量方程 z + p/(ρg) + v²/(2g) = C 可知，同一总能水平下流速大处动水压强小。靠近水流较急一侧的船舷相对水流速度 v_急 大于缓流侧 v_缓，故急流侧船舷所受水压强 p_急 小于缓流侧 p_缓，两侧横向压强差合力指向急流侧，迫使船只向水流较急的一侧河岸靠拢。",
                "judgeAnswer": None,
                "answer": "**机理解释**：\n1. 取随船平动的参考系（或考察同一水平水深 $z_1 = z_2$ 处绕流船体左右两舷的水流），忽略局部短距离能量损失，应用理想不可压缩液体伯努利能量方程式：\n\n$$\nz + \\frac{p}{\\rho g} + \\frac{v^2}{2g} = C \\implies p + \\frac{1}{2}\\rho v^2 = \\text{const}\n$$\n\n2. 在天然河道（如弯道凹岸侧或主槽偏岸侧）中，横断面流速分布不对称：靠近水流较急一侧河岸的船舷外侧水流相对船体流速 $v_{\\text{急}}$ 较大，单位重量动能 $\\frac{v_{\\text{急}}^2}{2g}$ 较大；而另一侧（缓流侧）船舷外侧相对流速 $v_{\\text{缓}}$ 较小，单位重量动能 $\\frac{v_{\\text{缓}}^2}{2g}$ 较小（$v_{\\text{急}} > v_{\\text{缓}}$）；\n3. 代入同高程伯努利方程可知，流速大的一侧动水压强小，流速小的一侧动水压强大：\n\n$$\np_{\\text{急}} - p_{\\text{缓}} = \\frac{1}{2}\\rho \\left(v_{\\text{缓}}^2 - v_{\\text{急}}^2\\right) < 0 \\implies p_{\\text{急}} < p_{\\text{缓}}\n$$\n\n4. 船体左右两侧浸水船壳上产生由高压区（缓流侧）指向低压区（急流侧）的横向动水总压力差 $\\Delta F = \\int_A (p_{\\text{缓}} - p_{\\text{急}})\\,\\mathrm{d}A > 0$，在该横向推力持续作用下，船只总是被迫向水流较急的一侧河岸偏移靠拢。",
                "analysis": "**工程航运延伸**：\n不仅偏岸急流会产生“岸吸 / 急流吸船”现象，当船只过于贴近陡直河岸航行时，船岸之间过水断面变窄，由连续性方程 $q = v A$ 知船岸狭窄水道内水流进一步加速（$v_{\\text{岸侧}} > v_{\\text{河心侧}}$），同样产生将船吸向岸壁的横向负压差（“岸吸效应”），故内河航行规程严禁船只贴近急流陡岸过近行驶。",
                "analysisFigures": [],
                "pitfalls": "务必先写出完整的伯努利能量方程式 $z + \\frac{p}{\\rho g} + \\frac{v^2}{2g} = C$，指明左右船舷处于同一高程 $z$，再由 $v_{\\text{急}} > v_{\\text{缓}}$ 推出 $p_{\\text{急}} < p_{\\text{缓}}$ 及横向压差合力方向，切勿漏列方程。",
                "chapter": 3,
                "kps": ["伯努利方程物理意义", "流速与动压强转换关系"],
                "method": "伯努利方程动能压能转化分析法",
                "difficulty": 1,
                "rubric": [
                    {"label": "正确列出伯努利能量方程式 z + p/(ρg) + v²/(2g) = C", "pts": 4},
                    {"label": "对比船体两侧同高程处水流速度 v急 > v缓，推导出急流侧动水压强小于缓流侧（p急 < p缓）", "pts": 4},
                    {"label": "指出船体受由缓流高压侧指向急流低压侧的横向压差合力，故被迫向急流侧靠拢", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2011-04",
                "year": 2011,
                "no": 4,
                "type": "short",
                "score": 8,
                "title": "恒定流量与恒温条件下有压圆管雷诺数随管径增大的变化规律",
                "stem": "压力输水管道中，当通过的流量 $Q$ 一定，水的温度不变，随管道直径的增大，雷诺数 $Re$ 是增大还是减小？为什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "雷诺数 Re 减小。因为水温不变则运动黏度 ν 不变，将 v = 4Q/(πd²) 代入 Re = vd/ν 得 Re = 4Q/(πdν)；当 Q、ν 一定时，Re 与管径 d 成反比，故随管径 d 增大，流速以 d⁻² 急剧减小，导致 Re 减小。",
                "judgeAnswer": None,
                "answer": "**结论**：随管道直径 $d$ 的增大，雷诺数 **$Re$ 减小**。\n\n**原因**：\n1. 有压满流圆管的雷诺数定义为 $Re = \\frac{v d}{\\nu}$，而断面平均流速与体积流量 $Q$ 的连续性关系为 $v = \\frac{Q}{A} = \\frac{4 Q}{\\pi d^2}$；\n2. 将流速表达式代入雷诺数定义式消去 $v$，得到以流量 $Q$ 和管径 $d$ 表示的雷诺数公式：\n\n$$\nRe = \\frac{v d}{\\nu} = \\frac{\\frac{4Q}{\\pi d^2} \\cdot d}{\\nu} = \\frac{4 Q}{\\pi \\nu d}\n$$\n\n3. 因水的温度保持不变，水的运动黏度 $\\nu$ 为常数；通过的流量 $Q$ 又保持一定，故 $\\frac{4Q}{\\pi\\nu}$ 为定值，雷诺数 **$Re$ 与管径 $d$ 成反比**（$Re \\propto d^{-1}$）。因此，随管道直径 $d$ 的增大，雷诺数 $Re$ 单调减小。",
                "analysis": "**易错直觉剖析**：\n初学者若只孤立看定义式 $Re = \\frac{v d}{\\nu}$ 分子上的 $d$，极易误以为“$d$ 增大则 $Re$ 增大”，却忽略了在 **$Q = \\text{const}$ 约束下 $v$ 并非不变量**！当管径扩大为原来的 $2$ 倍时，断面积扩大为 $4$ 倍，流速骤降为原来的 $\\frac{1}{4}$，乘积 $v d$ 净减小为原来的 $\\frac{1}{2}$。",
                "analysisFigures": [],
                "pitfalls": "切忌脱离“流量 $Q$ 一定”的前提条件把断面平均流速 $v$ 当作常数！必须把 $v = \\frac{4Q}{\\pi d^2}$ 代入 $Re = \\frac{vd}{\\nu}$ 化简出 $Re = \\frac{4Q}{\\pi\\nu d}$ 后再下结论。",
                "chapter": 4,
                "kps": ["雷诺数与流态判别", "恒定总流连续性方程"],
                "method": "连续性方程消去流速导出流量型雷诺数法",
                "difficulty": 1,
                "rubric": [
                    {"label": "明确回答随管径 d 增大，雷诺数 Re 减小", "pts": 2},
                    {"label": "联立 Re = vd/ν 与 v = 4Q/(πd²) 正确推导出 Re = 4Q/(πνd)", "pts": 4},
                    {"label": "结合水温不变则运动黏度 ν 不变、流量 Q 一定，说明 Re 与管径 d 成反比", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2011-05",
                "year": 2011,
                "no": 5,
                "type": "short",
                "score": 10,
                "title": "管道突然扩大段总水头线先陡后缓与测压管水头线逐渐升高的机理解释",
                "stem": "如图所示为一突然扩大的管道，图中绘出了总水头线和测压管水头线。试解释管径突然扩大后，为什么总水头线变成先陡后缓的曲线，测压管水头线逐渐升高？",
                "note": "",
                "figures": [
                    {"src": "figures/q05_orig.png", "caption": "题 5 图　管道突然扩大段流束扩散、旋涡区与水头线变化"}
                ],
                "shortAnswer": "（1）总水头线先陡后缓：管径突扩后主流与壁面分离，在拐角环形区形成剧烈回流旋涡与强剪切混掺，单位长度局部能量耗散极大故水头线急剧陡降；下游流束重新贴壁充满大管后旋涡消失，仅剩大管中很小的沿程损失（v2 小、d2 大，J2 很小），故水头线转趋平缓。（2）测压管水头线逐渐升高：水平扩散段内主流流速由 v1 逐渐减速至 v2，动能减少量 (α1v1² - α2v2²)/(2g) 大于包达突扩局部水头损失 (v1 - v2)²/(2g)，净余动能转化为压能使动水压强沿程恢复升高。",
                "judgeAnswer": None,
                "answer": "**（1）总水头线变成“先陡后缓”曲线的原因**：\n- 总水头线的坡度 $J = -\\frac{\\mathrm{d}E}{\\mathrm{d}s}$ 代表单位流长上的水头损失率。\n- **先陡**：水流由细管（流速 $v_1$）突然进入粗管时，由于流体惯性，高速主流不能立即折转贴附大管壁面，发生强烈的**边界层分离**，在突扩台阶拐角环形空间激起剧烈翻滚的**旋涡回流区**。主流与旋涡区交界面上速度梯度极大、湍流混掺与碰撞耗能极为剧烈，产生很大的局部水头损失 $h_j = \\frac{(v_1 - v_2)^2}{2g}$，单位长度机械能迅速衰减，故总水头线在突扩初期**急剧陡降**；\n- **后缓**：随着主流沿程逐渐扩散并最终重新附着充满整个粗管断面，分离旋涡区逐渐消亡，剧烈的局部耗能过程结束，此后仅剩下粗管内的正常沿程摩阻损失。因粗管直径 $d_2 > d_1$ 且流速 $v_2 \\ll v_1$，沿程水力坡度 $J_2 = \\lambda_2\\frac{v_2^2}{2g d_2}$ 极小，故总水头线逐渐过渡为**坡度很缓的直线**。\n\n**（2）测压管水头线“逐渐升高”的原因**：\n- 对水平突扩前断面 $1$ 与扩散恢复后断面 $2$（$z_1 = z_2$）列恒定总流能量方程（取 $\\alpha_1 \\approx \\alpha_2 \\approx 1$）：\n\n$$\n\\frac{p_2}{\\rho g} - \\frac{p_1}{\\rho g} = \\frac{v_1^2 - v_2^2}{2g} - h_j\n$$\n\n- 代入突扩包达（Borda-Carnot）局部损失公式 $h_j = \\frac{(v_1 - v_2)^2}{2g}$（忽略极短扩散段沿程损失），化简得：\n\n$$\n\\frac{p_2}{\\rho g} - \\frac{p_1}{\\rho g} = \\frac{v_1^2 - v_2^2 - (v_1^2 - 2v_1 v_2 + v_2^2)}{2g} = \\frac{v_2(v_1 - v_2)}{g} > 0\n$$\n\n- 上式定量表明：在主流扩散减速过程中，**流速水头的减小量大于旋涡消耗的局部水头损失**，多余的一部分动能逐步转化为压强势能（即扩压恢复效应），因此测压管水头 $z + \\frac{p}{\\rho g}$ 在主流扩散段内**沿程逐渐升高**（直至流束完全充满大管后才按微小沿程坡度 $J_2$ 缓慢下降）。",
                "analysis": "**细节补充：为何题 5 图中突扩刚出口处测压管水头线有一小段微降凹坑？**\n仔细观察题 5 图可见，刚过突扩台阶断面处测压管水头线先略微下凹再明显爬升——这是因为自由射流核心刚冲出细管口时尚受周围卷吸旋涡影响略微收缩加速，随后在主流扩散减速段压强才显著回升并超过进口压强 $p_1$。",
                "analysisFigures": [],
                "pitfalls": "解释“测压管水头线升高”时，切忌只笼统说“流速减小所以压强增大”而漏掉与局部损失 $h_j$ 的大小比较！在实际黏性流体中，只有当**动能减小量大于该段水头损失**（$\\frac{v_1^2 - v_2^2}{2g} > h_j$，差值为 $\\frac{v_2(v_1-v_2)}{g} > 0$）时，测压管水头才会真正净升高。",
                "chapter": 4,
                "kps": ["沿程与局部损失", "边界层分离", "包达突然扩大公式", "总水头线与测压管水头线"],
                "method": "旋涡耗散率分析总水头线+包达公式证扩压升水头法",
                "difficulty": 3,
                "rubric": [
                    {"label": "阐明突扩拐角旋涡分离剧烈耗能使总水头线陡降，下游流束充满大管后仅剩微小沿程损失故转缓", "pts": 5},
                    {"label": "列水平伯努利方程并结合包达公式说明动能减小量大于局部损失（差值 v2(v1-v2)/g > 0），故测压管水头线逐渐升高", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2011-06",
                "year": 2011,
                "no": 6,
                "type": "calc",
                "score": 15,
                "title": "无摩擦活塞油缸加载下 U 形水银测压计液面高差计算",
                "stem": "如图测量装置，活塞直径 $d = 35\\,\\mathrm{mm}$，油的相对密度 $S_{\\text{油}} = \\rho_{\\text{油}}/\\rho_{\\text{水}} = 0.92$，水银的相对密度 $S_{\\text{水银}} = 13.60$，活塞与缸壁无泄漏和摩擦。当活塞重为 $15\\,\\mathrm{N}$ 时，$h = 700\\,\\mathrm{mm}$，试计算 U 形管测压计的液面高度 $\\Delta h$ 值。",
                "note": "",
                "figures": [
                    {"src": "figures/q06_orig.png", "caption": "题 6 图　活塞油室与 U 形水银测压计装置"}
                ],
                "shortAnswer": "Δh ≈ 0.164 m（即 16.43 cm 或 164.3 mm；若取 g=9.81 m/s² 则为 164.2 mm）",
                "judgeAnswer": None,
                "answer": "U 形管水银测压计的液面高度差 $\\Delta h \\approx 0.164\\,\\mathrm{m}$（即 $16.43\\,\\mathrm{cm}$ 或 $164.3\\,\\mathrm{mm}$；若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $164.2\\,\\mathrm{mm}$）。",
                "analysis": "**1. 求活塞底面传递给油液顶部的相对压强 $p_{\\text{塞}}$**\n\n已知活塞直径 $d = 35\\,\\mathrm{mm} = 0.035\\,\\mathrm{m}$，活塞自重 $G = 15\\,\\mathrm{N}$，活塞与缸壁无泄漏和摩擦，其上表面受大气压 $p_a$ 作用，故活塞底面油液的相对压强（表压强）为：\n\n$$\nA = \\frac{\\pi}{4}d^2 = \\frac{\\pi}{4} \\times 0.035^2 \\approx 9.6211 \\times 10^{-4}\\,\\mathrm{m^2}\n$$\n\n$$\np_{\\text{塞}} = \\frac{G}{A} = \\frac{15}{9.6211 \\times 10^{-4}} \\approx 15590.7\\,\\mathrm{Pa} \\approx 15.59\\,\\mathrm{kPa}\n$$\n\n**2. 选取油—水银交界面为等压面列平衡方程求 $\\Delta h$**\n\n如题 6 图所示，过 U 形管左支油—水银交界面作水平面 $1\\text{—}1$。因下方水银静止且连续连通，平面 $1\\text{—}1$ 为等压面；右支顶端通大气（相对压强为 $0$），左支在 $1\\text{—}1$ 面以上油柱总高度为 $h = 700\\,\\mathrm{mm} = 0.70\\,\\mathrm{m}$。由等压面压强相等列方程：\n\n$$\np_{\\text{塞}} + S_{\\text{油}}\\rho_{\\text{水}} g h = S_{\\text{水银}}\\rho_{\\text{水}} g \\Delta h\n$$\n\n代入 $\\rho_{\\text{水}} = 1000\\,\\mathrm{kg/m^3}$，$g = 9.80\\,\\mathrm{m/s^2}$，$S_{\\text{油}} = 0.92$，$S_{\\text{水银}} = 13.60$：\n\n$$\n\\Delta h = \\frac{\\frac{p_{\\text{塞}}}{\\rho_{\\text{水}} g} + S_{\\text{油}} h}{S_{\\text{水银}}} = \\frac{\\frac{15590.7}{1000 \\times 9.80} + 0.92 \\times 0.70}{13.60} = \\frac{1.5909 + 0.6440}{13.60} = \\frac{2.2349}{13.60} \\approx 0.16433\\,\\mathrm{m} \\approx 164.3\\,\\mathrm{mm}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $p_{\\text{塞}}/(\\rho_{\\text{水}} g) = 1.5893\\,\\mathrm{m}$，$\\Delta h = 2.2333 / 13.60 \\approx 0.16421\\,\\mathrm{m} \\approx 164.2\\,\\mathrm{mm}$。）",
                "analysisFigures": [],
                "pitfalls": "1. 等压面方程右端是水银柱静水压强 $S_{\\text{水银}}\\rho_{\\text{水}} g \\Delta h$，求解 $\\Delta h$ 时分母必须除以 **$S_{\\text{水银}} \\rho_{\\text{水}} g = 13.60 \\rho_{\\text{水}} g$**，切勿笔误写成 $\\rho_{\\text{水}} g$！\n2. 活塞直径 $d = 35\\,\\mathrm{mm}$ 与液高 $h = 700\\,\\mathrm{mm}$ 代入计算前务必先统一换算为国际单位米（$\\mathrm{m}$）。",
                "chapter": 2,
                "kps": ["多液层压差计", "等压面性质", "帕斯卡定律"],
                "method": "等压面静水压强递推法",
                "difficulty": 2,
                "rubric": [
                    {"label": "计算活塞截面积 A ≈ 9.621×10⁻⁴ m² 及活塞底面相对压强 p塞 = G/A ≈ 15.59 kPa", "pts": 5},
                    {"label": "取左支油-水银分界面 1—1 为等压面，正确列出 p塞 + S油ρ水gh = S水银ρ水gΔh", "pts": 6},
                    {"label": "代入数据解得水银液面高度差 Δh ≈ 0.164 m（16.43 cm）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2011-07",
                "year": 2011,
                "no": 7,
                "type": "calc",
                "score": 15,
                "title": "两侧受水压斜置矩形自动开启水闸铰链轴位置计算",
                "stem": "绕铰链轴 $O$ 转动的自动开启式水闸，当水位超过 $H = 2\\,\\mathrm{m}$ 时，矩形闸门自动开启。若闸门另一侧的水位 $h = 0.4\\,\\mathrm{m}$，角 $\\alpha = 60^{\\circ}$，试求铰链的位置 $x$。",
                "note": "",
                "figures": [
                    {"src": "figures/q07_orig.png", "caption": "题 7 图　绕铰链轴 O 转动的自动开启式斜置矩形水闸"}
                ],
                "shortAnswer": "x ≈ 0.795 m（精确值 248/(180√3) ≈ 0.7955 m）",
                "judgeAnswer": None,
                "answer": "铰链轴 $O$ 距闸门底端沿门面的位置距离为 $x \\approx 0.795\\,\\mathrm{m}$（保留四位小数为 $0.7955\\,\\mathrm{m}$）。",
                "analysis": "**1. 计算闸门左、右两侧静水总压力大小与作用点位置**\n\n取单位门宽 $b = 1\\,\\mathrm{m}$ 分析（门宽 $b$ 在力矩方程两端严格约去，受力与力臂见解图 7）。闸门倾角 $\\alpha = 60^{\\circ}$：\n\n- **左侧上游水压力 $P_1$（水深 $H = 2.0\\,\\mathrm{m}$）**：\n  左侧受压斜面长度 $L_1 = \\frac{H}{\\sin\\alpha} = \\frac{2.0}{\\sin 60^{\\circ}} = \\frac{4}{\\sqrt{3}} \\approx 2.3094\\,\\mathrm{m}$，静水压强呈三角形分布，故总压力与压力中心距门底的距离 $e_1$ 分别为：\n\n$$\nP_1 = \\rho g \\frac{H}{2} (b L_1) = \\frac{\\rho g b H^2}{2\\sin\\alpha}, \\qquad e_1 = \\frac{L_1}{3} = \\frac{H}{3\\sin\\alpha} \\approx 0.7698\\,\\mathrm{m}\n$$\n\n- **右侧下游水压力 $P_2$（水深 $h = 0.4\\,\\mathrm{m}$）**：\n  右侧受压斜面长度 $L_2 = \\frac{h}{\\sin\\alpha} = \\frac{0.4}{\\sin 60^{\\circ}} = \\frac{0.8}{\\sqrt{3}} \\approx 0.4619\\,\\mathrm{m}$，同理得总压力与作用点距门底距离 $e_2$：\n\n$$\nP_2 = \\frac{\\rho g b h^2}{2\\sin\\alpha}, \\qquad e_2 = \\frac{L_2}{3} = \\frac{h}{3\\sin\\alpha} \\approx 0.1540\\,\\mathrm{m}\n$$\n\n**2. 列临界自动开启瞬间的绕铰轴 $O$ 力矩平衡方程求 $x$**\n\n当上游水深较低时，闸门底端紧靠左侧底坎止水处于关闭状态；当上游水位刚升至临界值 $H = 2.0\\,\\mathrm{m}$ 即将顺时针翻转开启（上部向右倾倒泄流、底端脱离底坎）的临界瞬间，底坎法向支持反力恰好减为零（不计门重与铰摩擦），左、右两侧静水总压力对铰链轴 $O$ 的力矩严格平衡：\n\n$$\nP_1 (x - e_1) = P_2 (x - e_2)\n$$\n\n注意到压力之比 $\\frac{P_1}{P_2} = \\frac{H^2}{h^2} = \\left(\\frac{2.0}{0.4}\\right)^2 = 25$，解出铰链轴距门底距离 $x$：\n\n$$\nx = \\frac{P_1 e_1 - P_2 e_2}{P_1 - P_2} = \\frac{H^3 - h^3}{3(H^2 - h^2)\\sin\\alpha}\n$$\n\n代入 $H = 2.0\\,\\mathrm{m}$，$h = 0.4\\,\\mathrm{m}$，$\\sin 60^{\\circ} = \\frac{\\sqrt{3}}{2}$：\n\n$$\nx = \\frac{2.0^3 - 0.4^3}{3 \\times (2.0^2 - 0.4^2) \\times \\frac{\\sqrt{3}}{2}} = \\frac{8.000 - 0.064}{3 \\times 3.84 \\times 0.866025} = \\frac{7.936}{9.9766} \\approx 0.79546\\,\\mathrm{m} \\approx 0.795\\,\\mathrm{m}\n$$\n\n（物理验证：当上游水位超过 $2.0\\,\\mathrm{m}$ 时，$e_1 = \\frac{H}{3\\sin 60^{\\circ}}$ 随 $H$ 增大并越过 $O$ 点，顺时针开启力矩大于逆时针闭合力矩，水闸确能自动开启。）",
                "analysisFigures": [
                    {"src": "figures/q07_sol.png", "caption": "解图 7　自动开启水闸两侧三角形静水荷载与对铰轴 O 的力矩平衡图"}
                ],
                "pitfalls": "1. 自自由水面延伸至底部的三角形静水荷载，其压力中心直接位于斜面水下长度自上而下 $\\frac{2}{3}L$ 处，即**距闸门底端 $\\frac{1}{3}L$ 处**（利用图解法秒得 $e_1 = L_1/3$、$e_2 = L_2/3$，比套平行移轴公式快得多且不易算错）！\n2. 切勿把竖直水深 $H$、$h$ 直接当作斜面受压长度：斜面长度为 $L_1 = H/\\sin 60^{\\circ}$、$L_2 = h/\\sin 60^{\\circ}$，分母上的 $\\sin 60^{\\circ}$ 千万不能漏掉！",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力", "自动开启闸门力矩平衡", "压力中心图解法"],
                "method": "三角形压强分布图解法与铰轴力矩平衡法",
                "difficulty": 3,
                "rubric": [
                    {"label": "按斜面受压长度 L1=H/sin60°、L2=h/sin60° 正确写出两侧静水总压力 P1、P2 表达式", "pts": 5},
                    {"label": "确定两侧压力中心距门底距离 e1 = L1/3 ≈ 0.770 m、e2 = L2/3 ≈ 0.154 m", "pts": 4},
                    {"label": "列出临界开启力矩平衡方程 P1(x - e1) = P2(x - e2) 并解出 x ≈ 0.795 m", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2011-08",
                "year": 2011,
                "no": 8,
                "type": "calc",
                "score": 15,
                "title": "汽油容器浮子曳绳自动底阀临界开启油面高度计算",
                "stem": "在盛有汽油的容器的底上有一直径 $d_2 = 2\\,\\mathrm{cm}$ 的圆阀，该阀用曳绳系于直径 $d_1 = 10\\,\\mathrm{cm}$ 的圆柱形浮子上，如图所示，设浮子及圆阀的总重量 $G = 0.981\\,\\mathrm{N}$，汽油的密度 $\\rho = 750\\,\\mathrm{kg/m^3}$，曳绳长度为 $z = 15\\,\\mathrm{cm}$，问圆阀将在汽油油面超过什么高度时开启？",
                "note": "",
                "figures": [
                    {"src": "figures/q08_orig.png", "caption": "题 8 图　汽油容器圆柱浮子与底孔圆阀连接示意图"}
                ],
                "shortAnswer": "H ≈ 17.40 cm（即 0.174 m，此时浮子吃油深度 h ≈ 2.40 cm）",
                "judgeAnswer": None,
                "answer": "当容器内汽油油面高度超过 **$H \\approx 17.40\\,\\mathrm{cm}$（即 $0.174\\,\\mathrm{m}$）**时，底部圆阀将自动开启。",
                "analysis": "**1. 建立临界开启瞬间的整体竖向受力平衡方程**\n\n设圆阀即将被拉起开启时的临界汽油总深度为 $H$，此时曳绳（长 $z = 15\\,\\mathrm{cm} = 0.15\\,\\mathrm{m}$）绷紧，圆柱形浮子浸入汽油的吃液深度为 $h = H - z$（忽略极薄圆阀厚度与细绳体积，受力见解图 8）。\n\n取“圆柱形浮子 + 曳绳 + 底部圆阀”整体为隔离体，临界开启瞬间阀口支承座接触反力为零，竖向共受三个力作用：\n\n1. **浮子所受竖直向上的阿基米德浮力 $F_b$**：\n\n$$\nF_b = \\rho g V_{\\text{排}} = \\rho g h A_1 = \\rho g (H - z)\\frac{\\pi}{4}d_1^2\n$$\n\n2. **底部圆阀所受竖直向下的静液压力 $P_v$**（圆阀底面通外部大气，表压为零；顶面受总油深 $H$ 处的静压强 $p = \\rho g H$）：\n\n$$\nP_v = \\rho g H A_2 = \\rho g H \\cdot \\frac{\\pi}{4}d_2^2\n$$\n\n3. **浮子与圆阀总自重**：$G = 0.981\\,\\mathrm{N}$（竖直向下）。\n\n由竖向力平衡 $\\sum F_z = 0$：\n\n$$\nF_b = G + P_v \\implies \\rho g (H - z)\\frac{\\pi}{4}d_1^2 = G + \\rho g H \\frac{\\pi}{4}d_2^2\n$$\n\n**2. 代入物理参数求解临界油面高度 $H$**\n\n移项整理直接解出 $H$（注意统一采用国际单位：$d_1 = 0.10\\,\\mathrm{m}$，$d_2 = 0.02\\,\\mathrm{m}$，$z = 0.15\\,\\mathrm{m}$，$\\rho = 750\\,\\mathrm{kg/m^3}$；结合 $G = 0.981\\,\\mathrm{N}$ 协调取 $g = 9.81\\,\\mathrm{m/s^2}$，同时校核 $g = 9.80\\,\\mathrm{m/s^2}$）：\n\n$$\nA_1 = \\frac{\\pi}{4} \\times 0.10^2 \\approx 7.8540 \\times 10^{-3}\\,\\mathrm{m^2}, \\qquad A_2 = \\frac{\\pi}{4} \\times 0.02^2 \\approx 3.1416 \\times 10^{-4}\\,\\mathrm{m^2}\n$$\n\n$$\nH = \\frac{\\frac{G}{\\rho g} + A_1 z}{A_1 - A_2} = \\frac{\\frac{0.981}{750 \\times 9.81} + 7.8540 \\times 10^{-3} \\times 0.15}{7.8540 \\times 10^{-3} - 3.1416 \\times 10^{-4}}\n$$\n\n计算分子与分母：\n\n$$\nH = \\frac{1.3333 \\times 10^{-4} + 1.1781 \\times 10^{-3}}{7.5398 \\times 10^{-3}} = \\frac{1.3114 \\times 10^{-3}}{7.5398 \\times 10^{-3}} \\approx 0.17393\\,\\mathrm{m} \\approx 17.39\\,\\mathrm{cm} \\approx 17.40\\,\\mathrm{cm}\n$$\n\n（此时浮子吃油深度 $h = H - z = 17.393 - 15.0 = 2.393\\,\\mathrm{cm} \\approx 2.40\\,\\mathrm{cm}$；若取 $g = 9.80\\,\\mathrm{m/s^2}$，算得 $H = 17.395\\,\\mathrm{cm} \\approx 17.40\\,\\mathrm{cm}$，两者完全一致。）",
                "analysisFigures": [
                    {"src": "figures/q08_sol.png", "caption": "解图 8　浮子—曳绳—圆阀整体临界开启竖向受力平衡图"}
                ],
                "pitfalls": "1. **严防厘米（$\\mathrm{cm}$）与米（$\\mathrm{m}$）单位混算！** $d_1 = 10\\,\\mathrm{cm}$、$d_2 = 2\\,\\mathrm{cm}$、$z = 15\\,\\mathrm{cm}$ 均为厘米，而 $G = 0.981\\,\\mathrm{N}$、$\\rho = 750\\,\\mathrm{kg/m^3}$ 为国际单位，算出 $h = 2.40\\,\\mathrm{cm}$、$H = 17.40\\,\\mathrm{cm}$（即 $0.174\\,\\mathrm{m}$），切勿误把厘米写成 $17.4\\,\\mathrm{m}$！\n2. 圆阀面积用的是底孔直径 $d_2 = 0.02\\,\\mathrm{m}$，浮子浮力用的是浮子直径 $d_1 = 0.10\\,\\mathrm{m}$，切勿代混；且流体密度是汽油 $\\rho = 750\\,\\mathrm{kg/m^3}$ 而非水。",
                "chapter": 2,
                "kps": ["浮力与自动泄水阀设计", "平面静水总压力", "阿基米德原理"],
                "method": "阿基米德浮力与静水压力平衡法",
                "difficulty": 3,
                "rubric": [
                    {"label": "正确写出浮子浮力 Fb = ρg(H - z)(πd1²/4) 与圆阀向下静液压力 Pv = ρgH(πd2²/4)", "pts": 6},
                    {"label": "列出临界开启竖向平衡方程 Fb = G + Pv", "pts": 4},
                    {"label": "统一国际单位代入汽油密度 ρ=750 kg/m³ 准确解出临界油面高度 H ≈ 17.40 cm（0.174 m）", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2011-09",
                "year": 2011,
                "no": 9,
                "type": "calc",
                "score": 15,
                "title": "顶部铅直进水侧向水平出水的水箱在磅秤上的动量读数计算",
                "stem": "质量为 $100\\,\\mathrm{kg}$ 的空水箱，放在磅秤上，如图所示。水箱中存有 $20\\,^{\\circ}\\mathrm{C}$ 的水，密度 $\\rho = 998\\,\\mathrm{kg/m^3}$，体积为 $1\\,\\mathrm{m^3}$。进水和出水管径均为 $d_1 = d_2 = 50\\,\\mathrm{mm}$，它们的流量均为 $0.06\\,\\mathrm{m^3/s}$，试问磅秤上的读数为多少？",
                "note": "",
                "figures": [
                    {"src": "figures/q09_orig.png", "caption": "题 9 图　置于磅秤上的恒定进出流水箱"}
                ],
                "shortAnswer": "磅秤承受的总下压力 N ≈ 12.59 kN（12590.2 N；若取 g=9.81 m/s² 则为 12.60 kN 即 12601.2 N），折合磅秤质量读数为 1284.7 kg（或 1284.5 kg）。",
                "judgeAnswer": None,
                "answer": "取 $g = 9.80\\,\\mathrm{m/s^2}$，水箱对磅秤的竖直总压力（力值读数）为 **$12.59\\,\\mathrm{kN}$（即 $12590.2\\,\\mathrm{N}$）**，折算为磅秤质量读数为 **$1284.7\\,\\mathrm{kg}$**。（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则力值读数为 $12.60\\,\\mathrm{kN}$ 即 $12601.2\\,\\mathrm{N}$，质量读数为 $1284.5\\,\\mathrm{kg}$。）",
                "analysis": "**1. 验证水箱恒定流条件并计算进出口射流流速**\n\n因进水流量与出水流量相等（$Q_1 = Q_2 = Q = 0.06\\,\\mathrm{m^3/s}$），箱内水体体积恒定保持 $V = 1\\,\\mathrm{m^3}$，流场处于恒定流状态。进、出水管内径均为 $d_1 = d_2 = 0.05\\,\\mathrm{m}$，断面平均流速为：\n\n$$\nA_1 = A_2 = \\frac{\\pi}{4}d_1^2 = \\frac{\\pi}{4} \\times 0.05^2 \\approx 1.9635 \\times 10^{-3}\\,\\mathrm{m^2}\n$$\n\n$$\nv_1 = v_2 = \\frac{Q}{A_1} = \\frac{0.06}{1.9635 \\times 10^{-3}} \\approx 30.5577\\,\\mathrm{m/s}\n$$\n\n**2. 选取“水箱壳体 + 箱内水体”整体控制体列竖向动量方程**\n\n以整个水箱及箱内 $1\\,\\mathrm{m^3}$ 水体为控制体（控制面紧贴水箱底面、顶部自由射流入口断面 $1\\text{—}1$ 及左侧水平出口断面 $2\\text{—}2$，见解图 9）。取竖直向上为 $y$ 轴正方向：\n\n- 进出口射流均直接通大气，相对压强为零（断面静压项为零）；\n- 顶部进水沿竖直向下方向流入控制体，竖向速度分量 $v_{1y} = -v_1 = -30.5577\\,\\mathrm{m/s}$；\n- 左侧出水沿水平方向流出控制体，竖向速度分量 $v_{2y} = 0$；\n- 控制体所受竖向外力为：磅秤台面对水箱底面竖直向上的支承反力 $N$，以及空水箱与箱内水体的总重力 $G_{\\text{总}} = (m_{\\text{箱}} + \\rho V)g$（竖直向下）。\n\n列 $y$ 方向恒定总流动量方程（取 $\\beta_1 = \\beta_2 = 1.0$）：\n\n$$\nN - (m_{\\text{箱}} + \\rho V)g = \\rho Q (v_{2y} - v_{1y}) = \\rho Q \\left[0 - (-v_1)\\right] = \\rho Q v_1\n$$\n\n**3. 代入数值求磅秤受力与读数**\n\n- 铅直入流射流冲击附加动水力：\n\n$$\nF_{\\text{动}} = \\rho Q v_1 = 998 \\times 0.06 \\times 30.5577 \\approx 1829.8\\,\\mathrm{N} \\approx 1.830\\,\\mathrm{kN}\n$$\n\n- 水箱与箱内水总静重（取 $g = 9.80\\,\\mathrm{m/s^2}$）：\n\n$$\nG_{\\text{总}} = (100 + 998 \\times 1) \\times 9.80 = 1098 \\times 9.80 = 10760.4\\,\\mathrm{N} \\approx 10.760\\,\\mathrm{kN}\n$$\n\n- 磅秤所受竖直向下总压力 $N^{\\prime} = N$：\n\n$$\nN^{\\prime} = G_{\\text{总}} + F_{\\text{动}} = 10760.4 + 1829.8 = 12590.2\\,\\mathrm{N} \\approx 12.59\\,\\mathrm{kN}\n$$\n\n若磅秤表盘以质量（$\\mathrm{kg}$）刻度显示，则磅秤读数为：\n\n$$\nM_{\\text{读}} = \\frac{N^{\\prime}}{g} = 1098 + \\frac{1829.8}{9.80} = 1098 + 186.71 = 1284.7\\,\\mathrm{kg}\n$$\n\n（若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $G_{\\text{总}} = 10771.4\\,\\mathrm{N}$，$N^{\\prime} = 12601.2\\,\\mathrm{N} \\approx 12.60\\,\\mathrm{kN}$，$M_{\\text{读}} = 1284.5\\,\\mathrm{kg}$。）",
                "analysisFigures": [
                    {"src": "figures/q09_sol.png", "caption": "解图 9　水箱与箱内水整体控制体竖向受力与动量通量图"}
                ],
                "pitfalls": "**切忌把箱内 $1\\,\\mathrm{m^3}$ 水的自重 $G_{\\text{水}} \\approx 9.78\\,\\mathrm{kN}$ 重复加两次！** 若先对水体单独列动量方程求出水对箱底总压力 $R^{\\prime} = G_{\\text{水}} + \\rho Q v_1 = 11.61\\,\\mathrm{kN}$，该 $R^{\\prime}$ 中**已经包含了水重 $G_{\\text{水}}$**，再求磅秤读数时只需加**空水箱重 $G_{\\text{箱}} = 0.98\\,\\mathrm{kN}$**（得 $12.59\\,\\mathrm{kN}$），绝不可再加一次 $G_{\\text{水}}$ 误算成 $22.39\\,\\mathrm{kN}$！直接取“水箱 + 水”整体控制体可从根源杜绝此错误。",
                "chapter": 3,
                "kps": ["恒定总流动量方程", "射流冲击力", "整体控制体法"],
                "method": "整体控制体竖向动量方程求支反力法",
                "difficulty": 3,
                "rubric": [
                    {"label": "由连续性方程求出进出水管流速 v1 = v2 ≈ 30.56 m/s 及射流冲击附加力 ρQv1 ≈ 1829.8 N", "pts": 5},
                    {"label": "取水箱与水整体为控制体，正确列出竖向动量方程 N - (m箱 + ρV)g = ρQv1（无重复计重）", "pts": 6},
                    {"label": "准确算出磅秤所受总压力 12.59 kN（或 12.60 kN，折合质量读数 1284.7 kg）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2011-10",
                "year": 2011,
                "no": 10,
                "type": "calc",
                "score": 20,
                "title": "已知水泵功率与效率向封闭加压水塔供水的输水管径设计",
                "stem": "如图所示，用功率 $N = 10\\,\\mathrm{kW}$，效率 $\\eta = 72\\%$ 的水泵将水从湖中通过图示管道抽至水塔中，水塔中液面与湖面的垂直距离为 $25\\,\\mathrm{m}$，水塔中的表压为 $150\\,\\mathrm{kPa}$，流量为 $0.012\\,\\mathrm{m^3/s}$，管道总长 $260\\,\\mathrm{m}$，沿程水头损失系数 $\\lambda = 0.023$，途中经过 $3$ 个局部阻力系数 $\\zeta_1 = 0.3$ 的 $90^{\\circ}$ 直角弯管，$2$ 个 $\\zeta_2 = 0.25$ 的 $45^{\\circ}$ 弯管，一个 $\\zeta_3 = 2$ 的吸水罩和一个 $\\zeta_4 = 70$ 的球阀。试求所用管径。",
                "note": "",
                "figures": [
                    {"src": "figures/q10_orig.png", "caption": "题 10 图　水泵从湖泊向密闭受压水塔抽水系统示意图"}
                ],
                "shortAnswer": "d ≈ 0.094 m（即 94.0 mm；若额外计入管口入水塔淹没局部损失系数 ζ出=1.0 则为 94.1 mm，工程标准管径可选 DN100）",
                "judgeAnswer": None,
                "answer": "所需输水管道的内径为 **$d \\approx 0.094\\,\\mathrm{m}$（即 $94.0\\,\\mathrm{mm}$）**（若计入管道入水塔淹没出口局部损失系数 $\\zeta_{\\text{出}} = 1.0$ 则为 $94.1\\,\\mathrm{mm}$）。",
                "analysis": "**1. 由水泵轴功率 $N$ 与效率 $\\eta$ 求水泵提供的总扬程 $H_p$**\n\n已知水泵输入轴功率 $N = 10\\,\\mathrm{kW} = 10000\\,\\mathrm{W}$，效率 $\\eta = 72\\% = 0.72$，设计输水流量 $Q = 0.012\\,\\mathrm{m^3/s}$。取 $\\rho = 1000\\,\\mathrm{kg/m^3}$，$g = 9.80\\,\\mathrm{m/s^2}$，由水泵功率关系式 $N = \\frac{\\rho g Q H_p}{1000\\,\\eta}$ 解得水泵扬程：\n\n$$\nH_p = \\frac{1000\\,\\eta N}{\\rho g Q} = \\frac{1000 \\times 0.72 \\times 10}{1000 \\times 9.80 \\times 0.012} = \\frac{7200}{117.6} \\approx 61.224\\,\\mathrm{m}\n$$\n\n**2. 对湖面与密闭水塔液面列总流能量方程，求管路允许总水头损失 $h_w$**\n\n以湖泊自由水面为基准面（$z_1 = 0,\\; p_1 = 0,\\; v_1 \\approx 0$），密闭水塔内液面高程 $z_2 = 25\\,\\mathrm{m}$、表压强 $p_2 = 150\\,\\mathrm{kPa} = 1.5 \\times 10^5\\,\\mathrm{Pa}$、液面下降/上升流速 $v_2 \\approx 0$。列全系统能量方程（水头构成见解图 10）：\n\n$$\n0 + 0 + 0 + H_p = z_2 + \\frac{p_2}{\\rho g} + 0 + h_w\n$$\n\n其中净静扬程（地形高差 + 水塔表压水头）为：\n\n$$\nH_{\\text{静}} = z_2 + \\frac{p_2}{\\rho g} = 25 + \\frac{150 \\times 10^3}{1000 \\times 9.80} = 25 + 15.306 = 40.306\\,\\mathrm{m}\n$$\n\n故管路沿程与局部总水头损失为：\n\n$$\nh_w = H_p - H_{\\text{静}} = 61.224 - 40.306 = 20.918\\,\\mathrm{m}\n$$\n\n**3. 建立关于管径 $d$ 的五次水头损失方程并迭代求解**\n\n汇总题干给定的全部局部阻力系数：\n\n$$\n\\sum \\zeta = 3\\zeta_1 + 2\\zeta_2 + \\zeta_3 + \\zeta_4 = 3 \\times 0.3 + 2 \\times 0.25 + 2 + 70 = 0.9 + 0.5 + 2 + 70 = 73.4\n$$\n\n由连续性方程 $v = \\frac{4Q}{\\pi d^2}$ 及达西—魏斯巴赫公式，管路总水头损失（同时包含全长 $l = 260\\,\\mathrm{m}$ 的沿程损失与全部局部损失！）为：\n\n$$\nh_w = \\left(\\lambda \\frac{l}{d} + \\sum \\zeta\\right)\\frac{v^2}{2g} = \\left(\\lambda \\frac{l}{d} + \\sum \\zeta\\right)\\frac{8 Q^2}{\\pi^2 g d^4}\n$$\n\n代入 $\\lambda = 0.023,\\; l = 260\\,\\mathrm{m}\\;(\\lambda l = 5.98\\,\\mathrm{m})$，$\\frac{8 Q^2}{\\pi^2 g} = \\frac{8 \\times 0.012^2}{\\pi^2 \\times 9.80} \\approx 1.1909 \\times 10^{-5}\\,\\mathrm{m^5}$：\n\n$$\n\\left(\\frac{5.98}{d} + 73.4\\right)\\frac{1.1909 \\times 10^{-5}}{d^4} = 20.918 \\implies d = \\left[\\frac{1.1909 \\times 10^{-5}}{20.918}\\left(\\frac{5.98}{d} + 73.4\\right)\\right]^{1/4}\n$$\n\n用简单不动点迭代法迅速求解：\n- 初设 $d^{(0)} = 0.10\\,\\mathrm{m}$，代入右端括号得 $\\frac{5.98}{0.10} + 73.4 = 133.2$，算得 $d^{(1)} = (5.693 \\times 10^{-7} \\times 133.2)^{1/4} \\approx 0.0933\\,\\mathrm{m}$；\n- 代入 $d^{(1)} = 0.0933\\,\\mathrm{m}$，括号内为 $\\frac{5.98}{0.0933} + 73.4 = 137.49$，算得 $d^{(2)} \\approx 0.09406\\,\\mathrm{m}$；\n- 代入 $d^{(2)} = 0.09406\\,\\mathrm{m}$，括号内为 $136.98$，算得 **$d \\approx 0.09398\\,\\mathrm{m} \\approx 0.094\\,\\mathrm{m} = 94.0\\,\\mathrm{mm}$**。\n\n（注：① 若额外计入管道进入水塔的淹没出口局部损失 $\\zeta_{\\text{出}} = 1.0$，即 $\\sum\\zeta = 74.4$，解得 $d = 94.14\\,\\mathrm{mm} \\approx 0.094\\,\\mathrm{m}$；② 若取 $g = 9.81\\,\\mathrm{m/s^2}$，解得 $d = 94.01\\,\\mathrm{mm} \\approx 0.094\\,\\mathrm{m}$，结果高度一致。）",
                "analysisFigures": [
                    {"src": "figures/q10_sol.png", "caption": "解图 10　水泵总扬程 61.22 m 的能量分配构成与管径反算关系"}
                ],
                "pitfalls": "1. **严禁遗漏长 $260\\,\\mathrm{m}$ 管道的沿程水头损失项 $\\lambda\\frac{l}{d}\\frac{v^2}{2g}$！** 在 $d = 0.094\\,\\mathrm{m}$ 下，$\\lambda\\frac{l}{d} \\approx 63.6$ 与局部阻力系数和 $\\sum\\zeta = 73.4$ 量级相当，若漏掉沿程损失项将把管径严重误算为 $0.057\\,\\mathrm{m}$！\n2. 水塔并非敞口通大气，塔顶封闭气体有表压 $150\\,\\mathrm{kPa}$（折合 $15.31\\,\\mathrm{m}$ 静压水头），列能量方程时切勿漏加 $\\frac{p_2}{\\rho g}$；且弯管有 $3$ 个 $90^{\\circ}$、$2$ 个 $45^{\\circ}$，注意乘各自个数。",
                "chapter": 6,
                "kps": ["水泵扬程与轴功率", "有压管路水力计算", "沿程与局部损失"],
                "method": "水泵轴功率求扬程+五次阻力方程迭代求管径法",
                "difficulty": 4,
                "rubric": [
                    {"label": "由 N = ρgQHp/(1000η) 正确求出水泵总扬程 Hp ≈ 61.22 m", "pts": 5},
                    {"label": "计入地形高差 25 m 与水塔表压水头 15.31 m，求得管路总水头损失 hw ≈ 20.92 m", "pts": 5},
                    {"label": "准确汇总全部局部阻力系数 Σζ = 73.4（或含出口 74.4）并写出含沿程项 λl/d 的总损失方程", "pts": 5},
                    {"label": "代入 Q = 0.012 m³/s 迭代解得管道直径 d ≈ 0.094 m（94.0 mm）", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2011-11",
                "year": 2011,
                "no": 11,
                "type": "proof",
                "score": 12,
                "title": "孔板流量计理论与局部损失修正流量表达式及差压计实际流量公式推导",
                "stem": "孔板流量计是工业上测量给水和蒸气流量常用的节流装置。孔板由不锈钢制成，中间圆孔与管道同心，如图所示。孔板流量计的测流原理与文丘里管基本一致。已知圆管管径为 $d$，孔板前管轴线处的压强为 $p_1$，孔板的孔径为 $d_0$，孔板后中心处的压强为 $p_2$，孔板流量计的局部阻力系数为 $\\zeta$，试推求孔板流量计的流量表达式。实际孔板的测压位置紧靠孔板的两侧，即图中的测压装置，试根据前面得到的流量公式形式，写出孔板流量计的实际流量公式。",
                "note": "",
                "figures": [
                    {"src": "figures/q11_orig.png", "caption": "题 11 图　同心圆孔板流量计流束收缩与两侧差压计构造"}
                ],
                "shortAnswer": "（1）设孔后收缩断面收缩系数为 ε = A2/A0（若不计收缩取 ε=1），流量表达式为 Q = [ε(π/4)d0² / √(1 + ζ - ε²(d0/d)⁴)]·√[2(p1 - p2)/ρ]（当 ε=1 时为 [(π/4)d0² / √(1 + ζ - (d0/d)⁴)]·√[2(p1 - p2)/ρ]）；（2）紧靠孔板两侧角接取压并接重液 U 形差压计（读数 h，指示液密度 ρm）时，引入综合流量系数 μ，实际流量公式为 Q = μ(π/4)d0²·√[2g(ρm - ρ)h / ρ]（或以两侧实测压差 Δp 表为 Q = μ(π/4)d0²·√(2Δp/ρ)）。",
                "judgeAnswer": None,
                "answer": "**（1）由断面 $p_1$、$p_2$ 与局部阻力系数 $\\zeta$ 推求的流量表达式**：\n设孔板圆孔面积 $A_0 = \\frac{\\pi}{4}d_0^2$，孔后流束收缩断面面积 $A_2 = \\varepsilon A_0$（$\\varepsilon$ 为收缩系数）：\n\n$$\nQ = \\frac{\\varepsilon \\frac{\\pi}{4}d_0^2}{\\sqrt{1 + \\zeta - \\varepsilon^2\\left(\\frac{d_0}{d}\\right)^4}}\\sqrt{\\frac{2(p_1 - p_2)}{\\rho}}\n$$\n\n（注：若按题设将局部损失系数 $\\zeta$ 直接定义在孔口名义断面 $d_0$ 上且令 $\\varepsilon = 1$，则表达式简化为 $Q = \\frac{\\frac{\\pi}{4}d_0^2}{\\sqrt{1 + \\zeta - (d_0/d)^4}}\\sqrt{\\frac{2(p_1 - p_2)}{\\rho}}$。）\n\n**（2）紧靠孔板两侧角接取压配图示 U 形差压计的实际流量公式**：\n将收缩系数 $\\varepsilon$、局部阻力系数 $\\zeta$、径比 $\\frac{d_0}{d}$、流速不均及紧靠孔板两侧取压位置修正统一归并为实验标定的**孔板流量系数 $\\mu$**（设下方 U 形管指示液密度为 $\\rho_m$，液面差为 $h$）：\n\n$$\nQ = \\mu \\frac{\\pi}{4}d_0^2 \\sqrt{2g\\left(\\frac{\\rho_m - \\rho}{\\rho}\\right)h} \\quad \\left(\\text{或写为 } Q = \\mu \\frac{\\pi}{4}d_0^2 \\sqrt{\\frac{2 \\Delta p}{\\rho}}\\right)\n$$",
                "analysis": "**1. 第一问：运用恒定总流能量方程与连续性方程推导**\n\n选取孔板前未受扰动的圆管正常断面 $1\\text{—}1$（直径 $d$，面积 $A_1 = \\frac{\\pi}{4}d^2$，轴线压强 $p_1$，流速 $v_1$）和孔板后收缩断面 $2\\text{—}2$（面积 $A_2 = \\varepsilon A_0 = \\varepsilon \\frac{\\pi}{4}d_0^2$，中心压强 $p_2$，流速 $v_2$）。水平管道轴线高程相等（$z_1 = z_2$），忽略极短距离沿程损失，计入 $1\\text{—}2$ 段局部水头损失 $h_j = \\zeta \\frac{v_2^2}{2g}$，取 $\\alpha_1 = \\alpha_2 = 1.0$，列能量方程：\n\n$$\n\\frac{p_1}{\\rho g} + \\frac{v_1^2}{2g} = \\frac{p_2}{\\rho g} + \\frac{v_2^2}{2g} + \\zeta \\frac{v_2^2}{2g}\n$$\n\n由连续性方程 $Q = A_1 v_1 = A_2 v_2$ 得：\n\n$$\nv_1 = \\frac{A_2}{A_1}v_2 = \\varepsilon \\left(\\frac{d_0}{d}\\right)^2 v_2\n$$\n\n代入能量方程消去 $v_1$：\n\n$$\n\\frac{p_1 - p_2}{\\rho g} = \\left[1 + \\zeta - \\varepsilon^2 \\left(\\frac{d_0}{d}\\right)^4\\right]\\frac{v_2^2}{2g} \\implies v_2 = \\frac{1}{\\sqrt{1 + \\zeta - \\varepsilon^2 (d_0/d)^4}}\\sqrt{\\frac{2(p_1 - p_2)}{\\rho}}\n$$\n\n乘以过流面积 $A_2 = \\varepsilon \\frac{\\pi}{4}d_0^2$ 即得流量理论结构式：\n\n$$\nQ = A_2 v_2 = \\frac{\\varepsilon \\frac{\\pi}{4}d_0^2}{\\sqrt{1 + \\zeta - \\varepsilon^2\\left(\\frac{d_0}{d}\\right)^4}}\\sqrt{\\frac{2(p_1 - p_2)}{\\rho}}\n$$\n\n（特别地，若不单列 $\\varepsilon$ 而直接取孔口速度，即对应 $\\varepsilon = 1$ 形式：$Q = \\frac{\\frac{\\pi}{4}d_0^2}{\\sqrt{1 + \\zeta - (d_0/d)^4}}\\sqrt{\\frac{2(p_1 - p_2)}{\\rho}}$。）\n\n**2. 第二问：紧靠孔板两侧取压及 U 形管差压计换算**\n\n- 实际工业标准孔板常采用如题 11 图所示的**角接取压（紧靠孔板前后两侧壁面测压）**，该处流线弯曲且并非理想的渐变流断面 $1$ 和最小收缩断面 $2$，但前后压差 $\\Delta p = p_1^{\\prime} - p_2^{\\prime}$ 仍与动能水头成严格比例；\n- 对于图下方装有重质指示液（密度 $\\rho_m > \\rho$，如水银）的 U 形管差压计，过左侧指示液分界面作水平等压面，有：\n\n$$\np_1^{\\prime} + \\rho g h = p_2^{\\prime} + \\rho_m g h \\implies \\frac{p_1^{\\prime} - p_2^{\\prime}}{\\rho g} = \\left(\\frac{\\rho_m - \\rho}{\\rho}\\right)h\n$$\n\n- 保持第一问导出的公式结构，令无量纲综合**流量系数 $\\mu$** 吸收 $\\varepsilon$、$\\zeta$、$\\left(\\frac{d_0}{d}\\right)^4$ 及取压口位置修正系数（一般 $\\mu \\approx 0.60\\sim 0.65$），即得孔板流量计实际流量计算公式：\n\n$$\nQ = \\mu A_0 \\sqrt{2g\\left(\\frac{\\rho_m - \\rho}{\\rho}\\right)h} = \\mu \\frac{\\pi}{4}d_0^2 \\sqrt{2g\\left(\\frac{\\rho_m - \\rho}{\\rho}\\right)h}\n$$",
                "analysisFigures": [],
                "pitfalls": "1. 写下方 U 形重液差压计压差水头时，因差压计上方充满被测流体（密度 $\\rho$），有效压差水头是 **$\\left(\\frac{\\rho_m - \\rho}{\\rho}\\right)h$**（须减去被测流体柱密度 $\\rho$），切勿误写成 $\\frac{\\rho_m}{\\rho}h$！\n2. 孔板由于锐缘剧烈收缩与扩散旋涡，流量系数 $\\mu \\approx 0.62$ 显著小于文丘里流量计（$\\mu \\approx 0.96$）。",
                "chapter": 3,
                "kps": ["伯努利方程测流", "孔板流量计", "多液层压差计"],
                "method": "伯努利方程与连续性方程联立测流法",
                "difficulty": 3,
                "rubric": [
                    {"label": "正确列出含局部阻力系数 ζ 的孔前至孔后断面能量方程与连续性方程", "pts": 4},
                    {"label": "消去上游流速 v1 推导出孔板流量计关于 (p1 - p2) 的流量表达式", "pts": 4},
                    {"label": "结合紧靠孔板两侧取压修正系数 μ 及图示 U 形差压计等压面关系写出实际流量公式", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2011-12",
                "year": 2011,
                "no": 12,
                "type": "calc",
                "score": 12,
                "title": "已知二元恒定势流速度势函数求指定点流速与流函数表达式",
                "stem": "已知二元恒定势流的流速势函数 $\\varphi = x(2y - 1)$，求点 $(2\\,\\mathrm{m},\\; 5\\,\\mathrm{m})$ 处的流速，并求流函数的表达式。",
                "note": "",
                "figures": [],
                "shortAnswer": "点 (2 m, 5 m) 处流速分量 ux = 9 m/s、uy = 4 m/s，合流速大小 u = √97 ≈ 9.85 m/s；流函数表达式为 ψ = y² - y - x² + C（C 为任意常数）。",
                "judgeAnswer": None,
                "answer": "1. **点 $(2\\,\\mathrm{m},\\; 5\\,\\mathrm{m})$ 处的流速**：速度分量为 $u_x = 9\\,\\mathrm{m/s}$，$u_y = 4\\,\\mathrm{m/s}$，合流速大小为 **$u = \\sqrt{97} \\approx 9.85\\,\\mathrm{m/s}$**；\n\n2. **流函数的表达式**：\n\n$$\n\\psi(x, y) = y^2 - y - x^2 + C\\quad (C\\text{ 为任意常数})\n$$\n\n（注：若教材采用反号约定 $u_x = -\\frac{\\partial\\psi}{\\partial y},\\; u_y = \\frac{\\partial\\psi}{\\partial x}$，则对应 $\\psi = x^2 - y^2 + y + C$。）",
                "analysis": "**1. 求速度分量及点 $(2\\,\\mathrm{m},\\; 5\\,\\mathrm{m})$ 处的流速**\n\n将速度势函数展开为 $\\varphi(x, y) = 2xy - x$（先校验拉普拉斯方程：$\\nabla^2 \\varphi = \\frac{\\partial^2 \\varphi}{\\partial x^2} + \\frac{\\partial^2 \\varphi}{\\partial y^2} = 0 + 0 = 0$，确为不可压缩平面势流，从而必存在流函数 $\\psi$）。\n\n由速度势函数定义求 $x$、$y$ 方向流速分量：\n\n$$\nu_x = \\frac{\\partial \\varphi}{\\partial x} = 2y - 1, \\qquad u_y = \\frac{\\partial \\varphi}{\\partial y} = 2x\n$$\n\n将坐标 $(x, y) = (2\\,\\mathrm{m},\\; 5\\,\\mathrm{m})$ 代入得：\n\n$$\nu_x(2, 5) = 2 \\times 5 - 1 = 9\\,\\mathrm{m/s}, \\qquad u_y(2, 5) = 2 \\times 2 = 4\\,\\mathrm{m/s}\n$$\n\n该点合流速大小为：\n\n$$\nu = \\sqrt{u_x^2 + u_y^2} = \\sqrt{9^2 + 4^2} = \\sqrt{81 + 16} = \\sqrt{97} \\approx 9.8489\\,\\mathrm{m/s} \\approx 9.85\\,\\mathrm{m/s}\n$$\n\n（方向与 $+x$ 轴夹角 $\\theta = \\arctan\\frac{4}{9} \\approx 23.96^{\\circ}$。）\n\n**2. 利用柯西—黎曼（Cauchy-Riemann）条件积分求流函数 $\\psi(x, y)$**\n\n由流函数与势函数的正交关系：\n\n$$\n\\frac{\\partial \\psi}{\\partial y} = u_x = 2y - 1, \\qquad \\frac{\\partial \\psi}{\\partial x} = -u_y = -2x\n$$\n\n写出流函数全微分 $\\mathrm{d}\\psi$ 并直接积分：\n\n$$\n\\mathrm{d}\\psi = \\frac{\\partial \\psi}{\\partial x}\\,\\mathrm{d}x + \\frac{\\partial \\psi}{\\partial y}\\,\\mathrm{d}y = -2x\\,\\mathrm{d}x + (2y - 1)\\,\\mathrm{d}y = \\mathrm{d}(-x^2 + y^2 - y)\n$$\n\n积分即得流函数通解：\n\n$$\n\\psi(x, y) = y^2 - y - x^2 + C\\quad (C\\text{ 为任意常数})\n$$",
                "analysisFigures": [],
                "pitfalls": "1. 流函数符号务必写为 **$\\psi$**（切勿把流函数也笔误写成势函数符号 $\\varphi$），且不定积分末尾不要漏写任意常数 $+ C$！\n2. 运用柯西—黎曼方程 $\\frac{\\partial \\psi}{\\partial x} = -u_y = -2x$ 时注意负号，积分后对 $x, y$ 求偏导回代校核一次（$\\frac{\\partial\\psi}{\\partial y} = 2y - 1 = u_x$，$-\\frac{\\partial\\psi}{\\partial x} = 2x = u_y$）确保万无一失。",
                "chapter": 5,
                "kps": ["流函数与势函数", "柯西-黎曼条件", "平面势流速度场"],
                "method": "势函数偏导求流速与柯西—黎曼全微分求流函数法",
                "difficulty": 2,
                "rubric": [
                    {"label": "由 ux = ∂φ/∂x = 2y - 1、uy = ∂φ/∂y = 2x 求出点 (2, 5) 分速 ux = 9 m/s、uy = 4 m/s", "pts": 4},
                    {"label": "求出该点合流速大小 u = √(9² + 4²) = √97 ≈ 9.85 m/s", "pts": 3},
                    {"label": "利用 dψ = -uy dx + ux dy 积分求得流函数表达式 ψ = y² - y - x² + C", "pts": 5}
                ]
            }
        ]
    }


# ==============================================================================
# 2010 EXAM DATA (11 questions, totalScore = 150)
# ==============================================================================

def build_2010_paper() -> dict:
    return {
        "year": 2010,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "全卷共 11 道大题：第 1～2 题为水力学经典定理证明题（12 + 10 = 22 分），第 3～11 题为综合计算题（12 + 15 + 12 + 15 + 13 + 15 + 15 + 15 + 16 = 128 分）。",
            "结合第 4 题与第 8 题参数协调关系，计算统一取重力加速度 $g = 9.80\\,\\mathrm{m/s^2}$，水的密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$（解析同步附 $g = 9.81\\,\\mathrm{m/s^2}$ 对照结果）。"
        ],
        "sections": [
            {
                "id": "proof",
                "title": "一、理论证明题",
                "description": "第 1～2 题（12 + 10 分），共 22 分。",
                "range": [1, 2],
                "totalScore": 22
            },
            {
                "id": "calc",
                "title": "二、综合计算题",
                "description": "第 3～11 题（12×2 + 13×1 + 15×5 + 16×1 分），共 128 分。",
                "range": [3, 11],
                "totalScore": 128
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2010-01",
                "year": 2010,
                "no": 1,
                "type": "proof",
                "score": 12,
                "title": "证明梯形断面明渠水力最佳断面的水力半径等于水深的一半",
                "stem": "证明：梯形断面明渠水力最佳断面的水力半径等于水深的一半。",
                "note": "",
                "figures": [],
                "shortAnswer": "固定过水断面积 A = (b + mh)h 与边坡系数 m，将 b = A/h - mh 代入湿周 χ = b + 2h√(1+m²) = A/h + (2√(1+m²) - m)h，令 dχ/dh = 0 得最佳宽深比 βm = b/h = 2(√(1+m²) - m) 即 A = (2√(1+m²) - m)h²、χmin = (4√(1+m²) - 2m)h = 2A/h，故 Rm = A/χmin = h/2。",
                "judgeAnswer": None,
                "answer": "**证明**：\n设梯形明渠底宽为 $b$，水深为 $h$，边坡系数为 $m$（给定常数），则过水断面积 $A$ 与湿周 $\\chi$ 分别为：\n\n$$\nA = (b + m h) h, \\qquad \\chi = b + 2 h \\sqrt{1 + m^2}\n$$\n\n水力最佳断面的条件是：**当过水断面积 $A$、底坡 $i$ 和糙率 $n$ 一定时，通过流量 $Q = \\frac{1}{n}A R^{2/3} i^{1/2}$ 最大，等价于水力半径 $R = \\frac{A}{\\chi}$ 最大，即湿周 $\\chi$ 最小**。\n\n由面积式解出底宽 $b = \\frac{A}{h} - m h$，代入湿周表达式将 $\\chi$ 表为水深 $h$ 的一元函数（视 $A, m$ 为常数）：\n\n$$\n\\chi(h) = \\frac{A}{h} - m h + 2 h \\sqrt{1 + m^2} = \\frac{A}{h} + \\left(2\\sqrt{1 + m^2} - m\\right) h\n$$\n\n对 $h$ 求一阶导数并令极值条件 $\\frac{\\mathrm{d}\\chi}{\\mathrm{d}h} = 0$：\n\n$$\n\\frac{\\mathrm{d}\\chi}{\\mathrm{d}h} = -\\frac{A}{h^2} + 2\\sqrt{1 + m^2} - m = 0 \\implies A = \\left(2\\sqrt{1 + m^2} - m\\right) h^2\n$$\n\n（且二阶导数 $\\frac{\\mathrm{d}^2 \\chi}{\\mathrm{d}h^2} = \\frac{2A}{h^3} > 0$，确为极小值点。）将 $A = \\left(2\\sqrt{1 + m^2} - m\\right) h^2$ 代回湿周表达式得最小湿周 $\\chi_{\\min}$：\n\n$$\n\\chi_{\\min} = \\left(2\\sqrt{1 + m^2} - m\\right) h + \\left(2\\sqrt{1 + m^2} - m\\right) h = 2\\left(2\\sqrt{1 + m^2} - m\\right) h = \\frac{2A}{h}\n$$\n\n因此，水力最佳断面的水力半径 $R_m$ 为：\n\n$$\nR_m = \\frac{A}{\\chi_{\\min}} = \\frac{\\left(2\\sqrt{1 + m^2} - m\\right) h^2}{2\\left(2\\sqrt{1 + m^2} - m\\right) h} = \\frac{h}{2}\n$$\n\n即证得梯形断面明渠水力最佳断面的水力半径等于水深的一半（包含 $m=0$ 矩形最佳断面作为特例）。",
                "analysis": "**推论与几何意义**：\n由 $A = (b + mh)h = \\left(2\\sqrt{1 + m^2} - m\\right) h^2$ 同时可得梯形水力最佳宽深比：\n\n$$\n\\beta_m = \\frac{b}{h} = 2\\left(\\sqrt{1 + m^2} - m\\right)\n$$\n\n几何上，以水面中点为圆心、以水深的一半 $r = h/2$ 为半径作半圆，水力最佳梯形断面的渠底与两侧边坡恰好同时与该半圆相切！",
                "analysisFigures": [],
                "pitfalls": "证明时务必先说明“**固定过水断面积 $A$ 与边坡系数 $m$ 不变，用 $b = A/h - mh$ 消去变量 $b$**”再对 $h$ 求导！若不消去 $b$ 而误将 $b$ 当常数对 $\\chi = b + 2h\\sqrt{1+m^2}$ 直接求导，会得出荒谬结果；最好顺带验证 $\\frac{\\mathrm{d}^2\\chi}{\\mathrm{d}h^2} = \\frac{2A}{h^3} > 0$ 体现数学严密性。",
                "chapter": 7,
                "kps": ["水力最佳断面", "曼宁公式", "梯形断面水力要素"],
                "method": "面积约束消元求湿周极小值导数证明法",
                "difficulty": 2,
                "rubric": [
                    {"label": "阐述水力最佳断面条件（A、m 一定时 Q 最大等价于湿周 χ 最小）并写出 A、χ 表达式", "pts": 3},
                    {"label": "用 b = A/h - mh 消去 b，对 χ(h) 求导令 dχ/dh = 0 导出 A = (2√(1+m²) - m)h²", "pts": 5},
                    {"label": "计算最小湿周 χmin = 2A/h 并证得水力半径 Rm = A/χmin = h/2", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2010-02",
                "year": 2010,
                "no": 2,
                "type": "proof",
                "score": 10,
                "title": "证明断面比能一定时明渠最大流量相应的水深为临界水深",
                "stem": "证明：当断面比能 $E_s$ 及渠道断面形状、尺寸一定时，最大流量相应的水深是临界水深。",
                "note": "",
                "figures": [],
                "shortAnswer": "由 Es = h + αQ²/(2gA²) 解出 Q² = (2g/α)A²(Es - h)，因 Es 一定且 dA/dh = B（水面宽），令 d(Q²)/dh = (2g/α)[2AB(Es - h) - A²] = 0 得 Es - h = A/(2B)，代回 αQ²/(2gA²) = Es - h 化简即得临界流判据 αQ²B/(gA³) = 1（Fr = 1），故最大流量对应水深即为临界水深 hk。",
                "judgeAnswer": None,
                "answer": "**证明**：\n任意形状明渠过水断面的断面比能（断面单位重量水流相对渠底机械能）定义为：\n\n$$\nE_s = h + \\frac{\\alpha v^2}{2g} = h + \\frac{\\alpha Q^2}{2 g A^2}\n$$\n\n当断面比能 $E_s$ 及渠道断面形状、尺寸一定时，过水断面积 $A = A(h)$ 仅为水深 $h$ 的函数，且微元面积导数等于水面宽度 $\\frac{\\mathrm{d}A}{\\mathrm{d}h} = B$。将上式解出流量平方 $Q^2$ 表为水深 $h \\in (0, E_s)$ 的函数：\n\n$$\nQ^2(h) = \\frac{2g}{\\alpha} A^2(h) (E_s - h)\n$$\n\n因 $Q > 0$，$Q$ 取得最大值等价于 $Q^2$ 取得最大值（曲线形态见解图 2）。对 $h$ 求导并令 $\\frac{\\mathrm{d}(Q^2)}{\\mathrm{d}h} = 0$：\n\n$$\n\\frac{\\mathrm{d}(Q^2)}{\\mathrm{d}h} = \\frac{2g}{\\alpha}\\left[2 A \\frac{\\mathrm{d}A}{\\mathrm{d}h}(E_s - h) - A^2\\right] = \\frac{2g A}{\\alpha}\\left[2 B (E_s - h) - A\\right] = 0\n$$\n\n因过水断面积 $A > 0$，由括号内为零得极值条件：\n\n$$\nE_s - h = \\frac{A}{2 B}\n$$\n\n另一方面，由断面比能定义式有 $E_s - h = \\frac{\\alpha Q^2}{2 g A^2}$，联立两式：\n\n$$\n\\frac{\\alpha Q^2}{2 g A^2} = \\frac{A}{2 B} \\implies \\frac{\\alpha Q^2 B}{g A^3} = 1 \\quad \\left(\\text{即 } Fr = \\frac{v}{\\sqrt{g A / (\\alpha B)}} = 1\\right)\n$$\n\n上式正是明渠**临界水深 $h_k$ 的普遍判别方程**！（且由于端点 $h \\to 0$ 时 $A \\to 0,\\; Q \\to 0$，$h \\to E_s$ 时 $Q \\to 0$，而在 $(0, E_s)$ 内 $Q > 0$ 且有唯一驻点 $h = h_k$，故该驻点必为全局最大值点 $Q = Q_{\\max}$。）证毕。",
                "analysis": "**对偶定理解读**：\n明渠临界流具有著名的两组对偶极值性质：\n1. **流量 $Q$ 一定时**，临界水深 $h_k$ 对应**最小断面比能 $E_{s,\\min}$**；\n2. **断面比能 $E_s$ 一定时**，临界水深 $h_k$ 对应**最大过流能力 $Q_{\\max}$**（宽顶堰自由出流堰顶自动形成临界水深即源于此原理）。\n证明时对 $Q^2(h)$ 求导比直接对含根号的 $Q(h)$ 求导更加简洁清爽！",
                "analysisFigures": [
                    {"src": "figures/q02_sol.png", "caption": "解图 2　断面比能 Es 恒定时流量—水深关系曲线 Q(h) 及其极值点 h = hk"}
                ],
                "pitfalls": "推导中最关键的一步几何微元恒等式是 **$\\frac{\\mathrm{d}A}{\\mathrm{d}h} = B$**（过水断面积对水深的导数等于水面宽 $B$）！务必针对**任意断面形状**用 $A(h)$ 和 $B$ 证明导出通用临界流方程 $\\frac{\\alpha Q^2 B}{g A^3} = 1$，切忌只假设矩形断面 $A = bh$（那样只能得部分特殊情况分）。",
                "chapter": 8,
                "kps": ["断面比能与临界水深", "弗劳德数", "明渠最大流量极值原理"],
                "method": "断面比能反表流量平方求导极值证明法",
                "difficulty": 2,
                "rubric": [
                    {"label": "写出断面比能公式 Es = h + αQ²/(2gA²) 并反解出 Q² = (2g/α)A²(Es - h)", "pts": 3},
                    {"label": "利用几何导数关系 dA/dh = B 对 h 求导令 d(Q²)/dh = 0，导出 Es - h = A/(2B)", "pts": 4},
                    {"label": "代回流速水头整理得出通用临界流方程 αQ²B/(gA³) = 1，说明对应最大流量水深即为临界水深", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2010-03",
                "year": 2010,
                "no": 3,
                "type": "calc",
                "score": 12,
                "title": "薄油膜上匀速运动平板所受黏性阻力反求油的动力黏度",
                "stem": "如图所示有一 $0.8\\,\\mathrm{m} \\times 0.2\\,\\mathrm{m}$ 的平板在油面上作匀速水平运动，已知运动速度 $u = 1\\,\\mathrm{m/s}$，平板与固定边界的距离 $\\delta = 1\\,\\mathrm{mm}$，由平板带动的油的速度成线性分布，平板所受的阻力为 $184\\,\\mathrm{N}$，求油的动力粘度。",
                "note": "",
                "figures": [
                    {"src": "figures/q03_orig.png", "caption": "题 3 图　薄油层表面匀速水平运动平板及线性流速分布"}
                ],
                "shortAnswer": "μ = 1.15 Pa·s（即 1.15 N·s/m²）",
                "judgeAnswer": None,
                "answer": "油的动力黏度为 $\\mu = 1.15\\,\\mathrm{Pa\\cdot s}$（或写作 $1.15\\,\\mathrm{N\\cdot s/m^2}$）。",
                "analysis": "**1. 计算平板与油面接触面积及壁面切应力 $\\tau$**\n\n平板底面与油层接触的面积为：\n\n$$\nA = 0.8 \\times 0.2 = 0.16\\,\\mathrm{m^2}\n$$\n\n平板作匀速水平运动，所受黏性摩擦阻力 $F = 184\\,\\mathrm{N}$，故油层对平板底面的均匀切应力大小为：\n\n$$\n\\tau = \\frac{F}{A} = \\frac{184}{0.16} = 1150\\,\\mathrm{N/m^2} = 1150\\,\\mathrm{Pa}\n$$\n\n**2. 由牛顿内摩擦定律求油的动力黏度 $\\mu$**\n\n因油膜厚度 $\\delta = 1\\,\\mathrm{mm} = 1.0 \\times 10^{-3}\\,\\mathrm{m}$ 内流速呈线性分布（底部固定边界处流速为 $0$，紧贴运动平板底面处流速为 $u = 1\\,\\mathrm{m/s}$），速度梯度为常数：\n\n$$\n\\frac{\\mathrm{d}u}{\\mathrm{d}y} = \\frac{u - 0}{\\delta} = \\frac{1.0}{1.0 \\times 10^{-3}} = 1000\\,\\mathrm{s^{-1}}\n$$\n\n代入牛顿内摩擦定律 $\\tau = \\mu \\frac{\\mathrm{d}u}{\\mathrm{d}y}$，解得油的动力黏度：\n\n$$\n\\mu = \\frac{\\tau}{\\mathrm{d}u/\\mathrm{d}y} = \\frac{F \\delta}{A u} = \\frac{1150}{1000} = 1.15\\,\\mathrm{Pa\\cdot s}\\;(\\text{或 } 1.15\\,\\mathrm{N\\cdot s/m^2})\n$$",
                "analysisFigures": [],
                "pitfalls": "1. 油层厚度 $\\delta = 1\\,\\mathrm{mm} = 10^{-3}\\,\\mathrm{m}$ 务必换算为米，切勿直接代 $1$！\n2. 题 3 图明确显示平板**浮于油面顶部**单侧接触油层（接触面积 $A = 0.16\\,\\mathrm{m^2}$），切勿误当作夹在两油层中间的双面受剪薄板（无需乘 $2$）。",
                "chapter": 1,
                "kps": ["牛顿内摩擦定律", "动力黏度与运动黏度"],
                "method": "牛顿内摩擦定律线性速度梯度求黏度法",
                "difficulty": 1,
                "rubric": [
                    {"label": "计算平板受剪面积 A = 0.16 m² 及切应力 τ = F/A = 1150 Pa", "pts": 4},
                    {"label": "计算线性流速分布的速度梯度 du/dy = u/δ = 1000 s⁻¹", "pts": 4},
                    {"label": "由牛顿内摩擦定律 μ = τ/(du/dy) 解得动力黏度 μ = 1.15 Pa·s（单位正确）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2010-04",
                "year": 2010,
                "no": 4,
                "type": "calc",
                "score": 15,
                "title": "带扩大圆筒双液微压 U 形差压计交界面下降高度计算",
                "stem": "一 U 形差压计如图所示，下端为横截面积等于 $a$ 的玻璃管，顶端为横截面积 $A = 50a$ 的圆筒，左支内盛水（$\\rho_w = 1000\\,\\mathrm{kg/m^3}$），右支内盛油（$\\rho_o = 950\\,\\mathrm{kg/m^3}$），左右支顶端与欲测压差处相接。当 $p_1 = p_2$ 时，右支管内的油水交界面在 $x\\text{—}x$ 水平面处。当 $(p_2 - p_1)$ 为 $218.05\\,\\mathrm{Pa}$ 时，试计算右支管内油水交界面下降多少？",
                "note": "",
                "figures": [
                    {"src": "figures/q04_orig.png", "caption": "题 4 图　顶端带扩大圆筒的双液微压 U 形差压计"}
                ],
                "shortAnswer": "0.25 m（即 25.0 cm；若取 g=9.81 m/s² 则为 0.2497 m ≈ 25.0 cm）",
                "judgeAnswer": None,
                "answer": "当 $(p_2 - p_1) = 218.05\\,\\mathrm{Pa}$ 时，右支管内油水交界面下降 **$\\Delta h = 0.25\\,\\mathrm{m}$（即 $25.0\\,\\mathrm{cm}$）**。",
                "analysis": "**1. 建立初始平衡态（$p_1 = p_2$）液面高程关系**\n\n当 $p_1 = p_2$ 时，右支细管内油—水交界面位于水平面 $x\\text{—}x$。设此时左支扩大圆筒内水面距 $x\\text{—}x$ 面的高度为 $z_{01}$，右支扩大圆筒内油面距 $x\\text{—}x$ 面的高度为 $z_{02}$。过 $x\\text{—}x$ 等压面列静水压强平衡方程：\n\n$$\np_1 + \\rho_w g z_{01} = p_2 + \\rho_o g z_{02} \\implies \\rho_w g z_{01} = \\rho_o g z_{02} \\quad (1)\n$$\n\n**2. 建立加压后（$p_2 > p_1$）不可压缩体积守恒与新等压面平衡方程**\n\n设当 $p_2 - p_1 = 218.05\\,\\mathrm{Pa}$ 时，右支细管（截面积 $a$）内的油—水交界面由 $x\\text{—}x$ 向下移动了 $\\Delta h$ 到达新水平面 $1\\text{—}1$（液面位移关系见解图 4）。\n\n由不可压缩液体体积守恒，右支细管排入左支的水体积为 $a \\Delta h$，故左支扩大圆筒（截面积 $A = 50a$）水面较初始位置**上升** $\\delta z = \\frac{a}{A}\\Delta h = \\frac{\\Delta h}{50}$；同理，右支扩大圆筒油面较初始位置**下降** $\\delta z = \\frac{a}{A}\\Delta h = \\frac{\\Delta h}{50}$。\n\n因此，相对于新油—水交界面（新等压面 $1\\text{—}1$）：\n- 左侧水柱总高度变为：$H_w = z_{01} + \\frac{\\Delta h}{50} + \\Delta h = z_{01} + \\frac{51}{50}\\Delta h$；\n- 右侧油柱总高度变为：$H_o = z_{02} - \\frac{\\Delta h}{50} + \\Delta h = z_{02} + \\frac{49}{50}\\Delta h$。\n\n过新等压面 $1\\text{—}1$ 列静水压强平衡方程：\n\n$$\np_1 + \\rho_w g \\left(z_{01} + \\frac{51}{50}\\Delta h\\right) = p_2 + \\rho_o g \\left(z_{02} + \\frac{49}{50}\\Delta h\\right) \\quad (2)\n$$\n\n**3. 联立消去初始高度 $z_{01}, z_{02}$，精确解出下降量 $\\Delta h$**\n\n将式 (1) $\\rho_w g z_{01} = \\rho_o g z_{02}$ 代入式 (2) 消去初始项，整理得双液微压计压差放大公式：\n\n$$\np_2 - p_1 = g \\left(\\frac{51}{50}\\rho_w - \\frac{49}{50}\\rho_o\\right)\\Delta h = g \\left[\\rho_w - \\rho_o + \\frac{1}{50}(\\rho_w + \\rho_o)\\right]\\Delta h\n$$\n\n代入 $\\rho_w = 1000\\,\\mathrm{kg/m^3}$，$\\rho_o = 950\\,\\mathrm{kg/m^3}$，$g = 9.80\\,\\mathrm{m/s^2}$，$p_2 - p_1 = 218.05\\,\\mathrm{Pa}$：\n\n$$\n\\frac{51}{50}\\rho_w - \\frac{49}{50}\\rho_o = 1.02 \\times 1000 - 0.98 \\times 950 = 1020 - 931 = 89.0\\,\\mathrm{kg/m^3}\n$$\n\n$$\n\\Delta h = \\frac{p_2 - p_1}{89.0 \\times g} = \\frac{218.05}{89.0 \\times 9.80} = \\frac{218.05}{872.20} = 0.2500\\,\\mathrm{m} = 25.0\\,\\mathrm{cm}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $\\Delta h = 218.05 / 873.09 = 0.2497\\,\\mathrm{m} \\approx 25.0\\,\\mathrm{cm}$。）",
                "analysisFigures": [
                    {"src": "figures/q04_sol.png", "caption": "解图 4　双液扩大圆筒微压计新旧等压面位移与液面升降几何关系"}
                ],
                "pitfalls": "**切忌忽略扩大圆筒内液面的微小升降 $\\pm \\frac{a}{A}\\Delta h = \\pm \\frac{\\Delta h}{50}$！** 虽然面积比 $\\frac{a}{A} = \\frac{1}{50}$ 看似只有 $2\\%$，但由于水油密度差极小（$\\rho_w - \\rho_o = 50\\,\\mathrm{kg/m^3}$），扩大筒液面升降贡献项 $\\frac{\\rho_w + \\rho_o}{50} = 39\\,\\mathrm{kg/m^3}$ 占总系数 $89\\,\\mathrm{kg/m^3}$ 的 **$44\\%$** 之巨！若漏算扩大筒液面变化误按 $(\\rho_w - \\rho_o)g\\Delta h$ 计算，结果将错成 $0.445\\,\\mathrm{m}$。",
                "chapter": 2,
                "kps": ["多液层压差计", "微压计原理", "等压面性质"],
                "method": "初末两态等压面相减与体积守恒法",
                "difficulty": 4,
                "rubric": [
                    {"label": "列出初始平衡条件 ρw·g·z01 = ρo·g·z02", "pts": 3},
                    {"label": "由体积守恒求出左右扩大筒液面变化 ±Δh/50，确定新交界面以上水柱高 z01+51Δh/50 与油柱高 z02+49Δh/50", "pts": 6},
                    {"label": "列新等压面方程消去初态项，代入 p2-p1=218.05 Pa 解出交界面下降量 Δh = 0.25 m（25 cm）", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2010-05",
                "year": 2010,
                "no": 5,
                "type": "calc",
                "score": 12,
                "title": "盛水变截面圆柱圆锥组合容器渐缩壁面 ABCD 竖向静水总压力计算",
                "stem": "盛水的变截面圆柱体容器，如图所示，试求作用于渐缩段 $ABCD$ 上的竖向分力。",
                "note": "",
                "figures": [
                    {"src": "figures/q05_orig.png", "caption": "题 5 图　盛水变截面圆柱—圆锥台容器尺寸剖面图"}
                ],
                "shortAnswer": "Pz = (86/3)πρg ≈ 882.58 kN（若取 g=9.81 m/s² 则为 883.48 kN），方向竖直向上。",
                "judgeAnswer": None,
                "answer": "作用于圆锥台渐缩壁面 $ABCD$ 上的静水总压力竖向分力大小为 **$882.58\\,\\mathrm{kN}$**（精确值 $\\frac{86}{3}\\pi \\rho g$；若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $883.48\\,\\mathrm{kN}$），方向**竖直向上**。",
                "analysis": "**1. 判断渐缩壁面 $ABCD$ 压力体性质与竖向力方向**\n\n由题 5 图轴对称容器尺寸可知：上部小圆筒直径 $d_1 = 2\\,\\mathrm{m}$（半径 $r_1 = 1\\,\\mathrm{m}$）、高度 $h_1 = 3\\,\\mathrm{m}$；中部圆锥台渐缩壁面 $ABCD$ 竖直高度 $h_2 = 1\\,\\mathrm{m}$，半径由 $r_1 = 1\\,\\mathrm{m}$ 扩大至下部大圆筒半径 $r_2 = \\frac{6}{2} = 3\\,\\mathrm{m}$。\n\n水体位于圆锥台内壁 $ABCD$ 的**下方**，壁面法向受压方向斜向上，故 $ABCD$ 与其铅直投影柱面（内径 $2\\,\\mathrm{m}$、外径 $6\\,\\mathrm{m}$）及自由液面延长面所围成的环形空间无水，属于**虚压力体**（见解图 5），作用于壁面 $ABCD$ 上的竖向分力 $P_z$ **方向竖直向上**。\n\n**2. 计算环形虚压力体体积 $V_z$**\n\n- **方法一（立体几何分块相减法）**：\n  外圆柱（半径 $r_2 = 3\\,\\mathrm{m}$，自 $BD$ 平面水深 $H_2 = 3 + 1 = 4\\,\\mathrm{m}$ 至自由液面）总体积为：\n\n$$\nV_{\\text{外柱}} = \\pi r_2^2 H_2 = \\pi \\times 3^2 \\times 4 = 36\\pi\\,\\mathrm{m^3}\n$$\n\n  减去中央上部小圆柱水体体积 $V_{\\text{内柱}} = \\pi r_1^2 h_1 = \\pi \\times 1^2 \\times 3 = 3\\pi\\,\\mathrm{m^3}$，再减去 $ABCD$ 下方圆台水体体积 $V_{\\text{圆台}} = \\frac{1}{3}\\pi h_2 (r_1^2 + r_1 r_2 + r_2^2) = \\frac{1}{3}\\pi \\times 1 \\times (1^2 + 1 \\times 3 + 3^2) = \\frac{13}{3}\\pi\\,\\mathrm{m^3}$：\n\n$$\nV_z = V_{\\text{外柱}} - V_{\\text{内柱}} - V_{\\text{圆台}} = 36\\pi - 3\\pi - \\frac{13}{3}\\pi = \\left(33 - \\frac{13}{3}\\right)\\pi = \\frac{86}{3}\\pi \\approx 90.0590\\,\\mathrm{m^3}\n$$\n\n- **方法二（极坐标圆环微元直接积分校核，更快更不易错！）**：\n  在半径 $r \\in [1,\\; 3]$ 处，锥壁距自由水面的淹深线性分布为 $h(r) = 3 + \\frac{r - 1}{3 - 1}\\times 1 = 2.5 + 0.5 r$，水平投影微圆环面积 $\\mathrm{d}A_z = 2\\pi r\\,\\mathrm{d}r$：\n\n$$\nV_z = \\int_1^3 h(r)\\cdot 2\\pi r\\,\\mathrm{d}r = 2\\pi \\int_1^3 (2.5 r + 0.5 r^2)\\,\\mathrm{d}r = 2\\pi\\left[1.25(3^2 - 1^2) + \\frac{3^3 - 1^3}{6}\\right] = 2\\pi\\left(10 + \\frac{13}{3}\\right) = \\frac{86}{3}\\pi\\,\\mathrm{m^3}\n$$\n\n**3. 计算竖向静水总压力 $P_z$**\n\n取 $\\rho = 1000\\,\\mathrm{kg/m^3}$，$g = 9.80\\,\\mathrm{m/s^2}$：\n\n$$\nP_z = \\rho g V_z = 1000 \\times 9.80 \\times \\frac{86}{3}\\pi \\approx 882578\\,\\mathrm{N} \\approx 882.58\\,\\mathrm{kN}\\;(\\text{方向竖直向上})\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $P_z = 1000 \\times 9.81 \\times \\frac{86}{3}\\pi \\approx 883.48\\,\\mathrm{kN}$，方向竖直向上。）",
                "analysisFigures": [
                    {"src": "figures/q05_sol.png", "caption": "解图 5　变截面圆柱圆锥容器渐缩段 ABCD 上方环形虚压力体分解图"}
                ],
                "pitfalls": "1. 容器是**三维轴对称旋转体**（题干写明“变截面圆柱体容器”），切忌当成二维平面梯形断面按单位宽度算面积！\n2. 最下面 $2\\,\\mathrm{m}$ 高的大圆柱段位于 $BD$ 平面以下，与锥壁 $ABCD$ 的压力体无关（只须算到 $BD$ 所在深度 $4\\,\\mathrm{m}$ 即可，或如原总体积 $54\\pi$ 减去底柱 $18\\pi$ 亦等价得 $36\\pi$），且务必写明方向**竖直向上**！",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力", "压力体与铅直分力", "轴对称旋转曲面水压力"],
                "method": "轴对称环形虚压力体体积法（或微环积分法）",
                "difficulty": 3,
                "rubric": [
                    {"label": "正确判定渐缩段 ABCD 受水体向上托力，其压力体为环形虚压力体且竖向分力方向竖直向上", "pts": 3},
                    {"label": "运用圆台体积相减或极坐标积分准确算出虚压力体体积 Vz = (86/3)π ≈ 90.06 m³", "pts": 6},
                    {"label": "算出竖向分力大小 Pz = ρgVz ≈ 882.58 kN（或 883.48 kN）", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2010-06",
                "year": 2010,
                "no": 6,
                "type": "calc",
                "score": 15,
                "title": "直角 L 形自动溢水阀门临界开启水深推导计算",
                "stem": "如图所示的 L 形状阀门，已知圆弧半径为 $L$，当上游水深 $h$ 超过某高度时，阀门会自动开启溢水，如不计铰的阻力和阀门自重，试求使阀门开启的临界水深 $h$。",
                "note": "",
                "figures": [
                    {"src": "figures/q06_orig.png", "caption": "题 6 图　直角 L 形自动开启溢水阀门构造与受力示意"}
                ],
                "shortAnswer": "h = √3 L ≈ 1.732 L",
                "judgeAnswer": None,
                "answer": "使 L 形阀门自动开启溢水的临界水深为 **$h = \\sqrt{3}\\,L \\approx 1.732\\,L$**。",
                "analysis": "**1. 分析直角 L 形阀门两翼板上的静水总压力与作用线**\n\n由题 6 图构造可知，直角 L 形阀门拐角铰接于轴 $O$，由铅直挡水翼板（受压水深为 $h$）与水平底翼板（长等于下方溢流圆弧半径 $L$，右端平时受顶部限位挡块止水）刚性正交组成。取单位门宽 $b = 1\\,\\mathrm{m}$ 分析（受力分布与力臂见解图 6）：\n\n1. **铅直翼板所受水平静水总压力 $F_x$**：\n   压强自水面 $0$ 至铰轴深度 $\\rho g h$ 呈三角形分布，合力大小及距铰轴 $O$ 的竖直力臂 $e_x$ 为：\n\n$$\nF_x = \\frac{1}{2}\\rho g h^2 b\\;(\\text{水平向右}), \\qquad e_x = \\frac{h}{3}\n$$\n\n   $F_x$ 对铰轴 $O$ 产生**顺时针方向的开启力矩** $M_{\\text{开}} = F_x e_x$（使水平翼板向下摆入圆弧槽、铅直翼板向右倾倒溢水）。\n\n2. **水平翼板所受铅直静水总压力 $F_z$**：\n   水平翼板全长 $L$ 处于水深 $h$ 同一水平面上，下表面承受水体向上的均匀静水压强 $p = \\rho g h$（右侧圆弧外通大气），合力大小及距铰轴 $O$ 的水平力臂 $e_z$ 为：\n\n$$\nF_z = (\\rho g h)(b L) = \\rho g h L b\\;(\\text{竖直向上}), \\qquad e_z = \\frac{L}{2}\n$$\n\n   $F_z$ 对铰轴 $O$ 产生**逆时针方向的闭合力矩** $M_{\\text{闭}} = F_z e_z$（在 $h$ 较小时将水平翼板右端向上顶紧限位挡块保持关闭）。\n\n**2. 列绕拐角铰轴 $O$ 的临界力矩平衡方程求 $h$**\n\n当上游水深升至临界开启水深 $h$ 时，右端限位挡块接触反力恰好降为零，不计阀门自重与铰轴摩擦，顺时针开启力矩与逆时针闭合力矩相等：\n\n$$\n\\sum M_O = 0 \\implies F_x \\cdot \\frac{h}{3} = F_z \\cdot \\frac{L}{2}\n$$\n\n代入 $F_x$、$F_z$ 表达式：\n\n$$\n\\left(\\frac{1}{2}\\rho g h^2 b\\right)\\cdot\\frac{h}{3} = (\\rho g h L b)\\cdot\\frac{L}{2}\n$$\n\n约去公因子 $\\frac{1}{2}\\rho g b h$（$h > 0$），立得：\n\n$$\n\\frac{h^2}{3} = L^2 \\implies h = \\sqrt{3}\\,L \\approx 1.732\\,L\n$$\n\n（物理验证：当水深超过 $\\sqrt{3}\\,L$ 时，$M_{\\text{开}} \\propto h^3$ 的增长快于 $M_{\\text{闭}} \\propto h$，顺时针力矩占优，阀门自动开启泄洪。）",
                "analysisFigures": [
                    {"src": "figures/q06_sol.png", "caption": "解图 6　直角 L 形阀门铅直板三角形荷载与水平板矩形荷载对铰 O 的力矩平衡"}
                ],
                "pitfalls": "1. 下方半径为 $L$ 的 $1/4$ 圆弧是固定混凝土溢流槽壁（给出了水平门叶长度恰为 $L$ 以及阀门向下翻转开启的避让空间），受压转动的阀门本身是由垂直板与水平板构成的**直角平面 L 形门**，切勿误把固定圆弧槽壁当成曲面闸门去算曲面压力体！\n2. 最终化简结果务必写准字母 **$h = \\sqrt{3}\\,L$**。",
                "chapter": 2,
                "kps": ["平面与曲面静水总压力", "自动开启闸门力矩平衡"],
                "method": "直角折板静水荷载分解与铰轴力矩平衡法",
                "difficulty": 3,
                "rubric": [
                    {"label": "正确求出铅直翼板水平水压力 Fx = ρgh²b/2 及其对铰 O 的力臂 ex = h/3", "pts": 5},
                    {"label": "正确求出水平翼板向上水压力 Fz = ρghLb 及其对铰 O 的力臂 ez = L/2", "pts": 5},
                    {"label": "列出临界开启力矩平衡方程 Fx·(h/3) = Fz·(L/2)，解得临界水深 h = √3 L", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2010-07",
                "year": 2010,
                "no": 7,
                "type": "calc",
                "score": 13,
                "title": "水平匀加速直线运动小直径 U 形管液面高差求加速度表达式",
                "stem": "装有液体的小直径 U 型管，沿 $x$ 方向加速运动，如图所示，设已知液面高差 $h$，U 型管水平段长 $L$，试求加速度 $a$ 的表达式。",
                "note": "",
                "figures": [
                    {"src": "figures/q07_orig.png", "caption": "题 7 图　沿 +x 方向水平匀加速运动的小直径 U 形管加速计"}
                ],
                "shortAnswer": "a = (h / L) g",
                "judgeAnswer": None,
                "answer": "U 形管沿 $+x$ 方向运动的水平加速度表达式为：\n\n$$\na = \\frac{h}{L}g\n$$",
                "analysis": "**方法一：由欧拉流体相对平衡微分方程推导（标准规范解法）**\n\n建立如题 7 图所示随 U 形管一起平动的非惯性直角坐标系 $Oxz$（$x$ 轴水平向右与加速度 $\\vec{a}$ 同向，$z$ 轴竖直向上）。处于相对静止状态的液体同时受重力与达朗贝尔惯性力作用，单位质量力分量为：\n\n$$\nf_x = -a, \\qquad f_y = 0, \\qquad f_z = -g\n$$\n\n代入流体平衡微分方程 $\\mathrm{d}p = \\rho (f_x\\,\\mathrm{d}x + f_y\\,\\mathrm{d}y + f_z\\,\\mathrm{d}z)$：\n\n$$\n\\mathrm{d}p = \\rho (-a\\,\\mathrm{d}x - g\\,\\mathrm{d}z)\n$$\n\n连接左右两竖直细管液面（坐标分别为 $A(0, z_A)$ 与 $B(L, z_B)$，其中液面高差 $z_A - z_B = h$）的假想自由等压面满足 $\\mathrm{d}p = 0$（两开口端均通大气，$p_A = p_B = p_a$），对微分方程从左管液面 $(0, z_A)$ 积分至右管液面 $(L, z_B)$：\n\n$$\n\\int_{p_A}^{p_B} \\mathrm{d}p = -\\rho a \\int_0^L \\mathrm{d}x - \\rho g \\int_{z_A}^{z_B} \\mathrm{d}z = 0\n$$\n\n$$\n-\\rho a L - \\rho g (z_B - z_A) = 0 \\implies \\rho a L = \\rho g (z_A - z_B) = \\rho g h\n$$\n\n解得水平加速度表达式：\n\n$$\na = \\frac{h}{L}g\n$$\n\n**方法二：水平管段液柱牛顿第二定律直接校核**\n\n取底部水平管段长 $L$、截面积 $A_0$ 的液柱为隔离体：左端受压强 $p_1 = \\rho g z_A$，右端受压强 $p_2 = \\rho g z_B$，液柱质量 $m = \\rho A_0 L$。由牛顿第二定律 $F_x = m a$：\n\n$$\n(p_1 - p_2) A_0 = \\rho g (z_A - z_B) A_0 = (\\rho A_0 L) a \\implies a = \\frac{h}{L}g\n$$\n\n（极限物理检验：当静止 $a = 0$ 时液面高差 $h = 0$，量纲 $[a] = [g] = \\mathrm{L\\,T^{-2}}$，完全自洽！）",
                "analysisFigures": [],
                "pitfalls": "**务必用极限法检验分子分母位置，严防把 $\\frac{h}{L}g$ 颠倒错写成 $\\frac{L}{h}g$！** 由等压面倾角 $\\tan\\theta = \\frac{|\\mathrm{d}z|}{\\mathrm{d}x} = \\frac{a}{g} = \\frac{h}{L}$，竖直高差 $h$ 在分子、水平间距 $L$ 在分母（若写反成 $\\frac{L}{h}g$，当液面平齐 $h \\to 0$ 时竟得出 $a \\to \\infty$，一秒即可识破错误！）。",
                "chapter": 2,
                "kps": ["液体相对平衡", "等加速水平运动容器", "欧拉平衡微分方程"],
                "method": "达朗贝尔惯性质量力与等压面微分方程法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确写出随动参考系下单位质量力分量 fx = -a、fy = 0、fz = -g", "pts": 4},
                    {"label": "代入欧拉平衡微分方程 dp = ρ(-a dx - g dz) 并结合两支管开口等压条件积分", "pts": 5},
                    {"label": "由 zA - zB = h 准确导出加速度表达式 a = (h/L)g（分子分母无颠倒）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2010-08",
                "year": 2010,
                "no": 8,
                "type": "calc",
                "score": 15,
                "title": "密闭受压盛水容器底部倾斜细管自由出流流量计算",
                "stem": "一盛水密封容器，液面上气体的相对压强 $p_0 = 0.2$ 个大气压，在容器底部接一段管路，管长 $L = 4\\,\\mathrm{m}$，与水平面夹角为 $30^{\\circ}$，管径 $d = 10\\,\\mathrm{mm}$，若管路进口断面到液面的水头 $H = 5\\,\\mathrm{m}$，已知管道沿程阻力系数为 $0.02$，管道进口局部阻力系数为 $0.5$，求流量 $Q$（容器内水面保持不变，容器内水流速度近似为零）。",
                "note": "",
                "figures": [
                    {"src": "figures/q08_orig.png", "caption": "题 8 图　密闭加压容器底部接 30° 向下倾斜出流短管"}
                ],
                "shortAnswer": "Q ≈ 3.38×10⁻⁴ m³/s（即 0.338 L/s，按工程大气压 pa=98 kPa 即 p0/(ρg)=2.0 m 计；若按标准大气压 101.325 kPa 计则为 3.40×10⁻⁴ m³/s）",
                "judgeAnswer": None,
                "answer": "管道自由出流的体积流量为 **$Q \\approx 3.38 \\times 10^{-4}\\,\\mathrm{m^3/s}$（即 $0.338\\,\\mathrm{L/s}$）**（按工程大气压 $1\\,\\mathrm{at} = 98\\,\\mathrm{kPa}$ 即 $10\\,\\mathrm{m}$ 水柱计；若按物理标准大气压 $101.325\\,\\mathrm{kPa}$ 计则为 $3.40 \\times 10^{-4}\\,\\mathrm{m^3/s}$）。",
                "analysis": "**1. 确定容器液面至斜管出口断面的总作用水头 $H_0$**\n\n以向下倾斜管道（倾角 $\\theta = 30^{\\circ}$）的出口断面 $2\\text{—}2$ 形心所在水平面为基准面（$z_2 = 0$，出口自由射流通大气故表压 $p_2 = 0$）：\n- 管路进口断面距出口断面的铅直高差为：$L \\sin 30^{\\circ} = 4 \\times 0.5 = 2.0\\,\\mathrm{m}$；\n- 容器内自由液面 $1\\text{—}1$ 距进口断面的水深为 $H = 5.0\\,\\mathrm{m}$，故液面相对出口基准面的位置高程为：$z_1 = H + L\\sin 30^{\\circ} = 5.0 + 2.0 = 7.0\\,\\mathrm{m}$；\n- 水力学工程计算中，$1$ 个工程大气压对应 $10\\,\\mathrm{m}$ 水柱（$p_a = 98\\,\\mathrm{kPa}$，$g = 9.80\\,\\mathrm{m/s^2}$），故液面上气体相对压强 $p_0 = 0.2$ 个大气压折算水柱水头为：\n\n$$\n\\frac{p_0}{\\rho g} = 0.2 \\times 10.0 = 2.0\\,\\mathrm{m}\n$$\n\n因此，全系统总作用水头为：\n\n$$\nH_0 = z_1 + \\frac{p_0}{\\rho g} = 7.0 + 2.0 = 9.00\\,\\mathrm{m}\n$$\n\n**2. 列 $1\\text{—}1$ 至出口 $2\\text{—}2$ 的恒定总流能量方程求流速 $v$ 与流量 $Q$**\n\n容器内水流速度近似为零（$v_1 \\approx 0$），取出口动能修正系数 $\\alpha_2 = 1.0$，管径 $d = 10\\,\\mathrm{mm} = 0.01\\,\\mathrm{m}$，进口局部阻力系数 $\\zeta_{\\text{进}} = 0.5$，沿程阻力系数 $\\lambda = 0.02$：\n\n$$\nz_1 + \\frac{p_0}{\\rho g} + 0 = 0 + 0 + \\frac{\\alpha_2 v^2}{2g} + \\left(\\zeta_{\\text{进}} + \\lambda \\frac{L}{d}\\right)\\frac{v^2}{2g}\n$$\n\n计算系统总阻力系数（含出口动能项 $1.0$）：\n\n$$\n1 + \\zeta_{\\text{进}} + \\lambda \\frac{L}{d} = 1 + 0.5 + 0.02 \\times \\frac{4.0}{0.01} = 1.5 + 8.0 = 9.5\n$$\n\n解得管内平均流速 $v$（取 $g = 9.80\\,\\mathrm{m/s^2}$）：\n\n$$\nv = \\sqrt{\\frac{2 g H_0}{1 + \\zeta_{\\text{进}} + \\lambda\\frac{L}{d}}} = \\sqrt{\\frac{2 \\times 9.80 \\times 9.00}{9.5}} = \\sqrt{18.5684} \\approx 4.3091\\,\\mathrm{m/s} \\approx 4.31\\,\\mathrm{m/s}\n$$\n\n通过管道的体积流量 $Q$ 为：\n\n$$\nQ = \\frac{\\pi}{4}d^2 v = \\frac{\\pi}{4} \\times 0.01^2 \\times 4.3091 \\approx 3.384 \\times 10^{-4}\\,\\mathrm{m^3/s} \\approx 3.38 \\times 10^{-4}\\,\\mathrm{m^3/s}\\;(\\text{即 } 0.338\\,\\mathrm{L/s})\n$$\n\n（注：若按物理标准大气压 $p_a = 101.325\\,\\mathrm{kPa}$ 或 $100\\,\\mathrm{kPa}$ 折算，$H_0 = 9.07\\,\\mathrm{m}$ 或 $9.04\\,\\mathrm{m}$，$v = 4.33\\,\\mathrm{m/s}$ 或 $4.32\\,\\mathrm{m/s}$，$Q = 3.40 \\times 10^{-4}\\,\\mathrm{m^3/s}$ 或 $3.39 \\times 10^{-4}\\,\\mathrm{m^3/s}$，工程精度高度一致。）",
                "analysisFigures": [],
                "pitfalls": "1. 斜管向下倾斜 $30^{\\circ}$ 延伸了 $L = 4\\,\\mathrm{m}$，使出口比进口又降低了 $L\\sin 30^{\\circ} = 2.0\\,\\mathrm{m}$，故总位置高差是 $5.0 + 2.0 = 7.0\\,\\mathrm{m}$，切勿漏加这 $2.0\\,\\mathrm{m}$！\n2. 管道直接排入大气（自由出流），不是淹没入下游水池，能量方程右端必须保留出口动能项 $\\frac{v^2}{2g}$（系数 $+1$），而无须再重复加淹没出口损失系数！",
                "chapter": 6,
                "kps": ["简单短管水力计算", "恒定总流能量方程", "沿程与局部损失"],
                "method": "加压短管自由出流总水头能量方程法",
                "difficulty": 2,
                "rubric": [
                    {"label": "计入斜管高差 L·sin30° = 2 m 与液面气压水头 p0/(ρg) ≈ 2 m，求得总作用水头 H0 = 9.0 m", "pts": 5},
                    {"label": "正确列出自由出流短管能量方程 H0 = (1 + ζ进 + λL/d)·v²/(2g)，算得总系数 9.5", "pts": 6},
                    {"label": "解得管内流速 v ≈ 4.31 m/s 及流量 Q ≈ 3.38×10⁻⁴ m³/s", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2010-09",
                "year": 2010,
                "no": 9,
                "type": "calc",
                "score": 15,
                "title": "连接两水池水平有压短管流量与中点测压管水头计算",
                "stem": "有一长度为 $L = 10\\,\\mathrm{m}$ 的有压管道连结两水池（水池体积较大），管径 $d = 0.1\\,\\mathrm{m}$，两水池水位差 $Z = 3.5\\,\\mathrm{m}$，在 $L/2$ 处装一测压管，已知管道沿程阻力系数为 $0.02$，求：\n\n（1）管道中通过的流量；\n\n（2）测压管水头 $H$。",
                "note": "",
                "figures": [
                    {"src": "figures/q09_orig.png", "caption": "题 9 图　两水池间连通短管及中点测压管水头 H 示意"}
                ],
                "shortAnswer": "（1）流量 Q ≈ 0.0348 m³/s（即 34.8 L/s，管内流速 v ≈ 4.43 m/s）；（2）中点测压管水头（高于下游水池水面高度）H = 1.00 m。",
                "judgeAnswer": None,
                "answer": "（1）管道中通过的流量：$Q \\approx 0.0348\\,\\mathrm{m^3/s}$（即 $34.8\\,\\mathrm{L/s}$）；\n\n（2）管道中点（$L/2$ 处）相对下游水面的测压管水头：**$H = 1.00\\,\\mathrm{m}$**。",
                "analysis": "**（1）列上下游两水池自由水面能量方程求管道流量 $Q$**\n\n以**下游水池自由水面**为基准面（$z_{\\text{下}} = 0$），则上游水池自由水面高程为 $z_{\\text{上}} = Z = 3.5\\,\\mathrm{m}$；两水池体积较大，水面行近流速 $v_{\\text{上}} \\approx v_{\\text{下}} \\approx 0$，水面表压均为零。\n\n管道与大水池平齐直角连接，按水力学标准局部阻力系数：直角进口局部阻力系数 $\\zeta_{\\text{进}} = 0.5$，淹没入下游水池出口局部阻力系数 $\\zeta_{\\text{出}} = 1.0$，全管沿程阻力系数项为 $\\lambda \\frac{L}{d} = 0.02 \\times \\frac{10}{0.1} = 2.0$。\n\n对上下游水面列恒定总流能量方程（总水头线与测压管水头线见解图 9）：\n\n$$\nZ = \\left(\\zeta_{\\text{进}} + \\lambda \\frac{L}{d} + \\zeta_{\\text{出}}\\right)\\frac{v^2}{2g} = (0.5 + 2.0 + 1.0)\\frac{v^2}{2g} = 3.5\\,\\frac{v^2}{2g}\n$$\n\n代入水位差 $Z = 3.5\\,\\mathrm{m}$，立得管道流速水头恰为整数：\n\n$$\n\\frac{v^2}{2g} = \\frac{3.5}{3.5} = 1.00\\,\\mathrm{m}\n$$\n\n取 $g = 9.80\\,\\mathrm{m/s^2}$，求得管内平均流速 $v$ 与流量 $Q$：\n\n$$\nv = \\sqrt{2 g \\times 1.00} = \\sqrt{19.60} \\approx 4.4272\\,\\mathrm{m/s} \\approx 4.43\\,\\mathrm{m/s}\n$$\n\n$$\nQ = \\frac{\\pi}{4}d^2 v = \\frac{\\pi}{4} \\times 0.1^2 \\times 4.4272 \\approx 0.03477\\,\\mathrm{m^3/s} \\approx 0.0348\\,\\mathrm{m^3/s}\n$$\n\n（若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $v = 4.429\\,\\mathrm{m/s}$，$Q = 0.03479\\,\\mathrm{m^3/s} \\approx 0.0348\\,\\mathrm{m^3/s}$。）\n\n**（2）求 $L/2$ 中点断面处的测压管水头 $H$**\n\n由题 9 图尺寸标示，所求 $H$ 为中点测压管液面高于下游水池自由水面（基准面 $z_{\\text{下}} = 0$）的高度，即中点断面相对基准面的测压管水头 $H = z_m + \\frac{p_m}{\\rho g}$。\n\n对上游水池液面与管道中点断面 $m\\text{—}m$（距进口 $\\frac{L}{2} = 5\\,\\mathrm{m}$，取 $\\alpha_m = 1.0$）列能量方程：\n\n$$\nZ = H + \\frac{v^2}{2g} + \\left(\\zeta_{\\text{进}} + \\lambda \\frac{L/2}{d}\\right)\\frac{v^2}{2g}\n$$\n\n其中前半段沿程系数 $\\lambda \\frac{L/2}{d} = 0.02 \\times \\frac{5}{0.1} = 1.0$。将 $Z = 3.5\\,\\mathrm{m}$、$\\zeta_{\\text{进}} = 0.5$ 及 $\\frac{v^2}{2g} = 1.00\\,\\mathrm{m}$ 代入：\n\n$$\n3.5 = H + 1.00 + (0.5 + 1.0) \\times 1.00 = H + 2.50 \\implies H = 1.00\\,\\mathrm{m}\n$$\n\n（反向校核：由中点 $m\\text{—}m$ 至下游水池列能量方程，$H + \\frac{v^2}{2g} = \\left(\\lambda\\frac{L/2}{d} + \\zeta_{\\text{出}}\\right)\\frac{v^2}{2g} = (1.0 + 1.0)\\times 1.00 = 2.00\\,\\mathrm{m} \\implies H = 2.00 - 1.00 = 1.00\\,\\mathrm{m}$，完全吻合！）",
                "analysisFigures": [
                    {"src": "figures/q09_sol.png", "caption": "解图 9　连通两水池有压短管总水头线、测压管水头线与中点水头 H = 1.00 m"}
                ],
                "pitfalls": "1. 必须牢记水池接圆管的两个基本局部损失系数：**直角进口 $\\zeta_{\\text{进}} = 0.5$，淹没出口 $\\zeta_{\\text{出}} = 1.0$**！千万不可将两者记反（若误记为进口 $1.0$、出口 $0.5$，虽然总和仍是 $1.5$ 不影响第一问流量，但第二问前半段损失会多算 $0.5\\,\\mathrm{m}$ 导致 $H$ 算错为 $0.5\\,\\mathrm{m}$）！\n2. 流量 $Q$ 的单位为 **$\\\\mathrm{m^3/s}$**，注意书写规范。",
                "chapter": 6,
                "kps": ["简单短管水力计算", "总水头线与测压管水头线", "沿程与局部损失"],
                "method": "两水池淹没短管能量方程与分段测压管水头法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确计入直角进口 ζ进=0.5、沿程 λL/d=2.0 与淹没出口 ζ出=1.0 列全管能量方程求出 v²/(2g) = 1.00 m", "pts": 5},
                    {"label": "算出管内平均流速 v ≈ 4.43 m/s 及流量 Q ≈ 0.0348 m³/s（单位正确）", "pts": 4},
                    {"label": "对上游水面与管道中点断面列能量方程 Z = H + (1 + ζ进 + λL/(2d))·v²/(2g)，解得 H = 1.00 m", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2010-10",
                "year": 2010,
                "no": 10,
                "type": "calc",
                "score": 15,
                "title": "嵌入支座内水平渐缩输水管段支座轴向推力计算",
                "stem": "嵌入支座内的一段输水管，其直径由 $1.5\\,\\mathrm{m}$ 变化到 $1\\,\\mathrm{m}$（如图示）。当支座前的压强 $p = 0.5\\,\\mathrm{MPa}$（相对压强），流量 $Q$ 为 $1.85\\,\\mathrm{m^3/s}$ 时，试确定渐变段支座所受的轴向力（不计水头损失）。",
                "note": "",
                "figures": [
                    {"src": "figures/q10_orig.png", "caption": "题 10 图　嵌入固定混凝土支座内的水平渐缩输水管段"}
                ],
                "shortAnswer": "F ≈ 490.20 kN，方向水平向右（顺水流方向）。",
                "judgeAnswer": None,
                "answer": "渐变段混凝土支座所受的轴向作用力大小为 **$490.20\\,\\mathrm{kN}$**，方向**水平向右（顺水流方向）**。",
                "analysis": "**1. 由连续性方程计算支座前后进、出口断面流速**\n\n已知进口管径 $d_1 = 1.5\\,\\mathrm{m}$，出口管径 $d_2 = 1.0\\,\\mathrm{m}$，流量 $Q = 1.85\\,\\mathrm{m^3/s}$：\n\n$$\nA_1 = \\frac{\\pi}{4}d_1^2 = \\frac{\\pi}{4} \\times 1.5^2 \\approx 1.76715\\,\\mathrm{m^2}, \\qquad v_1 = \\frac{Q}{A_1} = \\frac{1.85}{1.76715} \\approx 1.04689\\,\\mathrm{m/s}\n$$\n\n$$\nA_2 = \\frac{\\pi}{4}d_2^2 = \\frac{\\pi}{4} \\times 1.0^2 \\approx 0.78540\\,\\mathrm{m^2}, \\qquad v_2 = \\frac{Q}{A_2} = \\frac{1.85}{0.78540} \\approx 2.35549\\,\\mathrm{m/s}\n$$\n\n**2. 由水平无损伯努利方程求出口断面相对压强 $p_2$**\n\n管道水平布置（$z_1 = z_2$），不计水头损失（$h_w = 0$），支座前相对压强 $p_1 = 0.5\\,\\mathrm{MPa} = 500\\,\\mathrm{kPa} = 5.0 \\times 10^5\\,\\mathrm{Pa}$。取 $\\alpha_1 = \\alpha_2 = 1.0$，列 $1\\text{—}1$ 至 $2\\text{—}2$ 能量方程：\n\n$$\n\\frac{p_1}{\\rho g} + \\frac{v_1^2}{2g} = \\frac{p_2}{\\rho g} + \\frac{v_2^2}{2g} \\implies p_2 = p_1 + \\frac{1}{2}\\rho (v_1^2 - v_2^2)\n$$\n\n代入 $\\rho = 1000\\,\\mathrm{kg/m^3}$：\n\n$$\np_2 = 500000 + \\frac{1}{2} \\times 1000 \\times (1.04689^2 - 2.35549^2) = 500000 - 2226.2 = 497773.8\\,\\mathrm{Pa} \\approx 497.77\\,\\mathrm{kPa}\n$$\n\n**3. 对渐缩段水体控制体列轴向动量方程求支座受力**\n\n计算进、出口断面上的法向动水总压力 $P_1$ 与 $P_2$：\n\n$$\nP_1 = p_1 A_1 = 500 \\times 1.76715 = 883.573\\,\\mathrm{kN}\\;(\\text{水平向右})\n$$\n\n$$\nP_2 = p_2 A_2 = 497.7738 \\times 0.78540 = 390.951\\,\\mathrm{kN}\\;(\\text{水平向左})\n$$\n\n取水平向右（顺水流方向）为 $+x$ 正向，设支座通过渐缩管壁对水体的轴向反作用力为 $R$（假设方向**水平向左**），取 $\\beta_1 = \\beta_2 = 1.0$，列水平动量方程：\n\n$$\nP_1 - P_2 - R = \\rho Q (v_2 - v_1)\n$$\n\n其中动量通量变化率 $\\rho Q (v_2 - v_1) = 1.0 \\times 1.85 \\times (2.35549 - 1.04689) = 2.421\\,\\mathrm{kN}$。解出管壁对水体的向左反力 $R$：\n\n$$\nR = 883.573 - 390.951 - 2.421 = 490.201\\,\\mathrm{kN} \\approx 490.20\\,\\mathrm{kN}\n$$\n\n$R > 0$ 表明支座对水体的反力确实水平向左。根据**牛顿第三定律**，水流通过渐缩管壁作用于混凝土支座上的轴向推力 $F = R = 490.20\\,\\mathrm{kN}$，方向**水平向右（顺水流方向）**。",
                "analysisFigures": [],
                "pitfalls": "1. **切勿搞反牛顿第三定律的方向！** 支座对水体的反力 $R$ 向左阻挡水流，因此**支座本身所承受的轴向推力方向必然水平向右（顺水流方向）**（直观检查：左侧大断面推力 $P_1 = 883.6\\,\\mathrm{kN}$ 远大于右侧小断面反推力 $P_2 = 391.0\\,\\mathrm{kN}$，水流显然把渐缩管往右推！）；\n2. 动量方程左端必须是**压力 $P_1 = p_1 A_1$、$P_2 = p_2 A_2$**（单位 $\\mathrm{N}$ 或 $\\mathrm{kN}$），绝不可漏乘面积写成压强 $p_1 - p_2$。",
                "chapter": 3,
                "kps": ["闸门与弯管动水总压力", "恒定总流动量方程", "恒定总流能量方程"],
                "method": "能量方程求压强+控制体动量方程求镇墩力",
                "difficulty": 2,
                "rubric": [
                    {"label": "由连续性方程求出进出口面积与流速 v1 ≈ 1.05 m/s、v2 ≈ 2.36 m/s", "pts": 4},
                    {"label": "由水平伯努利方程求出出口压强 p2 ≈ 497.77 kPa 及断面总压力 P1 ≈ 883.57 kN、P2 ≈ 390.95 kN", "pts": 5},
                    {"label": "列轴向动量方程 P1 - P2 - R = ρQ(v2 - v1) 求得 R ≈ 490.20 kN，并由牛顿第三定律指明支座受力水平向右", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2010-11",
                "year": 2010,
                "no": 11,
                "type": "calc",
                "score": 16,
                "title": "直角角隅平面流函数 ψ = Axy 的变形与旋转特性判别及势函数求解",
                "stem": "已知某流场的流函数为 $\\psi = Axy$，式中 $A$ 为常数（$A \\neq 0$）。试求：\n\n1）流动是否有变形和旋转运动；\n\n2）如无旋转运动，求其流速势函数。",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）存在线变形运动（εxx = A ≠ 0，εyy = -A ≠ 0，坐标轴向角变形率 εxy = 0），故流动有变形运动；旋转角速度 ωz = (∂uy/∂x - ∂ux/∂y)/2 = 0，故无旋转运动（为不可压缩无旋势流）。（2）流速势函数为 φ = (1/2)A(x² - y²) + C（C 为任意常数）。",
                "judgeAnswer": None,
                "answer": "**1）变形与旋转运动判别**：\n- 由 $\\psi = Axy$ 得 $u_x = Ax,\\; u_y = -Ay,\\; u_z = 0$；\n- **有变形运动**：线变形率 $\\varepsilon_{xx} = \\frac{\\partial u_x}{\\partial x} = A \\neq 0$，$\\varepsilon_{yy} = \\frac{\\partial u_y}{\\partial y} = -A \\neq 0$（沿坐标轴角变形率 $\\varepsilon_{xy} = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} + \\frac{\\partial u_x}{\\partial y}\\right) = 0$），流体微团沿 $x$ 向拉伸、沿 $y$ 向压缩，存在线变形运动；\n- **无旋转运动**：旋转角速度分量 $\\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right) = 0$（$\\omega_x = \\omega_y = 0$），故流动为**无旋流动**。\n\n**2）流速势函数表达式**：\n\n$$\n\\varphi(x, y) = \\frac{1}{2}A(x^2 - y^2) + C\\quad (C\\text{ 为任意常数})\n$$",
                "analysis": "**1. 导出速度场并逐项计算亥姆霍兹（Helmholtz）微团运动特征量**\n\n已知二维平面流函数 $\\psi(x, y) = A x y$（默认非退化流场 $A \\neq 0$），流速分量为：\n\n$$\nu_x = \\frac{\\partial \\psi}{\\partial y} = A x, \\qquad u_y = -\\frac{\\partial \\psi}{\\partial x} = -A y, \\qquad u_z = 0\n$$\n\n（注：此即经典的直角壁面驻点势流 / 平面纯拉伸流。）\n\n1. **线变形率（正应变率）**：\n\n$$\n\\varepsilon_{xx} = \\frac{\\partial u_x}{\\partial x} = A, \\qquad \\varepsilon_{yy} = \\frac{\\partial u_y}{\\partial y} = -A, \\qquad \\varepsilon_{zz} = \\frac{\\partial u_z}{\\partial z} = 0\n$$\n\n   虽然体积膨胀率 $\\theta = \\varepsilon_{xx} + \\varepsilon_{yy} + \\varepsilon_{zz} = A - A + 0 = 0$（满足不可压缩条件），但各向线变形率 $\\varepsilon_{xx} \\neq 0,\\; \\varepsilon_{yy} \\neq 0$，流体微团发生形状改变（矩形微团变扁变长）。\n\n2. **角变形率（切应变率）**：\n\n$$\n\\varepsilon_{xy} = \\varepsilon_{yx} = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} + \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{1}{2}(0 + 0) = 0, \\qquad \\varepsilon_{yz} = \\varepsilon_{zx} = 0\n$$\n\n   （坐标轴 $x, y$ 恰为主应变率方向，故平行于 $x, y$ 轴的微元边夹角不变；因线变形率非零，**总结论：该流动存在变形运动**。）\n\n3. **旋转角速度（涡量的一半）**：\n\n$$\n\\omega_x = 0, \\qquad \\omega_y = 0, \\qquad \\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{1}{2}(0 - 0) = 0\n$$\n\n   （亦可验证 $\\nabla^2 \\psi = \\frac{\\partial^2\\psi}{\\partial x^2} + \\frac{\\partial^2\\psi}{\\partial y^2} = 0$。）故**该流动无旋转运动**。\n\n**2. 积分求流速势函数 $\\varphi(x, y)$**\n\n因流动无旋，必存在单值速度势函数 $\\varphi(x, y)$ 满足 $\\frac{\\partial \\varphi}{\\partial x} = u_x = A x$，$\\frac{\\partial \\varphi}{\\partial y} = u_y = -A y$。对全微分 $\\mathrm{d}\\varphi$ 直接积分：\n\n$$\n\\mathrm{d}\\varphi = u_x\\,\\mathrm{d}x + u_y\\,\\mathrm{d}y = A x\\,\\mathrm{d}x - A y\\,\\mathrm{d}y = \\mathrm{d}\\left[\\frac{1}{2}A(x^2 - y^2)\\right]\n$$\n\n即得流速势函数：\n\n$$\n\\varphi(x, y) = \\frac{1}{2}A(x^2 - y^2) + C\\quad (C\\text{ 为任意常数})\n$$\n\n（注：等流函数线 $xy = \\text{const}$ 与等势线 $x^2 - y^2 = \\text{const}$ 为两组处处正交的双曲线族。）",
                "analysisFigures": [],
                "pitfalls": "1. **严格区分角变形率与旋转角速度的加减号！** 角变形率是加号 $\\varepsilon_{xy} = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} + \\frac{\\partial u_x}{\\partial y}\\right)$，而旋转角速度是**减号** $\\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right)$！虽本题两偏导均为 $0$，但公式符号写错会被直接扣概念分；\n2. 变形运动包括**线变形**与**角变形**两类，只要任一应变率分量非零（此处 $\\varepsilon_{xx} = A \\neq 0$）即属于**有变形运动**。",
                "chapter": 5,
                "kps": ["流函数与势函数", "流体微团运动分解", "线变形率与角变形率", "有旋流与无旋流判别"],
                "method": "亥姆霍兹微团应变率旋度分解与势函数全微分法",
                "difficulty": 3,
                "rubric": [
                    {"label": "由流函数 ψ = Axy 正确求出流速分量 ux = Ax、uy = -Ay", "pts": 3},
                    {"label": "正确写出并计算线变形率（εxx=A, εyy=-A ≠ 0）与角变形率（εxy=0），明确指出存在变形运动", "pts": 5},
                    {"label": "正确写出旋转角速度公式 ωz = (∂uy/∂x - ∂ux/∂y)/2 = 0（减号准确），判定无旋转运动", "pts": 4},
                    {"label": "由 dφ = ux dx + uy dy 积分求得流速势函数 φ = A(x² - y²)/2 + C", "pts": 4}
                ]
            }
        ]
    }


# ==============================================================================
# WRITE STANDARDIZED PACKS + WEB-READY JSON & WEBP ASSETS
# ==============================================================================

def write_year_outputs(paper: dict, pack_dir: Path) -> None:
    year = int(paper["year"])
    pack_dir.mkdir(parents=True, exist_ok=True)
    src_fig_dir = pack_dir / "figures"

    pack_json = pack_dir / f"{year}.json"
    pack_json.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[PACK] Wrote {pack_json} ({len(paper['questions'])} questions)")

    web_fig_dir = WEB_COURSE_DIR / "figures" / str(year)
    web_fig_dir.mkdir(parents=True, exist_ok=True)
    web_paper = copy.deepcopy(paper)

    fig_count = 0
    for q in web_paper["questions"]:
        for key in ("figures", "analysisFigures"):
            new_list = []
            for fig in q.get(key, []):
                raw_name = Path(fig["src"]).name
                src_png = src_fig_dir / raw_name
                if not src_png.exists():
                    raise FileNotFoundError(f"Missing source figure: {src_png}")
                webp_name = f"{Path(raw_name).stem}.webp"
                dest_webp = web_fig_dir / webp_name
                im = Image.open(src_png)
                if im.mode not in ("RGB", "RGBA"):
                    im = im.convert("RGBA")
                im.save(dest_webp, format="WEBP", quality=90, method=5)
                new_list.append({
                    "src": f"figures/{year}/{webp_name}",
                    "caption": fig["caption"]
                })
                fig_count += 1
            q[key] = new_list

    web_json = WEB_COURSE_DIR / f"{year}.json"
    web_json.write_text(json.dumps(web_paper, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[WEB]  Wrote {web_json} ({len(web_paper['questions'])} questions, {fig_count} WebP figures)")


def main() -> None:
    pack_2011 = PACK_ROOT / "2011"
    build_2011_figures(pack_2011 / "figures")
    paper_2011 = build_2011_paper()
    write_year_outputs(paper_2011, pack_2011)

    pack_2010 = PACK_ROOT / "2010"
    build_2010_figures(pack_2010 / "figures")
    paper_2010 = build_2010_paper()
    write_year_outputs(paper_2010, pack_2010)


if __name__ == "__main__":
    main()
