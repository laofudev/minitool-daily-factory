# SEO 页面包装契约（工具上线后的页面形态）

> 本文从站点 SPEC 提炼，描述 `integrate_tool.py` 如何把工具 zip 包装成符合站点契约的 SEO 工具页。
> 写 manifest 文案前读本文：每个字段出现在页面哪里、受什么约束，都在这里。

## 1. 页面骨架

每个工具上线后在仓库中得到 `tools/<file>.html`（文件保留 `.html` 扩展名），对外公开 URL 为 `https://minitool.io/tools/<file>`（Cloudflare Pages 会自动做 pretty URL）。结构克隆标准参考页 `tools/json-formatter.html`：

```
<head>  SEO meta（title / description / canonical / OG / Twitter / JSON-LD×2）
<body>
  site-nav（Logo + All Tools + About）
  breadcrumb（Home › Category › Tool）
  main.tool-page
    H1 + 副标题（统一 "Free, fast, and private. No signup required."）
    div.tool-container        ← 你的工具 HTML 注入这里，CSS/JS 随页面内联
    article.tool-description  ← SEO 文章：What is / How to Use / Why Use 三段
    section.related-tools     ← 同类最近 2 个工具的卡片
  footer（© 年份自动更新 + Privacy/Terms/About）
  common.js → analytics.js → 工具内联脚本
```

模板文件见 `assets/page-template.html`，占位符形如 `{{TOOL_NAME}}`。

## 2. 模板变量 ↔ manifest 字段

| 占位符 | 来源 | 出现位置与约束 |
| --- | --- | --- |
| `{{TOOL_NAME}}` | `manifest.name` | `<title>`（`{{TOOL_NAME}} - Free Online \| Minitool`，整体 ≤60 字符）、OG/Twitter title、H1（全页仅一次）、面包屑末段、JSON-LD name |
| `{{FILE_NAME}}` | `manifest.file` | canonical / og:url / JSON-LD url：`https://minitool.io/tools/<file>`；面包屑与卡片链接 |
| `{{META_DESCRIPTION}}` | `manifest.metaDescription` | meta description（≤155）、og:description、twitter:description |
| `{{CATEGORY_ID}}` | `manifest.category` | 面包屑分类锚点 `../#<category>` |
| `{{CATEGORY_NAME}}` | 由 category 映射 | 面包屑分类显示名（text-tools→Text & Writing Tools；developer-tools→Developer Tools；calculators→Calculators & Converters） |
| `{{APPLICATION_CATEGORY}}` | 由 category 映射 | JSON-LD WebApplication.applicationCategory（developer-tools→DeveloperApplication，其余→UtilitiesApplication） |
| `{{KEYWORDS}}` | `manifest.keywords` | meta keywords、首页卡片 `data-keywords`（搜索过滤用，空格连接） |
| `{{TOOL_PURPOSE}}` | `manifest.toolPurpose` | SEO 文章 What is 段核心句、JSON-LD description |

另有两个注入位（不算变量，由集成脚本生成）：

- **FAQ**：`manifest.faq` 3 条 → FAQPage JSON-LD（与 json-formatter 参考页一致，仅结构化数据）。
- **Related Tools**：从 `registry.json` 自动选**同分类最近集成的 2 个**工具（不足时回退到全站最近）；渲染为 `.tool-grid` 卡片，含图标 SVG + 名称 + desc。
- **工具本体**：包内 `index.html` 的 `<body>` 内容注入 `.tool-container`；包内 CSS（内联 `<style>` + 外置 `.css`）合并为页面 `<style>`；包内 JS（按 `<script src>` 顺序）合并为页面尾部内联 `<script>`。

## 3. 硬性 SEO 要求（模板已保证，无需在包内处理）

