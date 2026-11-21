# -*- coding: utf-8 -*-
"""
Lightweight, reusable engineering schematic toolkit for rapid textbook-quality
exam diagram redrawing (matplotlib Agg + numpy + PIL -> archived PNG + WebP).
"""

from __future__ import annotations

import math
import shutil
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Standard textbook color palette (clean monochrome + subtle fluid/concrete tints)
INK = "#111827"
AUX = "#334155"
WATER = "#e0f2fe"
OIL = "#fef3c7"
MERCURY = "#334155"
CONCRETE = "#e2e8f0"


def init_style() -> None:
    """Configure fast, consistent matplotlib typography and math settings."""
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["mathtext.fontset"] = "dejavusans"
    plt.rcParams["font.size"] = 10.5


def new_canvas(
    w: float = 6.2,
    h: float = 3.8,
    xlim: tuple[float, float] = (0.0, 10.0),
    ylim: tuple[float, float] = (0.0, 6.0),
    equal: bool = True,
):
    """Create a borderless white canvas ready for engineering schematics."""
    init_style()
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    if equal:
        ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    return fig, ax


def water_surface(
    ax,
    x0: float,
    x1: float,
    y: float,
    mark_x: float | None = None,
    size: float = 0.22,
    ls: str = "-",
    lw: float = 1.6,
    color: str = INK,
    label: str | None = None,
    label_pos: str = "top",
    fontsize: float = 10.5,
) -> None:
    """Draw a free water surface line with standard inverted triangle ▽ and ripples."""
    ax.plot([x0, x1], [y, y], ls=ls, lw=lw, color=color, zorder=4)
    mx = 0.5 * (x0 + x1) if mark_x is None else mark_x
    tw = size * 0.58
    th = size * 0.90
    ax.plot(
        [mx, mx - tw, mx + tw, mx],
        [y, y + th, y + th, y],
        color=color,
        lw=max(1.0, lw * 0.78),
        zorder=5,
    )
    ax.plot([mx - size * 0.72, mx + size * 0.72], [y - size * 0.34, y - size * 0.34], color=color, lw=1.0, zorder=4)
    ax.plot([mx - size * 0.42, mx + size * 0.42], [y - size * 0.64, y - size * 0.64], color=color, lw=1.0, zorder=4)
    if label:
        dy = th + size * 0.35 if label_pos == "top" else -size * 1.15
        va = "bottom" if label_pos == "top" else "top"
        ax.text(mx, y + dy, label, ha="center", va=va, fontsize=fontsize, color=color)


def ground_hatch(
    ax,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    side: str = "below",
    step: float = 0.28,
    depth: float = 0.18,
    lw: float = 1.8,
    hatch_lw: float = 0.9,
    color: str = INK,
    ls: str = "-",
    flip_angle: bool = False,
) -> None:
    """Draw a solid/dashed wall or bed segment with uniform angled hatch ticks."""
    if lw > 0:
        ax.plot([x0, x1], [y0, y1], color=color, lw=lw, ls=ls, zorder=4)
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return
    tx, ty = dx / length, dy / length
    n1 = (-ty, tx)
    n2 = (ty, -tx)
    if side == "below":
        nx, ny = n1 if n1[1] < n2[1] else n2
    elif side == "above":
        nx, ny = n1 if n1[1] > n2[1] else n2
    elif side == "left":
        nx, ny = n1 if n1[0] < n2[0] else n2
    else:  # "right"
        nx, ny = n1 if n1[0] > n2[0] else n2

    sign_t = -0.68 if flip_angle else 0.68
    n_ticks = max(2, int(length / step))
    ts = np.linspace(0.06, max(0.06, length - 0.06), n_ticks)
    for d in ts:
        bx = x0 + tx * d
        by = y0 + ty * d
        ex = bx + nx * depth + sign_t * tx * depth
        ey = by + ny * depth + sign_t * ty * depth
        ax.plot([bx, ex], [by, ey], color=AUX, lw=hatch_lw, zorder=3)


