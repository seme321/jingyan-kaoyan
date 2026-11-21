# -*- coding: utf-8 -*-
"""
Generate stem figures (q*_orig.png), clean matplotlib solution schematics
(q*_sol.png, dpi=220), standardized exam packs in `扬州大学已整理数据/{2008,2007}/`,
and web-ready JSON + WebP assets in `web/public/data/yzu-849/` for
Yangzhou University 849 Hydraulics (2008 & 2007).
"""

import copy
import json
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


def remove_small_specks(binary_ink: np.ndarray, min_pixels: int = 5) -> np.ndarray:
    """Remove isolated 1~4 px scan dust specks while keeping all strokes and dots."""
    h, w = binary_ink.shape
    visited = np.zeros_like(binary_ink, dtype=bool)
    cleaned = binary_ink.copy()
    ys, xs = np.where(binary_ink)
    for y0, x0 in zip(ys, xs):
        if visited[y0, x0]:
            continue
        y_min, y_max = max(0, y0 - 2), min(h, y0 + 3)
        x_min, x_max = max(0, x0 - 2), min(w, x0 + 3)
        if binary_ink[y_min:y_max, x_min:x_max].sum() >= min_pixels:
            visited[y0, x0] = True
            continue
        stack = [(y0, x0)]
        comp = []
        visited[y0, x0] = True
        while stack and len(comp) < min_pixels + 2:
            cy, cx = stack.pop()
            comp.append((cy, cx))
            for ny in range(max(0, cy - 1), min(h, cy + 2)):
                for nx in range(max(0, cx - 1), min(w, cx + 2)):
                    if binary_ink[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((ny, nx))
        if len(comp) < min_pixels and not stack:
            for cy, cx in comp:
                cleaned[cy, cx] = False
    return cleaned


def clean_and_pad(pil_img: Image.Image, pad: int = 16, thresh: int = 215) -> Image.Image:
    """Auto-trim ink bounds, clean background to pure white #FFFFFF, and add 16px margin."""
    gray = np.array(pil_img.convert("L"), dtype=np.uint8)
    ink = remove_small_specks(gray < thresh, min_pixels=5)
    ys, xs = np.where(ink)
    if len(xs) == 0:
        return pil_img.convert("RGB")
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    sub = gray[y0:y1, x0:x1].copy()
    sub_ink = ink[y0:y1, x0:x1]
    sub_f = np.clip((sub.astype(np.float32) - 45.0) * (255.0 / (225.0 - 45.0)), 0, 255).astype(np.uint8)
    sub_f[~sub_ink & (sub > 205)] = 255
    out = np.full((sub_f.shape[0] + 2 * pad, sub_f.shape[1] + 2 * pad), 255, dtype=np.uint8)
    out[pad:pad + sub_f.shape[0], pad:pad + sub_f.shape[1]] = sub_f
    return Image.fromarray(out, mode="L").convert("RGB")


def extract_2008_stem_figures():
    """Crop the 5 crisp stem figures from `849-水力学（水）2008.pdf` at 300 DPI."""
    fig_dir = PACK_ROOT / "2008" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    specs = {
        "q21_orig.png": (1, (1335, 2205, 1982, 2705)),
        "q22_orig.png": (2, (1455, 480, 1990, 885)),
        "q23_orig.png": (2, (1680, 940, 1985, 1230)),
        "q24_orig.png": (2, (1505, 1400, 1990, 1795)),
        "q25_orig.png": (2, (1085, 1905, 2020, 2500)),
    }
    doc = pymupdf.open(RAW_DIR / "849-水力学（水）2008.pdf")
    pages = {}
    for fname, (pidx, box) in specs.items():
        if pidx not in pages:
            pix = doc[pidx].get_pixmap(dpi=300)
            pages[pidx] = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        clean_and_pad(pages[pidx].crop(box), pad=16).save(fig_dir / fname)
    doc.close()
    print(f"[2008] Extracted {len(specs)} stem figures at 300 DPI -> {fig_dir}")


# ==============================================================================
# Clean Engineering Redraws of 2007 Stem Figures (eliminating scan tilt & fade)
# ==============================================================================

def draw_water_sym(ax, x, y, s=0.14, color="#0f172a"):
    ax.plot([x, x - s, x + s, x], [y, y + 1.45 * s, y + 1.45 * s, y], color=color, lw=1.2)
    ax.plot([x - 1.2 * s, x + 1.2 * s], [y - 0.55 * s, y - 0.55 * s], color=color, lw=1.0)
    ax.plot([x - 0.75 * s, x + 0.75 * s], [y - 1.05 * s, y - 1.05 * s], color=color, lw=1.0)
    ax.plot([x - 0.35 * s, x + 0.35 * s], [y - 1.50 * s, y - 1.50 * s], color=color, lw=1.0)


def draw_2007_stem_figures():
    fig_dir = PACK_ROOT / "2007" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. q02_orig: two rectangular channels (4x1 and 2.82x1.41)
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    fig.patch.set_facecolor("white")
    # Left channel: b=4, h=1
    ax.plot([0.5, 0.5, 4.5, 4.5], [1.45, 0.0, 0.0, 1.45], color="#0f172a", lw=2.0)
    ax.plot([0.5, 4.5], [1.0, 1.0], color="#0f172a", lw=1.4)
    draw_water_sym(ax, 1.15, 1.0, s=0.12)
    ax.text(2.5, 0.52, r"$Q_1$", fontsize=12, ha="center", va="center")
    ax.annotate("", xy=(4.5, -0.28), xytext=(0.5, -0.28), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.2))
    ax.plot([0.5, 0.5], [-0.04, -0.40], color="#0f172a", lw=0.9)
    ax.plot([4.5, 4.5], [-0.04, -0.40], color="#0f172a", lw=0.9)
    ax.text(2.5, -0.48, "4", fontsize=11, ha="center")
    ax.plot([4.54, 5.02], [1.0, 1.0], color="#0f172a", lw=0.9)
    ax.plot([4.54, 5.02], [0.0, 0.0], color="#0f172a", lw=0.9)
    ax.annotate("", xy=(4.85, 1.0), xytext=(4.85, 0.0), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.2))
    ax.text(4.96, 0.50, "1", fontsize=11, va="center")

    # Right channel: b=2.82, h=1.41
    x0 = 6.2
    ax.plot([x0, x0, x0 + 2.82, x0 + 2.82], [1.85, 0.0, 0.0, 1.85], color="#0f172a", lw=2.0)
    ax.plot([x0, x0 + 2.82], [1.41, 1.41], color="#0f172a", lw=1.4)
    draw_water_sym(ax, x0 + 0.65, 1.41, s=0.12)
    ax.text(x0 + 1.41, 0.72, r"$Q_2$", fontsize=12, ha="center", va="center")
    ax.annotate("", xy=(x0 + 2.82, -0.28), xytext=(x0, -0.28), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.2))
    ax.plot([x0, x0], [-0.04, -0.40], color="#0f172a", lw=0.9)
    ax.plot([x0 + 2.82, x0 + 2.82], [-0.04, -0.40], color="#0f172a", lw=0.9)
    ax.text(x0 + 1.41, -0.48, "2.82", fontsize=11, ha="center")
    ax.plot([x0 + 2.86, x0 + 3.32], [1.41, 1.41], color="#0f172a", lw=0.9)
    ax.plot([x0 + 2.86, x0 + 3.32], [0.0, 0.0], color="#0f172a", lw=0.9)
    ax.annotate("", xy=(x0 + 3.16, 1.41), xytext=(x0 + 3.16, 0.0), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.2))
    ax.text(x0 + 3.26, 0.70, "1.41", fontsize=11, va="center")

    ax.set_xlim(0.1, 10.2)
    ax.set_ylim(-0.72, 2.05)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q02_orig.png", dpi=220, facecolor="white")
    plt.close(fig)

    # 2. q06_orig: two containers of different shape, equal base area & equal depth H
    fig, ax = plt.subplots(figsize=(6.2, 2.8))
    fig.patch.set_facecolor("white")
    ax.plot([0.2, 6.2], [0.0, 0.0], color="#0f172a", lw=1.8)
    for xh in np.linspace(0.35, 6.05, 26):
        ax.plot([xh, xh - 0.14], [0.0, -0.22], color="#334155", lw=0.9)
    # Left container (flared trapezoid)
    ax.plot([0.55, 1.10, 2.30, 2.85], [1.60, 0.0, 0.0, 1.60], color="#0f172a", lw=2.0)
    ax.plot([0.62, 2.78], [1.40, 1.40], color="#0f172a", lw=1.4)
    draw_water_sym(ax, 1.70, 1.40, s=0.11)
    ax.annotate("", xy=(1.70, 0.02), xytext=(1.70, 0.72), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.5))
    ax.text(1.82, 0.42, r"$P_1$", fontsize=11.5)
    # Right container (vertical cylinder/prism, same bottom width 1.20)
    ax.plot([4.35, 4.35, 5.55, 5.55], [1.60, 0.0, 0.0, 1.60], color="#0f172a", lw=2.0)
    ax.plot([4.35, 5.55], [1.40, 1.40], color="#0f172a", lw=1.4)
    draw_water_sym(ax, 4.95, 1.40, s=0.11)
    ax.annotate("", xy=(4.95, 0.02), xytext=(4.95, 0.72), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.5))
    ax.text(5.07, 0.42, r"$P_2$", fontsize=11.5)
    # Depth H dimension between them
    ax.plot([2.88, 4.25], [1.40, 1.40], color="#0f172a", ls="--", lw=0.9)
    ax.annotate("", xy=(3.55, 1.40), xytext=(3.55, 0.0), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.3))
    ax.text(3.67, 0.70, r"$H$", fontsize=11.5, va="center")
    ax.set_xlim(0.0, 6.4)
    ax.set_ylim(-0.35, 1.88)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q06_orig.png", dpi=220, facecolor="white")
    plt.close(fig)

    # 3. q07_orig: hemispherical gate R=1m, H=1m
    fig, ax = plt.subplots(figsize=(5.8, 4.2))
    fig.patch.set_facecolor("white")
    ax.plot([-2.1, 2.2], [0.0, 0.0], color="#0f172a", lw=2.0)
    for xh in np.linspace(-1.95, 2.05, 18):
        ax.plot([xh, xh + 0.14], [0.0, -0.20], color="#334155", lw=0.9)
    # Vertical dam wall above hemisphere (from y=2 to y=3.3)
    ax.plot([0.0, 0.0], [2.0, 3.25], color="#0f172a", lw=2.2)
    # Left semicircle (convex protruding left into upstream water), center O=(0, 1), R=1
    th = np.linspace(np.pi / 2, 3 * np.pi / 2, 160)
    ax.plot(np.cos(th), 1.0 + np.sin(th), color="#0f172a", lw=2.2)
    # Upstream WS y=3.0, Downstream WS y=2.0
    ax.plot([-2.05, 0.0], [3.0, 3.0], color="#0f172a", lw=1.5)
    draw_water_sym(ax, -1.25, 3.0, s=0.13)
    ax.plot([0.0, 2.05], [2.0, 2.0], color="#0f172a", lw=1.5)
    draw_water_sym(ax, 1.45, 2.0, s=0.13)
    # Dimension H = 1 m
    ax.plot([0.05, 0.75], [3.0, 3.0], color="#0f172a", lw=0.9)
    ax.annotate("", xy=(0.55, 3.0), xytext=(0.55, 2.0), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.2))
    ax.text(0.65, 2.50, r"$H = 1\,\mathrm{m}$", fontsize=10.5, va="center")
    # Radius R = 1 m arrow
    ang = np.radians(135)
    ax.annotate("", xy=(np.cos(ang), 1.0 + np.sin(ang)), xytext=(0.0, 1.0),
                arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.3))
    ax.scatter([0.0], [1.0], color="#0f172a", s=16)
    ax.text(0.10, 1.08, r"$R = 1\,\mathrm{m}$", fontsize=10.5)
    ax.annotate("球形闸门", xy=(-0.82, 1.56), xytext=(-1.95, 2.05), fontsize=10.5,
                arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.1))
    ax.set_xlim(-2.25, 2.35)
    ax.set_ylim(-0.35, 3.45)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q07_orig.png", dpi=220, facecolor="white")
    plt.close(fig)

    # 4. q08_orig: horizontal Venturi suction pipe
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    fig.patch.set_facecolor("white")
    # Upper and lower pipe walls (d1=0.60, throat d2=0.30)
    xs_top = [0.6, 2.4, 3.2, 3.7, 4.5, 5.8]
    ys_top = [2.30, 2.30, 2.15, 2.15, 2.30, 2.30]
    ys_bot = [1.70, 1.70, 1.85, 1.85, 1.70, 1.70]
    ax.plot(xs_top, ys_top, color="#0f172a", lw=2.0)
    ax.plot([0.6, 2.4, 3.2, 3.36], [1.70, 1.70, 1.85, 1.85], color="#0f172a", lw=2.0)
    ax.plot([3.54, 3.7, 4.5, 5.8], [1.85, 1.85, 1.70, 1.70], color="#0f172a", lw=2.0)
    # Piezometer at section 1-1 (x=1.8)
    ax.plot([1.72, 1.72], [2.30, 3.55], color="#0f172a", lw=1.5)
    ax.plot([1.88, 1.88], [2.30, 3.55], color="#0f172a", lw=1.5)
    ax.plot([1.72, 1.88], [3.25, 3.25], color="#0f172a", lw=1.3)
    ax.plot([1.92, 2.42], [3.25, 3.25], color="#0f172a", lw=0.9)
    ax.plot([0.4, 5.95], [2.00, 2.00], color="#64748b", ls="-.", lw=0.9)
    ax.annotate("", xy=(2.25, 3.25), xytext=(2.25, 2.00), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.2))
    ax.text(2.38, 2.68, r"$\dfrac{p_1}{\rho g}$", fontsize=11.5, va="center")
    # Section labels 1-1 and 2-2
    ax.plot([1.45, 1.45], [1.55, 2.45], color="#0f172a", ls="--", lw=1.0)
    ax.text(1.45, 2.52, "1", ha="center", fontsize=10.5)
    ax.text(1.45, 1.38, "1", ha="center", fontsize=10.5)
    ax.plot([3.45, 3.45], [1.95, 2.38], color="#0f172a", ls="--", lw=1.0)
    ax.text(3.45, 2.45, "2", ha="center", fontsize=10.5)
    # Diameter d1 annotations
    ax.annotate("", xy=(1.10, 2.30), xytext=(1.10, 2.68), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.1))
    ax.annotate("", xy=(1.10, 1.70), xytext=(1.10, 1.32), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.1))
    ax.text(1.18, 1.38, r"$d_1$", fontsize=11)
    ax.annotate("", xy=(5.20, 2.30), xytext=(5.20, 2.68), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.1))
    ax.annotate("", xy=(5.20, 1.70), xytext=(5.20, 1.32), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.1))
    ax.text(5.28, 1.38, r"$d_1$", fontsize=11)
    ax.annotate("", xy=(0.85, 2.00), xytext=(0.18, 2.00), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.6))
    ax.text(0.45, 2.15, r"$Q$", fontsize=11.5, ha="center")
    # Vertical suction tube down into container A
    ax.plot([3.36, 3.36], [0.42, 1.85], color="#0f172a", lw=1.6)
    ax.plot([3.54, 3.54], [0.42, 1.85], color="#0f172a", lw=1.6)
    # Open tank A below
    ax.plot([2.55, 2.55, 4.35, 4.35], [1.15, 0.20, 0.20, 1.15], color="#0f172a", lw=1.9)
    ax.plot([2.55, 3.36], [0.85, 0.85], color="#0f172a", lw=1.4)
    ax.plot([3.54, 4.35], [0.85, 0.85], color="#0f172a", lw=1.4)
    draw_water_sym(ax, 2.95, 0.85, s=0.10)
    ax.text(2.85, 0.42, r"$A$", fontsize=11.5)
    # Dimension hk from tank A WS to throat centerline
    ax.plot([4.38, 4.82], [0.85, 0.85], color="#0f172a", lw=0.9)
    ax.annotate("", xy=(4.65, 2.00), xytext=(4.65, 0.85), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.2))
    ax.text(4.75, 1.42, r"$h_k$", fontsize=11.5, va="center")
    ax.set_xlim(0.05, 6.05)
    ax.set_ylim(0.05, 3.70)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q08_orig.png", dpi=220, facecolor="white")
    plt.close(fig)

    # 5. q09_orig: Simple hydraulic press (O-A-B lever, large & small pistons)
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    fig.patch.set_facecolor("white")
    # Connected hydraulic press cylinders (left large d2, right small d1)
    # Left cylinder x in [0.8, 2.6], y in [0.4, 2.3]
    # Connecting pipe y in [0.4, 0.75] from x=2.6 to x=4.6
    # Right cylinder x in [4.6, 5.1], y in [0.4, 1.9]
    ax.plot([0.8, 0.8, 5.1, 5.1], [2.35, 0.4, 0.4, 1.95], color="#0f172a", lw=2.1)
    ax.plot([2.6, 2.6, 4.6, 4.6], [2.35, 0.78, 0.78, 1.95], color="#0f172a", lw=2.1)
    # Large piston (举重活塞)
    ax.add_patch(patches.Rectangle((0.83, 1.45), 1.74, 0.25, facecolor="#e2e8f0", edgecolor="#0f172a", lw=1.6, hatch="///"))
    ax.add_patch(patches.Rectangle((1.12, 1.70), 1.16, 0.62, facecolor="#f8fafc", edgecolor="#0f172a", lw=1.6))
    ax.text(1.70, 2.00, "重物", fontsize=10.5, ha="center", va="center")
    ax.text(1.70, 2.55, "举重活塞", fontsize=10.2, ha="center")
    ax.text(1.70, 0.92, "水", fontsize=11, ha="center")
    # Small piston (加重活塞)
    ax.add_patch(patches.Rectangle((4.63, 1.45), 0.44, 0.22, facecolor="#e2e8f0", edgecolor="#0f172a", lw=1.5, hatch="///"))
    ax.plot([4.85, 4.85], [1.67, 2.65], color="#0f172a", lw=1.8)
    ax.text(5.22, 1.56, "加重活塞", fontsize=10.2, va="center")
    # Fulcrum O at (4.15, 2.65), A at (4.85, 2.65), B at (6.95, 2.65) -> AO : AB = 1 : 3!
    ax.plot([4.15, 4.15], [1.95, 2.65], color="#0f172a", lw=1.6)
    ax.plot([3.95, 4.35], [1.95, 1.95], color="#0f172a", lw=1.6)
    ax.plot([4.15, 6.95], [2.65, 2.65], color="#0f172a", lw=2.4)
    for px, lbl, py in [(4.15, r"$O$", 2.84), (4.85, r"$A$", 2.84), (6.95, r"$B$", 2.34)]:
        ax.scatter([px], [2.65], color="white", edgecolor="#0f172a", lw=1.5, s=34, zorder=5)
        ax.text(px, py, lbl, fontsize=11, ha="center")
    ax.annotate("", xy=(6.95, 2.68), xytext=(6.95, 3.40), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.9))
    ax.text(7.06, 3.15, r"$P$", fontsize=11.5, va="center")
    ax.set_xlim(0.45, 7.55)
    ax.set_ylim(0.18, 3.60)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q09_orig.png", dpi=220, facecolor="white")
    plt.close(fig)

    # 6. q10_orig: Horizontal jet striking 60 deg inclined plate
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    fig.patch.set_facecolor("white")
    ang = np.radians(60)
    # Plate from bottom-left to top-right passing through (0, 0)
    L = 1.9
    ax.plot([-L * np.cos(ang), L * np.cos(ang)], [-L * np.sin(ang), L * np.sin(ang)], color="#0f172a", lw=2.6)
    # Horizontal reference dashed line
    ax.plot([-2.4, 1.65], [0.0, 0.0], color="#475569", ls="-.", lw=1.1)
    # Incoming jet
    ax.plot([-2.3, -0.35], [0.22, 0.22], color="#0f172a", lw=1.6)
    ax.plot([-2.3, -0.35], [-0.22, -0.22], color="#0f172a", lw=1.6)
    ax.annotate("", xy=(-0.85, 0.0), xytext=(-1.95, 0.0), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.8))
    ax.text(-2.45, 0.0, r"$v,\; Q$", fontsize=11.5, ha="right", va="center")
    # Split jet 1 (up-right along plate)
    n_vec = np.array([-np.sin(ang), np.cos(ang)])
    t_vec = np.array([np.cos(ang), np.sin(ang)])
    p1_start = 0.35 * t_vec + 0.14 * n_vec
    p1_end = 1.55 * t_vec + 0.14 * n_vec
    ax.annotate("", xy=p1_end, xytext=p1_start, arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.7))
    ax.text(p1_end[0] - 0.05, p1_end[1] + 0.24, r"$v_1,\; Q_1$", fontsize=11.5, ha="center")
    # Split jet 2 (down-left along plate)
    p2_start = -0.35 * t_vec + 0.14 * n_vec
    p2_end = -1.55 * t_vec + 0.14 * n_vec
    ax.annotate("", xy=p2_end, xytext=p2_start, arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.7))
    ax.text(p2_end[0] - 0.52, p2_end[1] - 0.14, r"$v_2,\; Q_2$", fontsize=11.5, ha="center")
    # Angle arc 60 deg
    arc = patches.Arc((0, 0), 1.05, 1.05, angle=0, theta1=0, theta2=60, color="#0f172a", lw=1.2)
    ax.add_patch(arc)
    ax.text(0.68, 0.26, r"$60^{\circ}$", fontsize=11)
    ax.set_xlim(-3.2, 2.0)
    ax.set_ylim(-2.05, 2.05)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q10_orig.png", dpi=220, facecolor="white")
    plt.close(fig)

    # 7. q11_orig: Upright mercury U-tube connecting A and B (elevation diff S, mercury diff h)
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    fig.patch.set_facecolor("white")
    # Container A (left, center at (0.8, 2.4)) and Container B (right, center at (2.8, 3.2))
    ax.add_patch(patches.Rectangle((0.35, 2.15), 0.90, 0.52, facecolor="white", edgecolor="#0f172a", lw=1.9))
    ax.text(0.80, 2.41, r"$A$", fontsize=11.5, ha="center", va="center")
    ax.add_patch(patches.Rectangle((2.35, 2.95), 0.90, 0.52, facecolor="white", edgecolor="#0f172a", lw=1.9))
    ax.text(2.80, 3.21, r"$B$", fontsize=11.5, ha="center", va="center")
    # U-tube legs from x=0.80 and x=2.80 down to y=0.65
    tw = 0.08
    ax.plot([0.80 - tw, 0.80 - tw, 2.80 + tw, 2.80 + tw], [2.15, 0.57, 0.57, 2.95], color="#0f172a", lw=1.8)
    ax.plot([0.80 + tw, 0.80 + tw, 2.80 - tw, 2.80 - tw], [2.15, 0.73, 0.73, 2.95], color="#0f172a", lw=1.8)
    # Dark mercury fill: left meniscus at y=0.95 (line c-c), right meniscus at y=1.55 (height h above c-c)
    ax.add_patch(patches.Rectangle((0.80 - tw, 0.57), 2 * tw, 0.95 - 0.57, facecolor="#1e293b"))
    ax.add_patch(patches.Rectangle((0.80 - tw, 0.57), 2.0 + 2 * tw, 0.16, facecolor="#1e293b"))
    ax.add_patch(patches.Rectangle((2.80 - tw, 0.57), 2 * tw, 1.55 - 0.57, facecolor="#1e293b"))
    # Equal pressure line c-c
    ax.plot([0.25, 3.35], [0.95, 0.95], color="#0f172a", ls="--", lw=1.1)
    ax.text(0.18, 0.95, r"$c$", fontsize=10.5, ha="right", va="center")
    ax.text(3.42, 0.95, r"$c$", fontsize=10.5, ha="left", va="center")
    # Dimension S between A and B centers
    ax.plot([1.28, 2.10], [2.41, 2.41], color="#0f172a", lw=0.9)
    ax.plot([1.75, 2.32], [3.21, 3.21], color="#0f172a", lw=0.9)
    ax.annotate("", xy=(1.92, 3.21), xytext=(1.92, 2.41), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.2))
    ax.text(2.02, 2.81, r"$S$", fontsize=11.5, va="center")
    # Dimension h between left and right mercury menisci
    ax.plot([1.75, 2.70], [1.55, 1.55], color="#0f172a", lw=0.9)
    ax.annotate("", xy=(1.92, 1.55), xytext=(1.92, 0.95), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.2))
    ax.text(2.02, 1.25, r"$h$", fontsize=11.5, va="center")
    # Density labels
    ax.text(1.05, 1.78, r"$\rho$", fontsize=11)
    ax.annotate(r"$\rho_m$", xy=(1.80, 0.64), xytext=(2.15, 0.22), fontsize=11.5,
                arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.1))
    ax.set_xlim(-0.05, 3.70)
    ax.set_ylim(0.05, 3.65)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q11_orig.png", dpi=220, facecolor="white")
    plt.close(fig)

    # 8. q12_orig: Vertical pipe bend + horizontal nozzle + mercury U-tube
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    fig.patch.set_facecolor("white")
    # Vertical pipe d1 (x in [2.3, 3.1], y from 3.4 down to 1.4), bends to horizontal nozzle at y=1.15
    ax.plot([2.3, 2.3], [3.4, 1.55], color="#0f172a", lw=2.0)
    ax.plot([3.1, 3.1], [3.4, 1.80], color="#0f172a", lw=2.0)
    # Smooth 90 deg elbow arcs
    th_out = np.linspace(np.pi, 1.5 * np.pi, 60)
    ax.plot(3.1 + 0.8 * np.cos(th_out), 1.55 + 0.8 * np.sin(th_out), color="#0f172a", lw=2.0)
    ax.plot(3.1 + 0.35 * np.cos(th_out) + 0.35, 1.80 + 0.35 * np.sin(th_out), color="#0f172a", lw=2.0)
    # Horizontal pipe & converging nozzle
    ax.plot([3.45, 5.15, 5.85], [1.45, 1.45, 1.30], color="#0f172a", lw=2.0)
    ax.plot([3.10, 5.15, 5.85], [0.75, 0.75, 0.90], color="#0f172a", lw=2.0)
    # Centerline & Section 1-1 (y=2.65, elev 20) and Section 2-2 (y=1.10, elev 18)
    ax.plot([2.70, 2.70], [3.50, 1.60], color="#64748b", ls="-.", lw=0.9)
    ax.plot([1.40, 4.20], [2.65, 2.65], color="#0f172a", ls="--", lw=1.0)
    ax.text(2.15, 2.74, "1", fontsize=10.5)
    ax.text(3.22, 2.74, "1", fontsize=10.5)
    draw_water_sym(ax, 3.62, 2.65, s=0.11)
    ax.text(3.82, 2.74, "20", fontsize=10.5)
    ax.annotate("", xy=(2.70, 2.15), xytext=(2.70, 2.65), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.5))
    ax.text(2.80, 2.38, r"$v_1$", fontsize=11)

    ax.plot([5.85, 5.85], [0.65, 1.55], color="#0f172a", ls="--", lw=1.0)
    ax.text(5.85, 1.62, "2", ha="center", fontsize=10.5)
    ax.text(5.85, 0.45, "2", ha="center", fontsize=10.5)
    ax.plot([5.0, 6.95], [1.10, 1.10], color="#0f172a", ls="-.", lw=0.9)
    draw_water_sym(ax, 6.45, 1.10, s=0.11)
    ax.text(6.65, 1.18, "18", fontsize=10.5)
    ax.annotate("", xy=(6.35, 1.10), xytext=(5.85, 1.10), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.5))
    ax.text(6.05, 0.85, r"$v_2$", fontsize=11)

    # U-tube manometer attached on left of 1-1 at y=2.65
    # Right leg at x=1.40, left leg at x=0.70, bottom outer y=1.24, inner y=1.38
    ax.plot([2.30, 1.33, 1.33, 0.77, 0.77], [2.71, 2.71, 1.38, 1.38, 3.05], color="#0f172a", lw=1.6)
    ax.plot([2.30, 1.47, 1.47, 0.63, 0.63], [2.59, 2.59, 1.24, 1.24, 3.05], color="#0f172a", lw=1.6)
    # Mercury in U-tube: right meniscus at y=1.65 (h1 below 2.65), left meniscus at y=2.15 (dh above 1.65)
    ax.add_patch(patches.Rectangle((0.63, 1.24), 0.14, 2.15 - 1.24, facecolor="#1e293b"))
    ax.add_patch(patches.Rectangle((0.63, 1.24), 0.84, 0.14, facecolor="#1e293b"))
    ax.add_patch(patches.Rectangle((1.33, 1.24), 0.14, 1.65 - 1.24, facecolor="#1e293b"))
    ax.annotate("", xy=(0.70, 2.68), xytext=(0.70, 3.18), arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.1))
    ax.text(0.82, 3.02, r"$p_a$", fontsize=10.5)
    # Dimension dh and h1
    ax.plot([0.77, 1.22], [2.15, 2.15], color="#0f172a", lw=0.8)
    ax.plot([0.77, 1.98], [1.65, 1.65], color="#0f172a", lw=0.8)
    ax.annotate("", xy=(1.04, 2.15), xytext=(1.04, 1.65), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.1))
    ax.text(1.06, 1.90, r"$\Delta h$", fontsize=9.8, va="center")
    ax.annotate("", xy=(1.82, 2.65), xytext=(1.82, 1.65), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.1))
    ax.text(1.90, 2.15, r"$h_1$", fontsize=10.5, va="center")
    ax.text(1.42, 0.92, "水银 " + r"$\rho_{\mathrm{Hg}}$", fontsize=9.8, ha="center")

    ax.set_xlim(0.35, 7.15)
    ax.set_ylim(0.28, 3.60)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q12_orig.png", dpi=220, facecolor="white")
    plt.close(fig)

    print(f"[2007] Drew 8 crisp engineering stem figures -> {fig_dir}")


