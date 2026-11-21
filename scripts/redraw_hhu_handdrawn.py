# -*- coding: utf-8 -*-
"""
Batch redraw all 35 hand-drawn / photographed / noisy original exam figures in
`hhu-814` (2017: 14, 2018: 11, 2022: 10) into crisp, faithful schematics.

Usage:
  python scripts/redraw_hhu_handdrawn.py --workers 4 --qa-dir "<scratch>/fig_qa"
  python scripts/redraw_hhu_handdrawn.py --year 2022
  python scripts/redraw_hhu_handdrawn.py --only 2022:3,2018:20
"""

from __future__ import annotations

import argparse
import concurrent.futures
import math
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.patches as patches
import numpy as np

from fig_kit import (
    AUX,
    CONCRETE,
    INK,
    MERCURY,
    OIL,
    WATER,
    angle_arc,
    backup_and_save,
    build_qa_sheets,
    concrete_block,
    dim_arrow,
    flow_arrow,
    ground_hatch,
    new_canvas,
    piezometer,
    section_cut,
    u_manometer,
    water_surface,
)

REGISTRY: dict[tuple[int, int], Callable[[], object]] = {}


def reg(year: int, no: int):
    def deco(fn: Callable[[], object]):
        REGISTRY[(year, no)] = fn
        return fn
    return deco


# ==============================================================================
# 2022 (10 figures)
# ==============================================================================


@reg(2022, 3)
def draw_2022_03():
    fig, ax = new_canvas(5.4, 3.8, (0, 8), (0, 5.6))
    # Inclined wall bottom-left to top-right
    ax.plot([2.2, 6.9], [0.6, 5.0], color=INK, lw=2.2, zorder=4)
    # Top horizontal free water surface line meeting wall at x ≈ 6.05
    ax.plot([1.0, 6.05], [4.2, 4.2], color=INK, lw=1.6, zorder=4)
    # Contact point on wall: t = 0.48 -> (4.46, 2.71)
    cx, cy = 4.46, 2.71
    # Horizontal reference line extending left
    ax.plot([2.1, cx], [cy, cy], color=INK, lw=1.4, zorder=4)
    # Perpendicular normal arrow pointing into wall from upper-left
    ang = math.degrees(math.atan2(4.4, 4.7))  # ~43.1 deg
    nx, ny = math.sin(math.radians(ang)), -math.cos(math.radians(ang))  # into wall (down-right)
    sx, sy = cx - 2.2 * nx, cy - 2.2 * ny
    flow_arrow(ax, (sx, sy), (cx - 0.06 * nx, cy - 0.06 * ny), label=r"$p_n$", text_offset=(0.24, 0.44), fontsize=13, lw=1.9)
    # Angle arc between left horizontal ray (180 deg) and arrow incoming direction (angle ~ 133 deg)
    # Notice arrow vector goes at -47 deg, so incoming ray from contact point toward sx is 133 deg -> span 133..180
    theta_ray = math.degrees(math.atan2(sy - cy, sx - cx)) % 360.0
    angle_arc(ax, (cx, cy), theta_ray, 180.0, radius=0.95, label=r"$\alpha$", label_r=1.34, fontsize=12)
    return fig


@reg(2022, 4)
def draw_2022_04():
    fig, ax = new_canvas(5.4, 4.4, (0, 8.2), (0, 6.6))
    # Tank walls
    tx0, tx1, ty0, ty1 = 1.6, 5.4, 0.7, 5.8
    # Liquid fills
    ax.add_patch(patches.Rectangle((tx0, ty0), tx1 - tx0, 2.5, facecolor="#f1f5f9", edgecolor="none", zorder=1))
    ax.add_patch(patches.Rectangle((tx0, 3.2), tx1 - tx0, 2.0, facecolor=WATER, edgecolor="none", zorder=1))
    # Outer tank frame (open top)
    ax.plot([tx0, tx0, tx1, tx1], [ty1, ty0, ty0, ty1], color=INK, lw=2.0, zorder=4)
    # Liquid surfaces
    water_surface(ax, tx0, tx1, 5.2, mark_x=3.5)
    ax.plot([tx0, tx1], [3.2, 3.2], ls="--", color=INK, lw=1.4, zorder=4)
    # Points A and B
    ax.plot(3.75, 4.35, marker="o", ms=5, color=INK, zorder=5)
    ax.text(3.92, 4.42, r"$A$", fontsize=12, fontweight="bold")
    ax.text(2.45, 4.30, r"$\rho_1$", fontsize=12)
    ax.plot(3.35, 1.85, marker="o", ms=5, color=INK, zorder=5)
    ax.text(3.52, 1.92, r"$B$", fontsize=12, fontweight="bold")
    ax.text(4.35, 2.35, r"$\rho_2$", fontsize=12)
    # Side piezometer connected into lower layer rho_2
    px, py_c, py_t, py_w = 6.3, 1.8, 5.0, 4.25
    ax.add_patch(patches.Rectangle((tx1, py_c - 0.12), px - tx1 + 0.12, 0.24, facecolor="#f1f5f9", edgecolor="none", zorder=2))
    ax.plot([tx1, px + 0.12, px + 0.12], [py_c - 0.12, py_c - 0.12, py_t], color=INK, lw=1.6, zorder=4)
    ax.plot([tx1, px - 0.12, px - 0.12], [py_c + 0.12, py_c + 0.12, py_t], color=INK, lw=1.6, zorder=4)
    ax.add_patch(patches.Rectangle((px - 0.12, py_c + 0.10), 0.24, py_w - py_c - 0.10, facecolor="#f1f5f9", edgecolor="none", zorder=2))
    water_surface(ax, px - 0.12, px + 0.12, py_w, mark_x=px, size=0.14, lw=1.3)
    return fig


@reg(2022, 13)
def draw_2022_13():
    fig, ax = new_canvas(6.8, 3.6, (0, 12), (0, 5.8))
    # Left panel: flat wall impact
    ground_hatch(ax, 4.2, 0.7, 4.2, 5.0, side="right", step=0.30, depth=0.20, lw=2.0)
    # Horizontal jet pipe
    ax.add_patch(patches.Rectangle((0.6, 2.65), 3.35, 0.40, facecolor=WATER, edgecolor="none", zorder=2))
    ax.plot([0.6, 3.95], [3.05, 3.05], color=INK, lw=1.7, zorder=4)
    ax.plot([0.6, 3.95], [2.65, 2.65], color=INK, lw=1.7, zorder=4)
    # Splitting along wall
    ax.plot([3.95, 3.95], [3.05, 4.85], color=INK, lw=1.5, zorder=4)
    ax.plot([3.95, 3.95], [2.65, 0.85], color=INK, lw=1.5, zorder=4)
    flow_arrow(ax, (1.1, 2.85), (2.7, 2.85), label=r"$Q_1$", text_offset=(0, 0.42), fontsize=12)
    flow_arrow(ax, (4.06, 3.25), (4.06, 4.55), lw=1.4)
    flow_arrow(ax, (4.06, 2.45), (4.06, 1.15), lw=1.4)

    # Right panel: curved symmetric vane deflecting at 135 deg
    vx_c, vy_c, r_v = 9.0, 2.85, 1.85
    th = np.linspace(-math.radians(65), math.radians(65), 80)
    ax.plot(vx_c + r_v * np.cos(th), vy_c + r_v * np.sin(th), color=INK, lw=2.2, zorder=4)
    ax.plot(vx_c + (r_v + 0.14) * np.cos(th), vy_c + (r_v + 0.14) * np.sin(th), color=AUX, lw=1.2, zorder=4)
    # Incoming jet Q_2
    ax.add_patch(patches.Rectangle((6.3, 2.68), 4.2, 0.34, facecolor=WATER, edgecolor="none", zorder=2))
    ax.plot([6.3, 10.65], [3.02, 3.02], color=INK, lw=1.6, zorder=4)
    ax.plot([6.3, 10.65], [2.68, 2.68], color=INK, lw=1.6, zorder=4)
    flow_arrow(ax, (6.7, 2.85), (8.2, 2.85), label=r"$Q_2$", text_offset=(0, 0.42), fontsize=12)
    # Deflected water sheets & 135 deg indicator
    th_up = np.linspace(0, math.radians(58), 40)
    ax.plot(vx_c + (r_v - 0.22) * np.cos(th_up), vy_c + (r_v - 0.22) * np.sin(th_up), color=INK, lw=1.2, zorder=4)
    ax.plot(vx_c + (r_v - 0.22) * np.cos(-th_up), vy_c + (r_v - 0.22) * np.sin(-th_up), color=INK, lw=1.2, zorder=4)
    flow_arrow(ax, (10.35, 3.65), (9.55, 4.45), lw=1.5)
    flow_arrow(ax, (10.35, 2.05), (9.55, 1.25), lw=1.5)
    # Dashed horizontal extension + 135 deg arc
    ax.plot([9.6, 11.4], [4.42, 4.42], ls="--", color=AUX, lw=1.0, zorder=3)
    ax.text(8.75, 4.85, r"$135^{\circ}$", fontsize=11.5)
    return fig