def concrete_block(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    lw: float = 1.8,
    fill: str = CONCRETE,
    dots: int = 14,
    edge_color: str = INK,
) -> None:
    """Draw a concrete wall/pier/block with deterministic gravel stipple marks."""
    rect = patches.Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge_color, lw=lw, zorder=3)
    ax.add_patch(rect)
    if dots <= 0 or w <= 0 or h <= 0:
        return
    seed = int(abs(x * 131 + y * 57 + w * 29 + h * 17)) % (2**31)
    rng = np.random.default_rng(seed)
    pad_x = min(w * 0.14, 0.18)
    pad_y = min(h * 0.14, 0.18)
    span_x = max(1e-3, w - 2 * pad_x)
    span_y = max(1e-3, h - 2 * pad_y)
    s = min(0.11, min(w, h) * 0.16)
    for i in range(dots):
        cx = x + pad_x + rng.random() * span_x
        cy = y + pad_y + rng.random() * span_y
        if i % 3 == 0:
            ang = rng.random() * 2 * math.pi
            tri = np.array([
                [cx + s * math.cos(ang), cy + s * math.sin(ang)],
                [cx + s * math.cos(ang + 2.1), cy + s * math.sin(ang + 2.1)],
                [cx + s * math.cos(ang + 4.2), cy + s * math.sin(ang + 4.2)],
            ])
            ax.add_patch(patches.Polygon(tri, closed=True, facecolor="none", edgecolor=AUX, lw=0.8, zorder=4))
        else:
            ax.plot(cx, cy, marker="o", markersize=1.6, color=AUX, zorder=4)


def dim_arrow(
    ax,
    p1: Sequence[float],
    p2: Sequence[float],
    label: str = "",
    text_offset: tuple[float, float] = (0.0, 0.0),
    ext_len: float = 0.0,
    ext_dir: tuple[float, float] = (0.0, 0.0),
    both: bool = True,
    fontsize: float = 10.5,
    lw: float = 1.1,
    ha: str = "center",
    va: str = "center",
    color: str = INK,
    bbox_white: bool = False,
) -> None:
    """Draw a dimension arrow with optional witness extension lines and centered label."""
    x1, y1 = p1
    x2, y2 = p2
    if ext_len > 0 and (ext_dir[0] != 0 or ext_dir[1] != 0):
        el = math.hypot(ext_dir[0], ext_dir[1])
        ux, uy = ext_dir[0] / el, ext_dir[1] / el
        for px, py in ((x1, y1), (x2, y2)):
            ax.plot([px, px + ux * ext_len], [py, py + uy * ext_len], color=AUX, lw=0.85, zorder=4)
    style = "<->" if both else "->"
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color, lw=lw, shrinkA=0, shrinkB=0),
        zorder=5,
    )
    if label:
        mx = 0.5 * (x1 + x2) + text_offset[0]
        my = 0.5 * (y1 + y2) + text_offset[1]
        kw = dict(bbox=dict(facecolor="white", edgecolor="none", pad=1.2)) if bbox_white else {}
        ax.text(mx, my, label, fontsize=fontsize, ha=ha, va=va, color=color, zorder=6, **kw)


def section_cut(
    ax,
    p1: Sequence[float],
    p2: Sequence[float],
    label: str = "1",
    fontsize: float = 10.5,
    lw: float = 1.3,
    ls: str = "-.",
    color: str = AUX,
    offset: float = 0.22,
) -> None:
    """Draw a cross-section cut line labeled at both ends."""
    x1, y1 = p1
    x2, y2 = p2
    ax.plot([x1, x2], [y1, y2], ls=ls, lw=lw, color=color, zorder=5)
    dx, dy = x2 - x1, y2 - y1
    d = max(1e-6, math.hypot(dx, dy))
    ux, uy = dx / d, dy / d
    if label:
        ax.text(x1 - ux * offset, y1 - uy * offset, label, fontsize=fontsize, ha="center", va="center", color=INK, zorder=6)
        ax.text(x2 + ux * offset, y2 + uy * offset, label, fontsize=fontsize, ha="center", va="center", color=INK, zorder=6)