# ==============================================================================
# Clean Matplotlib Solution Diagrams for 2008 & 2007 (dpi=220, ZERO CJK in $...$)
# ==============================================================================

def draw_2008_sol_figures():
    fig_dir = PACK_ROOT / "2008" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. 2008 q22_sol: Curved gate ABC (TRUE circle via set_aspect('equal')!)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 4.4), gridspec_kw={"width_ratios": [1.25, 1.0]})
    fig.patch.set_facecolor("white")

    # Left: Tank + equivalent free surface at z=2 (through A!) + triangular Px diagram
    ax1.add_patch(patches.Rectangle((-2.2, 0.0), 2.2, 3.0, facecolor="#e0f2fe", alpha=0.50))
    # Remove semicircle interior (air)
    th = np.linspace(np.pi / 2, 3 * np.pi / 2, 180)
    semi_x = np.cos(th)
    semi_y = 1.0 + np.sin(th)
    ax1.add_patch(patches.Polygon(list(zip(semi_x, semi_y)) + [(0.0, 0.0), (0.0, 2.0)],
                                  closed=True, facecolor="white", edgecolor="none", zorder=3))
    # Highlight virtual semicircular pressure body ABCOA
    ax1.add_patch(patches.Polygon(list(zip(semi_x, semi_y)) + [(0.0, 0.0), (0.0, 2.0)],
                                  closed=True, facecolor="#fef3c7", edgecolor="#d97706",
                                  hatch="///", lw=1.4, alpha=0.75, zorder=4))
    # Tank walls
    ax1.plot([-2.2, -2.2, 0.0], [3.55, 0.0, 0.0], color="#0f172a", lw=2.2, zorder=5)
    ax1.plot([0.0, 0.0], [2.0, 3.55], color="#0f172a", lw=2.2, zorder=5)
    ax1.plot([-2.2, 0.0], [3.55, 3.55], color="#0f172a", lw=2.2, zorder=5)
    ax1.plot(semi_x, semi_y, color="#0f172a", lw=2.4, zorder=6)
    ax1.plot([-2.2, 0.0], [3.0, 3.0], color="#0284c7", lw=1.8, zorder=5)
    ax1.text(-1.1, 3.28, "真空气体 " + r"$p_0 = -9.8\,\mathrm{kPa}$", ha="center", va="center", fontsize=9.0, color="#334155")

    # Equivalent free surface p=0 at y=2.0 (passing right through A!)
    ax1.plot([-2.45, 0.55], [2.0, 2.0], color="#dc2626", ls="--", lw=1.7, zorder=6)
    ax1.text(-1.15, 2.15, "等效自由液面（" + r"$p=0,\; h=2.0\,\mathrm{m}$" + "）", ha="center", fontsize=8.8, color="#dc2626", fontweight="bold")
    # Triangular horizontal pressure distribution on projection AC
    ax1.add_patch(patches.Polygon([(-1.0, 2.0), (-1.0, 0.0), (-2.05, 0.0)],
                                  closed=True, facecolor="#bae6fd", edgecolor="#0284c7", lw=1.4, alpha=0.80, zorder=5))
    ax1.annotate("", xy=(-1.02, 0.67), xytext=(-1.95, 0.67), arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.2), zorder=6)
    ax1.text(-1.62, 1.52, r"$P_x = 19.60\,\mathrm{kN}$" + "\n（水平向右）", ha="center", va="center", fontsize=8.5,
             color="#0369a1", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.16", facecolor="white", edgecolor="#7dd3fc", alpha=0.95), zorder=7)

    ax1.text(0.10, 2.02, r"$A$", fontsize=10.5, fontweight="bold")
    ax1.text(-1.12, 1.00, r"$B$", fontsize=10.5, fontweight="bold", ha="right", va="center",
             bbox=dict(boxstyle="round,pad=0.06", facecolor="white", edgecolor="none", alpha=0.80), zorder=7)
    ax1.text(0.10, -0.08, r"$C$", fontsize=10.5, fontweight="bold")
    ax1.scatter([0.0], [1.0], color="#0f172a", s=26, zorder=7)
    ax1.text(0.10, 1.0, r"$O$", fontsize=10.5, va="center")
    ax1.text(-0.42, 0.96, "虚压力体\n" + r"$V_z = \frac{1}{2}\pi R^2 b$", ha="center", va="center", fontsize=8.4,
             color="#92400e", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.16", facecolor="#fffbeb", edgecolor="#f59e0b", alpha=0.92), zorder=7)
    ax1.set_xlim(-2.55, 0.72)
    ax1.set_ylim(-0.30, 3.72)
    ax1.set_aspect("equal")
    ax1.axis("off")
    ax1.set_title("（a）等效液面与半圆虚压力体分解", fontsize=10.5, pad=6)

    # Right: True circular arc ABC with resultant force P through O intersecting lower arc BC
    ax2.plot(semi_x, semi_y, color="#0f172a", lw=2.5)
    ax2.plot([0.0, 0.0], [0.0, 2.0], color="#94a3b8", ls=":", lw=1.2)
    ax2.plot([-1.15, 0.35], [1.0, 1.0], color="#94a3b8", ls=":", lw=1.1)
    ax2.scatter([0.0], [1.0], color="#0f172a", s=30, zorder=6)
    ax2.text(0.08, 1.02, r"$O$", fontsize=10.5)
    ax2.text(0.08, 2.00, r"$A$", fontsize=10.5)
    ax2.text(-1.10, 1.00, r"$B$", fontsize=10.5, ha="right", va="center")
    ax2.text(0.08, -0.05, r"$C$", fontsize=10.5)

    theta_rad = np.arctan2(15.394, 19.60)
    xD = -np.cos(theta_rad)
    yD = 1.0 - np.sin(theta_rad)
    ax2.scatter([xD], [yD], color="#dc2626", s=44, zorder=7)
    ax2.text(xD - 0.08, yD - 0.14, r"$D$", fontsize=11, color="#dc2626", fontweight="bold", ha="right")

    # Force arrows at D: Px right, Pz up, P along D -> O
    ax2.annotate("", xy=(0.0, 1.0), xytext=(xD, yD),
                 arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.6), zorder=7)
    ax2.annotate("", xy=(xD + 0.68, yD), xytext=(xD, yD),
                 arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.0), zorder=6)
    ax2.annotate("", xy=(xD, yD + 0.54), xytext=(xD, yD),
                 arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.0), zorder=6)

    ax2.text(0.10, 1.38, "合力 " + r"$P = 24.92\,\mathrm{kN}$" + "\n过圆心 " + r"$O$" + "，倾角 " + r"$38.15^{\circ}$",
             fontsize=9.2, color="#dc2626", fontweight="bold")
    ax2.text(0.10, 0.42, r"$P_x = 19.60\,\mathrm{kN}\;\rightarrow$" + "\n" + r"$P_z = 15.39\,\mathrm{kN}\;\uparrow$",
             fontsize=9.0, color="#0f172a")
    ax2.text(-0.20, -0.28, "作用点 " + r"$D$" + " 位于 " + r"$A$" + " 下方 " + r"$1.618\,\mathrm{m}$",
             ha="center", fontsize=9.0, color="#dc2626", fontweight="bold")

    ax2.set_xlim(-1.35, 1.48)
    ax2.set_ylim(-0.42, 2.25)
    ax2.set_aspect("equal")
    ax2.axis("off")
    ax2.set_title("（b）合力方向与作用点 " + r"$D$" + " 位置", fontsize=10.5, pad=6)

    plt.tight_layout()
    fig.savefig(fig_dir / "q22_sol.png", dpi=220, facecolor="white")
    plt.close(fig)

    # 2. 2008 q23_sol: Side orifice trajectories + range curve
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.0, 3.9), gridspec_kw={"width_ratios": [1.15, 1.0]})
    fig.patch.set_facecolor("white")
    ax1.add_patch(patches.Rectangle((-0.45, 0.0), 0.45, 1.0, facecolor="#bae6fd", alpha=0.65))
    ax1.plot([-0.45, -0.45, 0.0, 0.0], [1.12, 0.0, 0.0, 1.12], color="#0f172a", lw=2.1)
    ax1.plot([-0.45, 0.0], [1.0, 1.0], color="#0284c7", lw=2.0)
    ax1.plot([-0.5, 1.22], [0.0, 0.0], color="#334155", lw=1.8)
    for ratio, col, ls, lbl in [
        (0.2, "#0284c7", "--", r"$h = 0.2H \Rightarrow x = 0.8H$"),
        (0.5, "#dc2626", "-", r"$h = 0.5H \Rightarrow x_{\max} = H$"),
        (0.8, "#16a34a", "-.", r"$h = 0.8H \Rightarrow x = 0.8H$"),
    ]:
        xmax = 2.0 * np.sqrt(ratio * (1.0 - ratio))
        xs = np.linspace(0, xmax, 100)
        ys = ratio - (xs**2) / (4.0 * (1.0 - ratio))
        ax1.plot(xs, ys, color=col, ls=ls, lw=2.1, label=lbl)
        ax1.scatter([0.0], [ratio], color=col, s=22, zorder=5)
    ax1.annotate("", xy=(1.0, -0.10), xytext=(0.0, -0.10), arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.5))
    ax1.text(0.5, -0.22, r"$x_{\max} = H$", ha="center", fontsize=9.8, color="#dc2626", fontweight="bold")
    ax1.legend(loc="upper right", frameon=True, fontsize=8.5)
    ax1.set_xlim(-0.55, 1.30)
    ax1.set_ylim(-0.30, 1.22)
    ax1.axis("off")
    ax1.set_title("（a）不同孔口高度平抛射流轨迹对比", fontsize=10.5, pad=6)

    eta = np.linspace(0.0, 1.0, 200)
    xi = 2.0 * np.sqrt(eta * (1.0 - eta))
    ax2.plot(xi, eta, color="#0284c7", lw=2.3)
    ax2.scatter([1.0], [0.5], color="#dc2626", s=42, zorder=5)
    ax2.plot([0, 1.0], [0.5, 0.5], color="#dc2626", ls="--", lw=1.3)
    ax2.plot([1.0, 1.0], [0, 0.5], color="#dc2626", ls="--", lw=1.3)
    ax2.text(0.54, 0.56, "极值点：" + r"$h = \dfrac{H}{2},\; x_{\max} = H$", fontsize=9.1, color="#dc2626", fontweight="bold")
    ax2.set_xlabel("无量纲水平射程 " + r"$x / H$", fontsize=9.8)
    ax2.set_ylabel("无量纲孔口高度 " + r"$h / H$", fontsize=9.8)
    ax2.set_xlim(0.0, 1.18)
    ax2.set_ylim(0.0, 1.08)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.set_title("（b）无量纲射程曲线 " + r"$x/H = 2\sqrt{(h/H)(1-h/H)}$", fontsize=10.2, pad=6)
    plt.tight_layout()
    fig.savefig(fig_dir / "q23_sol.png", dpi=220, facecolor="white")
    plt.close(fig)

    # 3. 2008 q24_sol: Whole-system CV on platform scale (top inlet, 2 symmetric bottom outlets)
    fig, ax = plt.subplots(figsize=(7.8, 4.3))
    fig.patch.set_facecolor("white")
    ax.add_patch(patches.Rectangle((1.2, 0.35), 3.6, 0.30, facecolor="#cbd5e1", edgecolor="#0f172a", lw=1.8))
    ax.plot([0.7, 5.3], [0.20, 0.20], color="#0f172a", lw=2.2)
    # Stand legs
    ax.plot([2.0, 2.25], [0.65, 1.05], color="#0f172a", lw=2.5)
    ax.plot([4.0, 3.75], [0.65, 1.05], color="#0f172a", lw=2.5)
    # Tank + water (0.9 m depth)
    ax.add_patch(patches.Rectangle((1.35, 1.05), 3.30, 1.80, facecolor="#bae6fd", alpha=0.65))
    ax.plot([1.35, 1.35, 2.78, 2.78], [1.28, 3.10, 3.10, 3.50], color="#0f172a", lw=2.1)
    ax.plot([4.65, 4.65, 3.22, 3.22], [1.28, 3.10, 3.10, 3.50], color="#0f172a", lw=2.1)
    ax.plot([0.85, 5.15], [1.05, 1.05], color="#0f172a", lw=2.1)
    ax.plot([0.85, 1.35], [1.28, 1.28], color="#0f172a", lw=1.9)
    ax.plot([4.65, 5.15], [1.28, 1.28], color="#0f172a", lw=1.9)
    ax.plot([1.35, 4.65], [2.85, 2.85], color="#0284c7", lw=2.0)

    # Top inlet arrow
    ax.annotate("", xy=(3.0, 2.88), xytext=(3.0, 3.92), arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.6))
    ax.text(3.25, 3.65, "铅直入射 " + r"$V_1 = 5\,\mathrm{m/s},\; Q = 0.025\,\mathrm{m^3/s}$" + "\n动量冲击 " + r"$\rho Q V_1 = 125\,\mathrm{N}$",
            fontsize=9.1, va="center", color="#0369a1", fontweight="bold")
    # Two horizontal bottom outlets
    ax.annotate("", xy=(0.15, 1.16), xytext=(0.95, 1.16), arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.1))
    ax.annotate("", xy=(5.85, 1.16), xytext=(5.05, 1.16), arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.1))
    ax.text(0.55, 1.48, "水平出流\n" + r"$v_{2z} = 0$", ha="center", fontsize=8.8, color="#0369a1")
    ax.text(5.45, 1.48, "水平出流\n" + r"$v_{2z} = 0$", ha="center", fontsize=8.8, color="#0369a1")

    # Dashed whole-system CV
    ax.add_patch(patches.Rectangle((1.05, 0.72), 3.90, 2.62, fill=False, edgecolor="#dc2626", ls="--", lw=1.7))
    ax.text(5.08, 3.12, "整体控制体\n（水箱 + 支架 + 水）", fontsize=9.0, color="#dc2626", va="top")

    # Gravity and Scale support reaction N
    ax.annotate("", xy=(2.10, 1.48), xytext=(2.10, 2.52), arrowprops=dict(arrowstyle="->", color="#ea580c", lw=2.3))
    ax.text(2.22, 2.28, "总重 " + r"$G_{\mathrm{tank}} + G_{\mathrm{water}}$" + "\n" + r"$= 392 + 8820 = 9212\,\mathrm{N}$",
            ha="left", va="center", fontsize=8.8, color="#c2410c", fontweight="bold")
    ax.annotate("", xy=(2.95, 1.72), xytext=(2.95, 0.45), arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.7))
    ax.text(3.08, 1.45, "磅秤读数 " + r"$N = 9337\,\mathrm{N}$" + "\n（" + r"$g=9.80\,\mathrm{m/s^2}$" + "）",
            ha="left", va="center", fontsize=9.1, color="#15803d", fontweight="bold")

    ax.set_xlim(-0.15, 6.75)
    ax.set_ylim(0.05, 4.10)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q24_sol.png", dpi=220, facecolor="white")
    plt.close(fig)

    # 4. 2008 q25_sol: Siphon A-B-C with exact submerged exit HGL/EGL boundary
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    fig.patch.set_facecolor("white")
    # Upstream well WS y=1.80, Downstream basin WS y=0.60, Apex B y=3.45
    ax.add_patch(patches.Rectangle((0.6, 0.1), 1.0, 1.70, facecolor="#e0f2fe", alpha=0.60))
    ax.plot([0.6, 0.6, 1.6, 1.6], [2.1, 0.1, 0.1, 2.1], color="#0f172a", lw=1.9)
    ax.plot([0.6, 1.6], [1.80, 1.80], color="#0284c7", lw=2.0)

    ax.add_patch(patches.Rectangle((5.4, 0.0), 2.3, 0.60, facecolor="#e0f2fe", alpha=0.60))
    ax.plot([5.4, 5.4, 7.7], [1.2, 0.0, 0.0], color="#0f172a", lw=1.9)
    ax.plot([5.4, 7.7], [0.60, 0.60], color="#0284c7", lw=2.0)
    # Hill outline
    ax.plot([1.6, 2.8, 5.4], [2.1, 3.22, 1.2], color="#475569", lw=1.7)

    # Siphon pipe A -> bend1 -> B -> C
    sx = [1.20, 1.20, 2.85, 6.50]
    sy = [1.15, 2.05, 3.45, 0.30]
    ax.plot(sx, sy, color="#0f172a", lw=4.5, solid_capstyle="round")
    ax.plot(sx, sy, color="#bae6fd", lw=2.2, solid_capstyle="round")
    ax.scatter([2.85], [3.45], color="#dc2626", s=40, zorder=6)
    ax.text(2.85, 3.62, "虹吸管顶点 " + r"$B$", fontsize=9.8, ha="center", color="#dc2626", fontweight="bold")
    ax.text(0.92, 1.15, r"$A$", fontsize=10.5, ha="center", va="center", fontweight="bold")
    ax.text(6.65, 0.25, r"$C$", fontsize=10.5, fontweight="bold")

    # Exact EGL & HGL: HGL meets downstream WS (y=0.60) smoothly at submerged exit x=6.50;
    # EGL stays vh=0.22 above HGL and drops vertically by zeta_4*v^2/(2g)=0.22 at x=6.50!
    vh = 0.22
    hx = [1.20, 2.85, 6.50]
    hgl_y = [1.50, 1.12, 0.60]
    egl_y = [y + vh for y in hgl_y]  # [1.72, 1.34, 0.82]
    ax.plot([0.80, 1.20] + hx + [6.50], [1.80, 1.80] + egl_y + [0.60],
            color="#16a34a", lw=1.9, ls="--", label="总水头线 (E.G.L.)")
    ax.plot([1.20] + hx, [1.80] + hgl_y,
            color="#7c3aed", lw=1.9, ls="-.", label="测压管水头线 (H.G.L.)")

    # Vacuum head at B
    ax.annotate("", xy=(2.85, 3.42), xytext=(2.85, hgl_y[1]),
                arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.7), zorder=6)
    ax.text(3.00, 2.38, "顶点最大真空度\n" + r"$h_{v,B} = 5.34\,\mathrm{m} < [h_v] = 7\,\mathrm{m}$" + "\n（满足安全要求）",
            fontsize=8.9, ha="left", va="center", color="#dc2626", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.24", facecolor="white", edgecolor="#fca5a5", alpha=0.95), zorder=7)

    # Dimension H=1.60 m
    ax.plot([1.60, 7.15], [1.80, 1.80], color="#94a3b8", ls=":", lw=1.0)
    ax.annotate("", xy=(7.00, 1.80), xytext=(7.00, 0.60), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.3))
    ax.text(7.10, 1.20, r"$H = 1.60\,\mathrm{m}$", fontsize=9.6, va="center")

    ax.legend(loc="upper right", frameon=True, fontsize=8.8)
    ax.set_xlim(0.35, 8.20)
    ax.set_ylim(-0.18, 3.92)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q25_sol.png", dpi=220, facecolor="white")
    plt.close(fig)

    print(f"[2008] Drew 4 matplotlib solution figures -> {fig_dir}")


