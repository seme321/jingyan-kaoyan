# -*- coding: utf-8 -*-
r"""
Generate high-res 300 DPI cropped stem figures (q*_orig.png), clean matplotlib
solution schematics (q*_sol.png, dpi=220), standardized exam packs in
`扬州大学已整理数据/{2017,2016}/`, and web-ready JSON + WebP assets in
`web/public/data/yzu-849/` for Yangzhou University 849 Hydraulics (2017 & 2016).
"""

import copy
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pymupdf
from PIL import Image

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "扬州大学待处理数据"
PACK_ROOT = ROOT / "扬州大学已整理数据"
WEB_COURSE_DIR = ROOT / "web" / "public" / "data" / "yzu-849"


def remove_small_specks(binary_ink: np.ndarray, min_pixels: int = 5) -> np.ndarray:
    """Remove tiny isolated 1~4 px scan dust specks while preserving all strokes & dots."""
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
    """Auto-trim ink bounds, clean paper background to pure white #FFFFFF, and add 16px margin."""
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


def extract_stem_figures():
    """Render 2017 & 2016 PDFs at 300 DPI and crop stem figures cleanly without `题X图` captions."""
    crops_by_year = {
        2017: (
            "849-水力学（水）2017.pdf",
            {
                "q07_orig.png": (0, (575, 2365, 1175, 3055)),
                "q08_orig.png": (0, (1475, 2365, 2125, 3045)),
                "q09_orig.png": (1, (540, 1065, 1065, 1445)),
                "q10_orig.png": (1, (1410, 910, 1965, 1465)),
                "q11_orig.png": (1, (405, 2235, 1070, 2625)),
                "q12_orig.png": (1, (1260, 2205, 2125, 2610)),
            },
        ),
        2016: (
            "849-水力学（水）2016.pdf",
            {
                "q02_orig.png": (0, (540, 1230, 1270, 1650)),
                "q03_orig.png": (0, (1575, 1245, 1925, 1655)),
                "q04_orig.png": (0, (270, 2285, 1285, 2810)),
                "q05_orig.png": (0, (1385, 2385, 2205, 2825)),
                "q09_orig.png": (1, (475, 935, 1060, 1465)),
                "q10_orig.png": (1, (1330, 995, 1985, 1475)),
                "q11_orig.png": (1, (475, 1895, 1075, 2380)),
                "q12_orig.png": (1, (1350, 1955, 2130, 2405)),
                "q13_orig.png": (2, (840, 665, 1640, 1192)),
            },
        ),
    }

    for year, (pdf_name, fig_specs) in crops_by_year.items():
        fig_dir = PACK_ROOT / str(year) / "figures"
        fig_dir.mkdir(parents=True, exist_ok=True)
        doc = pymupdf.open(RAW_DIR / pdf_name)
        rendered = {}
        for fname, (pidx, box) in fig_specs.items():
            if pidx not in rendered:
                pix = doc[pidx].get_pixmap(dpi=300)
                rendered[pidx] = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            cropped = clean_and_pad(rendered[pidx].crop(box), pad=16)
            cropped.save(fig_dir / fname)
        doc.close()
        print(f"[{year}] Extracted {len(fig_specs)} stem figures at 300 DPI -> {fig_dir}")


# ==============================================================================
# Matplotlib Solution Figures for 2017 (dpi=220, ZERO CJK inside $...$)
# ==============================================================================