def flow_arrow(
    ax,
    p1: Sequence[float],
    p2: Sequence[float],
    label: str = "",
    text_offset: tuple[float, float] = (0.0, 0.20),
    fontsize: float = 11.0,
    lw: float = 1.6,
    color: str = INK,
    ha: str = "center",
    va: str = "center",
) -> None:
    """Draw a clean directional velocity/flow/force arrow."""
    ax.annotate(
        "",
        xy=p2,
        xytext=p1,
        arrowprops=dict(arrowstyle="->", color=color, lw=lw, shrinkA=0, shrinkB=0),
        zorder=6,
    )
    if label:
        mx = 0.5 * (p1[0] + p2[0]) + text_offset[0]
        my = 0.5 * (p1[1] + p2[1]) + text_offset[1]
        ax.text(mx, my, label, fontsize=fontsize, ha=ha, va=va, color=color, zorder=7)


def angle_arc(
    ax,
    vertex: Sequence[float],
    theta1_deg: float,
    theta2_deg: float,
    radius: float = 0.6,
    label: str = "",
    label_r: float | None = None,
    fontsize: float = 10.5,
    lw: float = 1.1,
    color: str = INK,
) -> None:
    """Draw an angle arc and place its label at the bisector angle."""
    vx, vy = vertex
    t1, t2 = theta1_deg % 360.0, theta2_deg % 360.0
    arc = patches.Arc((vx, vy), 2 * radius, 2 * radius, angle=0, theta1=t1, theta2=t2, color=color, lw=lw, zorder=5)
    ax.add_patch(arc)
    if label:
        span = (t2 - t1) % 360.0
        mid_rad = math.radians(t1 + 0.5 * span)
        lr = radius * 1.48 if label_r is None else label_r
        ax.text(vx + lr * math.cos(mid_rad), vy + lr * math.sin(mid_rad), label, fontsize=fontsize, ha="center", va="center", color=color, zorder=6)


def piezometer(
    ax,
    x: float,
    y_conn: float,
    y_top: float,
    y_water: float,
    tube_w: float = 0.18,
    liquid_color: str = WATER,
    mark: bool = True,
    lw: float = 1.4,
    label: str | None = None,
    open_conn: bool = True,
) -> None:
    """Draw a vertical piezometer tube connected at y_conn with liquid column to y_water."""
    hw = tube_w * 0.5
    if y_water > y_conn:
        ax.add_patch(patches.Rectangle((x - hw, y_conn), tube_w, y_water - y_conn, facecolor=liquid_color, edgecolor="none", zorder=2))
    ax.plot([x - hw, x - hw], [y_conn, y_top], color=INK, lw=lw, zorder=5)
    ax.plot([x + hw, x + hw], [y_conn, y_top], color=INK, lw=lw, zorder=5)
    if open_conn:
        ax.plot([x - hw + 0.02, x + hw - 0.02], [y_conn, y_conn], color=liquid_color, lw=lw + 0.8, zorder=4.5)
    ax.plot([x - hw, x + hw], [y_water, y_water], color=INK, lw=1.2, zorder=5)
    if mark:
        sz = max(0.14, tube_w * 0.85)
        ax.plot([x, x - sz * 0.5, x + sz * 0.5, x], [y_water, y_water + sz * 0.8, y_water + sz * 0.8, y_water], color=INK, lw=1.0, zorder=5)
    if label:
        ax.text(x, y_top + 0.14, label, ha="center", va="bottom", fontsize=10, color=INK)