def draw_2007_sol_figures():
    fig_dir = PACK_ROOT / "2007" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. 2007 q05_sol: Streamlines psi1, psi2 & arbitrary curve AB flux element
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    fig.patch.set_facecolor("white")
    xs = np.linspace(0.4, 6.2, 160)
    y1 = 0.75 + 0.35 * np.sin(0.55 * xs)
    y2 = 2.55 + 0.38 * np.sin(0.55 * xs - 0.3)
    ax.plot(xs, y1, color="#0284c7", lw=2.3)
    ax.plot(xs, y2, color="#0284c7", lw=2.3)
    ax.text(5.75, y1[-15] - 0.25, "流线 1：" + r"$\psi = \psi_1$", fontsize=9.8, color="#0369a1", fontweight="bold")
    ax.text(5.75, y2[-15] + 0.18, "流线 2：" + r"$\psi = \psi_2$", fontsize=9.8, color="#0369a1", fontweight="bold")

    # Arbitrary curve AB connecting A on psi1 to B on psi2
    t = np.linspace(0, 1, 100)
    xA, yA = 2.0, 0.75 + 0.35 * np.sin(0.55 * 2.0)
    xB, yB = 3.6, 2.55 + 0.38 * np.sin(0.55 * 3.6 - 0.3)
    xc = xA + (xB - xA) * t + 0.35 * np.sin(np.pi * t)
    yc = yA + (yB - yA) * t
    ax.plot(xc, yc, color="#dc2626", lw=2.2, ls="--")
    ax.scatter([xA, xB], [yA, yB], color="#dc2626", s=40, zorder=5)
    ax.text(xA - 0.15, yA - 0.22, r"$A(\psi_1)$", fontsize=10, color="#dc2626", fontweight="bold", ha="right")
    ax.text(xB - 0.12, yB + 0.18, r"$B(\psi_2)$", fontsize=10, color="#dc2626", fontweight="bold", ha="right")

    # Highlight differential triangle (dx, dy, ds) around t=0.52
    xm, ym = xc[52], yc[52]
    dx, dy = 0.42, 0.48
    ax.plot([xm, xm + dx, xm + dx], [ym, ym, ym + dy], color="#0f172a", lw=1.4)
    ax.plot([xm, xm + dx], [ym, ym + dy], color="#dc2626", lw=2.8)
    ax.text(xm + dx * 0.5, ym - 0.16, r"$\mathrm{d}x$", fontsize=9.8, ha="center")
    ax.text(xm + dx + 0.10, ym + dy * 0.5, r"$\mathrm{d}y$", fontsize=9.8, va="center")
    ax.text(xm + 0.04, ym + 0.36, r"$\mathrm{d}s$", fontsize=9.8, color="#dc2626", fontweight="bold")

    # Velocity arrows ux, uy passing across dy and dx
    ax.annotate("", xy=(xm + dx + 0.55, ym + 0.24), xytext=(xm + dx - 0.15, ym + 0.24),
                arrowprops=dict(arrowstyle="->", color="#16a34a", lw=1.8))
    ax.text(xm + dx + 0.60, ym + 0.24, r"$u_x$", fontsize=10, color="#15803d", va="center", fontweight="bold")
    ax.annotate("", xy=(xm + 0.20, ym + 0.32), xytext=(xm + 0.20, ym - 0.35),
                arrowprops=dict(arrowstyle="->", color="#16a34a", lw=1.8))
    ax.text(xm + 0.02, ym - 0.38, r"$u_y$", fontsize=10, color="#15803d", fontweight="bold")

    ax.text(4.65, 1.55, r"$\mathrm{d}q = u_x\mathrm{d}y - u_y\mathrm{d}x = \mathrm{d}\psi$" + "\n" + r"$q_{AB} = \int_A^B \mathrm{d}\psi = \psi_2 - \psi_1$",
            fontsize=9.6, color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.30", facecolor="#f8fafc", edgecolor="#94a3b8"))
    ax.set_xlim(0.2, 6.85)
    ax.set_ylim(0.15, 3.45)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q05_sol.png", dpi=220, facecolor="white")
    plt.close(fig)

    # 2. 2007 q07_sol: True-circle hemispherical gate pressure-body cancellation & net Px
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 4.2), gridspec_kw={"width_ratios": [1.2, 1.0]})
    fig.patch.set_facecolor("white")

    th = np.linspace(np.pi / 2, 3 * np.pi / 2, 180)
    sx, sy = np.cos(th), 1.0 + np.sin(th)
    ax1.add_patch(patches.Rectangle((-2.1, 0.0), 2.1, 3.0, facecolor="#e0f2fe", alpha=0.50))
    ax1.add_patch(patches.Rectangle((0.0, 0.0), 1.6, 2.0, facecolor="#bae6fd", alpha=0.55))
    ax1.add_patch(patches.Polygon(list(zip(sx, sy)) + [(0.0, 0.0), (0.0, 2.0)],
                                  closed=True, facecolor="#fde68a", edgecolor="#d97706", hatch="///", alpha=0.75, zorder=4))
    ax1.plot([-2.1, 1.6], [0.0, 0.0], color="#0f172a", lw=2.2)
    ax1.plot([0.0, 0.0], [2.0, 3.3], color="#0f172a", lw=2.2)
    ax1.plot(sx, sy, color="#0f172a", lw=2.4, zorder=5)
    ax1.plot([-2.1, 0.0], [3.0, 3.0], color="#0284c7", lw=2.0)
    ax1.plot([0.0, 1.6], [2.0, 2.0], color="#0284c7", lw=2.0)

    # Upward Pz1 (from left convex water) and downward Pz2 (from right concave water)
    ax1.annotate("", xy=(-0.55, 2.45), xytext=(-0.55, 1.25), arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.5), zorder=6)
    ax1.text(-1.95, 2.55, "左侧水体向上浮托\n" + r"$P_{z1} = \frac{2}{3}\pi\rho g R^3\;\uparrow$",
             fontsize=8.8, color="#15803d", fontweight="bold")
    ax1.annotate("", xy=(-0.30, 0.15), xytext=(-0.30, 1.25), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.5), zorder=6)
    ax1.text(0.15, 0.95, "右侧凹腔水体重力\n" + r"$P_{z2} = \frac{2}{3}\pi\rho g R^3\;\downarrow$" + "\n" + r"$\Rightarrow P_z = P_{z1} - P_{z2} = 0$",
             fontsize=8.8, color="#b91c1c", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#fca5a5", alpha=0.95), zorder=7)
    ax1.set_xlim(-2.25, 1.85)
    ax1.set_ylim(-0.25, 3.45)
    ax1.set_aspect("equal")
    ax1.axis("off")
    ax1.set_title("（a）左右两侧半球压力体抵消（" + r"$P_z = 0$" + "）", fontsize=10.2, pad=6)

    # Right: Uniform net pressure difference Δp = ρgH on vertical projected circle πR²
    ax2.plot(sx, sy, color="#0f172a", lw=2.4)
    ax2.plot([0.0, 0.0], [0.0, 2.0], color="#0284c7", ls="--", lw=1.5)
    ax2.add_patch(patches.Rectangle((-1.85, 0.0), 0.75, 2.0, facecolor="#bae6fd", edgecolor="#0284c7", lw=1.4, alpha=0.75))
    for yp in (0.35, 1.0, 1.65):
        ax2.annotate("", xy=(-1.12, yp), xytext=(-1.82, yp), arrowprops=dict(arrowstyle="->", color="#0284c7", lw=1.6))
    ax2.text(-1.48, 2.18, "均布净压强差\n" + r"$\Delta p = \rho g H$", ha="center", fontsize=9.0, color="#0369a1", fontweight="bold")
    ax2.annotate("", xy=(0.95, 1.0), xytext=(-0.35, 1.0), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.8), zorder=6)
    ax2.text(0.15, 1.48, "净水平推力（向右）\n" + r"$P_x = \rho g H \cdot \pi R^2$" + "\n" + r"$= 30.79\,\mathrm{kN}$",
             fontsize=9.3, color="#dc2626", fontweight="bold")
    ax2.set_xlim(-2.10, 1.65)
    ax2.set_ylim(-0.25, 2.65)
    ax2.set_aspect("equal")
    ax2.axis("off")
    ax2.set_title("（b）水平投影圆 " + r"$A_x = \pi R^2$" + " 净推力", fontsize=10.2, pad=6)
    plt.tight_layout()
    fig.savefig(fig_dir / "q07_sol.png", dpi=220, facecolor="white")
    plt.close(fig)

    # 3. 2007 q10_sol: Inclined 60 deg plate CV & tangential momentum balance
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    fig.patch.set_facecolor("white")
    ang = np.radians(60)
    t_vec = np.array([np.cos(ang), np.sin(ang)])
    n_vec = np.array([-np.sin(ang), np.cos(ang)])
    L = 2.05
    ax.plot([-L * t_vec[0], L * t_vec[0]], [-L * t_vec[1], L * t_vec[1]], color="#0f172a", lw=3.0)
    # Dashed CV around impingement zone
    cv_pts = [(-1.55, 0.25), (-1.55, -0.25), -1.35 * t_vec + 0.16 * n_vec, -1.35 * t_vec + 0.02 * n_vec,
              1.35 * t_vec + 0.02 * n_vec, 1.35 * t_vec + 0.24 * n_vec]
    ax.add_patch(patches.Polygon(cv_pts, closed=True, facecolor="#bae6fd", edgecolor="#dc2626", ls="--", lw=1.6, alpha=0.65))
    # Incoming jet
    ax.annotate("", xy=(-0.55, 0.0), xytext=(-1.95, 0.0), arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.3))
    ax.text(-2.05, 0.0, "入射射流 " + r"$v,\; Q$", ha="right", va="center", fontsize=9.8, color="#0369a1", fontweight="bold")
    # Split jets
    ax.annotate("", xy=1.75 * t_vec + 0.15 * n_vec, xytext=0.75 * t_vec + 0.15 * n_vec,
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.3))
    ax.text(1.75 * t_vec[0] - 0.68, 1.75 * t_vec[1] + 0.25, r"$v_1 = v,\; Q_1$", fontsize=9.8, color="#0369a1", fontweight="bold")
    ax.annotate("", xy=-1.75 * t_vec + 0.12 * n_vec, xytext=-0.85 * t_vec + 0.12 * n_vec,
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.1))
    ax.text(-1.75 * t_vec[0] - 0.95, -1.75 * t_vec[1] - 0.12, r"$v_2 = v,\; Q_2$", fontsize=9.8, color="#0369a1", fontweight="bold")
    # Normal reaction R_n and tangential axis s
    ax.annotate("", xy=0.95 * n_vec, xytext=(0.0, 0.0), arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.2))
    ax.text(1.02 * n_vec[0] - 0.10, 1.02 * n_vec[1] + 0.12, "法向反力 " + r"$R_n$" + "\n（切向摩阻 " + r"$F_s = 0$" + "）",
            ha="right", fontsize=9.0, color="#dc2626", fontweight="bold")
    ax.annotate("", xy=1.85 * t_vec - 0.28 * n_vec, xytext=1.15 * t_vec - 0.28 * n_vec,
                arrowprops=dict(arrowstyle="->", color="#16a34a", lw=2.0))
    ax.text(1.90 * t_vec[0] + 0.22, 1.90 * t_vec[1] - 0.28, r"$+s$" + " 切向轴", fontsize=9.3, color="#15803d", fontweight="bold")
    # Angle 60 deg
    ax.plot([-0.1, 1.55], [0.0, 0.0], color="#64748b", ls=":", lw=1.2)
    ax.add_patch(patches.Arc((0, 0), 0.95, 0.95, theta1=0, theta2=60, color="#0f172a", lw=1.2))
    ax.text(0.58, 0.22, r"$60^{\circ}$", fontsize=10.5)
    ax.text(1.35, -1.05, "沿切向列动量方程：\n" + r"$0 = \rho v(Q_1 - Q_2 - Q\cos 60^{\circ})$" + "\n" + r"$\Rightarrow \dfrac{Q_1}{Q_2} = \dfrac{1 + \cos 60^{\circ}}{1 - \cos 60^{\circ}} = 3$",
            fontsize=9.2, color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.28", facecolor="#f8fafc", edgecolor="#94a3b8"))
    ax.set_xlim(-3.25, 3.15)
    ax.set_ylim(-2.10, 2.25)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q10_sol.png", dpi=220, facecolor="white")
    plt.close(fig)

    # 4. 2007 q13_sol: Free vortex (irrotational + shear deformation) vs Forced vortex (rotational + rigid)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.0, 4.2))
    fig.patch.set_facecolor("white")
    grid = np.linspace(-1.8, 1.8, 13)
    X, Y = np.meshgrid(grid, grid)
    R2 = X**2 + Y**2
    mask = R2 > 0.32
    # (1) Free vortex: u = -y/r^2, v = x/r^2
    U1 = np.where(mask, -Y / np.maximum(R2, 0.32), np.nan)
    V1 = np.where(mask, X / np.maximum(R2, 0.32), np.nan)
    ax1.quiver(X, Y, U1, V1, color="#0284c7", scale=14, width=0.006)
    for rad in (0.65, 1.25):
        ax1.add_patch(patches.Circle((0, 0), rad, fill=False, edgecolor="#94a3b8", ls="--", lw=1.0))
    ax1.scatter([0], [0], color="#dc2626", s=38, zorder=5)
    ax1.text(0.0, -2.18, "无旋有变形（自由涡 / 点涡）\n" + r"$\omega_z = 0,\; \varepsilon_{xx}, \varepsilon_{yy}, \varepsilon_{xy} \neq 0$",
             ha="center", va="top", fontsize=9.2, color="#0369a1", fontweight="bold")
    ax1.set_xlim(-2.05, 2.05)
    ax1.set_ylim(-2.10, 2.05)
    ax1.set_aspect("equal")
    ax1.axis("off")
    ax1.set_title("（1）" + r"$u_x = -\dfrac{ay}{x^2+y^2},\; u_y = \dfrac{ax}{x^2+y^2}$", fontsize=10.0, pad=6)

    # (2) Forced vortex (solid-body rotation): u = -y, v = x
    U2 = -Y
    V2 = X
    ax2.quiver(X, Y, U2, V2, color="#16a34a", scale=22, width=0.006)
    for rad in (0.65, 1.25):
        ax2.add_patch(patches.Circle((0, 0), rad, fill=False, edgecolor="#94a3b8", ls="--", lw=1.0))
    ax2.scatter([0], [0], color="#0f172a", s=30, zorder=5)
    ax2.text(0.0, -2.18, "有旋无变形（刚体旋转 / 强迫涡）\n" + r"$\omega_z = b \neq 0,\; \varepsilon_{xx} = \varepsilon_{yy} = \varepsilon_{xy} = 0$",
             ha="center", va="top", fontsize=9.2, color="#15803d", fontweight="bold")
    ax2.set_xlim(-2.05, 2.05)
    ax2.set_ylim(-2.10, 2.05)
    ax2.set_aspect("equal")
    ax2.axis("off")
    ax2.set_title("（2）" + r"$u_x = -by,\; u_y = bx$", fontsize=10.0, pad=6)

    plt.tight_layout()
    fig.savefig(fig_dir / "q13_sol.png", dpi=220, facecolor="white")
    plt.close(fig)

    print(f"[2007] Drew 4 matplotlib solution figures -> {fig_dir}")


# ==============================================================================
# Build Standardized JSON Dictionaries for 2008 & 2007
# ==============================================================================

def build_2008_paper() -> dict:
    return {
        "year": 2008,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "全卷共 27 题：一、单项选择题（10×3=30 分）；二、填空题（10×2=20 分）；三、计算与推导题（6×15 + 1×10 = 100 分）。",
            "结合题干参数（如 $p_0 = -9.8\\,\\mathrm{kPa}$、$p_k = 24.5\\,\\mathrm{kN/m^2}$），常温清水密度取 $\\rho = 1000\\,\\mathrm{kg/m^3}$，重力加速度取 $g = 9.80\\,\\mathrm{m/s^2}$（解析同步列出 $g = 9.81\\,\\mathrm{m/s^2}$ 对照值）。"
        ],
        "sections": [
            {
                "id": "single_choice",
                "title": "一、单项选择题",
                "description": "第 1～10 题，每小题 3 分，共 30 分。",
                "range": [1, 10],
                "scorePerQuestion": 3,
                "totalScore": 30
            },
            {
                "id": "fill",
                "title": "二、填空题",
                "description": "第 11～20 题，每小题 2 分，共 20 分。",
                "range": [11, 20],
                "scorePerQuestion": 2,
                "totalScore": 20
            },
            {
                "id": "calc",
                "title": "三、计算与推导题",
                "description": "第 21～27 题（15×5 + 10 + 15 分），共 100 分。",
                "range": [21, 27],
                "totalScore": 100
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2008-01",
                "year": 2008,
                "no": 1,
                "type": "single_choice",
                "score": 3,
                "title": "液体动力黏滞系数的国际单位判别",
                "stem": "液体的动力粘滞系数的单位是：",
                "options": [
                    {"label": "A", "text": "$\\mathrm{m^2/s}$"},
                    {"label": "B", "text": "$(\\mathrm{N\\cdot s})/\\mathrm{m^2}$"},
                    {"label": "C", "text": "$\\mathrm{N/m^2}$"},
                    {"label": "D", "text": "$\\mathrm{Pa/s}$"}
                ],
                "choiceAnswer": "B",
                "note": "",
                "figures": [],
                "shortAnswer": "B",
                "judgeAnswer": None,
                "answer": "**B**（$(\\mathrm{N\\cdot s})/\\mathrm{m^2} = \\mathrm{Pa\\cdot s}$）",
                "analysis": "由牛顿内摩擦定律 $\\tau = \\mu \\frac{\\mathrm{d}u}{\\mathrm{d}y}$ 解出动力黏滞系数（动力黏度）$\\mu = \\frac{\\tau}{\\mathrm{d}u/\\mathrm{d}y}$，其国际单位为：\n\n$$\n[\\mu] = \\frac{\\mathrm{N/m^2}}{(\\mathrm{m/s})/\\mathrm{m}} = \\frac{\\mathrm{N\\cdot s}}{\\mathrm{m^2}} = \\mathrm{Pa\\cdot s}\n$$\n\n选项 A（$\\mathrm{m^2/s}$）是运动黏度 $\\nu$ 的单位；选项 C（$\\mathrm{N/m^2}$）是压强或切应力的单位；选项 D 为 $\\mathrm{Pa/s}$（多了除号，易与 $\\mathrm{Pa\\cdot s}$ 混淆）。故选 **B**。",
                "analysisFigures": [],
                "pitfalls": "审题切忌把 D 项的 $\\mathrm{Pa/s}$ 误看成 $\\mathrm{Pa\\cdot s}$！$\\mathrm{Pa\\cdot s} = (\\mathrm{N/m^2})\\cdot\\mathrm{s} = (\\mathrm{N\\cdot s})/\\mathrm{m^2}$。",
                "chapter": 1,
                "kps": ["动力黏度与运动黏度", "牛顿内摩擦定律"],
                "method": "物理量量纲与单位推导法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-02",
                "year": 2008,
                "no": 2,
                "type": "single_choice",
                "score": 3,
                "title": "等直径管恒定流动测压管水头线沿程变化规律",
                "stem": "水流在等直径管中作恒定流动时，其测压管水头线沿程：",
                "options": [
                    {"label": "A", "text": "下降"},
                    {"label": "B", "text": "不变"},
                    {"label": "C", "text": "上升"},
                    {"label": "D", "text": "可上升，亦可下降"}
                ],
                "choiceAnswer": "A",
                "note": "",
                "figures": [],
                "shortAnswer": "A",
                "judgeAnswer": None,
                "answer": "**A**（下降）",
                "analysis": "对不可压缩实际流体在**等直径管道**中的恒定流，由连续性方程 $Q = A v = \\text{const}$ 且断面面积 $A$ 不变，故断面平均流速 $v$ 及流速水头 $\\frac{\\alpha v^2}{2g}$ 沿程恒定不变。由能量方程：\n\n$$\n\\left(z_1 + \\frac{p_1}{\\rho g}\\right) - \\left(z_2 + \\frac{p_2}{\\rho g}\\right) = h_{w1\\text{-}2} > 0\n$$\n\n测压管水头线与总水头线互相平行，因实际流动沿程总有水头损失 $h_w > 0$，无论管道水平、上坡还是下坡，测压管水头线沿程**必然单调下降**。故选 **A**。",
                "analysisFigures": [],
                "pitfalls": "只有**变直径扩散管**才可能出现测压管水头线沿程上升！本题明确限定为“等直径管”，速度水头不变，故测压管水头线必沿程下降。",
                "chapter": 3,
                "kps": ["测压管水头", "实际液体恒定总流能量方程"],
                "method": "总水头线与测压管水头线定性分析法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-03",
                "year": 2008,
                "no": 3,
                "type": "single_choice",
                "score": 3,
                "title": "液体发生真空时绝对压强与相对压强符号判别",
                "stem": "液体中某点发生真空时，该点的：",
                "options": [
                    {"label": "A", "text": "绝对压强为负值"},
                    {"label": "B", "text": "相对压强为负值"},
                    {"label": "C", "text": "绝对压强小于相对压强"},
                    {"label": "D", "text": "绝对压强大于大气压强"}
                ],
                "choiceAnswer": "B",
                "note": "",
                "figures": [],
                "shortAnswer": "B",
                "judgeAnswer": None,
                "answer": "**B**（相对压强为负值）",
                "analysis": "液体中某点发生真空是指该点的绝对压强小于当地大气压强（$0 < p_{\\text{绝}} < p_a$）。由相对压强（表压）定义 $p_{\\text{相}} = p_{\\text{绝}} - p_a$ 可知，发生真空时**相对压强为负值**（$p_{\\text{相}} < 0$），而绝对压强恒为非负值（$p_{\\text{绝}} \\ge 0$），且 $p_{\\text{绝}} = p_a + p_{\\text{相}} > p_{\\text{相}}$。故选 **B**。",
                "analysisFigures": [],
                "pitfalls": "绝对压强以绝对零压为基准，物理上不可能为负；真空压强 $p_v = p_a - p_{\\text{绝}} = -p_{\\text{相}}$ 为正值，对应的相对压强 $p_{\\text{相}}$ 为负值。",
                "chapter": 2,
                "kps": ["绝对压强、相对压强与真空度"],
                "method": "物理概念定义辨析",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-04",
                "year": 2008,
                "no": 4,
                "type": "single_choice",
                "score": 3,
                "title": "同流量同断面参数下明渠底坡对正常水深的影响",
                "stem": "有两条梯形断面渠道 1 和 2，已知其流量、边坡系数、底宽和糙率相同，底坡 $i_1 > i_2$，则其均匀流水深 $h_{01}$ 和 $h_{02}$ 的关系为：",
                "options": [
                    {"label": "A", "text": "$h_{01} > h_{02}$"},
                    {"label": "B", "text": "$h_{01} = h_{02}$"},
                    {"label": "C", "text": "$h_{01} < h_{02}$"},
                    {"label": "D", "text": "$h_{01} \\le h_{02}$"}
                ],
                "choiceAnswer": "C",
                "note": "",
                "figures": [],
                "shortAnswer": "C",
                "judgeAnswer": None,
                "answer": "**C**（$h_{01} < h_{02}$）",
                "analysis": "由明渠均匀流曼宁公式 $Q = K(h_0)\\sqrt{i}$，当流量 $Q$ 相同时，流量模数满足：\n\n$$\nK(h_0) = \\frac{1}{n} A R^{2/3} = \\frac{Q}{\\sqrt{i}}\n$$\n\n因 $i_1 > i_2$，故 $K(h_{01}) < K(h_{02})$。对底宽 $b$、边坡系数 $m$ 与糙率 $n$ 相同的梯形单式断面渠道，流量模数 $K(h_0)$ 随水深 $h_0$ 单调严格递增，因此必有 $h_{01} < h_{02}$（底坡越陡，流速越快，通过相同流量所需的正常水深越浅）。故选 **C**。",
                "analysisFigures": [],
                "pitfalls": "牢记直观物理规律：同一流量下，渠底越陡（$i$ 越大），水流跑得越快，过水断面越扁浅（正常水深 $h_0$ 越小）。",
                "chapter": 7,
                "kps": ["明渠均匀流", "曼宁公式", "流量模数"],
                "method": "明渠均匀流流量模数单调性分析法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-05",
                "year": 2008,
                "no": 5,
                "type": "single_choice",
                "score": 3,
                "title": "无支流串联管道各管段基本水力特征",
                "stem": "串联管道，无支流分出，则各管段的：",
                "options": [
                    {"label": "A", "text": "流量相等"},
                    {"label": "B", "text": "切应力相等"},
                    {"label": "C", "text": "沿程水头损失相等"},
                    {"label": "D", "text": "水力坡度相等"}
                ],
                "choiceAnswer": "A",
                "note": "",
                "figures": [],
                "shortAnswer": "A",
                "judgeAnswer": None,
                "answer": "**A**（流量相等）",
                "analysis": "由质量守恒（连续性原理），恒定串联管道若沿途无支流汇入或分出，通过各串联管段的体积流量必然处处相等：$Q_1 = Q_2 = \\cdots = Q_n = Q$；而各管段的管径、管长、糙率可能各不相同，故切应力、沿程水头损失和水力坡度一般不相等。故选 **A**。",
                "analysisFigures": [],
                "pitfalls": "注意串联与并联管道的口诀区别：串联管“流量相等、总水头损失相加”；并联管“各支路水头损失相等、总流量相加”。",
                "chapter": 6,
                "kps": ["串联管路特性", "恒定总流连续性方程"],
                "method": "物理概念定义辨析",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-06",
                "year": 2008,
                "no": 6,
                "type": "single_choice",
                "score": 3,
                "title": "水温升高对同管等速流动雷诺数的影响",
                "stem": "同一管道中，当水流流速不变，温度上升时，则雷诺数：",
                "options": [
                    {"label": "A", "text": "增大"},
                    {"label": "B", "text": "减小"},
                    {"label": "C", "text": "不变"},
                    {"label": "D", "text": "不一定"}
                ],
                "choiceAnswer": "A",
                "note": "",
                "figures": [],
                "shortAnswer": "A",
                "judgeAnswer": None,
                "answer": "**A**（增大）",
                "analysis": "圆管雷诺数定义为 $Re = \\frac{v d}{\\nu}$。同一管道（$d$ 不变）、流速 $v$ 不变时，$Re$ 与水的运动黏度 $\\nu$ 成反比。液体（水）的黏滞性主要源于分子内聚力，温度升高时分子间距增大、内聚力减弱，故水的运动黏度 $\\nu$ **减小**，从而雷诺数 $Re$ **增大**。故选 **A**。",
                "analysisFigures": [],
                "pitfalls": "切勿把液体与气体的黏温特性记反：液体温度升高 $\\nu \\downarrow \\Rightarrow Re \\uparrow$；气体温度升高则 $\\nu \\uparrow \\Rightarrow Re \\downarrow$。",
                "chapter": 4,
                "kps": ["雷诺数", "液体黏滞性随温度变化"],
                "method": "无量纲参数控制变量分析法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-07",
                "year": 2008,
                "no": 7,
                "type": "single_choice",
                "score": 3,
                "title": "平衡液体等压面的普适几何性质",
                "stem": "平衡液体的等压面一定是：",
                "options": [
                    {"label": "A", "text": "水平面"},
                    {"label": "B", "text": "斜平面"},
                    {"label": "C", "text": "旋转抛物面"},
                    {"label": "D", "text": "与质量力正交的面"}
                ],
                "choiceAnswer": "D",
                "note": "",
                "figures": [],
                "shortAnswer": "D",
                "judgeAnswer": None,
                "answer": "**D**（与质量力正交的面）",
                "analysis": "由欧拉液体平衡微分方程 $\\mathrm{d}p = \\rho (f_x\\,\\mathrm{d}x + f_y\\,\\mathrm{d}y + f_z\\,\\mathrm{d}z) = \\rho \\vec{f}\\cdot\\mathrm{d}\\vec{r}$，在等压面上 $\\mathrm{d}p = 0$，即 $\\vec{f}\\cdot\\mathrm{d}\\vec{r} = 0$。这表明平衡液体的等压面在任意点处都**与单位质量力 $\\vec{f}$ 垂直（正交）**。A、B、C 仅分别是重力平衡、匀加速直线平动、等角速度绕铅直轴旋转等特定质量力场下的特例。故选 **D**。",
                "analysisFigures": [],
                "pitfalls": "只有在“仅受重力作用的绝对静止液体”中，等压面才一定是水平面；对于一般“平衡液体”（含相对平衡），最普适的结论是等压面必与质量力正交。",
                "chapter": 2,
                "kps": ["欧拉平衡微分方程", "等压面性质"],
                "method": "物理概念定义辨析",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-08",
                "year": 2008,
                "no": 8,
                "type": "single_choice",
                "score": 3,
                "title": "紊流粗糙区流速加倍时沿程水头损失变化倍数",
                "stem": "一段直径不变管道的流速从 $2\\,\\mathrm{m/s}$ 增加到 $4\\,\\mathrm{m/s}$ 时，在水流都处于紊流粗糙区时，沿程水头损失是原来的（　）倍：",
                "options": [
                    {"label": "A", "text": "$1$"},
                    {"label": "B", "text": "$\\sqrt{2}$"},
                    {"label": "C", "text": "$2$"},
                    {"label": "D", "text": "$4$"}
                ],
                "choiceAnswer": "D",
                "note": "",
                "figures": [],
                "shortAnswer": "D",
                "judgeAnswer": None,
                "answer": "**D**（$4$ 倍）",
                "analysis": "在紊流粗糙区（阻力平方区），沿程阻力系数 $\\lambda$ 仅与管道相对粗糙度 $\\Delta/d$ 有关而与雷诺数（流速 $v$）无关，即 $\\lambda$ 为常数。由达西公式 $h_f = \\lambda \\frac{l}{d}\\frac{v^2}{2g} \\propto v^2$，流速由 $2\\,\\mathrm{m/s}$ 增至 $4\\,\\mathrm{m/s}$（变为原来的 $2$ 倍）时，沿程水头损失变为原来的 $2^2 = 4$ 倍。故选 **D**。",
                "analysisFigures": [],
                "pitfalls": "区分三大流区流速指数：层流区 $h_f \\propto v^1$（变 2 倍），紊流光滑区 $h_f \\propto v^{1.75}$（变 $2^{1.75}$ 倍），紊流粗糙区 $h_f \\propto v^2$（变 4 倍）。",
                "chapter": 4,
                "kps": ["紊流粗糙区", "达西-韦斯巴赫公式"],
                "method": "沿程阻力系数雷诺数依赖性与达西公式辨析",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-09",
                "year": 2008,
                "no": 9,
                "type": "single_choice",
                "score": 3,
                "title": "平面不可压缩流动流函数的基本性质",
                "stem": "流函数：",
                "options": [
                    {"label": "A", "text": "在等势面上为常量"},
                    {"label": "B", "text": "只有无旋流动中才存在"},
                    {"label": "C", "text": "沿流线为常量"},
                    {"label": "D", "text": "表达了速度与压强的关系"}
                ],
                "choiceAnswer": "C",
                "note": "",
                "figures": [],
                "shortAnswer": "C",
                "judgeAnswer": None,
                "answer": "**C**（沿流线为常量）",
                "analysis": "在平面不可压缩流动中，流函数 $\\psi$ 满足 $u_x = \\frac{\\partial \\psi}{\\partial y}$、$u_y = -\\frac{\\partial \\psi}{\\partial x}$，其全微分为 $\\mathrm{d}\\psi = -u_y\\,\\mathrm{d}x + u_x\\,\\mathrm{d}y$。沿流线满足流线微分方程 $\\frac{\\mathrm{d}x}{u_x} = \\frac{\\mathrm{d}y}{u_y} \\iff u_x\\,\\mathrm{d}y - u_y\\,\\mathrm{d}x = 0$，故 $\\mathrm{d}\\psi = 0$，即**流函数沿流线恒为常量**。流函数存在的条件是满足连续性方程，无论有旋还是无旋均存在（故 B 错）。故选 **C**。",
                "analysisFigures": [],
                "pitfalls": "切勿混淆流函数 $\\psi$ 与速度势函数 $\\varphi$ 的存在条件：$\\psi$ 对应不可压缩连续性（有旋无旋皆可存在），$\\varphi$ 对应无旋流动条件。",
                "chapter": 5,
                "kps": ["流函数与势函数", "流线微分方程"],
                "method": "物理概念定义辨析",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-10",
                "year": 2008,
                "no": 10,
                "type": "single_choice",
                "score": 3,
                "title": "水力坡度的物理定义",
                "stem": "水力坡度是指一个单位长度上的：",
                "options": [
                    {"label": "A", "text": "测压管水头"},
                    {"label": "B", "text": "流速水头"},
                    {"label": "C", "text": "总水头"},
                    {"label": "D", "text": "水头损失"}
                ],
                "choiceAnswer": "D",
                "note": "",
                "figures": [],
                "shortAnswer": "D",
                "judgeAnswer": None,
                "answer": "**D**（水头损失）",
                "analysis": "水力坡度（又称总水头线坡度）定义为沿流程单位长度上的机械能（总水头）降落值，即单位流程长度上的**水头损失**：\n\n$$\nJ = -\\frac{\\mathrm{d}H}{\\mathrm{d}s} = \\frac{h_f}{l}\n$$\n\n故选 **D**。",
                "analysisFigures": [],
                "pitfalls": "注意区分“水力坡度 $J = h_f / l$（总水头线坡度）”与“测压管坡度 $J_p = -\\mathrm{d}(z + p/\\rho g)/\\mathrm{d}s$”；仅在均匀流中两者相等。",
                "chapter": 4,
                "kps": ["水力坡度", "总水头线"],
                "method": "物理概念定义辨析",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-11",
                "year": 2008,
                "no": 11,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "液体黏滞性随温度的变化规律",
                "stem": "液体的粘滞性随温度的增加而________。",
                "note": "",
                "figures": [],
                "shortAnswer": "减小",
                "judgeAnswer": None,
                "answer": "减小",
                "analysis": "液体黏滞性主要由分子间的内聚力引起。温度升高时液体分子热运动加剧、分子平均间距增大，分子内聚力减弱，因而液体的黏滞性（动力黏度 $\\mu$ 与运动黏度 $\\nu$）随温度的增加而**减小**。",
                "analysisFigures": [],
                "pitfalls": "液体升温黏度减小，气体升温黏度增大，切勿混淆。",
                "chapter": 1,
                "kps": ["液体黏滞性随温度变化"],
                "method": "物理概念定义辨析",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-12",
                "year": 2008,
                "no": 12,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "理想液体流动切应力特征",
                "stem": "理想液体流动时，切应力 $\\tau =$ ________。",
                "note": "",
                "figures": [],
                "shortAnswer": "0",
                "judgeAnswer": None,
                "answer": "$0$（零）",
                "analysis": "理想液体假设完全没有黏滞性（$\\mu = 0$），根据牛顿内摩擦定律 $\\tau = \\mu \\frac{\\mathrm{d}u}{\\mathrm{d}y}$，无论流动速度梯度多大，理想液体流动时内部切应力恒为 $\\tau = 0$。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 1,
                "kps": ["理想液体假设", "牛顿内摩擦定律"],
                "method": "物理概念定义辨析",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-13",
                "year": 2008,
                "no": 13,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "演示层流与紊流流态的经典试验",
                "stem": "能直观演示出水流的层流与紊流的试验是________试验。",
                "note": "",
                "figures": [],
                "shortAnswer": "雷诺",
                "judgeAnswer": None,
                "answer": "雷诺",
                "analysis": "1883 年英国科学家奥斯本·雷诺（Osborne Reynolds）通过玻璃管色线演示实验首次直观揭示了层流（色线成笔直细丝）与紊流（色线剧烈掺混扩散）两种截然不同的流态，并提出了无量纲判据雷诺数 $Re$。",
                "analysisFigures": [],
                "pitfalls": "题干横线后已自带“试验”二字，填“雷诺”即可。",
                "chapter": 4,
                "kps": ["雷诺试验", "层流与紊流"],
                "method": "物理概念定义辨析",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-14",
                "year": 2008,
                "no": 14,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "等流函数曲线的几何意义",
                "stem": "流函数相等的点连成的曲线就是________。",
                "note": "",
                "figures": [],
                "shortAnswer": "流线",
                "judgeAnswer": None,
                "answer": "流线",
                "analysis": "平面不可压缩流动中，等流函数曲线 $\\psi(x, y) = C$ 满足 $\\mathrm{d}\\psi = -u_y\\,\\mathrm{d}x + u_x\\,\\mathrm{d}y = 0 \\iff \\frac{\\mathrm{d}x}{u_x} = \\frac{\\mathrm{d}y}{u_y}$，与流线微分方程完全一致，故等流函数线即为**流线**。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 5,
                "kps": ["流函数与势函数", "流线"],
                "method": "物理概念定义辨析",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-15",
                "year": 2008,
                "no": 15,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "明渠均匀流沿流向的力平衡特征",
                "stem": "明渠均匀流中，水流重力在流动方向的分力与________相平衡。",
                "note": "",
                "figures": [],
                "shortAnswer": "边壁摩擦阻力（或摩阻力）",
                "judgeAnswer": None,
                "answer": "边壁摩擦阻力（或摩阻力）",
                "analysis": "明渠均匀流中流速沿程不变、上下游过水断面水深相等（断面静水总压力彼此抵消），流向加速度为零，故水体所受重力沿渠底方向的分力 $\\rho g A L \\sin\\theta$ 与渠底及边壁施加的摩擦阻力 $\\tau_0 \\chi L$ 大小相等、方向相反，互相平衡。",
                "analysisFigures": [],
                "pitfalls": "",
                "chapter": 7,
                "kps": ["明渠均匀流特点"],
                "method": "明渠均匀流特征与形成条件判别法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-16",
                "year": 2008,
                "no": 16,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "流线与迹线重合的流态条件",
                "stem": "当液流为________流时，流线与迹线重合。",
                "note": "",
                "figures": [],
                "shortAnswer": "恒定",
                "judgeAnswer": None,
                "answer": "恒定（或定常）",
                "analysis": "流线是同一瞬时速度矢量的包络线，迹线是同一流体质点在不同时刻的空间运动轨迹。当流动为**恒定流**（定常流，$\\frac{\\partial \\vec{u}}{\\partial t} = 0$）时，流场不随时间改变，流线形状固定不变，流体质点始终沿流线运动，故流线与迹线完全重合。",
                "analysisFigures": [],
                "pitfalls": "横线后已有“流”字，直接填“恒定”（或“定常”）即可。",
                "chapter": 3,
                "kps": ["恒定流定义", "流线与迹线"],
                "method": "物理概念定义辨析",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-17",
                "year": 2008,
                "no": 17,
                "type": "fill",
                "subType": "mini-calc",
                "score": 2,
                "title": "由真空计读数换算相对压强水头",
                "stem": "水泵进口真空计的读数为 $p_k = 24.5\\,\\mathrm{kN/m^2}$，则该处的相对压强水头为________。",
                "note": "",
                "figures": [],
                "shortAnswer": "-2.5 m",
                "judgeAnswer": None,
                "answer": "$-2.5\\,\\mathrm{m}$（水柱）",
                "analysis": "真空计读数 $p_k = 24.5\\,\\mathrm{kN/m^2} = 24.5\\,\\mathrm{kPa}$ 表示该处低于当地大气压的数值，因此其**相对压强**为负值 $p = -p_k = -24.5\\,\\mathrm{kPa}$。取 $\\rho = 1000\\,\\mathrm{kg/m^3}$、$g = 9.80\\,\\mathrm{m/s^2}$，相对压强水头为：\n\n$$\n\\frac{p}{\\rho g} = -\\frac{24.5 \\times 10^3}{1000 \\times 9.80} = -2.5\\,\\mathrm{m}\n$$",
                "analysisFigures": [],
                "pitfalls": "务必带上**负号**与单位 $\\mathrm{m}$！真空高度 $h_v = +2.5\\,\\mathrm{m}$，而“相对压强水头”为 $-2.5\\,\\mathrm{m}$。",
                "chapter": 2,
                "kps": ["绝对压强、相对压强与真空度"],
                "method": "压强与水头单位换算法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-18",
                "year": 2008,
                "no": 18,
                "type": "fill",
                "subType": "mini-calc",
                "score": 2,
                "title": "满流圆管水力半径计算",
                "stem": "直径为 $1\\,\\mathrm{m}$ 的圆管中的水流，其水力半径为________。",
                "note": "",
                "figures": [],
                "shortAnswer": "0.25 m",
                "judgeAnswer": None,
                "answer": "$0.25\\,\\mathrm{m}$",
                "analysis": "对于满管流圆管，过水断面面积 $A = \\frac{\\pi}{4}d^2$，湿周 $\\chi = \\pi d$，故水力半径为：\n\n$$\nR = \\frac{A}{\\chi} = \\frac{d}{4} = \\frac{1}{4} = 0.25\\,\\mathrm{m}\n$$",
                "analysisFigures": [],
                "pitfalls": "圆管满流的水力半径是直径的四分之一（$R = d/4$），不是半径 $d/2$！",
                "chapter": 4,
                "kps": ["水力半径与湿周"],
                "method": "过水断面水力半径定义法",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-19",
                "year": 2008,
                "no": 19,
                "type": "fill",
                "subType": "mini-calc",
                "score": 2,
                "title": "谢才系数与达西沿程阻力系数换算",
                "stem": "已知谢齐系数 $C = 100\\,\\mathrm{m^{1/2}/s}$，则沿程阻力系数 $\\lambda =$ ________。",
                "note": "",
                "figures": [],
                "shortAnswer": "7.84 × 10⁻³（或 0.00784；取 g=9.81 m/s² 时为 7.85 × 10⁻³）",
                "judgeAnswer": None,
                "answer": "$7.84 \\times 10^{-3}$（取 $g = 9.80\\,\\mathrm{m/s^2}$；若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $7.85 \\times 10^{-3}$）",
                "analysis": "联立谢才公式 $v = C\\sqrt{R J}$ 与达西公式 $J = \\frac{h_f}{l} = \\lambda \\frac{1}{4R}\\frac{v^2}{2g}$ 消去 $v, R, J$ 得 $C = \\sqrt{\\frac{8g}{\\lambda}}$，从而：\n\n$$\n\\lambda = \\frac{8g}{C^2} = \\frac{8 \\times 9.80}{100^2} = 7.84 \\times 10^{-3}\n$$\n\n（若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $\\lambda = \\frac{8 \\times 9.81}{100^2} = 7.848 \\times 10^{-3} \\approx 7.85 \\times 10^{-3}$。）",
                "analysisFigures": [],
                "pitfalls": "熟记换算公式 $C = \\sqrt{8g/\\lambda}$ 及 $\\lambda$ 为无量纲数。",
                "chapter": 4,
                "kps": ["谢才系数与沿程阻力系数关系"],
                "method": "谢才与达西阻力公式换算法",
                "difficulty": 2
            },
            {
                "id": "yzu-849-2008-20",
                "year": 2008,
                "no": 20,
                "type": "fill",
                "subType": "blank",
                "score": 2,
                "title": "平面流动两流线流函数差值的物理意义",
                "stem": "在平面流动中，两条流线的流函数数值之差就等于两流线间的________。",
                "note": "",
                "figures": [],
                "shortAnswer": "单宽流量",
                "judgeAnswer": None,
                "answer": "单宽流量",
                "analysis": "沿连接流线 1 与流线 2 的任意曲线积分得通过单位宽度的体积流量 $q = \\int_1^2 (u_x\\,\\mathrm{d}y - u_y\\,\\mathrm{d}x) = \\int_1^2 \\mathrm{d}\\psi = \\psi_2 - \\psi_1$，即等于两流线间的**单宽流量**。",
                "analysisFigures": [],
                "pitfalls": "务必写明“单宽流量”（单位宽度流量），不可只笼统写成“流量”。",
                "chapter": 5,
                "kps": ["流函数与势函数", "单宽流量"],
                "method": "物理概念定义辨析",
                "difficulty": 1
            },
            {
                "id": "yzu-849-2008-21",
                "year": 2008,
                "no": 21,
                "type": "calc",
                "score": 15,
                "title": "双 U 形多液层测压计测量 A、B 两点压差计算",
                "stem": "如图所示，用双 U 形管测压计测量 $A$、$B$ 两点的压差。已知 $h_1 = 600\\,\\mathrm{mm}$，$h_2 = 250\\,\\mathrm{mm}$，$h_3 = 200\\,\\mathrm{mm}$，$h_4 = 300\\,\\mathrm{mm}$，$h_5 = 500\\,\\mathrm{mm}$，$\\rho_1 = 1000\\,\\mathrm{kg/m^3}$，$\\rho_2 = 772.7\\,\\mathrm{kg/m^3}$，$\\rho_3 = 13.6 \\times 10^3\\,\\mathrm{kg/m^3}$，求 $A$、$B$ 两点的压差。",
                "note": "",
                "figures": [
                    {"src": "figures/q21_orig.png", "caption": "题 21 图　双 U 形管多液层压差计"}
                ],
                "shortAnswer": "pA - pB = 67.87 kPa（取 g = 9.80 m/s²；若取 g = 9.81 m/s² 则为 67.94 kPa）",
                "judgeAnswer": None,
                "answer": "$A$、$B$ 两点的压差 $p_A - p_B \\approx 67.87\\,\\mathrm{kPa}$（若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $67.94\\,\\mathrm{kPa}$）。",
                "analysis": "**1. 利用三个等压面 $1\\text{—}1$、$2\\text{—}2$、$3\\text{—}3$ 逐段递推压强**\n\n如题 21 图所示，在同种连续静止液体内依次选取水平等压面 $1\\text{—}1$（左 U 形管水银 $\\rho_3$ 连通）、$2\\text{—}2$（中间倒 U 形管轻液 $\\rho_2$ 连通）和 $3\\text{—}3$（右 U 形管水银 $\\rho_3$ 连通），自 $A$ 点出发沿管路向右逐段递推至 $B$ 点：\n\n1. 由 $A$ 至等压面 $1\\text{—}1$：$p_1 = p_A + \\rho_1 g h_1$；\n2. 由 $1\\text{—}1$ 上升 $h_2$（水银 $\\rho_3$）至等压面 $2\\text{—}2$：$p_2 = p_1 - \\rho_3 g h_2$；\n3. 由 $2\\text{—}2$ 下降 $h_3$（轻液 $\\rho_2$）至等压面 $3\\text{—}3$：$p_3 = p_2 + \\rho_2 g h_3$；\n4. 由 $3\\text{—}3$ 上升 $h_4$（水银 $\\rho_3$）再上升 $(h_5 - h_4)$（液体 $\\rho_1$）到达 $B$ 点：\n\n$$\np_B = p_3 - \\rho_3 g h_4 - \\rho_1 g (h_5 - h_4)\n$$\n\n**2. 合并递推式并代入数值求解 $p_A - p_B$**\n\n将以上四式合并整理：\n\n$$\np_A + \\rho_1 g h_1 - \\rho_3 g h_2 + \\rho_2 g h_3 - \\rho_3 g h_4 - \\rho_1 g (h_5 - h_4) = p_B\n$$\n\n$$\np_A - p_B = \\rho_1 g (h_5 - h_4 - h_1) + \\rho_3 g (h_2 + h_4) - \\rho_2 g h_3\n$$\n\n统一换算为国际单位：$h_1 = 0.60\\,\\mathrm{m}$，$h_2 = 0.25\\,\\mathrm{m}$，$h_3 = 0.20\\,\\mathrm{m}$，$h_4 = 0.30\\,\\mathrm{m}$，$h_5 = 0.50\\,\\mathrm{m}$，代入 $g = 9.80\\,\\mathrm{m/s^2}$：\n\n$$\n\\begin{aligned}\np_A - p_B &= 1000 \\times 9.80 \\times (0.50 - 0.30 - 0.60) + 13600 \\times 9.80 \\times (0.25 + 0.30) - 772.7 \\times 9.80 \\times 0.20 \\\\\n&= -3920.0 + 73304.0 - 1514.49 \\\\\n&= 67869.51\\,\\mathrm{Pa} \\approx 67.87\\,\\mathrm{kPa}\n\\end{aligned}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $p_A - p_B = 67938.76\\,\\mathrm{Pa} \\approx 67.94\\,\\mathrm{kPa}$。）",
                "analysisFigures": [],
                "pitfalls": "1. 最右支从等压面 $3\\text{—}3$ 到 $B$ 点总高差为 $h_5$，其中下半段 $h_4$ 是水银 $\\rho_3$，上半段才是液体 $\\rho_1$（高度为 $h_5 - h_4 = 0.20\\,\\mathrm{m}$），切勿直接把整段 $h_5$ 都按 $\\rho_1$ 计算！\n2. 牢记静水压强逐段递推口诀：“**向下加，向上减，过等压面平移不变**”。",
                "chapter": 2,
                "kps": ["多液层压差计", "等压面性质", "静水压强基本方程"],
                "method": "等压面静水压强递推法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确选取 1—1、2—2、3—3 三个等压面，逐段列出静水压强递推关系式", "pts": 6},
                    {"label": "准确识别右支液体 ρ1 柱高为 (h5 - h4) 并整理出 pA - pB 显式表达式", "pts": 5},
                    {"label": "统一换算长度单位为 m 并准确算出压差 pA - pB ≈ 67.87 kPa（或 67.94 kPa）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2008-22",
                "year": 2008,
                "no": 22,
                "type": "calc",
                "score": 15,
                "title": "封闭负压水箱测压管液面与半圆柱曲面静水总压力计算",
                "stem": "如图所示，一个封闭水箱，液面相对压强 $p_0 = -9.8\\,\\mathrm{kPa}$，右侧面有一个 $1/2$ 圆柱曲面 $ABC$，宽 $b = 1\\,\\mathrm{m}$（垂直于纸面方向），半径 $R = 1\\,\\mathrm{m}$，$H = 3\\,\\mathrm{m}$，试求：\n\n（1）水箱左侧的测压管中水柱高度 $h$；\n\n（2）曲面 $ABC$ 所受静水总压力的大小、方向和作用点位置。",
                "note": "",
                "figures": [
                    {"src": "figures/q22_orig.png", "caption": "题 22 图　封闭真空水箱与右侧半圆柱曲面 ABC"}
                ],
                "shortAnswer": "（1）h = 2.00 m；（2）总压力 P = 24.92 kN（Px = 19.60 kN 向右，Pz = 15.39 kN 向上），方向指向右上方、与水平面夹角 θ = 38.15°，作用线通过半圆圆心 O，作用点 D 位于下半圆弧 BC 上、距 A 点竖直距离 1.618 m（距 C 点 0.382 m）处。",
                "judgeAnswer": None,
                "answer": "（1）水箱左侧测压管中水柱高度 $h = 2.00\\,\\mathrm{m}$；\n\n（2）曲面 $ABC$ 所受静水总压力大小为 **$P = 24.92\\,\\mathrm{kN}$**（若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $24.96\\,\\mathrm{kN}$），方向指向**右上方**、与水平方向夹角 $\\theta = 38.15^{\\circ}$；其作用线通过圆柱圆心 $O$，作用点 $D$ 位于下半圆弧 $BC$ 上（过 $O$ 点向圆弧下方偏转 $38.15^{\\circ}$ 处，距 $A$ 点竖直下方 $1.618\\,\\mathrm{m}$、距 $C$ 点竖直上方 $0.382\\,\\mathrm{m}$）。",
                "analysis": "**（1）求左侧测压管水柱高度 $h$**\n\n过曲面最低点 $C$ 及测压管接管中心作水平等压面，测压管上端通大气（表压为 $0$）。由静水压强基本方程（取 $\\rho = 1000\\,\\mathrm{kg/m^3}$，$g = 9.80\\,\\mathrm{m/s^2}$）：\n\n$$\np_0 + \\rho g H = \\rho g h \\implies h = H + \\frac{p_0}{\\rho g} = 3.0 + \\frac{-9.8 \\times 10^3}{1000 \\times 9.80} = 3.0 - 1.0 = 2.00\\,\\mathrm{m}\n$$\n\n这表明箱内水体的**等效自由液面（$p = 0$ 面）**位于 $C$ 点上方 $h = 2.00\\,\\mathrm{m}$ 处——由于半圆柱直径 $2R = 2.00\\,\\mathrm{m}$，等效自由液面**恰好水平通过曲面顶点 $A$**（见解图 22）。\n\n**（2）求半圆柱曲面 $ABC$ 所受静水总压力的大小、方向与作用点**\n\n1. **水平分力 $P_x$**：\n   曲面 $ABC$ 在铅直面上的投影为高 $2R = 2.0\\,\\mathrm{m}$、宽 $b = 1.0\\,\\mathrm{m}$ 的矩形，面积 $A_x = 2R b = 2.0\\,\\mathrm{m^2}$；投影面形心即圆心 $O$，位于等效自由液面（过 $A$ 点）下方 $h_C = R = 1.0\\,\\mathrm{m}$ 处，故：\n   $$\n   P_x = \\rho g h_C A_x = 1000 \\times 9.80 \\times 1.0 \\times 2.0 = 19600\\,\\mathrm{N} = 19.60\\,\\mathrm{kN} \\quad (\\text{方向水平向右})\n   $$\n2. **铅垂分力 $P_z$（压力体法）**：\n   上半圆弧 $AB$ 承受箱内水体向下的压力（实压力体为 $AB$ 上方至等效液面 $A$ 的曲边角区），下半圆弧 $BC$ 承受箱内水体向上的压力（虚压力体为 $BC$ 上方至等效液面 $A$ 的区域）。两者方向相抵后，净压力体恰好为半圆弧 $ABC$ 与弦 $AC$ 所围成的**半圆柱虚压力体**（因水在半圆凸面外侧，下方向上净推力大于上方压力），体积 $V_z = \\frac{1}{2}\\pi R^2 b = \\frac{\\pi}{2}\\,\\mathrm{m^3}$，故：\n   $$\n   P_z = \\rho g V_z = 1000 \\times 9.80 \\times \\frac{\\pi}{2} \\times 1.0^2 \\times 1.0 \\approx 15393.8\\,\\mathrm{N} \\approx 15.39\\,\\mathrm{kN} \\quad (\\text{方向竖直向上})\n   $$\n3. **总压力大小、方向与作用点位置**：\n   $$\n   P = \\sqrt{P_x^2 + P_z^2} = \\sqrt{19.60^2 + 15.394^2} \\approx 24.92\\,\\mathrm{kN}\n   $$\n   合力与水平方向的夹角 $\\theta$：\n   $$\n   \\theta = \\arctan\\frac{P_z}{P_x} = \\arctan\\frac{15.394}{19.60} = \\arctan\\frac{\\pi}{4} \\approx 38.15^{\\circ}\n   $$\n   因 $P_x$ 向右、$P_z$ 向上，合力 $P$ 指向**右上方**；又因为圆柱面上所有微元水压力均沿法线指向圆心 $O$，故总压力作用线**必然通过圆心 $O$**。沿合力反向由圆心 $O$ 引射线与半圆弧交于作用点 $D$（位于下半圆弧 $BC$ 上，在水平半径 $OB$ 下方 $38.15^{\\circ}$ 处），作用点 $D$ 距 $A$ 点的竖直距离为：\n   $$\n   h_{AD} = R + R\\sin\\theta = 1.0 + 1.0 \\times \\sin 38.15^{\\circ} \\approx 1.618\\,\\mathrm{m}\n   $$\n   （即位于 $C$ 点上方 $R - R\\sin\\theta \\approx 0.382\\,\\mathrm{m}$ 处。注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $h = 2.001\\,\\mathrm{m}$，$P_x = 19.64\\,\\mathrm{kN}$，$P_z = 15.41\\,\\mathrm{kN}$，$P = 24.96\\,\\mathrm{kN}$，$\\theta = 38.12^{\\circ}$。）",
                "analysisFigures": [
                    {"src": "figures/q22_sol.png", "caption": "解图 22　半圆柱曲面 ABC 等效自由液面、虚压力体及总压力作用点分析"}
                ],
                "pitfalls": "1. 本题水面压强 $p_0 = -9.8\\,\\mathrm{kPa} < 0$ 为**真空负压**，等效自由液面应从实际液面**向下**移 $1.0\\,\\mathrm{m}$（正好落在 $A$ 点高程），切勿反号加上去算成 $4.0\\,\\mathrm{m}$！\n2. 确定作用点 $D$ 高度时务必画图看清：合力向右上方指向圆心 $O$，因此交点 $D$ 必在圆心 $O$ **下方**的 $BC$ 弧上，距 $A$ 点竖直距离为 $R + R\\sin\\theta = 1.618\\,\\mathrm{m}$（因 $A$ 点压强为零，压心必大幅偏向底部高压区 $C$ 附近！），切勿错算成 $2R - R\\sin\\theta = 1.38\\,\\mathrm{m}$！",
                "chapter": 2,
                "kps": ["等效自由液面", "曲面静水总压力", "压力体计算"],
                "method": "等效自由液面+水平投影与铅垂压力体合成法",
                "difficulty": 3,
                "rubric": [
                    {"label": "由静水压强方程求得左侧测压管水柱高度 h = H + p0/(ρg) = 2.00 m（确认等效液面过 A 点）", "pts": 4},
                    {"label": "求出水平分力 Px = 19.60 kN（向右）与半圆虚压力体铅垂分力 Pz = 15.39 kN（向上）", "pts": 6},
                    {"label": "合成总压力 P = 24.92 kN，给出右上方倾角 38.15°、作用线过圆心 O 及作用点距 A 点 1.618 m", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2008-23",
                "year": 2008,
                "no": 23,
                "type": "proof",
                "score": 15,
                "title": "大容器侧壁小孔自由射流水平射程公式推导与极值求解",
                "stem": "一个很大的容器，侧壁有一小孔，其中心到容器底部的距离为 $h$，如图所示。忽略流动能量损失。试推导自由喷射流在水平方向所喷射的距离 $x$ 与 $H$ 和 $h$ 的函数关系；在 $H$ 一定的条件下，$h$ 为何值时，$x$ 最大。",
                "note": "",
                "figures": [
                    {"src": "figures/q23_orig.png", "caption": "题 23 图　大容器侧壁小孔自由平抛射流"}
                ],
                "shortAnswer": "x = 2√[h(H - h)]；当 h = H/2 时水平射程 x 最大，且 xmax = H。",
                "judgeAnswer": None,
                "answer": "（1）水平射程函数关系：$x = 2\\sqrt{h(H - h)}$（$0 < h < H$）；\n\n（2）当 $h = \\frac{H}{2}$ 时，水平射程 $x$ 达到最大值 $x_{\\max} = H$。",
                "analysis": "**1. 列伯努利方程求小孔出口水平流速 $v$**\n\n以容器底面为基准面（$z = 0$）。容器很大故液面行近流速 $v_0 \\approx 0$，忽略流动能量损失（$h_w = 0$，$\\alpha = 1.0$）。对自由液面 $1\\text{—}1$（$z_1 = H$，$p_1 = 0$）与小孔出口自由射流断面 $2\\text{—}2$（$z_2 = h$，$p_2 = 0$）列理想液体能量方程：\n\n$$\nH + 0 + 0 = h + 0 + \\frac{v^2}{2g} \\implies v = \\sqrt{2g(H - h)}\n$$\n\n**2. 结合平抛运动方程推导水平射程 $x(H, h)$**\n\n水股水平射出后仅受重力作用作平抛运动，下落竖直高度 $h$ 到达底面所需时间 $t$ 为：\n\n$$\nh = \\frac{1}{2}g t^2 \\implies t = \\sqrt{\\frac{2h}{g}}\n$$\n\n因此水平射程 $x$ 为：\n\n$$\nx = v t = \\sqrt{2g(H - h)} \\cdot \\sqrt{\\frac{2h}{g}} = 2\\sqrt{h(H - h)} = 2\\sqrt{Hh - h^2}\n$$\n\n**3. 求 $H$ 一定时 $x$ 的极大值条件（见解图 23）**\n\n令 $x(h)$ 对 $h$ 的一阶导数为零：\n\n$$\n\\frac{\\mathrm{d}x}{\\mathrm{d}h} = \\frac{H - 2h}{\\sqrt{Hh - h^2}} = 0 \\implies h = \\frac{H}{2}\n$$\n\n在 $0 < h < \\frac{H}{2}$ 时 $\\frac{\\mathrm{d}x}{\\mathrm{d}h} > 0$，在 $\\frac{H}{2} < h < H$ 时 $\\frac{\\mathrm{d}x}{\\mathrm{d}h} < 0$，故在 **$h = \\frac{H}{2}$** 处水平射程 $x$ 取得最大值，最大射程为 $x_{\\max} = 2\\sqrt{\\frac{H}{2}\\cdot\\frac{H}{2}} = H$。",
                "analysisFigures": [
                    {"src": "figures/q23_sol.png", "caption": "解图 23　不同孔口高度平抛射流轨迹对比与无量纲极值曲线"}
                ],
                "pitfalls": "注意根号合并时 $\\sqrt{2g(H-h)} \\cdot \\sqrt{2h/g} = \\sqrt{4h(H-h)} = 2\\sqrt{h(H-h)}$，前面的系数是 **$2$**（绝非 $\\sqrt{2}$）！代入 $h = H/2$ 立即验证 $x_{\\max} = H$。",
                "chapter": 9,
                "kps": ["薄壁孔口自由出流", "实际液体恒定总流能量方程", "平抛射流极值分析"],
                "method": "孔口出流托里拆利公式与平抛运动极值法",
                "difficulty": 2,
                "rubric": [
                    {"label": "对液面与小孔出口列伯努利方程推得出口流速 v = √[2g(H - h)]", "pts": 5},
                    {"label": "联立自由落体时间 t = √(2h/g) 正确导出水平射程函数关系 x = 2√[h(H - h)]", "pts": 5},
                    {"label": "通过求导 dx/dh = 0 并校验单调性（或均值不等式）证得 h = H/2 时 x 最大且 xmax = H", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2008-24",
                "year": 2008,
                "no": 24,
                "type": "calc",
                "score": 15,
                "title": "顶部进水两侧底口水平出流水箱的磅秤读数计算",
                "stem": "有一金属水箱，高 $1\\,\\mathrm{m}$，横截面面积为 $1\\,\\mathrm{m^2}$，包括支架在内的水箱质量为 $40\\,\\mathrm{kg}$。水箱放在一磅秤上，如图所示。水从顶部面积 $A_1 = 0.005\\,\\mathrm{m^2}$ 的开口处流入，通过侧壁底部两个面积为 $0.002\\,\\mathrm{m^2}$ 的开口流出。入口处水的流速 $V_1 = 5\\,\\mathrm{m/s}$，出口处水的流速随着水箱中的水位不断上升而增加，当达到定常流动时，水箱内的水深为 $0.9\\,\\mathrm{m}$，试问此时磅秤的读数为多少牛顿？假定水的密度为 $1000\\,\\mathrm{kg/m^3}$。",
                "note": "",
                "figures": [
                    {"src": "figures/q24_orig.png", "caption": "题 24 图　顶部铅直进水、底部双侧水平出流的磅秤水箱"}
                ],
                "shortAnswer": "9337.0 N（9.34 kN；若取 g = 9.81 m/s² 则为 9346.4 N ≈ 9.35 kN）",
                "judgeAnswer": None,
                "answer": "达到定常流动时磅秤的读数为 **$9337.0\\,\\mathrm{N}$**（即 $9.34\\,\\mathrm{kN}$；若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 **$9346.4\\,\\mathrm{N} \\approx 9.35\\,\\mathrm{kN}$**）。",
                "analysis": "**1. 计算定常流动时的总流量 $Q$ 及水箱与存水重量**\n\n达到定常（恒定）流动时，水箱内水位稳定在 $h = 0.9\\,\\mathrm{m}$，进水流量等于两侧出口总出流流量：\n\n$$\nQ = A_1 V_1 = 0.005 \\times 5 = 0.025\\,\\mathrm{m^3/s}\n$$\n\n箱内存水体积 $V_{\\text{水}} = A_{\\text{箱}} h = 1.0 \\times 0.9 = 0.9\\,\\mathrm{m^3}$，取 $g = 9.80\\,\\mathrm{m/s^2}$：\n- 空水箱及支架自重：$G_{\\text{箱}} = m_{\\text{箱}} g = 40 \\times 9.80 = 392.0\\,\\mathrm{N}$；\n- 箱内水体重力：$G_{\\text{水}} = \\rho V_{\\text{水}} g = 1000 \\times 0.9 \\times 9.80 = 8820.0\\,\\mathrm{N}$。\n\n**2. 取“水箱 + 支架 + 箱内水体”整体控制体列竖向动量方程（见解图 24）**\n\n以顶部入口断面 $1\\text{—}1$ 及两侧底部水平出口断面 $2\\text{—}2$、$3\\text{—}3$ 为控制面，包裹整个水箱、支架及箱内水体作为控制体，规定竖直向上为 $z$ 轴正方向：\n- 竖向外力：磅秤向上的支反力 $N$、向下的总重力 $(G_{\\text{箱}} + G_{\\text{水}})$（各进、出口均为大气自由射流，相对压强为 $0$）；\n- 竖向速度投影：进口水流铅直向下射入，$v_{1z} = -V_1 = -5\\,\\mathrm{m/s}$；底部两侧开口均沿水平方向射出，竖向速度分量均为零（$v_{2z} = v_{3z} = 0$，且左右两水平出流对称抵消、不产生净水平推力）。\n\n取动量修正系数 $\\beta = 1.0$，列 $z$ 向恒定总流动量方程：\n\n$$\nN - G_{\\text{箱}} - G_{\\text{水}} = \\rho Q (0 - (-V_1)) = \\rho Q V_1\n$$\n\n顶部铅直射流产生的动量冲击力为：\n\n$$\nF_{\\text{动}} = \\rho Q V_1 = 1000 \\times 0.025 \\times 5 = 125.0\\,\\mathrm{N}\n$$\n\n解得磅秤对水箱支架的支反力（即磅秤读数）：\n\n$$\nN = G_{\\text{箱}} + G_{\\text{水}} + \\rho Q V_1 = 392.0 + 8820.0 + 125.0 = 9337.0\\,\\mathrm{N} \\approx 9.34\\,\\mathrm{kN}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $G_{\\text{箱}} = 392.4\\,\\mathrm{N}$，$G_{\\text{水}} = 8829.0\\,\\mathrm{N}$，$N = 392.4 + 8829.0 + 125.0 = 9346.4\\,\\mathrm{N} \\approx 9.35\\,\\mathrm{kN}$。）",
                "analysisFigures": [
                    {"src": "figures/q24_sol.png", "caption": "解图 24　水箱、支架及箱内水体整体控制体竖向受力与动量通量图"}
                ],
                "pitfalls": "切忌先单取水体算出箱底对水体作用力 $R = G_{\\text{水}} + \\rho Q V_1 = 8945\\,\\mathrm{N}$ 后，又在求磅秤读数时把 $G_{\\text{水}}$ **重复再加一遍**（错算成 $8820 + 8945 + 392 = 18157\\,\\mathrm{N}$）！箱底作用力 $R$ 本身已经包含了 $8820\\,\\mathrm{N}$ 的水重，磅秤读数仅为 $R + G_{\\text{箱}} = 9337\\,\\mathrm{N}$。直接取整体控制体一次列式可彻底杜绝此错误。",
                "chapter": 3,
                "kps": ["恒定总流动量方程", "射流冲击力", "控制体选取技巧"],
                "method": "整体控制体竖向动量方程求支反力法",
                "difficulty": 3,
                "rubric": [
                    {"label": "求出定常流量 Q = A1·V1 = 0.025 m³/s 及箱内水重 8820 N、箱体支架重 392 N", "pts": 4},
                    {"label": "选取整体控制体列出竖向动量方程 N - G箱 - G水 = ρQ(0 - (-V1))，算出射流冲击力 125 N", "pts": 6},
                    {"label": "准确汇总（不重复计入水重）求得磅秤读数 N = 9337.0 N（或 9346.4 N）", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2008-25",
                "year": 2008,
                "no": 25,
                "type": "calc",
                "score": 15,
                "title": "钻井至集水池虹吸管流量计算与顶部真空度安全校核",
                "stem": "用虹吸管自钻井输水至集水池，如图所示。虹吸管长 $l = l_{AB} + l_{BC} = 30\\,\\mathrm{m} + 40\\,\\mathrm{m} = 70\\,\\mathrm{m}$，直径 $d = 200\\,\\mathrm{mm}$。钻井至集水池间的恒定水位高差 $H = 1.60\\,\\mathrm{m}$。又已知沿程阻力系数 $\\lambda = 0.03$，管路进口、$120^{\\circ}$ 弯头、$90^{\\circ}$ 弯头及出口处的局部阻力系数分别为 $\\zeta_1 = 0.5$，$\\zeta_2 = 0.2$，$\\zeta_3 = 0.5$，$\\zeta_4 = 1$。试求：\n\n（1）流经虹吸管的流量 $Q$；\n\n（2）如虹吸管顶部 $B$ 点安装高度 $h_B = 4.5\\,\\mathrm{m}$，校核其真空度（真空度的允许值 $[h_v] = 7\\,\\mathrm{m}$ 水柱）。",
                "note": "",
                "figures": [
                    {"src": "figures/q25_orig.png", "caption": "题 25 图　钻井至集水池跨坡虹吸管布置图"}
                ],
                "shortAnswer": "（1）流量 Q = 0.0494 m³/s（49.37 L/s）；（2）B 点弯头后最大真空度 hv,B = 5.34 m（弯头前为 5.28 m），均小于允许值 [hv] = 7 m，故满足真空度安全要求。",
                "judgeAnswer": None,
                "answer": "（1）流经虹吸管的流量 $Q \\approx 0.0494\\,\\mathrm{m^3/s}$（即 $49.37\\,\\mathrm{L/s}$）；\n\n（2）顶部 $B$ 点断面最大真空度（计入 $B$ 处 $90^{\\circ}$ 弯头损失后）为 $h_{v,B} = 5.34\\,\\mathrm{m}$ 水柱（若取 $B$ 处 $90^{\\circ}$ 弯头前断面则为 $5.28\\,\\mathrm{m}$ 水柱），均小于允许真空值 $[h_v] = 7\\,\\mathrm{m}$ 水柱，**满足真空度安全要求**。",
                "analysis": "**（1）求虹吸管输水流量 $Q$**\n\n以集水池自由水面 $2\\text{—}2$ 为基准面，对钻井自由水面 $1\\text{—}1$（$z_1 = H = 1.60\\,\\mathrm{m}$，$p_1 = 0$，$v_1 \\approx 0$）与集水池自由水面 $2\\text{—}2$（$z_2 = 0$，$p_2 = 0$，$v_2 \\approx 0$）列恒定总流能量方程（淹没出口 $\\zeta_4 = 1$ 已计入出口动能耗散）：\n\n$$\nH = \\left(\\lambda \\frac{l}{d} + \\zeta_1 + \\zeta_2 + \\zeta_3 + \\zeta_4\\right)\\frac{v^2}{2g}\n$$\n\n计算全管总阻力系数（$l = 70\\,\\mathrm{m}$，$d = 0.20\\,\\mathrm{m}$）：\n\n$$\n\\Sigma K = 0.03 \\times \\frac{70}{0.20} + 0.5 + 0.2 + 0.5 + 1.0 = 10.5 + 2.2 = 12.7\n$$\n\n解得管内流速水头、平均流速与体积流量（取 $g = 9.80\\,\\mathrm{m/s^2}$）：\n\n$$\n\\frac{v^2}{2g} = \\frac{1.60}{12.7} \\approx 0.12598\\,\\mathrm{m}, \\qquad v = \\sqrt{2 \\times 9.80 \\times 0.12598} \\approx 1.5714\\,\\mathrm{m/s}\n$$\n\n$$\nQ = \\frac{\\pi}{4} d^2 v = \\frac{\\pi}{4} \\times 0.20^2 \\times 1.5714 \\approx 0.04937\\,\\mathrm{m^3/s} \\approx 0.0494\\,\\mathrm{m^3/s} = 49.37\\,\\mathrm{L/s}\n$$\n\n**（2）校核顶部 $B$ 点最大真空度（见解图 25）**\n\n以钻井自由水面 $1\\text{—}1$ 为基准面，对水面 $1\\text{—}1$ 与虹吸管顶部 $B$ 点断面（高程 $z_B = h_B = 4.5\\,\\mathrm{m}$，相对压强水头 $\\frac{p_B}{\\rho g} = -h_{v,B}$）列能量方程。由题 25 图可知，从进口 $A$ 至顶部 $B$ 管长 $l_{AB} = 30\\,\\mathrm{m}$，途经进口（$\\zeta_1 = 0.5$）、$120^{\\circ}$ 折弯（$\\zeta_2 = 0.2$）以及顶点 $B$ 处的 $90^{\\circ}$ 弯头（$\\zeta_3 = 0.5$）。最不利（真空度最大）断面位于 $B$ 处 $90^{\\circ}$ 弯头紧后方：\n\n$$\n0 = h_B - h_{v,B} + \\left(1 + \\lambda \\frac{l_{AB}}{d} + \\zeta_1 + \\zeta_2 + \\zeta_3\\right)\\frac{v^2}{2g}\n$$\n\n代入数值（与 $g$ 无关！）：\n\n$$\nh_{v,B} = 4.5 + \\left(1 + 0.03 \\times \\frac{30}{0.20} + 0.5 + 0.2 + 0.5\\right) \\times \\frac{1.60}{12.7} = 4.5 + 6.7 \\times 0.12598 = 4.5 + 0.844 = 5.344\\,\\mathrm{m} \\approx 5.34\\,\\mathrm{m}\n$$\n\n（注：若考察 $B$ 处 $90^{\\circ}$ 弯头紧前方断面，不计 $\\zeta_3$，则 $h_{v,B^-} = 4.5 + 6.2 \\times 0.12598 = 5.28\\,\\mathrm{m}$；若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $Q = 0.0494\\,\\mathrm{m^3/s}$，$h_{v,B}$ 数值完全不变。）\n\n因为 $h_{v,B} = 5.34\\,\\mathrm{m} < [h_v] = 7\\,\\mathrm{m}$ 水柱，故顶部真空度留有充分安全裕度，**不会发生汽化断流，满足要求**。",
                "analysisFigures": [
                    {"src": "figures/q25_sol.png", "caption": "解图 25　钻井跨坡虹吸管总水头线、测压管水头线与 B 点真空度校核"}
                ],
                "pitfalls": "校核虹吸管顶点 $B$ 的最大真空度时，必须选取过完顶点弯头后的紧邻断面（即计入 $\\zeta_3$，得 $5.34\\,\\mathrm{m}$）最为偏于安全；同时切勿漏加顶点管内的流速水头 $1 \\cdot \\frac{v^2}{2g}$！",
                "chapter": 6,
                "kps": ["虹吸管水力计算", "简单短管流量计算", "最大允许吸水高度与空化"],
                "method": "简单短管能量方程测流与允许真空度校核",
                "difficulty": 3,
                "rubric": [
                    {"label": "列上下游水面能量方程，正确计算全管总阻力系数 ΣK = 12.7", "pts": 4},
                    {"label": "求出管内流速 v ≈ 1.57 m/s 及输水流量 Q ≈ 0.0494 m³/s", "pts": 4},
                    {"label": "列钻井水面至顶部 B 断面能量方程求出真空度 hv,B = 5.34 m（或弯前 5.28 m）并与 [hv]=7 m 比较得出满足结论", "pts": 7}
                ]
            },
            {
                "id": "yzu-849-2008-26",
                "year": 2008,
                "no": 26,
                "type": "proof",
                "score": 10,
                "title": "不可压缩平面线性速度场满足连续性方程与无旋条件的系数关系推导",
                "stem": "不可压缩流体的速度分布为 $u = Ax + By$，$v = Cx + Dy$，$w = 0$，若此流场满足连续性方程和无旋条件，试导出 $A$、$B$、$C$、$D$ 所需满足的条件。假设不计重力影响。",
                "note": "",
                "figures": [],
                "shortAnswer": "A + D = 0（即 A = -D）且 B = C。",
                "judgeAnswer": None,
                "answer": "常数 $A$、$B$、$C$、$D$ 所需满足的充要条件为：\n\n$$\nA + D = 0 \\quad (\\text{即 } A = -D), \\qquad B = C\n$$",
                "analysis": "**1. 由不可压缩流体连续性微分方程导出条件**\n\n不可压缩流体的三维连续性微分方程为：\n\n$$\n\\frac{\\partial u}{\\partial x} + \\frac{\\partial v}{\\partial y} + \\frac{\\partial w}{\\partial z} = 0\n$$\n\n将 $u = Ax + By$、$v = Cx + Dy$、$w = 0$ 分别求偏导代入：\n\n$$\n\\frac{\\partial u}{\\partial x} = A, \\qquad \\frac{\\partial v}{\\partial y} = D, \\qquad \\frac{\\partial w}{\\partial z} = 0\n$$\n\n因此满足连续性方程的充要条件为：\n\n$$\nA + D = 0 \\iff A = -D\n$$\n\n**2. 由无旋流动条件导出条件**\n\n流场无旋的充要条件是流体微团旋转角速度矢量 $\\vec{\\omega} = \\frac{1}{2}\\nabla \\times \\vec{V} = \\vec{0}$。由于 $w = 0$ 且 $u, v$ 均与 $z$ 无关，有 $\\omega_x = 0$、$\\omega_y = 0$，仅需检验绕 $z$ 轴的旋转角速度 $\\omega_z$：\n\n$$\n\\omega_z = \\frac{1}{2}\\left(\\frac{\\partial v}{\\partial x} - \\frac{\\partial u}{\\partial y}\\right) = \\frac{1}{2}(C - B) = 0\n$$\n\n由此解得满足无旋条件的充要条件为：\n\n$$\nB = C\n$$\n\n综合上述两步，$A$、$B$、$C$、$D$ 必须同时满足 $A + D = 0$（即 $A = -D$）与 $B = C$。",
                "analysisFigures": [],
                "pitfalls": "写绕 $z$ 轴旋转角速度公式时务必核准偏导变量：$\\omega_z = \\frac{1}{2}\\left(\\frac{\\partial v}{\\partial x} - \\frac{\\partial u}{\\partial y}\\right)$（交叉偏导！），切勿错写成 $\\frac{\\partial v}{\\partial y} - \\frac{\\partial u}{\\partial x}$！",
                "chapter": 5,
                "kps": ["不可压缩连续性微分方程", "无旋流判别条件"],
                "method": "连续性与无旋微分条件判别法",
                "difficulty": 2,
                "rubric": [
                    {"label": "写出不可压缩连续性方程 ∂u/∂x + ∂v/∂y + ∂w/∂z = 0，求偏导导出 A + D = 0（即 A = -D）", "pts": 5},
                    {"label": "写出无旋条件 ωz = (∂v/∂x - ∂u/∂y)/2 = 0（且 ωx = ωy = 0），求偏导导出 B = C", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2008-27",
                "year": 2008,
                "no": 27,
                "type": "calc",
                "score": 15,
                "title": "由梯形引水渠道实测流量与水面降落反推渠道糙率",
                "stem": "为了收集某引水渠道糙率的资料，经实测得渠中流量 $Q = 9.45\\,\\mathrm{m^3/s}$ 时，水深 $h_0 = 1.20\\,\\mathrm{m}$；在长 $l = 200\\,\\mathrm{m}$ 的渠段内，水面降落 $\\Delta z = 0.16\\,\\mathrm{m}$。渠中水流近似为恒定均匀流。渠道横断面为梯形：底宽 $b = 7.0\\,\\mathrm{m}$，边坡系数 $m = 1.5$。试确定该渠道的糙率值。",
                "note": "",
                "figures": [],
                "shortAnswer": "n = 0.030（精确值 0.0302）",
                "judgeAnswer": None,
                "answer": "该引水渠道的糙率值 $n \\approx 0.030$（精确值 $0.0302$）。",
                "analysis": "**1. 计算梯形过水断面水力要素**\n\n已知梯形断面底宽 $b = 7.0\\,\\mathrm{m}$，边坡系数 $m = 1.5$，均匀流水深 $h_0 = 1.20\\,\\mathrm{m}$：\n- 过水断面面积 $A$：\n\n$$\nA = (b + m h_0) h_0 = (7.0 + 1.5 \\times 1.20) \\times 1.20 = 8.80 \\times 1.20 = 10.56\\,\\mathrm{m^2}\n$$\n\n- 湿周 $\\chi$：\n\n$$\n\\chi = b + 2 h_0 \\sqrt{1 + m^2} = 7.0 + 2 \\times 1.20 \\times \\sqrt{1 + 1.5^2} = 7.0 + 2.4 \\times 1.80278 \\approx 11.3267\\,\\mathrm{m}\n$$\n\n- 水力半径 $R$：\n\n$$\nR = \\frac{A}{\\chi} = \\frac{10.56}{11.3267} \\approx 0.9323\\,\\mathrm{m}\n$$\n\n**2. 求水力坡度（底坡）$i$**\n\n明渠近似为恒定均匀流，总水头线、水面线与渠底线互相平行，故水力坡度（底坡）等于水面比降：\n\n$$\ni = J = \\frac{\\Delta z}{l} = \\frac{0.16}{200} = 0.0008\n$$\n\n**3. 应用谢才—曼宁公式反求渠道糙率 $n$**\n\n由 $Q = A C \\sqrt{R i} = \\frac{1}{n} A R^{2/3} i^{1/2}$ 解出糙率 $n$：\n\n$$\nn = \\frac{A R^{2/3} i^{1/2}}{Q} = \\frac{10.56 \\times 0.9323^{2/3} \\times \\sqrt{0.0008}}{9.45} = \\frac{10.56 \\times 0.95434 \\times 0.028284}{9.45} \\approx 0.03016 \\approx 0.030\n$$",
                "analysisFigures": [],
                "pitfalls": "注意梯形湿周公式中的斜边长度为 $h_0\\sqrt{1 + m^2}$，两侧共 $2h_0\\sqrt{1 + m^2}$，切勿遗漏系数 $2$ 或误写成 $2m h_0$；另外在均匀流中直接由水面落差与渠段长之比 $\\Delta z / l$ 即可求得 $i = J$。",
                "chapter": 7,
                "kps": ["梯形断面水力要素", "曼宁公式", "明渠均匀流计算"],
                "method": "谢才—曼宁公式明渠均匀流水力计算法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确算出梯形断面面积 A = 10.56 m²、湿周 χ ≈ 11.33 m 及水力半径 R ≈ 0.932 m", "pts": 5},
                    {"label": "由均匀流三线平行性质求得底坡（水力坡度）i = Δz/l = 0.0008", "pts": 4},
                    {"label": "由曼宁公式 Q = (1/n)AR^(2/3)i^(1/2) 反解出渠道糙率 n ≈ 0.030", "pts": 6}
                ]
            }
        ]
    }


def build_2007_paper() -> dict:
    return {
        "year": 2007,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试（当年试卷代码 442，现并入 849 水力学历年真题库）。",
            "全卷共 13 道大题：第 1～6 题为概念分析与基础证明题（10 + 5×8 = 50 分），第 7～13 题为综合计算与证明题（5×14 + 2×15 = 100 分）。",
            "除题干另有给定外，常温清水密度取 $\\rho = 1000\\,\\mathrm{kg/m^3}$，重力加速度取 $g = 9.80\\,\\mathrm{m/s^2}$（解析同步附 $g = 9.81\\,\\mathrm{m/s^2}$ 对照值）。"
        ],
        "sections": [
            {
                "id": "short",
                "title": "一、简答与基础证明题",
                "description": "第 1～6 题（10 + 8×5 分），共 50 分。",
                "range": [1, 6],
                "totalScore": 50
            },
            {
                "id": "calc",
                "title": "二、综合计算与证明题",
                "description": "第 7～13 题（14+15+14+15+14+14+14 分），共 100 分。",
                "range": [7, 13],
                "totalScore": 100
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2007-01",
                "year": 2007,
                "no": 1,
                "type": "proof",
                "score": 10,
                "title": "证明定面积矩形有压流断面中正方形水力半径最大",
                "stem": "试证明矩形断面有压流，当过水断面面积一定时，正方形的水力半径最大。",
                "note": "",
                "figures": [],
                "shortAnswer": "有压满流矩形断面积 A = ab 一定，湿周 χ = 2(a+b) ≥ 4√(ab) = 4√A，当且仅当 a = b（正方形）时湿周最小，故水力半径 R = A/χ 最大（Rmax = √A/4 = a/4）。",
                "judgeAnswer": None,
                "answer": "设矩形断面边长分别为 $a > 0$、$b > 0$，过水断面面积 $A = a b$ 为定值。因有压满流四壁皆与水流接触，湿周 $\\chi = 2(a + b)$，水力半径为 $R = \\frac{A}{\\chi} = \\frac{A}{2(a + b)}$。由均值不等式（或求导）知 $a + b \\ge 2\\sqrt{ab} = 2\\sqrt{A}$，当且仅当 **$a = b$（即正方形）**时湿周最小（$\\chi_{\\min} = 4\\sqrt{A}$），从而水力半径取得最大值 $R_{\\max} = \\frac{\\sqrt{A}}{4} = \\frac{a}{4}$。",
                "analysis": "**证明**：\n\n设矩形有压管流的横断面宽度为 $a > 0$、高度为 $b > 0$，给定过水断面面积 $A = a b = \\text{const}$。因为是**有压满管流动**，矩形的四个内壁面全部被水润湿，故湿周为：\n\n$$\n\\chi = 2(a + b)\n$$\n\n水力半径定义为：\n\n$$\nR = \\frac{A}{\\chi} = \\frac{A}{2(a + b)}\n$$\n\n当 $A$ 一定时，欲使 $R$ 最大，只需使湿周 $\\chi = 2(a + b)$ 最小。\n\n- **方法一（均值不等式法）**：由基本不等式 $a + b \\ge 2\\sqrt{a b} = 2\\sqrt{A}$，可得：\n  $$\n  \\chi = 2(a + b) \\ge 4\\sqrt{A} \\implies R = \\frac{A}{\\chi} \\le \\frac{A}{4\\sqrt{A}} = \\frac{\\sqrt{A}}{4}\n  $$\n  当且仅当 $a = b = \\sqrt{A}$（即矩形断面为**正方形**）时等号成立，此时水力半径取得最大值 $R_{\\max} = \\frac{\\sqrt{A}}{4} = \\frac{a}{4}$。\n- **方法二（微积分求极值法）**：将 $b = A/a$ 代入 $\\chi(a) = 2\\left(a + \\frac{A}{a}\\right)$，求导并令一阶导数为零：\n  $$\n  \\frac{\\mathrm{d}\\chi}{\\mathrm{d}a} = 2\\left(1 - \\frac{A}{a^2}\\right) = 0 \\implies a = \\sqrt{A} \\implies b = \\frac{A}{a} = a\n  $$\n  检验二阶导数 $\\frac{\\mathrm{d}^2\\chi}{\\mathrm{d}a^2} = \\frac{4A}{a^3} > 0$，确认 $a = b$ 为湿周极小值点，即水力半径极大值点。证毕。",
                "analysisFigures": [],
                "pitfalls": "审题切记本题是**有压流（满管流）**，四条边均计入湿周 $\\chi = 2(a + b)$，最优形状为**正方形**（$a = b$）；切勿与无压矩形明渠水力最佳断面（仅三条边计入湿周 $\\chi = b + 2h$，最优宽深比 $b = 2h$）相混淆！",
                "chapter": 6,
                "kps": ["水力半径与湿周", "有压矩形管最佳断面"],
                "method": "定面积最小湿周极值证明法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确写出有压满流矩形断面积 A = ab、四边湿周 χ = 2(a+b) 及水力半径 R = A/[2(a+b)]", "pts": 4},
                    {"label": "运用均值不等式或微积分求导（含二阶导检验）严谨证明当且仅当 a = b（正方形）时 R 最大（Rmax = √A/4）", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2007-02",
                "year": 2007,
                "no": 2,
                "type": "short",
                "score": 8,
                "title": "等面积矩形明渠不同宽深比均匀流过流能力比较",
                "stem": "如图所示两矩形断面渠道，其过水断面面积、糙率及底坡均相等，但底宽及水深不同，当两渠道中均为均匀流时，比较其通过流量大小。",
                "note": "",
                "figures": [
                    {"src": "figures/q02_orig.png", "caption": "题 2 图　两等面积不同宽深比矩形断面明渠"}
                ],
                "shortAnswer": "Q2 > Q1（因两渠面积、糙率、底坡均相等，渠道 2 满足矩形水力最佳宽深比 b2 = 2h2，湿周 χ2 = 5.64 < χ1 = 6，水力半径 R2 > R1，故 Q2 > Q1）。",
                "judgeAnswer": None,
                "answer": "**渠道 2 的通过流量大于渠道 1，即 $Q_2 > Q_1$。**",
                "analysis": "由明渠均匀流曼宁公式：\n\n$$\nQ = \\frac{1}{n} A R^{2/3} i^{1/2} = \\frac{A^{5/3} i^{1/2}}{n \\chi^{2/3}}\n$$\n\n已知两矩形渠道的过水断面面积 $A$、糙率 $n$ 及底坡 $i$ 均相等（注：图中渠道 2 标注 $b_2 = 2.82 \\approx 2\\sqrt{2}$、$h_2 = 1.41 \\approx \\sqrt{2}$ 为四舍五入值，严格面积均为 $A_1 = A_2 = 4$），故流量大小仅取决于湿周 $\\chi$（或水力半径 $R = A/\\chi$）：**湿周越小、水力半径越大，通过流量越大**。\n\n分别计算两矩形明渠（敞口三边湿周 $\\chi = b + 2h$）的水力要素：\n1. **渠道 1**（$b_1 = 4$，$h_1 = 1$）：\n   $$\n   A_1 = 4 \\times 1 = 4, \\qquad \\chi_1 = 4 + 2 \\times 1 = 6, \\qquad R_1 = \\frac{4}{6} = 0.667, \\qquad \\frac{A_1^{5/3}}{\\chi_1^{2/3}} \\approx 3.05\n   $$\n2. **渠道 2**（$b_2 = 2.82$，$h_2 = 1.41$，满足矩形水力最佳宽深比 $b_2 / h_2 = 2$）：\n   $$\n   \\chi_2 = 2.82 + 2 \\times 1.41 = 5.64 < \\chi_1 = 6\n   $$\n   按面积相等 $A_2 = 4$（或按标注数值 $A_2 = 2.82 \\times 1.41 = 3.976$）均有：\n   $$\n   R_2 = \\frac{A_2}{\\chi_2} \\approx 0.705 \\sim 0.709 > R_1 = 0.667, \\qquad \\frac{A_2^{5/3}}{\\chi_2^{2/3}} \\approx 3.15 > 3.05\n   $$\n\n因此，**$Q_2 > Q_1$**（从概念上也可直接看出：渠道 2 的宽深比 $b_2 / h_2 = 2$ 正好是矩形明渠的**水力最佳断面**，在相同 $A, n, i$ 条件下其输水流量必大于其它任意宽深比的矩形渠道）。",
                "analysisFigures": [],
                "pitfalls": "本题是矩形**明渠**（自由水面），湿周公式为 $\\chi = b + 2h$（不含水面宽），切勿与第 1 题有压管流的四边湿周混淆！",
                "chapter": 7,
                "kps": ["水力最佳断面", "曼宁公式", "水力半径与湿周"],
                "method": "水力最佳断面与湿周大小比较法",
                "difficulty": 1,
                "rubric": [
                    {"label": "写出明渠均匀流曼宁公式 Q = (1/n)A^(5/3)i^(1/2)/χ^(2/3)，指明 A、n、i 相同时 χ 越小（R 越大）则 Q 越大", "pts": 3},
                    {"label": "准确计算两渠湿周 χ1 = 6、χ2 = 5.64（及水力半径 R1 = 0.667 < R2 ≈ 0.705），明确得出结论 Q2 > Q1", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2007-03",
                "year": 2007,
                "no": 3,
                "type": "short",
                "score": 8,
                "title": "等直径水平有压管道恒定流动压强沿程变化规律分析",
                "stem": "水流沿等直径水平放置管道作有压恒定流动，沿流动方向各断面的压强沿程如何变化，为什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "沿流动方向各断面的压强沿程线性（单调）下降。因为管道水平（z1=z2）且等直径恒定流（v1=v2），位置水头与流速水头沿程不变，克服沿程水头损失 hf = λ(l/d)(v²/2g) 所消耗的能量完全由压强势能提供，故 p2 = p1 - ρg·hf 沿流程线性降低。",
                "judgeAnswer": None,
                "answer": "**沿流动方向，各过水断面的压强沿程线性（单调）降低。**\n\n**原因**：\n以水平管道轴线为基准面（$z_1 = z_2 = 0$），沿水流方向任取相距 $l$ 的上游断面 $1\\text{—}1$ 与下游断面 $2\\text{—}2$。因管道等直径且为不可压缩恒定流，由连续性方程知 $v_1 = v_2 = v$，两断面流速水头相等（$\\frac{\\alpha_1 v_1^2}{2g} = \\frac{\\alpha_2 v_2^2}{2g}$）。列实际液体恒定总流能量方程：\n\n$$\nz_1 + \\frac{p_1}{\\rho g} + \\frac{\\alpha_1 v_1^2}{2g} = z_2 + \\frac{p_2}{\\rho g} + \\frac{\\alpha_2 v_2^2}{2g} + h_{f1\\text{-}2}\n$$\n\n化简得：\n\n$$\n\\frac{p_1 - p_2}{\\rho g} = h_{f1\\text{-}2} = \\lambda \\frac{l}{d}\\frac{v^2}{2g} = J l > 0 \\implies p_2 = p_1 - \\rho g J l\n$$\n\n由于实际水流具有黏滞性，流动中不断克服沿程摩阻力做功消耗机械能（$h_f > 0$），而水平等径管中位置势能和动能均保持不变，水头损失只能全部依靠降低压强势能来补偿；且均匀流段水力坡度 $J = \\text{const}$，故各断面压强沿流动方向随管长 $l$ 呈**直线规律单调下降**。",
                "analysis": "本题可从水头线几何意义直观验证：水平等径管中，$z = \\text{const}$ 使测压管水头线就是压强水头 $\\frac{p}{\\rho g}$ 的变化线；同时 $v = \\text{const}$ 使测压管水头线与总水头线保持平行、斜率恒等于 $-J$，因此压强 $p(x) = p_1 - \\rho g J x$ 沿程严格线性下降。",
                "analysisFigures": [],
                "pitfalls": "务必同时写出三项关键条件——“水平（$z_1 = z_2$）”“等直径恒定流（$v_1 = v_2$）”“实际液体沿程损失（$h_f = Jl > 0$）”，缺一不可，且需点明是“沿程**线性**下降”。",
                "chapter": 6,
                "kps": ["实际液体恒定总流能量方程", "沿程水头损失", "测压管水头"],
                "method": "能量方程与水头线沿程变化分析法",
                "difficulty": 1,
                "rubric": [
                    {"label": "明确回答沿流动方向各断面压强沿程线性（单调）下降", "pts": 2},
                    {"label": "列恒定总流能量方程，结合水平管 z1=z2、等径恒定流 v1=v2 推出 (p1-p2)/(ρg) = hf = Jl > 0 并阐明物理机制", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2007-04",
                "year": 2007,
                "no": 4,
                "type": "short",
                "score": 8,
                "title": "定流量输水管管径减小对雷诺数的影响分析",
                "stem": "当输水管的流量一定时，随管径的减小，雷诺数如何变化，为什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "雷诺数增大。因 Q = (πd²/4)v，代入雷诺数公式得 Re = vd/ν = 4Q/(πνd)；当流量 Q 与运动黏度 ν 一定时，Re 与管径 d 成反比，故管径减小使雷诺数增大。",
                "judgeAnswer": None,
                "answer": "**雷诺数增大。**\n\n**原因**：\n圆管流动雷诺数定义为 $Re = \\frac{v d}{\\nu}$。由连续性方程 $Q = A v = \\frac{\\pi}{4}d^2 v$，得断面平均流速 $v = \\frac{4Q}{\\pi d^2}$。将其代入雷诺数定义式消去流速 $v$：\n\n$$\nRe = \\frac{v d}{\\nu} = \\frac{4 Q}{\\pi d^2} \\cdot \\frac{d}{\\nu} = \\frac{4 Q}{\\pi \\nu d}\n$$\n\n当输水管的流量 $Q$ 一定且水温（运动黏度 $\\nu$）不变时，雷诺数 $Re$ 与管径 $d$ 成**反比**（因为管径减小时，流速按 $d^{-2}$ 急剧增大，其增幅远超过特征长度 $d$ 线性减小的幅度，导致惯性力相对黏性力显著增强）。因此，随着管径 $d$ 的减小，雷诺数 $Re$ **增大**。",
                "analysis": "对比两种不同约束条件下的雷诺数变化规律，可帮助彻底避免直觉误判：\n- **流速 $v$ 一定**时：$Re = \\frac{vd}{\\nu} \\propto d$，管径减小则 $Re$ 减小；\n- **流量 $Q$ 一定**时：$Re = \\frac{4Q}{\\pi \\nu d} \\propto \\frac{1}{d}$，管径减小则 $Re$ 反而**增大**！",
                "analysisFigures": [],
                "pitfalls": "千万不要只看 $Re = vd/\\nu$ 表面上的分子 $d$ 而误以为“管径减小、雷诺数减小”！必须将题设不变量 $Q$ 代入消去隐含变量 $v$，得到 $Re = \\frac{4Q}{\\pi \\nu d}$ 才能正确判断。",
                "chapter": 4,
                "kps": ["雷诺数", "恒定总流连续性方程"],
                "method": "无量纲参数控制变量分析法",
                "difficulty": 1,
                "rubric": [
                    {"label": "明确回答雷诺数随管径减小而增大", "pts": 2},
                    {"label": "联立 Re = vd/ν 与 Q = (πd²/4)v 推导出 Re = 4Q/(πνd)，说明 Q、ν 一定时 Re 与 d 成反比", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2007-05",
                "year": 2007,
                "no": 5,
                "type": "proof",
                "score": 8,
                "title": "证明平面流动中两流线流函数之差等于两流线间单宽流量",
                "stem": "证明在平面流动中，两流线的流函数之差等于两流线间的单宽流量。",
                "note": "",
                "figures": [],
                "shortAnswer": "沿连接流线 1、2 的任意曲线 AB 取微元弧段 ds（分量 dx、dy），通过微元段的单宽流量 dq = ux·dy - uy·dx = (∂ψ/∂y)dy + (∂ψ/∂x)dx = dψ，积分得 q = ∫_A^B dψ = ψ2 - ψ1。",
                "judgeAnswer": None,
                "answer": "取连接两条流线（流函数值分别为 $\\psi_1$、$\\psi_2$）的任意光滑曲线 $AB$，通过曲线微元段 $\\mathrm{d}s$（投影分量 $\\mathrm{d}x, \\mathrm{d}y$）的单宽流量为 $\\mathrm{d}q = u_x\\,\\mathrm{d}y - u_y\\,\\mathrm{d}x$；代入平面不可压缩流函数定义 $u_x = \\frac{\\partial \\psi}{\\partial y}$、$u_y = -\\frac{\\partial \\psi}{\\partial x}$ 得 $\\mathrm{d}q = \\frac{\\partial \\psi}{\\partial x}\\,\\mathrm{d}x + \\frac{\\partial \\psi}{\\partial y}\\,\\mathrm{d}y = \\mathrm{d}\\psi$，沿曲线 $AB$ 积分即得 $q_{AB} = \\int_A^B \\mathrm{d}\\psi = \\psi_2 - \\psi_1$（与积分路径无关）。",
                "analysis": "**证明（见解图 5）**：\n\n在平面不可压缩流动中任取两条流线 1 和 2，其流函数值分别为常量 $\\psi_1$ 和 $\\psi_2$。作一条任意连接流线 1 上点 $A$ 与流线 2 上点 $B$ 的曲线 $AB$，在曲线上取微元弧段 $\\mathrm{d}s$，其在 $x$、$y$ 轴上的投影分量分别为 $\\mathrm{d}x$ 和 $\\mathrm{d}y$（规定由 $A$ 指向 $B$ 为弧段正向，流向从曲线左侧穿向右侧为单宽流量正方向）。\n\n1. **写出微元弧段 $\\mathrm{d}s$ 上的单宽流量 $\\mathrm{d}q$**：\n   单位宽度下，沿 $x$ 方向通过铅直投影边 $\\mathrm{d}y$ 的正向流量为 $+u_x\\,\\mathrm{d}y$，沿 $y$ 方向通过水平投影边 $\\mathrm{d}x$ 的流量为 $-u_y\\,\\mathrm{d}x$（因 $u_y > 0$ 时从下方穿入微元三角形流向左侧，与正向相反），故通过微元段 $\\mathrm{d}s$ 的单宽流量为：\n   $$\n   \\mathrm{d}q = u_x\\,\\mathrm{d}y - u_y\\,\\mathrm{d}x\n   $$\n2. **代入流函数定义化为全微分**：\n   由平面不可压缩流动流函数定义 $u_x = \\frac{\\partial \\psi}{\\partial y}$、$u_y = -\\frac{\\partial \\psi}{\\partial x}$，代入上式得：\n   $$\n   \\mathrm{d}q = \\frac{\\partial \\psi}{\\partial y}\\,\\mathrm{d}y + \\frac{\\partial \\psi}{\\partial x}\\,\\mathrm{d}x = \\mathrm{d}\\psi\n   $$\n3. **沿任意路径 $AB$ 积分**：\n   $$\n   q_{AB} = \\int_A^B \\mathrm{d}q = \\int_A^B \\mathrm{d}\\psi = \\psi_B - \\psi_A = \\psi_2 - \\psi_1\n   $$\n   可见积分结果只取决于起点和终点所在的流线值 $\\psi_1, \\psi_2$，与所取曲线 $AB$ 的形状无关，其大小 $q = |\\psi_2 - \\psi_1|$ 即为两流线之间的单宽流量。证毕。",
                "analysisFigures": [
                    {"src": "figures/q05_sol.png", "caption": "解图 5　平面流动两流线间任意曲线微元段单宽流量积分证明图"}
                ],
                "pitfalls": "证明时最容易把微元流量写成 $u_x\\,\\mathrm{d}y + u_y\\,\\mathrm{d}x$ 导致无法凑成 $\\mathrm{d}\\psi$！画出一个小小的微元直角三角形 $(\\mathrm{d}x, \\mathrm{d}y, \\mathrm{d}s)$ 标注箭头方向，一眼就能确定进入与流出斜边时的符号为 $u_x\\,\\mathrm{d}y - u_y\\,\\mathrm{d}x$。",
                "chapter": 5,
                "kps": ["流函数与势函数", "单宽流量"],
                "method": "微元通量全微分积分证明法",
                "difficulty": 2,
                "rubric": [
                    {"label": "作连接两流线的任意曲线 AB 及微元弧段 ds，正确写出单宽微元流量 dq = ux·dy - uy·dx", "pts": 4},
                    {"label": "代入流函数定义 ux = ∂ψ/∂y、uy = -∂ψ/∂x 化为全微分 dq = dψ 并积分证得 q = ψ2 - ψ1", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2007-06",
                "year": 2007,
                "no": 6,
                "type": "short",
                "score": 8,
                "title": "等底面积等水深不同形状容器底部静水总压力比较（静水佯谬）",
                "stem": "如图所示，两形状不同的盛水容器，其底面面积相等，水深相同，试比较两容器底部所受静水总压力 $P$ 的相对大小并说明理由。",
                "note": "",
                "figures": [
                    {"src": "figures/q06_orig.png", "caption": "题 6 图　底面积与水深均相等的两种不同形状盛水容器"}
                ],
                "shortAnswer": "两容器底部所受静水总压力相等（P1 = P2 = ρgHA）。因为静止均质液体内部任一点相对静水压强 p = ρgh 仅取决于液体密度与淹没水深，与容器形状及盛水总重量无关；两容器水平底面水深 H 与面积 A 均相等，故 P1 = P2。",
                "judgeAnswer": None,
                "answer": "**两容器底部所受静水总压力完全相等，即 $P_1 = P_2$。**\n\n**理由**：\n1. 由重力场静止均质液体的静水压强基本方程，容器水平底面上各点的相对静水压强均匀分布，大小为：\n   $$\n   p = \\rho g H\n   $$\n   可见静水压强仅取决于液体密度 $\\rho$ 与自由液面以下的铅垂深度 $H$，与容器的侧壁形状及容器内盛水的总重量无关。\n2. 水平底面所受静水总压力等于底面压强与底面积之积：\n   $$\n   P_1 = \\rho g H A_1, \\qquad P_2 = \\rho g H A_2\n   $$\n   因两容器盛同种液体（水）、水深 $H$ 相同且底面面积 $A_1 = A_2 = A$，故两容器底部所受静水总压力相等：$P_1 = P_2 = \\rho g H A$。\n3. **力学解释（水静力学佯谬）**：左容器虽盛水更多（水重 $G_1 > P_1$），但倾斜侧壁对水体施加了斜向上的法向支反力，其竖直向上分量承担了多余部分水体的重量（$G_1 = P_1 + R_{\\text{壁},z}$），因此传递到底面上的静水总压力仍严格等于 $P_1 = \\rho g H A$。",
                "analysis": "这就是水静力学中著名的**帕斯卡静水佯谬**：容器底面所受静水总压力 $P = \\rho g H A$ 仅等于底面积乘以水深的铅直液柱重（压力体重量），而与实际盛水总重量 $G$ 无必然相等关系——口大底小时 $G > P$（斜壁向上分担部分水重），上下等宽直壁时 $G = P$，口小底大时 $G < P$（斜壁向下反压水体使底面压力大于水重）。",
                "analysisFigures": [],
                "pitfalls": "切忌误把容器底部所受静水总压力 $P$ 与整个容器放在秤上测得的“容器内水总重量 $G$”混为一谈！底面水压力 $P$ 相等（$P_1 = P_2$），但两容器内盛水总重力并不相等（$G_1 > G_2$）。",
                "chapter": 2,
                "kps": ["静水压强基本方程", "平面静水总压力", "水静力学佯谬"],
                "method": "静水压强深度唯一性与压力体平衡分析法",
                "difficulty": 1,
                "rubric": [
                    {"label": "明确判断两容器底部所受静水总压力相等（P1 = P2）", "pts": 2},
                    {"label": "由静水压强公式 p = ρgH 和总压力 P = ρgHA 阐明底面压力仅取决于 ρ、H、A 而与容器形状和总水重无关（补充斜壁分担水重更佳）", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2007-07",
                "year": 2007,
                "no": 7,
                "type": "calc",
                "score": 14,
                "title": "双侧挡水半球形闸门水平与竖直静水总压力计算",
                "stem": "如图示，一半球形闸门，已知球门的半径 $R = 1\\,\\mathrm{m}$，上下游水位差 $H = 1\\,\\mathrm{m}$，试求闸门受到的水平作用力和竖直作用力的大小和方向。",
                "note": "",
                "figures": [
                    {"src": "figures/q07_orig.png", "caption": "题 7 图　双侧挡水半球形闸门（R = 1 m，H = 1 m）"}
                ],
                "shortAnswer": "水平作用力 Px = 30.79 kN（取 g=9.80 m/s²；若取 g=9.81 m/s² 则为 30.82 kN），方向水平向右；竖直作用力 Pz = 0。",
                "judgeAnswer": None,
                "answer": "- **水平作用力**：$P_x \\approx 30.79\\,\\mathrm{kN}$（若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $30.82\\,\\mathrm{kN}$），方向**水平向右**（指向下游）；\n- **竖直作用力**：$P_z = 0$。",
                "analysis": "**1. 求半球形闸门受到的净水平作用力 $P_x$**\n\n三维半球形闸门在铅直面上的投影是一个半径 $R = 1\\,\\mathrm{m}$ 的整圆，投影面积为：\n\n$$\nA_x = \\pi R^2 = \\pi \\times 1^2 = \\pi \\approx 3.1416\\,\\mathrm{m^2}\n$$\n\n由题 7 图可知，下游水面恰与半球顶部齐平，故投影圆圆心（形心）位于下游水面下深度 $h_{C\\text{右}} = R = 1\\,\\mathrm{m}$ 处，位于上游水面下深度 $h_{C\\text{左}} = H + R = 2\\,\\mathrm{m}$ 处。\n\n- 上游（左侧）水体对闸门的水平推力（方向向右，取 $g = 9.80\\,\\mathrm{m/s^2}$）：\n  $$\n  P_{x\\text{左}} = \\rho g h_{C\\text{左}} A_x = 1000 \\times 9.80 \\times (1 + 1) \\times \\pi \\times 1^2 = 19600\\pi \\approx 61575\\,\\mathrm{N} = 61.58\\,\\mathrm{kN}\n  $$\n- 下游（右侧）水体对闸门的水平推力（方向向左）：\n  $$\n  P_{x\\text{右}} = \\rho g h_{C\\text{右}} A_x = 1000 \\times 9.80 \\times 1 \\times \\pi \\times 1^2 = 9800\\pi \\approx 30788\\,\\mathrm{N} = 30.79\\,\\mathrm{kN}\n  $$\n- 净水平作用力（方向**水平向右**）：\n  $$\n  P_x = P_{x\\text{左}} - P_{x\\text{右}} = \\rho g H \\cdot \\pi R^2 = 9800\\pi \\approx 30.79\\,\\mathrm{kN}\n  $$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $P_{x\\text{左}} = 61.64\\,\\mathrm{kN}$，$P_{x\\text{右}} = 30.82\\,\\mathrm{kN}$，$P_x = 30.82\\,\\mathrm{kN}$。）\n\n**2. 求半球形闸门受到的净竖直作用力 $P_z$（两种等价方法，见解图 7）**\n\n- **方法一（左右两侧压力体分解法）**：\n  - 左侧上游水体位于凸半球面外侧，经上下四分之一球面抵消后，净压力体为该半球体积 $V_{\\text{半球}} = \\frac{2}{3}\\pi R^3$ 的**虚压力体**，产生竖直**向上**的作用力 $P_{z\\text{左}} = \\rho g \\left(\\frac{2}{3}\\pi R^3\\right) \\approx 20.53\\,\\mathrm{kN}$（向上）；\n  - 右侧下游水体完全充满凹半球内部，经上下内球面抵消后，净压力体为同体积 $V_{\\text{半球}} = \\frac{2}{3}\\pi R^3$ 的**实压力体**（即凹球腔内水体自重），产生竖直**向下**的作用力 $P_{z\\text{右}} = \\rho g \\left(\\frac{2}{3}\\pi R^3\\right) \\approx 20.53\\,\\mathrm{kN}$（向下）；\n  - 两力大小相等、方向相反，故净竖直作用力：\n    $$\n    P_z = P_{z\\text{左}} - P_{z\\text{右}} = 0\n    $$\n- **方法二（逐点压强差对称性法）**：在半球面上任意同一高程处，上游相对压强减去下游相对压强恒为均匀常数 $\\Delta p = p_{\\text{左}} - p_{\\text{右}} = \\rho g H$（与深度无关）。由于半球面关于过球心的水平面对称，上半球面所受向下的净竖直分力与下半球面所受向上的净竖直分力严格相等、完全抵消，故必有 $P_z = 0$。",
                "analysisFigures": [
                    {"src": "figures/q07_sol.png", "caption": "解图 7　双侧挡水半球形闸门压力体抵消与水平投影净推力分析"}
                ],
                "pitfalls": "1. 审题切忌把**三维半球形闸门**误当成二维半圆柱闸门！半球的铅直投影面积是圆形 $A_x = \\pi R^2$（题干未给宽度 $b$ 正是关键提示！），压力体体积是半球体积 $\\frac{2}{3}\\pi R^3$。\n2. 千万不要只算上游一侧的铅垂压力体而忘记下游水体同样充满半球右侧凹腔，导致误算出 $P_z = 20.53\\,\\mathrm{kN}$！两侧同密度水体完全淹没时，竖直分力严格抵消为零。",
                "chapter": 2,
                "kps": ["三维曲面静水总压力", "压力体计算", "双侧挡水曲面闸门"],
                "method": "三维曲面投影与双侧压力体合成法",
                "difficulty": 3,
                "rubric": [
                    {"label": "识别三维半球铅直投影面积为圆 Ax = πR²，分别求出上游推力 Px左、下游推力 Px右", "pts": 4},
                    {"label": "求得净水平作用力 Px = ρgH·πR² ≈ 30.79 kN（或 30.82 kN）并指明方向水平向右", "pts": 4},
                    {"label": "通过左右压力体（虚实半球体积 2πR³/3 抵消）或均匀净压差对称性严谨证得竖直作用力 Pz = 0", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2007-08",
                "year": 2007,
                "no": 8,
                "type": "calc",
                "score": 15,
                "title": "水平收缩管喉部负压抽吸下容器水的临界吸升高度计算",
                "stem": "如图所示管路，已知：通过流量 $Q = 2.71\\,\\mathrm{L/s}$，直径 $d_1 = 5\\,\\mathrm{cm}$，相对压强 $p_1 = 0.784\\,\\mathrm{N/cm^2}$，收缩断面处的直径 $d_2 = 2.5\\,\\mathrm{cm}$，若不计水头损失，试求：能将容器 $A$ 中的水吸入水管中收缩断面处的高度 $h_k$。",
                "note": "",
                "figures": [
                    {"src": "figures/q08_orig.png", "caption": "题 8 图　水平收缩管喉部负压抽吸装置"}
                ],
                "shortAnswer": "hk = 0.658 m（65.8 cm；若取 g = 9.81 m/s² 则为 0.657 m）",
                "judgeAnswer": None,
                "answer": "能将容器 $A$ 中的水吸入水管收缩断面处的最大（临界）高度 $h_k \\approx 0.658\\,\\mathrm{m}$（即 $65.8\\,\\mathrm{cm}$；若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $0.657\\,\\mathrm{m}$）。",
                "analysis": "**1. 统一单位并由连续性方程求断面 $1\\text{—}1$ 与收缩断面 $2\\text{—}2$ 流速**\n\n将已知参数换算为国际单位：\n- $Q = 2.71\\,\\mathrm{L/s} = 2.71 \\times 10^{-3}\\,\\mathrm{m^3/s}$；\n- $d_1 = 0.05\\,\\mathrm{m}$，$d_2 = 0.025\\,\\mathrm{m}$（管径比 $d_1 / d_2 = 2$）；\n- $p_1 = 0.784\\,\\mathrm{N/cm^2} = 0.784 \\times 10^4\\,\\mathrm{N/m^2} = 7840\\,\\mathrm{Pa}$。\n\n由连续性方程求两断面平均流速：\n\n$$\nv_1 = \\frac{Q}{\\dfrac{\\pi}{4}d_1^2} = \\frac{2.71 \\times 10^{-3}}{\\dfrac{\\pi}{4} \\times 0.05^2} = \\frac{2.71 \\times 10^{-3}}{1.9635 \\times 10^{-3}} \\approx 1.3802\\,\\mathrm{m/s}\n$$\n\n$$\nv_2 = v_1 \\left(\\frac{d_1}{d_2}\\right)^2 = 1.3802 \\times 2^2 = 5.5208\\,\\mathrm{m/s}\n$$\n\n**2. 列 $1\\text{—}1$ 与 $2\\text{—}2$ 断面伯努利方程求收缩断面真空高度**\n\n以水平管轴线为基准面（$z_1 = z_2 = 0$），不计水头损失（$h_w = 0$，取 $\\alpha_1 = \\alpha_2 = 1.0$），对 $1\\text{—}1$ 与 $2\\text{—}2$ 断面列理想液体伯努利方程：\n\n$$\n\\frac{p_1}{\\rho g} + \\frac{v_1^2}{2g} = \\frac{p_2}{\\rho g} + \\frac{v_2^2}{2g}\n$$\n\n代入 $g = 9.80\\,\\mathrm{m/s^2}$：\n- 断面 $1\\text{—}1$ 压强水头：$\\frac{p_1}{\\rho g} = \\frac{7840}{1000 \\times 9.80} = 0.8000\\,\\mathrm{m}$；\n- 流速水头差：$\\frac{v_2^2 - v_1^2}{2g} = \\frac{5.5208^2 - 1.3802^2}{2 \\times 9.80} = \\frac{30.4789 - 1.9049}{19.60} = \\frac{28.5740}{19.60} \\approx 1.4579\\,\\mathrm{m}$。\n\n解得收缩断面 $2\\text{—}2$ 处的相对压强水头：\n\n$$\n\\frac{p_2}{\\rho g} = \\frac{p_1}{\\rho g} - \\frac{v_2^2 - v_1^2}{2g} = 0.8000 - 1.4579 = -0.6579\\,\\mathrm{m}\n$$\n\n**3. 确定临界吸升高度 $h_k$**\n\n当水恰好被吸升至收缩断面 $2\\text{—}2$ 处的临界状态时，竖直吸水管内水柱处于临界静止平衡，容器 $A$ 自由液面表压为 $0$，故吸升高度等于收缩断面处的真空水柱高度：\n\n$$\nh_k = -\\frac{p_2}{\\rho g} = 0.6579\\,\\mathrm{m} \\approx 0.658\\,\\mathrm{m}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，算得 $\\frac{p_1}{\\rho g} = 0.7992\\,\\mathrm{m}$，$\\frac{v_2^2 - v_1^2}{2g} = 1.4564\\,\\mathrm{m}$，故 $h_k = 0.6572\\,\\mathrm{m} \\approx 0.657\\,\\mathrm{m}$；工程表述亦写作 $h_k \\le 0.658\\,\\mathrm{m}$ 时可将水吸入。）",
                "analysisFigures": [],
                "pitfalls": "特别注意压强单位换算：$1\\,\\mathrm{N/cm^2} = 10^4\\,\\mathrm{N/m^2} = 10^4\\,\\mathrm{Pa}$，故 $0.784\\,\\mathrm{N/cm^2} = 7840\\,\\mathrm{Pa}$（恰对应 $0.80\\,\\mathrm{m}$ 水柱），切勿误按 $10^2$ 换算！",
                "chapter": 3,
                "kps": ["伯努利方程测流", "恒定总流连续性方程", "喉管真空抽吸"],
                "method": "能量方程求喉部真空度定吸升高度法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确换算单位（p1 = 7840 Pa，Q = 2.71×10⁻³ m³/s）并求得流速 v1 ≈ 1.38 m/s、v2 ≈ 5.52 m/s", "pts": 5},
                    {"label": "对 1—1、2—2 断面列伯努利方程求得收缩断面相对压强水头 p2/(ρg) ≈ -0.658 m", "pts": 6},
                    {"label": "由临界吸升平衡条件 hk = -p2/(ρg) 解得最大吸升高度 hk ≈ 0.658 m（或 0.657 m）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2007-09",
                "year": 2007,
                "no": 9,
                "type": "calc",
                "score": 14,
                "title": "杠杆增力简易水压机最大举重量计算",
                "stem": "有一简易水压机如图所示，加重活塞与举重活塞直径之比为 $1 : 4$，$AO$ 与 $AB$ 之比为 $1 : 3$。问在 $B$ 点加力 $P = 15\\,\\mathrm{N}$，水压机可举重多少？",
                "note": "",
                "figures": [
                    {"src": "figures/q09_orig.png", "caption": "题 9 图　杠杆驱动简易水压机示意图"}
                ],
                "shortAnswer": "960 N",
                "judgeAnswer": None,
                "answer": "该简易水压机可举重 **$960\\,\\mathrm{N}$**。",
                "analysis": "**1. 由杠杆力矩平衡求作用于小活塞（加重活塞）上的下压力 $F_A$**\n\n如题 9 图所示，杠杆绕左端固定铰链 $O$ 转动，$A$ 点连接加重活塞推杆，$B$ 点施加向下外力 $P = 15\\,\\mathrm{N}$。已知 $AO : AB = 1 : 3$，则 $B$ 点至支点 $O$ 的力臂为：\n\n$$\nOB = OA + AB = OA + 3\\,OA = 4\\,OA\n$$\n\n忽略杠杆自重与摩擦，对铰链 $O$ 列力矩平衡方程：\n\n$$\nF_A \\cdot OA = P \\cdot OB \\implies F_A = \\frac{OB}{OA} P = 4 \\times 15 = 60\\,\\mathrm{N}\n$$\n\n**2. 应用帕斯卡定律求大活塞（举重活塞）可举重量 $G$**\n\n不计两活塞高差、自重及密封摩擦，根据帕斯卡静水压强等值传递原理，加重活塞（直径 $d_1$，面积 $A_1 = \\frac{\\pi}{4}d_1^2$）与举重活塞（直径 $d_2$，面积 $A_2 = \\frac{\\pi}{4}d_2^2$）底部液体压强相等：\n\n$$\np = \\frac{F_A}{A_1} = \\frac{G}{A_2}\n$$\n\n已知直径比 $d_1 : d_2 = 1 : 4$（即 $d_2 / d_1 = 4$），解得水压机可举重物重量：\n\n$$\nG = F_A \\frac{A_2}{A_1} = F_A \\left(\\frac{d_2}{d_1}\\right)^2 = 60 \\times 4^2 = 60 \\times 16 = 960\\,\\mathrm{N}\n$$",
                "analysisFigures": [],
                "pitfalls": "本题有两处高频小陷阱：\n1. 题干给的是 $AO : AB = 1 : 3$（而非 $AO : OB$），故力臂比 $OB / OA = (1 + 3) / 1 = 4$，切勿误把 $3$ 当作杠杆放大倍数！\n2. 帕斯卡定律放大倍数是**面积比** $(d_2 / d_1)^2 = 4^2 = 16$，切勿漏平方直接乘以 $4$！",
                "chapter": 2,
                "kps": ["帕斯卡定律", "静水压强传递", "杠杆力矩平衡"],
                "method": "杠杆力矩平衡与帕斯卡定律联立法",
                "difficulty": 2,
                "rubric": [
                    {"label": "由 AO : AB = 1 : 3 正确得出 OB = 4 OA，对支点 O 列力矩平衡求出小活塞下压力 FA = 60 N", "pts": 6},
                    {"label": "应用帕斯卡定律 FA/A1 = G/A2 及面积比 (d2/d1)² = 16，准确求得水压机举重量 G = 960 N", "pts": 8}
                ]
            },
            {
                "id": "yzu-849-2007-10",
                "year": 2007,
                "no": 10,
                "type": "proof",
                "score": 15,
                "title": "自由射流冲击 60° 斜置光滑平板分流流量比证明",
                "stem": "已知一射流在平面上以速度 $v$ 冲击一斜置平板，平板和射流的夹角 $\\alpha = 60^{\\circ}$，如不考虑水头损失及水流和平板的摩擦力，取动能、动量系数均为 $1$，试证明两分流的流量比 $\\frac{Q_1}{Q_2} = 3$。",
                "note": "",
                "figures": [
                    {"src": "figures/q10_orig.png", "caption": "题 10 图　水平自由射流冲击 60° 斜置平板"}
                ],
                "shortAnswer": "由能量方程得 v1 = v2 = v，由连续性方程得 Q = Q1 + Q2，沿光滑平板切向列动量方程 0 = ρQ1v1 - ρQ2v2 - ρQv·cos60° 得 Q1 - Q2 = (Q1 + Q2)/2，从而证得 Q1 / Q2 = 3。",
                "judgeAnswer": None,
                "answer": "联立水平面能量方程（$v_1 = v_2 = v$）、连续性方程（$Q = Q_1 + Q_2$）与沿光滑平板切向的无外力动量方程（$Q_1 - Q_2 = Q\\cos 60^{\\circ}$），解得 $\\frac{Q_1}{Q_2} = \\frac{1 + \\cos 60^{\\circ}}{1 - \\cos 60^{\\circ}} = \\frac{1 + 0.5}{1 - 0.5} = 3$。",
                "analysis": "**证明（受力与坐标系见解图 10）**：\n\n**1. 应用恒定总流能量方程确定两分流流速**\n\n射流在水平平面内运动（位置高程相同 $z = z_1 = z_2$），入射与两股分流均暴露于大气中（相对压强 $p = p_1 = p_2 = 0$），且不计水头损失（$h_w = 0$），动能修正系数为 $1$。对入射断面与两分流出口断面分别列伯努利方程：\n\n$$\n\\frac{v^2}{2g} = \\frac{v_1^2}{2g} = \\frac{v_2^2}{2g} \\implies v_1 = v_2 = v\n$$\n\n**2. 应用连续性方程**\n\n$$\nQ = Q_1 + Q_2\n$$\n\n**3. 选取射流冲击区为控制体，沿平板切向列动量方程**\n\n以平行于平板并指向分流 $Q_1$ 的方向为 $+s$ 切向轴。因不计水流与平板间的摩擦力，平板对水体只产生垂直于板面的法向反力 $R_n$（其在切向 $s$ 轴上的投影为零），且三个自由射流断面相对压强均为零，故控制体沿切向所受合外力 $\\sum F_s = 0$。取动量修正系数 $\\beta = 1$，沿 $+s$ 方向列恒定总流动量方程：\n\n$$\n\\sum F_s = \\rho Q_1 v_{1s} + \\rho Q_2 v_{2s} - \\rho Q v_s\n$$\n\n其中 $v_{1s} = +v_1 = +v$，$v_{2s} = -v_2 = -v$，$v_s = +v\\cos\\alpha = +v\\cos 60^{\\circ}$，代入得：\n\n$$\n0 = \\rho Q_1 v - \\rho Q_2 v - \\rho Q v \\cos 60^{\\circ}\n$$\n\n两边同除以 $\\rho v$ 并代入 $Q = Q_1 + Q_2$ 及 $\\cos 60^{\\circ} = \\frac{1}{2}$：\n\n$$\nQ_1 - Q_2 = (Q_1 + Q_2)\\cos 60^{\\circ} = \\frac{1}{2}(Q_1 + Q_2)\n$$\n\n移项整理得：\n\n$$\n\\frac{1}{2} Q_1 = \\frac{3}{2} Q_2 \\implies \\frac{Q_1}{Q_2} = 3\n$$\n\n证毕。（一般倾角 $\\alpha$ 下有普适结论 $\\frac{Q_1}{Q_2} = \\frac{1 + \\cos\\alpha}{1 - \\cos\\alpha} = \\cot^2\\frac{\\alpha}{2}$。）",
                "analysisFigures": [
                    {"src": "figures/q10_sol.png", "caption": "解图 10　自由射流冲击 60° 光滑斜置平板控制体与切向动量分析"}
                ],
                "pitfalls": "切忌向水平 $x$ 轴或竖直 $y$ 轴投影列动量方程——那样会引入未知的平板法向反力 $R_n$，无法直接消元求流量比！利用“光滑无摩擦平板切向合外力为零（$\\sum F_s = 0$）”，沿平板切向投影一步即可消去未知反力 $R_n$！",
                "chapter": 3,
                "kps": ["恒定总流动量方程", "射流冲击斜置平板", "实际液体恒定总流能量方程"],
                "method": "沿光滑壁面切向动量方程求分流比法",
                "difficulty": 3,
                "rubric": [
                    {"label": "由水平自由射流能量方程证得两分流速度与入射速度相等 v1 = v2 = v，并写出连续性方程 Q = Q1 + Q2", "pts": 5},
                    {"label": "合理选取沿平板切向的坐标轴（说明无摩擦故 ΣFs = 0）正确列出动量方程 0 = ρQ1v - ρQ2v - ρQv·cos60°", "pts": 6},
                    {"label": "代入 Q = Q1 + Q2 与 cos60° = 1/2 准确推导得出 Q1 / Q2 = 3", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2007-11",
                "year": 2007,
                "no": 11,
                "type": "calc",
                "score": 14,
                "title": "直立水银 U 形压差计测量不同高程容器压差通式推导",
                "stem": "如图所示，两容器内盛有同种液体，密度为 $\\rho$，今使用水银 U 形差计测量两容器中 $A$、$B$ 两点之压差。测量时将压差计直立安放，当把压差计与容器连接后，压差计中水银面的高差为 $h$，水银密度为 $\\rho_m$，已知 $A$、$B$ 两点高差为 $S$，试求 $A$、$B$ 之压差 $p_A - p_B$。（用 $\\rho$、$\\rho_m$、$h$、$S$ 表示）",
                "note": "",
                "figures": [
                    {"src": "figures/q11_orig.png", "caption": "题 11 图　直立水银 U 形压差计测量 A、B 两容器压差"}
                ],
                "shortAnswer": "pA - pB = ρgS + (ρm - ρ)gh",
                "judgeAnswer": None,
                "answer": "$A$、$B$ 两点的压差为：\n\n$$\np_A - p_B = \\rho g S + (\\rho_m - \\rho) g h\n$$",
                "analysis": "**1. 选取等压面 $c\\text{—}c$**\n\n如题 11 图所示，容器 $B$ 中心高出容器 $A$ 中心 $S$，U 形压差计右支水银面高出左支水银面 $h$。过左支水银—液体分界面作水平面 $c\\text{—}c$；因下方水银连续、均质且静止，故 $c\\text{—}c$ 为等压面，左、右两支在 $c\\text{—}c$ 平面上的静水压强相等。\n\n**2. 列等压面两侧静水压强平衡方程**\n\n设容器 $A$ 中心至右侧水银液面的铅垂距离为 $a$（辅助中间变量，也可设 $A$ 至 $c\\text{—}c$ 距离为 $a + h$），则：\n- 左支 $c\\text{—}c$ 面压强（由 $A$ 向下经高度 $a + h$ 的密度 $\\rho$ 液体）：\n  $$\n  p_{c\\text{左}} = p_A + \\rho g (a + h)\n  $$\n- 右支 $c\\text{—}c$ 面压强（由 $B$ 向下经高度 $S + a$ 的密度 $\\rho$ 液体，再向下经高度 $h$ 的水银 $\\rho_m$）：\n  $$\n  p_{c\\text{右}} = p_B + \\rho g (S + a) + \\rho_m g h\n  $$\n\n**3. 消去辅助高度 $a$ 解出 $p_A - p_B$**\n\n由 $p_{c\\text{左}} = p_{c\\text{右}}$ 得：\n\n$$\np_A + \\rho g a + \\rho g h = p_B + \\rho g S + \\rho g a + \\rho_m g h\n$$\n\n辅助量 $\\rho g a$ 严格抵消，整理得：\n\n$$\np_A - p_B = \\rho g S + (\\rho_m - \\rho) g h\n$$\n\n（物理校验：压差 $p_A - p_B$ 恰好由两项组成——静水位高差引起的 $\\rho g S$ 与测压管水头差引起的 $(\\rho_m - \\rho) g h$，即测压管水头差 $\\left(z_A + \\frac{p_A}{\\rho g}\\right) - \\left(z_B + \\frac{p_B}{\\rho g}\\right) = \\frac{\\rho_m - \\rho}{\\rho} h$，与压差计安装深浅 $a$ 无关！）",
                "analysisFigures": [],
                "pitfalls": "务必看清题图中 $B$ 点高于 $A$ 点（$z_B - z_A = S$）且右支水银面高于左支水银面（高度差 $h$）：压差 $p_A - p_B$ 中 $\\rho g S$ 项为**正号**（较低的 $A$ 点静水压更大），切勿写反符号成 $-\\rho g S$！",
                "chapter": 2,
                "kps": ["U形压差计", "等压面性质", "静水压强基本方程"],
                "method": "等压面静水压强递推法",
                "difficulty": 2,
                "rubric": [
                    {"label": "以左支液-汞交界面 c—c 为等压面，引入辅助高度正确写出左、右两支在 c—c 处的压强表达式", "pts": 6},
                    {"label": "令两侧压强相等并消去辅助高度，准确推导出 pA - pB = ρgS + (ρm - ρ)gh", "pts": 8}
                ]
            },
            {
                "id": "yzu-849-2007-12",
                "year": 2007,
                "no": 12,
                "type": "calc",
                "score": 14,
                "title": "带 U 形水银测压管与喷嘴的弯管系统流量计算",
                "stem": "如图所示，水流通过管路经喷嘴射入大气。已知 U 型测压管中水银液柱高差 $\\Delta h = 0.2\\,\\mathrm{m}$，$h_1 = 0.72\\,\\mathrm{m}$，管径 $d_1 = 15\\,\\mathrm{cm}$，喷嘴出口直径 $d_2 = 5\\,\\mathrm{cm}$，如不计水头损失，试求管中流量 $Q$。（图中高程单位为 $\\mathrm{m}$，$\\rho_{\\text{汞}} = 13.6\\rho_{\\text{水}}$）",
                "note": "",
                "figures": [
                    {"src": "figures/q12_orig.png", "caption": "题 12 图　带 U 形水银测压管与出口喷嘴的弯管流动系统"}
                ],
                "shortAnswer": "Q = 0.0175 m³/s（17.49 L/s）",
                "judgeAnswer": None,
                "answer": "管中流量 $Q \\approx 0.0175\\,\\mathrm{m^3/s}$（即 $17.49\\,\\mathrm{L/s}$；若取 $g = 9.81\\,\\mathrm{m/s^2}$ 则为 $17.50\\,\\mathrm{L/s}$）。",
                "analysis": "**1. 由 U 形水银测压计求断面 $1\\text{—}1$ 处的相对压强水头 $\\frac{p_1}{\\rho_{\\text{水}} g}$**\n\n过 U 形测压管右支水—水银交界面作水平等压面，左支顶端通大气（相对压强为 $0$），左支水银柱高出等压面 $\\Delta h = 0.2\\,\\mathrm{m}$，右支水柱高出等压面 $h_1 = 0.72\\,\\mathrm{m}$。由等压面平衡方程：\n\n$$\np_1 + \\rho_{\\text{水}} g h_1 = \\rho_{\\text{汞}} g \\Delta h\n$$\n\n两边同除以 $\\rho_{\\text{水}} g$（代入 $\\rho_{\\text{汞}}/\\rho_{\\text{水}} = 13.6$）：\n\n$$\n\\frac{p_1}{\\rho_{\\text{水}} g} = 13.6\\,\\Delta h - h_1 = 13.6 \\times 0.2 - 0.72 = 2.72 - 0.72 = 2.00\\,\\mathrm{m}\n$$\n\n**2. 联立连续性方程与伯努利方程求流量 $Q$**\n\n由题 12 图读取高程：断面 $1\\text{—}1$ 高程 $z_1 = 20\\,\\mathrm{m}$，喷嘴出口断面 $2\\text{—}2$ 高程 $z_2 = 18\\,\\mathrm{m}$（高差 $z_1 - z_2 = 2.00\\,\\mathrm{m}$），出口射入大气故相对压强 $p_2 = 0$。两断面直径比 $d_1 / d_2 = 15 / 5 = 3$，由连续性方程：\n\n$$\nv_1 = \\left(\\frac{d_2}{d_1}\\right)^2 v_2 = \\frac{1}{9} v_2\n$$\n\n不计水头损失（$h_w = 0$，取 $\\alpha_1 = \\alpha_2 = 1.0$），对断面 $1\\text{—}1$ 与喷嘴出口断面 $2\\text{—}2$ 列理想液体伯努利方程：\n\n$$\nz_1 + \\frac{p_1}{\\rho_{\\text{水}} g} + \\frac{v_1^2}{2g} = z_2 + 0 + \\frac{v_2^2}{2g}\n$$\n\n移项并代入数值：\n\n$$\n\\frac{v_2^2 - v_1^2}{2g} = (z_1 - z_2) + \\frac{p_1}{\\rho_{\\text{水}} g} = (20 - 18) + 2.00 = 4.00\\,\\mathrm{m}\n$$\n\n将 $v_1 = v_2 / 9$ 代入：\n\n$$\n\\left(1 - \\frac{1}{81}\\right)\\frac{v_2^2}{2g} = \\frac{80}{81}\\frac{v_2^2}{2g} = 4.00\\,\\mathrm{m} \\implies \\frac{v_2^2}{2g} = 4.00 \\times \\frac{81}{80} = 4.05\\,\\mathrm{m}\n$$\n\n取 $g = 9.80\\,\\mathrm{m/s^2}$ 解得喷嘴流速与管中流量：\n\n$$\nv_2 = \\sqrt{2 \\times 9.80 \\times 4.05} = \\sqrt{79.38} \\approx 8.9095\\,\\mathrm{m/s}\n$$\n\n$$\nQ = \\frac{\\pi}{4} d_2^2 v_2 = \\frac{\\pi}{4} \\times 0.05^2 \\times 8.9095 \\approx 0.017494\\,\\mathrm{m^3/s} \\approx 17.49\\,\\mathrm{L/s}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $v_2 = 8.9141\\,\\mathrm{m/s}$，$Q = 0.017503\\,\\mathrm{m^3/s} = 17.50\\,\\mathrm{L/s}$。）",
                "analysisFigures": [],
                "pitfalls": "1. 切勿忘记将图上标注的两断面位置高程差 $z_1 - z_2 = 20 - 18 = 2.00\\,\\mathrm{m}$ 与断面 $1\\text{—}1$ 压强水头 $2.00\\,\\mathrm{m}$ 相加（总有效驱动水头为 $4.00\\,\\mathrm{m}$）！\n2. 断面 $1\\text{—}1$ 并非静止大水箱，而是内径 $15\\,\\mathrm{cm}$ 的流动管道，必须保留行近流速水头 $\\frac{v_1^2}{2g} = \\frac{1}{81}\\frac{v_2^2}{2g}$ 联立求解。",
                "chapter": 3,
                "kps": ["U形压差计", "伯努利方程测流", "恒定总流连续性方程"],
                "method": "压差计定压强+伯努利与连续性方程测流法",
                "difficulty": 3,
                "rubric": [
                    {"label": "由 U 形水银测压计等压面平衡求出断面 1—1 压强水头 p1/(ρg) = 13.6Δh - h1 = 2.00 m", "pts": 4},
                    {"label": "结合高程差 z1 - z2 = 2.00 m 与连续性方程 v1 = v2/9，列出 1—1 至 2—2 伯努利方程", "pts": 5},
                    {"label": "解出喷嘴流速 v2 ≈ 8.91 m/s 及管中流量 Q ≈ 0.0175 m³/s（17.49 L/s）", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2007-13",
                "year": 2007,
                "no": 13,
                "type": "calc",
                "score": 14,
                "title": "自由涡与强迫涡平面速度场的连续性、有旋性及变形分析",
                "stem": "已知两速度场分别为：\n\n（1）$u_x = -\\dfrac{ay}{x^2 + y^2}$，$u_y = \\dfrac{ax}{x^2 + y^2}$（$a$ 为常数）；\n\n（2）$u_x = -by$，$u_y = bx$（$b$ 为常数）。\n\n求解：\n\n1）两速度场描述的流动是否可能；\n\n2）如流动可能，判别两运动是有旋还是无旋运动，流动是否有变形。",
                "note": "",
                "figures": [],
                "shortAnswer": "1）两速度场均满足不可压缩连续性方程 ∂ux/∂x + ∂uy/∂y = 0，故流动均可能（速度场（1）需在原点奇点外 x²+y² ≠ 0）；2）速度场（1）为无旋（ωz = 0）、有变形运动（自由涡）；速度场（2）为有旋（ωz = b ≠ 0）、无变形运动（刚体旋转 / 强迫涡）。",
                "judgeAnswer": None,
                "answer": "1）**两个速度场描述的不可压缩平面流动均可能发生**（速度场（1）在除去原点 $(0,0)$ 的区域内满足连续性方程，速度场（2）在全平面满足连续性方程）；\n\n2）\n- **速度场（1）（自由涡 / 点涡）**：为**无旋运动**（$\\omega_z = 0$），且**有变形**（线变形率 $\\varepsilon_{xx}, \\varepsilon_{yy}$ 与角变形率 $\\varepsilon_{xy}$ 均不为零）；\n- **速度场（2）（刚体旋转 / 强迫涡，设 $b \\neq 0$）**：为**有旋运动**（$\\omega_z = b \\neq 0$），且**无变形**（线变形率与角变形率全为零）。",
                "analysis": "**1）利用不可压缩连续性方程检验两流动是否可能**\n\n- **速度场（1）**：在 $(x, y) \\neq (0, 0)$ 处分别对 $x$、$y$ 求偏导：\n  $$\n  \\frac{\\partial u_x}{\\partial x} = \\frac{2 a x y}{(x^2 + y^2)^2}, \\qquad \\frac{\\partial u_y}{\\partial y} = -\\frac{2 a x y}{(x^2 + y^2)^2}\n  $$\n  $$\n  \\frac{\\partial u_x}{\\partial x} + \\frac{\\partial u_y}{\\partial y} = \\frac{2 a x y - 2 a x y}{(x^2 + y^2)^2} = 0\n  $$\n  满足不可压缩连续性方程，故**流动可能**（原点为奇点）。\n- **速度场（2）**：\n  $$\n  \\frac{\\partial u_x}{\\partial x} = 0, \\qquad \\frac{\\partial u_y}{\\partial y} = 0 \\implies \\frac{\\partial u_x}{\\partial x} + \\frac{\\partial u_y}{\\partial y} = 0\n  $$\n  满足不可压缩连续性方程，故**流动可能**。\n\n**2）判别旋转角速度（有旋/无旋）与变形率（有无变形）（见解图 13）**\n\n- **速度场（1）**：先求交叉偏导数：\n  $$\n  \\frac{\\partial u_y}{\\partial x} = \\frac{a(x^2 + y^2) - ax(2x)}{(x^2 + y^2)^2} = \\frac{a(y^2 - x^2)}{(x^2 + y^2)^2}, \\qquad \\frac{\\partial u_x}{\\partial y} = \\frac{-a(x^2 + y^2) + ay(2y)}{(x^2 + y^2)^2} = \\frac{a(y^2 - x^2)}{(x^2 + y^2)^2}\n  $$\n  - **旋转角速度**：\n    $$\n    \\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right) = 0 \\implies \\text{无旋运动（自由涡）}\n    $$\n  - **线变形率与角变形率**（设非平凡情况 $a \\neq 0$）：\n    $$\n    \\varepsilon_{xx} = \\frac{\\partial u_x}{\\partial x} = \\frac{2axy}{(x^2 + y^2)^2} \\neq 0, \\qquad \\varepsilon_{yy} = \\frac{\\partial u_y}{\\partial y} = -\\frac{2axy}{(x^2 + y^2)^2} \\neq 0\n    $$\n    $$\n    \\varepsilon_{xy} = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} + \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{a(y^2 - x^2)}{(x^2 + y^2)^2} \\neq 0\n    $$\n    因此速度场（1）**既有线变形又有角变形（有变形运动）**——虽然流体微团沿圆周流线运动，但因内圈快、外圈慢（$v_\\theta = a/r$），微团自身不旋转却发生强烈剪切拉伸变形！\n\n- **速度场（2）**：先求交叉偏导数 $\\frac{\\partial u_y}{\\partial x} = b$，$\\frac{\\partial u_x}{\\partial y} = -b$：\n  - **旋转角速度**（设 $b \\neq 0$）：\n    $$\n    \\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{1}{2}[b - (-b)] = b \\neq 0 \\implies \\text{有旋运动（强迫涡）}\n    $$\n  - **线变形率与角变形率**：\n    $$\n    \\varepsilon_{xx} = \\frac{\\partial u_x}{\\partial x} = 0, \\qquad \\varepsilon_{yy} = \\frac{\\partial u_y}{\\partial y} = 0, \\qquad \\varepsilon_{xy} = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} + \\frac{\\partial u_x}{\\partial y}\\right) = \\frac{1}{2}(b - b) = 0\n    $$\n    所有线变形率与角变形率恒为零，因此速度场（2）**无变形**——流场整体以恒定角速度 $b$ 绕原点作刚体旋转运动。",
                "analysisFigures": [
                    {"src": "figures/q13_sol.png", "caption": "解图 13　自由涡（无旋有变形）与强迫涡（有旋无变形）流场对比"}
                ],
                "pitfalls": "本题是流体运动学最经典的对照题！切忌误认为“流线是同心圆就一定是有旋运动”：自由涡（1）的流线是同心圆但 $\\omega_z = 0$（无旋却有剧烈剪切变形），强迫涡（2）的流线也是同心圆但 $\\omega_z = b \\neq 0$（有旋却无任何变形）。判断时务必同时计算 $\\varepsilon_{xx}, \\varepsilon_{yy}, \\varepsilon_{xy}$ 与 $\\omega_z$。",
                "chapter": 5,
                "kps": ["不可压缩连续性微分方程", "无旋流判别条件", "流体微团线变形与角变形"],
                "method": "连续性、旋转角速度与应变率张量判别法",
                "difficulty": 3,
                "rubric": [
                    {"label": "分别检验两速度场满足不可压缩连续性方程 ∂ux/∂x + ∂uy/∂y = 0，判定两流动均可能", "pts": 4},
                    {"label": "求出速度场（1）的 ωz = 0（无旋）及非零线/角变形率 εxx, εyy, εxy（有变形）", "pts": 5},
                    {"label": "求出速度场（2）的 ωz = b ≠ 0（有旋）及全为零的变形率 εxx = εyy = εxy = 0（无变形）", "pts": 5}
                ]
            }
        ]
    }


def export_pack_and_web(paper: dict):
    """Write standardized pack (`扬州大学已整理数据/<year>/`) AND web JSON + WebP (`web/public/data/yzu-849/`)."""
    year = int(paper["year"])
    pack_dir = PACK_ROOT / str(year)
    pack_fig_dir = pack_dir / "figures"
    pack_dir.mkdir(parents=True, exist_ok=True)
    pack_fig_dir.mkdir(parents=True, exist_ok=True)

    pack_json_path = pack_dir / f"{year}.json"
    pack_json_path.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")

    web_fig_dir = WEB_COURSE_DIR / "figures" / str(year)
    web_fig_dir.mkdir(parents=True, exist_ok=True)
    web_paper = copy.deepcopy(paper)

    fig_count = 0
    for q in web_paper["questions"]:
        for key in ("figures", "analysisFigures"):
            new_list = []
            for fig in q.get(key) or []:
                raw_name = Path(fig["src"]).name
                src_png = pack_fig_dir / raw_name
                if not src_png.exists():
                    raise FileNotFoundError(f"Missing source figure: {src_png}")
                webp_name = f"{src_png.stem}.webp"
                dest_webp = web_fig_dir / webp_name
                img = Image.open(src_png)
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA")
                img.save(dest_webp, format="WEBP", quality=90, method=5)
                new_list.append({
                    "src": f"figures/{year}/{webp_name}",
                    "caption": fig["caption"],
                })
                fig_count += 1
            q[key] = new_list

    web_json_path = WEB_COURSE_DIR / f"{year}.json"
    web_json_path.write_text(json.dumps(web_paper, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{year}] Wrote pack JSON ({pack_json_path}) & web JSON ({web_json_path}) with {fig_count} WebP figures.")


def main():
    extract_2008_stem_figures()
    draw_2007_stem_figures()
    draw_2008_sol_figures()
    draw_2007_sol_figures()
    export_pack_and_web(build_2008_paper())
    export_pack_and_web(build_2007_paper())


if __name__ == "__main__":
    main()