1. `<title>` 格式 `{{TOOL_NAME}} - Free Online | Minitool`（≤60 字符）→ **name 不要太长**
2. meta description ≤155 字符，含核心关键词 + 行动号召
3. canonical 指向 `https://minitool.io/tools/<file>`
4. Open Graph + Twitter Card meta 完整
5. JSON-LD ×2：WebApplication + FAQPage（3 条 Q&A，来自 manifest.faq）
6. 面包屑 Home › Category › Tool
7. H1 全页仅一次；副标题统一
8. SEO 文章 250–500 词，自然融入关键词，全英文。文章必须包含以下五段，且**严禁模板化**：
   - **What is**：从 `manifest.toolPurpose` 生成，必须直接说明该工具解决的具体问题，禁止出现 “small, focused utility”“there is nothing to install” 等通用填充句。
   - **Common Use Cases**：至少 3 条、至多 4 条，必须围绕该工具的真实场景撰写，不能从其他工具复制粘贴。
   - **How to Use**：4 步以内，步骤中的动词/对象要贴合该工具的实际 UI（例如计算器用 “Enter values and click Calculate”，文本工具用 “Paste text and choose a transformation”）。
   - **Who Uses This Tool?**：一句话目标用户，必须具体（例如 “web developers debugging API payloads”，而不是 “anyone who needs a quick online tool”）。
   - **Why Use Our {name}?**：4–5 条卖点，可保留站点通用项（Free / Privacy / Fast / Mobile Friendly），但至少要有一条和该工具特性相关。
9. Related Tools 区块 2 个已发布工具
10. 页脚版权行 `© <span id="year">`（common.js 自动更新）
11. 引入顺序：style.css → 页面 → common.js → analytics.js → 工具内联脚本
12. 无任何外部 CDN/字体/库依赖

## 4. integrate_tool.py 对站点仓库的改动清单

一次成功集成会产生以下变更（脚本末尾打印对应 git 命令）：

| 文件 | 改动 |
| --- | --- |
| `tools/<file>.html` | 新建 SEO 工具页（上述骨架） |
| `index.html` | **首页工具区是 registry.json 的自动生成投影**：`<!-- TOOLS-REGION:BEGIN/END -->` 之间的内容整体重建——分类 section 按 registry 分类目录顺序渲染（**manifest 里写了新分类会自动创建 section**，可用 categoryTitle/categoryDesc 指定文案，否则自动标题化）；分类内卡片**新的在前**；`badge-new` 只挂在最新集成的工具上；空分类不渲染；stat-strip 工具数更新为 registry 工具总数。也可随时用 `python3 integrate_tool.py --rebuild <repo>` 单独重建首页 |
| `sitemap.xml` | 以 `</urlset>` 为锚点插入新 `<url>` 条目（priority 0.8，lastmod 当天）；更新已有工具时同步更新对应 URL 的 `lastmod` |
| `registry.json` | 追加工具记录（file / name / category / icon / desc / keywords / integratedAt），供 Related Tools 与后续集成使用；不存在则以首页现有 5 个工具为种子创建 |
| `archive/<file>.zip` | 原始 zip 归档（幂等依据之一） |

**幂等**：普通集成时，若 `tools/<file>.html` 已存在或 registry 已含该 file，脚本拒绝重复集成（退出码 2），不会重复插卡。

**更新模式**：`python3 integrate_tool.py --update tool.zip <repo>` 会原地覆盖已有工具：`tools/<file>.html`、registry 条目、sitemap `lastmod`、`archive/<file>.zip` 都会被替换，但工具在 registry 中的位置不变（因此 "New" 徽章位置不变）。CI 中上传 `incoming/<file>-update.zip` 也会触发同样逻辑。

## 5. 首页卡片渲染样例

```html
<a href="tools/case-converter" class="tool-card" data-keywords="case converter uppercase lowercase">
  <span class="card-icon" aria-hidden="true"><svg …（icon 六选一）…></svg></span>
  <span><strong>Case Converter<span class="badge-new">New</span></strong><p>Convert text between upper, lower, title and camel case.</p></span>
</a>
```
