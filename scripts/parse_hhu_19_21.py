# -*- coding: utf-8 -*-
r"""
Parse Hohai University 814 Hydraulics exam years 2021, 2020, 2019 from
`河海大学已整理真题/{2021,2020,2019}年河海大学814《水力学》考研真题及详细解析.docx`
into:
  1) Standardized packs: `河海大学已整理数据/{year}/{year}.json` + `figures/*.png`
  2) Web-ready packs:    `web/public/data/hhu-814/{year}.json` + `figures/{year}/*.webp`

Includes independent physical/numerical verification & diagram fixes:
  - 2021 Q28 & Q29: clean control-volume / sharp-elbow HGL-THL diagrams matching stem geometry
  - 2020 Q10: fix judge answer to True (`√`) — stem diagram shows a sudden-expansion pipe
    with erroneously stepped-down HGL, equal velocity-head gaps, and unattenuated slope J2
  - 2020 Q26: fix horizontally flipped 9-plate folded wall pressure-body diagram to true `\` orientation
  - 2019 Q03: crisp high-DPI redraw of submerged vs emergent gate figures (fixing garbled scan labels)
  - 2019 Q27: fix siphon submerged-outlet THL/HGL diagram (THL vertical exit drop v²/2g, HGL smooth)
  - 2019 Q29: refine supercritical root 0.4783 -> exact 0.4828 m in analysis & Es-h diagram
"""

import copy
import json
import math
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse_2024_2025 as base_parser

# Extend OMML symbol mappings for 2019-2021 docx files
base_parser.GREEK_AND_MATH_MAP.update({
    "κ": r"\kappa ",
    "∑": r"\sum ",
    "∈": r"\in ",
    "Φ": r"\Phi ",
    "Ω": r"\Omega ",
    "≡": r"\equiv ",
    "≢": r"\not\equiv ",
    "–": "-",
    "—": "-",
    "∫": r"\int ",
    "∬": r"\iint ",
    "∮": r"\oint ",
})

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent
SRC_DOCX_DIR = ROOT / "河海大学已整理真题"
STD_ROOT = ROOT / "河海大学已整理数据"
WEB_COURSE_DIR = ROOT / "web" / "public" / "data" / "hhu-814"