def draw_2017_q06_sol(fig_dir: Path):
    """Compare free irrotational vortex (potential exists) vs forced rotational vortex."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 4.3))
    fig.patch.set_facecolor("white")

    th = np.linspace(0, 2 * np.pi, 200)
    for ax, title, is_free in [
        (ax1, "（a）无旋自由点涡（$u_\\theta = \\frac{\\Gamma}{2\\pi r}$，存在势函数 $\\varphi$）", True),
        (ax2, "（b）有旋强制涡（$u_\\theta = \\omega_0 r$，不存在势函数）", False),
    ]:
        for rad in (0.55, 1.05, 1.55):
            ax.plot(rad * np.cos(th), rad * np.sin(th), color="#0284c7", lw=1.4, alpha=0.8)
        ax.scatter([0], [0], s=38, color="#dc2626" if is_free else "#334155", zorder=6)

        for ang_deg in (0, 90, 180, 270):
            ang = math.radians(ang_deg)
            cx, cy = 1.05 * math.cos(ang), 1.05 * math.sin(ang)
            if is_free:
                ax.add_patch(patches.Rectangle((cx - 0.14, cy - 0.14), 0.28, 0.28,
                                               facecolor="#fef3c7", edgecolor="#b45309", lw=1.4, zorder=5))
                ax.annotate("", xy=(cx + 0.13, cy), xytext=(cx - 0.11, cy),
                            arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.8), zorder=6)
            else:
                dx, dy = 0.12 * math.cos(ang), 0.12 * math.sin(ang)
                ax.add_patch(patches.Circle((cx, cy), 0.15, facecolor="#fee2e2", edgecolor="#b91c1c", lw=1.4, zorder=5))
                ax.annotate("", xy=(cx + dx, cy + dy), xytext=(cx - dx, cy - dy),
                            arrowprops=dict(arrowstyle="->", color="#991b1b", lw=1.8), zorder=6)

        a45 = math.radians(45)
        ax.annotate("", xy=(1.55 * math.cos(a45 + 0.22), 1.55 * math.sin(a45 + 0.22)),
                    xytext=(1.55 * math.cos(a45 - 0.12), 1.55 * math.sin(a45 - 0.12)),
                    arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.0))

        if is_free:
            ax.text(0, -1.92, "微团绕原点公转但不自转（$\\omega_z = 0$）\n除奇点 $r=0$ 外满足无旋条件，$\\varphi = \\frac{\\Gamma}{2\\pi}\\theta$",
                    fontsize=9.0, ha="center", va="top", color="#15803d", fontweight="bold")
        else:
            ax.text(0, -1.92, "微团绕自身轴线刚体自转（$\\omega_z = \\omega_0 \\neq 0$）\n属于有旋流动，不存在流速势函数 $\\varphi$",
                    fontsize=9.0, ha="center", va="top", color="#b91c1c", fontweight="bold")

        ax.set_xlim(-2.05, 2.05)
        ax.set_ylim(-2.55, 1.95)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=10.2, pad=4)

    plt.tight_layout()
    fig.savefig(fig_dir / "q06_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2017_q08_sol(fig_dir: Path):
    """Cylinder resting on 60-deg inclined wall: Px projection + upward Pz pressure body."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.4, 4.4))
    fig.patch.set_facecolor("white")

    R = 1.0
    th_all = np.linspace(0, 2 * np.pi, 300)
    xA, yA = -math.sqrt(3) / 2.0, 0.5
    xB, yB = math.sqrt(3) / 2.0, -0.5

    # Panel (a): Horizontal force Px
    ax1.plot(R * np.cos(th_all), R * np.sin(th_all), color="#0f172a", lw=2.2, zorder=5)
    t_wall = np.linspace(-1.35, 1.85, 50)
    wx = xB + t_wall * math.cos(math.radians(60))
    wy = yB + t_wall * math.sin(math.radians(60))
    ax1.plot(wx, wy, color="#334155", lw=2.0)
    ax1.plot([-2.5, xA], [yA, yA], color="#0284c7", lw=2.0)

    x_tri = -2.15
    ax1.add_patch(patches.Polygon([(x_tri, yA), (x_tri, yB), (x_tri + 0.85, yB)],
                                  closed=True, facecolor="#bae6fd", edgecolor="#0284c7", lw=1.6, alpha=0.85))
    ax1.plot([x_tri, xB], [yB, yB], color="#64748b", ls=":", lw=1.2)
    ax1.annotate("", xy=(x_tri + 0.98, yB + 0.33), xytext=(x_tri + 0.15, yB + 0.33),
                 arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=2.4))
    ax1.text(x_tri + 0.45, yB - 0.25, "$P_x = \\frac{1}{2}\\rho g h_{AB}^2 b$\n$= 19.60\\,\\mathrm{kN}\\;(\\rightarrow)$",
             fontsize=9.2, ha="center", va="top", color="#1e40af", fontweight="bold")
    ax1.text(-0.15, -1.42, "底部 $y \\in [-1.0,-0.5]$ 左右水平压力相互抵消", fontsize=8.8, ha="center", color="#475569")
    ax1.text(xA - 0.16, yA + 0.10, "$A$", fontsize=10.5, fontweight="bold")
    ax1.text(xB + 0.14, yB - 0.08, "$B$", fontsize=10.5, fontweight="bold")
    ax1.plot([xA, xB], [yA, yB], color="#475569", ls="--", lw=1.4)
    ax1.set_xlim(-2.55, 1.85)
    ax1.set_ylim(-1.68, 1.35)
    ax1.set_aspect("equal")
    ax1.axis("off")
    ax1.set_title("（a）铅垂投影面与水平静水总压力 $P_x$", fontsize=10.5, pad=6)

    # Panel (b): Upward virtual pressure body Pz & Resultant P
    th_wet = np.linspace(math.radians(150), math.radians(330), 200)
    poly_semi = list(zip(R * np.cos(th_wet), R * np.sin(th_wet)))
    ax2.add_patch(patches.Polygon(poly_semi, closed=True, facecolor="#ffedd5", edgecolor="#ea580c", lw=1.5, alpha=0.85,
                                  label="下半圆面积 $\\frac{1}{8}\\pi d^2 = 1.571\\,\\mathrm{m^2}$"))
    ax2.add_patch(patches.Polygon([(xA, yA), (xB, yB), (xB, yA)], closed=True,
                                  facecolor="#fef08a", edgecolor="#ca8a04", lw=1.5, alpha=0.85,
                                  label="上部直角三角形 $\\frac{1}{2}ha = 0.866\\,\\mathrm{m^2}$"))

    ax2.plot(R * np.cos(th_all), R * np.sin(th_all), color="#0f172a", lw=2.2, zorder=5)
    ax2.plot(wx, wy, color="#334155", lw=2.0)
    ax2.plot([-1.45, xB + 0.35], [yA, yA], color="#0284c7", lw=1.8, ls="--")
    ax2.scatter([0], [0], s=32, color="#0f172a", zorder=6)
    ax2.text(-0.20, 0.08, "$O$", fontsize=10, fontweight="bold")

    ang_p = math.radians(78.4)
    ax2.annotate("", xy=(1.35 * math.cos(ang_p), 1.35 * math.sin(ang_p)),
                 xytext=(-0.12 * math.cos(ang_p), -0.12 * math.sin(ang_p)),
                 arrowprops=dict(arrowstyle="->", color="#15803d", lw=2.8), zorder=7)
    ax2.text(0.42, 1.16, "$P = 97.51\\,\\mathrm{kN}$\n$\\theta = 78.40^{\\circ}$（过圆心 $O$）",
             fontsize=9.1, color="#15803d", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.28", facecolor="#f0fdf4", edgecolor="#86efac"))
    ax2.text(xA - 0.16, yA + 0.10, "$A$", fontsize=10.5, fontweight="bold")
    ax2.text(xB + 0.14, yB - 0.08, "$B$", fontsize=10.5, fontweight="bold")

    ax2.legend(loc="lower left", fontsize=8.2, framealpha=0.94)
    ax2.set_xlim(-1.55, 2.35)
    ax2.set_ylim(-1.68, 1.58)
    ax2.set_aspect("equal")
    ax2.axis("off")
    ax2.set_title("（b）铅垂虚压力体（$P_z = 95.52\\,\\mathrm{kN}\\uparrow$）与总压力 $P$", fontsize=10.5, pad=6)

    plt.tight_layout()
    fig.savefig(fig_dir / "q08_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2017_q10_sol(fig_dir: Path):
    """Venturi jet ejector suction head & energy conversion diagram for 2017 Q10."""
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    fig.patch.set_facecolor("white")

    # Upper tank
    ax.plot([2.0, 2.0, 3.1], [4.2, 3.2, 3.2], color="#0f172a", lw=2.0)
    ax.plot([3.7, 4.8, 4.8], [3.2, 3.2, 4.2], color="#0f172a", lw=2.0)
    ax.add_patch(patches.Rectangle((2.02, 3.22), 2.76, 0.73, facecolor="#bae6fd", alpha=0.6))
    ax.plot([2.0, 4.8], [3.95, 3.95], color="#0284c7", lw=2.0)

    # Vertical pipe with throat 1-1 -> horizontal nozzle 2-2
    ax.plot([3.1, 3.1, 3.25, 3.1, 3.1, 6.0], [3.2, 2.65, 2.45, 2.25, 0.45, 0.45], color="#0f172a", lw=2.0)
    ax.plot([3.7, 3.7, 3.55, 3.7, 3.7, 6.0], [3.2, 2.65, 2.45, 2.25, 0.75, 0.75], color="#0f172a", lw=2.0)
    ax.plot([6.0, 6.4], [0.75, 0.67], color="#0f172a", lw=2.0)
    ax.plot([6.0, 6.4], [0.45, 0.53], color="#0f172a", lw=2.0)

    # Lower tank M & suction pipe
    ax.plot([0.9, 0.9, 2.15, 2.15], [1.25, 0.45, 0.45, 1.25], color="#0f172a", lw=1.8)
    ax.add_patch(patches.Rectangle((0.92, 0.47), 1.21, 0.48, facecolor="#e0f2fe", alpha=0.7))
    ax.plot([0.9, 2.15], [0.95, 0.95], color="#0284c7", lw=1.8)
    ax.plot([1.42, 1.42, 3.25], [0.65, 2.52, 2.52], color="#0f172a", lw=1.6)
    ax.plot([1.58, 1.58, 3.25], [0.65, 2.38, 2.38], color="#0f172a", lw=1.6)
    ax.text(1.85, 0.65, "$M$", fontsize=11, fontweight="bold")

    # Sections & datum
    ax.plot([2.7, 7.1], [0.60, 0.60], color="#64748b", ls="-.", lw=1.2)
    ax.text(7.18, 0.60, "0—0（基准面）", fontsize=8.8, va="center", color="#475569")
    ax.plot([3.00, 3.85], [2.45, 2.45], color="#dc2626", ls="--", lw=1.5)
    ax.text(3.92, 2.45, "喉道 1—1 ($A_1, v_1$)", fontsize=9.0, va="center", color="#b91c1c", fontweight="bold")
    ax.plot([6.4, 6.4], [0.32, 0.92], color="#dc2626", ls="--", lw=1.5)
    ax.text(6.4, 1.02, "喷嘴 2—2\n$v_2 = \\sqrt{2gH}$", fontsize=8.8, ha="center", color="#1d4ed8")

    # Dimensions h, H, b
    ax.annotate("", xy=(5.25, 3.95), xytext=(5.25, 2.45), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.4))
    ax.text(5.34, 3.20, "$h$", fontsize=10.5, va="center")
    ax.annotate("", xy=(5.82, 3.95), xytext=(5.82, 0.60), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.4))
    ax.text(5.91, 2.15, "$H$", fontsize=10.5, va="center")
    ax.annotate("", xy=(0.68, 2.45), xytext=(0.68, 0.95), arrowprops=dict(arrowstyle="<->", color="#b91c1c", lw=1.5))
    ax.text(0.58, 1.70, "$b$", fontsize=10.5, ha="right", va="center", color="#b91c1c")

    # Core derivation callout box
    ax.text(6.35, 3.25,
            "抽水起动判据：\n$\\frac{p_1}{\\rho g} = h - \\frac{v_1^2}{2g} \\leq -b$\n$\\Rightarrow v_1 \\geq \\sqrt{2g(h+b)}$\n$\\Rightarrow \\frac{A_1}{A_2} = \\frac{v_2}{v_1} \\leq \\sqrt{\\frac{H}{h+b}}$",
            fontsize=9.2, ha="left", va="center", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.38", facecolor="#f0fdf4", edgecolor="#86efac"))

    ax.set_title("第 10 题：喷射抽水装置喉道负压起动条件分析图", fontsize=11, pad=6)
    ax.set_xlim(0.15, 9.15)
    ax.set_ylim(0.15, 4.38)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q10_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2017_q11_sol(fig_dir: Path):
    """Jet impinging on flat plate sealing tank-2 mouthpiece for 2017 Q11."""
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    fig.patch.set_facecolor("white")

    ax.plot([0.5, 2.2, 2.2], [0.5, 0.5, 1.15], color="#0f172a", lw=2.2)
    ax.plot([2.2, 2.2], [1.45, 3.7], color="#0f172a", lw=2.2)
    ax.add_patch(patches.Rectangle((0.5, 0.52), 1.68, 2.88, facecolor="#bae6fd", alpha=0.6))
    ax.plot([0.5, 2.2], [3.4, 3.4], color="#0284c7", lw=2.0)
    ax.annotate("", xy=(1.2, 3.4), xytext=(1.2, 1.3), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.4))
    ax.text(1.08, 2.35, "$h_1$", fontsize=11, ha="right", va="center")

    ax.add_patch(patches.Rectangle((2.2, 1.15), 2.45, 0.30, facecolor="#7dd3fc", alpha=0.75))
    ax.plot([2.2, 4.35], [1.45, 1.45], color="#0284c7", lw=1.6)
    ax.plot([2.2, 4.35], [1.15, 1.15], color="#0284c7", lw=1.6)
    ax.annotate("", xy=(4.52, 2.32), xytext=(4.52, 1.45), arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.0))
    ax.annotate("", xy=(4.52, 0.25), xytext=(4.52, 1.15), arrowprops=dict(arrowstyle="->", color="#0284c7", lw=2.0))
    ax.annotate("", xy=(3.55, 1.30), xytext=(2.55, 1.30), arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.2))
    ax.text(3.15, 1.72, "射流 $v_1 = \\sqrt{2gh_1}$\n直径 $d_1 = 0.5 d_2$", fontsize=9.1, ha="center", color="#0369a1")

    ax.add_patch(patches.Rectangle((3.75, 0.55), 0.90, 1.50, facecolor="none", edgecolor="#dc2626", ls="--", lw=1.6))

    ax.add_patch(patches.Rectangle((4.65, 0.72), 0.26, 1.16, facecolor="#cbd5e1", edgecolor="#0f172a", lw=2.0, hatch="///", zorder=5))
    ax.add_patch(patches.Rectangle((4.91, 1.00), 0.89, 0.60, facecolor="#fde68a", alpha=0.6))
    ax.add_patch(patches.Rectangle((5.80, 0.52), 1.90, 1.98, facecolor="#fde68a", alpha=0.55))
    ax.plot([4.91, 5.80, 5.80], [1.60, 1.60, 2.95], color="#0f172a", lw=2.2)
    ax.plot([4.91, 5.80, 5.80, 7.7], [1.00, 1.00, 0.5, 0.5], color="#0f172a", lw=2.2)
    ax.plot([5.80, 7.7], [2.50, 2.50], color="#d97706", lw=2.0)
    ax.annotate("", xy=(6.8, 2.50), xytext=(6.8, 1.30), arrowprops=dict(arrowstyle="<->", color="#92400e", lw=1.4))
    ax.text(6.92, 1.90, "$h_2$", fontsize=11, va="center", color="#92400e")

    ax.annotate("", xy=(4.63, 1.30), xytext=(3.95, 1.30), arrowprops=dict(arrowstyle="->", color="#15803d", lw=2.6), zorder=7)
    ax.annotate("", xy=(4.93, 1.30), xytext=(5.65, 1.30), arrowprops=dict(arrowstyle="->", color="#b45309", lw=2.6), zorder=7)
    ax.text(4.85, 3.25,
            "平板水平受力平衡条件：\n射流冲击力 $F_1 = \\rho Q v_1 = \\frac{\\pi}{2}\\rho g h_1 d_1^2\\;(\\rightarrow)$\n水箱 2 静水压力 $P_2 = \\frac{\\pi}{4}\\rho g h_2 d_2^2\\;(\\leftarrow)$\n封住条件 $F_1 \\geq P_2 \\Rightarrow h_2 \\leq 2\\left(\\frac{d_1}{d_2}\\right)^2 h_1 = 0.5 h_1$",
            fontsize=9.1, ha="center", va="center", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#f8fafc", edgecolor="#94a3b8"))

    ax.set_title("第 11 题：射流冲击平板封堵管嘴的动量与静水压力平衡图", fontsize=11, pad=6)
    ax.set_xlim(0.3, 7.9)
    ax.set_ylim(0.15, 4.05)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q11_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2017_q14_sol(fig_dir: Path):
    """Hyperbolic streamlines xy = C and equipotentials x^2 - y^2 = C' for 2017 Q14."""
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    fig.patch.set_facecolor("white")

    x = np.linspace(-2.5, 2.5, 400)
    y = np.linspace(-2.5, 2.5, 400)
    X, Y = np.meshgrid(x, y)
    Phi = 0.5 * (X**2 - Y**2)
    Psi = X * Y

    ax.contour(X, Y, Psi, levels=[-3.0, -1.8, -0.9, -0.35, 0.35, 0.9, 1.8, 3.0],
               colors="#0284c7", linewidths=1.9, linestyles="solid")
    ax.contour(X, Y, Phi, levels=[-2.2, -1.2, -0.45, 0.45, 1.2, 2.2],
               colors="#dc2626", linewidths=1.2, linestyles="--")

    ax.axhline(0, color="#0f172a", lw=1.4)
    ax.axvline(0, color="#0f172a", lw=1.4)
    for px, py in [(0, 1.6), (0, -1.6), (1.3, 0), (-1.3, 0), (1.0, 0.9), (-1.0, 0.9), (1.0, -0.9), (-1.0, -0.9)]:
        vx, vy = px, -py
        nrm = math.hypot(vx, vy)
        ax.annotate("", xy=(px + 0.32 * vx / nrm, py + 0.32 * vy / nrm), xytext=(px, py),
                    arrowprops=dict(arrowstyle="->", color="#0369a1", lw=1.8))

    ax.plot([], [], color="#0284c7", lw=2.0, label="流线簇 $xy = C$（双曲线，$a > 0$ 流向）")
    ax.plot([], [], color="#dc2626", lw=1.3, ls="--", label="等势线簇 $x^2 - y^2 = C^{\\prime}$（与流线正交）")
    ax.legend(loc="upper right", fontsize=8.8, framealpha=0.95)
    ax.set_xlabel("$x$", fontsize=10.5)
    ax.set_ylabel("$y$", fontsize=10.5)
    ax.set_title("第 14 题：平面驻点势流 $\\varphi = \\frac{a}{2}(x^2 - y^2)$ 流线与等势线正交网图", fontsize=10.5, pad=8)
    ax.set_xlim(-2.4, 2.4)
    ax.set_ylim(-2.4, 2.4)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.2)
    plt.tight_layout()
    fig.savefig(fig_dir / "q14_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# Matplotlib Solution Figures for 2016 (dpi=220, ZERO CJK inside $...$)
# ==============================================================================

def draw_2016_q02_sol(fig_dir: Path):
    """Parallel-plate parabolic velocity & shear stress directions on blocks A, B, C for 2016 Q02."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.0), gridspec_kw={"width_ratios": [1.55, 1.0]})
    fig.patch.set_facecolor("white")

    r = np.linspace(-1.0, 1.0, 200)
    u = 1.6 * (1.0 - r**2)
    ax1.plot([-0.2, 3.8], [1.0, 1.0], color="#1e293b", lw=2.2)
    ax1.plot([-0.2, 3.8], [-1.0, -1.0], color="#1e293b", lw=2.2)
    for xh in np.linspace(-0.15, 3.7, 28):
        ax1.plot([xh, xh + 0.1], [1.0, 1.12], color="#64748b", lw=0.9)
        ax1.plot([xh, xh - 0.1], [-1.0, -1.12], color="#64748b", lw=0.9)

    ax1.axhline(0, color="#94a3b8", ls="-.", lw=1.0)
    ax1.plot(u, r, color="#0284c7", lw=2.2)
    ax1.axvline(0, ymin=0.08, ymax=0.92, color="#334155", lw=1.2)
    for ri in np.linspace(-0.8, 0.8, 9):
        ui = 1.6 * (1.0 - ri**2)
        ax1.annotate("", xy=(ui, ri), xytext=(0, ri),
                     arrowprops=dict(arrowstyle="->", color="#0284c7", lw=1.1))

    blocks = [
        ("A", 0.72, 0.90, "left", "right"),
        ("B", -0.09, 0.09, "left", "left"),
        ("C", -0.78, -0.60, "right", "left"),
    ]
    bx0, bw = 2.35, 0.68
    for name, y_bot, y_top, top_dir, bot_dir in blocks:
        rect = patches.Rectangle((bx0, y_bot), bw, y_top - y_bot,
                                 facecolor="#e0f2fe", edgecolor="#0f172a", lw=1.5, hatch="///")
        ax1.add_patch(rect)
        ax1.text(bx0 - 0.18, 0.5 * (y_bot + y_top), f"${name}$", fontsize=12, va="center", ha="right", fontweight="bold")
        for y_pos, drc in [(y_top + 0.06, top_dir), (y_bot - 0.06, bot_dir)]:
            if drc == "left":
                ax1.annotate("", xy=(bx0 + 0.05, y_pos), xytext=(bx0 + bw - 0.05, y_pos),
                             arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.8))
            else:
                ax1.annotate("", xy=(bx0 + bw - 0.05, y_pos), xytext=(bx0 + 0.05, y_pos),
                             arrowprops=dict(arrowstyle="->", color="#16a34a", lw=1.8))

    ax1.text(2.7, 1.18, "红箭头：慢层阻滞（向左）　绿箭头：快层拖曳（向右）", fontsize=9.3, ha="center", color="#334155")
    ax1.text(-0.12, -0.08, "$O$", fontsize=11)
    ax1.set_xlim(-0.3, 3.9)
    ax1.set_ylim(-1.28, 1.32)
    ax1.axis("off")
    ax1.set_title("（a）自由水体 $A$、$B$、$C$ 上下表面切应力方向", fontsize=10.8, pad=6)

    ax2.plot([-0.1, 1.35], [1.0, 1.0], color="#1e293b", lw=2.0)
    ax2.plot([-0.1, 1.35], [-1.0, -1.0], color="#1e293b", lw=2.0)
    ax2.axhline(0, color="#94a3b8", ls="-.", lw=1.0)
    ax2.axvline(0, ymin=0.1, ymax=0.9, color="#334155", lw=1.2)
    tau_mag = np.abs(r)
    ax2.plot(tau_mag, r, color="#ea580c", lw=2.2)
    ax2.fill_betweenx(r, 0, tau_mag, color="#fed7aa", alpha=0.45)
    ax2.scatter([0.90, 0.0, 1.0], [0.90, 0.0, 1.0], color=["#dc2626", "#0284c7", "#7c2d12"], zorder=5, s=28)
    ax2.text(1.03, 0.92, "壁面 $\\tau_{\\max}$", fontsize=10, color="#7c2d12")
    ax2.text(0.86, 0.72, "$A$ 上面 / $C$ 下面最大", fontsize=9.2, color="#dc2626")
    ax2.text(0.10, 0.04, "对称轴 $\\tau = 0$（$B$ 处最小）", fontsize=9.2, color="#0369a1")
    ax2.set_xlim(-0.15, 1.68)
    ax2.set_ylim(-1.28, 1.32)
    ax2.axis("off")
    ax2.set_title("（b）切应力大小 $|\\tau| = \\mu|\\mathrm{d}u/\\mathrm{d}r|$ 分布", fontsize=10.8, pad=6)

    plt.tight_layout()
    fig.savefig(fig_dir / "q02_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2016_q03_sol(fig_dir: Path):
    """Required solution diagram for 2016 Q03: S-curve vertical pressure bodies + horizontal pressure triangle."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 4.4))
    fig.patch.set_facecolor("white")

    th_up = np.linspace(math.pi / 2, -math.pi / 2, 120)
    x_up = 0.75 * np.cos(th_up)
    y_up = 2.25 + 0.75 * np.sin(th_up)
    th_dn = np.linspace(math.pi / 2, 3 * math.pi / 2, 120)
    x_dn = 0.75 * np.cos(th_dn)
    y_dn = 0.75 + 0.75 * np.sin(th_dn)

    # Panel (a): Vertical pressure bodies
    ax1.add_patch(patches.Polygon(list(zip(x_up, y_up)), closed=True,
                                  facecolor="#ffedd5", edgecolor="#ea580c", lw=1.4, alpha=0.85,
                                  hatch="///", label="上段虚压力体（铅垂向上 $\\uparrow$）"))
    ax1.add_patch(patches.Polygon(list(zip(x_dn, y_dn)), closed=True,
                                  facecolor="#bae6fd", edgecolor="#0284c7", lw=1.4, alpha=0.85,
                                  hatch="\\\\\\", label="下段实压力体（铅垂向下 $\\downarrow$）"))

    ax1.plot([0.0, 1.85], [3.0, 3.0], color="#0284c7", lw=2.0)
    ax1.plot([-1.1, 1.85], [0.0, 0.0], color="#0f172a", lw=2.2)
    for xh in np.linspace(-1.0, 1.75, 16):
        ax1.plot([xh, xh - 0.10], [0.0, -0.14], color="#64748b", lw=0.9)
    ax1.plot(x_up, y_up, color="#0f172a", lw=2.8, zorder=5)
    ax1.plot(x_dn, y_dn, color="#0f172a", lw=2.8, zorder=5)
    ax1.plot([0, 0], [0.0, 3.0], color="#475569", ls=":", lw=1.4)

    ax1.annotate("", xy=(0.35, 2.75), xytext=(0.35, 1.75),
                 arrowprops=dict(arrowstyle="->", color="#c2410c", lw=2.5), zorder=6)
    ax1.annotate("", xy=(-0.35, 0.25), xytext=(-0.35, 1.25),
                 arrowprops=dict(arrowstyle="->", color="#0369a1", lw=2.5), zorder=6)

    ax1.text(-0.20, 3.02, "$A$", fontsize=11, fontweight="bold")
    ax1.scatter([0.0], [1.50], color="#0f172a", s=22, zorder=7)
    ax1.text(-0.18, 1.62, "$E$（拐点）", fontsize=9.2, color="#334155", ha="right", va="center")
    ax1.text(0.0, -0.32, "$B$", fontsize=11, fontweight="bold", ha="center")
    ax1.text(1.35, 2.72, "水体在右侧", fontsize=9.5, ha="center", color="#0369a1")
    ax1.legend(loc="lower right", fontsize=8.4, framealpha=0.94)
    ax1.set_xlim(-1.25, 2.15)
    ax1.set_ylim(-0.48, 3.35)
    ax1.set_aspect("equal")
    ax1.axis("off")
    ax1.set_title("（a）铅垂静水压力的压力体分布图", fontsize=10.5, pad=6)

    # Panel (b): Horizontal pressure distribution
    ax2.plot([0, 0], [0, 3.0], color="#0f172a", lw=2.6)
    ax2.plot([0, 1.65], [3.0, 3.0], color="#0284c7", lw=2.0)
    ax2.plot([-0.4, 2.0], [0.0, 0.0], color="#0f172a", lw=2.2)

    ax2.add_patch(patches.Polygon([(0, 3.0), (0, 0.0), (1.60, 0.0)],
                                  closed=True, facecolor="#dbeafe", edgecolor="#2563eb", lw=1.8, alpha=0.82))
    for yi in np.linspace(0.3, 2.6, 7):
        xi = 1.60 * (3.0 - yi) / 3.0
        ax2.annotate("", xy=(0.03, yi), xytext=(xi, yi),
                     arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=1.4))

    ax2.text(-0.18, 3.0, "$A$", fontsize=11, fontweight="bold", ha="right", va="center")
    ax2.text(0.0, -0.32, "$B$", fontsize=11, fontweight="bold", ha="center")
    ax2.text(1.65, 0.12, "$p_B = \\rho g H$", fontsize=10, color="#1e40af", fontweight="bold")
    ax2.text(1.18, 1.75, "水平分力 $P_x$ 指向左\n$p(z) = \\rho g z$ 呈三角形分布", fontsize=9.3, color="#1e40af",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="#eff6ff", edgecolor="#93c5fd"))

    ax2.set_xlim(-0.55, 2.85)
    ax2.set_ylim(-0.48, 3.35)
    ax2.set_aspect("equal")
    ax2.axis("off")
    ax2.set_title("（b）铅垂投影面上的水平压强分布图", fontsize=10.5, pad=6)

    plt.tight_layout()
    fig.savefig(fig_dir / "q03_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2016_q05_sol(fig_dir: Path):
    """Lossless constant-diameter bent pipe ABC EGL/HGL showing min/max pressure & pA < rho*g*H."""
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    fig.patch.set_facecolor("white")

    ax.plot([0.5, 2.2, 2.2], [0.4, 0.4, 1.0], color="#0f172a", lw=2.0)
    ax.plot([2.2, 2.2], [1.28, 3.6], color="#0f172a", lw=2.0)
    ax.add_patch(patches.Rectangle((0.5, 0.42), 1.68, 2.88, facecolor="#bae6fd", alpha=0.55))
    ax.plot([0.5, 2.2], [3.3, 3.3], color="#0284c7", lw=2.0)

    px = [2.2, 4.9, 7.2]
    py = [1.14, 2.65, 0.65]
    ax.plot(px, py, color="#0f172a", lw=7.5, solid_capstyle="round", zorder=3)
    ax.plot(px, py, color="#e0f2fe", lw=4.5, solid_capstyle="round", zorder=4)

    ax.plot([2.2, 7.5], [3.30, 3.30], color="#15803d", lw=2.3, label="总水头线 EGL（不计损失，水平）")
    ax.plot([2.2, 7.5], [0.65, 0.65], color="#dc2626", lw=2.2, ls="--", label="测压管水头线 HGL（平行位于 EGL 下方 $\\frac{v^2}{2g}$）")

    ax.annotate("", xy=(4.9, 2.65), xytext=(4.9, 0.65), arrowprops=dict(arrowstyle="<->", color="#b91c1c", lw=1.8))
    ax.text(6.15, 2.38, "最高点 $B$ 高出 HGL 最多\n负压最大，压强最小！",
            fontsize=9.0, color="#b91c1c", fontweight="bold", ha="left", va="center", zorder=8,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#fef2f2", edgecolor="#fca5a5"))

    ax.text(2.45, 0.90, "$A$", fontsize=11, fontweight="bold")
    ax.text(4.85, 2.85, "$B$", fontsize=11, fontweight="bold", ha="center")
    ax.text(7.35, 0.42, "$C$（最低点，$p_C = 0$ 最大）", fontsize=9.2, color="#0f172a", fontweight="bold")

    ax.annotate("", xy=(1.25, 3.30), xytext=(1.25, 1.14), arrowprops=dict(arrowstyle="<->", color="#334155", lw=1.4))
    ax.text(1.15, 2.22, "$H$", fontsize=11, ha="right", va="center")
    ax.text(2.35, 3.45, "$v_A = v_B = v_C = \\mathrm{const},\\; p_A = \\rho g H - \\frac{1}{2}\\rho v^2 < \\rho g H$",
            fontsize=9.3, color="#15803d", fontweight="bold")

    ax.legend(loc="lower left", fontsize=8.5, framealpha=0.95)
    ax.set_title("第 5 题：等径弯管（不计损失）总水头线与测压管水头线分析图", fontsize=10.8, pad=6)
    ax.set_xlim(0.3, 9.4)
    ax.set_ylim(0.05, 3.80)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q05_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2016_q08_sol(fig_dir: Path):
    """Open-channel uniform-flow control-volume force balance for 2016 Q08."""
    fig, ax = plt.subplots(figsize=(8.0, 4.1))
    fig.patch.set_facecolor("white")

    th = math.radians(15.0)
    x_bed = np.array([0.6, 7.6])
    y_bed = 2.6 - (x_bed - 0.6) * math.tan(th)
    ax.plot(x_bed, y_bed, color="#0f172a", lw=2.4)

    s1, s2, h = 1.6, 5.0, 1.15
    cos_t, sin_t = math.cos(th), math.sin(th)
    A = np.array([0.6 + s1 * cos_t, 2.6 - s1 * sin_t])
    D = np.array([0.6 + s2 * cos_t, 2.6 - s2 * sin_t])
    B = A + h * np.array([sin_t, cos_t])
    C = D + h * np.array([sin_t, cos_t])

    ax.add_patch(patches.Polygon([A, B, C, D], closed=True, facecolor="#bae6fd", edgecolor="#0284c7", lw=1.8, alpha=0.75))
    B_ext = A - 1.2 * np.array([cos_t, -sin_t]) + h * np.array([sin_t, cos_t])
    C_ext = D + 1.4 * np.array([cos_t, -sin_t]) + h * np.array([sin_t, cos_t])
    ax.plot([B_ext[0], C_ext[0]], [B_ext[1], C_ext[1]], color="#0284c7", lw=2.0)

    u_flow = np.array([cos_t, -sin_t])
    p1_pt = A + 0.38 * h * np.array([sin_t, cos_t])
    p2_pt = D + 0.38 * h * np.array([sin_t, cos_t])
    ax.annotate("", xy=p1_pt, xytext=p1_pt - 0.9 * u_flow, arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=2.2))
    ax.text(*(p1_pt - 1.0 * u_flow), "$P_1$", fontsize=10.5, ha="right", color="#1e40af", fontweight="bold")
    ax.annotate("", xy=p2_pt, xytext=p2_pt + 0.9 * u_flow, arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=2.2))
    ax.text(*(p2_pt + 1.0 * u_flow), "$P_2 = P_1$", fontsize=10.5, ha="left", color="#1e40af", fontweight="bold")

    mid_cv = 0.25 * (A + B + C + D)
    ax.annotate("", xy=mid_cv + 1.05 * u_flow, xytext=mid_cv, arrowprops=dict(arrowstyle="->", color="#15803d", lw=2.5))
    ax.text(*(mid_cv + 0.05 * u_flow + np.array([0.0, 0.28])), "$G\\sin\\theta$（顺坡分力）",
            fontsize=9.3, color="#15803d", fontweight="bold", ha="center")

    mid_bed = 0.5 * (A + D)
    ax.annotate("", xy=mid_bed - 1.15 * u_flow, xytext=mid_bed + 0.1 * u_flow,
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.5))
    ax.text(*(mid_bed - 0.6 * u_flow + np.array([-0.15, -0.38])), "$F_f = \\tau_0 \\chi l$（边壁摩阻力）",
            fontsize=9.5, color="#b91c1c", fontweight="bold", ha="center")

    ax.plot([D[0] - 0.2, 7.6], [y_bed[1], y_bed[1]], color="#64748b", ls="--", lw=1.2)
    ax.text(6.15, y_bed[1] + 0.08, "$\\theta$", fontsize=10.5)

    ax.text(4.1, 3.65,
            "均匀流沿流向力平衡：$P_1 - P_2 + G\\sin\\theta - F_f = 0 \\Rightarrow G\\sin\\theta = F_f > 0$\n"
            "仅顺坡（$i > 0$）满足平衡；平坡（$i = 0$）与逆坡（$i < 0$）无法平衡摩阻力 $F_f$！",
            fontsize=9.4, ha="center", va="center", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#f8fafc", edgecolor="#cbd5e1"))

    ax.set_title("第 8 题：明渠均匀流隔离体沿流向受力平衡机理图", fontsize=11, pad=6)
    ax.set_xlim(0.2, 8.2)
    ax.set_ylim(0.2, 4.25)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q08_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2016_q10_sol(fig_dir: Path):
    """Spherical valve plug (d=0.2m, D=0.1m) exact buoyancy + orifice head balance for 2016 Q10."""
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    fig.patch.set_facecolor("white")

    # Outer open tank (water surface at y = 2.65 -> h2 = 1.5 m above orifice y = 1.30)
    ax.plot([0.8, 0.8, 5.2, 5.2], [3.5, 0.4, 0.4, 3.5], color="#0f172a", lw=2.2)
    ax.add_patch(patches.Rectangle((0.82, 0.42), 4.36, 2.23, facecolor="#e0f2fe", alpha=0.55))
    ax.plot([0.8, 1.85], [2.65, 2.65], color="#0284c7", lw=2.0)
    ax.plot([4.15, 5.2], [2.65, 2.65], color="#0284c7", lw=2.0)
    ax.text(4.68, 2.82, "$p_a$", fontsize=10, ha="center", color="#0369a1")

    # Inner closed container (water surface at y = 3.55 -> h1 = 2.5 m above orifice y = 1.30!)
    ax.plot([1.85, 1.85, 2.65], [3.85, 1.30, 1.30], color="#0f172a", lw=2.2)
    ax.plot([3.35, 4.15, 4.15], [1.30, 1.30, 3.85], color="#0f172a", lw=2.2)
    arc_top = np.linspace(0, np.pi, 100)
    ax.plot(3.0 + 1.15 * np.cos(arc_top), 3.85 + 0.42 * np.sin(arc_top), color="#0f172a", lw=2.2)
    ax.add_patch(patches.Rectangle((1.87, 1.32), 2.26, 2.23, facecolor="#bae6fd", alpha=0.55))
    ax.plot([1.85, 4.15], [3.55, 3.55], color="#0284c7", lw=2.0)
    ax.text(3.0, 3.92, "封闭气室 $p_0 = -\\rho g h_v$", fontsize=9.2, ha="center", color="#991b1b", fontweight="bold")

    # Sphere d=0.2m (radius 0.70 scaled, hole half-width 0.35 -> yO = 1.30 + 0.70*sqrt(3)/2 = 1.906)
    Rs = 0.70
    yO = 1.30 + Rs * math.sqrt(3) / 2.0
    ax.add_patch(patches.Circle((3.0, yO), Rs, facecolor="#fef3c7", edgecolor="#0f172a", lw=2.2, zorder=5))
    ax.plot([2.65, 3.35], [1.30, 1.30], color="#dc2626", ls="--", lw=1.6, zorder=6)

    # Dimensions h1=2.5m (inner) & h2=1.5m (outer)
    ax.plot([0.15, 1.85], [3.55, 3.55], color="#64748b", ls=":", lw=1.1)
    ax.plot([0.15, 1.85], [1.30, 1.30], color="#64748b", ls=":", lw=1.1)
    ax.annotate("", xy=(0.30, 3.55), xytext=(0.30, 1.30), arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.3))
    ax.text(0.24, 2.42, "$h_1=2.5\\,\\mathrm{m}$", fontsize=8.8, ha="right", va="center", rotation=90)
    ax.annotate("", xy=(1.25, 2.65), xytext=(1.25, 1.30), arrowprops=dict(arrowstyle="<->", color="#0369a1", lw=1.3))
    ax.text(1.18, 1.98, "$h_2=1.5\\,\\mathrm{m}$", fontsize=8.8, ha="right", va="center", rotation=90, color="#0369a1")

    # Force vectors on sphere
    ax.annotate("", xy=(3.0, yO - 0.56), xytext=(3.0, yO + 0.14),
                arrowprops=dict(arrowstyle="->", color="#475569", lw=2.3), zorder=7)
    ax.text(3.0, yO + 0.34, "$G = 353\\,\\mathrm{N}$", fontsize=8.7, ha="center", va="center",
            color="#334155", fontweight="bold", zorder=8)

    ax.annotate("", xy=(2.48, yO + 1.25), xytext=(2.48, yO + 0.45),
                arrowprops=dict(arrowstyle="->", color="#15803d", lw=2.5), zorder=7)
    ax.text(2.60, yO + 1.00, "浮力 $+\\rho g\\frac{\\pi d^3}{6}$", fontsize=8.6, ha="left", va="center",
            color="#15803d", fontweight="bold")

    ax.annotate("", xy=(3.0, 1.20), xytext=(3.0, 0.58),
                arrowprops=dict(arrowstyle="->", color="#dc2626", lw=2.6), zorder=7)
    ax.text(3.0, 0.22, "孔口内外水头差推力 $\\rho g(h_2 - h_1 + h_v)\\frac{\\pi}{4}D^2\\;(\\uparrow)$",
            fontsize=8.6, ha="center", va="top", color="#b91c1c", fontweight="bold")

    # Exact derivation box on right
    ax.text(5.55, 2.35,
            "圆球止水塞竖向受力平衡：\n"
            "$F_z = \\rho g\\frac{\\pi d^3}{6} + \\rho g(h_2 - h_1 + h_v)\\frac{\\pi}{4}D^2 = G$\n"
            "• 全球浮力：$F_b = 41.05\\,\\mathrm{N}\\;(\\uparrow)$\n"
            "• 净需孔口顶推力：$G - F_b = 311.95\\,\\mathrm{N}$\n"
            "• 所需净水头差：$h_v - (h_1 - h_2) = 4.053\\,\\mathrm{m}$\n"
            "• 临界真空高度：$h_v = 1.0 + 4.053 \\approx 5.05\\,\\mathrm{m}$",
            fontsize=9.0, ha="left", va="center", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.38", facecolor="#f0fdf4", edgecolor="#86efac"))

    ax.set_title("第 10 题：圆球止水塞浮力与孔口内外压差联合平衡分析图", fontsize=11, pad=6)
    ax.set_xlim(-0.2, 9.6)
    ax.set_ylim(-0.08, 4.42)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q10_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


def draw_2016_q12_sol(fig_dir: Path):
    """Horizontal pipe 2-2 to 3-3 momentum CV & EGL/HGL diagram for 2016 Q12."""
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    fig.patch.set_facecolor("white")

    ax.plot([0.5, 2.0, 2.0], [0.5, 0.5, 0.95], color="#0f172a", lw=2.2)
    ax.plot([2.0, 2.0], [1.35, 3.65], color="#0f172a", lw=2.2)
    ax.add_patch(patches.Rectangle((0.5, 0.52), 1.48, 2.88, facecolor="#bae6fd", alpha=0.55))
    ax.plot([0.5, 2.0], [3.4, 3.4], color="#0284c7", lw=2.0)

    ax.add_patch(patches.Rectangle((2.0, 0.95), 4.8, 0.40, facecolor="#bae6fd", alpha=0.65))
    ax.plot([2.0, 6.8], [1.35, 1.35], color="#0f172a", lw=2.2)
    ax.plot([2.0, 6.8], [0.95, 0.95], color="#0f172a", lw=2.2)

    ax.plot([4.3, 4.3], [0.65, 1.70], color="#dc2626", ls="--", lw=1.7)
    ax.plot([6.8, 6.8], [0.65, 1.70], color="#dc2626", ls="--", lw=1.7)
    ax.text(4.3, 0.45, "断面 2—2", fontsize=9.5, ha="center", color="#991b1b")
    ax.text(6.8, 0.45, "断面 3—3 ($p_3 = 0$)", fontsize=9.5, ha="center", color="#991b1b")

    ax.plot([2.0, 4.3, 6.8], [3.40, 2.725, 2.275], color="#15803d", lw=2.3, label="总水头线 EGL")
    ax.plot([2.0, 4.3, 6.8], [2.275, 1.60, 1.15], color="#dc2626", lw=2.1, ls="--", label="测压管水头线 HGL")

    ax.annotate("", xy=(4.75, 1.15), xytext=(3.65, 1.15), arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=2.5))
    ax.text(3.35, 1.58, "$P_2 = p_2 A = 277.1\\,\\mathrm{N}\\;(\\rightarrow)$", fontsize=8.8, ha="center", color="#1e40af", fontweight="bold")
    ax.annotate("", xy=(5.15, 1.55), xytext=(6.25, 1.55), arrowprops=dict(arrowstyle="->", color="#b91c1c", lw=2.4))
    ax.text(5.75, 1.72, "管壁阻力 $N_x = 277.1\\,\\mathrm{N}\\;(\\leftarrow)$", fontsize=8.8, ha="center", color="#b91c1c", fontweight="bold")

    ax.text(5.55, 3.18,
            "$v_2 = v_3 = 6.64\\,\\mathrm{m/s}$\n"
            "$\\frac{p_2}{\\rho g} = h_{w2} = 0.4\\frac{v^2}{2g} = 0.90\\,\\mathrm{m}$\n"
            "水流对管壁水平总作用力 $F = 277.1\\,\\mathrm{N}\\;(\\rightarrow)$",
            fontsize=9.0, ha="center", va="center", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.32", facecolor="#f0fdf4", edgecolor="#86efac"))

    ax.legend(loc="upper left", bbox_to_anchor=(0.24, 0.99), fontsize=8.5, framealpha=0.94)
    ax.set_title("第 12 题：2—2 至 3—3 管段水头线与动量控制体受力图", fontsize=10.8, pad=6)
    ax.set_xlim(0.3, 7.6)
    ax.set_ylim(0.25, 3.80)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(fig_dir / "q12_sol.png", dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# 2017 Exam Paper Builder (14 Questions, 48 + 102 = 150 pts)
# ==============================================================================

def build_2017_paper() -> dict:
    return {
        "year": 2017,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "全卷共 14 道题：一、简答题（第 1～6 题，6×8=48 分）；二、计算题（第 7～14 题，12+15+10+15+15+15+10+10=102 分）。",
            "除特别说明外，主解统一取重力加速度 $g = 9.80\\,\\mathrm{m/s^2}$（并附注 $g = 9.81\\,\\mathrm{m/s^2}$ 对照值），水的密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$，水银密度 $\\rho_{\\mathrm{m}} = 13600\\,\\mathrm{kg/m^3}$。"
        ],
        "sections": [
            {
                "id": "short",
                "title": "一、简答题",
                "description": "本大题共 6 小题，每小题 8 分，共 48 分。",
                "range": [1, 6],
                "scorePerQuestion": 8,
                "totalScore": 48
            },
            {
                "id": "calc",
                "title": "二、计算题",
                "description": "本大题共 8 小题（12+15+10+15+15+15+10+10 分），共 102 分。",
                "range": [7, 14],
                "totalScore": 102
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2017-01",
                "year": 2017,
                "no": 1,
                "type": "short",
                "score": 8,
                "title": "实际液体与理想液体的本质区别及理想液体计算模型优缺点",
                "stem": "实际液体与理想液体有何区别？试举一例说明，按理想液体进行计算的优缺点？",
                "note": "",
                "figures": [],
                "shortAnswer": "最根本区别在于是否考虑黏滞性（理想液体 μ=0、绝对不可压缩、无表面张力）；以文丘里流量计或孔口出流为例，按理想液体可大幅简化方程求得理论解析解，但忽略了水头损失导致计算流量偏大，需引入流速/流量系数修正。",
                "judgeAnswer": None,
                "answer": "（1）**本质区别**：实际液体具有黏滞性、可压缩性及表面张力；理想液体是人为抽象的理论模型，假定其绝对无黏滞性（$\\mu = 0$）、绝对不可压缩且无表面张力。由于液体的压缩性与表面张力在常规水力工程中影响极小，**是否考虑黏滞性是两者的最根本区别**。\n\n（2）**工程举例（以文丘里流量计测流为例）**：\n- **优点**：忽略黏滞性与水头损失（$h_w = 0$），可直接应用理想流体伯努利方程与连续性方程导出简洁的理论流量解析式 $Q_{\\text{理}} = \\frac{A_2}{\\sqrt{1 - (A_2/A_1)^2}}\\sqrt{2g\\Delta H}$，清晰揭示测流物理本质；\n- **缺点**：忽略实际流动中的沿程与局部水头损失，导致理论流量偏大于实测流量，工程应用时必须通过试验引入流量修正系数 $\\mu$（$Q = \\mu Q_{\\text{理}}$）加以校正。",
                "analysis": "**1. 实际液体与理想液体的物理性质对比**\n\n- **实际液体**：同时具有惯性、重力特性、黏滞性（运动时产生切应力 $\\tau = \\mu\\frac{\\mathrm{d}u}{\\mathrm{d}y}$ 并消耗机械能）、微弱的可压缩性与热胀性以及表面张力。\n- **理想液体**：绝对无黏滞性（$\\mu = 0$，无论静止还是运动状态内部均无切应力，流动不产生水头损失）、绝对不可压缩（$\\rho = \\mathrm{const}$）且不计表面张力的假想连续介质。\n- **核心差异**：工程水力学中水几乎不可压缩、表面张力仅在细管或微小水滴中显著，因此**有无黏滞性**是实际液体与理想液体的首要区别。\n\n**2. 举例评述按理想液体计算的优缺点**\n\n以**文丘里流量计**（或**孔口自由出流**、**绕流阻力计算**）为例：\n- **优点**：省去复杂的黏性切应力项与难以纯理论预估的水头损失项 $h_w$，使运动微分方程（由 N-S 方程退化为欧拉方程）和能量方程大幅简化，能迅速求得封闭解析解，并用于指导工程试验数据的整理与无量纲化；\n- **缺点**：无法反映真实流动中的机械能不可逆耗散（$h_w > 0$）、边界层分离与绕流压差阻力等现象。例如文丘里管或薄壁孔口按理想液体算得的理论流量均大于实际流量，必须乘以实验测定的流量系数（或流速系数 $\\varphi$）才能用于实际工程；在管道长距离输水计算中若按理想液体忽略阻力则会得出完全失真的结果。",
                "analysisFigures": [],
                "pitfalls": "切忌只背“理想液体没有黏滞性”而不举具体实例，或只写优点漏写缺点！答题务必包含“核心区别（黏滞性）+ 具体工程实例（如文丘里管/孔口出流）+ 优点（简化数学求解）+ 缺点（忽略水头损失需系数修正）”四要素。",
                "chapter": 1,
                "kps": ["理想液体假设", "黏滞性", "理想流体伯努利方程"],
                "method": "牛顿内摩擦定律与黏滞性物理本质辨析",
                "difficulty": 1,
                "rubric": [
                    {"label": "准确阐明实际液体与理想液体的区别，并点明“有无黏滞性”是最根本区别", "pts": 3},
                    {"label": "举出恰当的水力学工程实例（如文丘里流量计、孔口出流等）", "pts": 2},
                    {"label": "完整辩证地说明按理想液体计算的优点（简化求解）与缺点（忽略水头损失需系数修正）", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2017-02",
                "year": 2017,
                "no": 2,
                "type": "short",
                "score": 8,
                "title": "静水压强基本公式中相对压强与绝对压强的适用性辨析",
                "stem": "水静力学基本公式 $p = p_0 + \\rho g h$ 中，压强 $p$ 是相对压强还是绝对压强？或两者均可？为什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "两者均可，只要等式两端的 p 与 p0 采用统一的压强起算基准即可（等式两端同加或同减当地大气压 pa 恒等式不变）。",
                "judgeAnswer": None,
                "answer": "**两者均可**（既可同取相对压强，也可同取绝对压强），前提是公式中的 $p$ 与液面压强 $p_0$ 必须采用**同一压强计算基准**。\n\n**原因**：绝对压强与相对压强仅相差一个常数——当地大气压强 $p_a$，即 $p_{\\text{abs}} = p_{\\text{rel}} + p_a$、$p_{0,\\text{abs}} = p_{0,\\text{rel}} + p_a$。将其代入绝对压强形式的水静力学基本方程 $p_{\\text{abs}} = p_{0,\\text{abs}} + \\rho g h$，等式左右两端的 $p_a$ 恰好消去，得到相对压强形式 $p_{\\text{rel}} = p_{0,\\text{rel}} + \\rho g h$，形式完全相同。",
                "analysis": "**1. 绝对压强与相对压强的定义关系**\n\n- **绝对压强** $p_{\\text{abs}}$：以绝对真空（零压强）为起算基准；\n- **相对压强（表压）** $p_{\\text{rel}}$：以当地大气压强 $p_a$ 为起算基准。\n\n两者对同一点满足严格的平移关系：\n\n$$\np_{\\text{abs}} = p_{\\text{rel}} + p_a, \\qquad p_{0,\\text{abs}} = p_{0,\\text{rel}} + p_a\n$$\n\n**2. 数学消元验证**\n\n由重力场中静止均质液体的平衡微分方程 $\\mathrm{d}p = -\\rho g\\,\\mathrm{d}z$ 积分可知，任意两点间的**压强差**仅取决于液体重度与竖直高差：$p - p_0 = \\rho g h$。将绝对压强与相对压强的换算式代入：\n\n$$\n(p_{\\text{rel}} + p_a) = (p_{0,\\text{rel}} + p_a) + \\rho g h \\iff p_{\\text{rel}} = p_{0,\\text{rel}} + \\rho g h\n$$\n\n可见，当地大气压 $p_a$ 作为常数在等式两端完全抵消。因此只要 $p$ 与 $p_0$ 采用**统一标准**（同为绝对压强，或同为相对压强），公式 $p = p_0 + \\rho g h$ 均严格成立；特别地，对敞口容器液面，$p_{0,\\text{abs}} = p_a$，而 $p_{0,\\text{rel}} = 0$，使用相对压强可简写为 $p_{\\text{rel}} = \\rho g h$。",
                "analysisFigures": [],
                "pitfalls": "虽然绝对压强和相对压强均可使用，但**严禁在同一方程中混用两种基准**（例如 $p_0$ 代入相对压强却把 $p$ 当成绝对压强）。",
                "chapter": 2,
                "kps": ["静水压强基本方程", "绝对压强与相对压强"],
                "method": "压强零点平移消元验证法",
                "difficulty": 1,
                "rubric": [
                    {"label": "明确给出结论“两者均可”并强调 p 与 p0 必须采用统一计压基准", "pts": 3},
                    {"label": "准确写出绝对压强与相对压强的起算基准及关系式 p_abs = p_rel + p_a", "pts": 2},
                    {"label": "通过代入方程消去两端当地大气压 p_a 严密证明公式形式不变", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2017-03",
                "year": 2017,
                "no": 3,
                "type": "short",
                "score": 8,
                "title": "静止液体平面受压面压力中心 D 与形心 C 的相对位置及重合条件",
                "stem": "压力中心 $D$ 和受压面形心 $C$ 的位置之间有何关系？什么情况下 $D$ 点和 $C$ 点重合？",
                "note": "",
                "figures": [],
                "shortAnswer": "倾斜或铅直平面上，压力中心 D 恒位于形心 C 下方（yD = yC + IC/(yC·A) > yC）；当受压平面水平放置（或仅受均匀等压作用、淹深趋于无穷大）时，压强均匀分布，D 与 C 重合。",
                "judgeAnswer": None,
                "answer": "（1）**相对位置关系**：对倾斜或铅直放置于静止液体中的平面，压力中心 $D$ 总是位于受压面形心 $C$ 的**下方**，定量满足：\n\n$$\ny_D = y_C + \\frac{I_C}{y_C A} > y_C\n$$\n\n（式中 $I_C > 0$ 为受压面对过形心水平轴的惯性矩，$y_C > 0$，$A > 0$，故偏心距 $e = \\frac{I_C}{y_C A} > 0$）。\n\n（2）**重合条件**：当受压平面**水平放置**（$\\sin\\theta = 0$，各点淹深相等、静水压强均匀分布）时，压心 $D$ 与形心 $C$ 严格重合；此外，在无重力/纯气体均匀受压情形下，或倾斜平面淹深极大（$y_C \\to \\infty$，偏心距 $e \\to 0$）时，$D$ 与 $C$ 也重合（或趋于重合）。",
                "analysis": "**1. 压心公式推导与物理成因**\n\n设平面受压面与水平自由液面的夹角为 $\\theta$（$\\theta \\neq 0$），沿受压面斜面向下建立坐标 $y$（液面交线处 $y = 0$）。任意微元 $\\mathrm{d}A$ 处的静水压强 $p = \\rho g y \\sin\\theta$ 随深度线性增大，即受压面下部承受的压强大于上部。对液面交线取合力矩等于各微元压力矩之和：\n\n$$\ny_D P = \\int_A y\\,(\\rho g y\\sin\\theta)\\,\\mathrm{d}A = \\rho g\\sin\\theta \\int_A y^2\\,\\mathrm{d}A = \\rho g\\sin\\theta\\,(I_C + y_C^2 A)\n$$\n\n代入总压力 $P = \\rho g y_C \\sin\\theta \\cdot A$ 并约去公因子 $\\rho g\\sin\\theta$，得：\n\n$$\ny_D = y_C + \\frac{I_C}{y_C A}\n$$\n\n由于 $I_C > 0$、$y_C > 0$、$A > 0$，必有 $y_D > y_C$，故**压力中心 $D$ 恒在形心 $C$ 的下方**。\n\n**2. $D$ 点与 $C$ 点重合的条件**\n\n- **水平放置平面**（$\\theta = 0$）：平面上各点处于同一等压面，静水压强 $p = \\rho g h = \\mathrm{const}$ 均匀分布，总压力合力必然通过几何形心，$D$ 与 $C$ 严格重合。\n- **补充说明**：当倾斜平面相对于自身尺寸淹没极深（$y_C \\gg \\sqrt{I_C/A}$）时，偏心距 $e = \\frac{I_C}{y_C A} \\to 0$，压心 $D$ 无限趋近于形心 $C$；若两侧均完全淹没（潜没闸门），净压强差沿全门均匀分布，净总压力作用点亦与形心重合。",
                "analysisFigures": [],
                "pitfalls": "切忌说“压心永远在形心下方”——忽略“水平放置时重合”的例外情形是水力学简答与判断题的头号失分点！",
                "chapter": 2,
                "kps": ["平面静水总压力", "压心与形心关系"],
                "method": "平面静水总压力解析法与平行移轴求压心法",
                "difficulty": 1,
                "rubric": [
                    {"label": "给出压心公式 yD = yC + IC/(yC·A) 并明确指出倾斜/铅直平面上压心 D 恒位于形心 C 下方", "pts": 4},
                    {"label": "结合压强随水深线性增大（下大上小）或 IC/(yC·A) > 0 阐明物理/数学原因", "pts": 2},
                    {"label": "准确指出受压平面水平放置（压强均匀分布）时 D 与 C 重合", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2017-04",
                "year": 2017,
                "no": 4,
                "type": "short",
                "score": 8,
                "title": "均匀流过水断面上各点单位重量液体势能与机械能分布判别",
                "stem": "均匀流过水断面上，各点单位重量液体的势能是否为常数？各点单位重量液体的机械能是否为常数？请分别说明理由。",
                "note": "",
                "figures": [],
                "shortAnswer": "单位重量液体势能（z + p/ρg）为常数（均匀流流线平行直线，过水断面满足静水压强分布）；单位重量液体机械能（z + p/ρg + u²/2g）不是常数（实际黏性流体断面上流速 u 分布不均，壁面为零、中心最大）。",
                "judgeAnswer": None,
                "answer": "（1）**各点单位重量液体的势能（测压管水头 $z + \\frac{p}{\\rho g}$）是常数**。\n- **理由**：均匀流的流线是互相平行的直线，过水断面为平面且垂直于流线，在过水断面内流体质点无向心法向加速度（$a_n = \\frac{u^2}{r} = 0$），动水压强在过水断面上按静水压强规律分布，故同一过水断面上处处满足 $z + \\frac{p}{\\rho g} = C$（常数）。\n\n（2）**各点单位重量液体的机械能（总水头 $z + \\frac{p}{\\rho g} + \\frac{u^2}{2g}$）不是常数**。\n- **理由**：实际液体具有黏滞性，受固体边壁无滑移条件制约，均匀流过水断面上各点流速 $u$ 分布不均匀（如圆管层流呈抛物线分布、紊流呈对数分布，壁面处 $u = 0$ 而中心轴处 $u = u_{\\max}$）。由于各点单位势能相等而单位动能 $\\frac{u^2}{2g}$ 随位置变化，故各点单位重量液体的总机械能 $z + \\frac{p}{\\rho g} + \\frac{u^2}{2g}$ 并非同一常数（中心最大、壁面最小）。",
                "analysis": "**1. 单位重量液体势能 $e_p = z + \\frac{p}{\\rho g}$ 的分析**\n\n均匀流具有流线平行直线的几何特征，沿垂直于流线方向（即过水断面平面内），流体微团的法向加速度 $a_n = 0$。由欧拉运动微分方程在法向上的投影：\n\n$$\n-g\\frac{\\partial z}{\\partial n} - \\frac{1}{\\rho}\\frac{\\partial p}{\\partial n} = a_n = 0 \\implies \\frac{\\partial}{\\partial n}\\left(z + \\frac{p}{\\rho g}\\right) = 0\n$$\n\n由此可见，同一均匀流过水断面上，各点的动水压强分布遵循静水压强分布规律，**单位重量液体的势能（位置水头与压强水头之和）恒为常数**。\n\n**2. 单位重量液体机械能 $e = z + \\frac{p}{\\rho g} + \\frac{u^2}{2g}$ 的分析**\n\n- 对于**实际黏性液体**，尽管同一过水断面上各点 $z + \\frac{p}{\\rho g} = C$ 相同，但固体边界无滑移条件决定了断面上局部流速 $u$ 必然不均匀（边壁处 $u = 0$，远离边壁流速增大至核心区最大），从而各点的单位动能 $\\frac{u^2}{2g}$ 互不相等。\n- 将常数势能与非常数动能相加，各点单位重量液体的机械能 $e = C + \\frac{u^2}{2g}$ **不是常数**（仅对假想无黏且来流均匀的理想液体才为常数）。",
                "analysisFigures": [],
                "pitfalls": "本题常被误答为“均匀流流速相等所以机械能也是常数”！务必区分**“沿流程不变（均匀流）”**与**“同一过水断面上处处相等”**：均匀流指的是沿程流速分布形状不变，而非同一断面上各点流速相等。",
                "chapter": 3,
                "kps": ["均匀流特性", "测压管水头", "断面流速分布"],
                "method": "势能静水分布与黏性流速梯度叠加分析法",
                "difficulty": 2,
                "rubric": [
                    {"label": "明确判断各点单位重量液体势能为常数，并由均匀流流线平行直线、满足静水压强分布给出证明", "pts": 4},
                    {"label": "明确判断各点单位重量液体机械能不是常数，并结合实际黏性流体断面流速分布不均匀（u 非常数）说明理由", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2017-05",
                "year": 2017,
                "no": 5,
                "type": "short",
                "score": 8,
                "title": "同几何参数输水与输油管道在等流速/等雷诺数下的沿程损失与临界雷诺数对比",
                "stem": "有两根 $d$、$l$、$\\Delta$ 及液体温度均相同的管道，一根输水，另一根输油，若断面平均流速 $v$ 相等，$Re$、$h_f$ 是否相等？若 $Re$ 相等，$v$、$h_f$ 是否相等？两管的 $Re_k$ 是否相等？",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）v 相等时：因 ν水≠ν油，Re 不等；仅两管同处紊流阻力平方区时 hf 相等，其余流区 hf 不等。（2）Re 相等时：v 不等（v∝ν），虽然 λ 相同，但 hf∝v² 故 hf 不等。（3）圆管下临界雷诺数 Rek（≈2000~2320）与液体种类无关，两管 Rek 相等。",
                "judgeAnswer": None,
                "answer": "已知两管管径 $d$、管长 $l$、绝对粗糙度 $\\Delta$ 及温度均相同，但同温下油的运动黏度远大于水（$\\nu_{\\text{油}} > \\nu_{\\text{水}}$）：\n\n（1）**若 $v$ 相等**：\n- 由 $Re = \\frac{vd}{\\nu}$，因 $\\nu_{\\text{水}} \\neq \\nu_{\\text{油}}$，故 **$Re$ 不相等**（$Re_{\\text{水}} > Re_{\\text{油}}$）；\n- 由达西公式 $h_f = \\lambda\\frac{l}{d}\\frac{v^2}{2g}$，若两管**同时处于紊流阻力平方区（粗糙区）**，则 $\\lambda$ 仅取决于相同的相对粗糙度 $\\Delta/d$ 而与 $Re$ 无关，此时 **$h_f$ 相等**；在其余阻力区（层流区、光滑区、过渡区）$\\lambda$ 依赖 $Re$，故 **$h_f$ 不相等**。\n\n（2）**若 $Re$ 相等**：\n- 由 $v = \\frac{Re\\cdot\\nu}{d}$，因 $\\nu_{\\text{油}} > \\nu_{\\text{水}}$，故 **$v$ 不相等**（$v_{\\text{油}} > v_{\\text{水}}$）；\n- 虽然两管 $Re$ 与 $\\Delta/d$ 均相同，故沿程阻力系数 $\\lambda$ 相等，但 $h_f = \\lambda\\frac{l}{d}\\frac{v^2}{2g} \\propto v^2$，由于 $v$ 不相等，故 **$h_f$ 不相等**（$h_{f,\\text{油}} > h_{f,\\text{水}}$）。\n\n（3）**两管的临界雷诺数 $Re_k$ 相等**：\n- 圆管下临界雷诺数 $Re_k$（工程上常取 $2000 \\sim 2320$）是无量纲普适常数，仅与管流几何边界有关，与流体种类（水或油）无关，因此两管 $Re_k$ 相等。",
                "analysis": "**1. 当断面平均流速 $v$ 相等时**\n\n- **雷诺数 $Re$**：$Re = \\frac{vd}{\\nu}$。虽然 $v$、$d$ 相同，但相同温度下油与水的运动黏度不同（$\\nu_{\\text{油}} > \\nu_{\\text{水}}$），因此 $Re_{\\text{水}} > Re_{\\text{油}}$，两者不相等。\n- **沿程水头损失 $h_f$**：$h_f = \\lambda\\frac{l}{d}\\frac{v^2}{2g}$。因 $l, d, v$ 均相同，$h_f$ 是否相等完全取决于沿程阻力系数 $\\lambda$ 是否相等。结合尼古拉兹实验阻力分区规律：\n  - 若两管均处于**紊流阻力平方区（水力粗糙区）**，$\\lambda = f(\\Delta/d)$ 与 $Re$ 无关，因 $\\Delta/d$ 相同故 $\\lambda$ 相等，从而 $h_f$ 相等；\n  - 若至少有一管处于层流区、临界过渡区、紊流光滑区或紊流过渡区，$\\lambda$ 受 $Re$ 影响，因 $Re$ 不同导致 $\\lambda$ 不同，故 $h_f$ 不相等。\n\n**2. 当雷诺数 $Re$ 相等时**\n\n- **断面平均流速 $v$**：$v = \\frac{\\nu\\,Re}{d}$。因 $Re$、$d$ 相同而 $\\nu_{\\text{油}} > \\nu_{\\text{水}}$，必有 $v_{\\text{油}} > v_{\\text{水}}$，两者不相等。\n- **沿程水头损失 $h_f$**：由于两管的 $Re$ 和相对粗糙度 $\\Delta/d$ 均相同，无论处于哪个流态分区，沿程阻力系数 $\\lambda = f(Re, \\Delta/d)$ 必定相等。但代入达西公式 $h_f = \\lambda\\frac{l}{d}\\frac{v^2}{2g}$ 可见 $h_f \\propto v^2$，因为 $v_{\\text{油}} > v_{\\text{水}}$，故 $h_{f,\\text{油}} > h_{f,\\text{水}}$，两者不相等。\n\n**3. 下临界雷诺数 $Re_k$ 的比较**\n\n圆管由紊流转变为层流的下临界雷诺数 $Re_k \\approx 2000 \\sim 2320$（扬大通用教材多取 $Re_k = 2000$ 或 $2320$）是一个与流体密度、黏度、管径及流速均无关的稳定无量纲数，故两管 $Re_k$ 相等。",
                "analysisFigures": [],
                "pitfalls": "第（1）问判断 $h_f$ 时切忌一刀切地回答“不等”！必须分阻力分区讨论：当且仅当两管**均位于紊流阻力平方区**时 $\\lambda$ 与 $Re$ 无关，此时 $h_f$ 相等。",
                "chapter": 4,
                "kps": ["雷诺数与临界雷诺数", "达西公式", "尼古拉兹阻力分区"],
                "method": "沿程阻力系数雷诺数依赖性与达西公式辨析",
                "difficulty": 2,
                "rubric": [
                    {"label": "v 相等时：指出因 ν 不同故 Re 不等；分流区说明仅同处紊流阻力平方区时 hf 相等、其余区不等", "pts": 3},
                    {"label": "Re 相等时：指出因 ν 不同故 v 不等；虽 λ 相等但 hf ∝ v² 故 hf 不等", "pts": 3},
                    {"label": "正确指出圆管下临界雷诺数 Rek 为无量纲稳定常数（≈2000~2320），两管 Rek 相等", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2017-06",
                "year": 2017,
                "no": 6,
                "type": "short",
                "score": 8,
                "title": "封闭圆形流线与流速势函数存在性的无旋判据辨析",
                "stem": "“若流场中的流线为封闭圆周线，则该流动一定不存在流速势函数”，这种说法对吗？为什么？",
                "note": "",
                "figures": [],
                "shortAnswer": "不对。流速势函数存在的充要条件是流体微团本身无旋转（无旋流动 ω=0），而非质点轨道或流线是否为圆周。典型反例为平面自由点涡（uθ = Γ/(2πr)），其流线为同心封闭圆周，但除原点奇点外处处 ωz=0，存在流速势函数 φ = (Γ/2π)θ。",
                "judgeAnswer": None,
                "answer": "**不对（错误）**。\n\n**理由**：流速势函数 $\\varphi$ 存在的充要条件是流动为**无旋流动**（即流体微团绕自身轴线的旋转角速度 $\\vec{\\omega} = \\frac{1}{2}\\nabla \\times \\vec{u} = \\vec{0}$），这取决于流体微团自身是否自转，而**不能单凭流线（或质点迹线）是否为封闭圆周来判断**。\n\n**典型反例——平面自由涡（无旋点涡）**：其速度场为 $u_r = 0,\\; u_\\theta = \\frac{\\Gamma}{2\\pi r}$（或直角坐标 $u_x = -\\frac{Cy}{x^2+y^2},\\; u_y = \\frac{Cx}{x^2+y^2}$），流线为以原点为圆心的同心封闭圆周，但在除原点外的整个复连通流场中，旋转角速度 $\\omega_z = \\frac{1}{2r}\\frac{\\partial(r u_\\theta)}{\\partial r} = 0$，流体微团只公转不自转，属于无旋流动，且存在多值流速势函数 $\\varphi = \\frac{\\Gamma}{2\\pi}\\theta = \\frac{\\Gamma}{2\\pi}\\arctan\\frac{y}{x}$。",
                "analysis": "**1. 判别势函数存在的根本标准**\n\n流体流动中是否存在流速势函数 $\\varphi$（使 $\\vec{u} = \\nabla \\varphi$），取决于流动是否**无旋（有势）**，即速度旋度为零：\n\n$$\n\\omega_x = \\frac{1}{2}\\left(\\frac{\\partial u_z}{\\partial y} - \\frac{\\partial u_y}{\\partial z}\\right) = 0, \\quad \\omega_y = \\frac{1}{2}\\left(\\frac{\\partial u_x}{\\partial z} - \\frac{\\partial u_z}{\\partial x}\\right) = 0, \\quad \\omega_z = \\frac{1}{2}\\left(\\frac{\\partial u_y}{\\partial x} - \\frac{\\partial u_x}{\\partial y}\\right) = 0\n$$\n\n**2. 反例对比（见解图 6）**\n\n同样以同心圆周为流线的两种经典平面涡流，有旋性截然不同：\n- **有旋强制涡（刚体旋转）**：$u_\\theta = \\omega_0 r$，则 $\\omega_z = \\frac{1}{2r}\\frac{\\mathrm{d}(\\omega_0 r^2)}{\\mathrm{d}r} = \\omega_0 \\neq 0$，流体微团随流线绕圆心转动的同时也绕自身轴线自转，属于有旋流，确实不存在流速势函数。\n- **无旋自由涡（点涡）**：$u_\\theta = \\frac{\\Gamma}{2\\pi r}$（$r > 0$），则：\n\n$$\n\\omega_z = \\frac{1}{2r}\\frac{\\mathrm{d}(r\\cdot u_\\theta)}{\\mathrm{d}r} = \\frac{1}{2r}\\frac{\\mathrm{d}}{\\mathrm{d}r}\\left(\\frac{\\Gamma}{2\\pi}\\right) = 0\n$$\n\n虽然其流线全是封闭同心圆，但流体微团在公转过程中自身方位角始终不变（犹如摩天轮座舱，只公转不自转），在除去原点奇点的区域内处处满足无旋条件，存在流速势函数 $\\varphi = \\frac{\\Gamma}{2\\pi}\\theta$（仅在复连通区域表现为多值函数，任一单连通子域内均单值光滑）。\n\n因此，仅凭“流线为封闭圆周线”便断言“一定不存在流速势函数”是错误的。",
                "analysisFigures": [
                    {"src": "figures/q06_sol.png", "caption": "解图 6　无旋自由点涡与有旋强制涡微团运动特征对比图"}
                ],
                "pitfalls": "1. 不要把“质点做圆周公转”与“微团自身旋转（有旋）”混为一谈！反之，质点沿平行直线运动（如平板间库埃特剪切流）也可以是有旋流动。\n2. 写出平面点涡 $u_\\theta = \\frac{\\Gamma}{2\\pi r}$、$\\varphi = \\frac{\\Gamma}{2\\pi}\\theta$ 的反例是本题拿满分的黄金采分点。",
                "chapter": 5,
                "kps": ["无旋流判别条件", "流速势函数", "自由涡与强制涡"],
                "method": "流函数拉普拉斯无旋判据与柯西—黎曼积分法",
                "difficulty": 2,
                "rubric": [
                    {"label": "明确判断该说法“不对（错误）”", "pts": 2},
                    {"label": "阐明势函数存在的充要条件是流体微团本身无自转（无旋 ω = 0），与流线是否为封闭圆周无必然联系", "pts": 3},
                    {"label": "举出无旋自由点涡（uθ = Γ/(2πr)，φ = (Γ/2π)θ，ωz = 0）反例加以严密论证", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2017-07",
                "year": 2017,
                "no": 7,
                "type": "calc",
                "score": 12,
                "title": "双液层封闭容器连水银测压计反求油面相对压强",
                "stem": "如图所示一封闭容器中盛有相对密度为 $0.8$ 的油，其深度 $h_1 = 0.3\\,\\mathrm{m}$；下面为水，深度 $h_2 = 0.5\\,\\mathrm{m}$。测压管中水银液面读数 $h = 0.4\\,\\mathrm{m}$，求封闭容器中的油表面压强 $p_0$。",
                "note": "",
                "figures": [
                    {"src": "figures/q07_orig.png", "caption": "题 7 图　油水双液层封闭容器与 U 形水银测压计"}
                ],
                "shortAnswer": "p0 = 46.06 kPa（取 g = 9.80 m/s²；取 g = 9.81 m/s² 为 46.11 kPa）。",
                "judgeAnswer": None,
                "answer": "封闭容器中油表面的相对压强 $p_0 = 46.06\\,\\mathrm{kPa}$（若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $p_0 \\approx 46.11\\,\\mathrm{kPa}$）。",
                "analysis": "**1. 确定等压面并列出静水压强平衡方程**\n\n已知油的密度 $\\rho_0 = 0.8\\rho = 800\\,\\mathrm{kg/m^3}$，水的密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$，水银密度 $\\rho_{\\mathrm{m}} = 13600\\,\\mathrm{kg/m^3}$；油层厚 $h_1 = 0.3\\,\\mathrm{m}$，水层（油水界面至 U 形管左侧水—水银交界面）高差 $h_2 = 0.5\\,\\mathrm{m}$，水银液面读数 $h = 0.4\\,\\mathrm{m}$。\n\n过 U 形管左侧水—水银分界面作水平等压面 $1\\text{—}1$（该水平面以下均为连通静止的同种水银，故左右两支管在 $1\\text{—}1$ 面上的静水压强严格相等）：\n- 左侧（经油层、水层向下递推）：$p_{\\text{左}} = p_0 + \\rho_0 g h_1 + \\rho g h_2$\n- 右侧（U 形管右端通大气，相对压强为 $0$）：$p_{\\text{右}} = \\rho_{\\mathrm{m}} g h$\n\n由 $p_{\\text{左}} = p_{\\text{右}}$ 得：\n\n$$\np_0 + \\rho_0 g h_1 + \\rho g h_2 = \\rho_{\\mathrm{m}} g h\n$$\n\n**2. 代入数值求解油面相对压强 $p_0$**\n\n取 $g = 9.80\\,\\mathrm{m/s^2}$：\n\n$$\np_0 = (\\rho_{\\mathrm{m}} h - \\rho h_2 - \\rho_0 h_1) g = (13600 \\times 0.4 - 1000 \\times 0.5 - 800 \\times 0.3) \\times 9.80\n$$\n\n$$\np_0 = (5440 - 500 - 240) \\times 9.80 = 4700 \\times 9.80 = 46060\\,\\mathrm{Pa} = 46.06\\,\\mathrm{kPa}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $p_0 = 4700 \\times 9.81 = 46107\\,\\mathrm{Pa} \\approx 46.11\\,\\mathrm{kPa}$。）",
                "analysisFigures": [],
                "pitfalls": "选取等压面 $1\\text{—}1$ 时必须同时满足**静止、连通、同种均质流体**三条件，因此应选在最下方的水—水银交界面处，而不能选在油—水交界面以上。",
                "chapter": 2,
                "kps": ["等压面原理", "多液层静水压强", "U形水银测压计"],
                "method": "等压面静水压强递推法",
                "difficulty": 1,
                "rubric": [
                    {"label": "正确选取左侧水—水银交界面为等压面并写出压强平衡方程 p0 + ρ0gh1 + ρgh2 = ρmgh", "pts": 6},
                    {"label": "准确代入相对密度与液柱高度算得 p0 = 46.06 kPa（或按 g=9.81 得 46.11 kPa，单位正确）", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2017-08",
                "year": 2017,
                "no": 8,
                "type": "calc",
                "score": 15,
                "title": "斜靠 60° 斜面圆柱挡水体静水总压力大小与方向计算",
                "stem": "一圆筒直径 $d = 2.0\\,\\mathrm{m}$，长度 $b = 4.0\\,\\mathrm{m}$，斜靠在与水平面成 $60^{\\circ}$ 的斜面上，如图所示。求圆筒所受到的静水总压力的大小及其方向。",
                "note": "",
                "figures": [
                    {"src": "figures/q08_orig.png", "caption": "题 8 图　斜靠 60° 斜面的圆柱形挡水圆筒"}
                ],
                "shortAnswer": "P = 97.51 kN（Px = 19.60 kN 向右，Pz = 95.52 kN 向上），与水平面夹角 θ = 78.40° 指向右上方且过圆心 O（取 g = 9.81 m/s² 时 P = 97.61 kN）。",
                "judgeAnswer": None,
                "answer": "圆筒所受静水总压力大小 $P \\approx 97.51\\,\\mathrm{kN}$（水平分力 $P_x = 19.60\\,\\mathrm{kN}$ 向右，铅垂分力 $P_z \\approx 95.52\\,\\mathrm{kN}$ 向上），方向与水平面成仰角 $\\theta \\approx 78.40^{\\circ}$ 指向右上方，作用线通过圆筒中心 $O$（若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $P_x = 19.62\\,\\mathrm{kN}$，$P_z = 95.62\\,\\mathrm{kN}$，$P = 97.61\\,\\mathrm{kN}$）。",
                "analysis": "**1. 分析几何关系与受压圆弧段（见解图 8）**\n\n圆筒直径 $d = 2.0\\,\\mathrm{m}$（半径 $R = 1.0\\,\\mathrm{m}$），轴向长度 $b = 4.0\\,\\mathrm{m}$。斜面与水平面倾角为 $60^{\\circ}$，圆筒与斜面相切于点 $B$，过切点 $B$ 的直径 $AB$ 垂直于斜面，故直径 $AB$ 与水平面夹角为 $30^{\\circ}$。由题图可知，自由液面恰与直径上端点 $A$ 齐平，整个受压浸水面为左下方的半圆弧 $ACB$。\n\n切点 $B$ 低于水面 $A$ 的竖直深度 $h_{AB}$ 及直径 $AB$ 的水平投影宽 $a$ 分别为：\n\n$$\nh_{AB} = d\\sin 30^{\\circ} = d\\cos 60^{\\circ} = 2.0 \\times 0.5 = 1.0\\,\\mathrm{m}\n$$\n\n$$\na = d\\cos 30^{\\circ} = d\\sin 60^{\\circ} = 2.0 \\times \\frac{\\sqrt{3}}{2} = \\sqrt{3}\\,\\mathrm{m} \\approx 1.7321\\,\\mathrm{m}\n$$\n\n**2. 计算水平分力 $P_x$**\n\n虽然半圆弧最底端浸深达 $1.5\\,\\mathrm{m}$，但切点 $B$ 高程以下（深度 $1.0\\sim 1.5\\,\\mathrm{m}$）左侧圆弧所受向右的水平压力与右侧圆弧所受向左的水平压力大小相等、方向相反、彼此抵消。因此，有效铅垂投影高度仅为 $A$、$B$ 间高差 $h_{AB} = 1.0\\,\\mathrm{m}$，水体在左、推动圆筒向右（取 $g = 9.80\\,\\mathrm{m/s^2}$）：\n\n$$\nP_x = \\frac{1}{2}\\rho g h_{AB}^2 b = 0.5 \\times 1000 \\times 9.80 \\times 1.0^2 \\times 4.0 = 19600\\,\\mathrm{N} = 19.60\\,\\mathrm{kN} \\quad (\\text{水平向右})\n$$\n\n**3. 用压力体法计算铅垂分力 $P_z$**\n\n封闭半圆弧 $ACB$ 与其倾斜直径 $AB$ 组成半圆柱，将虚实压力体合成后（或由闭合半圆弧阿基米德浮力定理叠加倾斜直径 $AB$ 上方直角三角形水柱重），总铅垂有效压力体全部为**虚压力体（方向竖直向上）**，其横截面积由两部分组成：\n- 倾斜直径 $AB$ 下方的半圆面积：$A_{\\text{半圆}} = \\frac{1}{8}\\pi d^2 = \\frac{\\pi}{2} \\approx 1.5708\\,\\mathrm{m^2}$；\n- 倾斜直径 $AB$ 上方至自由液面的直角三角形面积：$A_{\\Delta} = \\frac{1}{2} h_{AB} a = \\frac{1}{2} \\times 1.0 \\times \\sqrt{3} \\approx 0.8660\\,\\mathrm{m^2}$。\n\n因此铅垂总压力体体积与铅垂分力为：\n\n$$\nV_z = (A_{\\text{半圆}} + A_{\\Delta}) b = \\left(\\frac{\\pi}{2} + \\frac{\\sqrt{3}}{2}\\right) \\times 4.0 = 2(\\pi + \\sqrt{3}) \\approx 9.7473\\,\\mathrm{m^3}\n$$\n\n$$\nP_z = \\rho g V_z = 1000 \\times 9.80 \\times 9.7473 \\approx 95523\\,\\mathrm{N} \\approx 95.52\\,\\mathrm{kN} \\quad (\\text{竖直向上})\n$$\n\n**4. 合成静水总压力 $P$ 与方向**\n\n$$\nP = \\sqrt{P_x^2 + P_z^2} = \\sqrt{19.60^2 + 95.523^2} \\approx 97.51\\,\\mathrm{kN}\n$$\n\n$$\n\\theta = \\arctan\\frac{P_z}{P_x} = \\arctan\\frac{95.523}{19.60} \\approx 78.40^{\\circ}\n$$\n\n由于圆柱面上每一点静水压强均沿径向指向圆心，故静水总压力的作用线**必通过圆筒中心 $O$**，方向与水平面成 $78.40^{\\circ}$ 指向右上方。（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，算得 $P_x = 19.62\\,\\mathrm{kN}$、$P_z = 95.62\\,\\mathrm{kN}$、$P = 97.61\\,\\mathrm{kN}$，方向角 $\\theta = 78.40^{\\circ}$ 不变。）",
                "analysisFigures": [
                    {"src": "figures/q08_sol.png", "caption": "解图 8　斜靠 60° 斜面圆柱体水平投影抵消与铅垂虚压力体合成图"}
                ],
                "pitfalls": "1. 水平投影高度切勿误算成圆筒最底端深度 $1.5\\,\\mathrm{m}$！切点 $B$ 以下左右对称弧段的水平压力已相互抵消，净有效投影高度仅为 $h_{AB} = d\\cos 60^{\\circ} = 1.0\\,\\mathrm{m}$。\n2. 铅垂压力体千万不要漏算倾斜直径 $AB$ 上方的直角三角形 $\\frac{1}{2} h_{AB} a$，也不要忘了说明合力作用线**过圆心 $O$**。",
                "chapter": 2,
                "kps": ["圆柱曲面静水总压力", "压力体图与虚压力体", "合力方向过圆心"],
                "method": "等效自由液面+水平投影与铅垂压力体合成法",
                "difficulty": 3,
                "rubric": [
                    {"label": "由斜面倾角 60° 求出端点高差 hAB = d·cos60° = 1.0 m 及水平宽 a = d·sin60° = √3 m", "pts": 3},
                    {"label": "正确消去底端对称水平压力，求出净水平分力 Px = 19.60 kN（向右）", "pts": 4},
                    {"label": "将铅垂压力体分解为半圆加直角三角形，求得铅垂分力 Pz ≈ 95.52 kN（向上）", "pts": 5},
                    {"label": "合成总压力 P ≈ 97.51 kN，给出仰角 θ = 78.40°（右上方）并指明作用线通过圆心 O", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2017-09",
                "year": 2017,
                "no": 9,
                "type": "calc",
                "score": 10,
                "title": "毕托管配水银压差计测量输水管管轴流速与总流量计算",
                "stem": "利用毕托管原理测量输水管中的流量（见图示）。已知输水管直径 $d$ 为 $200\\,\\mathrm{mm}$，测得水银差压计读数 $h_p$ 为 $60\\,\\mathrm{mm}$，若此时断面平均流速 $v = 0.84 u$，式中 $u$ 是毕托管前管轴上未受扰动水流的流速。问输水管中的流量 $Q$ 多大？",
                "note": "",
                "figures": [
                    {"src": "figures/q09_orig.png", "caption": "题 9 图　毕托管与 U 形水银差压计测流装置"}
                ],
                "shortAnswer": "Q ≈ 0.1016 m³/s（101.6 L/s；取 g = 9.81 m/s² 亦为 0.1016 m³/s）。",
                "judgeAnswer": None,
                "answer": "输水管中的流量 $Q \\approx 0.1016\\,\\mathrm{m^3/s}$（即 $101.6\\,\\mathrm{L/s}$，保留三位有效数字为 $0.102\\,\\mathrm{m^3/s}$）。",
                "analysis": "**1. 列毕托管驻点流线能量方程与水银差压计等压面方程**\n\n设毕托管上游管轴未受扰动处为点 $1$（静压强 $p_1$，流速 $u$），毕托管迎流口滞止驻点为点 $2$（总压强 $p_2$，流速 $u_2 = 0$）。两测点位于同一水平管轴线上（$z_1 = z_2$），不计局部损失，列点 $1$ 至点 $2$ 的微小流束伯努利方程：\n\n$$\n\\frac{p_1}{\\rho g} + \\frac{u^2}{2g} = \\frac{p_2}{\\rho g} \\implies \\frac{u^2}{2g} = \\frac{p_2 - p_1}{\\rho g}\n$$\n\n由 U 形水银压差计两侧支管（左支管接管壁静压 $p_1$，右支管接毕托管总压 $p_2$）在水银下交界面处列等压面方程：\n\n$$\np_1 + \\rho_{\\mathrm{m}} g h_p = p_2 + \\rho g h_p \\implies \\frac{p_2 - p_1}{\\rho g} = \\frac{\\rho_{\\mathrm{m}} - \\rho}{\\rho} h_p = 12.6\\,h_p\n$$\n\n**2. 计算管轴流速 $u$、断面平均流速 $v$ 与流量 $Q$**\n\n已知 $h_p = 60\\,\\mathrm{mm} = 0.06\\,\\mathrm{m}$，$d = 200\\,\\mathrm{mm} = 0.20\\,\\mathrm{m}$，取 $g = 9.80\\,\\mathrm{m/s^2}$：\n\n$$\nu = \\sqrt{2g \\times 12.6\\,h_p} = \\sqrt{2 \\times 9.80 \\times 12.6 \\times 0.06} = \\sqrt{14.8176} \\approx 3.8494\\,\\mathrm{m/s}\n$$\n\n断面平均流速 $v$ 与管道流量 $Q$ 为：\n\n$$\nv = 0.84\\,u = 0.84 \\times 3.8494 \\approx 3.2335\\,\\mathrm{m/s}\n$$\n\n$$\nQ = v \\cdot \\frac{\\pi}{4} d^2 = 3.2335 \\times \\frac{\\pi}{4} \\times 0.20^2 \\approx 0.10158\\,\\mathrm{m^3/s} \\approx 0.102\\,\\mathrm{m^3/s}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，算得 $u = 3.8513\\,\\mathrm{m/s}$，$v = 3.2351\\,\\mathrm{m/s}$，$Q = 0.10163\\,\\mathrm{m^3/s} \\approx 0.102\\,\\mathrm{m^3/s}$。）",
                "analysisFigures": [],
                "pitfalls": "1. 水银差压计两管内水银上方均为**水**而非空气，故压强水头差系数为 $\\frac{\\rho_{\\mathrm{m}} - \\rho}{\\rho} = 12.6$，切勿误用 $13.6$！\n2. 毕托管测出的是管轴点流速 $u$，求流量 $Q$ 前必须乘以题目给定的换算系数 $0.84$ 得到断面平均流速 $v$。",
                "chapter": 3,
                "kps": ["毕托管测速原理", "U形水银压差计", "恒定流能量方程"],
                "method": "驻点滞止增压与总静压差测点速法",
                "difficulty": 2,
                "rubric": [
                    {"label": "由毕托管驻点能量方程与水银差压计等压面方程导出 u = √(2g·12.6·hp) ≈ 3.85 m/s", "pts": 5},
                    {"label": "换算断面平均流速 v = 0.84u ≈ 3.23 m/s，求得输水管流量 Q ≈ 0.102 m³/s（单位正确）", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2017-10",
                "year": 2017,
                "no": 10,
                "type": "calc",
                "score": 15,
                "title": "喷射抽水装置喉道负压起动临界断面面积比条件推导",
                "stem": "如图所示为利用喷射水流，在喉道上 $1\\text{—}1$ 断面造成负压，而将容器 $M$ 中的水抽出的装置。已知 $H$、$b$、$h$ 值，当不计水头损失时，取动能校正系数 $\\alpha = 1.0$，问喉道断面面积 $A_1$ 与喷嘴出口断面面积 $A_2$ 的比值应满足什么条件才能使抽水装置开始工作？",
                "note": "",
                "figures": [
                    {"src": "figures/q10_orig.png", "caption": "题 10 图　利用喷射水流在喉道形成负压的抽水装置"}
                ],
                "shortAnswer": "A1 / A2 < √(H / (h + b))（临界起动条件为 A1 / A2 ≤ √(H / (h + b))）。",
                "judgeAnswer": None,
                "answer": "喉道断面面积 $A_1$ 与喷嘴出口断面面积 $A_2$ 的比值应满足：\n\n$$\n\\frac{A_1}{A_2} < \\sqrt{\\frac{H}{h + b}} \\quad \\left(\\text{临界起动条件：}\\frac{A_1}{A_2} \\le \\sqrt{\\frac{H}{h + b}}\\right)\n$$",
                "analysis": "**1. 建立抽水装置起动的喉道负压条件（见解图 10）**\n\n要将下方敞口容器 $M$（自由液面处相对压强为 $0$）中的水沿吸水管向上抽吸高度 $b$ 进入喉道断面 $1\\text{—}1$，喉道内的静水（动水）相对压强 $p_1$ 必须达到足以克服水柱高度 $b$ 的真空度，即：\n\n$$\np_1 + \\rho g b \\le 0 \\implies \\frac{p_1}{\\rho g} \\le -b\n$$\n\n（严格开始抽水时取“$<$”，临界液面恰抵喉道时取“$=$”。）\n\n**2. 列上游水箱液面至喷嘴出口 $2\\text{—}2$ 的能量方程**\n\n以喷嘴中心水平面 $0\\text{—}0$ 为基准面（$z_2 = 0$，喷嘴自由射入大气 $p_2 = 0$；水箱自由液面 $z_0 = H$，$p_0 = 0$，$v_0 \\approx 0$），不计水头损失且 $\\alpha = 1.0$：\n\n$$\nH + 0 + 0 = 0 + 0 + \\frac{v_2^2}{2g} \\implies v_2 = \\sqrt{2gH}\n$$\n\n**3. 列上游水箱液面至喉道断面 $1\\text{—}1$ 的能量方程**\n\n喉道 $1\\text{—}1$ 位于水箱液面以下 $h$ 处，故其高程 $z_1 = H - h$。列水箱液面与 $1\\text{—}1$ 断面的能量方程：\n\n$$\nH = (H - h) + \\frac{p_1}{\\rho g} + \\frac{v_1^2}{2g} \\implies \\frac{p_1}{\\rho g} = h - \\frac{v_1^2}{2g}\n$$\n\n将此式代入起动负压判据 $\\frac{p_1}{\\rho g} \\le -b$：\n\n$$\nh - \\frac{v_1^2}{2g} \\le -b \\implies \\frac{v_1^2}{2g} \\ge h + b \\implies v_1 \\ge \\sqrt{2g(h + b)}\n$$\n\n**4. 联立连续性方程求面积比 $A_1 / A_2$ 条件**\n\n在抽水刚刚起动瞬间，容器 $M$ 尚未形成流入流量（$Q_M = 0$），故喉道与喷嘴流量相等：$Q_1 = Q_2 \\implies A_1 v_1 = A_2 v_2$，于是：\n\n$$\n\\frac{A_1}{A_2} = \\frac{v_2}{v_1} \\le \\frac{\\sqrt{2gH}}{\\sqrt{2g(h + b)}} = \\sqrt{\\frac{H}{h + b}}\n$$\n\n即必须使喉道充分收缩，满足 $\\frac{A_1}{A_2} < \\sqrt{\\frac{H}{h + b}}$（临界值 $\\frac{A_1}{A_2} \\le \\sqrt{\\frac{H}{h + b}}$），才能在喉道产生足够大的流速与真空度将容器 $M$ 中的水抽出。",
                "analysisFigures": [
                    {"src": "figures/q10_sol.png", "caption": "解图 10　喷射抽水装置喉道负压形成机理与能量转换关系图"}
                ],
                "pitfalls": "本题极易在移项变号时把不等号方向写反成 $\\frac{A_1}{A_2} \\ge \\sqrt{\\frac{H}{h+b}}$！请用物理直觉秒验：喉道越**细**（$A_1 / A_2$ 越**小**），喉道流速 $v_1$ 越**大**，压强越**低**、真空度越**大**，越容易抽水，因此必然是 $A_1/A_2$ **小于**临界值！",
                "chapter": 3,
                "kps": ["文丘里负压抽吸原理", "恒定总流能量方程", "连续性方程"],
                "method": "多断面伯努利方程与连续性方程联立求解法",
                "difficulty": 3,
                "rubric": [
                    {"label": "写出容器 M 抽水起动的喉道真空压强判据 p1/(ρg) ≤ -b", "pts": 4},
                    {"label": "列能量方程分别求得喷嘴出口流速 v2 = √(2gH) 及喉道压强关系 p1/(ρg) = h - v1²/(2g)", "pts": 5},
                    {"label": "代入负压判据正确推出 v1 ≥ √(2g(h+b))，联立连续性方程得出 A1/A2 ≤ √(H/(h+b))（不等号方向正确）", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2017-11",
                "year": 2017,
                "no": 11,
                "type": "calc",
                "score": 15,
                "title": "孔口水平射流冲击平板封堵管嘴的动量与静水压力平衡计算",
                "stem": "如图所示，水由水箱 $1$ 经孔口水平射出冲击到一平板上，使平板能封盖住另一水箱 $2$ 的管嘴。孔口与管嘴中心重合，而且 $d_1 = 0.5 d_2$。不计水头损失，不计平板自重。当已知水箱 $1$ 中水深为 $h_1$ 时，求水箱 $2$ 中水深 $h_2$ 为多大时才能将管嘴封住。",
                "note": "",
                "figures": [
                    {"src": "figures/q11_orig.png", "caption": "题 11 图　孔口射流冲击平板封堵水箱 2 管嘴装置"}
                ],
                "shortAnswer": "h2 ≤ 0.5 h1（最大允许水深 h2,max = 0.5 h1）。",
                "judgeAnswer": None,
                "answer": "当水箱 $2$ 中水深满足 $h_2 \\le 0.5 h_1$（即最大封堵水深 $h_{2,\\max} = 0.5 h_1$）时，平板才能将管嘴封住。",
                "analysis": "**1. 求水箱 1 孔口水平射流的流速 $v_1$ 与流量 $Q$（见解图 11）**\n\n以孔口中心轴线为基准面，列水箱 $1$ 自由液面 $1\\text{—}1$ 至孔口射流断面 $2\\text{—}2$（自由出流 $p = 0$，不计水头损失且 $\\alpha = 1.0$）的能量方程：\n\n$$\nh_1 + 0 + 0 = 0 + 0 + \\frac{v_1^2}{2g} \\implies v_1 = \\sqrt{2g h_1}\n$$\n\n射流过水断面面积 $A_1 = \\frac{\\pi}{4} d_1^2$，流量 $Q = v_1 A_1 = \\frac{\\pi}{4} d_1^2 \\sqrt{2g h_1}$。\n\n**2. 用动量方程求水平射流对平板的冲击力 $F_1$**\n\n取射流撞击平板转向区为控制体（以水平向右为 $+x$ 方向）。自由射流四周均受大气压（相对压强为 $0$），射入控制体的水平速度 $v_{\\mathrm{in},x} = v_1$，撞击铅直平板后沿板面垂直折转向上下四周流出，故流出水平速度分量 $v_{\\mathrm{out},x} = 0$。\n\n设平板对控制体水流的水平反力 $R_x$ 水平向左，列 $x$ 向恒定总流动量方程（取 $\\beta = 1.0$）：\n\n$$\n-R_x = \\rho Q (0 - v_1) \\implies R_x = \\rho Q v_1 = \\rho A_1 v_1^2 = \\rho \\left(\\frac{\\pi}{4} d_1^2\\right) (2g h_1) = \\frac{\\pi}{2} \\rho g h_1 d_1^2\n$$\n\n由牛顿第三定律，射流对平板向右的水平冲击力为：\n\n$$\nF_1 = R_x = \\frac{\\pi}{2} \\rho g h_1 d_1^2 \\quad (\\text{水平向右})\n$$\n\n**3. 计算水箱 2 管嘴内静水对平板的总压力 $P_2$ 并列平衡条件**\n\n平板封住管嘴时，管嘴内水体静止，管嘴圆断面（直径 $d_2$，面积 $A_2 = \\frac{\\pi}{4} d_2^2$）形心淹深为 $h_2$，故水箱 $2$ 水体对平板向左的静水总压力为：\n\n$$\nP_2 = \\rho g h_2 A_2 = \\frac{\\pi}{4} \\rho g h_2 d_2^2 \\quad (\\text{水平向左})\n$$\n\n要使平板紧密压住管嘴而不被水箱 $2$ 顶开，必须满足 $F_1 \\ge P_2$：\n\n$$\n\\frac{\\pi}{2} \\rho g h_1 d_1^2 \\ge \\frac{\\pi}{4} \\rho g h_2 d_2^2 \\implies h_2 \\le 2\\left(\\frac{d_1}{d_2}\\right)^2 h_1\n$$\n\n代入已知 $d_1 = 0.5 d_2$（即 $\\frac{d_1}{d_2} = \\frac{1}{2}$）：\n\n$$\nh_2 \\le 2 \\times (0.5)^2 h_1 = 0.5\\,h_1\n$$",
                "analysisFigures": [
                    {"src": "figures/q11_sol.png", "caption": "解图 11　水平射流冲击平板与水箱 2 管嘴静水压力平衡分析图"}
                ],
                "pitfalls": "1. 射流冲击平板产生的动水推力为 $F_1 = \\rho Q v_1 = 2 \\rho g h_1 A_1$，是同面积静水压力 $\\rho g h_1 A_1$ 的 **2 倍**！切勿漏掉系数 $2$。\n2. 最终结果应表述为范围 $h_2 \\le 0.5 h_1$（临界最大值 $0.5 h_1$）。",
                "chapter": 3,
                "kps": ["托里拆利公式", "射流冲击平板动量方程", "平面静水总压力"],
                "method": "能量方程求流量+控制体动量方程求反力",
                "difficulty": 2,
                "rubric": [
                    {"label": "由水箱 1 能量方程求出孔口射流流速 v1 = √(2gh1) 及流量 Q = A1·v1", "pts": 4},
                    {"label": "取射流撞击平板控制体列水平动量方程，求出射流对平板向右的冲击力 F1 = (π/2)ρgh1d1²", "pts": 6},
                    {"label": "求出水箱 2 管嘴静水总压力 P2 = (π/4)ρgh2d2²，由 F1 ≥ P2 解得 h2 ≤ 0.5h1", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2017-12",
                "year": 2017,
                "no": 12,
                "type": "calc",
                "score": 15,
                "title": "密闭加压容器经含多弯头阀门短管向高位水池输水流量计算",
                "stem": "水从封闭容器 $A$ 经直径 $d = 25\\,\\mathrm{mm}$，长度 $l = 10\\,\\mathrm{m}$ 管道流入容器 $B$。容器 $A$ 水面上的相对压强 $p_1$ 为 $2$ 个大气压，$H_1 = 1\\,\\mathrm{m}$，$H_2 = 5\\,\\mathrm{m}$，局部阻力系数 $\\zeta_{\\text{进口}} = 0.5$，$\\zeta_{\\text{阀}} = 4.0$，$\\zeta_{\\text{弯}} = 0.3$，沿程阻力系数 $\\lambda = 0.025$，求通过的流量 $Q$。",
                "note": "",
                "figures": [
                    {"src": "figures/q12_orig.png", "caption": "题 12 图　密闭加压容器 A 经短管向高位水池 B 输水系统"}
                ],
                "shortAnswer": "Q ≈ 2.15 × 10⁻³ m³/s（2.15 L/s，按工程大气压 1 at = 10 m 水柱计；按标准大气压 101.325 kPa 计为 2.19 × 10⁻³ m³/s）。",
                "judgeAnswer": None,
                "answer": "管道通过的流量 $Q \\approx 2.15 \\times 10^{-3}\\,\\mathrm{m^3/s}$（即 $2.15\\,\\mathrm{L/s}$，按工程大气压 $1\\,\\mathrm{at} = 98.0\\,\\mathrm{kPa}$ 即 $10\\,\\mathrm{m}$ 水柱计；若按标准大气压 $1\\,\\mathrm{atm} = 101.325\\,\\mathrm{kPa}$ 计，则 $Q \\approx 2.19 \\times 10^{-3}\\,\\mathrm{m^3/s}$）。",
                "analysis": "**1. 识别全部沿程与局部水头损失项**\n\n观察题 12 图，管道从容器 $A$ 出发，依次经过：进口（$\\zeta_{\\text{进口}} = 0.5$）、阀门（$\\zeta_{\\text{阀}} = 4.0$）、**3 个 $90^{\\circ}$ 弯头**（$3\\zeta_{\\text{弯}} = 3 \\times 0.3 = 0.9$）以及**淹没流入水池 $B$ 的出口**（$\\zeta_{\\text{出口}} = 1.0$）。\n\n已知 $d = 25\\,\\mathrm{mm} = 0.025\\,\\mathrm{m}$，$l = 10\\,\\mathrm{m}$，$\\lambda = 0.025$，全管总阻力系数为：\n\n$$\n\\sum\\xi = \\lambda\\frac{l}{d} + \\zeta_{\\text{进口}} + \\zeta_{\\text{阀}} + 3\\zeta_{\\text{弯}} + \\zeta_{\\text{出口}} = 0.025 \\times \\frac{10}{0.025} + 0.5 + 4.0 + 3 \\times 0.3 + 1.0 = 10.0 + 6.4 = 16.4\n$$\n\n**2. 列容器 $A$ 液面至水池 $B$ 液面的总流能量方程**\n\n以地面为基准面（$z_A = H_1 = 1\\,\\mathrm{m}$，$z_B = H_2 = 5\\,\\mathrm{m}$；两容器液面流速 $v_A \\approx 0,\\; v_B \\approx 0$；水池 $B$ 敞口，$p_B = 0$）。容器 $A$ 水面相对压强 $p_1$ 为 $2$ 个工程大气压（$1\\,\\mathrm{at} = 10\\,\\mathrm{m}$ 水柱，即 $\\frac{p_1}{\\rho g} = 20\\,\\mathrm{m}$）：\n\n$$\nH_1 + \\frac{p_1}{\\rho g} = H_2 + \\left(\\sum\\xi\\right)\\frac{v^2}{2g}\n$$\n\n代入数值：\n\n$$\n1 + 20 = 5 + 16.4\\,\\frac{v^2}{2g} \\implies 16.4\\,\\frac{v^2}{2g} = 16.0\n$$\n\n**3. 计算管内流速 $v$ 与输水流量 $Q$**\n\n取 $g = 9.80\\,\\mathrm{m/s^2}$：\n\n$$\nv = \\sqrt{\\frac{2 \\times 9.80 \\times 16.0}{16.4}} \\approx 4.3729\\,\\mathrm{m/s}\n$$\n\n$$\nQ = v \\cdot \\frac{\\pi}{4} d^2 = 4.3729 \\times \\frac{\\pi}{4} \\times 0.025^2 \\approx 2.1465 \\times 10^{-3}\\,\\mathrm{m^3/s} \\approx 2.15 \\times 10^{-3}\\,\\mathrm{m^3/s}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，仍按工程大气压 $20\\,\\mathrm{m}$ 水柱算得 $v = 4.3751\\,\\mathrm{m/s}$、$Q = 2.148 \\times 10^{-3}\\,\\mathrm{m^3/s} \\approx 2.15 \\times 10^{-3}\\,\\mathrm{m^3/s}$；若按标准物理大气压 $1\\,\\mathrm{atm} = 101.325\\,\\mathrm{kPa}$ 折算，则 $\\frac{p_1}{\\rho g} = 20.679\\,\\mathrm{m}$，$\\Delta H = 16.679\\,\\mathrm{m}$，算得 $v = 4.465\\,\\mathrm{m/s}$、$Q = 2.19 \\times 10^{-3}\\,\\mathrm{m^3/s}$。）",
                "analysisFigures": [],
                "pitfalls": "1. 一定要仔细数图中的弯头个数——管道由水平转竖直向上、再转水平、再转竖直向下，共 **3 个弯头**（$3 \\times 0.3 = 0.9$），切勿漏数！\n2. 管道末端淹没插入水池 $B$ 中，题目未显式列出 $\\zeta_{\\text{出口}}$，但必须自行计入淹没出口局部阻力系数 $\\zeta_{\\text{出口}} = 1.0$。",
                "chapter": 6,
                "kps": ["简单短管淹没出流", "沿程与局部水头损失", "恒定总流能量方程"],
                "method": "两水池淹没短管能量方程与分段测压管水头法",
                "difficulty": 2,
                "rubric": [
                    {"label": "完整计入沿程阻力 10.0 及进口 0.5、阀门 4.0、3 个弯头 0.9、淹没出口 1.0，得出总阻力系数 16.4", "pts": 6},
                    {"label": "列 A—B 液面总流能量方程，正确换算 2 个大气压水头并求得流速 v ≈ 4.37 m/s", "pts": 5},
                    {"label": "代入管径 d = 0.025 m 准确算得流量 Q ≈ 2.15 × 10⁻³ m³/s（按标准大气压 2.19 × 10⁻³ m³/s 亦给满分）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2017-13",
                "year": 2017,
                "no": 13,
                "type": "calc",
                "score": 10,
                "title": "矩形混凝土明渠均匀流底坡与上下端水面落差计算",
                "stem": "一矩形混凝土渠，长为 $200\\,\\mathrm{m}$，按均匀流设计，渠道底宽 $b = 2\\,\\mathrm{m}$，水深 $h = 1\\,\\mathrm{m}$，流量 $Q = 5.25\\,\\mathrm{m^3/s}$，粗糙系数 $n = 0.015$，求渠道上下端水面落差？",
                "note": "",
                "figures": [],
                "shortAnswer": "底坡 i ≈ 0.00391，上下端水面落差 Δh ≈ 0.781 m。",
                "judgeAnswer": None,
                "answer": "渠道上下端水面落差 $\\Delta h \\approx 0.781\\,\\mathrm{m}$（若中间取 $C = 59.39$ 截位约得 $0.782\\,\\mathrm{m}$）。",
                "analysis": "**1. 计算矩形明渠断面几何与水力要素**\n\n已知底宽 $b = 2\\,\\mathrm{m}$，均匀流水深 $h = 1\\,\\mathrm{m}$：\n- 过水断面面积：$A = b h = 2 \\times 1 = 2.0\\,\\mathrm{m^2}$\n- 湿周（不含自由水面）：$\\chi = b + 2h = 2 + 2 \\times 1 = 4.0\\,\\mathrm{m}$\n- 水力半径：$R = \\frac{A}{\\chi} = \\frac{2.0}{4.0} = 0.50\\,\\mathrm{m}$\n\n**2. 应用谢才—曼宁公式反求渠道底坡 $i$**\n\n粗糙系数 $n = 0.015$，谢才系数 $C$ 为：\n\n$$\nC = \\frac{1}{n} R^{1/6} = \\frac{1}{0.015} \\times 0.50^{1/6} \\approx 59.3933\\,\\mathrm{m^{1/2}/s}\n$$\n\n由明渠均匀流流量公式 $Q = A C \\sqrt{R i}$ 反解底坡 $i$：\n\n$$\ni = \\frac{Q^2}{A^2 C^2 R} = \\frac{5.25^2}{2.0^2 \\times 59.3933^2 \\times 0.50} = \\frac{27.5625}{7055.12} \\approx 3.9067 \\times 10^{-3}\n$$\n\n**3. 计算渠道上下端水面落差 $\\Delta h$**\n\n明渠均匀流的水面线与渠底线互相平行，水面坡度等于渠道底坡 $i$，已知渠长 $L = 200\\,\\mathrm{m}$，故上下端水面落差为：\n\n$$\n\\Delta h = i L = 3.9067 \\times 10^{-3} \\times 200 \\approx 0.7813\\,\\mathrm{m} \\approx 0.781\\,\\mathrm{m}\n$$",
                "analysisFigures": [],
                "pitfalls": "明渠均匀流的水面坡度 $J_w$、总水头坡度 $J$ 与渠道底坡 $i$ 三者相等，故上下端水面落差 $\\Delta h = i L$；此外注意矩形明渠湿周为 $b + 2h = 4\\,\\mathrm{m}$，而非 $2(b + h)$。",
                "chapter": 7,
                "kps": ["矩形明渠水力要素", "谢才-曼宁公式", "明渠均匀流特征"],
                "method": "明渠均匀流曼宁公式求底坡与高程法",
                "difficulty": 1,
                "rubric": [
                    {"label": "计算过水面积 A = 2 m²、湿周 χ = 4 m 及水力半径 R = 0.5 m", "pts": 3},
                    {"label": "由曼宁公式求得谢才系数 C ≈ 59.39 m^(1/2)/s 及底坡 i ≈ 3.91 × 10⁻³", "pts": 4},
                    {"label": "由均匀流水面平行于渠底得上下端水面落差 Δh = iL ≈ 0.781 m", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2017-14",
                "year": 2017,
                "no": 14,
                "type": "calc",
                "score": 10,
                "title": "由平面驻点势流流速势函数求速度分量与流线方程",
                "stem": "已知某流场的流速势为 $\\varphi = \\frac{a}{2}(x^2 - y^2)$，式中 $a$ 为常数，试求（1）$u_x$ 及 $u_y$；（2）流线方程。",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）ux = ax，uy = -ay；（2）流线方程 xy = C（双曲线簇）。",
                "judgeAnswer": None,
                "answer": "（1）流速分量为 $u_x = ax$，$u_y = -ay$；\n\n（2）流线方程为 $xy = C$（$C$ 为任意常数，等轴双曲线簇）。",
                "analysis": "**（1）由流速势函数求流速分量 $u_x$ 及 $u_y$**\n\n根据流速势函数的定义（正梯度约定 $\\vec{u} = \\nabla \\varphi$）：\n\n$$\nu_x = \\frac{\\partial \\varphi}{\\partial x} = \\frac{\\partial}{\\partial x}\\left[\\frac{a}{2}(x^2 - y^2)\\right] = ax\n$$\n\n$$\nu_y = \\frac{\\partial \\varphi}{\\partial y} = \\frac{\\partial}{\\partial y}\\left[\\frac{a}{2}(x^2 - y^2)\\right] = -ay\n$$\n\n（检验连续性方程 $\\frac{\\partial u_x}{\\partial x} + \\frac{\\partial u_y}{\\partial y} = a - a = 0$，满足不可压缩平面势流拉普拉斯方程 $\\nabla^2 \\varphi = 0$。）\n\n**（2）求流线方程（见解图 14）**\n\n将 $u_x = ax$、$u_y = -ay$ 代入平面流线微分方程 $\\frac{\\mathrm{d}x}{u_x} = \\frac{\\mathrm{d}y}{u_y}$：\n\n$$\n\\frac{\\mathrm{d}x}{ax} = \\frac{\\mathrm{d}y}{-ay} \\implies \\frac{\\mathrm{d}x}{x} + \\frac{\\mathrm{d}y}{y} = 0\n$$\n\n两边积分得：\n\n$$\n\\ln|x| + \\ln|y| = \\ln|C| \\implies xy = C \\quad (C\\text{ 为任意常数})\n$$\n\n（亦可由柯西—黎曼条件 $\\frac{\\partial \\psi}{\\partial y} = u_x = ax$、$-\\frac{\\partial \\psi}{\\partial x} = u_y = -ay$ 积出流函数 $\\psi = axy$，令 $\\psi = \\text{const}$ 同样得流线方程 $xy = C$；若个别教材采用负梯度定义 $\\vec{u} = -\\nabla \\varphi$，则 $u_x = -ax,\\; u_y = ay$，流线方程仍为 $xy = C$。）",
                "analysisFigures": [
                    {"src": "figures/q14_sol.png", "caption": "解图 14　平面驻点势流等轴双曲线流线簇与正交等势线网图"}
                ],
                "pitfalls": "积分 $\\frac{\\mathrm{d}x}{x} = -\\frac{\\mathrm{d}y}{y}$ 时注意把积分常数写作 $\\ln|C|$ 便于整理成标准代数形式 $xy = C$，切勿漏掉任意常数 $C$。",
                "chapter": 5,
                "kps": ["流速势函数", "流线微分方程", "平面驻点势流"],
                "method": "势函数偏导求流速与柯西—黎曼全微分求流函数法",
                "difficulty": 1,
                "rubric": [
                    {"label": "正确对势函数求偏导得到流速分量 ux = ax，uy = -ay", "pts": 4},
                    {"label": "代入流线微分方程 dx/ux = dy/uy 分离变量积分，准确求得流线方程 xy = C", "pts": 6}
                ]
            }
        ]
    }


# ==============================================================================
# 2016 Exam Paper Builder (15 Questions, 64 + 86 = 150 pts)
# ==============================================================================

def build_2016_paper() -> dict:
    return {
        "year": 2016,
        "code": "849",
        "subject": "水力学（水）",
        "school": "扬州大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": True,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "全卷共 15 道题：一、简答题（第 1～8 题，8×8=64 分）；二、计算题（第 9～15 题，12+15+12+15+12+10+10=86 分）。",
            "除特别说明外，主解统一取重力加速度 $g = 9.80\\,\\mathrm{m/s^2}$（并附注 $g = 9.81\\,\\mathrm{m/s^2}$ 对照值），水的密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$，水银密度 $\\rho_{\\mathrm{m}} = 13600\\,\\mathrm{kg/m^3}$。"
        ],
        "sections": [
            {
                "id": "short",
                "title": "一、简答题",
                "description": "本大题共 8 小题，每小题 8 分，共 64 分。",
                "range": [1, 8],
                "scorePerQuestion": 8,
                "totalScore": 64
            },
            {
                "id": "calc",
                "title": "二、计算题",
                "description": "本大题共 7 小题（12+15+12+15+12+10+10 分），共 86 分。",
                "range": [9, 15],
                "totalScore": 86
            }
        ],
        "questions": [
            {
                "id": "yzu-849-2016-01",
                "year": 2016,
                "no": 1,
                "type": "short",
                "score": 8,
                "title": "液体黏性内摩擦力与固体间外摩擦力的本质区别",
                "stem": "液体的粘性引起的内摩擦力与固体间的摩擦力有何区别？",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）产生条件：液体静止无内摩擦力，仅在存在相对运动（du/dy≠0）时产生；固体静止时可有静摩擦力。（2）影响因素：液体内摩擦力 T = μA(du/dy) 与接触面积、速度梯度及黏度成正比，与正压力无关；固体摩擦力 F = fN 与正压力成正比，与接触面积及滑动速度大小基本无关。（3）发生部位：液体内摩擦发生在液流内部任意相对运动的相邻液层间，固体摩擦仅发生在固体接触表面。",
                "judgeAnswer": None,
                "answer": "液体黏性内摩擦力（遵循牛顿内摩擦定律 $T = \\mu A\\frac{\\mathrm{d}u}{\\mathrm{d}y}$）与固体间外摩擦力（遵循库仑摩擦定律 $F = f N$）主要有以下四点区别：\n\n1. **产生条件不同**：液体处于静止或作刚体式均匀平移/旋转（$\\frac{\\mathrm{d}u}{\\mathrm{d}y} = 0$）时不存在内摩擦力，液体无静摩擦力；固体间在相对静止但有运动趋势时即可存在静摩擦力。\n2. **与正压力及接触面积的关系不同**：液体内摩擦力大小与接触面积 $A$ 成正比，与作用面上的正压力（压强）无关；固体摩擦力大小与法向正压力 $N$ 成正比，与宏观接触面积无关。\n3. **与速度的关系不同**：液体内摩擦力与流速梯度（剪切变形速率）$\\frac{\\mathrm{d}u}{\\mathrm{d}y}$ 及流体黏度 $\\mu$ 成正比；固体滑动摩擦力与相对滑动速度大小基本无关，只取决于表面粗糙材质（摩擦系数 $f$）。\n4. **发生部位不同**：液体内摩擦力发生于液流内部所有存在相对运动的相邻液层之间；固体外摩擦力仅发生于两固体相互接触的界面上。",
                "analysis": "对比**牛顿内摩擦定律**与**库仑干摩擦定律**即可清晰归纳二者的全部物理差异：\n\n- **液体黏性内摩擦**：\n\n$$\nT = \\tau A = \\mu A \\frac{\\mathrm{d}u}{\\mathrm{d}y}\n$$\n\n核心特征：无静摩擦（相对运动时才显现）、正比于接触面积 $A$ 与速度梯度 $\\frac{\\mathrm{d}u}{\\mathrm{d}y}$、与法向压应力无关、受流体种类与温度（$\\mu$）影响显著，分布于整个流动区域内部。\n\n- **固体间干摩擦**：\n\n$$\nF_{\\text{静}} \\le f_s N, \\qquad F_{\\text{动}} = f_k N\n$$\n\n核心特征：存在静摩擦力、正比于法向正压力 $N$、与接触面积和相对速度大小基本无关、仅局限于固—固接触表面。",
                "analysisFigures": [],
                "pitfalls": "答题建议分条列出公式 $T = \\mu A\\frac{\\mathrm{d}u}{\\mathrm{d}y}$ 与 $F = f N$ 逐项对照，至少涵盖“有无静摩擦、与面积/正压力关系、与速度梯度关系、发生部位”四个维度，避免漏项失分。",
                "chapter": 1,
                "kps": ["牛顿内摩擦定律", "液体黏滞性"],
                "method": "牛顿内摩擦定律与库仑摩擦对比法",
                "difficulty": 1,
                "rubric": [
                    {"label": "指出发生条件与部位区别（液体静止无静摩擦、发生在内部各相对运动液层；固体有静摩擦、限于接触面）", "pts": 3},
                    {"label": "指出与接触面积及法向正压力关系的区别（液体正比于面积且与正压力无关；固体正比于正压力且与面积无关）", "pts": 3},
                    {"label": "指出与速度梯度/黏度关系的区别并写出牛顿内摩擦定律表达式", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2016-02",
                "year": 2016,
                "no": 2,
                "type": "short",
                "score": 8,
                "title": "平行平板间抛物线流速分布微元水体切应力方向与极值分析",
                "stem": "液体在两块平板间流动，流速分布如图所示，从中取出 $A$、$B$、$C$ 三块自由水体，试分析：\n\n（1）各水体上下两平面上所受切应力的方向；\n\n（2）定性指出哪个面上的切应力最大？哪个最小？为什么？",
                "note": "",
                "figures": [
                    {"src": "figures/q02_orig.png", "caption": "题 2 图　两平行平板间流速分布与自由水体 A、B、C 位置"}
                ],
                "shortAnswer": "（1）A 上左、下右；B 上左、下左；C 上右、下左。（2）最靠近上下固定壁面的面（A 上面或 C 下面）切应力最大，位于对称中心轴线处（B 中心面，du/dr=0）切应力最小为零。",
                "judgeAnswer": None,
                "answer": "（1）**各水体上下表面切应力方向**（以主流方向向右为正，见解图 2）：\n- 水体 $A$（上半区）：**上表面向左**（上方紧贴静止壁面流速更慢，施加阻滞力），**下表面向右**（下方靠近中心轴流速更快，施加拖曳力）；\n- 水体 $B$（跨对称轴）：**上表面向左、下表面向左**（对称轴处流速最大，上下外侧液层均比 $B$ 的核心慢，均施加向左的阻滞力）；\n- 水体 $C$（下半区）：**上表面向右**（上方靠近中心轴流速更快，施加拖曳力），**下表面向左**（下方靠近静止底板流速更慢，施加阻滞力）。\n\n（2）**切应力极值位置及理由**：\n由牛顿内摩擦定律 $|\\tau| = \\mu\\left|\\frac{\\mathrm{d}u}{\\mathrm{d}r}\\right|$，切应力大小与速度梯度绝对值成正比。在抛物线形流速分布中，**最靠近上下固定壁面的平面（图中水体 $A$ 的上表面，或若 $C$ 等距对称则 $C$ 的下表面）速度梯度 $\\left|\\frac{\\mathrm{d}u}{\\mathrm{d}r}\\right|$ 最大，故切应力最大**；在**两板中间对称轴线 $r = 0$（水体 $B$ 中心面）处流速达极值，$\\frac{\\mathrm{d}u}{\\mathrm{d}r} = 0$，故切应力最小（为零）**（在三个水体的六个外表面中，$B$ 的上下表面离轴线最近，所受切应力最小）。",
                "analysis": "**1. 判断切应力方向的万能口诀：“快拖慢、慢阻快”**\n\n平行平板间的抛物线形层流流速分布为 $u(r) = u_{\\max}\\left(1 - \\frac{r^2}{r_0^2}\\right)$，水流整体向右流动，中心轴 $r = 0$ 处流速最大，向上下固定平板 $r = \\pm r_0$ 递减至 $0$。对每一块自由水体的上、下表面，只需比较交界面**外侧液层**与**水体自身**谁更快：\n- **水体 $A$**：外侧上面更慢 $\\Rightarrow$ 上表面受**向左**阻力；外侧下面更快 $\\Rightarrow$ 下表面受**向右**拖曳力。\n- **水体 $B$**：跨越对称轴 $r = 0$，无论上表面外侧还是下表面外侧，流速均小于 $B$ 内部，故**上下两面均受向左的阻滞切应力**。\n- **水体 $C$**：外侧上面更快 $\\Rightarrow$ 上表面受**向右**拖曳力；外侧下面更慢 $\\Rightarrow$ 下表面受**向左**阻力。\n\n**2. 切应力大小分布规律**\n\n对 $u(r)$ 求导得：\n\n$$\n|\\tau(r)| = \\mu\\left|\\frac{\\mathrm{d}u}{\\mathrm{d}r}\\right| = \\frac{2\\mu u_{\\max}}{r_0^2}|r|\n$$\n\n可见切应力大小从中心轴 $r = 0$ 处的 $0$ 沿径向呈线性递增，至上下固定壁面 $|r| = r_0$ 处达到最大值 $\\tau_{\\max} = \\frac{2\\mu u_{\\max}}{r_0}$。结合题图可见，水体 $A$ 最贴近上壁面（$A$ 上表面 $|r|$ 最大），切应力最大；对称中心轴线处（水体 $B$ 中心）$\\frac{\\mathrm{d}u}{\\mathrm{d}r} = 0$、$\\tau = 0$ 最小（若仅在六表面中比较，则 $B$ 的上下表面 $|r|$ 最小、切应力最小）。",
                "analysisFigures": [
                    {"src": "figures/q02_sol.png", "caption": "解图 2　平行平板间自由水体 A、B、C 切应力方向与大小分布图"}
                ],
                "pitfalls": "最容易错判的是居中水体 $B$ 的下表面方向！$B$ 跨越最大流速对称轴，其上下外侧液层均比中心慢，因此 $B$ 的**上下两表面切应力均向左**（与压力梯度推动力平衡）。",
                "chapter": 1,
                "kps": ["牛顿内摩擦定律", "微元水体切应力方向"],
                "method": "牛顿内摩擦快拖慢方向判别法",
                "difficulty": 2,
                "rubric": [
                    {"label": "准确判出 A（上左下右）、B（上左下左）、C（上右下左）三块水体共六个表面的切应力方向", "pts": 5},
                    {"label": "依据牛顿内摩擦定律 τ = μ|du/dr| 指出近壁面（A 上面 / C 下面）最大、中心对称轴处（B 处）最小并阐明理由", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2016-03",
                "year": 2016,
                "no": 3,
                "type": "short",
                "score": 8,
                "title": "S 形二元曲面铅垂压力体与铅垂投影面水平压强分布图绘制",
                "stem": "绘出图中二维曲面上的铅垂水压力的压力体及曲面在铅垂投影面上的水平压强分布图。",
                "note": "",
                "figures": [
                    {"src": "figures/q03_orig.png", "caption": "题 3 图　右侧挡水的 S 形二维曲面 AB"}
                ],
                "shortAnswer": "详见解图 3：以拐点 E 为界，上段 AE 向右凸入水中，净铅垂压力体为封闭右半圆（虚压力体，向上 ↑）；下段 EB 向左凹入，净铅垂压力体为封闭左半圆（实压力体，向下 ↓）；铅垂投影面水平压强呈三角形分布（顶部为 0、底部为 ρgH，方向水平向左）。",
                "judgeAnswer": None,
                "answer": "铅垂静水压力的压力体图与铅垂投影面上的水平压强分布图详见**解图 3**：\n\n（1）**铅垂水压力的压力体**：设曲面中部的水平切线拐点为 $E$，连结铅垂基准线 $AEB$（水体位于曲面右侧）：\n- **上段圆弧 $AE$**：向右凸入水体内部，上四分之一弧段受水向下压力（实压力体）与下四分之一弧段受水向上压力（虚压力体）重叠抵消后，净压力体即为上段封闭的**右半圆区域（虚压力体，方向竖直向上 $\\uparrow$）**；\n- **下段圆弧 $EB$**：水体充满左侧凹腔，上四分之一弧段向上虚压力体与下四分之一弧段向下实压力体抵消其上方重合水柱后，净压力体即为下段封闭的**左半圆区域（实压力体，方向竖直向下 $\\downarrow$）**。\n\n（2）**铅垂投影面上的水平压强分布图**：曲面 $AB$ 在铅垂面上的有效投影为高度等于水深 $H$ 的铅垂线段，因水体位于曲面右侧，水平压强分布呈**直角三角形**（液面 $A$ 处 $p = 0$，底面 $B$ 处 $p = \\rho g H$），压强箭头全部**水平指向左方**。",
                "analysis": "**1. 分段绘出铅垂压力体并标明虚实方向**\n\n压力体由曲面本身、过曲面两端点的铅垂面以及自由液面（或其延长面）围成。观察题 3 图，自由液面在曲面右侧且过 $A$ 点，设中间拐点为 $E$（$A$、$E$、$B$ 共铅垂线）：\n- **上段弧 $AE$**：向右凸出排开水体。上侧四分之一弧的水体在上方（向下实压力体），下侧四分之一弧的水体在下方（向上虚压力体）；向上虚压力体比向下实压力体恰好大出整个右凸半圆的体积，因此净压力体是**右凸半圆（虚压力体，作用方向竖直向上）**。\n- **下段弧 $EB$**：水体位于左凹半圆内部。凹腔顶弧受向上虚压力体，凹腔底弧受向下实压力体；两者在凹腔顶弧以上的共同水柱正负抵消，留下的净压力体即为**左凹半圆（实压力体，作用方向竖直向下）**。\n\n（若上下两半圆半径相等，则上段向上浮力与下段向下水重大小相等、方向相反，整个 $S$ 形曲面净铅垂分力为零，但仍存在静水力偶。）\n\n**2. 绘出铅垂投影面上的水平压强分布图**\n\n水体始终在曲面右侧，水平静水压强仅取决于淹深 $z$：$p(z) = \\rho g z$。在高度为 $H$ 的铅垂投影面上，压强从顶端 $A$ 处的 $0$ 线性增大至底端 $B$ 处的 $\\rho g H$，形成直角三角形压强分布图，所有水平压强箭头均**指向左方**。",
                "analysisFigures": [
                    {"src": "figures/q03_sol.png", "caption": "解图 3　S 形二维曲面铅垂虚实压力体图与铅垂投影面水平压强分布图"}
                ],
                "pitfalls": "1. 绘压力体图**必须标明虚/实方向箭头（上段向上 $\\uparrow$、下段向下 $\\downarrow$）**，只画阴影不标方向会扣分！\n2. 水体在曲面**右侧**，因此铅垂投影面上的水平压强箭头必须**向左**指向受压面，切勿画成向右。",
                "chapter": 2,
                "kps": ["压力体图与虚压力体", "曲面静水总压力", "水平压强分布图"],
                "method": "水平投影与铅垂压力体分块合成法",
                "difficulty": 2,
                "rubric": [
                    {"label": "正确绘出上段右凸虚压力体并标明铅垂向上方向（↑）", "pts": 3},
                    {"label": "正确绘出下段左凹实压力体并标明铅垂向下方向（↓）", "pts": 3},
                    {"label": "正确绘出铅垂投影面三角形水平压强分布图（顶 0 底 ρgH，箭头向左）", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2016-04",
                "year": 2016,
                "no": 4,
                "type": "short",
                "score": 8,
                "title": "关阀静止给水管路特征点压强水头与测压管水头计算",
                "stem": "一给水管路在其出口闸门关闭时（见图示），试确定管路中 $A$、$B$ 两点的压强水头和测压管水头。",
                "note": "",
                "figures": [
                    {"src": "figures/q04_orig.png", "caption": "题 4 图　出口阀门关闭时的静止给水管路"}
                ],
                "shortAnswer": "压强水头：A 点为 3 m，B 点为 10 m；测压管水头（以 B 管轴线为基准面）：A、B 两点均为 10 m（若以水箱自由液面为基准面则均为 0 m）。",
                "judgeAnswer": None,
                "answer": "出口闸门关闭时管内水流静止，整个水箱与给水管构成连通静止的同种均质水体：\n\n（1）**压强水头（相对压强水头 $\\frac{p}{\\rho g}$）**：\n- $A$ 点位于自由液面以下 $h_A = 3\\,\\mathrm{m}$，故 $\\frac{p_A}{\\rho g} = 3\\,\\mathrm{m}$；\n- $B$ 点位于自由液面以下 $h_B = 10\\,\\mathrm{m}$，故 $\\frac{p_B}{\\rho g} = 10\\,\\mathrm{m}$。\n\n（2）**测压管水头（$z + \\frac{p}{\\rho g}$）**：\n- 选下方水平管轴线（过 $B$ 点水平面）为基准面（$z_B = 0\\,\\mathrm{m}$，$z_A = 10 - 3 = 7\\,\\mathrm{m}$）：\n  - $A$ 点测压管水头：$z_A + \\frac{p_A}{\\rho g} = 7 + 3 = 10\\,\\mathrm{m}$；\n  - $B$ 点测压管水头：$z_B + \\frac{p_B}{\\rho g} = 0 + 10 = 10\\,\\mathrm{m}$。\n（注：测压管水头数值与基准面选择有关，但同一静止连通液体各点测压管水头必相等且等于自由液面高程；若以水箱自由液面为基准面，则 $A$、$B$ 两点测压管水头均为 $0\\,\\mathrm{m}$。）",
                "analysis": "**1. 识别静止连通液体性质**\n\n出口闸门关闭后，管内无水流运动（$v = 0$），水箱与管道内所有水体处于重力静力平衡状态，处处满足水静力学基本方程：\n\n$$\nz + \\frac{p}{\\rho g} = \\mathrm{const} = z_{\\text{液面}}\n$$\n\n**2. 分别求压强水头与测压管水头**\n\n- **压强水头 $\\frac{p}{\\rho g}$** 与基准面无关，仅等于测点在自由液面以下的淹深：\n\n$$\n\\frac{p_A}{\\rho g} = h_A = 3\\,\\mathrm{m}, \\qquad \\frac{p_B}{\\rho g} = h_B = 10\\,\\mathrm{m}\n$$\n\n- **测压管水头 $z + \\frac{p}{\\rho g}$** 依赖基准面选取，作答时必须**先明确写出基准面**。取下方水平管轴线为 $0\\text{—}0$ 基准面（$z_B = 0$，水箱自由液面高程 $z_{\\text{液面}} = 10\\,\\mathrm{m}$，$z_A = 10 - 3 = 7\\,\\mathrm{m}$），则：\n\n$$\nH_{pA} = z_A + \\frac{p_A}{\\rho g} = 7 + 3 = 10\\,\\mathrm{m}, \\qquad H_{pB} = z_B + \\frac{p_B}{\\rho g} = 0 + 10 = 10\\,\\mathrm{m}\n$$",
                "analysisFigures": [],
                "pitfalls": "求**测压管水头** $z + \\frac{p}{\\rho g}$ 前一定要**先声明基准面位置**！不声明基准面直接写“$10\\,\\mathrm{m}$”是不严谨的扣分点。",
                "chapter": 2,
                "kps": ["压强水头", "测压管水头", "静水压强基本方程"],
                "method": "等压面静水压强递推法",
                "difficulty": 1,
                "rubric": [
                    {"label": "指出关阀后为静止连通水体，准确求得 A 点压强水头 3 m、B 点压强水头 10 m", "pts": 4},
                    {"label": "明确选定基准面（如下方水平管轴线），求得 A、B 两点测压管水头相等且均为 10 m", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2016-05",
                "year": 2016,
                "no": 5,
                "type": "short",
                "score": 8,
                "title": "等直径无损弯管流速沿程变化、压强极值位置及进口压强辨析",
                "stem": "有一如图所示的等直径弯管，试问：\n\n（1）水流由低处流向高处的 $AB$ 管段中断面平均流速 $v$ 是否会沿程减小？在由高处流向低处的 $BC$ 管段中断面平均流速 $v$ 是否会沿程增大？为什么？\n\n（2）如果不计管中的水头损失，何处压强最小？何处最大？进口内 $A$ 点压强是否为 $\\rho g H$？",
                "note": "",
                "figures": [
                    {"src": "figures/q05_orig.png", "caption": "题 5 图　水箱连接的等直径倾斜弯管 ABC"}
                ],
                "shortAnswer": "（1）均不会，由连续性方程 Q = vA，等径有压满管内断面平均流速 v 沿程恒定不变。（2）不计损失时，最高点 B 处压强最小（负压最大），管内最低点出口 C 处压强最大（pC = 0 大气压）；进口内 A 点压强 pA = ρgH - (1/2)ρv² < ρgH，不等于 ρgH。",
                "judgeAnswer": None,
                "answer": "（1）**均不会**（$AB$ 段流速不会减小，$BC$ 段流速也不会增大）。\n- **理由**：对于不可压缩恒定有压满管流，由连续性方程 $Q = v A = \\mathrm{const}$，因弯管为等直径管道（各断面面积 $A$ 处处相等），故断面平均流速 $v = Q/A$ 沿整个管段恒定不变（$v_A = v_B = v_C$），与管道爬升或下降无关。\n\n（2）**不计水头损失时（见解图 5）**：\n- 由等流速无损伯努利方程 $z + \\frac{p}{\\rho g} = z_C + \\frac{p_C}{\\rho g} = \\mathrm{const}$，位置越高压强越小、位置越低压强越大：\n  - **压强最小处**：管道**最高点 $B$ 处**（负压/真空度最大）；\n  - **压强最大处**：管内**最低点出口 $C$ 处**（$z_C < z_A < z_B$，相对压强 $p_C = 0$ 为大气压，而管内其余各点均高于 $C$ 故为负压，$p_B < p_A < p_C$）；\n- **进口内 $A$ 点压强不是 $\\rho g H$**：对水箱液面与进口内 $A$ 点列能量方程得 $H = \\frac{p_A}{\\rho g} + \\frac{v^2}{2g}$，故 $p_A = \\rho g H - \\frac{1}{2}\\rho v^2 < \\rho g H$（部分位能已转化为管内水流动态动能）。",
                "analysis": "**（1）连续性方程判别流速变化**\n\n不可压缩液体在充满水的等直径管道内作恒定流，根据质量守恒（连续性方程）：\n\n$$\nQ = v_A A_A = v_B A_B = v_C A_C\n$$\n\n因为管道等径（$A_A = A_B = A_C = A$），所以 $v_A = v_B = v_C = \\mathrm{const}$。管内水体是一个连续整体，不会在上升段减速或在下降段加速。\n\n**（2）无损伯努利方程判别压强极值与 $A$ 点压强（见解图 5）**\n\n不计水头损失（$h_w = 0$，取 $\\alpha = 1.0$），对水箱液面（$z_0 = Z_0, p_0 = 0, v_0 \\approx 0$）、管内任一点 $(z, p, v)$ 及自由出流出口 $C$（$z_C, p_C = 0, v_C = v$）列能量方程：\n\n$$\nZ_0 = z + \\frac{p}{\\rho g} + \\frac{v^2}{2g} = z_C + 0 + \\frac{v^2}{2g}\n$$\n\n由各处流速相等，消去相同流速水头 $\\frac{v^2}{2g}$ 可得全管内任一点的相对压强规律：\n\n$$\n\\frac{p(z)}{\\rho g} = z_C - z \\implies p(z) = \\rho g (z_C - z)\n$$\n\n- **压强极值**：因 $z_B > z_A > z_C$，故最高点 **$B$ 处压强最小**（$p_B = \\rho g(z_C - z_B) < 0$，负压最大），管内最低点 **$C$ 处压强最大**（$p_C = 0$，即 $p_B < p_A < p_C$）。\n- **进口内 $A$ 点压强**：对水箱液面与 $A$ 断面列能量方程：\n\n$$\nH = \\frac{p_A}{\\rho g} + \\frac{v^2}{2g} \\implies p_A = \\rho g H - \\frac{1}{2}\\rho v^2 < \\rho g H\n$$\n\n（且因 $z_A > z_C$，此处 $p_A = \\rho g(z_C - z_A)$ 甚至为负压！只有在出口封闭、水体静止 $v = 0$ 时 $p_A$ 才等于静水压强 $\\rho g H$。）",
                "analysisFigures": [
                    {"src": "figures/q05_sol.png", "caption": "解图 5　等径无损弯管总水头线、测压管水头线与压强分布分析图"}
                ],
                "pitfalls": "判断“何处压强最大”时切勿凭感觉答“$A$ 点压强最大”！观察题图可知出口 $C$ 明显低于进口 $A$（$z_C < z_A$），由 $z + p/(\\rho g) = z_C$ 知 $p_A = \\rho g(z_C - z_A) < 0 = p_C$，因此管内压强最大处是最低点 $C$ 而非 $A$！",
                "chapter": 3,
                "kps": ["连续性方程", "伯努利方程", "总水头线与测压管水头线"],
                "method": "伯努利方程动能压能转化分析法",
                "difficulty": 2,
                "rubric": [
                    {"label": "（1）应用连续性方程 Q = vA 准确论证等径管内流速 v 沿程不变（既不减小也不增大）", "pts": 3},
                    {"label": "（2）应用无损伯努利方程论证最高点 B 压强最小、最低点出口 C 压强最大（pB < pA < pC）", "pts": 3},
                    {"label": "（2）列水箱至 A 点能量方程证明 pA = ρgH - (1/2)ρv² ≠ ρgH", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2016-06",
                "year": 2016,
                "no": 6,
                "type": "short",
                "score": 8,
                "title": "层流黏性切应力与紊流总切应力的物理成因及流速关系对比",
                "stem": "层流与紊流中的切应力各由什么原因引起的？它们与流速又有什么关系？",
                "note": "",
                "figures": [],
                "shortAnswer": "层流切应力仅由分子热运动和分子间内聚力（黏滞性）引起，τ = μ(du/dy)，与流速梯度成正比；紊流总切应力由黏滞切应力 τv = μ(dū/dy) 和流体微团宏观紊动混掺动量交换引起的雷诺附加切应力 τt = -ρu'v' 组成，与时均流速梯度及脉动流速强度（或普朗特混合长度下 (dū/dy)²）有关。",
                "judgeAnswer": None,
                "answer": "（1）**层流中的切应力**：\n- **引起原因**：仅由流体分子热运动动量交换与分子间内聚力（即流体的**黏滞性**）引起；\n- **与流速关系**：遵循牛顿内摩擦定律 $\\tau = \\mu \\frac{\\mathrm{d}u}{\\mathrm{d}y}$，切应力与流速梯度（流速的法向一阶导数）呈**线性正比**关系（对圆管层流，壁面切应力 $\\tau_0 \\propto v$）。\n\n（2）**紊流中的切应力**：\n- **引起原因**：由两部分组成——一是流层间**时均流速**相对滑动引起的**黏滞切应力** $\\tau_v$；二是由流体微团剧烈**脉动混掺与横向动量交换**引起的**紊动附加切应力（雷诺应力）** $\\tau_t$：\n\n$$\n\\tau = \\tau_v + \\tau_t = \\mu \\frac{\\mathrm{d}\\overline{u}}{\\mathrm{d}y} - \\rho\\overline{u_x^{\\prime} u_y^{\\prime}}\n$$\n\n- **与流速关系**：既取决于**时均流速梯度** $\\frac{\\mathrm{d}\\overline{u}}{\\mathrm{d}y}$，更主要取决于**脉动流速**的相关强度（按普朗特混合长度理论 $\\tau_t = \\rho l^2\\left|\\frac{\\mathrm{d}\\overline{u}}{\\mathrm{d}y}\\right|\\frac{\\mathrm{d}\\overline{u}}{\\mathrm{d}y}$，在紊流核心区 $\\tau_t \\gg \\tau_v$，与时均流速梯度的平方成正比；在贴壁黏滞底层内 $\\tau_v$ 占主导）。",
                "analysis": "**1. 层流切应力机理与公式**\n\n层流中流体质点分层平稳流动、互不混掺，相邻液层间的动量传递完全依靠微观分子运动与分子吸引力（黏滞性），严格服从牛顿内摩擦定律：\n\n$$\n\\tau = \\mu \\frac{\\mathrm{d}u}{\\mathrm{d}y}\n$$\n\n它与瞬时流速的法向梯度 $\\frac{\\mathrm{d}u}{\\mathrm{d}y}$ 成一次线性正比关系。\n\n**2. 紊流切应力机理与公式**\n\n紊流中各点瞬时流速包含时均项与脉动项（$u = \\overline{u} + u^{\\prime}$）。流体团在垂直主流方向上的随机脉动混掺，不断将快层动量带入慢层、将慢层动量带入快层，产生远大于分子黏性的宏观附加切应力（雷诺应力 $\\tau_t = -\\rho\\overline{u_x^{\\prime} u_y^{\\prime}}$）。因此紊流总切应力为两项叠加：\n\n$$\n\\tau = \\mu \\frac{\\mathrm{d}\\overline{u}}{\\mathrm{d}y} - \\rho\\overline{u_x^{\\prime} u_y^{\\prime}} = \\mu \\frac{\\mathrm{d}\\overline{u}}{\\mathrm{d}y} + \\rho l^2 \\left|\\frac{\\mathrm{d}\\overline{u}}{\\mathrm{d}y}\\right|\\frac{\\mathrm{d}\\overline{u}}{\\mathrm{d}y}\n$$\n\n其中紧贴边壁的黏滞底层脉动受阻，$\\tau_v$ 占主导；而在广大的紊流核心区，$\\tau_t \\gg \\tau_v$，切应力与脉动流速相关量（或时均流速梯度的平方）成正比。",
                "analysisFigures": [],
                "pitfalls": "描述紊流切应力时务必同时写出**黏滞切应力**和**紊动附加切应力（雷诺应力）**两部分，切不可只写雷诺应力而忽略黏滞切应力。",
                "chapter": 4,
                "kps": ["牛顿内摩擦定律", "雷诺附加切应力", "普朗特混合长度理论"],
                "method": "分子黏性应力与湍流雷诺应力机理对比法",
                "difficulty": 2,
                "rubric": [
                    {"label": "准确阐明层流切应力由黏滞性（分子动量交换/内聚力）引起，τ = μ(du/dy) 与流速梯度成正比", "pts": 3},
                    {"label": "准确阐明紊流总切应力由黏滞切应力与微团脉动混掺引起的雷诺附加切应力组成，写出表达式", "pts": 3},
                    {"label": "清楚说明紊流切应力与时均流速梯度及脉动流速（或普朗特混合长度平方律）的关系", "pts": 2}
                ]
            },
            {
                "id": "yzu-849-2016-07",
                "year": 2016,
                "no": 7,
                "type": "short",
                "score": 8,
                "title": "保持明渠均匀流流量不变而减小流速防冲刷的工程措施分析",
                "stem": "今欲将产生均匀流的渠道中的流速减小，以减小冲刷，但是流量仍然保持不变，试问：有几种可能的方法可以达到此目的。",
                "note": "",
                "figures": [],
                "shortAnswer": "由 Q = vA 及谢才—曼宁公式 v = (1/n)R^(2/3)i^(1/2)，保持 Q 不变而减小 v 可通过四种途径：（1）减缓渠道底坡 i（如设跌水）；（2）增大渠道糙率 n（如护底加糙）；（3）增大过水断面面积 A（如拓宽渠底或加大水深）；（4）在保证 A 增大的同时减小水力半径 R（即增大湿周 χ，将断面改为宽浅式）。",
                "judgeAnswer": None,
                "answer": "由明渠均匀流连续性方程 $Q = v A$ 及谢才—曼宁公式 $v = \\frac{1}{n} R^{2/3} i^{1/2}$ 可知，在保持流量 $Q$ 不变的前提下，减小断面平均流速 $v$（同时必然伴随过水断面面积 $A = Q/v$ 的相应增大）有以下**四种工程方法**：\n\n1. **减小渠道底坡 $i$**（例如在渠线中增设跌水或陡坡建筑物分段消能、降低各段平顺渠道底坡）；\n2. **增大渠道粗糙系数 $n$**（例如采用砌石、混凝土块或植草等较粗糙的护砌材料增大边壁阻力）；\n3. **增大过水断面面积 $A$**（如加宽渠底宽度 $b$、放缓边坡系数 $m$ 以扩大断面过水面积）；\n4. **减小断面水力半径 $R$（即增大湿周 $\\chi$）**（例如将原本接近水力最佳断面的深窄断面改为宽浅式或复式断面，增大水体与边壁接触阻力，使流速降低）。",
                "analysis": "**从明渠均匀流基本控制方程出发系统分析**\n\n明渠恒定均匀流同时满足连续性方程与谢才—曼宁流速公式：\n\n$$\nQ = v A, \\qquad v = C\\sqrt{R i} = \\frac{1}{n} R^{2/3} i^{1/2} = \\frac{1}{n}\\left(\\frac{A}{\\chi}\\right)^{2/3} i^{1/2}\n$$\n\n要在保持过流能力 $Q$ 不变的同时降低平均流速 $v$，首先由 $A = Q/v$ 可知过水面积 $A$ 必须随之增大；其次由流速公式 $v = \\frac{1}{n} R^{2/3} i^{1/2}$ 可直接看出降低 $v$ 的全部独立可控水力参数：\n1. **降低底坡 $i$**：在总落差固定时，通过设置跌水、陡槽集中落差，可显著减小一般渠段底坡 $i$，降低流速；\n2. **增大糙率 $n$**：通过改换粗糙度较大的衬砌或铺设消能防冲加糙块体增大 $n$；\n3. **增大过水断面面积 $A$**：扩宽渠道断面使水流分散通过，直接降低平均流速 $v = Q/A$；\n4. **增大湿周 $\\chi$（减小水力半径 $R$）**：将渠道断面修筑得更宽浅（偏离水力最佳断面），使相同面积下的湿周增大、阻力增强，从而降低流速（且降低底坡 $i$ 或增大糙率 $n$ 后，相同 $Q$ 下均匀流水深自动壅高，$A$ 自然增大，与 $Q = vA$ 协调一致）。",
                "analysisFigures": [],
                "pitfalls": "不要只笼统写“增大面积 $A$”，必须结合曼宁公式 $v = \\frac{1}{n} R^{2/3} i^{1/2}$ 把**底坡 $i$、糙率 $n$、断面面积 $A$、湿周 $\\chi$（水力半径 $R$）**四个参数全部点明！",
                "chapter": 7,
                "kps": ["谢才-曼宁公式", "明渠均匀流水力设计"],
                "method": "谢才—曼宁公式明渠均匀流水力计算法",
                "difficulty": 2,
                "rubric": [
                    {"label": "写出连续性方程 Q = vA 与谢才—曼宁公式 v = (1/n)R^(2/3)i^(1/2) 作为理论依据", "pts": 2},
                    {"label": "完整答出减小底坡 i、增大糙率 n、增大过水面积 A、增大湿周 χ（减小水力半径 R）四种方法（每条 1.5 分）", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2016-08",
                "year": 2016,
                "no": 8,
                "type": "short",
                "score": 8,
                "title": "从力学平衡角度论证仅顺坡渠道可形成明渠均匀流",
                "stem": "试从力学角度分析解释为什么说只有在顺坡渠道中有可能形成均匀流，在平坡和逆坡渠道中不可能形成均匀流？",
                "note": "",
                "figures": [],
                "shortAnswer": "取均匀流棱柱体水体为隔离体，因上下游水深相等，静水压力 P1 = P2 相互抵消，沿流向动量变化为零，故力学平衡方程简化为 G·sinθ = Ff（重力沿流向分力平衡边壁摩阻力）。因摩阻力 Ff > 0 始终逆流向，仅顺坡（i > 0, G·sinθ > 0）可满足平衡；平坡（i = 0, G·sinθ = 0）和逆坡（i < 0, G·sinθ < 0 与 Ff 同向阻流）均无法平衡 Ff，故不可能形成均匀流。",
                "judgeAnswer": None,
                "answer": "取明渠恒定均匀流中任意一段长为 $l$ 的水体 $ABCD$ 为隔离体（渠底与水平面倾角为 $\\theta$，底坡 $i = \\sin\\theta$，见解图 8）。\n\n因均匀流沿程水深、断面面积及流速分布均不变化：\n- 上、下游两过水断面上的动水总压力相等且方向相反：$P_1 = P_2$；\n- 流出与流入隔离体的动量通量相等：$\\rho Q (\\beta_2 v_2 - \\beta_1 v_1) = 0$。\n\n因此，沿水流方向的力学（动量）平衡方程简化为：\n\n$$\nP_1 - P_2 + G\\sin\\theta - F_f = 0 \\implies G\\sin\\theta = F_f\n$$\n\n对于实际黏性流体，只要流动存在，边壁切向摩阻力 $F_f = \\tau_0 \\chi l > 0$ 且始终指向**逆水流方向**。分三种底坡讨论：\n1. **平坡（$i = 0,\\; \\theta = 0$）**：重力沿流向分力 $G\\sin\\theta = 0$，但 $F_f > 0$，合力不为零，无法满足 $G\\sin\\theta = F_f$；\n2. **逆坡（$i < 0,\\; \\theta < 0$）**：重力沿流向分力 $G\\sin\\theta < 0$ 与摩阻力 $F_f$ **同向阻滞水流**，更不可能相互平衡；\n3. **顺坡（$i > 0,\\; \\theta > 0$）**：重力沿流向分力 $G\\sin\\theta > 0$ 指向下游推动水流，与指向阻力方向的 $F_f$ 方向相反，当大小相等（$G\\sin\\theta = F_f$）时即满足力平衡条件，故**只有在顺坡渠道中才有可能形成明渠均匀流**。",
                "analysis": "**1. 明渠均匀流隔离体受力分析（见解图 8）**\n\n假设明渠中形成了恒定均匀流，截取长为 $l$ 的棱柱水体 $ABCD$，沿水流方向作用的全部外力包括：\n- 上游断面静水总压力 $P_1$（顺流向）与下游断面静水总压力 $P_2$（逆流向）；因均匀流水深 $h$ 沿程不变且断面呈静水压强分布，故 $P_1 = P_2$；\n- 液体自重沿流向的分力 $G\\sin\\theta = \\rho g A l \\sin\\theta$；\n- 固体边壁（渠底及边坡）对水流的摩阻力 $F_f = \\tau_0 \\chi l > 0$（逆流向）。\n\n又因恒定均匀流断面平均流速 $v_1 = v_2$、流速分布相同，动量变化率为零，故沿流向列动量平衡方程得：\n\n$$\nG\\sin\\theta = F_f > 0\n$$\n\n**2. 三类底坡的平衡条件判别**\n\n- **平坡（$i = 0$）**：$G\\sin\\theta = 0 \\neq F_f$，无动力克服阻力，水流必然依靠水深沿程减小提供压差力（$P_1 > P_2$），只能是非均匀流；\n- **逆坡（$i < 0$）**：$G\\sin\\theta < 0$ 与 $F_f$ 同向阻碍流动，更无法平衡；\n- **顺坡（$i > 0$）**：$G\\sin\\theta > 0$ 恰与 $F_f$ 反向，当水深自动调节至正常水深 $h_0$ 使 $G\\sin\\theta = F_f$ 时，即可形成明渠恒定均匀流。",
                "analysisFigures": [
                    {"src": "figures/q08_sol.png", "caption": "解图 8　明渠均匀流隔离体沿流向受力平衡机理图"}
                ],
                "pitfalls": "务必先说明均匀流为何 $P_1 = P_2$ 且动量变化为零，再得出核心判据 $G\\sin\\theta = F_f$，切忌跳过推导直接空泛回答“水往低处流”。",
                "chapter": 7,
                "kps": ["明渠均匀流形成条件", "均匀流力学平衡方程"],
                "method": "明渠隔离体沿流向重力与摩阻力平衡法",
                "difficulty": 2,
                "rubric": [
                    {"label": "取均匀流隔离体并说明上下游压差抵消（P1 = P2）及动量变化为零，导出核心平衡式 G·sinθ = Ff", "pts": 4},
                    {"label": "分别讨论平坡（i=0）、逆坡（i<0）无法平衡 Ff > 0，仅顺坡（i>0）满足平衡形成均匀流", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2016-09",
                "year": 2016,
                "no": 9,
                "type": "calc",
                "score": 12,
                "title": "双水银测压计封闭压力容器液面水深 H 计算",
                "stem": "某压力容器，如图所示。容器上装有两个水银测压计，已知 $h_1 = 2.0\\,\\mathrm{cm}$，$h_2 = 24.0\\,\\mathrm{cm}$，$h_3 = 22.0\\,\\mathrm{cm}$，求水深 $H$。",
                "note": "",
                "figures": [
                    {"src": "figures/q09_orig.png", "caption": "题 9 图　装设双 U 形水银测压计的压力容器"}
                ],
                "shortAnswer": "H = 2.48 m。",
                "judgeAnswer": None,
                "answer": "容器内水深 $H = 2.48\\,\\mathrm{m}$。",
                "analysis": "**1. 由上部右侧水银测压计求容器顶部气室相对压强 $p_0$**\n\n右侧 U 形水银测压计与容器上部密闭气体连通，右管敞口通大气（相对压强为 $0$），不计气体自重。过右侧 U 形管左支水银液面作等压面 $2\\text{—}2$：\n\n$$\np_0 = \\rho_{\\mathrm{m}} g h_1\n$$\n\n**2. 由下部左侧水银测压计列等压面方程并求解水深 $H$**\n\n左侧 U 形水银测压计与容器下部水体连通，左管敞口通大气（相对压强为 $0$）。过左侧 U 形管右支水—水银交界面作等压面 $1\\text{—}1$，水体总高度为 $H + h_2$，水银柱高度差为 $h_3$：\n\n$$\np_0 + \\rho g (H + h_2) = \\rho_{\\mathrm{m}} g h_3\n$$\n\n将 $p_0 = \\rho_{\\mathrm{m}} g h_1$ 代入上式，两边同除以 $\\rho g$：\n\n$$\n\\frac{\\rho_{\\mathrm{m}}}{\\rho} h_1 + (H + h_2) = \\frac{\\rho_{\\mathrm{m}}}{\\rho} h_3 \\implies H = \\frac{\\rho_{\\mathrm{m}}}{\\rho}(h_3 - h_1) - h_2\n$$\n\n代入已知数值（$\\frac{\\rho_{\\mathrm{m}}}{\\rho} = 13.6$，$h_1 = 0.02\\,\\mathrm{m}$，$h_2 = 0.24\\,\\mathrm{m}$，$h_3 = 0.22\\,\\mathrm{m}$）：\n\n$$\nH = 13.6 \\times (0.22 - 0.02) - 0.24 = 13.6 \\times 0.20 - 0.24 = 2.72 - 0.24 = 2.48\\,\\mathrm{m}\n$$",
                "analysisFigures": [],
                "pitfalls": "本题所有重力加速度 $g$ 均可约去，结果与 $g$ 取 $9.80$ 还是 $9.81$ 无关！注意看清题图中 $H$ 是从水面到左侧测压管接入口的距离，下方还需加上 $h_2$ 才到达左侧水—水银交界面。",
                "chapter": 2,
                "kps": ["等压面原理", "双U形水银测压计", "静水压强基本方程"],
                "method": "等压面静水压强递推法",
                "difficulty": 1,
                "rubric": [
                    {"label": "由上部水银测压计等压面方程正确写出气室相对压强 p0 = ρmgh1", "pts": 4},
                    {"label": "由下部水银测压计等压面方程正确写出 p0 + ρg(H + h2) = ρmgh3", "pts": 5},
                    {"label": "联立消元并代入数据准确解得水深 H = 2.48 m", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2016-10",
                "year": 2016,
                "no": 10,
                "type": "calc",
                "score": 15,
                "title": "密闭容器底部圆球止水塞临界开启真空高度计算",
                "stem": "如图所示，一密闭容器，底部有一圆球止水塞子，这一容器又放置在一个水箱中。设圆球塞子的直径 $d = 0.2\\,\\mathrm{m}$，其重量为 $G = 0.353\\,\\mathrm{kN}$，其它尺寸见图。问密闭容器水面上的真空高度为多少时，才能恰好将球塞打开？",
                "note": "",
                "figures": [
                    {"src": "figures/q10_orig.png", "caption": "题 10 图　放置于水箱中的密闭容器与底部圆球止水塞"}
                ],
                "shortAnswer": "hv ≈ 5.05 m（相对压强 p0 ≈ -49.52 kPa，真空压强 pv ≈ 49.52 kPa）。",
                "judgeAnswer": None,
                "answer": "当密闭容器水面上的真空高度达到 $h_v \\approx 5.05\\,\\mathrm{m}$ 时（取 $g = 9.80\\,\\mathrm{m/s^2}$ 为 $5.053\\,\\mathrm{m}$；取 $g = 9.81\\,\\mathrm{m/s^2}$ 为 $5.048\\,\\mathrm{m}$），才能恰好将圆球止水塞打开。",
                "analysis": "**1. 审清图中内外水深尺寸与测压管水头（见解图 10）**\n\n仔细识读题 10 图尺寸标注：\n- 密闭容器内部水深（内水面至容器底板孔口平面）：$h_1 = 2.5\\,\\mathrm{m}$，内水面真空高度为 $h_v$（即气室相对压强 $p_0 = -\\rho g h_v < 0$）；\n- 外部敞口水箱水深（外水面至容器底板孔口平面）：$h_2 = 1.5\\,\\mathrm{m}$，外水面通大气（相对压强为 $0$）；\n- 圆球直径 $d = 0.2\\,\\mathrm{m}$，底部圆孔直径 $D = 0.1\\,\\mathrm{m}$，球重 $G = 0.353\\,\\mathrm{kN} = 353\\,\\mathrm{N}$。\n\n以容器底部圆孔所在水平面为 $z = 0$（向上为正），则内、外水体的测压管水头分别为：\n\n$$\nH_{\\text{内}} = h_1 - h_v = 2.5 - h_v, \\qquad H_{\\text{外}} = h_2 = 1.5\\,\\mathrm{m}\n$$\n\n**2. 用“全球浮力 + 孔口内外压差叠加法”求圆球所受净向上静水总压力 $F_z$**\n\n圆球位于圆孔上方的主体球面接触**内部水体**，伸出圆孔下方的球冠接触**外部水体**。将实际静水压强场拆分为两项叠加：\n1. **假设整个圆球完全浸没在内部水体（水头 $H_{\\text{内}}$）中**：由阿基米德浮力定理，封闭球面所受净铅垂静水压力恰等于整个圆球排开水的重量（方向**竖直向上**）：\n\n$$\nF_b = +\\rho g V_{\\text{球}} = \\rho g \\frac{\\pi d^3}{6}\n$$\n\n2. **将孔口下方球冠表面（水平投影面积 $A_{\\text{孔}} = \\frac{\\pi}{4} D^2$）的内部水体替换为外部水体**：在球冠上任意高程 $z$ 处，内外水体压强差恒为常数（因为两侧均为水，$-\\rho g z$ 项完全抵消）：\n\n$$\n\\Delta p = p_{\\text{外}}(z) - p_{\\text{内}}(z) = \\rho g (H_{\\text{外}} - H_{\\text{内}}) = \\rho g (h_2 - h_1 + h_v)\n$$\n\n故该球冠贡献的附加向上推力为 $\\Delta F_z = \\Delta p \\cdot A_{\\text{孔}} = \\rho g (h_2 - h_1 + h_v)\\frac{\\pi}{4} D^2$。\n\n合并两项即得水体对圆球塞子的精确总向上静水压力：\n\n$$\nF_z = \\rho g \\frac{\\pi d^3}{6} + \\rho g (h_2 - h_1 + h_v)\\frac{\\pi}{4} D^2\n$$\n\n**3. 列临界开启力平衡方程求解真空高度 $h_v$**\n\n当球塞恰好被向上顶开瞬间，孔口支座反力为零，由 $F_z = G$ 得：\n\n$$\n\\rho g \\frac{\\pi d^3}{6} + \\rho g (h_2 - h_1 + h_v)\\frac{\\pi}{4} D^2 = G\n$$\n\n取 $g = 9.80\\,\\mathrm{m/s^2}$，分别计算：\n- 全球浮力：$F_b = 1000 \\times 9.80 \\times \\frac{\\pi \\times 0.2^3}{6} \\approx 41.050\\,\\mathrm{N}$；\n- 孔口面积：$A_{\\text{孔}} = \\frac{\\pi}{4} \\times 0.1^2 \\approx 7.8540 \\times 10^{-3}\\,\\mathrm{m^2}$；\n- 代入平衡方程：\n\n$$\n9800 \\times (1.5 - 2.5 + h_v) \\times 7.8540 \\times 10^{-3} = 353 - 41.050 = 311.950\\,\\mathrm{N}\n$$\n\n$$\nh_v - 1.0 = \\frac{311.950}{76.969} \\approx 4.0529\\,\\mathrm{m} \\implies h_v \\approx 5.053\\,\\mathrm{m} \\approx 5.05\\,\\mathrm{m}\n$$\n\n（注：物理验证非常直观——因内水面比外水面高 $1.0\\,\\mathrm{m}$，需先抽 $1.0\\,\\mathrm{m}$ 真空才能使内外测压管水头齐平，此时圆球仅受向上浮力 $41.05\\,\\mathrm{N}$；为再克服剩余净重 $311.95\\,\\mathrm{N}$，还需在孔口形成 $4.05\\,\\mathrm{m}$ 的净负压水头差，总真空高度必为 $1.0 + 4.05 = 5.05\\,\\mathrm{m}$！若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $F_b = 41.092\\,\\mathrm{N}$，$h_v = 5.048\\,\\mathrm{m} \\approx 5.05\\,\\mathrm{m}$。）",
                "analysisFigures": [
                    {"src": "figures/q10_sol.png", "caption": "解图 10　圆球止水塞全球浮力与孔口内外压差联合平衡分析图"}
                ],
                "pitfalls": "本题有两大极易连环踩坑的符号陷阱：① 一定要看清尺寸引线——**$h_1 = 2.5\\,\\mathrm{m}$ 是容器内水深、$h_2 = 1.5\\,\\mathrm{m}$ 是外部水箱水深**，内水比外水深 $1.0\\,\\mathrm{m}$ 会把球塞往下压，必须多抽 $1.0\\,\\mathrm{m}$ 真空来抵消（即 $h_2 - h_1 = -1.0\\,\\mathrm{m}$）；② 阿基米德浮力 $+\\rho g\\frac{\\pi d^3}{6}$ 是**向上托举**球塞的正项，切忌把浮力写成负号（若同时搞反这两个符号会误算成 $4.12\\,\\mathrm{m}$）！",
                "chapter": 2,
                "kps": ["曲面静水总压力", "阿基米德浮力原理", "真空高度"],
                "method": "阿基米德浮力与静水压力平衡法",
                "difficulty": 4,
                "rubric": [
                    {"label": "准确识读内水深 h1 = 2.5 m 与外水深 h2 = 1.5 m，列出内外测压管水头关系", "pts": 3},
                    {"label": "正确运用压力体叠加（或全球浮力+孔口压差法）导出向上净水压力 Fz = ρg(πd³/6) + ρg(h2 - h1 + hv)(πD²/4)", "pts": 7},
                    {"label": "令 Fz = G = 353 N，代入数值准确解得临界开启真空高度 hv ≈ 5.05 m", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2016-11",
                "year": 2016,
                "no": 11,
                "type": "calc",
                "score": 12,
                "title": "水箱短管出流水银压差计液面高差计算",
                "stem": "图示水银压差计装置，管长 $l = 75\\,\\mathrm{cm}$，管径 $d = 2.5\\,\\mathrm{cm}$，流速 $v = 3\\,\\mathrm{m/s}$，沿程水头损失系数 $\\lambda = 0.02$，进口局部水头损失系数 $\\zeta = 0.5$。计算水银液面高差 $h_p$。（不计水池中流速）",
                "note": "",
                "figures": [
                    {"src": "figures/q11_orig.png", "caption": "题 11 图　水箱水平出流短管与 U 形水银压差计"}
                ],
                "shortAnswer": "hp ≈ 7.65 cm（0.0765 m；取 g = 9.81 m/s² 为 7.64 cm）。",
                "judgeAnswer": None,
                "answer": "水银压差计液面高差 $h_p \\approx 0.0765\\,\\mathrm{m}$（即 $7.65\\,\\mathrm{cm}$；若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $h_p \\approx 0.0764\\,\\mathrm{m} = 7.64\\,\\mathrm{cm}$）。",
                "analysis": "**1. 列水池液面至测压管连接断面 2—2 的总流能量方程**\n\n以水平管道中心轴线为基准面（$z_1 = H$，$p_1 = 0$，$v_1 \\approx 0$；断面 $2\\text{—}2$ 高程 $z_2 = 0$，相对压强 $p_2$，流速 $v = 3\\,\\mathrm{m/s}$）。取 $\\alpha = 1.0$，计入进口局部水头损失与长 $l$ 管段沿程水头损失：\n\n$$\nH = \\frac{p_2}{\\rho g} + \\frac{v^2}{2g} + \\left(\\zeta + \\lambda\\frac{l}{d}\\right)\\frac{v^2}{2g} = \\frac{p_2}{\\rho g} + \\left(1 + \\zeta + \\lambda\\frac{l}{d}\\right)\\frac{v^2}{2g}\n$$\n\n由此得水池总水头与断面 $2\\text{—}2$ 测压管水头之差为：\n\n$$\nH - \\frac{p_2}{\\rho g} = \\left(1 + \\zeta + \\lambda\\frac{l}{d}\\right)\\frac{v^2}{2g}\n$$\n\n**2. 列 U 形水银压差计等压面方程**\n\n设水平管中心轴线至压差计右侧水—水银交界面的铅垂距离为 $a$，在左侧水—水银交界面（较低液面）作等压面。左侧连水池底部（静水测压管水头等于 $H$），右侧连管内断面 $2\\text{—}2$：\n\n$$\n\\rho g (H + a + h_p) = p_2 + \\rho g a + \\rho_{\\mathrm{m}} g h_p\n$$\n\n化简得：\n\n$$\nH - \\frac{p_2}{\\rho g} = \\frac{\\rho_{\\mathrm{m}} - \\rho}{\\rho} h_p = 12.6\\,h_p\n$$\n\n**3. 联立求解水银液面高差 $h_p$**\n\n已知 $l = 0.75\\,\\mathrm{m}$，$d = 0.025\\,\\mathrm{m}$，$\\lambda = 0.02$，$\\zeta = 0.5$，$v = 3\\,\\mathrm{m/s}$，取 $g = 9.80\\,\\mathrm{m/s^2}$：\n\n$$\n12.6\\,h_p = \\left(1 + 0.5 + 0.02 \\times \\frac{0.75}{0.025}\\right)\\frac{3^2}{2 \\times 9.80} = (1 + 0.5 + 0.6) \\times \\frac{9}{19.60} = 2.1 \\times 0.45918 \\approx 0.96429\\,\\mathrm{m}\n$$\n\n$$\nh_p = \\frac{0.96429}{12.6} \\approx 0.07653\\,\\mathrm{m} \\approx 7.65\\,\\mathrm{cm}\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $12.6\\,h_p = 0.96330\\,\\mathrm{m}$，$h_p = 0.07645\\,\\mathrm{m} \\approx 7.65\\,\\mathrm{cm}$ 或 $7.64\\,\\mathrm{cm}$。）",
                "analysisFigures": [],
                "pitfalls": "本题极易漏掉动能水头项“$1$”而误写成 $\\left(\\zeta + \\lambda\\frac{l}{d}\\right)\\frac{v^2}{2g}$！水银压差计测出的是水池静水面与管内 $2\\text{—}2$ 断面的**测压管水头差** $H - \\frac{p_2}{\\rho g}$，它等于**流速水头 + 水头损失**，系数为 $1 + 0.5 + 0.6 = 2.1$。",
                "chapter": 6,
                "kps": ["短管能量方程", "U形水银压差计", "测压管水头差"],
                "method": "短管出流能量方程与测压管水头线对比法",
                "difficulty": 2,
                "rubric": [
                    {"label": "列水池液面至 2-2 断面能量方程，正确写出 H - p2/(ρg) = (1 + ζ + λl/d)·v²/(2g)", "pts": 5},
                    {"label": "列 U 形水银压差计等压面方程，导出 H - p2/(ρg) = 12.6·hp", "pts": 4},
                    {"label": "联立代入数值准确解得水银液面高差 hp ≈ 0.0765 m（7.65 cm）", "pts": 3}
                ]
            },
            {
                "id": "yzu-849-2016-12",
                "year": 2016,
                "no": 12,
                "type": "calc",
                "score": 15,
                "title": "水箱水平出流直管段管壁所受水流水平总作用力计算",
                "stem": "一水平放置的水管从水箱引水，如图所示。已知水箱作用水头 $H = 4.5\\,\\mathrm{m}$，管径 $d = 20\\,\\mathrm{cm}$，由 $1\\text{—}1$ 断面至 $2\\text{—}2$ 断面的能量损失 $h_{w1} = 0.6\\frac{v^2}{2g}$，$2\\text{—}2$ 断面至 $3\\text{—}3$ 断面的能量损失 $h_{w2} = 0.4\\frac{v^2}{2g}$，$v$ 为管的断面平均流速。试求 $2\\text{—}2$、$3\\text{—}3$ 断面间的管壁所受的水平总作用力。",
                "note": "",
                "figures": [
                    {"src": "figures/q12_orig.png", "caption": "题 12 图　水箱水平引水管与 2-2、3-3 控制断面"}
                ],
                "shortAnswer": "F ≈ 277.1 N，方向水平向右（取 g = 9.81 m/s² 为 277.4 N）。",
                "judgeAnswer": None,
                "answer": "$2\\text{—}2$、$3\\text{—}3$ 断面间的管壁所受水流的水平总作用力大小为 $F \\approx 277.1\\,\\mathrm{N}$，方向**水平向右**（与水流方向一致；管壁对水流的水平摩阻力 $N_x = 277.1\\,\\mathrm{N}$ 方向水平向左。若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $F \\approx 277.4\\,\\mathrm{N}$）。",
                "analysis": "**1. 列能量方程求流速水头 $\\frac{v^2}{2g}$ 与断面 $2\\text{—}2$ 压强 $p_2$（见解图 12）**\n\n以水平管轴线 $0\\text{—}0$ 为基准面（$z_1 = H = 4.5\\,\\mathrm{m}$，$p_1 = 0$，$v_1 \\approx 0$；出口 $3\\text{—}3$ 自由射入大气，$z_3 = 0$，$p_3 = 0$，$v_3 = v$）。列 $1\\text{—}1$ 至 $3\\text{—}3$ 总流能量方程（取 $\\alpha = 1.0$）：\n\n$$\nH = \\frac{v^2}{2g} + h_{w1} + h_{w2} = (1 + 0.6 + 0.4)\\frac{v^2}{2g} = 2.0\\,\\frac{v^2}{2g}\n$$\n\n直接解得管内流速水头（与 $g$ 无关！）：\n\n$$\n\\frac{v^2}{2g} = \\frac{H}{2.0} = \\frac{4.5}{2.0} = 2.25\\,\\mathrm{m} \\implies v = \\sqrt{2 \\times 9.80 \\times 2.25} \\approx 6.6408\\,\\mathrm{m/s}\n$$\n\n再对等径直管段 $2\\text{—}2$ 与 $3\\text{—}3$（$z_2 = z_3 = 0$，$v_2 = v_3 = v$，$p_3 = 0$）列能量方程：\n\n$$\n\\frac{p_2}{\\rho g} = h_{w2} = 0.4\\,\\frac{v^2}{2g} = 0.4 \\times 2.25 = 0.90\\,\\mathrm{m}\n$$\n\n（亦可由 $1\\text{—}1$ 至 $2\\text{—}2$ 得 $\\frac{p_2}{\\rho g} = 4.5 - 1.6 \\times 2.25 = 0.90\\,\\mathrm{m}$，完全一致！）\n\n取 $g = 9.80\\,\\mathrm{m/s^2}$，得 $2\\text{—}2$ 断面相对压强：\n\n$$\np_2 = \\rho g \\times 0.90 = 1000 \\times 9.80 \\times 0.90 = 8820\\,\\mathrm{Pa} = 8.82\\,\\mathrm{kPa}\n$$\n\n**2. 取 $2\\text{—}2$ 至 $3\\text{—}3$ 管内水体为控制体列水平动量方程**\n\n以水流方向（水平向右）为 $+x$ 方向，设管壁对控制体水流的水平总阻力 $N_x$ 方向**水平向左**。因 $2\\text{—}2$ 至 $3\\text{—}3$ 为等径水平直管，$v_2 = v_3$（动量变化率为零），且出口 $p_3 = 0$（$P_3 = 0$），故动量方程简化为：\n\n$$\nP_2 - N_x = \\rho Q (v_3 - v_2) = 0 \\implies N_x = P_2 = p_2 A\n$$\n\n代入管径 $d = 20\\,\\mathrm{cm} = 0.20\\,\\mathrm{m}$：\n\n$$\nN_x = 8820 \\times \\frac{\\pi}{4} \\times 0.20^2 = 8820 \\times 0.0314159 \\approx 277.09\\,\\mathrm{N} \\approx 277.1\\,\\mathrm{N} \\quad (\\text{管壁对水流，水平向左})\n$$\n\n**3. 由牛顿第三定律给出管壁所受水平总作用力**\n\n水流对 $2\\text{—}2$、$3\\text{—}3$ 间管壁的水平总作用力 $F$ 与 $N_x$ 大小相等、方向相反：\n\n$$\nF = 277.1\\,\\mathrm{N} \\quad (\\text{方向水平向右})\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $p_2 = 8829\\,\\mathrm{Pa}$，$F = 277.37\\,\\mathrm{N} \\approx 277.4\\,\\mathrm{N}$。）",
                "analysisFigures": [
                    {"src": "figures/q12_sol.png", "caption": "解图 12　2—2 至 3—3 管段水头线与动量控制体受力分析图"}
                ],
                "pitfalls": "1. 直接保留整体 $\\frac{v^2}{2g} = 2.25\\,\\mathrm{m}$ 代入求 $\\frac{p_2}{\\rho g} = 0.90\\,\\mathrm{m}$ 既快又无任何中间舍入误差！\n2. 审清题干所问对象是“**管壁所受的**水平总作用力”，而非题图中标注的“管壁对水流的阻力 $N_x$”——水流拖曳管壁，故管壁所受作用力方向必然**水平向右**！",
                "chapter": 3,
                "kps": ["恒定总流能量方程", "恒定总流动量方程", "等径管壁切向拖曳力"],
                "method": "能量方程求压强+控制体动量方程求反力",
                "difficulty": 2,
                "rubric": [
                    {"label": "列 1-1 至 3-3 能量方程求出流速水头 v²/(2g) = 2.25 m（或流速 v ≈ 6.64 m/s）", "pts": 5},
                    {"label": "列 2-2 至 3-3（或 1-1 至 2-2）能量方程准确求得 p2/(ρg) = 0.90 m，p2 = 8.82 kPa", "pts": 5},
                    {"label": "列 2-2 至 3-3 动量方程得 Nx = p2A ≈ 277.1 N，并由牛顿第三定律指明管壁受力 277.1 N、方向水平向右", "pts": 5}
                ]
            },
            {
                "id": "yzu-849-2016-13",
                "year": 2016,
                "no": 13,
                "type": "calc",
                "score": 12,
                "title": "三测压管等径参考段消元法测定蝶阀局部阻力系数",
                "stem": "测定一蝶阀的局部阻力系数装置如图所示。在蝶阀的上、下游装设三个测压管，其间距 $l_1 = 1\\,\\mathrm{m}$，$l_2 = 2\\,\\mathrm{m}$。若圆管直径 $d = 50\\,\\mathrm{mm}$，实测 $\\nabla_1 = 150\\,\\mathrm{cm}$，$\\nabla_2 = 125\\,\\mathrm{cm}$，$\\nabla_3 = 40\\,\\mathrm{cm}$，流速 $v = 3\\,\\mathrm{m/s}$，试求蝶阀的局部阻力系数值。",
                "note": "",
                "figures": [
                    {"src": "figures/q13_orig.png", "caption": "题 13 图　三测压管测定蝶阀局部阻力系数实验装置"}
                ],
                "shortAnswer": "ζ ≈ 0.762（取 g = 9.80 m/s²；取 g = 9.81 m/s² 为 0.763）。",
                "judgeAnswer": None,
                "answer": "蝶阀的局部阻力系数 $\\zeta \\approx 0.762$（若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $\\zeta = 0.763$）。",
                "analysis": "**1. 利用上游纯直管参考段 $1\\text{—}2$ 确定单位管长沿程水头损失**\n\n观察题 13 图，测压管 $1$ 与测压管 $2$ 之间为长度 $l_1 = 1\\,\\mathrm{m}$ 的纯等径直管（不含蝶阀），故两测压管液面高差全部消耗于该段的沿程水头损失：\n\n$$\nh_{f,1\\text{-}2} = \\nabla_1 - \\nabla_2 = 1.50 - 1.25 = 0.25\\,\\mathrm{m}\n$$\n\n由此可得直管水力坡度 $J = \\frac{h_{f,1\\text{-}2}}{l_1} = 0.25$（对应沿程阻力系数 $\\lambda = \\frac{2g d J}{v^2} = \\frac{2 \\times 9.80 \\times 0.05 \\times 0.25}{9} \\approx 0.02722$）。\n\n**2. 扣除 $2\\text{—}3$ 段沿程损失求蝶阀局部水头损失 $h_j$**\n\n测压管 $2$ 与测压管 $3$ 之间管长 $l_2 = 2\\,\\mathrm{m}$，且包含蝶阀在内。因全管等径等流速，该段总水头损失等于测压管液面高差：\n\n$$\nh_{w,2\\text{-}3} = \\nabla_2 - \\nabla_3 = 1.25 - 0.40 = 0.85\\,\\mathrm{m}\n$$\n\n其中长度为 $l_2 = 2\\,\\mathrm{m}$ 的沿程水头损失为 $1\\text{—}2$ 段（$l_1 = 1\\,\\mathrm{m}$）的 $2$ 倍：\n\n$$\nh_{f,2\\text{-}3} = \\frac{l_2}{l_1} h_{f,1\\text{-}2} = \\frac{2}{1} \\times 0.25 = 0.50\\,\\mathrm{m}\n$$\n\n因此，蝶阀的净局部水头损失（精确值，无任何中间截位误差）：\n\n$$\nh_j = h_{w,2\\text{-}3} - h_{f,2\\text{-}3} = 0.85 - 0.50 = 0.35\\,\\mathrm{m}\n$$\n\n**3. 计算蝶阀局部阻力系数 $\\zeta$**\n\n已知流速 $v = 3\\,\\mathrm{m/s}$，取 $g = 9.80\\,\\mathrm{m/s^2}$：\n\n$$\n\\zeta = \\frac{h_j}{v^2/(2g)} = \\frac{0.35 \\times 2 \\times 9.80}{3^2} = \\frac{6.86}{9} \\approx 0.7622 \\approx 0.762\n$$\n\n（注：若取 $g = 9.81\\,\\mathrm{m/s^2}$，则 $\\zeta = \\frac{0.35 \\times 2 \\times 9.81}{9} = 0.7630 = 0.763$。）",
                "analysisFigures": [],
                "pitfalls": "先求 $\\lambda$ 再四舍五入（如截成 $\\lambda \\approx 0.027$）回代会导致显著的放大误差（误算成 $0.773$ 以上）！直接利用等径参考段比例 $h_{f,2\\text{-}3} = \\frac{l_2}{l_1} h_{f,1\\text{-}2} = 0.50\\,\\mathrm{m}$ 消去 $\\lambda$，一步得出精确值 $h_j = 0.35\\,\\mathrm{m}$ 既快又零误差！",
                "chapter": 4,
                "kps": ["局部阻力系数测定", "沿程与局部水头损失分离", "测压管水头差"],
                "method": "等径参考段消去沿程损失测局部阻力系数法",
                "difficulty": 2,
                "rubric": [
                    {"label": "由 1-2 纯直管段求得沿程损失 hf,1-2 = 0.25 m（或水力坡度 J = 0.25、λ ≈ 0.0272）", "pts": 4},
                    {"label": "由 2-3 段总水头差 0.85 m 扣除沿程损失 hf,2-3 = 0.50 m，准确求得蝶阀局部损失 hj = 0.35 m", "pts": 4},
                    {"label": "代入局部损失公式 hj = ζ·v²/(2g) 准确求得 ζ ≈ 0.762（取 g=9.81 为 0.763）", "pts": 4}
                ]
            },
            {
                "id": "yzu-849-2016-14",
                "year": 2016,
                "no": 14,
                "type": "calc",
                "score": 10,
                "title": "梯形断面土渠明渠均匀流流速与流量计算",
                "stem": "一梯形土渠，按均匀流设计。已知水深 $h$ 为 $1.2\\,\\mathrm{m}$，底宽 $b$ 为 $2.4\\,\\mathrm{m}$，边坡系数 $m$ 为 $1.5$，粗糙系数 $n$ 为 $0.025$，底坡 $i$ 为 $0.0016$。求流速 $v$ 和流量 $Q$。",
                "note": "",
                "figures": [],
                "shortAnswer": "v ≈ 1.32 m/s，Q ≈ 6.65 m³/s。",
                "judgeAnswer": None,
                "answer": "渠道断面平均流速 $v \\approx 1.32\\,\\mathrm{m/s}$，通过流量 $Q \\approx 6.65\\,\\mathrm{m^3/s}$。",
                "analysis": "**1. 计算梯形断面水力要素**\n\n已知底宽 $b = 2.4\\,\\mathrm{m}$，水深 $h = 1.2\\,\\mathrm{m}$，边坡系数 $m = 1.5$：\n- 过水断面面积：\n\n$$\nA = (b + m h) h = (2.4 + 1.5 \\times 1.2) \\times 1.2 = 4.2 \\times 1.2 = 5.04\\,\\mathrm{m^2}\n$$\n\n- 湿周：\n\n$$\n\\chi = b + 2h\\sqrt{1 + m^2} = 2.4 + 2 \\times 1.2 \\times \\sqrt{1 + 1.5^2} = 2.4 + 2.4\\sqrt{3.25} \\approx 6.7267\\,\\mathrm{m}\n$$\n\n- 水力半径：\n\n$$\nR = \\frac{A}{\\chi} = \\frac{5.04}{6.7267} \\approx 0.74926\\,\\mathrm{m}\n$$\n\n**2. 应用谢才—曼宁公式求流速 $v$ 与流量 $Q$**\n\n粗糙系数 $n = 0.025$，底坡 $i = 0.0016$（$\\sqrt{i} = 0.04$）：\n\n$$\nC = \\frac{1}{n} R^{1/6} = \\frac{1}{0.025} \\times 0.74926^{1/6} \\approx 38.128\\,\\mathrm{m^{1/2}/s}\n$$\n\n$$\nv = C\\sqrt{R i} = 38.128 \\times \\sqrt{0.74926 \\times 0.0016} \\approx 1.3199\\,\\mathrm{m/s} \\approx 1.32\\,\\mathrm{m/s}\n$$\n\n$$\nQ = v A = 1.3199 \\times 5.04 \\approx 6.652\\,\\mathrm{m^3/s} \\approx 6.65\\,\\mathrm{m^3/s}\n$$",
                "analysisFigures": [],
                "pitfalls": "注意梯形湿周公式中的斜坡长度系数是 $\\sqrt{1 + m^2} = \\sqrt{3.25} \\approx 1.8028$，切勿漏掉平方根或少乘两侧的系数 $2$。",
                "chapter": 7,
                "kps": ["梯形明渠水力要素", "谢才-曼宁公式"],
                "method": "谢才—曼宁公式明渠均匀流水力计算法",
                "difficulty": 1,
                "rubric": [
                    {"label": "计算梯形过水面积 A = 5.04 m²、湿周 χ ≈ 6.727 m 及水力半径 R ≈ 0.749 m", "pts": 4},
                    {"label": "代入曼宁公式求得谢才系数 C ≈ 38.13、流速 v ≈ 1.32 m/s 及流量 Q ≈ 6.65 m³/s", "pts": 6}
                ]
            },
            {
                "id": "yzu-849-2016-15",
                "year": 2016,
                "no": 15,
                "type": "calc",
                "score": 10,
                "title": "由不可压缩平面势流连续性定参及两点压强差计算",
                "stem": "已知平面流动的流速势函数 $\\varphi = 0.04 x^3 + a x y^2$，$x$、$y$ 单位为 $\\mathrm{m}$，$\\varphi$ 的单位为 $\\mathrm{m^2/s}$，试求：\n\n（1）常数 $a$；\n\n（2）点 $A(0,0)$ 和点 $B(3,4)$ 间的压强差，设流体的密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$。",
                "note": "",
                "figures": [],
                "shortAnswer": "（1）a = -0.12；（2）pA - pB = 4500 Pa（4.5 kPa）。",
                "judgeAnswer": None,
                "answer": "（1）常数 $a = -0.12$；\n\n（2）水平平面势流中点 $A(0,0)$ 与点 $B(3,4)$ 间的压强差 $p_A - p_B = 4500\\,\\mathrm{Pa} = 4.5\\,\\mathrm{kPa}$。",
                "analysis": "**（1）利用拉普拉斯方程（连续性方程）确定常数 $a$**\n\n由流速势函数 $\\varphi = 0.04 x^3 + a x y^2$ 求平面流速分量：\n\n$$\nu_x = \\frac{\\partial \\varphi}{\\partial x} = 0.12 x^2 + a y^2, \\qquad u_y = \\frac{\\partial \\varphi}{\\partial y} = 2 a x y\n$$\n\n不可压缩平面流动必满足连续性方程 $\\frac{\\partial u_x}{\\partial x} + \\frac{\\partial u_y}{\\partial y} = 0$（即 $\\nabla^2 \\varphi = 0$）：\n\n$$\n\\frac{\\partial^2 \\varphi}{\\partial x^2} + \\frac{\\partial^2 \\varphi}{\\partial y^2} = 0.24 x + 2 a x = (0.24 + 2a) x = 0\n$$\n\n要使上式在整个流场内恒成立，必有：\n\n$$\n0.24 + 2a = 0 \\implies a = -0.12\n$$\n\n**（2）应用定常无旋势流伯努利方程求 $A$、$B$ 两点压强差**\n\n将 $a = -0.12$ 代入速度场得 $u_x = 0.12(x^2 - y^2)$，$u_y = -0.24 x y$。分别计算 $A(0,0)$ 与 $B(3,4)$ 处的合流速：\n- 点 $A(0,0)$：$u_{xA} = 0$，$u_{yA} = 0 \\implies v_A = 0\\,\\mathrm{m/s}$；\n- 点 $B(3,4)$：\n\n$$\nu_{xB} = 0.12 \\times (3^2 - 4^2) = 0.12 \\times (-7) = -0.84\\,\\mathrm{m/s}\n$$\n\n$$\nu_{yB} = -0.24 \\times 3 \\times 4 = -2.88\\,\\mathrm{m/s}\n$$\n\n$$\nv_B = \\sqrt{(-0.84)^2 + (-2.88)^2} = \\sqrt{0.7056 + 8.2944} = \\sqrt{9.00} = 3.00\\,\\mathrm{m/s}\n$$\n\n该流动为定常不可压缩无旋势流，伯努利常数在整个流场中处处相同；对水平平面流（$z_A = z_B$），列 $A$、$B$ 两点伯努利方程：\n\n$$\n\\frac{p_A}{\\rho g} + \\frac{v_A^2}{2g} = \\frac{p_B}{\\rho g} + \\frac{v_B^2}{2g} \\implies p_A - p_B = \\frac{1}{2}\\rho (v_B^2 - v_A^2)\n$$\n\n代入 $\\rho = 1000\\,\\mathrm{kg/m^3}$，$v_A = 0$，$v_B = 3.00\\,\\mathrm{m/s}$：\n\n$$\np_A - p_B = \\frac{1}{2} \\times 1000 \\times (3.00^2 - 0) = 4500\\,\\mathrm{Pa} = 4.5\\,\\mathrm{kPa}\n$$",
                "analysisFigures": [],
                "pitfalls": "1. 计算压强差 $p_A - p_B = \\frac{1}{2}\\rho(v_B^2 - v_A^2)$ 的国际标准单位为 **$\\mathrm{Pa}$（即 $\\mathrm{N/m^2}$）**，切勿错写成流速势单位 $\\mathrm{m^2/s}$！\n2. 仅当流动为**无旋势流**时，伯努利方程才适用于流场中**任意两点**（不必位于同一条流线上）。",
                "chapter": 5,
                "kps": ["拉普拉斯方程", "势流伯努利方程", "流速势函数"],
                "method": "拉普拉斯方程定参数与势流伯努利求压差法",
                "difficulty": 2,
                "rubric": [
                    {"label": "（1）对 φ 求二阶偏导代入不可压缩连续性方程 ∇²φ = 0，解得常数 a = -0.12", "pts": 4},
                    {"label": "（2）算得 A(0,0) 流速 vA = 0 与 B(3,4) 流速 vB = √((-0.84)² + (-2.88)²) = 3.0 m/s", "pts": 3},
                    {"label": "（2）应用水平定常无旋流伯努利方程准确求得压强差 pA - pB = 4500 Pa（4.5 kPa）", "pts": 3}
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

    # 1. Save standardized JSON in `扬州大学已整理数据/<year>/<year>.json`
    pack_json_path = pack_dir / f"{year}.json"
    pack_json_path.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. Convert figures to WebP (`quality=90, method=5`) and rewrite `src` for web JSON
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
    print(f"[{year}] Wrote pack JSON ({pack_json_path.relative_to(ROOT)}) & web JSON ({web_json_path.relative_to(ROOT)}) with {fig_count} WebP figures.")


def main():
    extract_stem_figures()

    fig_2017 = PACK_ROOT / "2017" / "figures"
    draw_2017_q06_sol(fig_2017)
    draw_2017_q08_sol(fig_2017)
    draw_2017_q10_sol(fig_2017)
    draw_2017_q11_sol(fig_2017)
    draw_2017_q14_sol(fig_2017)
    print("[2017] Drew 5 matplotlib solution figures.")

    fig_2016 = PACK_ROOT / "2016" / "figures"
    draw_2016_q02_sol(fig_2016)
    draw_2016_q03_sol(fig_2016)
    draw_2016_q05_sol(fig_2016)
    draw_2016_q08_sol(fig_2016)
    draw_2016_q10_sol(fig_2016)
    draw_2016_q12_sol(fig_2016)
    print("[2016] Drew 6 matplotlib solution figures.")

    export_pack_and_web(build_2017_paper())
    export_pack_and_web(build_2016_paper())


if __name__ == "__main__":
    main()
