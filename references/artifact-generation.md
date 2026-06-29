# 交付物生成

## 默认策略

默认生成 HTML，因为它最容易做到审美在线、可预览、可打印 PDF。用户要求 Word 或 PDF 时再生成对应文件。

如果本地没有生成 PDF 的能力，保留 HTML，并告诉用户可以用浏览器打开后打印为 PDF。不要假装已经生成 PDF。

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

## 调用方式

```bash
python3 scripts/render_resume_artifacts.py resume-data.json --out-dir ./outputs --formats html,docx
```

`pdf` 会依次尝试 `weasyprint`、`wkhtmltopdf`、`reportlab`。在 Codex 环境中优先使用 workspace bundled Python 运行脚本，保证 `python-docx`、`reportlab`、`pypdf` 可用。都不可用时不会生成假 PDF。

## 命名

输出文件名优先使用：`姓名-目标岗位-简历.html`。姓名或岗位缺失时，用：`毕业生岗位定制简历.html`。

## 一致性交付门槛

HTML、DOCX、PDF 必须从同一个 `resume-data.json` 用同一条命令生成，不要手写其中一种格式后单独交付。推荐：

```bash
python3 scripts/render_resume_artifacts.py resume-data.json --out-dir ./outputs --formats html,docx,pdf
python3 scripts/verify_resume_artifacts.py resume-data.json --out-dir ./outputs
```

交付前必须确认：

- 三个文件时间接近，避免新旧版本混放。
- `verify_resume_artifacts.py` 通过：关键字段、摘要、章节、条目、标签都存在。
- 三版均无内部词：`求职说明`、`投递关键词`、`匹配策略`、`匹配：`、`JD 反推`、`ATS`、`缺口分析`、`CONTACT`。
- PDF 渲染为 1 页 A4 且中文正常；DOCX 至少用 `render_docx.py` 或 macOS Quick Look 预览检查。

## 复盘固化原则

这次失败的根因是三种格式分裂生成：HTML、DOCX、PDF 分别走不同临时逻辑，导致文案、视觉和时间戳漂移。通用化后必须遵守：

- Single source of truth：只改 `resume-data.json`，不要直接改某个格式里的正文。
- Single render command：多格式交付用同一次 `render_resume_artifacts.py --formats html,docx,pdf`。
- Single quality gate：交付前运行 `verify_resume_artifacts.py`，并检查 PDF/DOCX 视觉预览。
- No fake fallback：无法生成 PDF/DOCX 时只交付已真实生成的格式，并说明原因；不要留下“生成说明.txt”冒充交付物。
- No internal vocabulary：`CONTACT`、`匹配策略`、`投递关键词`、`匹配：` 等内部词一律视为交付失败。

推荐在 Codex 桌面环境中使用 workspace bundled Python 运行脚本，因为其中通常包含 `python-docx`、`reportlab`、`pypdf`：

```bash
/Users/chuanfan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/render_resume_artifacts.py resume-data.json --out-dir ./outputs --formats html,docx,pdf
/Users/chuanfan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/verify_resume_artifacts.py resume-data.json --out-dir ./outputs
```
