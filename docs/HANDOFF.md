# 项目交接文档（HANDOFF）

> **更新时间**：2026-11-21（全部 31 套真题上线）  
> **新会话 AI 指引**：接手本项目时，请先阅读本文档，再按任务类型查阅同目录下的 `01_真题精解数据包生成说明书(供AI使用).md` 或 `02_试卷与新板块导入说明书(供AI使用).md`。

---

## 一、项目概况与技术栈

- **站点名称**：鲸研专业课（品牌配置集中于 `web/src/brand.ts`）
- **定位**：对标“数砖”正交刷题体验的多院校、多专业课考研复习纯静态 PWA 网站（支持按年整卷、按考纲章节、按解题方法、逐题刷题、180 分钟全真模考+步骤采分点自评、错题本/收藏夹/笔记墙、掌握热力图、命题结构大盘、核心公式闪卡背诵）。
- **技术栈**：`Vite 6 + React 19 + TypeScript + React Router (HashRouter) + KaTeX`；无后端，学习进度按 `courseId` 隔离存储于浏览器 `localStorage`（支持全量 JSON 导入/导出备份）。
- **视觉与看板娘**：深海/浅海双主题毛玻璃风格；看板娘采用二头身 Q 版“蓝色大肥鱼”四姿态透明 WebP（`web/public/mascot/{hero,think,cheer,study}.webp`），并在「关于本站 → 角色图鉴」额外展示特别鸣谢角色 **Gemini** 定制立绘（`web/public/mascot/gemini.webp`）；`assets_src/mascot_raw/_original_v1/` 下保留有一套纯原创“小鲸”备用立绘。
- **联系与互动功能**：站长邮箱 `amassss321@gmail.com`、考研交流 QQ 群 `1058675261`，内置公告栏（`web/public/data/announcements.json`）、考研留言板（`/board`，本地存储+邮件投稿）及角色图鉴（`/about?section=codex`）。

---

## 二、当前各板块与本地资料状态盘点

| 板块 ID | 板块名称 | 当前线上状态 | 仓库内待处理原始资料位置 |
| :--- | :--- | :--- | :--- |
| `hhu-814` | **河海大学 · 814 水力学** | **已上线 2013～2026 共 14 套真题**（433 题 / 2100 分，274 幅 WebP 配图，全部通过 KaTeX 校验） | 无待导入年份（2013～2021 九套 `.docx` 已全部转换，标准包归档于 `河海大学已整理数据/<year>/`） |
| `yzu-849` | **扬州大学 · 849 水力学** | **已上线 2007～2008、2010～2024 共 17 套真题**（290 题 / 2550 分，205 幅 WebP 高清原图与解析图，含 10 章考纲与 32 组核心公式库；2009 年无试卷） | 无待导入年份；标准包归档于 `扬州大学已整理数据/<year>/`。参考资料：`扬州大学待处理数据/简答题Ⅰ~Ⅲ.pdf`、`水力学真题/*.jpg`、`真题答案/IMG_*.JPG`（仅作验算参照，含第三方水印，严禁直接引用） |

---

## 三、核心目录与关键文件索引

```text
c:\Users\6\Desktop\水力学\
├── .gitignore                                      # 发布隔离规则（屏蔽原始含水印真题、docx 与备份资产）
├── docs/
│   ├── HANDOFF.md                                  # 本交接文档
│   ├── 00_工作流设计与全局避坑思考.md               # 架构决策与 7 大跨专业课避坑说明
│   ├── 01_真题精解数据包生成说明书(供AI使用).md     # PDF/图片 -> 标准 <year>.json + figures/ 规范
│   ├── 02_试卷与新板块导入说明书(供AI使用).md       # 一键入库与新增专业课板块 SOP
│   └── 03_手绘原题图片重绘加速工作指南.md          # 轻量高保真工程简图重绘规范（含 4 项不变量、1600px QA 与 5 题翻车复盘）
├── scripts/
│   ├── fig_kit.py                                  # 工程示意图复用图元库（水面/剖面/压差计/质检拼图）
│   ├── redraw_hhu_handdrawn.py                     # 河海 814（2017/2018/2022）35 幅手绘原题图批量重绘脚本
│   ├── redraw_hhu_2025.py                          # 河海 814（2025）12 幅原题图去水印替换重绘脚本
│   ├── ingest_exam.py                              # 【主力入库脚本】标准真题包转 WebP + 写入 + 自动校验
│   ├── validate_course.mjs                         # 【必跑门禁】全板块 Schema/分值/采分点/图片/KaTeX 零错校验器
│   ├── build_yzu_2024.py                           # 扬大 849 2024 真题包与 Matplotlib 解析图生成脚本
│   ├── build_yzu_22_23.py / _20_21 / _18_19 / _16_17 / _14_15 / _12_13 / _10_11 / _07_08.py  # 扬大 849 2007～2023 各年真题包生成脚本（含 Matplotlib 解析图）
│   ├── parse_2023.py / parse_2022.py               # 河海 814 2022-2023 docx 解析与标准包生成脚本
│   ├── parse_2026.py / parse_2024_2025.py          # 河海 24-26 docx 历史导入脚本
│   ├── parse_hhu_19_21.py / parse_hhu_16_18.py / parse_hhu_13_15.py  # 河海 814 2013～2021 docx 解析与标准包生成脚本
│   ├── init_courses.py                             # 多板块目录与扬大 849 初始化脚本
│   └── build_mascot.py                             # 看板娘与 Gemini 立绘白底抠图转透明 WebP 脚本
└── web/
    ├── public/
    │   ├── data/
    │   │   ├── courses.json                        # 顶部左上角「板块切换器」总目录
    │   │   ├── announcements.json                  # 站点公告数据源
    │   │   ├── guestbook.json                      # 留言板预置置顶欢迎数据源
    │   │   ├── hhu-814/                            # 河海 814 题库、章节、公式与图片
    │   │   └── yzu-849/                            # 扬大 849 题库、章节、公式与图片
    │   ├── mascot/                                 # 看板娘（hero/think/cheer/study）与 Gemini 角色立绘 WebP
    │   └── sw.js                                   # PWA 离线缓存 Service Worker（当前 jingyan-multi-v15）
    └── src/
        ├── brand.ts                                # 站名、联系邮箱、QQ 群及留言 API 扩展配置
        ├── types.ts                                # 8 种通用题型、公告与留言类型定义
        ├── context/DataContext.tsx                 # 多板块动态数据与公告加载管理
        ├── context/StudyContext.tsx                # 按 courseId 分仓隔离的本地学习记录管理
        └── pages/                                  # Home, Year, Chapters, Methods, Practice, Mock, WrongBook, Progress, Dashboard, Formulas, Board, About
```