def u_manometer(
    ax,
    x1: float,
    y1_conn: float,
    x2: float,
    y2_conn: float,
    y_bot: float,
    y_m1: float,
    y_m2: float,
    tube_w: float = 0.16,
    mercury_color: str = MERCURY,
    left_fill: str = WATER,
    right_fill: str = WATER,
    lw: float = 1.4,
) -> None:
    """Draw a U-tube manometer whose bottom U-bend reaches y_bot with mercury to y_m1 (left) and y_m2 (right)."""
    hw = tube_w * 0.5
    # Left & right liquid fills above mercury
    if y1_conn > y_m1:
        ax.add_patch(patches.Rectangle((x1 - hw, y_m1), tube_w, y1_conn - y_m1, facecolor=left_fill, edgecolor="none", zorder=2))
    if y2_conn > y_m2:
        ax.add_patch(patches.Rectangle((x2 - hw, y_m2), tube_w, y2_conn - y_m2, facecolor=right_fill, edgecolor="none", zorder=2))

    # Mercury bottom fill (boxy bottom channel + vertical legs for clean geometry)
    ax.add_patch(patches.Rectangle((x1 - hw, y_bot - hw), (x2 - x1) + tube_w, tube_w, facecolor=mercury_color, edgecolor="none", zorder=2.5))
    ax.add_patch(patches.Rectangle((x1 - hw, y_bot - hw), tube_w, y_m1 - (y_bot - hw), facecolor=mercury_color, edgecolor="none", zorder=2.5))
    ax.add_patch(patches.Rectangle((x2 - hw, y_bot - hw), tube_w, y_m2 - (y_bot - hw), facecolor=mercury_color, edgecolor="none", zorder=2.5))

    # Outer and inner tube walls
    ax.plot([x1 - hw, x1 - hw, x2 + hw, x2 + hw], [y1_conn, y_bot - hw, y_bot - hw, y2_conn], color=INK, lw=lw, zorder=5)
    ax.plot([x1 + hw, x1 + hw, x2 - hw, x2 - hw], [y1_conn, y_bot + hw, y_bot + hw, y2_conn], color=INK, lw=lw, zorder=5)


def backup_and_save(
    fig,
    course: str,
    year: int,
    stem: str,
    root: Path,
    archive_base: str = "河海大学已整理数据",
    dpi: int = 160,
    webp_quality: int = 85,
) -> tuple[Path, Path]:
    """
    Idempotently back up original WebP/PNG if not already backed up, then save
    tight-cropped PNG (archive) and WebP (web/public/data) and close the figure.
    """
    webp_path = root / "web" / "public" / "data" / course / "figures" / str(year) / f"{stem}.webp"
    png_path = root / archive_base / str(year) / "figures" / f"{stem}.png"
    backup_dir = root / "assets_src" / "handdrawn_backup" / course / str(year)
    backup_dir.mkdir(parents=True, exist_ok=True)

    bak_webp = backup_dir / f"{stem}.webp"
    bak_png = backup_dir / f"{stem}.png"
    if webp_path.exists() and not bak_webp.exists():
        shutil.copy2(webp_path, bak_webp)
    if png_path.exists() and not bak_png.exists():
        shutil.copy2(png_path, bak_png)

    png_path.parent.mkdir(parents=True, exist_ok=True)
    webp_path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(png_path, dpi=dpi, bbox_inches="tight", pad_inches=0.12, facecolor="white")
    plt.close(fig)

    with Image.open(png_path) as im:
        rgb = im.convert("RGB")
        rgb.save(webp_path, format="WEBP", quality=webp_quality, method=4)

    return png_path, webp_path


