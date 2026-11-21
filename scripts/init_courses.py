# -*- coding: utf-8 -*-
"""
Initialize multi-course directory structure under `web/public/data/`:
- `courses.json`: master catalog of exam courses (河海 814 水力学, 扬大 849 水力学, extensible to any考研专业课)
- `hhu-814/`: normalize relative asset paths
- `yzu-849/`: initialize chapters, core formulas (including centrifugal pump & N-S equations), and 2007-2024 index
"""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = ROOT / "web" / "public" / "data"
HHU_DIR = DATA_ROOT / "hhu-814"
YZU_DIR = DATA_ROOT / "yzu-849"


def normalize_hhu_paths():
    for yr in (2024, 2025, 2026):
        fp = HHU_DIR / f"{yr}.json"
        if not fp.exists():
            continue
        txt = fp.read_text(encoding="utf-8")
        txt = txt.replace('"data/figures/', '"figures/')
        fp.write_text(txt, encoding="utf-8")

    idx_fp = HHU_DIR / "index.json"
    if idx_fp.exists():
        idx = json.loads(idx_fp.read_text(encoding="utf-8"))
        for item in idx.get("availableYears", []):
            item["dataFile"] = item["dataFile"].replace("data/", "")
        # Also list 2013-2022 available in 河海大学已整理真题 as planned
        existing_years = {x["year"] for x in idx["availableYears"]}
        for y in range(2022, 2012, -1):
            if y not in existing_years:
                idx["availableYears"].append({
                    "year": y,
                    "title": f"{y} 年河海大学 814 水力学考研真题",
                    "questionCount": 30,
                    "totalScore": 150,
                    "figureCount": 0,
                    "status": "planned",
                    "dataFile": f"{y}.json",
                })
        idx_fp.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")


