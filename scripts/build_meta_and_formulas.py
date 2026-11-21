# -*- coding: utf-8 -*-
"""
Generate `web/public/data/chapters.json` and `web/public/data/formulas.json`
for Hohai University 814 Hydraulics (河海大学 814 水力学).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DATA_DIR = ROOT / "web" / "public" / "data"

CHAPTERS_DATA = {
    "syllabusTitle": "814 水力学章节考察规律（据历年真题与公开资料整理，非官方）",
    "textbook": "参考教材：《水力学》，赵振兴、何建京等编著，清华大学出版社（以当年河海大学研究生院公布的参考书目为准）",
    "highlights": [
        "大题（计算题 100 分）近年来只出在前八章！",
        "第 9～13 章不考大题、只考小题（判断/填空/简答），总分值不超过 15 分。",
        "近年真题共 30 题：判断 10 题 + 填空简答 15 题 + 计算大题 5 题，限时 180 分钟且禁用计算器。",
    ],
    "omittedChapterNote": "教材第十二章（高速水流/波浪等选修内容）不在 814 常规命题范围内，故按考纲原表保留第 1～11 章及第 13 章。",
    "chapters": [
        {
            "chapter": 1,
            "name": "绪论",
            "fullTitle": "第一章：绪论",
            "questionTypes": "1～2 个小题，必有 1 个大题",
            "scoreRange": [10, 15],
            "scoreLabel": "10-15",
            "stars": 2,
            "hasBigQuestion": True,
            "summary": "聚焦连续介质与理想液体假设、液体主要物理性质（黏滞性、压缩性、表面张力），大题核心围绕牛顿内摩擦定律在平板剪切流、双层液体、同轴圆筒/圆盘间隙油膜中的力学平衡计算。",
            "coreKps": ["连续介质假设", "理想液体假设", "牛顿内摩擦定律", "双层液体平板剪切流", "环形/圆盘间隙黏性阻力矩"]
        },
        {
            "chapter": 2,
            "name": "水静力学",
            "fullTitle": "第二章：水静力学",
            "questionTypes": "2 个小题，必有 1～2 个大题",
            "scoreRange": [15, 30],
            "scoreLabel": "15-30",
            "stars": 3,
            "hasBigQuestion": True,
            "summary": "814 核心重分章！必考平面闸门（矩形/梯形/可绕轴转动闸门）或二元曲面（圆柱面/圆弧闸门）静水总压力计算，常与封闭容器气体压强、U 形水银压差计联合设题。",
            "coreKps": ["静水压强基本方程", "水头与能量量纲", "U形水银压差计测压", "平面静水总压力", "圆柱曲面静水总压力", "压力体图与虚压力体"]
        },
        {
            "chapter": 3,
            "name": "液体一元恒定总流基本原理",
            "fullTitle": "第三章：液体一元恒定总流基本原理",
            "questionTypes": "必有 1 个大题（含基础概念小题）",
            "scoreRange": [20, 30],
            "scoreLabel": "20-30",
            "stars": 3,
            "hasBigQuestion": True,
            "summary": "水力学三大方程（连续性方程、恒定总流能量方程/伯努利方程、恒定总流动量方程）综合运用！大题极常以渐缩弯管、分叉管、射流冲击或明渠底坎/闸门水流作用力压轴。",
            "coreKps": ["断面平均流速", "流线与迹线", "恒定总流连续性方程", "恒定总流能量方程", "总水头线与测压管水头线", "恒定总流动量方程", "弯管/底坎水流作用力"]
        },
        {
            "chapter": 4,
            "name": "层流紊流、液流阻力和水头损失",
            "fullTitle": "第四章：层流紊流、液流阻力和水头损失",
            "questionTypes": "小题较多",
            "scoreRange": [10, 15],
            "scoreLabel": "10-15",
            "stars": 1,
            "hasBigQuestion": False,
            "summary": "以概念辨析和小型计算为主：雷诺数流态判别、圆管层流流速抛物线与切应力线性分布、尼古拉兹试验五区规律、达西公式与局部水头损失公式。",
            "coreKps": ["雷诺数与流态判别", "圆管均匀流切应力分布", "圆管层流哈根-泊肃叶定律", "达西-韦斯巴赫公式", "紊流阻力分区", "断面流速分布", "沿程水头损失规律"]
        },
        {
            "chapter": 5,
            "name": "液体三元流动基本原理",
            "fullTitle": "第五章：液体三元流动基本原理",
            "questionTypes": "必有 1 个大题",
            "scoreRange": [15, 20],
            "scoreLabel": "15-20",
            "stars": 2,
            "hasBigQuestion": True,
            "summary": "题型高度固定、性价比极高的必拿分大题！重点掌握欧拉法加速度（当地+迁移）、连续性微分方程、有旋/无旋判据（旋转角速度）、平面势流流函数 ψ 与速度势 φ 偏积分及欧拉运动微分方程求压强差。",
            "coreKps": ["欧拉法速度场", "当地加速度与迁移加速度", "恒定流与均匀流判别", "平面不可压缩流连续性方程", "无旋流判据", "流函数与速度势函数求解", "欧拉运动微分方程"]
        },
        {
            "chapter": 6,
            "name": "有压管流",
            "fullTitle": "第六章：有压管流",
            "questionTypes": "必有 1 个大题（常与第 3、4 章结合）",
            "scoreRange": [10, 15],
            "scoreLabel": "10-15",
            "stars": 2,
            "hasBigQuestion": True,
            "summary": "涵盖简单短管自由/淹没出流、虹吸管水力计算（最高断面最大真空度校核）、长管串并联与三水池分叉管网水头分配，以及有压管道直接/间接水击计算。",
            "coreKps": ["简单短管自由出流", "虹吸管水力计算", "真空高度(真空度)", "长管串并联与三水池问题", "有压渐扩管压强变化", "有压管道水击(水锤)", "直接与间接水击判别", "儒可夫斯基公式"]
        },
        {
            "chapter": 7,
            "name": "明渠均匀流",
            "fullTitle": "第七章：明渠均匀流",
            "questionTypes": "第七章和第八章中必有 1～2 个大题",
            "scoreRange": [10, 15],
            "scoreLabel": "10-15",
            "stars": 2,
            "hasBigQuestion": True,
            "summary": "掌握矩形与梯形渠道几何要素（过水面积、水面宽、湿周、水力半径、水力深度）、谢才—曼宁公式、水力最佳断面条件及无压圆管最大流量/流速。",
            "coreKps": ["梯形断面水力要素", "明渠均匀流曼宁公式", "水力最佳断面", "弗劳德数判急缓流", "明渠雷诺数判层紊流"]
        },
        {
            "chapter": 8,
            "name": "明渠非均匀流",
            "fullTitle": "第八章：明渠非均匀流",
            "questionTypes": "第七章和第八章中必有 1～2 个大题",
            "scoreRange": [20, 30],
            "scoreLabel": "20-30",
            "stars": 3,
            "hasBigQuestion": True,
            "summary": "全书概念深度最高、小题与综合题并重的压轴板块！核心包含断面比能曲线、临界水深与临界底坡、水跃共轭水深、12 种棱柱形明渠水面曲线（M/S/C/H/A）定性绘制与分段求和法，兼及闸门启闭非恒定涌波。",
            "coreKps": ["断面单位能量(比能)", "临界水深与临界底坡", "明渠渐变流基本微分方程", "缓坡水面曲线(M1/M2/M3)", "明渠水面曲线定性分析", "急流减速水面线", "明渠水跃与跃后水深", "明渠非恒定流涌波"]
        },
        {
            "chapter": 9,
            "name": "堰流与孔流",
            "fullTitle": "第九章：堰流与孔流",
            "questionTypes": "无大题，只有小题",
            "scoreRange": [4, 4],
            "scoreLabel": "4",
            "stars": 1,
            "hasBigQuestion": False,
            "summary": "只考选择/判断/填空小计算：区分薄壁堰、实用堰、宽顶堰与孔口/闸孔出流的相对开度界限（e/H ≤ 0.65 为闸孔出流），熟记流量公式与水头幂次（孔闸 1/2 次方、堰流 3/2 次方）。",
            "coreKps": ["孔口与管嘴出流", "平板闸孔出流判别", "闸孔自由出流流量公式", "堰流分类与基本流量公式"]
        },
        {
            "chapter": 10,
            "name": "消能",
            "fullTitle": "第十章：消能",
            "questionTypes": "无大题，只有小题",
            "scoreRange": [2, 2],
            "scoreLabel": "2",
            "stars": 1,
            "hasBigQuestion": False,
            "summary": "高频 2 分必拿小题！重点掌握过堰/闸下急流收缩断面跃后共轭水深 h'' 与下游尾水深 ht 的三种衔接关系（远驱式、临界式、淹没式）及底流消力池设计判据。",
            "coreKps": ["底流消能判别", "水跃衔接形式", "矩形明渠共轭水深", "挑流与面流消能特点"]
        },
        {
            "chapter": 11,
            "name": "渗流",
            "fullTitle": "第十一章：渗流",
            "questionTypes": "无大题，只有小题",
            "scoreRange": [4, 4],
            "scoreLabel": "4",
            "stars": 1,
            "hasBigQuestion": False,
            "summary": "紧扣达西渗流定律适用范围（线性层流）、渗流流速与实际孔隙流速关系、潜水完全井/承压井裘布依公式，以及正交渗流流网求单宽渗流量与扬压力。",
            "coreKps": ["达西定律与适用范围", "渗流流速与实际流速", "平面渗流流网", "达西定律与单宽渗流量"]
        },
        {
            "chapter": 13,
            "name": "水力相似与模型试验基本原理",
            "fullTitle": "第十三章：水力相似与模型试验基本原理",
            "questionTypes": "无大题，只有小题",
            "scoreRange": [4, 4],
            "scoreLabel": "4",
            "stars": 1,
            "hasBigQuestion": False,
            "summary": "稳拿 4 分送分章！熟记几何/运动/动力相似关系，明渠堰闸采用弗劳德准则（v_r=L_r^0.5, Q_r=L_r^2.5, t_r=L_r^0.5, n_r=L_r^(1/6)），有压管流采用雷诺准则，以及河工模型加糙原理。",
            "coreKps": ["弗劳德相似准则", "流量比尺换算", "雷诺相似准则", "河工模型阻力相似", "糙率比尺与模型加糙"]
        }
    ]
}

FORMULAS_DATA = [
    # Chapter 1
    {
        "id": "f-01-01",
        "chapter": 1,
        "name": "牛顿内摩擦定律",
        "latex": r"\tau = \mu \frac{\mathrm{d}u}{\mathrm{d}y} = \rho \nu \frac{\mathrm{d}u}{\mathrm{d}y}, \quad F = \tau A",
        "variables": r"$\tau$ 为切应力（$\mathrm{Pa}$）；$\mu$ 为动力黏度（$\mathrm{Pa\cdot s}$）；$\nu = \mu/\rho$ 为运动黏度（$\mathrm{m^2/s}$）；$\mathrm{d}u/\mathrm{d}y$ 为法向速度梯度。",
        "note": r"仅适用于牛顿流体层流或薄油膜线性速度分布（$\mathrm{d}u/\mathrm{d}y \approx \Delta u / \delta$）；理想液体 $\mu=0 \Rightarrow \tau=0$。"
    },
    {
        "id": "f-01-02",
        "chapter": 1,
        "name": "双层牛顿液体平板剪切等效关系",
        "latex": r"\tau = \mu_1 \frac{U - v}{\delta_1} = \mu_2 \frac{v}{\delta_2} = \frac{U}{\dfrac{\delta_1}{\mu_1} + \dfrac{\delta_2}{\mu_2}}",
        "variables": r"$U$ 为上运动平板速度；$v$ 为两液层交界面速度；$\delta_1, \delta_2$ 与 $\mu_1, \mu_2$ 分别为两层厚度与动力黏度。",
        "note": r"类比串联热阻：恒定匀速剪切时液-液分界面两侧切应力相等且速度连续（2026 第 26 题直接秒杀校验公式）。"
    },
    {
        "id": "f-01-03",
        "chapter": 1,
        "name": "液体体积压缩系数与弹性模量",
        "latex": r"\beta_p = -\frac{1}{V}\frac{\mathrm{d}V}{\mathrm{d}p} = \frac{1}{\rho}\frac{\mathrm{d}\rho}{\mathrm{d}p}, \quad K = \frac{1}{\beta_p}",
        "variables": r"$\beta_p$ 为体积压缩系数（$\mathrm{Pa^{-1}}$）；$K$ 为体积弹性模量（$\mathrm{Pa}$），水中声速/刚性管水击波速 $c_0 = \sqrt{K/\rho}$。",
        "note": r"体积随压强增大而减小，故带负号以保证 $\beta_p > 0$。"
    },
    # Chapter 2
    {
        "id": "f-02-01",
        "chapter": 2,
        "name": "静水压强基本方程（水头形式与压强形式）",
        "latex": r"z + \frac{p}{\gamma} = C \quad \Longleftrightarrow \quad p = p_0 + \gamma h",
        "variables": r"$z$ 为单位重量液体的位置势能（位置水头，$\mathrm{m}$）；$p/\gamma$ 为单位重量液体的压强势能（压强水头，$\mathrm{m}$）；$z+p/\gamma$ 为测压管水头。",
        "note": r"适用条件：重力场中同一种连续、静止、均质不可压缩液体。注意区分“单位重量（$\mathrm{m}$）”与“单位体积（$\rho gz, \mathrm{Pa}$）”！"
    },
    {
        "id": "f-02-02",
        "chapter": 2,
        "name": "绝对压强、相对压强（表压）与真空度",
        "latex": r"p_{\text{相}} = p_{\text{绝}} - p_a, \quad p_v = p_a - p_{\text{绝}} = -p_{\text{相}}, \quad h_v = \frac{p_v}{\gamma}",
        "variables": r"$p_a$ 为当地大气压强；$p_v$ 为真空压强（当 $p_{\text{绝}} < p_a$ 时）；$h_v$ 为真空高度（水柱高，$\mathrm{m}$）。",
        "note": r"水力学计算中除特别声明外一律采用相对压强（表压），自由大气面 $p_{\text{相}} = 0$。"
    },
    {
        "id": "f-02-03",
        "chapter": 2,
        "name": "平面上的静水总压力与压心坐标",
        "latex": r"P = p_C A = \gamma h_C A, \quad y_D = y_C + \frac{I_C}{y_C A}",
        "variables": r"$h_C$ 为受压平面形心 $C$ 在等效自由液面下的淹没深度；$y_C$ 为沿斜面向下量至形心的斜距；$I_C$ 为平面绕水平形心轴的惯性矩。",
        "note": r"矩形绕水平形心轴 $I_C = bh^3/12$；压心 $D$ 恒在形心 $C$ 下方（水平放置平面除外）。梯形闸门也可拆分为矩形+两个对称三角形分块求和。"
    },
    {
        "id": "f-02-04",
        "chapter": 2,
        "name": "二元曲面静水总压力（水平投影与压力体合成）",
        "latex": r"P_x = \gamma h_C A_x, \quad P_z = \gamma V_z, \quad P = \sqrt{P_x^2 + P_z^2}, \quad \tan\alpha = \frac{P_z}{P_x}",
        "variables": r"$A_x$ 为曲面在铅直面上的投影面积；$h_C$ 为投影面形心淹没水深；$V_z$ 为曲面铅垂压力体体积。",
        "note": r"圆柱曲面上微元压力均垂直于弧面指向（或背离）圆心，故总压力合力 $P$ 作用线必通过圆柱圆心 $O$！注意实压力体向下、虚压力体向上。"
    },
    # Chapter 3
    {
        "id": "f-03-01",
        "chapter": 3,
        "name": "恒定总流连续性方程",
        "latex": r"Q = A_1 v_1 = A_2 v_2 = \int_A u\,\mathrm{d}A",
        "variables": r"$Q$ 为体积流量（$\mathrm{m^3/s}$）；$A$ 为过水断面面积；$v = Q/A$ 为断面平均流速。",
        "note": r"适用条件：不可压缩流体、恒定流、无沿程旁侧汇入或分出；对非渐变流断面只要封闭控制体恒定仍成立。"
    },
    {
        "id": "f-03-02",
        "chapter": 3,
        "name": "实际液体恒定总流能量方程（伯努利方程）",
        "latex": r"z_1 + \frac{p_1}{\gamma} + \frac{\alpha_1 v_1^2}{2g} = z_2 + \frac{p_2}{\gamma} + \frac{\alpha_2 v_2^2}{2g} + h_{w1\text{-}2}",
        "variables": r"$\alpha$ 为动能修正系数（圆管层流 $\alpha=2.0$，紊流取 $\alpha \approx 1.0$）；$h_{w1\text{-}2} = \sum h_f + \sum h_j$ 为两断面间总水头损失。",
        "note": r"所选计算断面 1—1、2—2 必须位于渐变流段（断面上符合静水压强分布规律 $z+p/\gamma = \text{const}$），两断面之间可以包含急变流段。"
    },
    {
        "id": "f-03-03",
        "chapter": 3,
        "name": "恒定总流动量方程",
        "latex": r"\sum \vec{F} = \rho Q \left( \beta_2 \vec{v}_2 - \beta_1 \vec{v}_1 \right)",
        "variables": r"$\sum \vec{F}$ 为作用在控制体水体上的全部外力矢量和（重力、动水压力、固壁反力等）；$\beta \approx 1.0$ 为动量修正系数。",
        "note": r"严格矢量方程！投影列式时先规定坐标正方向；求出固壁对水体的反力 $\vec{R}$ 后，水流对固壁的作用力 $\vec{R}^{\prime} = -\vec{R}$（方向相反）。"
    },
    # Chapter 4
    {
        "id": "f-04-01",
        "chapter": 4,
        "name": "圆管均匀流切应力分布与层流哈根—泊肃叶公式",
        "latex": r"\tau(r) = \frac{\gamma J r}{2} = \frac{r}{r_0}\tau_0, \quad u(r) = u_{\max}\left(1 - \frac{r^2}{r_0^2}\right), \quad v = \frac{1}{2}u_{\max} = \frac{\gamma J d^2}{32\mu}",
        "variables": r"$r$ 为距管轴径向距离；$r_0 = d/2$ 为管半径；$\tau_0 = \gamma R J$ 为管壁切应力；层流沿程阻力系数 $\lambda = 64/Re$。",
        "note": r"切应力线性分布 $\tau(r) \propto r$ 对圆管层流和紊流均匀流均成立！管轴处 $r=0 \Rightarrow \tau=0$（2026 第 21 题秒杀）。流速旋转抛物面仅限层流！"
    },
    {
        "id": "f-04-02",
        "chapter": 4,
        "name": "达西—韦斯巴赫沿程水头损失公式与局部损失公式",
        "latex": r"h_f = \lambda \frac{l}{d}\frac{v^2}{2g} = \lambda \frac{l}{4R}\frac{v^2}{2g}, \quad h_j = \zeta \frac{v^2}{2g}",
        "variables": r"$\lambda$ 为沿程阻力系数；$\zeta$ 为局部阻力系数；圆管突然扩大局部损失（波达公式）$h_j = \frac{(v_1 - v_2)^2}{2g}$。",
        "note": r"层流区 $h_f \propto v^1$；紊流光滑区（布拉休斯 $\lambda = 0.3164 Re^{-0.25}$）$h_f \propto v^{1.75}$；紊流粗糙区（阻力平方区）$h_f \propto v^2$（均指断面平均流速 $v$！）。"
    },
    {
        "id": "f-04-03",
        "chapter": 4,
        "name": "圆管与明渠下临界雷诺数",
        "latex": r"Re_d = \frac{vd}{\nu} \quad (Re_{d,c} = 2000), \qquad Re_R = \frac{vR}{\nu} \quad (Re_{R,c} = 500)",
        "variables": r"$d$ 为圆管内径；$R = A/\chi$ 为水力半径（满管圆管 $R = d/4$，故 $Re_d = 4 Re_R$，临界值 $2000 \leftrightarrow 500$ 一一对应）。",
        "note": r"小于下临界雷诺数为层流，大于则为紊流（或过渡流）。"
    },
    # Chapter 5
    {
        "id": "f-05-01",
        "chapter": 5,
        "name": "欧拉法流体质点全加速度（当地加速度 + 迁移加速度）",
        "latex": r"a_x = \frac{\mathrm{d}u_x}{\mathrm{d}t} = \frac{\partial u_x}{\partial t} + u_x\frac{\partial u_x}{\partial x} + u_y\frac{\partial u_x}{\partial y} + u_z\frac{\partial u_x}{\partial z}",
        "variables": r"$\partial u_x/\partial t$ 为当地（时变）加速度，恒定流为零；后三项之和为迁移（位变）加速度，均匀流为零。",
        "note": r"判断恒定流看速度分量是否显含时间 $t$；判断均匀流看速度分量是否随空间坐标变化（及流线是否为平行直线）。"
    },
    {
        "id": "f-05-02",
        "chapter": 5,
        "name": "不可压缩流体连续性微分方程",
        "latex": r"\nabla \cdot \vec{u} = \frac{\partial u_x}{\partial x} + \frac{\partial u_y}{\partial y} + \frac{\partial u_z}{\partial z} = 0",
        "variables": r"对不可压缩流体，无论恒定流还是非恒定流、理想流体还是黏性流体均成立！",
        "note": r"平面流动 $\frac{\partial u}{\partial x} + \frac{\partial v}{\partial y} = 0$ 是存在流函数 $\psi(x,y)$ 的充要条件。"
    },
    {
        "id": "f-05-03",
        "chapter": 5,
        "name": "平面流动旋转角速度、流函数与速度势函数",
        "latex": r"\omega_z = \frac{1}{2}\left(\frac{\partial v}{\partial x} - \frac{\partial u}{\partial y}\right), \quad u = \frac{\partial \psi}{\partial y} = \frac{\partial \varphi}{\partial x}, \quad v = -\frac{\partial \psi}{\partial x} = \frac{\partial \varphi}{\partial y}",
        "variables": r"$\omega_z = 0$ 为无旋（有势）流充要条件；平面不可压势流同时满足 $\nabla^2 \psi = 0$ 与 $\nabla^2 \varphi = 0$，流线与等势线正交。",
        "note": r"两流线间单宽流量 $q = |\psi_2 - \psi_1|$。答题时先写明自己采用的符号定义式，避免不同教材正负号约定差异失分。"
    },
    # Chapter 6
    {
        "id": "f-06-01",
        "chapter": 6,
        "name": "简单短管自由出流与淹没出流流量公式",
        "latex": r"Q = \mu_c A \sqrt{2gH_0}, \quad \mu_c = \frac{1}{\sqrt{\alpha + \lambda \dfrac{l}{d} + \sum \zeta}}",
        "variables": r"自由出流 $H_0$ 为上游行近总水头至出口断面中心的铅垂高差；淹没出流 $H_0$ 为上下游水池自由水面高差（且含出口突然扩大局部损失 $\zeta_{\text{出}}=1$）。",
        "note": r"管路系统阻抗不变时，增大上下游作用水头 $H_0$（如出口下移 $\Delta h$），流量必增大。"
    },
    {
        "id": "f-06-02",
        "chapter": 6,
        "name": "虹吸管顶部断面真空高度计算",
        "latex": r"h_{v,A} = -\frac{p_A}{\gamma} = z_A + \left( \alpha + \lambda \frac{l_1}{d} + \sum \zeta_{0\text{-}A} \right)\frac{v^2}{2g}",
        "variables": r"$z_A$ 为虹吸管最高断面高出上游水面的高度；$l_1$ 为进口至 $A$ 断面管长；流速 $v$ 先由上下游总水位差能量方程求出。",
        "note": r"工程上水泵与虹吸管最大允许真空高度一般不超过 $7\sim 8\,\mathrm{m}$ 水柱，防止汽化断流。"
    },
    {
        "id": "f-06-03",
        "chapter": 6,
        "name": "有压管道水击相长与儒可夫斯基直接水击公式",
        "latex": r"T_r = \frac{2L}{c}, \quad \Delta p_{\max} = \rho c v_0 \quad (T_s \le T_r\text{ 直接水击})",
        "variables": r"$L$ 为管长；$c$ 为水击波速；$T_r = 2L/c$ 为水击相（往返传播时间）；$T_s$ 为阀门关闭时间；$v_0$ 为关阀前流速。",
        "note": r"当 $T_s \le 2L/c$ 时阀门处为直接水击，最大水击水头增量 $\Delta H = c v_0 / g$；当 $T_s > 2L/c$ 时反射降压波抵消增压，为间接水击（$\Delta p < \rho c v_0$）。"
    },
    # Chapter 7
    {
        "id": "f-07-01",
        "chapter": 7,
        "name": "梯形明渠断面水力要素汇总",
        "latex": r"A = (b + mh)h, \quad B = b + 2mh, \quad \chi = b + 2h\sqrt{1+m^2}, \quad R = \frac{A}{\chi}, \quad \overline{h} = \frac{A}{B}",
        "variables": r"$b$ 为渠底宽；$m = \cot\theta$ 为边坡系数（矩形断面取 $m=0$）；$B$ 为水面宽；$\chi$ 为湿周（不含自由水面！）；$\overline{h}$ 为水力深度。",
        "note": r"湿周 $\chi$ 只算水体与固体渠壁接触的周长，切勿加上水面宽 $B$！"
    },
    {
        "id": "f-07-02",
        "chapter": 7,
        "name": "明渠均匀流谢才公式与曼宁公式",
        "latex": r"v = C\sqrt{RJ}, \quad C = \frac{1}{n}R^{1/6}, \quad Q = K\sqrt{i} = \frac{1}{n} A R^{2/3} i^{1/2}",
        "variables": r"$n$ 为曼宁糙率；$C$ 为谢才系数（量纲 $\mathrm{m^{1/2}/s}$，并非无量纲！）；均匀流时总水头坡度 $J = J_p = i$；$K = AC\sqrt{R}$ 为流量模数。",
        "note": r"仅在正坡（$i > 0$）、棱柱形长直顺直渠道、流量与糙率恒定时才可能形成明渠恒定均匀流。"
    },
    {
        "id": "f-07-03",
        "chapter": 7,
        "name": "梯形与矩形明渠水力最佳断面条件",
        "latex": r"\beta_{\text{优}} = \frac{b}{h} = 2\left(\sqrt{1+m^2} - m\right), \quad R_{\text{优}} = \frac{h}{2}",
        "variables": r"面积 $A$、底坡 $i$、糙率 $n$ 一定时湿周最小（通过流量最大）的断面。矩形（$m=0$）时最佳宽深比 $\beta_{\text{优}} = b/h = 2$。",
        "note": r"水力最佳梯形断面的三个边与底边均与以水面中点为圆心、半径为 $h/2$ 的半圆相切，恒有 $R_{\text{优}} = h/2$。"
    },
    # Chapter 8
    {
        "id": "f-08-01",
        "chapter": 8,
        "name": "明渠断面单位能量（断面比能）与弗劳德数",
        "latex": r"E_s = h + \frac{\alpha Q^2}{2gA^2}, \quad \frac{\mathrm{d}E_s}{\mathrm{d}h} = 1 - Fr^2, \quad Fr = \frac{v}{\sqrt{g\overline{h}}} = \sqrt{\frac{\alpha Q^2 B}{gA^3}}",
        "variables": r"$Fr < 1$ 为缓流（$h > h_c$）；$Fr = 1$ 为临界流（$h = h_c$，$E_s$ 取极小值 $E_{s,\min}$）；$Fr > 1$ 为急流（$h < h_c$）。",
        "note": r"非矩形断面弗劳德数必须用水力深度 $\overline{h} = A/B$！对矩形断面（$\alpha=1$）：$h_c = \sqrt[3]{q^2/g}$，$E_{s,\min} = \frac{3}{2}h_c$。"
    },
    {
        "id": "f-08-02",
        "chapter": 8,
        "name": "断面比能沿程变化率与棱柱形明渠渐变流基本微分方程",
        "latex": r"\frac{\mathrm{d}E_s}{\mathrm{d}s} = i - J, \qquad \frac{\mathrm{d}h}{\mathrm{d}s} = \frac{i - J}{1 - Fr^2} = \frac{i\left(1 - \dfrac{K_0^2}{K^2}\right)}{1 - \dfrac{h_c^3}{h^3}\text{（宽浅矩形）}}",
        "variables": r"$i = -\mathrm{d}z/\mathrm{d}s$ 为底坡；$J = -\mathrm{d}H/\mathrm{d}s > 0$ 为总水头线坡度；测压管坡度 $J_p = i - \mathrm{d}h/\mathrm{d}s$。",
        "note": r"1区（$h > h_0, h_c$）与 3区（$h < h_0, h_c$）分子分母同号，$\mathrm{d}h/\mathrm{d}s > 0$ 为壅水曲线；2区介于 $h_0$ 与 $h_c$ 之间，$\mathrm{d}h/\mathrm{d}s < 0$ 为降水曲线。"
    },
    {
        "id": "f-08-03",
        "chapter": 8,
        "name": "平底矩形明渠水跃共轭水深公式",
        "latex": r"h_2 = \frac{h_1}{2}\left(\sqrt{1 + 8 Fr_1^2} - 1\right), \quad h_1 h_2 \frac{h_1 + h_2}{2} = \frac{q^2}{g} = h_c^3, \quad h_j = \frac{(h_2 - h_1)^3}{4 h_1 h_2}",
        "variables": r"$h_1 < h_c$ 为跃前急流水深；$h_2 > h_c$ 为跃后缓流水深；$h_j = E_{s1} - E_{s2}$ 为水跃消能水头损失。",
        "note": r"由水平动量守恒（跃前跃后水跃函数 $J(h) = \frac{1}{2}bh^2 + \frac{Q^2}{gbh}$ 相等）导出，禁止对水跃段直接假设 $h_j=0$ 列能量方程求水深！"
    },
    {
        "id": "f-08-04",
        "chapter": 8,
        "name": "明渠闸门启闭四类非恒定涌波口诀",
        "latex": r"c_w = \pm \sqrt{gh} + v \quad (\text{微幅重力波速})",
        "variables": r"关小闸门：闸前逆行正波（涨水波）、闸后顺行负波（落水波）；开大闸门：闸前逆行负波（落水波）、闸后顺行正波（涨水波）。",
        "note": r"判断口诀：流量受阻水位涨（正波），流量泄空水位落（负波）；闸前向上游逆流传播（逆行），闸后向下游顺流传播（顺行）。"
    },
    # Chapter 9
    {
        "id": "f-09-01",
        "chapter": 9,
        "name": "平板闸孔出流与堰流界限及流量公式",
        "latex": r"Q_{\text{闸}} = \mu e b \sqrt{2gH_0} \;\left(\frac{e}{H} \le 0.65\right), \qquad Q_{\text{堰}} = \sigma_s \varepsilon m b \sqrt{2g}\,H_0^{3/2} \;\left(\frac{e}{H} > 0.65\right)",
        "variables": r"$e$ 为闸门开度；$H$ 为闸前水深；$\mu$ 为闸孔流量系数；$m$ 为堰流流量系数（薄壁堰约 $0.40\sim 0.42$，宽顶堰 $0.32\sim 0.385$）。",
        "note": r"孔流/闸孔出流流量与 $H_0^{1/2}$ 成正比；堰流表面自由跌落，流量与 $H_0^{3/2}$ 成正比！"
    },
    # Chapter 10
    {
        "id": "f-10-01",
        "chapter": 10,
        "name": "过堰/闸下急流底流消能与水跃衔接三种判据",
        "latex": r"\begin{cases} h_c^{\prime\prime} > h_t & \text{远驱式水跃（急流冲刷下游，必须设消能工！）} \\ h_c^{\prime\prime} = h_t & \text{临界式水跃（最理想衔接）} \\ h_c^{\prime\prime} < h_t & \text{淹没式水跃（无需额外加深消力池，但消能率下降）} \end{cases}",
        "variables": r"$h_c^{\prime\prime}$ 为收缩断面急流水深 $h_c^{\prime}$ 对应的跃后共轭水深；$h_t$ 为下游渠道天然尾水深。",
        "note": r"工程设计通常采用略微淹没的水跃（淹没系数 $\sigma_j = h_t / h_c^{\prime\prime} = 1.05 \sim 1.10$）以保证水跃稳定在消力池内。"
    },
    # Chapter 11
    {
        "id": "f-11-01",
        "chapter": 11,
        "name": "达西渗流定律与正交渗流流网单宽渗流量",
        "latex": r"v = k J = n_e u, \qquad q = k H \frac{N_f}{N_d} = k (h_1 - h_2)\frac{n_s - 1}{n_e - 1}",
        "variables": r"$v = Q/A$ 为断面假想渗流流速；$u$ 为孔隙实际平均流速（因孔隙度 $n_e < 1$，恒有 $v < u$）；$N_f$ 为流槽数；$N_d$ 为等势段数。",
        "note": r"达西定律仅适用于线性层流渗流（$Re \le 1\sim 10$）；流网计算切记将“流线条数 $n_s$、等势线条数 $n_e$”各自减 $1$ 化为区间段数！"
    },
    # Chapter 13
    {
        "id": "f-13-01",
        "chapter": 13,
        "name": "重力相似（弗劳德准则）常用物理量比尺速查表",
        "latex": r"\lambda_v = \lambda_L^{1/2}, \quad \lambda_t = \lambda_L^{1/2}, \quad \lambda_Q = \lambda_L^{5/2}, \quad \lambda_F = \lambda_\rho \lambda_L^3, \quad \lambda_n = \lambda_L^{1/6}",
        "variables": r"比尺定义 $\lambda_X = X_p / X_m$（原型比模型）。当模型与原型均用水（$\lambda_\rho = 1, \lambda_g = 1$）且为正态模型时适用。",
        "note": r"堰流、明渠流、溢洪道、波浪等自由水面重力主导流动均采用弗劳德准则；有压密闭管流黏性阻力主导则采用雷诺准则（$\lambda_v = \lambda_L^{-1}, \lambda_Q = \lambda_L$）。"
    }
]


def main():
    OUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DATA_DIR / "chapters.json").write_text(
        json.dumps(CHAPTERS_DATA, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT_DATA_DIR / "formulas.json").write_text(
        json.dumps({"formulas": FORMULAS_DATA}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"SUCCESS: Wrote {len(CHAPTERS_DATA['chapters'])} chapters and {len(FORMULAS_DATA)} core formulas.")


if __name__ == "__main__":
    main()