@reg(2022, 15)
def draw_2022_15():
    fig, ax = new_canvas(6.4, 4.4, (0, 10.5), (0, 7.2))
    # Inclined pipe from (1.2, 2.8) upward-right at 24 deg
    ang = math.radians(24)
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    pw = 0.65
    p_len = 6.8
    x0, y0 = 1.4, 2.8
    # Polygon fill
    p0 = (x0, y0)
    p1 = (x0 + p_len * ca, y0 + p_len * sa)
    poly = np.array([
        [p0[0] + 0.5 * pw * nx, p0[1] + 0.5 * pw * ny],
        [p1[0] + 0.5 * pw * nx, p1[1] + 0.5 * pw * ny],
        [p1[0] - 0.5 * pw * nx, p1[1] - 0.5 * pw * ny],
        [p0[0] - 0.5 * pw * nx, p0[1] - 0.5 * pw * ny],
    ])
    ax.add_patch(patches.Polygon(poly, closed=True, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot([poly[0, 0], poly[1, 0]], [poly[0, 1], poly[1, 1]], color=INK, lw=1.8, zorder=4)
    ax.plot([poly[3, 0], poly[2, 0]], [poly[3, 1], poly[2, 1]], color=INK, lw=1.8, zorder=4)
    # Centerline & flow arrow
    ax.plot([x0, p1[0]], [y0, p1[1]], ls="-.", color=AUX, lw=0.9, zorder=3)
    flow_arrow(ax, (x0 + 0.4 * ca, y0 + 0.4 * sa), (x0 + 1.45 * ca, y0 + 1.45 * sa), lw=1.6)
    ax.text(x0 + 0.65, y0 - 0.12, "水", fontsize=11, color=INK)

    # Taps A and B along pipe
    sA, sB = 2.0, 5.2
    ax_pt = (x0 + sA * ca, y0 + sA * sa)
    bx_pt = (x0 + sB * ca, y0 + sB * sa)
    ax.plot([ax_pt[0], bx_pt[0]], [ax_pt[1], bx_pt[1]], "o", ms=4.5, color=INK, zorder=6)
    ax.text(ax_pt[0] - 0.25, ax_pt[1] + 0.12, r"$A$", fontsize=11.5, fontweight="bold")
    ax.text(bx_pt[0] - 0.25, bx_pt[1] + 0.12, r"$B$", fontsize=11.5, fontweight="bold")

    # Dimension L_AB along top
    off = 1.05
    dA = (ax_pt[0] + off * nx, ax_pt[1] + off * ny)
    dB = (bx_pt[0] + off * nx, bx_pt[1] + off * ny)
    ax.plot([ax_pt[0] + 0.4 * nx, dA[0] + 0.1 * nx], [ax_pt[1] + 0.4 * ny, dA[1] + 0.1 * ny], color=AUX, lw=0.9)
    ax.plot([bx_pt[0] + 0.4 * nx, dB[0] + 0.1 * nx], [bx_pt[1] + 0.4 * ny, dB[1] + 0.1 * ny], color=AUX, lw=0.9)
    dim_arrow(ax, dA, dB, label=r"$L_{AB}=20\,\mathrm{m}$", text_offset=(-0.35, 0.55), fontsize=10.5)

    # Diameter D on upper right end
    e_top = (x0 + 6.4 * ca + 0.5 * pw * nx, y0 + 6.4 * sa + 0.5 * pw * ny)
    e_bot = (x0 + 6.4 * ca - 0.5 * pw * nx, y0 + 6.4 * sa - 0.5 * pw * ny)
    t_off = 0.65
    dim_arrow(
        ax,
        (e_bot[0] + t_off * ca, e_bot[1] + t_off * sa),
        (e_top[0] + t_off * ca, e_top[1] + t_off * sa),
        label=r"$D=0.1\,\mathrm{m}$",
        text_offset=(0.95, 0.05),
        fontsize=10.5,
    )

    # Vertical Delta z between A and B
    ax.plot([ax_pt[0], 7.4], [ax_pt[1], ax_pt[1]], ls=":", color=AUX, lw=1.0)
    ax.plot([bx_pt[0], 7.4], [bx_pt[1], bx_pt[1]], ls=":", color=AUX, lw=1.0)
    dim_arrow(ax, (7.1, ax_pt[1]), (7.1, bx_pt[1]), label=r"$\Delta z=0.5\,\mathrm{m}$", text_offset=(1.15, 0.0), fontsize=10.5)

    # U-tube mercury manometer hanging down from A and B (left lower, right higher)
    u_manometer(
        ax,
        ax_pt[0], ax_pt[1] - 0.34,
        bx_pt[0], bx_pt[1] - 0.34,
        y_bot=0.75,
        y_m1=1.35,
        y_m2=2.25,
        tube_w=0.20,
    )
    ax.plot([ax_pt[0], ax_pt[0]], [ax_pt[1], ax_pt[1] - 0.34], color=INK, lw=1.2)
    ax.plot([bx_pt[0], bx_pt[0]], [bx_pt[1], bx_pt[1] - 0.34], color=INK, lw=1.2)
    ax.plot([ax_pt[0] + 0.12, 7.2], [1.35, 1.35], ls=":", color=AUX, lw=1.0)
    ax.plot([bx_pt[0] + 0.12, 7.2], [2.25, 2.25], ls=":", color=AUX, lw=1.0)
    dim_arrow(ax, (6.95, 1.35), (6.95, 2.25), label=r"$\Delta h=0.17\,\mathrm{m}$", text_offset=(1.18, 0.0), fontsize=10.5)
    ax.text(4.65, 0.32, r"$\rho_m$", fontsize=11.5)
    return fig


@reg(2022, 17)
def draw_2022_17():
    fig, ax = new_canvas(6.4, 4.2, (0, 10.6), (0, 6.8))
    # Shared water level line on right/overall top
    water_surface(ax, 1.0, 7.6, 5.75, mark_x=6.8)
    # Left: front view of rectangular gate
    gx0, gx1, gy0, gy1 = 1.6, 4.0, 0.8, 4.65
    ax.add_patch(patches.Rectangle((gx0, gy0), gx1 - gx0, gy1 - gy0, facecolor=WATER, edgecolor=INK, lw=2.0, zorder=3))
    # Height H on left
    dim_arrow(ax, (1.1, gy0), (1.1, gy1), label=r"$H$", text_offset=(-0.28, 0), ext_len=0.35, ext_dir=(1, 0), fontsize=11.5)
    # Centroid C & H/2
    cy_mid = 0.5 * (gy0 + gy1)
    ax.plot(2.8, cy_mid, "o", ms=4.5, color=INK, zorder=5)
    ax.text(2.92, cy_mid + 0.08, r"$C$", fontsize=11)
    dim_arrow(ax, (2.3, cy_mid), (2.3, gy1), label=r"$\frac{H}{2}$", text_offset=(-0.28, 0), fontsize=10.5)
    # Hinge axis O-O below C
    hy = 2.25
    ax.plot([1.2, 4.4], [hy, hy], ls="-.", color=INK, lw=1.3, zorder=5)
    ax.add_patch(patches.Rectangle((gx0 - 0.14, hy - 0.18), 0.14, 0.36, facecolor=INK, edgecolor=INK, zorder=5))
    ax.add_patch(patches.Rectangle((gx1, hy - 0.18), 0.14, 0.36, facecolor=INK, edgecolor=INK, zorder=5))
    ax.text(1.22, hy - 0.34, r"$O$", fontsize=11)
    ax.text(4.32, hy - 0.34, r"$O$", fontsize=11)

    # Right: side cross section of vertical gate + concrete pier & sill
    sx = 7.75
    concrete_block(ax, sx - 0.3, 4.75, 0.85, 1.45, dots=10)
    concrete_block(ax, sx - 0.4, 0.35, 1.5, 0.45, dots=10)
    # Vertical gate plate
    ax.add_patch(patches.Rectangle((sx - 0.07, gy0), 0.14, gy1 - gy0, facecolor="#94a3b8", edgecolor=INK, lw=1.6, zorder=4))
    ax.plot(sx, hy, "o", ms=6, mfc="white", mec=INK, mew=1.6, zorder=6)
    ax.plot([sx, 8.75], [hy, hy], ls="-.", color=AUX, lw=1.0)
    # Water submergence h above top of gate
    ax.plot([6.2, sx + 0.2], [gy1, gy1], ls="--", color=AUX, lw=1.0)
    dim_arrow(ax, (6.5, gy1), (6.5, 5.75), label=r"$h$", text_offset=(-0.26, 0), fontsize=11)
    ground_hatch(ax, 5.4, 0.8, 9.6, 0.8, side="below", step=0.30, depth=0.18, lw=1.6)
    return fig


@reg(2022, 26)
def draw_2022_26():
    fig, ax = new_canvas(5.8, 4.0, (-0.8, 5.6), (-0.8, 4.6), equal=False)
    # Axes
    flow_arrow(ax, (0, 0), (5.0, 0), label=r"$u$", text_offset=(2.45, -0.30), fontsize=12, lw=1.8)
    flow_arrow(ax, (0, 0), (0, 4.1), label=r"$y$", text_offset=(-0.32, 1.95), fontsize=12, lw=1.8)
    ax.text(-0.22, -0.32, "0", fontsize=11)
    # Curve: vertex E at (u=1 -> x=3.6, y=0.04 -> y=3.2)
    xmax, ymax = 3.6, 3.2
    ys = np.linspace(0, ymax, 120)
    xs = xmax * (1.0 - (1.0 - ys / ymax) ** 2)
    ax.plot(xs, ys, color=INK, lw=2.2, zorder=5)
    # Velocity arrows from y-axis to curve
    for yi in np.linspace(0.55, ymax, 6):
        xi = xmax * (1.0 - (1.0 - yi / ymax) ** 2)
        ax.annotate("", xy=(xi, yi), xytext=(0, yi), arrowprops=dict(arrowstyle="->", color=INK, lw=1.2))
    # Dashed drop line at E
    ax.plot([xmax, xmax], [0, ymax], ls="--", color=AUX, lw=1.1, zorder=3)
    ax.plot(xmax, ymax, "o", ms=4.5, color=INK, zorder=6)
    ax.text(xmax + 0.18, ymax + 0.05, r"$E$", fontsize=12, fontweight="bold")
    ax.text(-0.58, ymax - 0.05, "0.04", fontsize=11)
    ax.text(xmax, -0.36, "1", ha="center", fontsize=11)
    return fig


@reg(2022, 27)
def draw_2022_27():
    fig, ax = new_canvas(6.4, 4.2, (0, 10.6), (0, 6.8))
    # Horizontal bed with hatch
    ground_hatch(ax, 0.8, 0.9, 9.8, 0.9, side="below", step=0.32, depth=0.20, lw=2.0)
    # Hinge A and bottom B on bed (30 deg slope upward-right: B at 4.4, A at 4.4 + L*cos30, 0.9 + L*sin30)
    L_sc = 3.8
    th = math.radians(30)
    bx, by = 4.4, 0.9
    ax_pt, ay_pt = bx + L_sc * math.cos(th), by + L_sc * math.sin(th)
    # Vertical partition wall rising above A
    ax.plot([ax_pt, ax_pt], [ay_pt, 5.7], color=INK, lw=2.0, zorder=4)
    # Left & right tank walls (open schematic)
    ax.plot([1.0, 1.0], [0.9, 5.7], color=INK, lw=1.6, zorder=4)
    ax.plot([9.6, 9.6], [0.9, 2.7], color=INK, lw=1.6, zorder=4)
    # Water fills
    poly_left = np.array([[1.0, 0.9], [bx, by], [ax_pt, ay_pt], [ax_pt, 5.1], [1.0, 5.1]])
    ax.add_patch(patches.Polygon(poly_left, closed=True, facecolor=WATER, edgecolor="none", zorder=1))
    poly_right = np.array([[bx, by], [9.6, 0.9], [9.6, 1.9], [bx + 1.0 / math.tan(th), 1.9]])
    ax.add_patch(patches.Polygon(poly_right, closed=True, facecolor=WATER, edgecolor="none", zorder=1))
    # Water surfaces
    water_surface(ax, 1.0, ax_pt, 5.1, mark_x=2.7)
    water_surface(ax, bx + 1.0 / math.tan(th), 9.6, 1.9, mark_x=8.2)
    # Gate plate AB
    ax.plot([bx, ax_pt], [by, ay_pt], color=INK, lw=5.0, solid_capstyle="round", zorder=5)
    ax.plot([bx, ax_pt], [by, ay_pt], color="#cbd5e1", lw=2.2, solid_capstyle="round", zorder=5.2)
    ax.plot(ax_pt, ay_pt, "o", ms=6.5, mfc="white", mec=INK, mew=1.8, zorder=6)
    ax.plot(bx, by, "o", ms=4.5, color=INK, zorder=6)
    ax.text(ax_pt + 0.18, ay_pt + 0.05, r"$A$", fontsize=12, fontweight="bold")
    ax.text(bx - 0.15, by - 0.42, r"$B$", fontsize=12, fontweight="bold")
    # Cable T from B going up-left
    flow_arrow(ax, (bx, by), (2.25, 5.95), label=r"$T$", text_offset=(-1.25, 1.85), fontsize=12.5, lw=1.7)
    # Depths H_1 and H_2, angle theta, regions 1 & 2
    dim_arrow(ax, (1.65, 0.9), (1.65, 5.1), label=r"$H_1$", text_offset=(0.30, 0), fontsize=11.5)
    dim_arrow(ax, (7.0, 0.9), (7.0, 1.9), label=r"$H_2$", text_offset=(0.32, 0), fontsize=11.5)
    angle_arc(ax, (bx, by), 0, 30, radius=0.85, label=r"$\theta$", label_r=1.18, fontsize=11)
    ax.text(3.85, 3.65, "①", fontsize=13, color=INK)
    ax.text(8.8, 1.35, "②", fontsize=12.5, color=INK)
    return fig


@reg(2022, 28)
def draw_2022_28():
    fig, ax = new_canvas(6.4, 3.8, (0, 10.6), (0, 6.2))
    # Vertical plane bend pipe: horizontal inlet from x=1.0 to x=4.4 (centerline y=1.8), curves smoothly upward 30 deg to (8.2, 3.9)
    # Build centerline with straight segment + circular arc + straight inclined segment
    yc = 1.8
    r_bend = 4.2
    x_tan = 4.4
    th_end = math.radians(30)
    # Circular arc center at (x_tan, yc + r_bend)
    arc_cx, arc_cy = x_tan, yc + r_bend
    angs = np.linspace(-math.pi / 2, -math.pi / 2 + th_end, 40)
    arc_x = arc_cx + r_bend * np.cos(angs)
    arc_y = arc_cy + r_bend * np.sin(angs)
    # Outlet end after bend
    ext_len = 2.0
    xe = arc_x[-1] + ext_len * math.cos(th_end)
    ye = arc_y[-1] + ext_len * math.sin(th_end)

    cx = np.concatenate([[1.0, x_tan], arc_x[1:], [xe]])
    cy = np.concatenate([[yc, yc], arc_y[1:], [ye]])
    # Pipe half-width
    hp = 0.36
    # Tangent normals at each point
    tx = np.gradient(cx)
    ty = np.gradient(cy)
    mag = np.hypot(tx, ty)
    nx, ny = -ty / mag, tx / mag
    ux, uy = cx + hp * nx, cy + hp * ny
    lx, ly = cx - hp * nx, cy - hp * ny
    poly = np.vstack([np.column_stack([ux, uy]), np.column_stack([lx[::-1], ly[::-1]])])
    ax.add_patch(patches.Polygon(poly, closed=True, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot(ux, uy, color=INK, lw=1.9, zorder=4)
    ax.plot(lx, ly, color=INK, lw=1.9, zorder=4)
    ax.plot(cx, cy, ls="-.", color=AUX, lw=0.9, zorder=3)
    # Horizontal reference line extending right from bend start
    ax.plot([x_tan, 8.8], [yc, yc], ls="--", color=AUX, lw=1.0, zorder=3)

    # Flow arrow & diameter d
    flow_arrow(ax, (1.3, yc), (2.5, yc), label=r"$Q$", text_offset=(0, 0.14), fontsize=11.5)
    dim_arrow(ax, (3.0, yc - hp), (3.0, yc + hp), label=r"$d$", text_offset=(0.24, 0), fontsize=11)

    # Section cuts 1-1 and 2-2
    section_cut(ax, (4.0, yc - 0.72), (4.0, yc + 0.72), label="1", fontsize=11)
    px2, py2 = arc_x[-1] + 0.9 * math.cos(th_end), arc_y[-1] + 0.9 * math.sin(th_end)
    n2x, n2y = -math.sin(th_end), math.cos(th_end)
    section_cut(ax, (px2 - 0.72 * n2x, py2 - 0.72 * n2y), (px2 + 0.72 * n2x, py2 + 0.72 * n2y), label="2", fontsize=11)

    # Angle theta, elevation Delta z (shifted cleanly right of section 2), and centerline length L
    angle_arc(ax, (x_tan + 0.85, yc), 0, 30, radius=1.25, label=r"$\theta$", label_r=1.55, fontsize=11)
    ax.plot([px2, 9.2], [py2, py2], ls=":", color=AUX, lw=0.95)
    ax.plot([8.8, 9.2], [yc, yc], ls=":", color=AUX, lw=0.95)
    dim_arrow(ax, (9.0, yc), (9.0, py2), label=r"$\Delta z$", text_offset=(0.36, 0.0), fontsize=11)
    # Length L indicator clearly below bend and section 1-1/2-2 labels
    ax.annotate("", xy=(px2 - 0.52 * n2x, py2 - 0.52 * n2y), xytext=(4.0, yc - 0.52),
                arrowprops=dict(arrowstyle="<->", connectionstyle="arc3,rad=0.18", color=INK, lw=1.1))
    ax.text(6.15, 1.02, r"$L$", fontsize=11.5)
    return fig


@reg(2022, 29)
def draw_2022_29():
    fig, ax = new_canvas(6.0, 3.8, (0, 10.0), (0, 6.2))
    ground_hatch(ax, 0.8, 0.9, 9.2, 0.9, side="below", step=0.30, depth=0.20, lw=2.0)
    # Concrete culvert roof block
    bx0, bw, by0, bh = 3.2, 3.6, 2.7, 2.1
    # Water fill under and around block
    ax.add_patch(patches.Rectangle((1.0, 0.9), 2.2, 3.45, facecolor=WATER, edgecolor="none", zorder=1))
    ax.add_patch(patches.Rectangle((3.2, 0.9), 3.6, 1.8, facecolor=WATER, edgecolor="none", zorder=1))
    ax.add_patch(patches.Rectangle((6.8, 0.9), 2.2, 2.95, facecolor=WATER, edgecolor="none", zorder=1))
    concrete_block(ax, bx0, by0, bw, bh, lw=2.0, dots=18)
    # Upstream & downstream water surfaces
    water_surface(ax, 1.0, bx0, 4.35, mark_x=2.0)
    water_surface(ax, bx0 + bw, 9.0, 3.85, mark_x=8.0)
    # Section cuts 1-1 and 2-2 + depths h_1, h_2
    section_cut(ax, (1.5, 0.7), (1.5, 4.65), label="1", fontsize=11)
    dim_arrow(ax, (2.45, 0.9), (2.45, 4.35), label=r"$h_1$", text_offset=(-0.28, 0), fontsize=11.5)
    section_cut(ax, (8.6, 0.7), (8.6, 4.25), label="2", fontsize=11)
    dim_arrow(ax, (7.6, 0.9), (7.6, 3.85), label=r"$h_2$", text_offset=(-0.28, 0), fontsize=11.5)
    return fig


@reg(2022, 31)
def draw_2022_31():
    fig, ax = new_canvas(6.8, 3.8, (0, 12.2), (0, 6.2))
    # Left tank
    ax.add_patch(patches.Rectangle((0.8, 1.8), 2.2, 3.2, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot([0.8, 0.8], [1.8, 5.5], color=INK, lw=1.8, zorder=4)
    ax.plot([3.0, 3.0], [2.25, 5.5], color=INK, lw=1.8, zorder=4)
    ax.plot([0.8, 3.0], [1.8, 1.8], color=INK, lw=1.8, zorder=4)
    water_surface(ax, 0.8, 3.0, 5.0, mark_x=1.8)
    # Long horizontal pipe: x from 3.0 to 7.8, y in [1.8, 2.25], then slope down to channel bed at (9.6, 0.9)
    pipe_poly = np.array([
        [3.0, 2.25], [7.8, 2.25], [9.6, 1.35], [9.6, 0.90], [7.65, 1.80], [3.0, 1.80]
    ])
    ax.add_patch(patches.Polygon(pipe_poly, closed=True, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot([3.0, 7.8, 9.6], [2.25, 2.25, 1.35], color=INK, lw=1.8, zorder=4)
    ax.plot([3.0, 7.65, 9.6], [1.80, 1.80, 0.90], color=INK, lw=1.8, zorder=4)
    # Datum reference line & H
    ax.plot([1.2, 11.4], [0.90, 0.90], ls=":", color=AUX, lw=1.0, zorder=2)
    dim_arrow(ax, (1.45, 0.90), (1.45, 5.0), label=r"$H$", text_offset=(-0.26, 0), fontsize=11.5)
    # Two piezometers 1 and 2 spaced 100m apart with 1.5m drop (wide enough for crisp labels)
    piezometer(ax, 4.15, 2.25, 5.3, 4.55, tube_w=0.18, mark=False)
    piezometer(ax, 6.75, 2.25, 5.3, 3.45, tube_w=0.18, mark=False)
    ax.text(3.88, 2.55, "1", fontsize=10.5)
    ax.text(7.02, 2.55, "2", fontsize=10.5)
    dim_arrow(ax, (4.15, 2.72), (6.75, 2.72), label=r"$100\,\mathrm{m}$", text_offset=(0, 0.28), fontsize=10)
    ax.plot([4.15, 5.55], [4.55, 4.55], ls="--", color=AUX, lw=0.9)
    ax.plot([4.85, 6.75], [3.45, 3.45], ls="--", color=AUX, lw=0.9)
    dim_arrow(ax, (5.15, 3.45), (5.15, 4.55), label=r"$1.5\,\mathrm{m}$", text_offset=(0.56, 0), fontsize=10)
    # Downstream open channel
    ax.add_patch(patches.Polygon([[9.6, 0.90], [11.8, 0.72], [11.8, 1.38], [9.6, 1.52]], closed=True, facecolor=WATER, edgecolor="none", zorder=1))
    ground_hatch(ax, 9.6, 0.90, 11.8, 0.72, side="below", step=0.28, depth=0.16, lw=1.8)
    water_surface(ax, 9.3, 11.8, 1.45, mark_x=11.0, size=0.18, lw=1.4)
    ax.text(10.7, 0.25, r"$i=0.0016$", ha="center", fontsize=10.5)
    return fig


# ==============================================================================
# 2018 (11 figures)
# ==============================================================================


@reg(2018, 10)
def draw_2018_10():
    # Erroneous water surface curve T/F question (faithful to original geometry & T/F topology)
    fig, ax = new_canvas(7.2, 3.1, (0, 13.0), (0, 5.1), equal=False)
    xb = [0.6, 4.8, 8.6, 12.1]
    yb = [2.85, 2.35, 1.45, 1.45]
    for k in range(3):
        ground_hatch(ax, xb[k], yb[k], xb[k + 1], yb[k + 1], side="below", step=0.26, depth=0.17, lw=1.8)
    # Free overfall brink drop at right end
    cliff_x = np.array([12.1, 12.22, 12.34, 12.42])
    cliff_y = np.array([1.45, 1.38, 1.12, 0.72])
    ax.plot(cliff_x, cliff_y, color=INK, lw=1.8, zorder=4)

    # Vertical section break lines
    yc_off = 0.52
    n1_off = 1.00
    n2_off = 1.50
    ax.plot([4.8, 4.8], [yb[1], yb[1] + n2_off + 0.35], color=AUX, lw=1.0, zorder=3)
    ax.plot([8.6, 8.6], [yb[2], yb[2] + n2_off + 0.25], color=AUX, lw=1.0, zorder=3)

    # Critical depth dashed line C parallel to bed
    ax.plot(xb, [y + yc_off for y in yb], ls="--", color=AUX, lw=1.2, zorder=4)
    ax.text(0.32, yb[0] + yc_off - 0.05, r"$C$", fontsize=10.5)
    ax.text(4.88, yb[1] + yc_off + 0.06, r"$C$", fontsize=10.5)
    ax.text(12.02, yb[3] + yc_off + 0.14, r"$C$", fontsize=10.5)

    # Normal depth dash-dot lines N_1 (reach 1) and N_2 (reach 2, strictly higher)
    ax.plot([xb[0] + 0.15, xb[1]], [yb[0] + n1_off - 0.02, yb[1] + n1_off], ls="-.", color=AUX, lw=1.2, zorder=4)
    ax.text(0.45, yb[0] + n1_off + 0.12, r"$N_1$", fontsize=10.5)
    ax.text(4.88, yb[1] + n1_off + 0.02, r"$N_1$", fontsize=10.5)

    ax.plot([xb[1], xb[2]], [yb[1] + n2_off, yb[2] + n2_off], ls="-.", color=AUX, lw=1.2, zorder=4)
    ax.text(4.80, yb[1] + n2_off + 0.40, r"$N_2$", ha="center", fontsize=10.5)
    ax.text(8.62, yb[2] + n2_off + 0.30, r"$N_2$", ha="center", fontsize=10.5)

    # Erroneous solid water surface profile matching original figure:
    # M1 starts at N1 on left, stretches gently flat/arching up to meet N2 at break 1
    t1 = np.linspace(0.0, 1.0, 45)
    x_r1 = xb[0] + 0.20 + t1 * (xb[1] - (xb[0] + 0.20))
    y_m1_start = yb[0] + n1_off
    y_m1_end = yb[1] + n2_off - 0.02
    y_m1 = (1 - t1) ** 2 * y_m1_start + 2 * (1 - t1) * t1 * (0.5 * (y_m1_start + y_m1_end) + 0.18) + t1 ** 2 * y_m1_end
    ax.plot(x_r1, y_m1, color=INK, lw=1.8, zorder=5)
    ax.text(2.65, 4.02, r"$M_1$", fontsize=10.5)

    # M2 starts continuously from N2 at break 1, stays near N2 then drops smoothly to H2 start at break 2
    t2 = np.linspace(0.0, 1.0, 45)
    x_r2 = xb[1] + t2 * (xb[2] - xb[1])
    y_h2_b2 = yb[2] + yc_off + 0.28
    # Cubic Hermite / Bezier curving sharply down in second half of reach 2
    p0y, p1y, p2y, p3y = y_m1_end, yb[1] + n2_off - 0.35, y_h2_b2 + 0.55, y_h2_b2
    y_m2 = (1 - t2) ** 3 * p0y + 3 * (1 - t2) ** 2 * t2 * p1y + 3 * (1 - t2) * t2 ** 2 * p2y + t2 ** 3 * p3y
    ax.plot(x_r2, y_m2, color=INK, lw=1.8, zorder=5)
    ax.text(6.95, 2.52, r"$M_2$", fontsize=10.5)

    # H2 starts continuously at break 2 and curves down smoothly to C at overfall brink, plus nappe
    t3 = np.linspace(0.0, 1.0, 40)
    x_r3 = xb[2] + t3 * (xb[3] - xb[2])
    y_h2 = y_h2_b2 - (y_h2_b2 - (yb[3] + yc_off)) * (t3 ** 1.35)
    ax.plot(x_r3, y_h2, color=INK, lw=1.8, zorder=5)
    nappe_x = np.array([12.1, 12.35, 12.56, 12.72])
    nappe_y = np.array([yb[3] + yc_off, 1.88, 1.52, 0.92])
    ax.plot(nappe_x, nappe_y, color=INK, lw=1.8, zorder=5)
    ax.text(10.25, 2.28, r"$H_2$", fontsize=10.5)

    # Slope labels below reaches
    ax.text(2.45, 1.72, r"$i_1 < i_c$", fontsize=10.5)
    ax.text(3.75, 1.20, r"$(i_1 > i_2)$", fontsize=10)
    ax.text(6.45, 1.15, r"$i_2 < i_c$", fontsize=10.5)
    ax.text(10.25, 0.78, r"$i_3 = 0$", fontsize=10.5)
    return fig


@reg(2018, 11)
def draw_2018_11():
    fig, ax = new_canvas(6.4, 3.2, (0, 10.6), (0, 4.8))
    # Left: semicircular open channel of radius r
    xc, yc, r = 2.6, 3.4, 1.45
    th = np.linspace(math.pi, 2 * math.pi, 90)
    sx, sy = xc + r * np.cos(th), yc + r * np.sin(th)
    ax.add_patch(patches.Polygon(np.column_stack([sx, sy]), closed=True, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot(sx, sy, color=INK, lw=1.9, zorder=4)
    # Radial outward hatches along semicircle
    for a in np.linspace(math.pi + 0.18, 2 * math.pi - 0.18, 11):
        p0 = (xc + r * np.cos(a), yc + r * np.sin(a))
        p1 = (xc + (r + 0.22) * np.cos(a), yc + (r + 0.22) * np.sin(a) - 0.08)
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=AUX, lw=0.9, zorder=3)
    # Shoulder banks
    ground_hatch(ax, 0.75, yc, xc - r, yc, side="below", step=0.22, depth=0.16, lw=1.8)
    ground_hatch(ax, xc + r, yc, 4.45, yc, side="below", step=0.22, depth=0.16, lw=1.8)
    water_surface(ax, xc - r, xc + r, yc, mark_x=xc - 0.45, size=0.18, lw=1.4)
    dim_arrow(ax, (xc, yc), (xc + r * math.cos(math.radians(-42)), yc + r * math.sin(math.radians(-42))),
              label=r"$r$", text_offset=(-0.05, 0.28), both=False, fontsize=11.5)
    ax.text(xc, 1.25, "半圆", ha="center", fontsize=11.5)

    # Right: rectangular open channel of width b and depth b/2
    rx0, rx1, ry0, ry1 = 6.3, 9.2, 1.95, 3.4
    ax.add_patch(patches.Rectangle((rx0, ry0), rx1 - rx0, ry1 - ry0, facecolor=WATER, edgecolor="none", zorder=1))
    ground_hatch(ax, rx0, ry1, rx0, ry0, side="left", step=0.24, depth=0.16, lw=1.9)
    ground_hatch(ax, rx0, ry0, rx1, ry0, side="below", step=0.26, depth=0.16, lw=1.9)
    ground_hatch(ax, rx1, ry0, rx1, ry1, side="right", step=0.24, depth=0.16, lw=1.9)
    ground_hatch(ax, rx0 - 0.45, ry1, rx0, ry1, side="below", step=0.22, depth=0.16, lw=1.8)
    ground_hatch(ax, rx1, ry1, rx1 + 0.45, ry1, side="below", step=0.22, depth=0.16, lw=1.8)
    water_surface(ax, rx0, rx1, ry1, mark_x=7.75, size=0.18, lw=1.4)
    dim_arrow(ax, (rx0, 2.55), (rx1, 2.55), label=r"$b$", text_offset=(0, -0.26), fontsize=11.5)
    dim_arrow(ax, (rx1 + 0.55, ry0), (rx1 + 0.55, ry1), label=r"$b/2$", text_offset=(0.45, 0), fontsize=11)
    ax.text(7.75, 1.25, "矩形", ha="center", fontsize=11.5)
    return fig


@reg(2018, 12)
def draw_2018_12():
    fig, ax = new_canvas(5.8, 3.2, (0, 9.6), (0, 4.8))
    # Water under free surface dropping smoothly from y=3.6 down to y=3.0 over bump
    xs = np.linspace(0.8, 8.8, 120)
    ys = 3.30 - 0.30 * np.tanh((xs - 4.7) / 0.75)
    ax.add_patch(patches.Polygon(np.vstack([np.column_stack([xs, ys]), [[8.8, 0.8], [0.8, 0.8]]]),
                                 closed=True, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot(xs, ys, color=INK, lw=1.7, zorder=4)
    water_surface(ax, 1.4, 2.4, 3.60, mark_x=2.0, size=0.18, lw=0)
    ground_hatch(ax, 0.8, 0.8, 8.8, 0.8, side="below", step=0.28, depth=0.18, lw=1.9)
    # Raised sill block of height Delta
    concrete_block(ax, 3.4, 0.8, 2.8, 1.05, lw=1.9, dots=12)
    dim_arrow(ax, (1.5, 0.8), (1.5, 3.59), label=r"$h_1$", text_offset=(0.28, 0), fontsize=11.5)
    dim_arrow(ax, (5.2, 1.85), (5.2, 3.12), label=r"$h_2$", text_offset=(0.28, 0), fontsize=11.5)
    dim_arrow(ax, (6.5, 0.8), (6.5, 1.85), label=r"$\Delta$", text_offset=(0.28, 0), ext_len=0.32, ext_dir=(-1, 0), fontsize=11)
    return fig


@reg(2018, 17)
def draw_2018_17():
    fig, ax = new_canvas(6.4, 4.0, (0, 10.6), (0, 6.4))
    # Upstream reservoir (left) and downstream reservoir (right)
    ax.add_patch(patches.Rectangle((0.9, 1.2), 2.2, 3.8, facecolor=WATER, edgecolor="none", zorder=1))
    ax.add_patch(patches.Rectangle((7.2, 1.2), 2.4, 2.2, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot([0.9, 0.9, 3.1, 3.1], [5.5, 1.2, 1.2, 1.75], color=INK, lw=1.9, zorder=4)
    ax.plot([3.1, 3.1], [2.15, 5.5], color=INK, lw=1.9, zorder=4)
    ax.plot([7.2, 7.2], [5.5, 2.15], color=INK, lw=1.9, zorder=4)
    ax.plot([7.2, 7.2, 9.6, 9.6], [1.75, 1.2, 1.2, 5.5], color=INK, lw=1.9, zorder=4)
    water_surface(ax, 0.9, 3.1, 5.0, mark_x=1.8)
    water_surface(ax, 7.2, 9.6, 3.4, mark_x=8.4)
    dim_arrow(ax, (6.5, 3.4), (6.5, 5.0), label=r"$H$", text_offset=(0.30, 0), ext_len=0.7, ext_dir=(1, 0), fontsize=11.5)
    # Original series pipe diameter d (length 2l = 4.1)
    ax.add_patch(patches.Rectangle((3.1, 1.75), 4.1, 0.40, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot([3.1, 7.2], [2.15, 2.15], color=INK, lw=1.8, zorder=4)
    ax.plot([3.1, 7.2], [1.75, 1.75], color=INK, lw=1.8, zorder=4)
    # Dashed expanded half on right half [5.15, 7.2], diameter 2d
    ax.plot([5.15, 7.2], [2.35, 2.35], ls="--", color=INK, lw=1.6, zorder=4)
    ax.plot([5.15, 7.2], [1.55, 1.55], ls="--", color=INK, lw=1.6, zorder=4)
    ax.plot([5.15, 5.15], [2.15, 2.35], ls="--", color=INK, lw=1.4, zorder=4)
    ax.plot([5.15, 5.15], [1.75, 1.55], ls="--", color=INK, lw=1.4, zorder=4)
    dim_arrow(ax, (4.1, 1.75), (4.1, 2.15), label=r"$d$", text_offset=(0.0, 0.36), fontsize=10.5)
    dim_arrow(ax, (7.6, 1.55), (7.6, 2.35), label=r"$2d$", text_offset=(0.34, 0), fontsize=10.5)
    dim_arrow(ax, (3.1, 0.95), (5.15, 0.95), label=r"$l$", text_offset=(0, -0.25), ext_len=0.5, ext_dir=(0, 1), fontsize=11)
    dim_arrow(ax, (5.15, 0.95), (7.2, 0.95), label=r"$l$", text_offset=(0, -0.25), ext_len=0.5, ext_dir=(0, 1), fontsize=11)
    return fig


@reg(2018, 20)
def draw_2018_20():
    fig, ax = new_canvas(6.0, 4.4, (0, 9.8), (0, 7.2))
    # Downward-sloping Venturi pipe along -40 deg from top-left (1.2, 5.6) to bottom-right (8.6, 0.8)
    ang = math.radians(-38)
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    # Centerline points distance s in [0, 8.2]: wide [0, 3.0] r=0.62, converge [3.0, 4.6], throat [4.6, 6.2] r=0.31, expand/end [6.2, 8.2]
    x0, y0 = 1.1, 5.8
    s_pts = [0.0, 3.0, 4.6, 6.2, 7.8]
    r_pts = [0.60, 0.60, 0.30, 0.30, 0.45]
    top_pts = [(x0 + s * ca + r * nx, y0 + s * sa + r * ny) for s, r in zip(s_pts, r_pts)]
    bot_pts = [(x0 + s * ca - r * nx, y0 + s * sa - r * ny) for s, r in zip(s_pts, r_pts)]
    poly = np.array(top_pts + bot_pts[::-1])
    ax.add_patch(patches.Polygon(poly, closed=True, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot([p[0] for p in top_pts], [p[1] for p in top_pts], color=INK, lw=1.9, zorder=4)
    ax.plot([p[0] for p in bot_pts], [p[1] for p in bot_pts], color=INK, lw=1.9, zorder=4)
    ax.plot([x0, x0 + 7.8 * ca], [y0, y0 + 7.8 * sa], ls="-.", color=AUX, lw=0.9, zorder=3)
    flow_arrow(ax, (x0 + 0.6 * ca, y0 + 0.6 * sa), (x0 + 1.8 * ca, y0 + 1.8 * sa), lw=1.6)

    # Diameter labels D=300mm and d=150mm (clear of pipe wall)
    p1t, p1b = (x0 + 1.7 * ca + 0.60 * nx, y0 + 1.7 * sa + 0.60 * ny), (x0 + 1.7 * ca - 0.60 * nx, y0 + 1.7 * sa - 0.60 * ny)
    dim_arrow(ax, p1b, p1t, label=r"$D=300\,\mathrm{mm}$", text_offset=(-1.28, -0.82), fontsize=10)
    p2t, p2b = (x0 + 5.4 * ca + 0.30 * nx, y0 + 5.4 * sa + 0.30 * ny), (x0 + 5.4 * ca - 0.30 * nx, y0 + 5.4 * sa - 0.30 * ny)
    dim_arrow(ax, p2b, p2t, label=r"$d=150\,\mathrm{mm}$", text_offset=(-0.82, -0.70), fontsize=10)

    # Inverted U-tube manometer rising vertically from wide tap (s=2.4) & throat tap (s=5.3)
    tx1, ty1 = top_pts[0][0] + 2.4 * ca, top_pts[0][1] + 2.4 * sa
    tx2, ty2 = x0 + 5.3 * ca + 0.30 * nx, y0 + 5.3 * sa + 0.30 * ny
    tw = 0.14
    y_top = 6.45
    yw1, yw2 = 5.65, 4.35
    ax.add_patch(patches.Rectangle((tx1 - tw / 2, ty1), tw, yw1 - ty1, facecolor=WATER, edgecolor="none", zorder=2))
    ax.add_patch(patches.Rectangle((tx2 - tw / 2, ty2), tw, yw2 - ty2, facecolor=WATER, edgecolor="none", zorder=2))
    ax.plot([tx1 - tw / 2, tx1 - tw / 2, tx2 + tw / 2, tx2 + tw / 2], [ty1, y_top + tw / 2, y_top + tw / 2, ty2], color=INK, lw=1.5, zorder=4)
    ax.plot([tx1 + tw / 2, tx1 + tw / 2, tx2 - tw / 2, tx2 - tw / 2], [ty1, y_top - tw / 2, y_top - tw / 2, ty2], color=INK, lw=1.5, zorder=4)
    ax.plot([tx1 - tw / 2, tx1 + tw / 2], [yw1, yw1], color=INK, lw=1.3, zorder=5)
    ax.plot([tx2 - tw / 2, tx2 + tw / 2], [yw2, yw2], color=INK, lw=1.3, zorder=5)
    ax.text(0.5 * (tx1 + tx2), y_top + 0.25, r"$B$", ha="center", fontsize=11.5, fontweight="bold")
    # 250 mm diff dimension
    ax.plot([tx1, tx2 + 0.7], [yw1, yw1], ls=":", color=AUX, lw=0.9)
    ax.plot([tx2, tx2 + 0.7], [yw2, yw2], ls=":", color=AUX, lw=0.9)
    dim_arrow(ax, (tx2 + 0.55, yw2), (tx2 + 0.55, yw1), label=r"$250\,\mathrm{mm}$", text_offset=(0.75, 0), fontsize=10)
    return fig


@reg(2018, 21)
def draw_2018_21():
    fig, ax = new_canvas(6.0, 4.2, (0, 10.0), (0, 6.8))
    # Horizontal pipe at bottom
    ax.add_patch(patches.Rectangle((1.0, 1.0), 8.0, 1.0, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot([1.0, 9.0], [2.0, 2.0], color=INK, lw=2.0, zorder=4)
    ax.plot([1.0, 9.0], [1.0, 1.0], color=INK, lw=2.0, zorder=4)
    section_cut(ax, (2.6, 0.72), (2.6, 2.22), label="", fontsize=11)
    ax.text(2.6, 0.42, "1", ha="center", va="center", fontsize=11)
    ax.text(2.92, 2.28, "1", ha="center", va="center", fontsize=11)
    section_cut(ax, (7.4, 0.72), (7.4, 2.22), label="", fontsize=11)
    ax.text(7.4, 0.42, "2", ha="center", va="center", fontsize=11)
    ax.text(7.08, 2.28, "2", ha="center", va="center", fontsize=11)
    flow_arrow(ax, (4.3, 1.5), (5.8, 1.5), label=r"$v$", text_offset=(-0.85, 0.0), fontsize=12)

    # Inverted U-tube above sections 1 and 2
    x1, x2, tw = 2.6, 7.4, 0.26
    yt, yi1, yi2 = 5.6, 3.05, 4.55
    # Water legs up to interfaces
    ax.add_patch(patches.Rectangle((x1 - tw / 2, 2.0), tw, yi1 - 2.0, facecolor=WATER, edgecolor="none", zorder=2))
    ax.add_patch(patches.Rectangle((x2 - tw / 2, 2.0), tw, yi2 - 2.0, facecolor=WATER, edgecolor="none", zorder=2))
    # Oil upper loop
    ax.add_patch(patches.Rectangle((x1 - tw / 2, yi1), tw, yt - yi1 + tw / 2, facecolor=OIL, edgecolor="none", zorder=2))
    ax.add_patch(patches.Rectangle((x2 - tw / 2, yi2), tw, yt - yi2 + tw / 2, facecolor=OIL, edgecolor="none", zorder=2))
    ax.add_patch(patches.Rectangle((x1 - tw / 2, yt - tw / 2), x2 - x1 + tw, tw, facecolor=OIL, edgecolor="none", zorder=2))
    # Walls
    ax.plot([x1 - tw / 2, x1 - tw / 2, x2 + tw / 2, x2 + tw / 2], [2.0, yt + tw / 2, yt + tw / 2, 2.0], color=INK, lw=1.7, zorder=4)
    ax.plot([x1 + tw / 2, x1 + tw / 2, x2 - tw / 2, x2 - tw / 2], [2.0, yt - tw / 2, yt - tw / 2, 2.0], color=INK, lw=1.7, zorder=4)
    ax.plot([x1 - tw / 2, x1 + tw / 2], [yi1, yi1], color=INK, lw=1.4, zorder=5)
    ax.plot([x2 - tw / 2, x2 + tw / 2], [yi2, yi2], color=INK, lw=1.4, zorder=5)
    ax.text(5.0, yt + 0.35, "油", ha="center", fontsize=11.5)
    ax.text(3.05, 2.45, "水", fontsize=11)
    # Interface height diff Delta h'
    ax.plot([x1 + tw / 2, 5.2], [yi1, yi1], ls="--", color=AUX, lw=1.0)
    ax.plot([4.5, x2 - tw / 2], [yi2, yi2], ls="--", color=AUX, lw=1.0)
    dim_arrow(ax, (4.85, yi1), (4.85, yi2), label=r"$\Delta h'$", text_offset=(-0.45, 0), fontsize=11.5)
    return fig


@reg(2018, 23)
def draw_2018_23():
    fig, ax = new_canvas(6.4, 3.8, (0, 10.8), (0, 6.2))
    # Upstream & downstream tanks
    ax.add_patch(patches.Rectangle((0.8, 1.2), 2.1, 3.6, facecolor=WATER, edgecolor="none", zorder=1))
    ax.add_patch(patches.Rectangle((7.6, 1.2), 2.2, 2.4, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot([0.8, 0.8, 2.9, 2.9], [5.4, 1.2, 1.2, 2.05], color=INK, lw=1.9, zorder=4)
    ax.plot([2.9, 2.9], [2.45, 5.4], color=INK, lw=1.9, zorder=4)
    ax.plot([7.6, 7.6], [5.4, 2.65], color=INK, lw=1.9, zorder=4)
    ax.plot([7.6, 7.6, 9.8, 9.8], [1.85, 1.2, 1.2, 5.4], color=INK, lw=1.9, zorder=4)
    water_surface(ax, 0.8, 2.9, 4.8, mark_x=1.8)
    water_surface(ax, 7.6, 9.8, 3.6, mark_x=8.7)
    dim_arrow(ax, (5.4, 3.6), (5.4, 4.8), label=r"$H$", text_offset=(0.30, 0), ext_len=0.9, ext_dir=(1, 0), fontsize=11.5)
    # Sudden expansion series pipe: [2.9..5.1] narrower, [5.1..7.6] wider
    ax.add_patch(patches.Rectangle((2.9, 2.05), 2.2, 0.40, facecolor=WATER, edgecolor="none", zorder=1))
    ax.add_patch(patches.Rectangle((5.1, 1.85), 2.5, 0.80, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot([2.9, 5.1, 5.1, 7.6], [2.45, 2.45, 2.65, 2.65], color=INK, lw=1.8, zorder=4)
    ax.plot([2.9, 5.1, 5.1, 7.6], [2.05, 2.05, 1.85, 1.85], color=INK, lw=1.8, zorder=4)
    ax.text(4.0, 1.15, "$d_1$\n$L_1$\n$\\lambda_1$", ha="center", va="center", fontsize=10.5)
    ax.text(6.35, 1.05, "$d_2$\n$L_2$\n$\\lambda_2$", ha="center", va="center", fontsize=10.5)
    return fig


@reg(2018, 24)
def draw_2018_24():
    fig, ax = new_canvas(6.0, 3.6, (-0.8, 9.6), (-0.6, 5.2), equal=False)
    ground_hatch(ax, 0.4, 0.6, 8.8, 0.6, side="below", step=0.30, depth=0.20, lw=2.0)
    # y axis at x=0.9, height H=3.3 (water surface at y=3.9), A at (7.4, 3.9)
    bx, by = 0.9, 0.6
    H, U = 3.3, 6.5
    # Vertical y-axis + label
    ax.plot([bx, bx], [by, by + H], color=INK, lw=1.3, zorder=4)
    dim_arrow(ax, (0.2, by), (0.2, by + H), label=r"$u$", text_offset=(-0.28, 0), both=False, fontsize=12)
    # Top velocity segment H/u: straight line from B(0.9, 0.6) to A(7.4, 3.9)
    # and parabola x(y) = u*[2*(y/H) - (y/H)^2] => bows downward-right below BA, tangent vertical at A!
    ax.plot([bx, bx + U], [by, by + H], color=INK, lw=1.7, zorder=5)
    ys = np.linspace(0, H, 100)
    xs = bx + U * (2.0 * (ys / H) - (ys / H) ** 2)
    ax.plot(xs, by + ys, color=INK, lw=2.1, zorder=5)
    ax.plot([bx, bx + U], [by + H, by + H], color=INK, lw=1.5, zorder=4)
    dim_arrow(ax, (bx, by + H + 0.35), (bx + U, by + H + 0.35), label=r"$H$", text_offset=(0, 0.25), ext_len=0.35, ext_dir=(0, -1), fontsize=11)
    # Curve labels matching original visual intuition cleanly (clear of line BA)
    ax.text(bx + 0.08, by + 0.48, r"$B$", fontsize=12, fontweight="bold")
    ax.text(bx + U + 0.18, by + H - 0.08, r"$A$", fontsize=12, fontweight="bold")
    ax.text(3.35, 2.35, r"$a$", fontsize=11.5)
    ax.text(5.25, 1.55, r"$b$", fontsize=11.5)
    return fig


@reg(2018, 26)
def draw_2018_26():
    fig, ax = new_canvas(6.0, 3.8, (0, 10.0), (0, 6.0))
    # Horizontal base + inclined slope at 30 deg downward-right
    ax_x, ax_y = 8.4, 0.8
    ang = math.radians(30)
    L_s = 7.4
    sx0, sy0 = ax_x - L_s * math.cos(ang), ax_y + L_s * math.sin(ang)
    ground_hatch(ax, 1.0, ax_y, ax_x + 0.6, ax_y, side="below", step=0.30, depth=0.18, lw=1.9)
    ground_hatch(ax, sx0, sy0, ax_x, ax_y, side="below", step=0.30, depth=0.18, lw=2.0)
    angle_arc(ax, (ax_x, ax_y), 150, 180, radius=1.55, label=r"$30^{\circ}$", label_r=2.12, fontsize=11)

    # Gap thickness delta & sliding plate along slope
    ca, sa = math.cos(ang), -math.sin(ang)  # unit down-slope tangent
    nx, ny = math.sin(ang), math.cos(ang)    # unit normal away from slope (up-right)
    delta = 0.26
    pw, ph = 3.2, 0.38
    s_start = 1.8
    # Plate corners
    p_bl = (sx0 + s_start * ca + delta * nx, sy0 + s_start * sa + delta * ny)
    p_br = (p_bl[0] + pw * ca, p_bl[1] + pw * sa)
    p_tr = (p_br[0] + ph * nx, p_br[1] + ph * ny)
    p_tl = (p_bl[0] + ph * nx, p_bl[1] + ph * ny)
    # Oil film hatch/tint
    oil_poly = np.array([
        [sx0 + (s_start - 0.5) * ca, sy0 + (s_start - 0.5) * sa],
        [sx0 + (s_start + pw + 0.5) * ca, sy0 + (s_start + pw + 0.5) * sa],
        [sx0 + (s_start + pw + 0.5) * ca + delta * nx, sy0 + (s_start + pw + 0.5) * sa + delta * ny],
        [sx0 + (s_start - 0.5) * ca + delta * nx, sy0 + (s_start - 0.5) * sa + delta * ny],
    ])
    ax.add_patch(patches.Polygon(oil_poly, closed=True, facecolor=OIL, edgecolor="none", zorder=1))
    ax.add_patch(patches.Polygon(np.array([p_bl, p_br, p_tr, p_tl]), closed=True, facecolor="#cbd5e1", edgecolor=INK, lw=1.8, hatch="///", zorder=4))
    # Delta dim & U arrow
    d_base = (sx0 + 1.15 * ca, sy0 + 1.15 * sa)
    d_top = (d_base[0] + delta * nx, d_base[1] + delta * ny)
    dim_arrow(ax, (d_base[0] - 0.38 * nx, d_base[1] - 0.38 * ny), d_base, label="", both=False, lw=1.1)
    dim_arrow(ax, (d_top[0] + 0.38 * nx, d_top[1] + 0.38 * ny), d_top, label=r"$\delta$", text_offset=(0.25, 0.25), both=False, lw=1.1, fontsize=11.5)
    u_mid = (0.5 * (p_br[0] + p_tr[0]), 0.5 * (p_br[1] + p_tr[1]))
    flow_arrow(ax, u_mid, (u_mid[0] + 1.1 * ca, u_mid[1] + 1.1 * sa), label=r"$U$", text_offset=(0.45, 0.22), fontsize=12)
    return fig


@reg(2018, 27)
def draw_2018_27():
    fig, ax = new_canvas(6.4, 4.0, (0, 10.6), (0, 6.4))
    # Semi-cylinder radius R=2.0 centered at (3.2, 2.8)
    cx, cy, R = 3.2, 2.8, 1.9
    th = np.linspace(math.pi / 2, 3 * math.pi / 2, 90)
    ax.add_patch(patches.Polygon(np.vstack([np.column_stack([cx + R * np.cos(th[:45]), cy + R * np.sin(th[:45])]), [[7.4, cy], [7.4, cy + R]]]),
                                 closed=True, facecolor=OIL, edgecolor="none", zorder=1))
    ax.add_patch(patches.Polygon(np.vstack([np.column_stack([cx + R * np.cos(th[44:]), cy + R * np.sin(th[44:])]), [[7.4, cy - R], [7.4, cy]]]),
                                 closed=True, facecolor=WATER, edgecolor="none", zorder=1))
    # Outer boundary ABC + top/bottom walls + vertical standpipe at x=7.0..7.4 rising 1.3 above top
    ax.plot(cx + R * np.cos(th), cy + R * np.sin(th), color=INK, lw=2.1, zorder=4)
    ax.plot([cx, 7.0], [cy + R, cy + R], color=INK, lw=2.0, zorder=4)
    ax.plot([cx, 8.8], [cy - R, cy - R], color=INK, lw=2.0, zorder=4)
    ax.plot([7.0, 7.0], [cy + R, 6.0], color=INK, lw=1.8, zorder=4)
    ax.plot([7.4, 7.4], [cy + R, 6.0], color=INK, lw=1.8, zorder=4)
    ax.plot([7.4, 8.8], [cy + R, cy + R], color=INK, lw=2.0, zorder=4)
    ax.add_patch(patches.Rectangle((7.0, cy + R), 0.4, 5.75 - (cy + R), facecolor=OIL, edgecolor="none", zorder=2))
    water_surface(ax, 7.0, 7.4, 5.75, mark_x=7.2, size=0.15, lw=1.3)
    # Dashed oil-water interface through B
    ax.plot([cx - R, 8.8], [cy, cy], ls="-.", color=INK, lw=1.3, zorder=4)
    # Points A, B, C & labels
    ax.text(cx, cy + R + 0.16, r"$A$", ha="center", fontsize=12, fontweight="bold")
    ax.text(cx - R - 0.28, cy, r"$B$", va="center", fontsize=12, fontweight="bold")
    ax.text(cx, cy - R - 0.36, r"$C$", ha="center", fontsize=12, fontweight="bold")
    ax.plot([cx, cx], [cy - R, cy + R], ls=":", color=AUX, lw=1.0)
    dim_arrow(ax, (cx + 0.25, cy), (cx + 0.25, cy + R), label=r"$2\,\mathrm{m}$", text_offset=(0.55, 0), fontsize=10.5)
    dim_arrow(ax, (cx + 0.25, cy - R), (cx + 0.25, cy), label=r"$2\,\mathrm{m}$", text_offset=(0.55, 0), fontsize=10.5)
    dim_arrow(ax, (8.0, cy + R), (8.0, 5.75), label=r"$2\,\mathrm{m}$", text_offset=(0.55, 0), ext_len=0.75, ext_dir=(-1, 0), fontsize=10.5)
    ax.text(5.7, cy + 0.9, "油", ha="center", fontsize=12)
    ax.text(5.7, cy - 1.0, "水", ha="center", fontsize=12)
    return fig


@reg(2018, 28)
def draw_2018_28():
    fig, ax = new_canvas(6.4, 4.2, (0, 10.6), (0, 6.8))
    # Horizontal support frame & bed
    ground_hatch(ax, 0.8, 0.7, 9.6, 0.7, side="below", step=0.30, depth=0.18, lw=1.9)
    # Outer vertical support frame around wide pipe
    ground_hatch(ax, 2.0, 0.7, 2.0, 5.1, side="right", step=0.30, depth=0.18, lw=1.7)
    ground_hatch(ax, 2.0, 5.1, 6.6, 5.1, side="below", step=0.30, depth=0.18, lw=1.7)
    ground_hatch(ax, 6.6, 0.7, 6.6, 5.1, side="left", step=0.30, depth=0.18, lw=1.7)
    # Pipe tapering from d_1 (y in [2.6, 3.4]) on left to d_2 (y in [2.8, 3.2]) on right
    p_poly = np.array([
        [0.8, 3.4], [5.4, 3.4], [6.6, 3.2], [9.4, 3.2],
        [9.4, 2.8], [6.6, 2.8], [5.4, 2.6], [0.8, 2.6]
    ])
    ax.add_patch(patches.Polygon(p_poly, closed=True, facecolor=WATER, edgecolor="none", zorder=3.5))
    ax.plot([0.8, 5.4, 6.6, 9.4], [3.4, 3.4, 3.2, 3.2], color=INK, lw=1.8, zorder=4)
    ax.plot([0.8, 5.4, 6.6, 9.4], [2.6, 2.6, 2.8, 2.8], color=INK, lw=1.8, zorder=4)
    ax.plot([0.8, 9.4], [3.0, 3.0], ls="-.", color=AUX, lw=0.9, zorder=4)
    dim_arrow(ax, (0.55, 2.6), (0.55, 3.4), label=r"$d_1$", text_offset=(-0.34, 0), fontsize=11)
    dim_arrow(ax, (9.65, 2.8), (9.65, 3.2), label=r"$d_2$", text_offset=(0.34, 0), ext_len=0.35, ext_dir=(-1, 0), fontsize=11)
    # Piezometer on fine pipe d_2 showing 0.3 m above centerline
    piezometer(ax, 7.6, 3.2, 5.7, 5.05, tube_w=0.18, mark=True)
    dim_arrow(ax, (8.3, 3.0), (8.3, 5.05), label=r"$0.3\,\mathrm{m}$", text_offset=(0.65, 0), ext_len=0.55, ext_dir=(-1, 0), fontsize=10.5)
    return fig


# ==============================================================================
# 2017 (14 figures)
# ==============================================================================


@reg(2017, 8)
def draw_2017_08():
    fig, ax = new_canvas(6.2, 3.3, (0, 10.4), (0, 5.2))
    # Bumped water surface (intentionally rising over bump as in original T/F)
    xs = np.linspace(0.6, 9.8, 140)
    ys = 3.15 + 0.65 * np.exp(-((xs - 5.2) / 1.45) ** 2)
    ax.add_patch(patches.Polygon(np.vstack([np.column_stack([xs, ys]), [[9.8, 0.9], [0.6, 0.9]]]),
                                 closed=True, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot(xs, ys, color=INK, lw=1.7, zorder=4)
    water_surface(ax, 1.3, 2.2, 3.16, mark_x=1.8, size=0.18, lw=0)
    water_surface(ax, 8.0, 8.9, 3.16, mark_x=8.5, size=0.18, lw=0)
    # Bed with raised bump of height a
    ground_hatch(ax, 0.6, 0.9, 3.4, 0.9, side="below", step=0.28, depth=0.18, lw=1.9)
    ground_hatch(ax, 3.4, 0.9, 3.4, 2.1, side="right", step=0.24, depth=0.18, lw=1.9)
    ground_hatch(ax, 3.4, 2.1, 7.0, 2.1, side="below", step=0.28, depth=0.18, lw=1.9)
    ground_hatch(ax, 7.0, 2.1, 7.0, 0.9, side="left", step=0.24, depth=0.18, lw=1.9)
    ground_hatch(ax, 7.0, 0.9, 9.8, 0.9, side="below", step=0.28, depth=0.18, lw=1.9)
    dim_arrow(ax, (1.1, 0.9), (1.1, 3.15), label=r"$h_1$", text_offset=(0.28, 0), fontsize=11.5)
    dim_arrow(ax, (2.8, 0.9), (2.8, 2.1), label=r"$a$", text_offset=(-0.25, 0), fontsize=11)
    dim_arrow(ax, (5.2, 2.1), (5.2, 3.80), label=r"$h_2$", text_offset=(0.28, 0), fontsize=11.5)
    return fig


def _ext_pair_arrows(ax, x: float, y_low: float, y_high: float, label: str, gap_ext: float = 0.55, dx: float = 0.22):
    """Draw external opposing vertical dimension arrows (up to y_low, down to y_high) like original."""
    ax.annotate("", xy=(x, y_high), xytext=(x, y_high + gap_ext),
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.0, shrinkA=0, shrinkB=0), zorder=6)
    ax.annotate("", xy=(x, y_low), xytext=(x, y_low - gap_ext),
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.0, shrinkA=0, shrinkB=0), zorder=6)
    ax.text(x + dx, y_high + 0.14, label, ha="left", va="bottom", fontsize=10, color=INK)


@reg(2017, 9)
def draw_2017_09():
    # Completely submerged inclined plane gate AB below BOTH upstream and downstream water levels
    fig, ax = new_canvas(5.8, 4.8, (0, 9.6), (0, 7.6))
    y_floor = 0.85
    x0 = 2.1
    slope_inv = 0.58  # dx / dy along incline

    def x_wall(y: float) -> float:
        return x0 + (y - y_floor) * slope_inv

    y_top = 7.2
    ax.plot([0.6, 6.9], [y_floor, y_floor], color=INK, lw=1.5, zorder=4)
    ax.plot([x0, x_wall(y_top)], [y_floor, y_top], color=INK, lw=1.3, zorder=4)
    ax.text(x0 - 0.15, 0.42, r"$(a)$", ha="center", fontsize=10.5)

    # Thick gate AB strictly below BOTH solid water levels (0.85 -> 3.90)
    y_gate_top = 3.90
    x_gate_top = x_wall(y_gate_top)
    ax.plot([x0, x_gate_top], [y_floor, y_gate_top], color=INK, lw=5.2, solid_capstyle="butt", zorder=5)
    ax.plot(x_gate_top, y_gate_top, "o", ms=5.0, mfc="white", mec=INK, mew=1.3, zorder=6)

    # Upstream levels (above downstream levels, intersecting thin upper incline)
    y_l_low, y_l_high = 5.65, 6.20
    ax.plot([0.5, x_wall(y_l_low)], [y_l_low, y_l_low], color=INK, lw=1.4, zorder=4)
    ax.plot([0.5, x_wall(y_l_high)], [y_l_high, y_l_high], ls="--", color=INK, lw=1.2, zorder=4)
    _ext_pair_arrows(ax, 1.55, y_l_low, y_l_high, r"$1\,\mathrm{m}$", gap_ext=0.52, dx=0.14)

    # Downstream levels (still completely above thick gate top 3.90!)
    y_r_low, y_r_high = 4.55, 5.10
    ax.plot([x_wall(y_r_low), 8.6], [y_r_low, y_r_low], color=INK, lw=1.4, zorder=4)
    water_surface(ax, x_wall(y_r_low), 8.6, y_r_low, mark_x=6.9, size=0.18, lw=0)
    ax.plot([x_wall(y_r_high), 8.6], [y_r_high, y_r_high], ls="--", color=INK, lw=1.2, zorder=4)
    _ext_pair_arrows(ax, 7.75, y_r_low, y_r_high, r"$1\,\mathrm{m}$", gap_ext=0.52, dx=0.14)
    return fig


@reg(2017, 10)
def draw_2017_10():
    # Erroneous EGL / HGL / negative-pressure zone T/F question (NO spoiler, free right outlet)
    fig, ax = new_canvas(6.8, 3.8, (0, 12.2), (0, 6.4), equal=False)
    # Left slope, flat top, right slope mound
    ground_hatch(ax, 0.5, 0.70, 3.85, 3.55, side="below", step=0.24, depth=0.15, lw=1.6)
    ground_hatch(ax, 3.85, 3.55, 7.65, 3.55, side="below", step=0.25, depth=0.15, lw=1.6)
    ground_hatch(ax, 7.65, 3.55, 11.4, 0.75, side="below", step=0.24, depth=0.15, lw=1.6)

    # Two small hatched support piers under horizontal reach l_2
    for px_pier in (4.9, 6.35):
        ax.add_patch(patches.Rectangle((px_pier, 3.55), 0.72, 0.36, facecolor=CONCRETE, edgecolor=INK, lw=1.1, hatch="///", zorder=3.5))

    # Constant-diameter bent pipe (inlet at 1.85 -> bend1 at 3.80 -> bend2 at 7.70 -> free outlet at 11.05)
    px = [1.85, 3.80, 7.70, 11.05]
    py = [2.42, 4.05, 4.05, 1.38]
    hp = 0.14
    for k in range(3):
        ax.plot([px[k], px[k + 1]], [py[k] + hp, py[k + 1] + hp], color=INK, lw=1.6, zorder=4)
        ax.plot([px[k], px[k + 1]], [py[k] - hp, py[k + 1] - hp], color=INK, lw=1.6, zorder=4)
    # Upstream reservoir surface only (NO downstream reservoir on the right!)
    water_surface(ax, 0.45, 2.22, 2.74, mark_x=1.22, size=0.17, lw=1.5)
    ax.text(0.85, 2.16, r"$v=0$", ha="center", fontsize=10.5)

    # Step-dropped solid EGL & HGL shown in original T/F question
    hv = 0.34
    # Segment 1 [1.85 -> 3.80], Segment 2 [3.80 -> 7.70], Segment 3 [7.70 -> 11.05]
    egl_pts = [
        ([1.85, 1.85, 3.80], [2.74, 2.48, 2.34]),
        ([3.80, 3.80, 7.70], [2.34, 2.18, 1.98]),
        ([7.70, 7.70, 11.05], [1.98, 1.82, 1.68]),
    ]
    hgl_pts = [
        ([1.85, 3.80], [2.48 - hv, 2.34 - hv]),
        ([3.80, 3.80, 7.70], [2.34 - hv, 2.18 - hv, 1.98 - hv]),
        ([7.70, 7.70, 11.05], [1.98 - hv, 1.82 - hv, 1.68 - hv]),
    ]
    for xs, ys in egl_pts:
        ax.plot(xs, ys, color=INK, lw=1.4, zorder=5)
    for xs, ys in hgl_pts:
        ax.plot(xs, ys, color=INK, lw=1.4, zorder=5)

    # Velocity head alpha*v^2/(2g) indicator between EGL and HGL on Reach 1
    xq = 2.95
    y_egl_q = 2.48 - (2.48 - 2.34) * (xq - 1.85) / (3.80 - 1.85)
    y_hgl_q = y_egl_q - hv
    ax.annotate("", xy=(xq, y_egl_q), xytext=(xq, y_egl_q + 0.38),
                arrowprops=dict(arrowstyle="->", color=INK, lw=0.95, shrinkA=0, shrinkB=0), zorder=6)
    ax.annotate("", xy=(xq, y_hgl_q), xytext=(xq, y_hgl_q - 0.38),
                arrowprops=dict(arrowstyle="->", color=INK, lw=0.95, shrinkA=0, shrinkB=0), zorder=6)
    ax.plot([xq - 0.38, xq], [1.18, y_hgl_q + 0.16], color=AUX, lw=0.85, zorder=5)
    ax.text(xq - 0.45, 0.92, r"$\alpha v^2 / 2g$", ha="center", va="center", fontsize=10.5)

    # Labels & pointers for grade lines and pipe lengths
    ax.annotate("总水头线", xy=(4.45, 2.14), xytext=(5.35, 1.05),
                arrowprops=dict(arrowstyle="->", color=AUX, lw=0.9), fontsize=10, ha="center")
    ax.annotate("测压管水头线", xy=(8.9, 1.44), xytext=(8.0, 0.55),
                arrowprops=dict(arrowstyle="->", color=AUX, lw=0.9), fontsize=10, ha="center")
    ax.text(5.75, 2.52, r"$l_1=l_2=l_3$", ha="center", fontsize=10.5)

    ax.text(2.68, 3.48, r"$l_1$", fontsize=10.5)
    ax.text(4.85, 4.48, r"$l_2$", ha="center", fontsize=10.5)
    ax.text(5.70, 4.48, r"$d$", ha="center", fontsize=10.5)
    dim_arrow(ax, (5.70, 3.91), (5.70, 4.19), both=True, lw=0.9)
    ax.text(6.65, 4.45, r"$v$", ha="center", fontsize=10.5)
    flow_arrow(ax, (6.20, 4.05), (7.10, 4.05), lw=1.1)
    ax.text(9.60, 2.85, r"$l_3$", fontsize=10.5)

    # Top negative-pressure zone bracket [1.85, 11.05]
    ax.plot([1.85, 1.85], [2.42, 5.55], color=INK, lw=1.0, zorder=4)
    ax.plot([11.05, 11.05], [1.38, 5.55], color=INK, lw=1.0, zorder=4)
    dim_arrow(ax, (1.85, 5.38), (11.05, 5.38), label="负压区", text_offset=(0, 0.34), fontsize=11.5)
    return fig


@reg(2017, 11)
def draw_2017_11():
    # Nikuradse log-log friction chart faithful to original topology
    fig, ax = new_canvas(5.8, 4.6, (-0.4, 9.5), (-0.8, 8.2), equal=False)
    x0, x1, y0, y1 = 1.3, 8.2, 0.8, 6.9
    ax.add_patch(patches.Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none", edgecolor=INK, lw=1.8, zorder=4))
    ax.text(0.45, 7.22, r"$\lg(100\lambda)$", fontsize=11.5)
    ax.text(7.55, 0.25, r"$\lg Re$", fontsize=11.5)

    # Laminar line a-b meeting bottom frame at (2.95, y0)
    ax.plot([1.65, 2.95], [6.00, y0], color=INK, lw=1.8, zorder=5)
    ax.text(1.76, 5.95, r"$a$", fontsize=11)
    ax.text(3.04, 1.02, r"$b$", fontsize=11)

    # Critical bend c=(2.10, 4.20) -> knee (2.52, 3.88) -> straight Blasius smooth-turbulent line to (6.55, y0)
    cx, cy = 2.10, 4.20
    kx, ky = 2.52, 3.88
    bx_end, by_end = 6.55, y0
    ax.plot([cx, kx, bx_end], [cy, ky, by_end], color=INK, lw=1.8, zorder=5)
    ax.text(2.36, 4.38, r"$c$", fontsize=11)
    ax.text(4.82, 1.32, r"$d$", fontsize=11.5)

    def y_cd(x: float) -> float:
        return ky + (by_end - ky) * (x - kx) / (bx_end - kx)

    # Straight dashed fully-rough boundary e=(3.75, 5.20) -> f=(8.20, 1.75) on right frame!
    ex, ey = 3.75, 5.20
    fx, fy = x1, 1.75
    ax.plot([ex, fx], [ey, fy], ls="--", color=INK, lw=1.4, zorder=5)
    ax.text(3.72, 5.42, r"$e$", ha="center", fontsize=11.5)
    ax.text(8.35, 1.65, r"$f$", fontsize=11.5)

    def y_ef(x: float) -> float:
        return ey + (fy - ey) * (x - ex) / (fx - ex)

    # Topmost branch (l_1): rises cleanly from c-d knee (2.52, 3.88) to e, then nearly flat to right border
    t_top = np.linspace(0.0, 1.0, 40)
    top_x = (1 - t_top) ** 2 * kx + 2 * (1 - t_top) * t_top * 2.85 + t_top ** 2 * ex
    top_y = (1 - t_top) ** 2 * ky + 2 * (1 - t_top) * t_top * 5.05 + t_top ** 2 * ey
    ax.plot(top_x, top_y, color=INK, lw=1.4, zorder=4)
    ax.plot([ex, x1], [ey, ey - 0.22], color=INK, lw=1.4, zorder=4)
    ax.text(5.85, ey + 0.08, r"$l_1$", fontsize=10.5)

    # Lower 5 Nikuradse sand-roughness curves:
    # Every curve starts ON c-d, dips downward (spoon curve), rises to meet e-f, then goes gently right to x1
    specs = [
        (2.85, 4.22, -0.02, -0.15, ""),
        (3.32, 4.72, -0.12, -0.14, r"$l_2$"),
        (3.85, 5.42, -0.22, -0.12, ""),
        (4.48, 6.28, -0.26, -0.08, ""),
        (5.28, fx,   -0.25,  0.00, ""),
    ]
    for xs, xe, dip, tail_drop, lbl in specs:
        ys = y_cd(xs)
        ye = y_ef(xe)
        # Concave spoon control point strictly below chord ys->ye
        xc = 0.52 * xs + 0.48 * xe
        yc = min(ys, ye) + dip
        tt = np.linspace(0.0, 1.0, 40)
        bx = (1 - tt) ** 2 * xs + 2 * (1 - tt) * tt * xc + tt ** 2 * xe
        by = (1 - tt) ** 2 * ys + 2 * (1 - tt) * tt * yc + tt ** 2 * ye
        ax.plot(bx, by, color=INK, lw=1.3, zorder=4)
        if xe < x1 - 1e-3:
            ax.plot([xe, x1], [ye, ye + tail_drop], color=INK, lw=1.35, zorder=4)
        if lbl:
            ax.text(5.95, ye + 0.06, lbl, fontsize=10.5)
    return fig


@reg(2017, 15)
def draw_2017_15():
    # Horizontal tunnel i=0 with bell-mouth inlet, dome crest + zigzag break, gate ABOVE ceiling flush with tailwater
    fig, ax = new_canvas(6.8, 3.1, (0, 10.8), (0, 5.0))
    y_bed = 1.00
    y_ceil = 2.35
    x_in = 2.15
    x_gate = 8.05

    # Horizontal bed line (i=0)
    ax.plot([0.55, 9.95], [y_bed, y_bed], color=INK, lw=1.8, zorder=4)
    ax.text(5.25, 0.56, r"$i=0$", ha="center", fontsize=10.5)

    # Upstream reservoir surface & rounded bell-mouth + horizontal tunnel ceiling flush with downstream water
    y_up = 3.72
    water_surface(ax, 0.55, 2.22, y_up, mark_x=1.22, size=0.17, lw=1.5)
    # Smooth C-shaped inlet fairing from ceiling (2.15, 2.35) to (2.22, 3.72)
    t_bell = np.linspace(0.0, np.pi, 35)
    bx_bell = 2.18 - 0.42 * np.sin(t_bell)
    by_bell = 0.5 * (y_ceil + y_up) - 0.5 * (y_up - y_ceil) * np.cos(t_bell)
    ax.plot(bx_bell, by_bell, color=INK, lw=1.6, zorder=4)
    ax.plot([2.18, x_gate], [y_ceil, y_ceil], color=INK, lw=1.6, zorder=4)

    # Downstream water surface FLUSH with tunnel ceiling y_ceil = 2.35!
    water_surface(ax, x_gate + 0.24, 9.95, y_ceil, mark_x=9.25, size=0.17, lw=1.5)

    # Smooth earth/concrete top dome from (2.22, y_up) to (x_gate, y_ceil) with center break zigzag
    left_arch_x = np.linspace(2.22, 4.72, 35)
    t_la = (left_arch_x - 2.22) / (4.72 - 2.22)
    left_arch_y = y_up + 0.72 * np.sin(0.5 * np.pi * t_la) ** 0.85
    ax.plot(left_arch_x, left_arch_y, color=INK, lw=1.6, zorder=4)
    zig_x = [4.72, 4.84, 5.02, 5.14]
    zig_y = [left_arch_y[-1], left_arch_y[-1] - 0.16, left_arch_y[-1] + 0.16, left_arch_y[-1]]
    ax.plot(zig_x, zig_y, color=INK, lw=1.5, zorder=4)
    right_arch_x = np.linspace(5.14, x_gate, 45)
    t_ra = (right_arch_x - 5.14) / (x_gate - 5.14)
    right_arch_y = left_arch_y[-1] - (left_arch_y[-1] - y_ceil) * (t_ra ** 1.75)
    ax.plot(right_arch_x, right_arch_y, color=INK, lw=1.6, zorder=4)

    # Hatched control gate resting ON TOP of y_ceil (with small chamfer touching bottom edge, NOT hanging into tunnel)
    gate_poly = np.array([
        [x_gate + 0.04, y_ceil],
        [x_gate + 0.24, y_ceil + 0.10],
        [x_gate + 0.24, 3.22],
        [x_gate, 3.22],
        [x_gate, y_ceil + 0.06],
    ])
    ax.add_patch(patches.Polygon(gate_poly, closed=True, facecolor=CONCRETE, edgecolor=INK, lw=1.5, hatch="///", zorder=5))

    # Points A, B and flow arrow inside uniform tunnel
    y_pt = 1.66
    ax.plot(3.15, y_pt, "o", ms=4.5, color=INK, zorder=5)
    ax.text(3.32, y_pt - 0.04, r"$A$", fontsize=11.5)
    flow_arrow(ax, (4.30, y_pt), (5.35, y_pt), lw=1.5)
    ax.plot(6.35, y_pt, "o", ms=4.5, color=INK, zorder=5)
    ax.text(6.52, y_pt - 0.04, r"$B$", fontsize=11.5)
    return fig


@reg(2017, 16)
def draw_2017_16():
    fig, ax = new_canvas(6.4, 3.8, (0, 10.6), (0, 6.2))
    # Left & right tanks
    ax.add_patch(patches.Rectangle((0.8, 1.0), 2.1, 4.0, facecolor=WATER, edgecolor="none", zorder=1))
    ax.add_patch(patches.Rectangle((7.6, 1.0), 2.2, 3.2, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot([0.8, 0.8, 2.9, 2.9], [5.4, 1.0, 1.0, 1.45], color=INK, lw=1.9, zorder=4)
    ax.plot([2.9, 2.9], [2.05, 3.45], color=INK, lw=1.9, zorder=4)
    ax.plot([2.9, 2.9], [3.95, 5.4], color=INK, lw=1.9, zorder=4)
    ax.plot([7.6, 7.6], [5.4, 3.45], color=INK, lw=1.9, zorder=4)
    ax.plot([7.6, 7.6], [2.95, 2.05], color=INK, lw=1.9, zorder=4)
    ax.plot([7.6, 7.6, 9.8, 9.8], [1.45, 1.0, 1.0, 5.4], color=INK, lw=1.9, zorder=4)
    water_surface(ax, 0.8, 2.9, 5.0, mark_x=1.8)
    water_surface(ax, 7.6, 9.8, 4.2, mark_x=8.7)
    dim_arrow(ax, (6.5, 4.2), (6.5, 5.0), label=r"$H$", text_offset=(0.30, 0), ext_len=0.8, ext_dir=(1, 0), fontsize=11.5)

    # Upper & lower parallel pipes sloping slightly downward
    p1 = np.array([[2.9, 3.95], [7.6, 3.45], [7.6, 2.95], [2.9, 3.45]])
    p2 = np.array([[2.9, 2.05], [7.6, 2.05], [7.6, 1.45], [2.9, 1.45]])
    ax.add_patch(patches.Polygon(p1, closed=True, facecolor=WATER, edgecolor=INK, lw=1.7, zorder=2))
    ax.add_patch(patches.Polygon(p2, closed=True, facecolor=WATER, edgecolor=INK, lw=1.7, zorder=2))
    ax.text(5.25, 4.22, r"$q_{v1},\, d_1,\, L_1,\, \lambda$", ha="center", fontsize=10.5)
    ax.text(5.25, 1.05, r"$q_{v2},\, d_2,\, L_2,\, \lambda$", ha="center", fontsize=10.5)
    return fig


@reg(2017, 17)
def draw_2017_17():
    fig, ax = new_canvas(5.4, 4.0, (0, 9.0), (0, 6.4))
    # Vertical trapezoid flush with top water surface, top h_1, bottom h_2, height h, internal vertical dashed lines
    ty, by = 4.9, 1.3
    x_tl, x_tr = 2.0, 6.2
    x_bl, x_br = 3.2, 5.0
    trap = np.array([[x_tl, ty], [x_tr, ty], [x_br, by], [x_bl, by]])
    ax.add_patch(patches.Polygon(trap, closed=True, facecolor=WATER, edgecolor=INK, lw=2.0, zorder=3))
    water_surface(ax, 1.0, 7.4, ty, mark_x=6.8, size=0.18, lw=1.4)
    ax.plot([x_bl, x_bl], [by, ty], ls="--", color=AUX, lw=1.2, zorder=4)
    ax.plot([x_br, x_br], [by, ty], ls="--", color=AUX, lw=1.2, zorder=4)
    dim_arrow(ax, (x_tl, 5.65), (x_tr, 5.65), label=r"$h_1$", text_offset=(0, 0), ext_len=0.55, ext_dir=(0, -1), fontsize=11.5, bbox_white=True)
    dim_arrow(ax, (x_bl, 0.72), (x_br, 0.72), label=r"$h_2$", text_offset=(0, -0.32), ext_len=0.45, ext_dir=(0, 1), fontsize=11.5)
    dim_arrow(ax, (7.6, by), (7.6, ty), label=r"$h$", text_offset=(0.30, 0), ext_len=2.1, ext_dir=(-1, 0), fontsize=11.5)
    return fig


@reg(2017, 18)
def draw_2017_18():
    fig, ax = new_canvas(5.8, 4.0, (0, 9.8), (0, 6.5))
    tx0, tx1, ty0, ty1 = 1.6, 4.8, 0.7, 5.7
    # Two layers: bottom rho_2, top rho_1 (depth h_1)
    ax.add_patch(patches.Rectangle((tx0, ty0), tx1 - tx0, 2.0, facecolor="#f1f5f9", edgecolor="none", zorder=1))
    ax.add_patch(patches.Rectangle((tx0, 2.7), tx1 - tx0, 2.35, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot([tx0, tx0, tx1, tx1], [ty1, ty0, ty0, ty1], color=INK, lw=2.0, zorder=4)
    water_surface(ax, tx0, tx1, 5.05, mark_x=3.2)
    ax.plot([tx0, tx1], [2.7, 2.7], color=INK, lw=1.5, zorder=4)
    ax.text(3.2, 3.85, r"$\rho_1$", ha="center", fontsize=13)
    ax.text(3.2, 1.70, r"$\rho_2$", ha="center", fontsize=13)
    dim_arrow(ax, (1.1, 2.7), (1.1, 5.05), label=r"$h_1$", text_offset=(-0.30, 0), ext_len=0.4, ext_dir=(1, 0), fontsize=11.5)

    # Upper piezometer from rho_1 -> flush at y=5.05
    p1x, p2x, tw = 5.9, 7.2, 0.24
    # Branch from rho_1 at y=3.75
    ax.add_patch(patches.Rectangle((tx1, 3.63), p1x - tx1 + tw / 2, 0.24, facecolor=WATER, edgecolor="none", zorder=2))
    ax.add_patch(patches.Rectangle((p1x - tw / 2, 3.63), tw, 5.05 - 3.63, facecolor=WATER, edgecolor="none", zorder=2))
    ax.plot([tx1, p1x - tw / 2, p1x - tw / 2], [3.87, 3.87, 5.75], color=INK, lw=1.5, zorder=4)
    ax.plot([tx1, p1x + tw / 2, p1x + tw / 2], [3.63, 3.63, 5.75], color=INK, lw=1.5, zorder=4)
    water_surface(ax, p1x - tw / 2, p1x + tw / 2, 5.05, mark_x=p1x, size=0.14, lw=1.3)

    # Lower piezometer from rho_2 at y=1.4 -> level y=3.75
    ax.add_patch(patches.Rectangle((tx1, 1.28), p2x - tx1 + tw / 2, 0.24, facecolor="#f1f5f9", edgecolor="none", zorder=2))
    ax.add_patch(patches.Rectangle((p2x - tw / 2, 1.28), tw, 3.75 - 1.28, facecolor="#f1f5f9", edgecolor="none", zorder=2))
    ax.plot([tx1, p2x - tw / 2, p2x - tw / 2], [1.52, 1.52, 5.75], color=INK, lw=1.5, zorder=4)
    ax.plot([tx1, p2x + tw / 2, p2x + tw / 2], [1.28, 1.28, 5.75], color=INK, lw=1.5, zorder=4)
    water_surface(ax, p2x - tw / 2, p2x + tw / 2, 3.75, mark_x=p2x, size=0.14, lw=1.3)

    # Delta h between the two piezometer levels
    ax.plot([p1x + tw / 2, 8.4], [5.05, 5.05], ls=":", color=AUX, lw=1.0)
    ax.plot([p2x + tw / 2, 8.4], [3.75, 3.75], ls=":", color=AUX, lw=1.0)
    dim_arrow(ax, (8.1, 3.75), (8.1, 5.05), label=r"$\Delta h$", text_offset=(0.45, 0), fontsize=11.5)
    return fig


@reg(2017, 19)
def draw_2017_19():
    fig, ax = new_canvas(6.4, 3.4, (0, 11.2), (0, 5.6))
    # Horizontal Venturi pipe: d1=1.0 half? radius 0.55 on left/right, throat radius 0.26 at x=[4.6, 5.6]
    yc = 4.05
    xs = [0.6, 3.6, 4.6, 5.8, 7.6, 10.6]
    rs = [0.52, 0.52, 0.24, 0.24, 0.52, 0.52]
    top = [(x, yc + r) for x, r in zip(xs, rs)]
    bot = [(x, yc - r) for x, r in zip(xs, rs)]
    ax.add_patch(patches.Polygon(np.array(top + bot[::-1]), closed=True, facecolor=WATER, edgecolor="none", zorder=1))
    ax.plot([p[0] for p in top], [p[1] for p in top], color=INK, lw=1.9, zorder=4)
    ax.plot([p[0] for p in bot], [p[1] for p in bot], color=INK, lw=1.9, zorder=4)
    ax.plot([0.6, 10.6], [yc, yc], ls="-.", color=AUX, lw=0.9, zorder=3)
    dim_arrow(ax, (2.2, yc - 0.52), (2.2, yc + 0.52), label=r"$d_1$", text_offset=(0, 0.78), fontsize=11)
    dim_arrow(ax, (5.2, yc - 0.24), (5.2, yc + 0.24), label=r"$d_2$", text_offset=(0, 0.56), fontsize=11)
    flow_arrow(ax, (9.0, yc), (10.3, yc), label=r"$Q_v$", text_offset=(0.65, 0.35), fontsize=11.5)

    # U-tube mercury manometer connected at x=3.1 (inlet) and x=5.2 (throat)
    x1, x2 = 3.1, 5.2
    u_manometer(ax, x1, yc - 0.52, x2, yc - 0.24, y_bot=0.8, y_m1=1.45, y_m2=2.55, tube_w=0.22)
    ax.plot([x1 + 0.14, 4.5], [1.45, 1.45], ls=":", color=AUX, lw=1.0)
    ax.plot([3.9, x2 - 0.14], [2.55, 2.55], ls=":", color=AUX, lw=1.0)
    dim_arrow(ax, (4.15, 1.45), (4.15, 2.55), label=r"$\Delta h$", text_offset=(-0.38, 0), fontsize=11.5)
    return fig


@reg(2017, 26)
def draw_2017_26():
    fig, ax = new_canvas(6.8, 3.2, (0, 11.8), (0, 5.2), equal=False)
    # Two panels side-by-side: Case 1 centered, Case 2 off-center (1.25cm top, 0.75cm bottom)
    for idx, (x0, x1, d1_lbl, d2_lbl, y_plate) in enumerate([
        (0.8, 5.2, r"$\delta_1 = 1\,\mathrm{cm}$", r"$\delta_2 = 1\,\mathrm{cm}$", 2.60),
        (6.6, 11.0, r"$\delta_1 = 1.25\,\mathrm{cm}$", r"$\delta_2 = 0.75\,\mathrm{cm}$", 2.15),
    ]):
        ground_hatch(ax, x0, 4.1, x1, 4.1, side="above", step=0.28, depth=0.18, lw=2.0)
        ground_hatch(ax, x0, 1.1, x1, 1.1, side="below", step=0.28, depth=0.18, lw=2.0)
        ax.add_patch(patches.Rectangle((x0, 1.1), x1 - x0, 3.0, facecolor=OIL, edgecolor="none", alpha=0.55, zorder=1))
        # Thin moving plate (starts right of gap labels so delta labels never collide)
        px0, px1 = x0 + 2.15, x1 - 0.85
        ax.plot([px0, px1], [y_plate, y_plate], color=INK, lw=4.0, zorder=5)
        flow_arrow(ax, (px1 + 0.05, y_plate), (x1 + 0.35, y_plate), label=r"$F$", text_offset=(0, 0.35), fontsize=11.5)
        # Gap dimension arrows cleanly on left of plate
        dx = x0 + 0.55
        ax.plot([dx - 0.15, px0 - 0.08], [y_plate, y_plate], ls=":", color=AUX, lw=0.95)
        dim_arrow(ax, (dx, y_plate), (dx, 4.1), label=d1_lbl, text_offset=(0.82, 0), fontsize=9.8)
        dim_arrow(ax, (dx, 1.1), (dx, y_plate), label=d2_lbl, text_offset=(0.82, 0), fontsize=9.8)
    return fig


@reg(2017, 27)
def draw_2017_27():
    fig, ax = new_canvas(6.0, 4.0, (0, 10.0), (0, 6.4))
    ground_hatch(ax, 0.8, 0.9, 9.2, 0.9, side="below", step=0.30, depth=0.20, lw=2.0)
    # Cylinder radius R=1.6 centered at (5.0, 2.5) resting on y=0.9
    cx, cy, R = 5.0, 2.5, 1.6
    # Point A on upper-left of circle (cos 135 deg? In original: vertical wall rests against A on upper-left/top-left!)
    # Wait: look at stem: D=2m -> R=1m; h1=3m; hA=1.3m -> y_A = h1 - hA = 3 - 1.3 = 1.7m above bed = 0.7m above center!
    # Vertical baffle sits against cylinder at x_wall = cx - sqrt(R^2 - 0.7^2) = cx - 0.714*R!
    sin_a = 0.70
    ax_pt = cx - R * math.sqrt(1 - sin_a ** 2)
    ay_pt = cy + R * sin_a
    # Water fills left and right (stop at right & left edges of cylinder)
    ax.add_patch(patches.Rectangle((1.0, 0.9), ax_pt - 1.0, 4.2, facecolor=WATER, edgecolor="none", zorder=1))
    # Water wedge under left arc of cylinder down to bed
    th_bot = np.linspace(math.pi - math.asin(sin_a), 1.5 * math.pi, 40)
    ax.add_patch(patches.Polygon(np.vstack([[[ax_pt, 0.9]], [[ax_pt, ay_pt]], np.column_stack([cx + R * np.cos(th_bot), cy + R * np.sin(th_bot)]), [[cx, 0.9]]]),
                                 closed=True, facecolor=WATER, edgecolor="none", zorder=1))
    ax.add_patch(patches.Rectangle((cx, 0.9), 3.9, 3.3, facecolor=WATER, edgecolor="none", zorder=1))
    # Cylinder circle (white fill on top of right water overlap so cylinder looks solid!)
    ax.add_patch(patches.Circle((cx, cy), R, facecolor="white", edgecolor=INK, lw=2.0, zorder=4))
    # Diameter D arrow inside cylinder
    d_ang = math.radians(-42)
    dim_arrow(ax, (cx - R * math.cos(d_ang), cy - R * math.sin(d_ang)),
              (cx + R * math.cos(d_ang), cy + R * math.sin(d_ang)), label=r"$D$", text_offset=(0.15, 0.25), fontsize=12)
    # Vertical baffle wall at x = ax_pt rising from A up to top
    ax.add_patch(patches.Rectangle((ax_pt - 0.14, ay_pt), 0.14, 5.5 - ay_pt, facecolor=CONCRETE, edgecolor=INK, lw=1.7, hatch="///", zorder=5))
    ax.plot(ax_pt, ay_pt, "o", ms=5, color=INK, zorder=6)
    ax.text(ax_pt - 0.38, ay_pt - 0.25, r"$A$", fontsize=12, fontweight="bold")
    # Water surfaces: left h1 = 5.1 (relative to y=0.9), right h2 = 4.2
    water_surface(ax, 1.0, ax_pt - 0.14, 5.1, mark_x=2.0)
    water_surface(ax, cx + R * math.sqrt(max(0, 1 - ((4.2 - cy) / R) ** 2)) if 4.2 < cy + R else ax_pt, 8.9, 4.2, mark_x=7.8)
    dim_arrow(ax, (1.55, 0.9), (1.55, 5.1), label=r"$h_1$", text_offset=(-0.30, 0), fontsize=11.5)
    dim_arrow(ax, (2.75, ay_pt), (2.75, 5.1), label=r"$h_A$", text_offset=(-0.32, 0), ext_len=0.9, ext_dir=(1, 0), fontsize=11.5)
    dim_arrow(ax, (8.1, 0.9), (8.1, 4.2), label=r"$h_2$", text_offset=(0.30, 0), fontsize=11.5)
    return fig


@reg(2017, 28)
def draw_2017_28():
    fig, ax = new_canvas(6.4, 4.0, (0, 10.6), (0, 6.4))
    # Upstream reservoir bank & embankment & tailrace floor
    ground_hatch(ax, 0.8, 1.2, 2.7, 1.2, side="below", step=0.28, depth=0.16, lw=1.8)
    ground_hatch(ax, 2.7, 1.2, 2.7, 3.85, side="right", step=0.28, depth=0.16, lw=1.8)
    ground_hatch(ax, 2.7, 3.85, 4.5, 4.95, side="below", step=0.28, depth=0.16, lw=1.8)
    ground_hatch(ax, 4.5, 4.95, 6.4, 4.95, side="below", step=0.28, depth=0.16, lw=1.8)
    ground_hatch(ax, 6.4, 4.95, 7.8, 3.25, side="below", step=0.28, depth=0.16, lw=1.8)
    ground_hatch(ax, 7.8, 3.25, 7.8, 0.9, side="left", step=0.28, depth=0.16, lw=1.8)
    ground_hatch(ax, 7.8, 0.9, 9.6, 0.9, side="below", step=0.28, depth=0.16, lw=1.8)

    # Siphon pipe centerline: intake (1.8, 2.0) -> up to crown (4.4..6.5, 5.25) -> down to outlet (8.2, 1.55)
    cx = np.array([1.8, 1.8, 4.4, 6.5, 8.2, 8.2])
    cy = np.array([2.0, 3.85, 5.25, 5.25, 3.25, 1.55])
    # Draw smooth double-walled siphon
    hp = 0.16
    ux, uy, lx, ly = [], [], [], []
    # Simple offset per vertex matching original crisp polygonal siphon bends
    pts_top = [(1.8 - hp, 2.0), (1.8 - hp, 3.92), (4.35, 5.41), (6.58, 5.41), (8.36, 3.30), (8.36, 1.55)]
    pts_bot = [(1.8 + hp, 2.0), (1.8 + hp, 3.78), (4.45, 5.09), (6.42, 5.09), (8.04, 3.20), (8.04, 1.55)]
    ax.add_patch(patches.Polygon(np.array(pts_top + pts_bot[::-1]), closed=True, facecolor=WATER, edgecolor="none", zorder=2))
    ax.plot([p[0] for p in pts_top], [p[1] for p in pts_top], color=INK, lw=1.7, zorder=4)
    ax.plot([p[0] for p in pts_bot], [p[1] for p in pts_bot], color=INK, lw=1.7, zorder=4)

    # Upstream & downstream water surfaces
    water_surface(ax, 0.8, 2.7, 3.85, mark_x=1.25, size=0.18)
    water_surface(ax, 7.8, 9.6, 1.55, mark_x=9.0, size=0.18)
    ax.text(0.90, 4.02, "1", fontsize=11, fontweight="bold")
    ax.plot(1.8, 3.85, "o", ms=4, color=INK, zorder=5)
    ax.text(2.12, 3.50, "2", fontsize=11, fontweight="bold")
    ax.text(6.5, 5.55, "3", fontsize=11, fontweight="bold")
    ax.text(8.55, 1.85, "4", fontsize=11, fontweight="bold")
    flow_arrow(ax, (4.9, 5.25), (5.8, 5.25), label=r"$V$", text_offset=(0, 0.35), fontsize=11.5)
    # z_3 = 2m crown above water surface 1 & h drop from 1 to 4 (clean spacing)
    ax.plot([0.35, 4.4], [5.25, 5.25], ls=":", color=AUX, lw=1.0)
    dim_arrow(ax, (0.55, 3.85), (0.55, 5.25), label=r"$z_3 = 2\,\mathrm{m}$", text_offset=(-0.05, 0.95), fontsize=10.5)
    ax.plot([0.35, 0.8], [3.85, 3.85], ls=":", color=AUX, lw=0.9)
    ax.plot([2.7, 8.6], [3.85, 3.85], ls=":", color=AUX, lw=0.9)
    dim_arrow(ax, (3.65, 1.55), (3.65, 3.85), label=r"$h$", text_offset=(0.25, 0), ext_len=0.7, ext_dir=(1, 0), fontsize=11.5)
    return fig


@reg(2017, 29)
def draw_2017_29():
    fig, ax = new_canvas(6.4, 3.8, (0, 10.6), (0, 6.2))
    ang = math.radians(28)
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    # Base anchor line below slope (hatched bedrock)
    gx0, gy0 = 1.6, 1.1
    gx1, gy1 = 9.0, 1.1 + 7.4 * math.tan(ang)
    ground_hatch(ax, gx0, gy0, gx1, gy1, side="below", step=0.30, depth=0.20, lw=1.9)
    # Pipe tapering from wide (r1=0.65) on lower-left to narrower (r2=0.32) on upper-right
    ax_0, ay_0 = 1.4, 1.8
    s_all = [0.0, 2.2, 5.6, 8.2]
    r_all = [0.58, 0.58, 0.28, 0.28]
    top_pts = [(ax_0 + s * ca + r * nx, ay_0 + s * sa + r * ny) for s, r in zip(s_all, r_all)]
    bot_pts = [(ax_0 + s * ca - r * nx, ay_0 + s * sa - r * ny) for s, r in zip(s_all, r_all)]
    # Concrete anchor block enclosing the tapered middle section s in [2.0, 6.0]
    a_poly = np.array([
        [ax_0 + 2.0 * ca - 0.95 * nx, ay_0 + 2.0 * sa - 0.95 * ny],
        [ax_0 + 6.0 * ca - 0.95 * nx, ay_0 + 6.0 * sa - 0.95 * ny],
        [ax_0 + 6.0 * ca + 1.05 * nx, ay_0 + 6.0 * sa + 1.05 * ny],
        [ax_0 + 2.0 * ca + 1.05 * nx, ay_0 + 2.0 * sa + 1.05 * ny],
    ])
    ax.add_patch(patches.Polygon(a_poly, closed=True, facecolor=CONCRETE, edgecolor=INK, lw=1.8, zorder=2))
    # Subtle gravel stipple dots on anchor block (top & bottom wings)
    for sc, nc in [(2.9, 0.72), (3.8, 0.78), (4.8, 0.72), (5.3, -0.68), (3.4, -0.72), (4.3, -0.68)]:
        ax.plot(ax_0 + sc * ca + nc * nx, ay_0 + sc * sa + nc * ny, marker="^", ms=4.0, mfc="none", mec=AUX, mew=0.9, zorder=2.5)
    # Pipe polygon on top of block
    p_poly = np.array(top_pts + bot_pts[::-1])
    ax.add_patch(patches.Polygon(p_poly, closed=True, facecolor=WATER, edgecolor="none", zorder=3))
    ax.plot([p[0] for p in top_pts], [p[1] for p in top_pts], color=INK, lw=1.9, zorder=4)
    ax.plot([p[0] for p in bot_pts], [p[1] for p in bot_pts], color=INK, lw=1.9, zorder=4)
    flow_arrow(ax, (ax_0 + 2.8 * ca, ay_0 + 2.8 * sa), (ax_0 + 4.4 * ca, ay_0 + 4.4 * sa), lw=1.7)
    # 30 deg angle arc (clear label)
    ax.plot([gx0, 4.7], [gy0, gy0], color=INK, lw=1.4, zorder=4)
    angle_arc(ax, (gx0, gy0), 0, 28, radius=1.75, label=r"$30^{\circ}$", label_r=2.35, fontsize=11)
    return fig


@reg(2017, 31)
def draw_2017_31():
    fig, ax = new_canvas(6.8, 3.3, (0, 11.8), (0, 5.2), equal=False)
    # Steep positive slope (i > 0) joining horizontal channel (i = 0) at A-A (x=5.6, y=1.3)
    xb, yb = 5.6, 1.3
    ground_hatch(ax, 0.8, 3.55, xb, yb, side="below", step=0.28, depth=0.18, lw=2.0)
    ground_hatch(ax, xb, yb, 11.2, yb, side="below", step=0.28, depth=0.18, lw=2.0)
    # Critical line C (h_c) above steep bed & horizontal bed
    hc = 0.95
    ax.plot([0.8, xb], [3.55 + hc, yb + hc], ls="--", color=INK, lw=1.3, zorder=4)
    ax.plot([xb, 11.2], [yb + hc, yb + hc], ls="--", color=INK, lw=1.3, zorder=4)
    ax.text(0.55, 3.55 + hc, r"$C$", fontsize=11.5)
    # Section A-A vertical break line
    section_cut(ax, (xb, 1.0), (xb, 3.45), label="A", fontsize=11)
    dim_arrow(ax, (4.3, 1.95), (4.3, 1.95 + hc), label=r"$h_c$", text_offset=(0.35, 0), fontsize=11)
    flow_arrow(ax, (1.4, 3.85), (2.9, 3.13), label=r"$q_v$", text_offset=(0.35, 0.55), fontsize=11.5)
    ax.text(2.4, 1.95, r"$i > 0$", fontsize=11.5)
    ax.text(8.4, 0.72, r"$i = 0$", fontsize=11.5)
    return fig


# ==============================================================================
# Runner + CLI + Parallel Execution + Before/After QA Builder
# ==============================================================================


def _render_one(task: tuple[int, int]) -> tuple[int, int, str, str]:
    year, no = task
    stem = f"q{no:02d}_orig"
    fig = REGISTRY[(year, no)]()
    png_p, webp_p = backup_and_save(fig, "hhu-814", year, stem, ROOT)
    return year, no, str(png_p), str(webp_p)


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch redraw all 35 hand-drawn HHU 814 original exam figures.")
    ap.add_argument("--year", type=int, default=0, help="Only render figures for this year (e.g. 2022)")
    ap.add_argument("--only", default="", help="Comma-separated year:no pairs, e.g. 2022:3,2018:20")
    ap.add_argument("--workers", type=int, default=4, help="Parallel worker processes (default 4)")
    ap.add_argument("--qa-dir", default="", help="Optional directory to output Before/After QA sheets")
    args = ap.parse_args()

    if args.only:
        tasks = []
        for tok in args.only.split(","):
            tok = tok.strip()
            if not tok:
                continue
            y_s, n_s = tok.split(":")
            key = (int(y_s), int(n_s))
            if key not in REGISTRY:
                raise SystemExit(f"Unknown figure key: {key}")
            tasks.append(key)
    elif args.year:
        tasks = sorted([k for k in REGISTRY if k[0] == args.year])
    else:
        tasks = sorted(REGISTRY.keys())

    print(f"Rendering {len(tasks)} figures with workers={args.workers} ...")
    if args.workers > 1 and len(tasks) > 1:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
            for yr, no, png_s, webp_s in pool.map(_render_one, tasks):
                print(f"  [OK] {yr} Q{no:02d} -> {Path(webp_s).name}")
    else:
        for t in tasks:
            yr, no, png_s, webp_s = _render_one(t)
            print(f"  [OK] {yr} Q{no:02d} -> {Path(webp_s).name}")

    if args.qa_dir:
        qa_dir = Path(args.qa_dir)
        pairs = []
        for yr, no in tasks:
            stem = f"q{no:02d}_orig"
            bak_p = ROOT / "assets_src" / "handdrawn_backup" / "hhu-814" / str(yr) / f"{stem}.webp"
            new_p = ROOT / "web" / "public" / "data" / "hhu-814" / "figures" / str(yr) / f"{stem}.webp"
            pairs.append((f"{yr} Q{no:02d} ({stem})", bak_p, new_p))
        sheets = build_qa_sheets(pairs, qa_dir, prefix="qa", pairs_per_sheet=4)
        print(f"Generated {len(sheets)} QA sheets:")
        for sp in sheets:
            print(f"  {sp}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
