# 交付物生成

## 默认策略

默认生成 HTML + PDF，因为 HTML 最容易做到审美在线、可预览，PDF 最适合打印和直接投递。用户明确要求可编辑版本时再生成 Word。

PDF 必须优先从 HTML 打印/渲染得到。若本地没有高质量 PDF 生成能力，保留 HTML，并告诉用户可以用浏览器打开后打印为 PDF。不要用低质手工重画 PDF 冒充交付物。

Word 的定位是可编辑内容版，不是视觉母版。不要承诺 Word 与 HTML/PDF 完全一致；不要用复杂侧栏、嵌套表格、绝对定位去仿网页简历，这类文件在 Word/WPS/Pages 之间极易变形。

## 结构化 JSON

`scripts/render_resume_artifacts.py` 接受 `design_brief`。没有提供时，脚本会回退到 `top-card` 基础版式；正式交付前应由 agent 根据 JD 和用户经历生成 `design_brief`。

```json
{
  "basics": {
    "name": "张三",
    "title": "产品运营实习生",
    "phone": "13800000000",
    "email": "zhangsan@example.com",
    "location": "上海",
    "links": ["作品集：https://example.com"],
    "photo": "/absolute/path/to/photo.jpg"
  },
  "target": {
    "role": "产品运营实习生",
    "company": "某某公司",
    "industry": "互联网"
  },
  "design_brief": {
    "tone": "清爽、数据感、校招友好",
    "layout": "sidebar-card",
    "palette": {
      "primary": "#1d4ed8",
      "accent": "#38bdf8",
      "soft": "#eff6ff",
      "paper": "#ffffff"
    },
    "photo": { "mode": "use_if_provided", "use_if_provided": true },
    "density": "content-light",
    "print_scale": 1,
    "module_order": ["header", "profile", "summary_cards", "education", "competency", "certificates"],
    "avoid": ["求职说明", "投递关键词", "匹配策略"]
  },
  "summary": ["一句证据型优势", "另一句证据型优势"],
  "sections": [],
  "keywords": ["用户调研", "活动执行", "数据整理"]
}
```

## layout 可选值

- `sidebar-card`：左侧信息栏 + 右侧正文，适合门店、销售、服务、运营、管培、经历较少。
- `top-card`：顶部名片 + 单栏正文，适合稳重岗位、ATS 友好、经历较完整。
- `timeline`：时间线经历，适合项目/实习丰富。
- `portfolio-light`：作品导向，适合设计、内容、品牌、新媒体。
- `technical-grid`：技能矩阵 + 项目块，适合研发、数据、工程、产品。

## print_scale

`design_brief.print_scale` 只影响打印/PDF，不影响屏幕 HTML。默认 `1`。当简历只有少量尾巴溢出到第二页时，可设置为 `0.82` 到 `0.92` 压回一页；不要低于 `0.8`，否则可读性会明显下降。内容本身确实丰富时，不要靠过度缩放硬塞一页，应删减内容或接受两页。

## 调用方式

```bash
python3 scripts/render_resume_artifacts.py resume-data.json --out-dir ./outputs --formats html,pdf
```

`pdf` 会优先尝试本机 Chrome 无界面打印 HTML，然后再回退到 `weasyprint`、`wkhtmltopdf`、`reportlab`。在 Codex 环境中优先使用 workspace bundled Python 运行脚本，保证 `python-docx`、`reportlab`、`pypdf` 可用。都不可用时不会生成假 PDF。

## 命名

输出文件名优先使用：`姓名-目标岗位-简历.html`。姓名或岗位缺失时，用：`毕业生岗位定制简历.html`。

## 一致性交付门槛

HTML、DOCX、PDF 必须从同一个 `resume-data.json` 用同一条命令生成，不要手写其中一种格式后单独交付。推荐：

```bash
python3 scripts/render_resume_artifacts.py resume-data.json --out-dir ./outputs --formats html,pdf
python3 scripts/verify_resume_artifacts.py resume-data.json --out-dir ./outputs --formats html,pdf
```

交付前必须确认：

- 三个文件时间接近，避免新旧版本混放。
- `verify_resume_artifacts.py` 通过：HTML/DOCX 的关键字段、摘要、章节、条目、标签都存在；PDF 至少页数正常、基础身份字段可读，并完成视觉预览。
- 三版均无内部词：`求职说明`、`投递关键词`、`匹配策略`、`匹配：`、`JD 反推`、`ATS`、`缺口分析`、`CONTACT`。
- PDF 渲染为 A4 且中文正常，优先一页，内容丰富时允许两页但不能出现大段空白或断裂；DOCX 只作为可编辑版，至少用 `render_docx.py` 或 macOS Quick Look 预览检查。

## 复盘固化原则

这次失败的根因是三种格式分裂生成：HTML、DOCX、PDF 分别走不同临时逻辑，导致文案、视觉和时间戳漂移。通用化后必须遵守：

- Single source of truth：只改 `resume-data.json`，不要直接改某个格式里的正文。
- Single render command：多格式交付用同一次 `render_resume_artifacts.py --formats html,pdf`；用户明确要 Word 时再使用 `html,pdf,docx`。
- Single quality gate：交付前运行 `verify_resume_artifacts.py`，并检查 PDF/DOCX 视觉预览。
- No fake fallback：无法生成高质量 PDF 时只交付 HTML，并说明原因；Word 如果观感不达标，只能标为可编辑版或不交付，不要把它说成精美简历。
- No internal vocabulary：`CONTACT`、`匹配策略`、`投递关键词`、`匹配：` 等内部词一律视为交付失败。

推荐在 Codex 桌面环境中使用 workspace bundled Python 运行脚本，因为其中通常包含 `python-docx`、`reportlab`、`pypdf`：

```bash
/Users/chuanfan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/render_resume_artifacts.py resume-data.json --out-dir ./outputs --formats html,pdf
/Users/chuanfan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/verify_resume_artifacts.py resume-data.json --out-dir ./outputs --formats html,pdf
```