---

## 四、常用开发与运维命令速查

在项目根目录 `c:\Users\6\Desktop\水力学` 下执行：

```powershell
# 1. 启动本地开发预览服务器（默认 http://localhost:5173/）
Set-Location web; npm run dev

# 2. 将生成的标准真题包一键导入指定板块（自动转 WebP + 更新索引 + 跑 KaTeX 校验）
python scripts/ingest_exam.py --course yzu-849 --json "扬州大学已整理数据/2024/2024.json" --figures "扬州大学已整理数据/2024/figures"

# 3. 单独运行全站全板块数据完整性与 KaTeX 零错校验（当前 16485 处公式 0 错误，共 31 套试卷（河海 14 + 扬大 17）全部通过）
node scripts/validate_course.mjs

# 4. TypeScript 严格检查与生产静态包构建（输出至 web/dist/）
Set-Location web; npm run build
```

---

## 五、后续会话待办事项（Next Steps）

> 截至 2026-11-21：河海 814（2013～2026，14 套）与扬大 849（2007～2008、2010～2024，17 套）已全部上线；`node scripts/validate_course.mjs` 全站 **Total errors: 0**（16485 处公式）；`npm run build` 通过；河海 2017/2018/2022 共 35 幅手绘原题图已通过 `scripts/redraw_hhu_handdrawn.py` 重绘并复核修正了 5 幅偏差题（`18.10`、`17.9`、`17.10`、`17.11`、`17.15`），河海 2025 全部 12 幅去水印原题图已通过 `scripts/redraw_hhu_2025.py` 重绘并完成 7 题定向精修（原图均已备份于 `assets_src/handdrawn_backup/`），河海 2026（8 幅）已核实原本即为矢量简图，其余河海 2013–2023（87 幅）与扬大真题卷原图均为清晰黑白印刷原图无需重绘；阶段 0 前端合规整改（首页主标题指示性降权、大肥鱼 CC BY-NC-SA 4.0 完整外链与修改声明、Gemini 方案 B 非商业说明、48 小时权利响应、刷题/整卷/模考区 AI 显式标识）、多院校元信息（`index.html` / `manifest.webmanifest`）、根目录 `.gitignore` 发布隔离、联系方式（`amassss321@gmail.com` / QQ 群 `1058675261`）、公告栏、留言板与角色图鉴均已就绪（`sw.js` 已升级至 `jingyan-multi-v15`），当前已达到可直接部署 `web/dist/` 公网发布状态。

1. **接入更多考研专业课板块**：
   - 按 `docs/02_试卷与新板块导入说明书(供AI使用).md` 场景 B，在 `courses.json` 注册新科目并建立对应 `<courseId>/` 三件套。
2. **题库与重绘质量持续打磨（可选）**：
   - 后续新增或重绘任何题图时，严格遵循 `docs/03_手绘原题图片重绘加速工作指南.md` 的「动笔前 4 项不变量 + 1600px 无损 QA 对照」；个别解析图可继续精修（例如扬大 2021 第 9 题 `q09_sol` 的 1/4 圆弧目前绘为近似椭圆）。
3. **公开发布前的合规与多端扩展（如未来部署公网）**：
   - 将题库中提取自原卷/第三方资料的其余配图逐步替换为 Python/SVG 自绘矢量工程图；若涉及商业用途，将看板娘与 Gemini 立绘切换为纯原创素材；
   - 如需将留言板从本地存储升级为多人实时同步，可在 `web/src/brand.ts` 的 `guestbookApiUrl` 接入轻量后端（如 Cloudflare Workers + D1）。
