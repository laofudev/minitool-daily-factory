---
name: minitool-daily-factory
description: >-
  Minitool 云端每日批量生产 skill：被每日定时任务（凌晨 0 点后）唤醒时，一次性产出 10 个
  不重复的离线工具 zip 包，按日期目录归档，每个包必须通过全部校验与测试才可交付。
  触发词：「每日工具」「做10个工具」「minitool每日批量」「批量做工具」「daily tools」。
  也用于：单补一个工具、排查批量生产失败、维护防重复档案。
metadata:
  version: "1.0.0"
---

# Minitool 每日工具工厂（云端批量版）

**Minitool 是一个纯静态英文工具站**（https://minitool.io，零后端零构建，HTML5+CSS3+经典 JS）。
本 skill 用于**云端定时批量生产**：每天凌晨 0 点后被调度器唤醒一次，产出 **10 个全新、互不重复、互不克隆**的工具 zip 包，按日期归档，等待统一上线。

目标产物：`output/<YYYY-MM-DD>/` 目录下 10 个通过全部校验与测试的 `*.zip` + 一份 `report.md`。

## 何时使用

- 每日定时任务触发（凌晨 0 点后）：批量生产 10 个工具
- 用户手动要求补做工具（「再做一个」「补两个」）
- 排查校验 / 测试失败，维护防重复档案

## 硬性规则（每条都必须遵守）

1. **不重复**：新工具的 `file` slug 和功能都不得与「已存在清单」重复（查重流程见下）。宁可做冷门方向，也不克隆已有工具。
2. **10 个一批**：每次定时运行必须产出恰好 10 个。因失败不足 10 个时，补足再做，report.md 里如实记录失败原因。
3. **质量门禁**：每个 zip 必须通过 `scripts/validate_tool.py` 全部检查（退出码 0），并通过下方「测试要求」。任何一项不过 = 不交付、不计入 10 个。
4. **按日期归档**：产出写入 `output/<当天日期 YYYY-MM-DD>/`，目录下同时写 `report.md`。
5. **全英文 UI**：按钮、占位符、提示、报错全部英文，语气简短直接。
6. **零外部依赖**：任何 `http(s)://` 资源引用（CDN/字体/图片/统计）一律禁止；纯前端零后端。

## 每日工作流程

### 第 0 步：查重（必做，开工前）

1. 读 [existing-tools.md](existing-tools.md) 防重复档案（权威清单）
2. 用 `curl -s "https://minitool.io/?cachebust=$(date +%s)"` 抓站点原始 HTML，grep `tools/` 链接核对最新 slug 列表
   - **禁止**用 FetchURL/网页摘要类工具核对——会拿到 CDN 缓存的旧页面（本站实测踩过此坑）
3. 两者取并集 = 「已存在清单」。今日 10 个工具的 slug 与功能均不得与之重复

### 第 1 步：选题（10 个）

- 从「已存在清单」之外选 10 个有真实搜索需求、纯前端可实现的方向
- **分类均衡**：尽量覆盖 `text-tools` / `developer-tools` / `calculators`，同一批内同分类不超过 5 个
- 先列出 10 个 `file` slug，逐一与已存在清单比对，全部通过再动手

### 第 2 步：逐个开发

动手前先读 [references/tool-package-spec.md](references/tool-package-spec.md) 并**严格遵守全部约束**（zip 结构、脚本外置、经典脚本、manifest 9 字段、UI 规范、复制契约），再读 [references/seo-page-template.md](references/seo-page-template.md) 确认 manifest 文案的最终落地位置。写完对照其 §5/§7 自检清单逐条打勾。

### 第 3 步：逐个质量门禁

每个工具必须全部通过：

1. **结构校验（硬性）**：`python3 scripts/validate_tool.py <tool.zip>` 退出码 0。其中已新增内容质量检查：`toolPurpose` 禁止模板填充句；推荐提供 `useCases`（3–4 条）和 `audience`。
2. **JS 语法检查**：`node --check app.js`（及包内每个 .js）零错误
3. **静态走查**：无内联脚本/行内事件、无 import/export、资源引用齐全、事件绑定闭环、DOM 引用存在、核心逻辑自洽
4. **内容去重**：同一批 10 个工具的 `useCases` / `audience` / `toolPurpose` 不能完全相同；`How to Use` 步骤不能整段复制其他工具。若发现 3 条以上通用文案重复，本批全部重写。
5. **已知答案测试向量**：对有确定性的逻辑（哈希/编码/转换/计算）在测试中用已验证的标准答案核对（可用 Node/Python 标准库生成参考值）
6. **浏览器实测（环境允许时）**：若环境提供浏览器自动化，必须真实打开页面、模拟点击、断言输出；无浏览器环境时在 report.md 中对该工具标注 `未浏览器实测`，其余测试项不能省略

### 第 4 步：归档 + 报告

- 每个 zip 放入 `output/<YYYY-MM-DD>/`
- 全部完成后写 `output/<YYYY-MM-DD>/report.md`：日期、10 个工具（slug/分类/测试结果/是否浏览器实测）、失败与重试记录
- 把 10 个新工具追加到 [existing-tools.md](existing-tools.md)（日期 / 工具名 / slug / 分类）

### 第 5 步：自动上线（可选，默认关闭）

若环境变量 `MINITOOL_SITE_REPO` 配置了站点仓库地址（如 `git@github.com:laofudev/minitool.git`），则自动推送到 `incoming/` 触发 CI 集成：

1. clone（或复用缓存克隆）`$MINITOOL_SITE_REPO`
2. 把当日 `output/<date>/*.zip` 复制进仓库 `incoming/`（新工具用 `<file>.zip`；更新已有工具才用 `<file>-update.zip`）
3. `git add incoming/ && git commit -m "daily tools: <date>" && git push`
4. CI 自动校验并集成每个 zip；失败的 zip 留在 `incoming/` 并生成 `FAILED-<name>.log`，需修复后重推
5. push 后 curl 核对站点已出现新 slug，再把 [existing-tools.md](existing-tools.md) 的"待上线"状态改为"已上线"并提交本 skill 仓库

**前提**：环境具备 git 与该仓库写权限（deploy key 或 PAT）；只有 10 个 zip 全部通过质量门禁才允许 push；任一 zip 未过门禁则整批不推，先修。

## 输出目录结构

```
output/
└── 2026-09-09/
    ├── 01-slug-one.zip
    ├── ...
    ├── 10-slug-ten.zip
    └── report.md
```

（序号前缀仅为阅读顺序，zip 内部结构与序号无关）

## 禁止事项

- 禁止交付未通过 validate 的 zip
- 禁止重复已存在工具（换皮、改名、微调参数都算重复）
- 禁止在 zip 内引用本 skill 之外的文件（包必须完全自包含）
- 禁止省略 report.md 或虚报测试结果

## Reference 与脚本

| 文件 | 用途 |
| --- | --- |
| [references/tool-package-spec.md](references/tool-package-spec.md) | zip 结构、manifest 契约、UI 规范、打包自检清单 |
| [references/seo-page-template.md](references/seo-page-template.md) | SEO 页模板、manifest 字段落地位置 |
| [scripts/validate_tool.py](scripts/validate_tool.py) | 校验脚本（仅标准库，自包含），`--fix` 可修结构问题 |
| [existing-tools.md](existing-tools.md) | 防重复档案（权威，每批结束后更新） |