def _load_qa_font(size: int, bold: bool = False):
    candidates = (
        [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\msyh.ttc"]
        if bold
        else [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]
    )
    for fp in candidates:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def _fit_rgba_on_white(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    rgba = img.convert("RGBA")
    bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    bg.alpha_composite(rgba)
    rgb = bg.convert("RGB")
    w, h = rgb.size
    scale = min(max_w / max(1, w), max_h / max(1, h))
    return rgb.resize((max(1, int(round(w * scale))), max(1, int(round(h * scale)))), Image.LANCZOS)


def build_qa_sheets(
    pairs: Iterable[tuple[str, Path, Path]],
    out_dir: Path,
    prefix: str = "qa",
    pairs_per_sheet: int = 4,
) -> list[Path]:
    """Build high-res 1600px lossless PNG Before (original backup) vs After (redrawn) QA sheets."""
    items = list(pairs)
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet_paths: list[Path] = []

    sheet_w = 1600
    outer_pad = 22
    row_gap = 18
    header_h = 40
    box_pad = 12
    img_area_h = 360
    row_h = header_h + box_pad * 2 + img_area_h + 10
    col_gap = 18
    col_w = (sheet_w - outer_pad * 2 - col_gap) // 2

    font_title = _load_qa_font(19, bold=True)
    font_tag = _load_qa_font(15, bold=True)
    font_meta = _load_qa_font(13, bold=False)

    for s_idx in range(0, len(items), pairs_per_sheet):
        chunk = items[s_idx : s_idx + pairs_per_sheet]
        sheet_h = outer_pad * 2 + len(chunk) * row_h + max(0, len(chunk) - 1) * row_gap
        sheet = Image.new("RGB", (sheet_w, sheet_h), (241, 245, 249))
        draw = ImageDraw.Draw(sheet)

        for r, (label, orig_p, new_p) in enumerate(chunk):
            ry = outer_pad + r * (row_h + row_gap)
            draw.rounded_rectangle(
                (outer_pad, ry, sheet_w - outer_pad, ry + row_h),
                radius=12,
                fill=(255, 255, 255),
                outline=(203, 213, 225),
                width=2,
            )
            draw.rounded_rectangle((outer_pad, ry, sheet_w - outer_pad, ry + header_h), radius=12, fill=(226, 232, 240))
            draw.rectangle((outer_pad, ry + header_h - 12, sheet_w - outer_pad, ry + header_h), fill=(226, 232, 240))
            draw.text((outer_pad + 14, ry + 9), label, font=font_title, fill=(15, 23, 42))

            orig_dim = ""
            new_dim = ""
            orig_im = Image.open(orig_p) if orig_p and orig_p.exists() else None
            new_im = Image.open(new_p) if new_p and new_p.exists() else None
            if orig_im is not None:
                orig_dim = f"{orig_im.width}×{orig_im.height}"
            if new_im is not None:
                new_dim = f"{new_im.width}×{new_im.height}"
            if orig_dim or new_dim:
                note = f"{orig_dim or '?'} -> {new_dim or '?'}"
                nb = draw.textbbox((0, 0), note, font=font_meta)
                draw.text((sheet_w - outer_pad - 14 - (nb[2] - nb[0]), ry + 12), note, font=font_meta, fill=(71, 85, 105))

            frame_y0 = ry + header_h + box_pad
            frame_y1 = ry + row_h - box_pad
            inner_w = col_w - 24
            inner_h = img_area_h - 14
            for side_idx, (tag, im_obj, tag_bg, tag_fg) in enumerate(
                [
                    ("[ORIG] 原图", orig_im, (254, 226, 226), (153, 27, 27)),
                    ("[NEW] 重绘", new_im, (220, 252, 231), (22, 101, 52)),
                ]
            ):
                fx0 = outer_pad + 10 + side_idx * (col_w + col_gap - 10)
                fx1 = fx0 + col_w - 10
                draw.rounded_rectangle((fx0, frame_y0, fx1, frame_y1), radius=8, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
                draw.rounded_rectangle((fx0 + 8, frame_y0 + 8, fx0 + 114, frame_y0 + 34), radius=6, fill=tag_bg)
                draw.text((fx0 + 16, frame_y0 + 11), tag, font=font_tag, fill=tag_fg)
                if im_obj is not None:
                    fitted = _fit_rgba_on_white(im_obj, inner_w - 8, inner_h - 24)
                    ix = fx0 + ((fx1 - fx0) - fitted.width) // 2
                    iy = frame_y0 + 34 + ((frame_y1 - (frame_y0 + 38)) - fitted.height) // 2
                    sheet.paste(fitted, (ix, iy))
                    im_obj.close()
                else:
                    draw.text((fx0 + 20, frame_y0 + 52), "MISSING FILE", font=font_tag, fill=(200, 0, 0))

        out_p = out_dir / f"{prefix}_{s_idx // pairs_per_sheet + 1}.png"
        sheet.save(out_p, "PNG", optimize=True)
        sheet_paths.append(out_p)

    return sheet_paths
