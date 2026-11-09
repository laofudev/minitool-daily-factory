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

目标产物：`output/<YYYY-MM-DD>/` 目录下通过全部校验与测试的 `*.zip` + 一份 `report.md`。每批目标最多 10 个，但若同分类配额已满或质量不达标，允许少于 10 个，不要硬凑。

## 何时使用

- 每日定时任务触发（凌晨 0 点后）：批量生产 10 个工具
- 用户手动要求补做工具（「再做一个」「补两个」）
- 排查校验 / 测试失败，维护防重复档案

## 硬性规则（每条都必须遵守）

1. **不重复**：新工具的 `file` slug 和功能都不得与主站 `registry.json` 重复（查重流程见下）。宁可做冷门方向，也不克隆已有工具。
2. **每批最多 10 个**：每次定时运行目标产出不超过 10 个；若同分类配额已满或质量不达标，允许少于 10 个，report.md 里如实记录。
3. **分类配额**：同一批内同分类不超过 4 个；滚动 7 天内同分类不超过 15 个。
4. **质量门禁**：每个 zip 必须通过 `scripts/validate_tool.py` 全部检查（退出码 0），并通过下方「测试要求」。任何一项不过 = 不交付、不计入。
5. **按日期归档**：产出写入 `output/<当天日期 YYYY-MM-DD>/`，目录下同时写 `report.md`。
6. **全英文 UI**：按钮、占位符、提示、报错全部英文，语气简短直接。
7. **零外部依赖**：任何 `http(s)://` 资源引用（CDN/字体/图片/统计）一律禁止；纯前端零后端。

## 每日工作流程

### 第 0 步：查重（必做，开工前）

**权威来源是主站 `registry.json`**，`existing-tools.md` 仅作参考，不再手动维护。

1. 下载主站 registry：`curl -sL "https://raw.githubusercontent.com/laofudev/minitool/main/registry.json?cachebust=$(date +%s)" -o /tmp/registry.json`
2. 解析 `tools` 数组，得到已存在 slug 列表（当前约 640+）
3. 功能指纹查重：对每一候选工具，用 `category|input|output|algorithm|options` 五元组与已存在工具比对；同指纹视为重复
4. 今日工具的 slug 与功能指纹均不得与已存在清单重复

### 第 1 步：选题（最多 10 个）

- 从「已存在清单」之外选有真实搜索需求、纯前端可实现的方向
- **分类配额**：同一批内同分类不超过 4 个；滚动 7 天同分类不超过 15 个
- 先列出候选 `file` slug，逐一与 registry 比对，全部通过再动手

### 第 2 步：逐个开发

动手前先读 [references/tool-package-spec.md](references/tool-package-spec.md) 并**严格遵守全部约束**（zip 结构、脚本外置、经典脚本、manifest 12 字段、UI 规范、复制契约），再读 [references/seo-page-template.md](references/seo-page-template.md) 确认 manifest 文案的最终落地位置。写完对照其 §5/§7 自检清单逐条打勾。

### 第 3 步：逐个质量门禁

每个工具必须全部通过：

1. **结构校验（硬性）**：`python3 scripts/validate_tool.py <tool.zip>` 退出码 0。校验已升级：除原有结构规则外，`useCases` / `howToSteps` / `audience` / `pageTitle` / `shortBlurb` / `whyUse` 为必填，且内容去重。
2. **JS 语法检查**：`node --check app.js`（及包内每个 .js）零错误
3. **静态走查**：无内联脚本/行内事件、无 import/export、资源引用齐全、事件绑定闭环、DOM 引用存在、核心逻辑自洽
4. **内容去重**：同一批 10 个工具的 `useCases` / `audience` / `toolPurpose` 不能完全相同；`How to Use` 步骤不能整段复制其他工具。若发现 3 条以上通用文案重复，本批全部重写。
5. **已知答案测试向量**：对有确定性的逻辑（哈希/编码/转换/计算）在测试中用已验证的标准答案核对（可用 Node/Python 标准库生成参考值）
6. **浏览器实测（环境允许时）**：若环境提供浏览器自动化，必须真实打开页面、模拟点击、断言输出；无浏览器环境时在 report.md 中对该工具标注 `未浏览器实测`，其余测试项不能省略

### 第 4 步：归档 + 报告

- 每个 zip 放入 `output/<YYYY-MM-DD>/`
- 全部完成后写 `output/<YYYY-MM-DD>/report.md`：日期、10 个工具（slug/分类/测试结果/是否浏览器实测）、失败与重试记录
- 把 10 个新工具追加到 [existing-tools.md](existing-tools.md)（日期 / 工具名 / slug / 分类）

### 第 5 步：上线（人工审核，禁止自动 push）

**本 skill 不再自动推送到主站 `incoming/`。** 每日产出保留在 `output/<date>/`，等待人工审核后再通过主站 CI 上线。

人工上线流程（由站长或授权助手执行）：

1. 复核当日 `output/<date>/report.md`，确认每个 zip 都通过质量门禁
2. 把 zip 复制进主站仓库 `incoming/`（新工具用 `<file>.zip`；更新已有工具用 `<file>-update.zip`）
3. 提交并 push 主站仓库，触发 `.github/workflows/tool-intake.yml`
4. CI 自动校验并集成每个 zip；失败的 zip 留在 `incoming/` 并生成 `FAILED-<name>.log`，需修复后重推
5. 上线成功后，运行 `scripts/sync_existing_tools.py` 更新 [existing-tools.md](existing-tools.md)（或直接用 registry.json 作为权威来源）

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