def init_yzu_849():
    YZU_DIR.mkdir(parents=True, exist_ok=True)
    (YZU_DIR / "figures").mkdir(parents=True, exist_ok=True)

    # Copy base formulas from HHU-814 and add YZU-849 signature formulas (Centrifugal Pump & N-S Equations!)
    hhu_formulas = json.loads((HHU_DIR / "formulas.json").read_text(encoding="utf-8"))["formulas"]
    yzu_extra_formulas = [
        {
            "id": "f-yzu-pump",
            "chapter": 6,
            "name": "水泵最大允许安装高程与水泵装置总扬程、轴功率",
            "latex": r"\nabla_{\max} = \nabla_1 + h_v - \left(\frac{\alpha v_s^2}{2g} + h_{w,s}\right), \quad H_p = \Delta Z + \sum h_w, \quad N_{\text{轴}} = \frac{\rho g Q H_p}{\eta}",
            "variables": r"$\nabla_1$ 为吸水池水面高程；$h_v$ 为水泵允许真空高度；$h_{w,s}$ 为吸水管水头损失；$H_p$ 为水泵总扬程；$\eta$ 为水泵效率。",
            "note": r"扬大 849 高频 20 分压轴大题！注意动力机输出功率单位换算（$\mathrm{W} \leftrightarrow \mathrm{kW}$）及铸铁长管采用曼宁公式求摩阻。"
        },
        {
            "id": "f-yzu-ns",
            "chapter": 5,
            "name": "不可压缩黏性流体纳维—斯托克斯（N-S）方程与平行平板层流",
            "latex": r"\frac{\mathrm{d}\vec{u}}{\mathrm{d}t} = \vec{f} - \frac{1}{\rho}\nabla p + \nu \nabla^2 \vec{u}, \qquad \frac{\mathrm{d}^2 u}{\mathrm{d}y^2} = \frac{1}{\mu}\frac{\mathrm{d}p}{\mathrm{d}x}",
            "variables": r"对水平平行平板恒定层流（上板速度 $U$、下板静止、间距 $h$）：$u(y) = \frac{U}{h}y - \frac{1}{2\mu}\frac{\mathrm{d}p}{\mathrm{d}x}y(h-y)$。",
            "note": r"扬大 849 常考 N-S 方程简化推导：先列出恒定、二维、充分发展层流（$u_y=0, \partial u/\partial x=0$）条件消去非线性惯性项，再两次积分代入边界条件求流速与单宽流量 $q = \int_0^h u\,\mathrm{d}y$。"
        },
    ]
    (YZU_DIR / "formulas.json").write_text(
        json.dumps({"formulas": hhu_formulas + yzu_extra_formulas}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    yzu_chapters = {
        "syllabusTitle": "扬州大学 849 水力学（水）章节体系与命题特征",
        "textbook": "参考教材：《水力学》，主流工科水力学通用教材（以当年扬州大学研究生院公布目录为准）",
        "highlights": [
            "题型鲜明：近年试卷多由 11 道大题构成（前 5 题为 10 分机理简答/定性分析/实验设计，后 6 题为 15～20 分综合计算与推导）。",
            "特色必考板块：除静水压力、动量方程、管流外，重点考查「离心泵允许安装高程与功率」及「N-S 方程推导层流流速分布」！",
            "定性分析比重大（约 50 分）：要求熟练解释切应力分布、分叉管改建流量变化、绕流压差阻力、明渠均匀流特征等物理本质。",
        ],
        "omittedChapterNote": "当前扬大 849 板块已完成框架与考纲公式初始化，待按《生成说明书》转换 PDF 真题后一键导入。",
        "chapters": [
            {"chapter": 1, "name": "绪论与液流切应力", "fullTitle": "第一章：绪论与液流切应力", "questionTypes": "10 分定性分析题", "scoreRange": [10, 15], "scoreLabel": "10-15", "stars": 2, "hasBigQuestion": True, "summary": "考查平板间流速分布与微元水体上下表面切应力方向及大小判别、液体物理性质。", "coreKps": ["牛顿内摩擦定律", "微元水体切应力方向"]},
            {"chapter": 2, "name": "水静力学与浮力稳定", "fullTitle": "第二章：水静力学与浮力稳定", "questionTypes": "15 分计算题（常出 2 题）", "scoreRange": [25, 35], "scoreLabel": "25-35", "stars": 3, "hasBigQuestion": True, "summary": "多液层活塞加压 U 形水银计计算、自动泄水阀圆柱/圆球浮标阿基米德浮力与静水压力平衡设计、平面与曲面总压力。", "coreKps": ["多液层压差计", "浮力与自动泄水阀设计", "平面与曲面静水总压力"]},
            {"chapter": 3, "name": "恒定总流三大方程", "fullTitle": "第三章：恒定总流三大方程", "questionTypes": "10 分实验设计 + 15 分计算题", "scoreRange": [25, 35], "scoreLabel": "25-35", "stars": 3, "hasBigQuestion": True, "summary": "恒定流发生装置设计（溢流保持水位恒定）、阀门启闭前后压力表读数求管内流速、平板闸门/弯管动水总压力（能量+动量方程）。", "coreKps": ["恒定流装置设计", "伯努利方程测流", "闸门与弯管动水总压力"]},
            {"chapter": 4, "name": "流动阻力、绕流与边界层", "fullTitle": "第四章：流动阻力、绕流与边界层", "questionTypes": "10 分机理分析题", "scoreRange": [10, 15], "scoreLabel": "10-15", "stars": 2, "hasBigQuestion": True, "summary": "平行来流与垂直来流平板摩擦阻力 vs 边界层分离压差阻力对比分析、沿程与局部水头损失。", "coreKps": ["摩擦阻力与压差阻力", "边界层分离", "沿程与局部损失"]},
            {"chapter": 5, "name": "有压管流与水泵水力计算", "fullTitle": "第五章：有压管流与水泵水力计算", "questionTypes": "10 分管网分析 + 20 分水泵大题", "scoreRange": [25, 35], "scoreLabel": "25-35", "stars": 3, "hasBigQuestion": True, "summary": "分叉管路加接支管/延长管后各支路流量增减定性分析；离心泵最大允许安装高程（允许真空度校核）、长管扬程与动力机功率计算。", "coreKps": ["分叉管改装流量变化分析", "水泵最大允许安装高程", "水泵扬程与轴功率"]},
            {"chapter": 6, "name": "明渠流、堰闸与渗流", "fullTitle": "第六章：明渠流、堰闸与渗流", "questionTypes": "10 分简答 + 15 分计算题", "scoreRange": [15, 25], "scoreLabel": "15-25", "stars": 2, "hasBigQuestion": True, "summary": "明渠均匀流形成条件与天然河道非均匀性分析、水面曲线定性分析、堰流与闸孔出流、达西渗流。", "coreKps": ["明渠均匀流特点", "水面曲线分析", "堰闸出流与渗流"]},
            {"chapter": 7, "name": "N-S 方程与黏性层流解析解", "fullTitle": "第七章：N-S 方程与黏性层流解析解", "questionTitle": "", "questionTypes": "20 分压轴推导题", "scoreRange": [15, 20], "scoreLabel": "15-20", "stars": 3, "hasBigQuestion": True, "summary": "应用不可压缩黏性流体纳维—斯托克斯（N-S）微分方程推导平行平板库埃特—泊肃叶混合层流流速分布与单宽流量公式。", "coreKps": ["纳维-斯托克斯(N-S)方程", "平板槽道层流流速推导", "流函数与势函数"]},
        ],
    }
    (YZU_DIR / "chapters.json").write_text(json.dumps(yzu_chapters, ensure_ascii=False, indent=2), encoding="utf-8")

    # Populate index.json from PDFs in 扬州大学待处理数据
    years_found = [2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2008, 2007]
    yzu_index = {
        "availableYears": [
            {
                "year": y,
                "title": f"{y} 年扬州大学 849 水力学（水）考研真题",
                "questionCount": 11 if y >= 2020 else 12,
                "totalScore": 150,
                "figureCount": 0,
                "status": "planned",
                "dataFile": f"{y}.json",
            }
            for y in years_found
        ]
    }
    (YZU_DIR / "index.json").write_text(json.dumps(yzu_index, ensure_ascii=False, indent=2), encoding="utf-8")


def write_courses_catalog():
    catalog = {
        "defaultCourseId": "hhu-814",
        "courses": [
            {
                "id": "hhu-814",
                "name": "河海大学 · 814 水力学",
                "shortLabel": "河海 814",
                "school": "河海大学",
                "code": "814",
                "subject": "水力学",
                "category": "水利 / 土木考研专业课",
                "examMetaBadge": "科目代码 814 · 闭卷 · 禁用计算器",
                "status": "ready",
                "description": "已上线 2024–2026 近三年共 90 道真题精解，另有 2013–2022 十年真题待按需导入。",
            },
            {
                "id": "yzu-849",
                "name": "扬州大学 · 849 水力学",
                "shortLabel": "扬大 849",
                "school": "扬州大学",
                "code": "849",
                "subject": "水力学（水）",
                "category": "水利 / 土木考研专业课",
                "examMetaBadge": "科目代码 849 · 满分 150 分 · 闭卷",
                "status": "preparing",
                "description": "已完成考纲章节与水泵/N-S方程核心公式库初始化，待将 2007–2024 原始试卷生成标准包后导入。",
            },
        ],
    }
    (DATA_ROOT / "courses.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    normalize_hhu_paths()
    init_yzu_849()
    write_courses_catalog()
    print("SUCCESS: Multi-course catalog (hhu-814 & yzu-849) initialized!")