# ==============================================================================
# Curated Metadata: 2021 (Q1 - Q31, total = 150 pts)
# Valid chapters in hhu-814/chapters.json: {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}
# ==============================================================================
META_2021 = {
    1:  {"title": "双层不混溶静止液体测压管水头大小判别", "chapter": 2, "kps": ["静水压强基本方程", "水头与能量量纲"], "method": "等压面静水压强递推法", "difficulty": 2},
    2:  {"title": "紊流脉动流速的时间平均值特性", "chapter": 4, "kps": ["断面流速分布"], "method": "物理概念定义辨析", "difficulty": 1},
    3:  {"title": "有压管道突然扩大段总水头线与测压管水头线判别", "chapter": 6, "kps": ["总水头线与测压管水头线", "恒定总流能量方程"], "method": "总水头线与测压管水头线判据", "difficulty": 2},
    4:  {"title": "等直径直管恒定流与放置倾角无关的均匀流判别", "chapter": 3, "kps": ["恒定流与均匀流判别"], "method": "物理概念定义辨析", "difficulty": 1},
    5:  {"title": "恒定流量条件下圆管雷诺数与管径反比关系", "chapter": 4, "kps": ["雷诺数与流态判别", "恒定总流连续性方程"], "method": "物理概念定义辨析", "difficulty": 1},
    6:  {"title": "宽浅缓坡明渠 M1 壅水曲线断面比能沿程变化判别", "chapter": 8, "kps": ["断面单位能量(比能)", "缓坡水面曲线(M1/M2/M3)", "临界水深与临界底坡"], "method": "比能沿程导数判别法", "difficulty": 3},
    7:  {"title": "牛顿流体的易流动性与受剪变形特性", "chapter": 1, "kps": ["牛顿内摩擦定律", "连续介质假设"], "method": "物理概念定义辨析", "difficulty": 1},
    8:  {"title": "急变流与层流两类流动划分标准辨析", "chapter": 4, "kps": ["雷诺数与流态判别"], "method": "概念偷换词辨析", "difficulty": 2},
    9:  {"title": "实际恒定管流测压管水头线的升降规律", "chapter": 6, "kps": ["总水头线与测压管水头线", "有压渐扩管压强变化"], "method": "总水头线与测压管水头线判据", "difficulty": 1},
    10: {"title": "静止液体平面受压面压心与形心相对位置辨析", "chapter": 2, "kps": ["平面静水总压力"], "method": "概念偷换词辨析", "difficulty": 2},
    11: {"title": "由当地大气压与真空度换算绝对压强", "chapter": 2, "kps": ["真空高度(真空度)", "静水压强基本方程"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "mini-calc"},
    12: {"title": "阀门突闭直接水击总压强儒可夫斯基公式计算", "chapter": 6, "kps": ["有压管道水击(水锤)", "儒可夫斯基公式"], "method": "水击相长判别与儒氏公式", "difficulty": 1, "subType": "mini-calc"},
    13: {"title": "毕托管倾斜测压管液面铅垂高差计算", "chapter": 3, "kps": ["恒定总流能量方程"], "method": "两段伯努利方程联立法", "difficulty": 2, "subType": "mini-calc"},
    14: {"title": "双层液体中倒三角形挡水板上下两部分压力之比", "chapter": 2, "kps": ["平面静水总压力", "静水压强基本方程"], "method": "平面总压力形心法/分块合成法", "difficulty": 3, "subType": "mini-calc"},
    15: {"title": "由断面比能与水深比值求矩形明渠弗劳德数", "chapter": 8, "kps": ["断面单位能量(比能)", "弗劳德数判急缓流"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 1, "subType": "mini-calc"},
    16: {"title": "等过水面积圆形与方形管道均匀流壁面切应力之比", "chapter": 4, "kps": ["圆管均匀流切应力分布"], "method": "圆管切应力线性分布性质", "difficulty": 2, "subType": "mini-calc"},
    17: {"title": "铅垂矩形挡水板静水总压力计算", "chapter": 2, "kps": ["平面静水总压力"], "method": "平面总压力形心法/分块合成法", "difficulty": 1, "subType": "mini-calc"},
    18: {"title": "同一管流断面动能修正系数与动量修正系数大小比较", "chapter": 3, "kps": ["恒定总流能量方程", "恒定总流动量方程"], "method": "核心基本概念记忆", "difficulty": 2, "subType": "blank"},
    19: {"title": "等管径两圆管雷诺数之比与流量之比关系", "chapter": 4, "kps": ["雷诺数与流态判别"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "mini-calc"},
    20: {"title": "由圆管流量与水力坡度反算沿程阻力系数", "chapter": 4, "kps": ["达西-韦斯巴赫公式", "沿程水头损失规律"], "method": "核心基本概念记忆", "difficulty": 2, "subType": "mini-calc"},
    21: {"title": "梯形水力最佳断面正常水深计算", "chapter": 7, "kps": ["水力最佳断面", "梯形断面水力要素"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 2, "subType": "mini-calc"},
    22: {"title": "等径等雷诺数条件下冷热水管流量大小比较", "chapter": 4, "kps": ["雷诺数与流态判别"], "method": "物理概念定义辨析", "difficulty": 2, "subType": "blank"},
    23: {"title": "等径等阻不等长并联长管流量比计算", "chapter": 6, "kps": ["长管串并联与三水池问题"], "method": "长管阻抗与多水池节点能量平衡", "difficulty": 2, "subType": "mini-calc"},
    24: {"title": "两恒定水位水箱连通管道断面平均流速计算", "chapter": 6, "kps": ["简单短管自由出流", "恒定总流能量方程"], "method": "短管自由出流流量公式判别", "difficulty": 2, "subType": "mini-calc"},
    25: {"title": "溢流堰重力相似模型长度比尺计算", "chapter": 13, "kps": ["弗劳德相似准则", "流量比尺换算"], "method": "弗劳德比尺幂次换算法", "difficulty": 1, "subType": "mini-calc"},
    26: {
        "title": "线性与抛物线形流速分布壁面切应力之比求解",
        "chapter": 1,
        "kps": ["牛顿内摩擦定律"],
        "method": "分层液体切应力连续与速度叠加法",
        "difficulty": 2,
        "rubric": [
            {"label": "由线性流速分布 u(y) = Uy/h 求得壁面切应力 τ1 = μU/h", "pts": 5},
            {"label": "代入无滑移、表面流速 U 及表面切应力为零条件求得抛物线分布 u(y) = 2Uy/h - Uy²/h² 及 τ2 = 2μU/h", "pts": 7},
            {"label": "准确求得两种流速分布下壁面切应力比值 τ1/τ2 = 1/2（或 0.5）", "pts": 3},
        ],
    },
    27: {
        "title": "密闭容器油水双层液体对组合双半圆弧曲面静水总压力计算",
        "chapter": 2,
        "kps": ["静水压强基本方程", "圆柱曲面静水总压力", "压力体图与虚压力体"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 4,
        "rubric": [
            {"label": "由右侧敞口测压管液面与 A 齐平递推求得 pB = 9.81 kPa、pC = 29.43 kPa 及顶部气室压强 pA = 3.924 kPa", "pts": 5},
            {"label": "分别计算 AB 与 BC 段水平投影静水压力并合成 Px ≈ 46.11 kN（水平向左）", "pts": 5},
            {"label": "正确判别 AB 半圆柱油体虚压力体（向上 2.311 kN）与 BC 半圆柱水体实压力体（向下 15.410 kN），求得净铅垂分力 Pz ≈ 13.10 kN（向下）", "pts": 6},
            {"label": "合成曲面静水总压力 P ≈ 47.93 kN 并给出方向角 θ ≈ 15.86°（指向左下方）", "pts": 4},
        ],
    },
    28: {
        "title": "竖直渐扩弯管自下而上流动的水流竖直作用力计算",
        "chapter": 3,
        "kps": ["恒定总流连续性方程", "恒定总流能量方程", "恒定总流动量方程", "弯管/底坎水流作用力"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 3,
        "rubric": [
            {"label": "求得进出口流速 v1 ≈ 1.592 m/s、v2 ≈ 0.398 m/s，列能量方程解得出口断面压强 p2 ≈ 16.28 kPa", "pts": 7},
            {"label": "计算两端动水总压力 P1、P2 与管内水重 G = 24.53 N，列竖直向控制体动量方程求得管壁反力 Rz ≈ 78.85 N（向上）", "pts": 9},
            {"label": "由牛顿第三定律给出水流对弯管的竖直作用力 Fz ≈ 78.85 N（方向竖直向下，单位准确为 N）", "pts": 4},
        ],
    },
    29: {
        "title": "水池引水管道直角弯管局部水头损失系数计算",
        "chapter": 6,
        "kps": ["恒定总流能量方程", "达西-韦斯巴赫公式", "总水头线与测压管水头线"],
        "method": "两段伯努利方程联立法",
        "difficulty": 3,
        "rubric": [
            {"label": "由 2 分钟出水量求得流量 Q = 0.006 m³/s、管内平均流速 v ≈ 0.764 m/s 及流速水头 v²/(2g) ≈ 0.0298 m", "pts": 5},
            {"label": "由达西公式求得 AB 段沿程水头损失 hf = λ(LAB/d)(v²/2g) ≈ 0.0892 m", "pts": 5},
            {"label": "列 A—B 断面能量方程求得总水头损失 hw = 0.126 m，解得弯管局部损失系数 ζ ≈ 1.24", "pts": 5},
        ],
    },
    30: {
        "title": "平面不可压缩流场线变形率、流函数与流速势函数求解",
        "chapter": 5,
        "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 3,
        "rubric": [
            {"label": "由速度偏导数求得三个方向线变形率 εx = 2x + 1、εy = -2x - 1、εz = 0", "pts": 5},
            {"label": "验证连续性方程 ∂ux/∂x + ∂uy/∂y = 0 成立，偏积分求得流函数 ψ = x²y + xy - y³/3 + C1", "pts": 8},
            {"label": "验证无旋条件 ωz = 0 成立，偏积分求得流速势函数 φ = x³/3 - xy² + x²/2 - y²/2 + C2", "pts": 7},
        ],
    },
    31: {
        "title": "等腰梯形排水明渠恒定均匀流流量计算",
        "chapter": 7,
        "kps": ["梯形断面水力要素", "明渠均匀流曼宁公式"],
        "method": "水力要素计算+曼宁公式+水力深度Fr判据",
        "difficulty": 2,
        "rubric": [
            {"label": "求得渠道底坡 i = 0.0001、过水断面面积 A = 16 m²、湿周 χ ≈ 12.94 m 及水力半径 R ≈ 1.236 m", "pts": 5},
            {"label": "应用谢才—曼宁公式求得谢才系数 C ≈ 69.06 m^(1/2)/s 及均匀流排水量 Q ≈ 12.29 m³/s", "pts": 5},
        ],
    },
}


# ==============================================================================
# Curated Metadata: 2020 (Q1 - Q30, total = 150 pts; Q17 has 2 blanks = 4 pts)
# ==============================================================================
META_2020 = {
    1:  {"title": "测压管管径不宜过细的毛细现象机理辨析", "chapter": 1, "kps": ["静水压强基本方程"], "method": "物理概念定义辨析", "difficulty": 1},
    2:  {"title": "重力平衡下同种均质连通液体单位势能相等", "chapter": 2, "kps": ["静水压强基本方程", "水头与能量量纲"], "method": "物理概念定义辨析", "difficulty": 1},
    3:  {"title": "能量方程求解动水压强与基准面选取无关性", "chapter": 3, "kps": ["恒定总流能量方程"], "method": "物理概念定义辨析", "difficulty": 1},
    4:  {"title": "急变流与非恒定流的分类标准辨析", "chapter": 3, "kps": ["恒定流与均匀流判别"], "method": "概念偷换词辨析", "difficulty": 1},
    5:  {"title": "温度与流量恒定时圆管雷诺数与管径反比关系", "chapter": 4, "kps": ["雷诺数与流态判别", "恒定总流连续性方程"], "method": "物理概念定义辨析", "difficulty": 2},
    6:  {"title": "边壁平均切应力公式 τ = ρgRJ 的均匀流适用条件", "chapter": 4, "kps": ["圆管均匀流切应力分布"], "method": "概念偷换词辨析", "difficulty": 2},
    7:  {"title": "雷诺流态实验与尼古拉兹阻力实验目的辨析", "chapter": 4, "kps": ["雷诺数与流态判别", "紊流阻力分区"], "method": "概念偷换词辨析", "difficulty": 2},
    8:  {"title": "并联支管单位水头损失相等与总能量损失功率辨析", "chapter": 6, "kps": ["长管串并联与三水池问题"], "method": "概念偷换词辨析", "difficulty": 2},
    9:  {"title": "等径圆管流量增大时水力粗糙与光滑壁面转化方向", "chapter": 4, "kps": ["紊流阻力分区"], "method": "物理概念定义辨析", "difficulty": 2},
    10: {"title": "突然扩大有压管总水头线与测压管水头线错绘判别", "chapter": 6, "kps": ["总水头线与测压管水头线", "有压渐扩管压强变化"], "method": "总水头线与测压管水头线判据", "difficulty": 3},
    11: {"title": "细微流量长输水管层流判别与沿程水头损失计算", "chapter": 4, "kps": ["雷诺数与流态判别", "圆管层流哈根-泊肃叶定律", "达西-韦斯巴赫公式"], "method": "核心基本概念记忆", "difficulty": 2, "subType": "mini-calc"},
    12: {"title": "明渠设计糙率偏小对设计水面高程的影响", "chapter": 7, "kps": ["明渠均匀流曼宁公式"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 2, "subType": "blank"},
    13: {"title": "负压密闭容器内敞口玻璃管充满空气的插入深度计算", "chapter": 2, "kps": ["静水压强基本方程", "真空高度(真空度)"], "method": "等压面静水压强递推法", "difficulty": 2, "subType": "mini-calc"},
    14: {"title": "变密度线性分层水体对铅直矩形钢板的静水总压力积分", "chapter": 2, "kps": ["平面静水总压力", "静水压强基本方程"], "method": "平面总压力形心法/分块合成法", "difficulty": 3, "subType": "mini-calc"},
    15: {"title": "缓坡接临界坡交汇处上游水面曲线类型判别", "chapter": 8, "kps": ["缓坡水面曲线(M1/M2/M3)", "明渠水面曲线定性分析"], "method": "渐变流微分方程符号判别", "difficulty": 2, "subType": "blank"},
    16: {"title": "河工重力相似模型原型河流流速换算", "chapter": 13, "kps": ["弗劳德相似准则"], "method": "弗劳德比尺幂次换算法", "difficulty": 1, "subType": "mini-calc"},
    17: {"title": "闸基正交渗流流网指定点压强水头与单宽渗流量计算", "chapter": 11, "kps": ["平面渗流流网", "达西定律与单宽渗流量"], "method": "正交流网段数减一计数法", "difficulty": 3, "subType": "mini-calc"},
    18: {"title": "对角线分割潜没正六边形平板分块压力比反求顶边淹深", "chapter": 2, "kps": ["平面静水总压力"], "method": "平面总压力形心法/分块合成法", "difficulty": 4, "subType": "mini-calc"},
    19: {"title": "等面积正方形满管与矩形明渠均匀流流量比计算", "chapter": 7, "kps": ["达西-韦斯巴赫公式", "明渠均匀流曼宁公式"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 2, "subType": "mini-calc"},
    20: {"title": "由缓流过底坎水面跌落特征反判明渠水流方向", "chapter": 8, "kps": ["断面单位能量(比能)", "弗劳德数判急缓流"], "method": "比能沿程导数判别法", "difficulty": 2, "subType": "blank"},
    21: {"title": "由水击相长判别阀门关闭水击类型", "chapter": 6, "kps": ["有压管道水击(水锤)", "直接与间接水击判别"], "method": "水击相长判别与儒氏公式", "difficulty": 1, "subType": "mini-calc"},
    22: {"title": "流速势函数存在的无旋流动充要条件", "chapter": 5, "kps": ["无旋流判据", "流函数与速度势函数求解"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    23: {"title": "无侧收缩矩形薄壁堰消除水舌下真空的通气措施", "chapter": 9, "kps": ["堰流分类与基本流量公式"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 1, "subType": "short-answer"},
    24: {"title": "由矩形明渠断面比能与水深之比计算弗劳德数", "chapter": 8, "kps": ["断面单位能量(比能)", "弗劳德数判急缓流"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 1, "subType": "mini-calc"},
    25: {
        "title": "矩形明渠二次多项式流速分布指定水深处黏性切应力计算",
        "chapter": 1,
        "kps": ["牛顿内摩擦定律"],
        "method": "分层液体切应力连续与速度叠加法",
        "difficulty": 1,
        "rubric": [
            {"label": "对流速分布求导得 du/dy = 15y + 3，代入 y = 0.15 m 求得流速梯度 5.25 s⁻¹", "pts": 5},
            {"label": "代入牛顿内摩擦定律 τ = μ(du/dy) 求得切应力 τ ≈ 4.38×10⁻³ N/m²（或 Pa）", "pts": 5},
        ],
    },
    26: {
        "title": "9 块正交拼接折板挡水墙静水总压力计算",
        "chapter": 2,
        "kps": ["平面静水总压力", "圆柱曲面静水总压力", "压力体图与虚压力体"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 4,
        "rubric": [
            {"label": "分析 9 块正交折板几何关系，消去正交折返高差求得总挡水水深 H = 5L·sin60° ≈ 6.495 m", "pts": 4},
            {"label": "由铅垂投影面求得水平静水总压力 Px = (1/2)ρgH²b ≈ 206.93 kN（水平向右）", "pts": 4},
            {"label": "由 60° 斜面虚压力体叠加 2 个凸入水中方形槽排开水体体积求得铅垂分力 Pz ≈ 163.62 kN（竖直向上）", "pts": 5},
            {"label": "合成静水总压力 P ≈ 263.80 kN 并指明仰角 α ≈ 38.33°（指向右上方）", "pts": 2},
        ],
    },
    27: {
        "title": "跨堤虹吸管出流射流冲击碗状挡板的水平作用力计算",
        "chapter": 3,
        "kps": ["虹吸管水力计算", "恒定总流能量方程", "恒定总流动量方程"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 3,
        "rubric": [
            {"label": "列水池水面至管口自由射流断面能量方程，求得出口射流流速 v ≈ 1.674 m/s 及流量 Q ≈ 0.01315 m³/s", "pts": 9},
            {"label": "取射流撞击碗状挡板控制体，列水平向动量方程（计入射流偏转 135° 反向分量）求得挡板反力 Rx ≈ 37.58 N", "pts": 8},
            {"label": "由牛顿第三定律指明碗状挡板所受水流水平作用力 F ≈ 37.58 N，方向水平向右", "pts": 3},
        ],
    },
    28: {
        "title": "三次齐次平面流速场的流函数与流速势函数存在性论证及求解",
        "chapter": 5,
        "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 2,
        "rubric": [
            {"label": "检验平面不可压缩连续性方程 ∂ux/∂x + ∂uy/∂y = 0 恒成立，偏积分求得流函数 ψ = xy³ - x³y + C1", "pts": 10},
            {"label": "检验无旋条件 ωz = (∂uy/∂x - ∂ux/∂y)/2 = 0 恒成立，偏积分求得流速势函数 φ = -(x⁴ + y⁴)/4 + (3/2)x²y² + C2", "pts": 10},
        ],
    },
    29: {
        "title": "宽浅矩形明渠急缓流判别及向更缓底坡过渡时断面比能变化分析",
        "chapter": 8,
        "kps": ["临界水深与临界底坡", "弗劳德数判急缓流", "缓坡水面曲线(M1/M2/M3)", "断面单位能量(比能)"],
        "method": "比能沿程导数判别法",
        "difficulty": 3,
        "rubric": [
            {"label": "求得临界水深 hc ≈ 1.177 m（或由 v = q/h 求得 Fr ≈ 0.695 < 1），判定 h = 1.5 m 处为缓流", "pts": 8},
            {"label": "由谢才公式求得原缓坡正常水深 h01 ≈ 1.805 m，阐明向更缓底坡（h02 > h01）过渡形成 M1 型壅水曲线（dh/ds > 0）", "pts": 6},
            {"label": "结合缓流区 dEs/dh > 0（或 dEs/ds = i - Jf > 0）论证过渡段断面单位能量 Es 沿程增大", "pts": 6},
        ],
    },
    30: {
        "title": "双层不混溶液体对半圆柱形挡水曲面的静水总压力计算",
        "chapter": 2,
        "kps": ["静水压强基本方程", "圆柱曲面静水总压力", "压力体图与虚压力体"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 3,
        "rubric": [
            {"label": "计算分界面 O 与底端 B 静水压强，分上下两段求得总水平分力 Px = Px1 + Px2 ≈ 35.03 kN（水平向右）", "pts": 5},
            {"label": "计算上段 AO 实压力体（向下 3.608 kN）与下段 OB 等效液面虚压力体（向上 32.224 kN），求得净铅垂分力 Pz ≈ 28.62 kN（向上）", "pts": 7},
            {"label": "合成总压力 P ≈ 45.23 kN、仰角 θ ≈ 39.24°（指向右上方，作用线过圆心）", "pts": 3},
        ],
    },
}


# ==============================================================================
# Curated Metadata: 2019 (Q1 - Q30, total = 150 pts; Q21 has 2 blanks = 4 pts)
# ==============================================================================
META_2019 = {
    1:  {"title": "牛顿流体的易流动性与受剪连续变形特性", "chapter": 1, "kps": ["牛顿内摩擦定律", "连续介质假设"], "method": "物理概念定义辨析", "difficulty": 1},
    2:  {"title": "缓流通过矩形明渠底坎障碍物时的水面跌落规律", "chapter": 8, "kps": ["断面单位能量(比能)", "弗劳德数判急缓流"], "method": "比能沿程导数判别法", "difficulty": 2},
    3:  {"title": "上下游水位同升对潜没与露顶平板闸门静水压力的影响", "chapter": 2, "kps": ["平面静水总压力"], "method": "平面总压力形心法/分块合成法", "difficulty": 3},
    4:  {"title": "曲面静水压力铅垂分力与压力体液重关系", "chapter": 2, "kps": ["圆柱曲面静水总压力", "压力体图与虚压力体"], "method": "物理概念定义辨析", "difficulty": 1},
    5:  {"title": "明渠设计糙率偏大对实际水深与设计水深关系的影响", "chapter": 7, "kps": ["明渠均匀流曼宁公式"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 2},
    6:  {"title": "双层分层静止液体侧壁测压管液面高程比较", "chapter": 2, "kps": ["静水压强基本方程", "水头与能量量纲"], "method": "等压面静水压强递推法", "difficulty": 2},
    7:  {"title": "实际液体均匀流过水断面动量校正系数辨析", "chapter": 3, "kps": ["恒定总流动量方程", "断面流速分布"], "method": "概念偷换词辨析", "difficulty": 1},
    8:  {"title": "恒定总流能量方程中水头损失的物理量纲意义", "chapter": 3, "kps": ["恒定总流能量方程", "水头与能量量纲"], "method": "概念偷换词辨析", "difficulty": 1},
    9:  {"title": "质点直线轨迹流动与有旋运动的兼容性辨析", "chapter": 5, "kps": ["流线与迹线", "无旋流判据"], "method": "物理概念定义辨析", "difficulty": 2},
    10: {"title": "等角速度旋转容器相对平衡等压面与单位质量力正交性", "chapter": 2, "kps": ["静水压强基本方程"], "method": "物理概念定义辨析", "difficulty": 2},
    11: {"title": "毕托管倾斜式压差计倾角增大对斜管读数差的影响", "chapter": 3, "kps": ["恒定总流能量方程"], "method": "等压面静水压强递推法", "difficulty": 2, "subType": "blank"},
    12: {"title": "负压密闭容器内敞口玻璃管充满空气的插入水深计算", "chapter": 2, "kps": ["静水压强基本方程", "真空高度(真空度)"], "method": "等压面静水压强递推法", "difficulty": 2, "subType": "mini-calc"},
    13: {"title": "重力相似模型消除比尺效应的紊流粗糙自模区条件", "chapter": 13, "kps": ["弗劳德相似准则", "河工模型阻力相似", "紊流阻力分区"], "method": "核心基本概念记忆", "difficulty": 1, "subType": "blank"},
    14: {"title": "受实验室最大供水流量限制的溢流坝模型长度比尺计算", "chapter": 13, "kps": ["弗劳德相似准则", "流量比尺换算"], "method": "弗劳德比尺幂次换算法", "difficulty": 2, "subType": "mini-calc"},
    15: {"title": "圆管均匀紊流壁面处黏滞切应力与紊动附加切应力比较", "chapter": 4, "kps": ["圆管均匀流切应力分布", "断面流速分布"], "method": "物理概念定义辨析", "difficulty": 2, "subType": "blank"},
    16: {"title": "有压管道避免直接水击的最短阀门关闭时间计算", "chapter": 6, "kps": ["有压管道水击(水锤)", "直接与间接水击判别"], "method": "水击相长判别与儒氏公式", "difficulty": 1, "subType": "mini-calc"},
    17: {"title": "感潮河段盐水密度线性分布对铅直挡潮闸的静水总压力", "chapter": 2, "kps": ["平面静水总压力", "静水压强基本方程"], "method": "平面总压力形心法/分块合成法", "difficulty": 3, "subType": "mini-calc"},
    18: {"title": "溢流坝顶多孔闸门自由出流判别与过流流量计算", "chapter": 9, "kps": ["平板闸孔出流判别", "闸孔自由出流流量公式", "堰流分类与基本流量公式"], "method": "堰流与闸孔出流判别及流量公式", "difficulty": 2, "subType": "mini-calc"},
    19: {"title": "主槽与滩地复式断面河道均匀流总流量计算", "chapter": 7, "kps": ["梯形断面水力要素", "明渠均匀流曼宁公式"], "method": "水力要素计算+曼宁公式+水力深度Fr判据", "difficulty": 3, "subType": "mini-calc"},
    20: {"title": "尼古拉兹试验曲线粗糙区沿程阻力系数与管径大小判别", "chapter": 4, "kps": ["紊流阻力分区", "达西-韦斯巴赫公式"], "method": "物理概念定义辨析", "difficulty": 2, "subType": "blank"},
    21: {"title": "输油圆管层流判别、沿程水头损失与管壁切应力计算", "chapter": 4, "kps": ["雷诺数与流态判别", "圆管层流哈根-泊肃叶定律", "圆管均匀流切应力分布"], "method": "圆管切应力线性分布性质", "difficulty": 3, "subType": "mini-calc"},
    22: {"title": "缓坡 M2 型降水曲线断面单位能量的沿程变化", "chapter": 8, "kps": ["缓坡水面曲线(M1/M2/M3)", "断面单位能量(比能)"], "method": "比能沿程导数判别法", "difficulty": 2, "subType": "blank"},
    23: {"title": "水平不透水层潜水完整集水廊道单宽渗流量计算", "chapter": 11, "kps": ["达西定律与单宽渗流量", "达西定律与适用范围"], "method": "核心基本概念记忆", "difficulty": 2, "subType": "mini-calc"},
    24: {"title": "水闸地基曲边正方形流网单宽渗流量计算", "chapter": 11, "kps": ["平面渗流流网", "达西定律与单宽渗流量"], "method": "正交流网段数减一计数法", "difficulty": 1, "subType": "mini-calc"},
    25: {
        "title": "同轴旋转内圆筒与静止外圆筒间隙液体黏滞作用力计算",
        "chapter": 1,
        "kps": ["牛顿内摩擦定律", "环形/圆盘间隙黏性阻力矩"],
        "method": "分层液体切应力连续与速度叠加法",
        "difficulty": 2,
        "rubric": [
            {"label": "由内筒角速度 ω = 10 rad/s 求得内筒线速度 vA = ωrA = 0.80 m/s 及线性速度梯度 du/dy = 400 s⁻¹", "pts": 3},
            {"label": "计算外筒 B 内半径 rB = rA + δ = 0.082 m 及内表面受剪面积 AB = 2πrBL ≈ 0.5152 m²", "pts": 3},
            {"label": "应用牛顿内摩擦定律 F = μAB(du/dy) 求得 B 筒内表面黏滞作用力 F ≈ 1.77 N（单位正确）", "pts": 4},
        ],
    },
    26: {
        "title": "溢流坝顶弧形闸门与坝下底孔圆形平板闸门静水总压力计算",
        "chapter": 2,
        "kps": ["圆柱曲面静水总压力", "压力体图与虚压力体", "平面静水总压力"],
        "method": "等效自由液面+水平投影与铅垂压力体合成法",
        "difficulty": 3,
        "rubric": [
            {"label": "（1）求得弧形闸门水平分力 Px = 176.58 kN（向右）及圆心角 α = arcsin(3/5) ≈ 36.87°", "pts": 5},
            {"label": "（1）由扇形减三角形求实压力体体积 Vz ≈ 8.175 m³、铅垂分力 Pz ≈ 80.20 kN（向下），合成总压力 P ≈ 193.94 kN、倾角 24.43°（过支铰 O）", "pts": 6},
            {"label": "（2）确定底孔圆形平板闸门形心淹深 hc = H + r + a/2 = 12 m，求得总压力 P' ≈ 369.83 kN", "pts": 5},
            {"label": "（2）由 yD = yc + Ic/(ycA) 求得压心淹深 yD ≈ 12.02 m（距底点 C 上方约 0.98 m）", "pts": 4},
        ],
    },
    27: {
        "title": "虹吸管流量计算及总水头线与测压管水头线定性绘制",
        "chapter": 6,
        "kps": ["虹吸管水力计算", "总水头线与测压管水头线", "真空高度(真空度)"],
        "method": "两段伯努利方程联立法",
        "difficulty": 3,
        "rubric": [
            {"label": "列上下游水池水面能量方程（计入沿程阻力及进口、2 个弯头、阀门、出口局部损失，总阻力系数 4.3），解得 v ≈ 3.021 m/s、Q ≈ 0.0237 m³/s", "pts": 8},
            {"label": "正确绘出总水头线（进口、弯头、阀门及淹没出口各局部台阶跌落，直管段均匀下降至下游水面）", "pts": 4},
            {"label": "正确绘出平行位于总水头线下方 v²/(2g) 的测压管水头线（出口平顺接下游水面，管顶高于测压管水头线呈负压区）", "pts": 3},
        ],
    },
    28: {
        "title": "二维流场流函数存在性论证、流线间单宽流量及速度势判别",
        "chapter": 5,
        "kps": ["平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解"],
        "method": "不可压与无旋偏导检验+偏积分求原函数法",
        "difficulty": 2,
        "rubric": [
            {"label": "验证二维连续性方程 ∂ux/∂x + ∂uy/∂y = 0 成立，偏积分求得流函数 ψ = x²y + C", "pts": 6},
            {"label": "代入 A(1,1)、B(2,2) 计算两条流线间单宽流量 q = |ψB - ψA| = 7 m²/s", "pts": 4},
            {"label": "计算旋转角速度 ωz = -y ≠ 0，判定流动为有旋运动、不存在流速势函数 φ", "pts": 5},
        ],
    },
    29: {
        "title": "矩形明渠局部底坎坎顶水深、底坎水平推力、流态判别及临界坎高计算",
        "chapter": 8,
        "kps": ["断面单位能量(比能)", "临界水深与临界底坡", "恒定总流动量方程", "弯管/底坎水流作用力"],
        "method": "能量方程求流量+控制体动量方程求反力",
        "difficulty": 4,
        "rubric": [
            {"label": "（1）求得临界水深 hc ≈ 0.542 m、上游比能 Es1 ≈ 0.924 m、坎顶比能 Es2 ≈ 0.824 m > Emin，选取缓流正根得 h2 ≈ 0.611 m", "pts": 8},
            {"label": "（2）计算上下游断面静水总压力 P1、P2，列水平动量方程求得水流对底坎水平作用力 F ≈ 1.41 kN（向下游）", "pts": 8},
            {"label": "（3）由 h2 > hc（或 Fr2 ≈ 0.835 < 1）准确判别坎顶水流为缓流", "pts": 4},
            {"label": "（4）由坎顶达最小比能 Emin = 1.5hc 求得临界坎高 a临 = Es1 - Emin ≈ 0.111 m", "pts": 5},
        ],
    },
    30: {
        "title": "陡坡接缓坡棱柱形明渠底坡判别、远驱水跃定位及水面曲线定性绘制",
        "chapter": 8,
        "kps": ["临界水深与临界底坡", "明渠水跃与跃后水深", "明渠水面曲线定性分析"],
        "method": "渐变流微分方程符号判别",
        "difficulty": 3,
        "rubric": [
            {"label": "（1）求得临界水深 hc ≈ 1.366 m，由 h01 = 0.7 m < hc < h02 = 2.0 m 判定上游为陡坡、下游为缓坡", "pts": 4},
            {"label": "（2）计算 h01 对应跃后共轭水深 h01'' ≈ 2.371 m > h02 = 2.0 m，判定发生远驱式水跃且水跃位于下游第 2 渠段", "pts": 6},
            {"label": "（3）定性绘出完整水面曲线并标明名称（上游均匀流或 S2 曲线，下游 M3 壅水曲线接水跃至 h02 均匀流）", "pts": 5},
        ],
    },
}


# ==============================================================================
# Clean Matplotlib Engineering Figures (dpi=220, zero CJK inside $...$)
# ==============================================================================

def draw_2021_q28_sol(dest_path: Path):
    """Vertical expanding pipe bend control-volume diagram for 2021 Q28."""
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    fig.patch.set_facecolor("white")

    # Control volume pipe outline: bottom narrow inlet (d1=0.04) -> inclined bend -> top wide outlet (d2=0.08)
    left_wall_x = [1.2, 1.2, 2.8, 2.8]
    left_wall_y = [0.4, 1.6, 2.5, 3.8]
    right_wall_x = [1.8, 1.8, 4.0, 4.0]
    right_wall_y = [0.4, 1.4, 2.3, 3.8]

    poly_pts = [
        (1.2, 0.7), (1.2, 1.6), (2.8, 2.5), (2.8, 3.5),
        (4.0, 3.5), (4.0, 2.3), (1.8, 1.4), (1.8, 0.7),
    ]
    ax.add_patch(Polygon(poly_pts, closed=True, facecolor="#dbeafe", edgecolor="none", alpha=0.65))
    ax.plot(left_wall_x, left_wall_y, color="#0f172a", lw=2.8)
    ax.plot(right_wall_x, right_wall_y, color="#0f172a", lw=2.8)

    # Control sections 1-1 and 2-2
    ax.plot([1.05, 1.95], [0.7, 0.7], color="#dc2626", ls="--", lw=1.8)
    ax.plot([2.65, 4.15], [3.5, 3.5], color="#dc2626", ls="--", lw=1.8)
    ax.text(0.95, 0.7, "断面 1—1", fontsize=9.5, ha="right", va="center", color="#991b1b")
    ax.text(4.25, 3.5, "断面 2—2", fontsize=9.5, ha="left", va="center", color="#991b1b")

    # Force vectors on CV
    ax.annotate("", xy=(1.5, 1.25), xytext=(1.5, 0.25),
                arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=2.5))
    ax.text(1.98, 0.65, "$P_1 = 25.13\\,\\mathrm{N}\\;(\\uparrow)$\n$v_1 = 1.592\\,\\mathrm{m/s}$",
            fontsize=9.5, color="#1e40af", va="center")

    ax.annotate("", xy=(3.4, 3.15), xytext=(3.4, 4.15),
                arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=2.5))
    ax.text(4.25, 3.95, "$P_2 = 81.84\\,\\mathrm{N}\\;(\\downarrow)$\n$v_2 = 0.398\\,\\mathrm{m/s}$",
            fontsize=9.5, color="#1e40af", va="top")

    # Weight G
    ax.annotate("", xy=(2.55, 1.55), xytext=(2.55, 2.45),
                arrowprops=dict(arrowstyle="->", color="#475569", lw=2.3))
    ax.text(2.70, 1.55, "水重 $G = 24.53\\,\\mathrm{N}\\;(\\downarrow)$", fontsize=9.5, color="#334155")

    # Wall reaction Rz and action Fz
    ax.annotate("", xy=(1.85, 3.05), xytext=(1.85, 2.05),
                arrowprops=dict(arrowstyle="->", color="#15803d", lw=2.6))
    ax.text(0.08, 3.25,
            "管壁对水流反力 $R_z = 78.85\\,\\mathrm{N}\\;(\\uparrow)$\n水流对弯管作用力 $F_z = 78.85\\,\\mathrm{N}\\;(\\downarrow)$",
            fontsize=9.5, color="#15803d", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#f0fdf4", edgecolor="#86efac"))

    ax.set_title("第 28 题：竖直渐扩弯管控制体竖直向受力与动量分析图", fontsize=11, pad=8)
    ax.set_xlim(0.0, 6.2)
    ax.set_ylim(0.1, 4.35)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2021_q29_sol(dest_path: Path):
    """Sharp 90-deg elbow pipe A-B energy loss diagram matching stem geometry for 2021 Q29."""
    fig, ax = plt.subplots(figsize=(7.8, 4.2))
    fig.patch.set_facecolor("white")

    # Upper tank
    ax.plot([0.4, 0.4, 1.3], [4.1, 3.2, 3.2], color="#0f172a", lw=2.2)
    ax.plot([1.7, 2.8, 2.8], [3.2, 3.2, 4.1], color="#0f172a", lw=2.2)
    ax.plot([0.4, 2.8], [3.85, 3.85], color="#2563eb", lw=2.0)

    # Vertical pipe down to 90 deg sharp elbow, then horizontal pipe right
    ax.plot([1.3, 1.3, 5.6], [3.2, 0.6, 0.6], color="#0f172a", lw=2.4)
    ax.plot([1.7, 1.7, 4.4], [3.2, 1.0, 1.0], color="#0f172a", lw=2.4)
    ax.plot([4.6, 5.6], [1.0, 1.0], color="#0f172a", lw=2.4)

    # Piezometer at A (vertical pipe, zA = 1.8) -> horizontal tap to standpipe at x=3.4
    ax.plot([1.7, 3.3, 3.3], [1.9, 1.9, 3.45], color="#334155", lw=1.7)
    ax.plot([1.7, 3.5, 3.5], [1.7, 1.7, 3.45], color="#334155", lw=1.7)
    ax.plot([3.3, 3.5], [3.05, 3.05], color="#2563eb", lw=2.2)  # meniscus A

    # Piezometer at B (horizontal pipe, zB = 0.8) -> standpipe at x=4.5
    ax.plot([4.4, 4.4], [1.0, 3.45], color="#334155", lw=1.7)
    ax.plot([4.6, 4.6], [1.0, 3.45], color="#334155", lw=1.7)
    ax.plot([4.4, 4.6], [2.55, 2.55], color="#2563eb", lw=2.2)  # meniscus B

    ax.text(1.02, 1.8, "$A$", fontsize=11, fontweight="bold", color="#0f172a")
    ax.text(4.5, 0.22, "$B$", fontsize=11, fontweight="bold", ha="center", color="#0f172a")

    # Elevation diff H = 0.1 m annotation
    ax.plot([0.85, 1.3], [1.8, 1.8], color="#64748b", ls=":", lw=1.2)
    ax.plot([0.85, 1.3], [0.8, 0.8], color="#64748b", ls=":", lw=1.2)
    ax.annotate("", xy=(0.95, 1.8), xytext=(0.95, 0.8),
                arrowprops=dict(arrowstyle="<->", color="#475569", lw=1.4))
    ax.text(0.88, 1.3, "$H = 0.1\\,\\mathrm{m}$", fontsize=9, ha="right", va="center", color="#334155")

    # Head loss annotation between piezometers
    ax.plot([3.5, 4.85], [3.05, 3.05], color="#dc2626", ls="--", lw=1.3)
    ax.plot([4.6, 4.85], [2.55, 2.55], color="#dc2626", ls="--", lw=1.3)
    ax.annotate("", xy=(4.78, 3.05), xytext=(4.78, 2.55),
                arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.6))
    ax.text(4.92, 2.80,
            "$h_w = (z_A - z_B) + \\frac{p_A - p_B}{\\rho g} = 0.126\\,\\mathrm{m}$\n"
            "$h_f = 0.0892\\,\\mathrm{m},\\; h_j = 0.0368\\,\\mathrm{m}$\n"
            "$\\Rightarrow \\zeta = 1.24$",
            fontsize=9.5, color="#991b1b", va="center",
            bbox=dict(boxstyle="round,pad=0.38", facecolor="#fef2f2", edgecolor="#fca5a5"))

    ax.set_title("第 29 题：A—B 直角弯管能量方程与水头损失分解示意图", fontsize=11, pad=8)
    ax.set_xlim(0.05, 7.9)
    ax.set_ylim(0.05, 4.25)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2020_q10_sol(dest_path: Path):
    """Correct vs erroneous THL/HGL diagram for sudden-expansion pipe in 2020 Q10."""
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    fig.patch.set_facecolor("white")

    # Upstream & downstream tanks + sudden expansion pipe
    ax.plot([0.3, 1.5, 1.5], [3.4, 3.4, 0.3], color="#1e293b", lw=2.0)
    ax.plot([0.3, 1.5], [0.3, 0.3], color="#1e293b", lw=2.0)
    ax.plot([5.9, 5.9, 7.2], [3.4, 0.3, 0.3], color="#1e293b", lw=2.0)

    # Pipe: narrow left (1.5..3.6, y=0.75..1.05), wide right (3.6..5.9, y=0.60..1.20)
    ax.add_patch(Rectangle((1.5, 0.75), 2.1, 0.30, facecolor="#e0f2fe", edgecolor="none"))
    ax.add_patch(Rectangle((3.6, 0.60), 2.3, 0.60, facecolor="#e0f2fe", edgecolor="none"))
    ax.plot([1.5, 3.6, 3.6, 5.9], [1.05, 1.05, 1.20, 1.20], color="#0f172a", lw=2.2)
    ax.plot([1.5, 3.6, 3.6, 5.9], [0.75, 0.75, 0.60, 0.60], color="#0f172a", lw=2.2)

    # Water surfaces
    ax.plot([0.35, 1.5], [3.15, 3.15], color="#2563eb", lw=2.0)
    ax.plot([5.9, 7.15], [2.05, 2.05], color="#2563eb", lw=2.0)

    # Correct THL (green solid): inlet drop -> steep J1 -> sudden expansion drop hj -> flat J2 -> exit drop hv2 to 2.05
    x_thl = [1.5, 1.5, 3.6, 3.6, 5.9, 5.9]
    y_thl = [3.15, 2.95, 2.45, 2.23, 2.17, 2.05]
    ax.plot(x_thl, y_thl, color="#15803d", lw=2.5, label="正确总水头线 THL（粗管坡度变缓）")

    # Correct HGL (red dashed): hv1 = 0.40 in thin pipe, hv2 = 0.12 in thick pipe -> RISES at x=3.6!
    x_hgl = [1.5, 3.6, 3.6, 5.9]
    y_hgl = [2.55, 2.05, 2.11, 2.05]
    ax.plot(x_hgl, y_hgl, color="#dc2626", lw=2.4, ls="--", label="正确测压管水头线 HGL（突扩处回升！）")

    # Erroneous HGL as drawn in stem (gray dotted, stepping down)
    ax.plot([1.5, 3.6, 3.6, 5.9], [2.65, 2.35, 2.15, 2.05], color="#94a3b8", lw=1.6, ls=":",
            label="原题错绘 HGL（误画为突降且间距不变）")

    ax.annotate("突扩减速增压\nHGL 应上升！", xy=(3.6, 2.11), xytext=(3.95, 2.68),
                fontsize=9.2, color="#b91c1c", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#b91c1c", lw=1.6))
    ax.text(2.45, 0.88, "$d_1$（细管 $v_1$ 大）", fontsize=8.8, ha="center", va="center", color="#0f172a")
    ax.text(4.75, 0.88, "$d_2$（粗管 $v_2$ 小）", fontsize=8.8, ha="center", va="center", color="#0f172a")

    ax.set_title("第 10 题：突然扩大有压管正确水头线与原图三处错绘对比（题干判“错误”为 √）", fontsize=10.5, pad=6)
    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.92)
    ax.set_xlim(0.2, 7.3)
    ax.set_ylim(0.15, 3.65)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2020_q17_sol(dest_path: Path):
    """Clean 21-equipotential flow-net head drop schematic for 2020 Q17."""
    fig, ax = plt.subplots(figsize=(8.2, 3.6))
    fig.patch.set_facecolor("white")

    # 21 equipotential lines (x = 0..20), 9 streamlines (y = 0..8)
    for ix in range(21):
        lw = 2.6 if ix == 15 else (1.8 if ix in (0, 20) else 0.9)
        col = "#dc2626" if ix == 15 else ("#0f172a" if ix in (0, 20) else "#64748b")
        ax.plot([ix, ix], [0, 4.0], color=col, lw=lw, zorder=3 if ix == 15 else 1)
    for iy in range(9):
        ax.plot([0, 20], [iy * 0.5, iy * 0.5], color="#1e40af", lw=1.0, alpha=0.75)

    ax.scatter([15], [1.5], s=90, color="#dc2626", zorder=5)
    ax.text(14.6, 2.25, "点 $A$：自上游数第 16 条等势线（已降 15 格）",
            fontsize=9.5, ha="right", color="#991b1b", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#fef2f2", edgecolor="#fca5a5"))

    ax.annotate("", xy=(17.5, 4.65), xytext=(2.5, 4.65),
                arrowprops=dict(arrowstyle="->", color="#2563eb", lw=2.3))
    ax.text(10.0, 4.88, "渗流方向：上游 $H_1 = 10\\,\\mathrm{m} \\rightarrow$ 下游 $H_2 = 0\\,\\mathrm{m}$（共 20 格，每格水头降 $0.5\\,\\mathrm{m}$）",
            fontsize=9.5, ha="center", color="#1d4ed8")

    for ix, lbl in [(0, "线 1\n$H=10.0\\,\\mathrm{m}$"), (5, "线 6\n$H=7.5\\,\\mathrm{m}$"),
                    (10, "线 11\n$H=5.0\\,\\mathrm{m}$"), (15, "线 16\n$H_A=2.5\\,\\mathrm{m}$"),
                    (20, "线 21\n$H=0.0\\,\\mathrm{m}$")]:
        c_txt = "#dc2626" if ix == 15 else "#334155"
        ax.text(ix, -0.55, lbl, fontsize=8.8, ha="center", va="top", color=c_txt)

    ax.text(10.0, -1.65,
            "压强水头：$h_{pA} = H_A - Z_A = 2.5 - (-10) = 12.5\\,\\mathrm{m}$；单宽流量：$q = k\\Delta h\\frac{M}{N} = 2\\times 10^{-4}\\,\\mathrm{m^2/s}$",
            fontsize=9.5, ha="center", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#f8fafc", edgecolor="#cbd5e1"))

    ax.set_title("第 17 题：闸基正交渗流流网（21 条等势线、9 条流线）水头递减图", fontsize=11, pad=6)
    ax.set_xlim(-1.2, 21.2)
    ax.set_ylim(-2.1, 5.4)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2020_q26_sol(dest_path: Path):
    """Exact true-orientation (`\\` top-left to bottom-right) 9-plate folded wall diagram for 2020 Q26."""
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    fig.patch.set_facecolor("white")

    L = 1.5
    th = math.radians(60.0)
    # y positive upward, water surface at y = H, floor at y = 0!
    H = 5.0 * L * math.sin(th)  # 6.4952 m
    u_vec = np.array([math.cos(th), -math.sin(th)])   # down-right along 60 deg baseline
    w_vec = np.array([-math.sin(th), -math.cos(th)])  # down-left protruding into water!
    dirs = [u_vec, w_vec, u_vec, -w_vec, u_vec, w_vec, u_vec, -w_vec, u_vec]
    pts = [np.array([0.0, H])]
    for dv in dirs:
        pts.append(pts[-1] + L * dv)
    pts_arr = np.array(pts)

    # Virtual pressure body triangle above baseline (0,H) -> (3.75, 0) -> (3.75, H)
    x_end = pts_arr[-1, 0]  # 3.75
    ax.add_patch(Polygon([(0.0, H), (x_end, 0.0), (x_end, H)],
                         closed=True, facecolor="#ffedd5", edgecolor="#ea580c", ls="--", lw=1.3, alpha=0.75,
                         label="斜面虚压力体 $V_\\Delta = 12.18\\,\\mathrm{m^3}\\;(\\uparrow)$"))

    # Two protruding 1.5x1.5 squares into water: P1-P2-P3-P4 and P5-P6-P7-P8
    for i0 in (1, 5):
        sq = pts_arr[i0:i0+4]
        ax.add_patch(Polygon(sq, closed=True, facecolor="#fef08a", edgecolor="#ca8a04", lw=1.3, alpha=0.85,
                             label="凸入水中方槽排开水体 $2L^2b = 4.50\\,\\mathrm{m^3}\\;(\\uparrow)$" if i0 == 1 else None))

    # Horizontal pressure triangle on the left for Px
    x_left = -3.2
    ax.add_patch(Polygon([(x_left, H), (x_left, 0.0), (x_left + 1.8, 0.0)],
                         closed=True, facecolor="#dbeafe", edgecolor="#2563eb", lw=1.4, alpha=0.8))
    ax.annotate("", xy=(x_left + 1.95, H / 3.0), xytext=(x_left + 0.35, H / 3.0),
                arrowprops=dict(arrowstyle="->", color="#1d4ed8", lw=2.4))
    ax.text(x_left + 0.9, H / 3.0 + 0.35, "$P_x = 206.93\\,\\mathrm{kN}\\;(\\rightarrow)$",
            fontsize=9.5, ha="center", color="#1e40af", fontweight="bold")

    # Water surface & floor & 9-plate polyline
    ax.plot([-3.5, x_end + 0.6], [H, H], color="#2563eb", lw=2.0)
    ax.plot([-3.5, x_end + 0.8], [0.0, 0.0], color="#475569", lw=2.0)
    ax.plot([0.0, x_end], [H, 0.0], color="#94a3b8", ls=":", lw=1.4)
    ax.plot(pts_arr[:, 0], pts_arr[:, 1], color="#0f172a", lw=3.0, zorder=5)
    ax.text(x_end - 1.18, 0.24, "$\\theta = 60^{\\circ}$", fontsize=9.5, color="#0f172a")

    # Upward Pz and Resultant P
    ax.annotate("", xy=(1.8, 5.5), xytext=(1.8, 3.6),
                arrowprops=dict(arrowstyle="->", color="#c2410c", lw=2.5), zorder=6)
    ax.text(1.95, 4.75, "$P_z = 163.62\\,\\mathrm{kN}\\;(\\uparrow)$", fontsize=9.5, color="#9a3412", fontweight="bold")

    ax.annotate("", xy=(4.85, 3.85), xytext=(2.85, 2.27),
                arrowprops=dict(arrowstyle="->", color="#15803d", lw=2.8), zorder=6)
    ax.text(4.05, 1.85,
            "总压力 $P = 263.80\\,\\mathrm{kN}$\n仰角 $\\alpha = 38.33^{\\circ}$（右上方）",
            fontsize=9.8, color="#15803d", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#f0fdf4", edgecolor="#86efac"))

    ax.set_title("第 26 题：9 块正交拼接折板水平投影与铅垂虚压力体合成图", fontsize=11, pad=8)
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.92)
    ax.set_xlim(-3.7, 6.8)
    ax.set_ylim(-0.4, H + 0.9)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2019_q03_orig(dest_path: Path):
    """Crisp redraw of 2019 Q03 stem figure (submerged gate vs emergent gate with 1 m rise)."""
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.8))
    fig.patch.set_facecolor("white")

    # Panel (1): Submerged gate AB
    ax = axes[0]
    ax.plot([-2.2, 2.0], [0.0, 0.0], color="#0f172a", lw=1.8)
    ax.plot([0.0, 1.35], [0.0, 3.6], color="#0f172a", lw=2.6)
    ax.text(0.82, 1.85, "$A$", fontsize=11, fontweight="bold")
    ax.text(0.0, -0.32, "$B$", fontsize=11, fontweight="bold", ha="center")
    # Upstream water levels (y=2.6 -> 3.2)
    ax.plot([-2.1, 0.975], [2.6, 2.6], color="#0f172a", lw=1.4)
    ax.plot([-2.0, 1.20], [3.2, 3.2], color="#0f172a", ls="--", lw=1.4)
    ax.annotate("", xy=(-0.6, 3.2), xytext=(-0.6, 2.6), arrowprops=dict(arrowstyle="<->", lw=1.2))
    ax.text(-0.72, 2.9, "$1\\,\\mathrm{m}$", fontsize=9.5, ha="right", va="center")
    # Downstream water levels (y=1.7 -> 2.3)
    ax.plot([0.638, 2.1], [1.7, 1.7], color="#0f172a", lw=1.4)
    ax.plot([0.863, 2.1], [2.3, 2.3], color="#0f172a", ls="--", lw=1.4)
    ax.annotate("", xy=(1.55, 2.3), xytext=(1.55, 1.7), arrowprops=dict(arrowstyle="<->", lw=1.2))
    ax.text(1.45, 2.0, "$1\\,\\mathrm{m}$", fontsize=9.5, ha="right", va="center")
    ax.text(0.0, -0.78, "图（1）", fontsize=11, ha="center")
    ax.set_xlim(-2.4, 2.3)
    ax.set_ylim(-0.95, 3.85)
    ax.set_aspect("equal")
    ax.axis("off")

    # Panel (2): Emergent gate AB (A above both water surfaces)
    ax = axes[1]
    ax.plot([-2.2, 2.0], [0.0, 0.0], color="#0f172a", lw=1.8)
    ax.plot([0.0, 1.35], [0.0, 3.6], color="#0f172a", lw=2.6)
    ax.text(1.25, 2.95, "$A$", fontsize=11, fontweight="bold")
    ax.text(0.0, -0.32, "$B$", fontsize=11, fontweight="bold", ha="center")
    # Upstream water levels (y=1.5 -> 2.1)
    ax.plot([-2.1, 0.563], [1.5, 1.5], color="#0f172a", lw=1.4)
    ax.plot([-2.0, 0.788], [2.1, 2.1], color="#0f172a", ls="--", lw=1.4)
    ax.annotate("", xy=(-0.7, 2.1), xytext=(-0.7, 1.5), arrowprops=dict(arrowstyle="<->", lw=1.2))
    ax.text(-0.82, 1.8, "$1\\,\\mathrm{m}$", fontsize=9.5, ha="right", va="center")
    # Downstream water levels (y=0.75 -> 1.35)
    ax.plot([0.281, 2.1], [0.75, 0.75], color="#0f172a", lw=1.4)
    ax.plot([0.506, 2.1], [1.35, 1.35], color="#0f172a", ls="--", lw=1.4)
    ax.annotate("", xy=(1.45, 1.35), xytext=(1.45, 0.75), arrowprops=dict(arrowstyle="<->", lw=1.2))
    ax.text(1.35, 1.05, "$1\\,\\mathrm{m}$", fontsize=9.5, ha="right", va="center")
    ax.text(0.0, -0.78, "图（2）", fontsize=11, ha="center")
    ax.set_xlim(-2.4, 2.3)
    ax.set_ylim(-0.95, 3.85)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2019_q27_sol(dest_path: Path):
    """Physically exact siphon THL & HGL diagram (with exit drop v^2/2g on THL) for 2019 Q27."""
    fig, ax = plt.subplots(figsize=(8.4, 4.5))
    fig.patch.set_facecolor("white")

    # Upstream reservoir (water surface at y = 2.0) & downstream reservoir (water surface at y = 0.0)
    ax.plot([0.2, 2.2], [2.0, 2.0], color="#2563eb", lw=2.2)
    ax.plot([6.8, 9.2], [0.0, 0.0], color="#2563eb", lw=2.2)
    ax.plot([0.2, 2.2, 2.2], [0.6, 0.6, 1.7], color="#475569", lw=1.8)
    ax.plot([6.8, 6.8, 9.2], [-0.2, -1.0, -1.0], color="#475569", lw=1.8)

    # Siphon centerline: inlet (1.8, 1.55) -> Bend 1 (3.2, 3.15) -> Bend 2 (4.8, 3.15) -> Valve (6.0, 1.65) -> Exit (7.2, -0.25)
    sx = [1.8, 3.2, 4.8, 6.0, 7.2]
    sy = [1.55, 3.15, 3.15, 1.65, -0.25]
    ax.plot(sx, sy, color="#0f172a", lw=5.5, solid_capstyle="round", zorder=3)
    ax.plot(sx, sy, color="#e2e8f0", lw=3.0, solid_capstyle="round", zorder=4)

    # Exact scaled heads (z = 2.0 m, hv = 2.0 / 4.3 = 0.4651 m)
    hv = 2.0 / 4.3
    # Cumulative arc fraction along x-projection: total hf = 2.0 * hv = 0.9302 m
    # Drops: inlet = 0.8*hv=0.3721, bend1 = 0.15*hv=0.0698, bend2 = 0.15*hv=0.0698, valve = 0.20*hv=0.0930, exit = 1.0*hv=0.4651
    hf_tot = 2.0 * hv
    x_nodes = [1.8, 3.2, 4.8, 6.0, 7.2]
    seg_fracs = [0.26, 0.29, 0.22, 0.23]  # sum = 1.0

    y0 = 2.0
    y_in_after = y0 - 0.8 * hv
    y_b1_pre = y_in_after - seg_fracs[0] * hf_tot
    y_b1_post = y_b1_pre - 0.15 * hv
    y_b2_pre = y_b1_post - seg_fracs[1] * hf_tot
    y_b2_post = y_b2_pre - 0.15 * hv
    y_v_pre = y_b2_post - seg_fracs[2] * hf_tot
    y_v_post = y_v_pre - 0.20 * hv
    y_out_pre = y_v_post - seg_fracs[3] * hf_tot  # equals hv = 0.4651!

    thl_x = [1.8, 1.8, 3.2, 3.2, 4.8, 4.8, 6.0, 6.0, 7.2, 7.2]
    thl_y = [2.0, y_in_after, y_b1_pre, y_b1_post, y_b2_pre, y_b2_post, y_v_pre, y_v_post, y_out_pre, 0.0]

    hgl_x = [1.8, 1.8, 3.2, 3.2, 4.8, 4.8, 6.0, 6.0, 7.2]
    hgl_y = [2.0, y_in_after - hv, y_b1_pre - hv, y_b1_post - hv,
             y_b2_pre - hv, y_b2_post - hv, y_v_pre - hv, y_v_post - hv, 0.0]

    # Shade negative-pressure (vacuum) region where pipe > HGL
    ax.add_patch(Polygon([(2.05, 1.83), (3.2, 3.15), (4.8, 3.15), (6.48, 1.05),
                          (6.0, y_v_post - hv), (4.8, y_b2_post - hv), (3.2, y_b1_post - hv)],
                         closed=True, facecolor="#fee2e2", edgecolor="none", alpha=0.65, zorder=2))
    ax.text(4.1, 2.15, "负压（真空）区\n管轴高程高于 HGL", fontsize=9.2, ha="center", color="#b91c1c", fontweight="bold")

    ax.plot(thl_x, thl_y, color="#15803d", lw=2.4, zorder=6,
            label="总水头线 THL（淹没出口突降 $\\zeta_4\\frac{v^2}{2g} = \\frac{v^2}{2g}$）")
    ax.plot(hgl_x, hgl_y, color="#dc2626", lw=2.2, ls="--", zorder=6,
            label="测压管水头线 HGL（平行位于 THL 下方 $\\frac{v^2}{2g}$，出口平顺接下游水面）")

    ax.scatter([6.0], [1.65], s=70, facecolor="#fef08a", edgecolor="#0f172a", lw=1.5, zorder=5)
    ax.text(3.2, 3.35, "转弯 1", fontsize=8.8, ha="center")
    ax.text(4.8, 3.35, "转弯 2", fontsize=8.8, ha="center")
    ax.text(6.18, 1.75, "阀门", fontsize=8.8, ha="left")
    ax.text(7.35, 0.25, "$\\frac{v^2}{2g}$", fontsize=9.5, color="#15803d", fontweight="bold")

    ax.set_title("第 27 题：虹吸管总水头线（THL）、测压管水头线（HGL）与真空区示意图", fontsize=11, pad=8)
    ax.legend(loc="lower left", fontsize=8.5, framealpha=0.94)
    ax.set_xlim(0.0, 9.4)
    ax.set_ylim(-1.25, 3.75)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


def draw_2019_q29_sol(dest_path: Path):
    """Specific energy Es-h curve for subcritical flow over upward step in 2019 Q29."""
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    fig.patch.set_facecolor("white")

    g_val = 9.81
    q = 1.25
    hc = (q ** 2 / g_val) ** (1.0 / 3.0)
    Emin = 1.5 * hc

    h_arr = np.linspace(0.32, 0.96, 400)
    Es_arr = h_arr + (q ** 2) / (2.0 * g_val * h_arr ** 2)

    ax.plot(Es_arr, h_arr, color="#1e3a8a", lw=2.6, label="$E_s = h + \\frac{q^2}{2gh^2}\\;(q = 1.25\\,\\mathrm{m^2/s})$")
    ax.axhline(hc, color="#64748b", ls="--", lw=1.4)
    ax.text(1.01, hc + 0.015, "$h_c = 0.5421\\,\\mathrm{m}$", fontsize=9.2, color="#334155")

    # Key states
    Es1, h1 = 0.9244, 0.80
    Es2, h2_sub, h2_sup = 0.8244, 0.6114, 0.4828

    ax.scatter([Es1], [h1], s=80, color="#2563eb", zorder=6)
    ax.text(Es1 + 0.008, h1, "上游缓流 $(0.9244,\\;0.80)$", fontsize=9.2, color="#1d4ed8", va="center")

    ax.scatter([Es2], [h2_sub], s=85, color="#15803d", zorder=6)
    ax.text(Es2 + 0.015, h2_sub - 0.012, "坎顶缓流正解 $(0.8244,\\;0.6114)$",
            fontsize=9.5, color="#15803d", fontweight="bold", va="center")

    ax.scatter([Es2], [h2_sup], s=85, marker="x", color="#dc2626", lw=2.4, zorder=6)
    ax.text(Es2 + 0.010, h2_sup - 0.018, "急流支舍去根 $(0.8244,\\;0.4828)$", fontsize=9.0, color="#b91c1c")

    ax.scatter([Emin], [hc], s=70, color="#475569", zorder=6)
    ax.annotate("", xy=(Emin, 0.93), xytext=(Es1, 0.93),
                arrowprops=dict(arrowstyle="<->", color="#7e22ce", lw=1.8))
    ax.text(0.5 * (Emin + Es1), 0.945, "$a_{\\mathrm{cr}} = E_{s1} - E_{\\min} = 0.1113\\,\\mathrm{m}$",
            fontsize=9.2, ha="center", color="#6b21a8")

    ax.annotate("", xy=(Es2, 0.30), xytext=(Es1, 0.30),
                arrowprops=dict(arrowstyle="->", color="#0f172a", lw=1.8))
    ax.text(0.5 * (Es1 + Es2), 0.255, "$\\Delta E_s = -a = -0.10\\,\\mathrm{m}$", fontsize=9.2, ha="center")

    ax.set_xlabel("断面单位能量 $E_s\\;(\\mathrm{m})$", fontsize=10)
    ax.set_ylabel("水深 $h\\;(\\mathrm{m})$", fontsize=10)
    ax.set_title("第 29 题：矩形明渠断面比能曲线 $E_s$—$h$ 与缓流过坎状态图", fontsize=11, pad=8)
    ax.set_xlim(0.77, 1.05)
    ax.set_ylim(0.22, 1.00)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="lower right", fontsize=8.8)
    plt.tight_layout()
    fig.savefig(dest_path, dpi=220, facecolor="white")
    plt.close(fig)


# ==============================================================================
# Text & Formula Sanitization Helpers
# ==============================================================================

def clean_year_text(s: str) -> str:
    if not s:
        return s
    # Fix OMML `not` + `\equiv` sequence without double-escaping `\not\equiv`
    s = re.sub(r"(?:\\mathrm\{not\}|(?<!\\)not)\s*\\equiv", r"\\not\\equiv ", s)
    # Strip any third-party, video, or internal reference-file wording
    replacements = [
        ("真题讲解视频", "水力学经典理论"),
        ("视频讲解", "水力学理论分析"),
        ("原视频", "常见解法"),
        ("随卷参考答案", "常见参考解答"),
        ("官方参考答案", "命题设定"),
        ("原卷 PDF 扫描件", "原卷"),
        ("原卷扫描件", "原卷"),
        ("扫描件", "原卷"),
        ("B 站", ""),
        ("B站", ""),
        ("凤鸣", ""),
        ("阿玉", ""),
        ("数砖", ""),
        ("去水印", ""),
        ("视频", "参考资料"),
    ]
    for old, new in replacements:
        s = s.replace(old, new)
    s = re.sub(r"BV1[0-9A-Za-z]+", "", s)
    s = re.sub(r"本地参考答案\s*[（(]?`?ans_p\d+`?[）)]?", "常见易错解法", s)
    s = re.sub(r"部分本地参考答案", "部分常见参考解答", s)
    s = re.sub(r"本地参考答案", "常见易错解法", s)
    s = re.sub(r"本地答案", "常见近似解法", s)
    return s.strip()


def normalize_stem(stem: str, qtype: str, year: int, qno: int) -> tuple[str, str]:
    notes = []

    # Year-specific stem typo cleanups with explicit note preservation
    if year == 2021 and qno == 14:
        stem = stem.replace(
            r"其中 ${\rho}_{1}=600{\mathrm{kg/m}}^{3}$，${\rho}_{1}=1000{\mathrm{kg/m}}^{3}$（注：原卷此处下标误印，实为 ${\rho}_{2}=1000{\mathrm{kg/m}}^{3}$）",
            r"其中 ${\rho}_{1}=600\,{\mathrm{kg/m}}^{3}$，${\rho}_{2}=1000\,{\mathrm{kg/m}}^{3}$",
        )
        notes.append("原卷将下层密度下标误印为 ρ₁=1000 kg/m³，已按 ρ₁ < ρ₂ 修正为 ρ₂=1000 kg/m³")
    elif year == 2021 and qno == 26:
        stem = stem.replace("抛物线性（注：应为“抛物线形”）", "抛物线形")
    elif year == 2021 and qno == 30:
        stem = re.sub(r"\s*\[注：[^\]]+\]", "", stem)
        notes.append("原卷 u_y 漏印负号写作 (2xy+y)，已按不可压缩无旋流场题意还原为 -(2xy+y)")
    elif year == 2020 and qno == 23:
        stem = stem.replace("行成（注：原卷误印，应为“形成”）", "形成")
    elif year == 2020 and qno == 26:
        stem = stem.replace("随后一块（注：应为“最后一块”）", "最后一块")
    elif year == 2019 and qno == 8:
        stem = re.sub(r"（注：[^）]+）", "", stem)
        notes.append("原卷公式中动能校正系数 α 误印为 ∂，已还原为 α")
    elif year == 2019 and qno == 21:
        stem = stem.replace(
            r"$\mu =0.072\, \mathrm{(N}\cdot {\mathrm{s)/m}}^{3}$（注：原卷单位误印，实为 $(\mathrm{N}\cdot {\mathrm{s)/m}}^{2}$ 即 $\mathrm{Pa}\cdot \mathrm{s}$）",
            r"$\mu =0.072\, \mathrm{(N\cdot s)/m^{2}}$",
        )
        notes.append("原卷将动力黏度单位误印为 (N·s)/m³，已修正为标准单位 (N·s)/m²")

    if qtype == "judge":
        stem = re.sub(r"[（(]\s*[）)]\s*$", "", stem).strip()
    elif qtype == "calc":
        # Strip trailing score like `（15 分）` or `, 10 分）` inside trailing parenthetical
        stem = re.sub(r"[，,]\s*\d+\s*分([）)])\s*$", r"\1", stem)
        stem = re.sub(r"[（(]\d+\s*分[）)]\s*$", "", stem).strip()
    elif qtype == "fill":
        # Convert empty parentheses `（        ）` or 3+ underscores outside `$...$` to `________`
        parts = re.split(r"(\$[^$]+\$)", stem)
        for i in range(0, len(parts), 2):
            parts[i] = re.sub(r"[（(]\s{2,}[）)]", "________", parts[i])
            parts[i] = re.sub(r"_{3,}", "________", parts[i])
        stem = "".join(parts)

    return stem.strip(), "；".join(notes)


def parse_single_year(
    year: int,
    meta_map: dict,
    calc_scores: list[int],
    double_blank_qno: int | None,
) -> dict:
    docx_path = SRC_DOCX_DIR / f"{year}年河海大学814《水力学》考研真题及详细解析.docx"
    out_dir = STD_ROOT / str(year)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    n_fill = 15 if double_blank_qno is None else 14
    n_calc = len(calc_scores)
    total_q = 10 + n_fill + n_calc

    sec_offsets = {
        "judge": 0,
        "fill": 10,
        "calc": 10 + n_fill,
    }

    questions: dict[int, dict] = {}
    analysis_buf: dict[int, list[str]] = {k: [] for k in range(1, total_q + 1)}
    pitfalls_buf: dict[int, list[str]] = {k: [] for k in range(1, total_q + 1)}

    with zipfile.ZipFile(docx_path) as zf:
        rels = {
            r.attrib["Id"]: r.attrib["Target"]
            for r in ET.fromstring(zf.read("word/_rels/document.xml.rels"))
        }
        body = ET.fromstring(zf.read("word/document.xml")).find("w:body", base_parser.NS)

        part1 = False
        part2 = False
        cur_sec = "judge"
        cur_q: int | None = None

        children = list(body)
        idx = 0
        while idx < len(children):
            el = children[idx]
            ctag = el.tag.split("}")[-1]
            raw_txt = "".join(el.itertext()).strip()

            if ctag == "p" and raw_txt.startswith("第一部分："):
                part1 = True
                idx += 1
                continue
            if ctag == "p" and raw_txt.startswith("第二部分："):
                part2 = True
                cur_q = None
                idx += 1
                continue

            if ctag == "p" and raw_txt.startswith("一、是非题"):
                cur_sec = "judge"
                cur_q = None
                idx += 1
                continue
            if ctag == "p" and raw_txt.startswith("二、填空题"):
                cur_sec = "fill"
                cur_q = None
                idx += 1
                continue
            if ctag == "p" and raw_txt.startswith(("三、计算题", "三、解答题")):
                cur_sec = "calc"
                cur_q = None
                idx += 1
                continue

            # --- Part 1: Exam Stems ---
            if part1 and not part2 and ctag == "p":
                md, imgs = base_parser.paragraph_to_markdown(el, rels)
                md = clean_year_text(md)

                m_q = re.match(r"^(\d{1,2})\.\s*(.+)$", md, flags=re.DOTALL)
                if m_q:
                    local_no = int(m_q.group(1))
                    qno = sec_offsets[cur_sec] + local_no
                    qtype = cur_sec
                    if qtype == "judge":
                        score = 2
                    elif qtype == "fill":
                        score = 4 if qno == double_blank_qno else 2
                    else:
                        score = calc_scores[local_no - 1]

                    stem_clean, note_txt = normalize_stem(m_q.group(2).strip(), qtype, year, qno)
                    questions[qno] = {
                        "id": f"{year}-{qno:02d}",
                        "year": year,
                        "no": qno,
                        "type": qtype,
                        "score": score,
                        "title": meta_map[qno]["title"],
                        "stem": stem_clean,
                        "note": note_txt,
                        "figures": [],
                        "shortAnswer": "",
                        "judgeAnswer": None,
                        "answer": "",
                        "analysis": "",
                        "analysisFigures": [],
                        "pitfalls": "",
                    }
                    cur_q = qno
                    idx += 1
                    continue

                if imgs and cur_q is not None:
                    if idx + 1 < len(children) and "".join(children[idx + 1].itertext()).strip().startswith("原卷附图"):
                        idx += 1
                    for i_im, media_rel in enumerate(imgs):
                        suf = "" if i_im == 0 else f"_{i_im + 1}"
                        fname = f"q{cur_q:02d}_orig{suf}.png"
                        (fig_dir / fname).write_bytes(zf.read("word/" + media_rel))
                        questions[cur_q]["figures"].append(
                            {"src": f"figures/{fname}", "caption": f"题 {cur_q} 图"}
                        )
                    idx += 1
                    continue

                if md and cur_q is not None and not md.startswith("原卷附图"):
                    extra_clean, extra_note = normalize_stem(md, questions[cur_q]["type"], year, cur_q)
                    questions[cur_q]["stem"] += "\n\n" + extra_clean
                    if extra_note:
                        questions[cur_q]["note"] = (
                            questions[cur_q]["note"] + "；" + extra_note
                            if questions[cur_q]["note"]
                            else extra_note
                        )
                idx += 1
                continue

            # --- Part 2: Solutions & Detailed Analysis ---
            if part2 and ctag == "p":
                md, imgs = base_parser.paragraph_to_markdown(el, rels)
                md = clean_year_text(md)

                m_sol = re.match(r"^第\s*(\d{1,2})\s*题\s*【参考答案】\s*(.+)$", md)
                if m_sol:
                    local_no = int(m_sol.group(1))
                    cur_q = sec_offsets[cur_sec] + local_no
                    ans_txt = m_sol.group(2).strip()
                    questions[cur_q]["answer"] = ans_txt
                    questions[cur_q]["shortAnswer"] = ans_txt
                    if questions[cur_q]["type"] == "judge":
                        is_true = "√" in ans_txt.split("（")[0]
                        questions[cur_q]["judgeAnswer"] = is_true
                        questions[cur_q]["shortAnswer"] = "√" if is_true else "×"
                        questions[cur_q]["answer"] = "√（正确）" if is_true else "×（错误）"
                    idx += 1
                    continue

                if cur_q is None:
                    idx += 1
                    continue

                if imgs:
                    if idx + 1 < len(children) and "".join(children[idx + 1].itertext()).strip().startswith("解析分析附图"):
                        idx += 1
                    for i_im, media_rel in enumerate(imgs):
                        suf = "" if i_im == 0 else f"_{i_im + 1}"
                        fname = f"q{cur_q:02d}_sol{suf}.png"
                        (fig_dir / fname).write_bytes(zf.read("word/" + media_rel))
                        questions[cur_q]["analysisFigures"].append(
                            {"src": f"figures/{fname}", "caption": f"第 {cur_q} 题解析示意图"}
                        )
                    idx += 1
                    continue

                if md.startswith("解析分析附图"):
                    idx += 1
                    continue

                if md.startswith("【详细解析】"):
                    md = md.replace("【详细解析】", "", 1).strip()

                if md.startswith(("【注意纠错】", "【重要勘误】", "【原卷勘误说明】", "【注：原卷中动力黏度")):
                    cleaned_pit = re.sub(r"^【[^】]+】\s*", "", md).strip()
                    cleaned_pit = re.sub(r"[，,]\s*由题干明确给出的[^：:]+[：:]\s*$", "，审题时切勿移错小数点。", cleaned_pit)
                    cleaned_pit = re.sub(r"以下按修正还原后的速度场[^：:]+[：:]\s*$", "", cleaned_pit).strip()
                    cleaned_pit = re.sub(r"本题必须对密度沿水深线性分布先积分求压强再积分求总压力[：:]\s*$",
                                         "本题必须对密度沿水深线性分布先积分求压强，再积分求总水压力。", cleaned_pit)
                    if cleaned_pit:
                        pitfalls_buf[cur_q].append(cleaned_pit)
                elif md:
                    if md.startswith("【注意核对原图】"):
                        md = md.replace("【注意核对原图】", "", 1).strip()
                    md = re.sub(r"^(?:正确推导如下|正确积分方法如下)[：:]\s*", "", md)
                    analysis_buf[cur_q].append(md)

            idx += 1

    final_questions = []
    for qno in range(1, total_q + 1):
        q = questions[qno]
        # Strip any trailing `(XX 分)` on multi-paragraph calc stems
        if q["type"] == "calc":
            q["stem"] = re.sub(r"[（(]\d+\s*分[）)]\s*$", "", q["stem"]).strip()
        q["analysis"] = "\n\n".join(analysis_buf[qno]).strip()
        q["pitfalls"] = "\n\n".join(pitfalls_buf[qno]).strip()
        meta = meta_map[qno]
        q["chapter"] = meta["chapter"]
        q["kps"] = meta["kps"]
        q["method"] = meta["method"]
        q["difficulty"] = meta["difficulty"]
        if "subType" in meta:
            q["subType"] = meta["subType"]
        if "rubric" in meta:
            q["rubric"] = meta["rubric"]
        final_questions.append(q)

    # --- Apply Targeted Independent Verification Fixes & Custom Matplotlib Figures ---
    if year == 2021:
        draw_2021_q28_sol(fig_dir / "q28_sol.png")
        draw_2021_q29_sol(fig_dir / "q29_sol.png")

    elif year == 2020:
        # Fix Q10: Stem diagram is a sudden-expansion pipe with 3 clear errors -> statement "绘制是错误的" is TRUE (`√`)!
        q10 = final_questions[9]
        draw_2020_q10_sol(fig_dir / "q10_sol.png")
        q10["judgeAnswer"] = True
        q10["shortAnswer"] = "√"
        q10["answer"] = "√（正确）"
        q10["analysis"] = (
            "观察题图可知，连接上下游两水池的有压管道在中部存在明显的**突然扩大变径**（左段细管管径 $d_1$ 小、流速 $v_1$ 大；右段粗管管径 $d_2$ 大、流速 $v_2$ 小）。图中总水头线与测压管水头线存在三处明显物理错误：\n\n"
            "1. **测压管水头线在突扩处升降方向画反**：水流经突然扩大断面减速增压，局部水头损失 $h_j = \\frac{(v_1 - v_2)^2}{2g}$ 小于流速水头减小量 $\\frac{v_1^2 - v_2^2}{2g}$，故测压管水头线在突扩过渡段应**沿程上升**（抬升量为 $\\frac{v_2(v_1 - v_2)}{g} > 0$），而图中却误画为随总水头线同步铅垂突降；\n\n"
            "2. **两线铅垂间距未随流速减小而收窄**：总水头线与测压管水头线之间的铅垂距离等于流速水头 $\\frac{\\alpha v^2}{2g}$，进入下游粗管后 $v_2 < v_1$，两线间距应显著变小，而图中前后两段间距几乎相等；\n\n"
            "3. **粗管段水力坡度未变缓**：由 $J = \\lambda \\frac{1}{d}\\frac{v^2}{2g} \\propto d^{-5}$ 知，下游粗管段的水头线斜率应远缓于上游细管段，图中两段斜率却画成相同。\n\n"
            "因此题干断言“下图所示的总水头线与测压管水头线的绘制是错误的”完全属实，应判为 **√**。"
        )
        q10["analysisFigures"] = [
            {"src": "figures/q10_sol.png", "caption": "第 10 题解析示意图"}
        ]
        q10["pitfalls"] = (
            "本题有双重审题陷阱：① 看清题图管道中部为**突然扩大变径管**而非等径直管；"
            "② 题干问的是“绘制是**错误的**（　）”，因原图确实画错，故命题本身成立，应打 √ 而非 ×！"
        )

        # Clean Q17 flow-net diagram & Q26 true-orientation folded-wall diagram
        draw_2020_q17_sol(fig_dir / "q17_sol.png")
        draw_2020_q26_sol(fig_dir / "q26_sol.png")

    elif year == 2019:
        # Crisp redraw of Q03 stem figure
        draw_2019_q03_orig(fig_dir / "q03_orig.png")
        q03 = final_questions[2]
        q03["pitfalls"] = (
            "务必区分潜没闸门与露顶闸门：仅当闸门顶边始终潜没于上下游水面以下（图 1）时，两侧同升相同水位产生的附加矩形压强分布完全抵消；"
            "一旦闸门露顶（图 2），水位上升会使受压面积向上扩展，净总压力增大且压心位置改变。"
        )

        # Physically exact siphon THL/HGL diagram for Q27
        draw_2019_q27_sol(fig_dir / "q27_sol.png")

        # Refine discarded supercritical root 0.4783 -> 0.4828 in Q29 + exact Es-h plot
        q29 = final_questions[28]
        q29["analysis"] = q29["analysis"].replace("0.4783", "0.4828")
        q29["answer"] = (
            "（1）$h_2 = 0.6114\\,\\mathrm{m}$；（2）$F = 1.406\\,\\mathrm{kN}$，方向水平向右（向下游）；"
            "（3）缓流；（4）$a_{\\text{临界}} = 0.1113\\,\\mathrm{m}$"
        )
        q29["shortAnswer"] = "（1）0.6114 m；（2）1.406 kN（向右）；（3）缓流；（4）0.1113 m"
        draw_2019_q29_sol(fig_dir / "q29_sol.png")

    # Build sections metadata
    fill_sec = {
        "id": "fill",
        "title": "二、填空题",
        "range": [11, 10 + n_fill],
        "totalScore": 30,
    }
    if double_blank_qno is None:
        fill_sec["description"] = "共 15 小题，每小题 2 分，共 30 分。"
        fill_sec["scorePerQuestion"] = 2
    else:
        fill_sec["description"] = f"共 {n_fill} 小题（第 {double_blank_qno} 题含 2 空为 4 分，其余每题 2 分），共 30 分。"

    calc_score_str = "+".join(str(s) for s in calc_scores)
    calc_sec = {
        "id": "calc",
        "title": "三、计算题",
        "description": f"共 {n_calc} 小题（{calc_score_str} 分），共 100 分。",
        "range": [11 + n_fill, total_q],
        "totalScore": 100,
    }

    paper = {
        "year": year,
        "code": "814",
        "subject": "水力学",
        "school": "河海大学",
        "totalScore": 150,
        "durationMinutes": 180,
        "calculatorAllowed": False,
        "examNotes": [
            "满分 150 分，考试时间 180 分钟，闭卷笔试。",
            "除特别说明外，统一取重力加速度 $g = 9.81\\,\\mathrm{m/s^2}$，水密度 $\\rho = 1000\\,\\mathrm{kg/m^3}$。",
            f"题型与分值：一、是非题（10×2=20 分）；二、填空题（共 15 空，每空 2 分，共 30 分）；三、计算题（共 {n_calc} 题，{calc_score_str}=100 分）。",
        ],
        "sections": [
            {
                "id": "judge",
                "title": "一、是非题",
                "description": "共 10 小题，每小题 2 分，共 20 分。",
                "range": [1, 10],
                "scorePerQuestion": 2,
                "totalScore": 20,
            },
            fill_sec,
            calc_sec,
        ],
        "questions": final_questions,
    }

    # 1) Write standardized pack: `河海大学已整理数据/{year}/{year}.json`
    std_json_path = out_dir / f"{year}.json"
    std_json_path.write_text(json.dumps(paper, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2) Write web-ready pack: `web/public/data/hhu-814/{year}.json` + WebP figures (quality=90, method=5)
    web_paper = copy.deepcopy(paper)
    web_fig_dir = WEB_COURSE_DIR / "figures" / str(year)
    web_fig_dir.mkdir(parents=True, exist_ok=True)

    fig_count = 0
    for q in web_paper["questions"]:
        for key in ("figures", "analysisFigures"):
            new_figs = []
            for fig_item in q.get(key, []):
                src_png = out_dir / fig_item["src"]
                webp_name = f"{src_png.stem}.webp"
                dest_webp = web_fig_dir / webp_name
                img = Image.open(src_png)
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA")
                img.save(dest_webp, format="WEBP", quality=90, method=5)
                new_figs.append({
                    "src": f"figures/{year}/{webp_name}",
                    "caption": fig_item["caption"],
                })
                fig_count += 1
            q[key] = new_figs

    web_json_path = WEB_COURSE_DIR / f"{year}.json"
    web_json_path.write_text(json.dumps(web_paper, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"[{year}] Wrote {len(final_questions)} questions (score={sum(q['score'] for q in final_questions)}), "
        f"{fig_count} figures -> {std_json_path.relative_to(ROOT)} & {web_json_path.relative_to(ROOT)}"
    )
    return web_paper


def main():
    parse_single_year(
        year=2021,
        meta_map=META_2021,
        calc_scores=[15, 20, 20, 15, 20, 10],
        double_blank_qno=None,
    )
    parse_single_year(
        year=2020,
        meta_map=META_2020,
        calc_scores=[10, 15, 20, 20, 20, 15],
        double_blank_qno=17,
    )
    parse_single_year(
        year=2019,
        meta_map=META_2019,
        calc_scores=[10, 20, 15, 15, 25, 15],
        double_blank_qno=21,
    )


if __name__ == "__main__":
    main()
