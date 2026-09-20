# Minitool 工具 ZIP 包构建规范

> Minitool 工具以**离线 zip 静态包**交付：纯本地、不联网，所有资源打包在 zip 内。
> 集成脚本会把包内页面拆出 HTML / CSS / JS，包进站点的 SEO 工具页模板（见 [seo-page-template.md](./seo-page-template.md)），因此包必须**完全自包含**、**脚本全部外置**。

## 目录

- §1 目录结构与打包
- §2 支持的文件类型
- §3 manifest.json（必填，站点集成清单）
- §4 资源加载与脚本规则
- §5 工具 UI 规范
- §6 路径与引用规则
- §7 打包前自检

---

## 1. 目录结构与打包

**唯一硬性结构要求：`index.html` 位于 zip 根目录作为入口。** 其余文件自由组织 —— 平铺或分目录（`assets/`、`images/` 等）皆可，用相对路径引用。

典型平铺结构（推荐，绝大多数工具够用）：

```
tool.zip
├── index.html        # 必需 — 工具 UI 入口，必须在根目录
├── app.js            # 工具逻辑（外置经典脚本）
├── style.css         # 工具样式（自包含）
├── manifest.json     # 必需 — 站点集成清单（见 §3）
└── icon.png          # 可选 — 包内图片
```

| 路径 | 要求 | 说明 |
| --- | --- | --- |
| `index.html` | **必须在 zip 根目录** | 唯一入口；不可改名、不可放进子目录 |
| `manifest.json` | **必须在 zip 根目录** | 集成脚本据此生成 SEO 页面与首页卡片 |
| 其余文件 / 文件夹 | 自由 | JS / CSS / 图片 / 字体等，平铺或分目录皆可，相对路径引用 |

### 禁止出现在 zip 内

- `.DS_Store`、`__MACOSX`、`node_modules`、`.git`
- `*.map`、构建配置文件（`vite.config.*`、`webpack.config.*` 等）
- 把整个项目多包一层目录，导致 `index.html` 不在根（错误：`app/index.html`；正确：根目录就有 `index.html`）

### 打包方式（关键）

**压缩的是「与 `index.html` 同级的那批文件」本身，不是它们所在的文件夹。** 必须先进入该目录再压缩当前目录内容，否则解压后会多套一层目录、`index.html` 不在根。

```bash
# ✅ 正确：进入目录，压缩目录“内容”（index.html 直接在 zip 根）
cd my-tool && zip -r ../tool.zip . -x '*.DS_Store'

# ❌ 错误：压缩目录“本身”，解压后多一层 my-tool/，index.html 变成 my-tool/index.html
zip -r tool.zip my-tool
```

解压后顶层应直接看到 `index.html` 与 `manifest.json`。

---

## 2. 支持的文件类型

zip 内仅允许以下类型（校验脚本按白名单逐文件检查）：

| 类型 | 用途 |
| --- | --- |
| `.html` | 入口，有且只有一个 `index.html` |
| `.css` | 样式文件 |
| `.js` | 脚本文件 |
| `.png` / `.jpg` / `.jpeg` / `.gif` / `.webp` / `.svg` | 图片资源 |
| `.woff` / `.woff2` | 字体文件 |
| `.json` | manifest 与静态数据 |

---

## 3. manifest.json（必填，站点集成清单）

`manifest.json` 是 Minitool 站点集成用的清单，**不是** PWA manifest。集成脚本只认这份文件来生成 SEO 工具页、首页卡片、sitemap 条目。字段**全部必填**：

```json
{
  "name": "Case Converter",
  "file": "case-converter",
  "category": "text-tools",
  "desc": "Convert text between upper, lower, title and camel case.",
  "metaDescription": "Free online case converter. Switch text between UPPER, lower, Title, camelCase and snake_case instantly in your browser. No signup, 100% private.",
  "keywords": ["case converter", "uppercase", "lowercase", "title case", "camel case", "text tools"],
  "icon": "text",
  "faq": [
    { "q": "What is a case converter?", "a": "A case converter changes the capitalization of text — for example turning a sentence into ALL CAPS, all lowercase, Title Case, or developer conventions like camelCase and snake_case." },
    { "q": "Is this case converter free?", "a": "Yes, completely free with no usage limits. No signup or installation is required — open the page and paste your text." },
    { "q": "Is my text uploaded anywhere?", "a": "No. All conversion happens locally in your browser using JavaScript. Your text never leaves your device." }
  ],
  "toolPurpose": "It converts any text between common capitalization styles — UPPERCASE, lowercase, Title Case, camelCase, and snake_case — in one click.",
  "useCases": [
    "Formatting variable names, titles, and URLs for code or publishing.",
    "Preparing content for social posts, ads, or style guides with strict case rules.",
    "Quickly switching between developer conventions like camelCase and snake_case."
  ],
  "audience": "writers, developers, editors, marketers, and anyone who needs consistent text capitalization."
}
```

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `name` | string | 工具英文名，用于 title / H1 / 卡片 / JSON-LD |
| `file` | string | **kebab-case**（`^[a-z0-9]+(-[a-z0-9]+)*$`）。仓库中生成 `tools/<file>.html`，对外公开 URL 为 `https://minitool.io/tools/<file>`（Cloudflare Pages pretty URL） |
| `category` | string | kebab-case。内置三个：`text-tools` / `developer-tools` / `calculators`；**写新值会自动在首页创建对应分类 section**（无需手工改首页） |
| `categoryTitle` | string | 可选，仅新分类时生效：section 标题（缺省自动标题化，如 design-tools → Design Tools） |
| `categoryDesc` | string | 可选，仅新分类时生效：section 副标题 |
| `desc` | string | 卡片一句话文案，**≤60 字符**，英文 |
| `metaDescription` | string | SEO meta description，**≤155 字符**，含核心关键词 + 行动号召，英文 |
| `keywords` | array | 关键词数组，用于首页搜索过滤与 meta keywords |
| `icon` | string | 六选一：`code` / `link` / `key` / `text` / `calc` / `swap` |
| `faq` | array | **恰好 3 条** `{q, a}`，英文问答，用于 FAQPage JSON-LD |
| `toolPurpose` | string | 一句话用途说明，用于 SEO 文章 What is 段落，英文。**禁止**写成 “Our free online X is a small, focused utility...” 等模板句；必须直接说明该工具的功能和价值 |
| `useCases` | array | **强烈推荐**提供 3–4 条具体使用场景，用于生成 Common Use Cases 段落。场景必须与工具真实用途相关，禁止跨工具复制粘贴 |
| `audience` | string | **强烈推荐**一句话目标用户，用于生成 Who Uses This Tool? 段落。必须具体，不能是 “anyone who needs a quick online tool” 这类泛泛描述 |

写文案前读 [seo-page-template.md](./seo-page-template.md)，弄清每个字段最终出现在页面的什么位置。

---

## 4. 资源加载与脚本规则

工具包按「受控离线容器」标准约束页面如何加载资源。除包内文件外，图片另允许 `data:` / `blob:` 内存来源。

| 资源类型 | 允许 | 禁止 |
| --- | --- | --- |
| 脚本 `<script>` | 引用包内脚本 `<script src="./app.js">` | 内联 `<script>...</script>`；行内事件 `onclick="..."`；`javascript:` URI；`eval()` / `new Function()`；外部域名 / `data:` / `blob:` 脚本 |
| 样式 `<style>` / `<link>` | 内联 `<style>`、行内 `style="..."`、包内样式表 | 外部域名样式表 |
| 图片 `<img>` / CSS 背景图 | 包内图片；`data:` URI；`blob:`（`createObjectURL`） | 外部域名图片 |
| 字体 `@font-face` | 包内字体文件 | 外部域名字体 |
| iframe / object | — | 全部禁止 |

关键点：

- **脚本必须外置**：内联 `<script>...</script>`、行内事件 `onclick="..."`、`javascript:` URI 一律禁止。JS 写进包内 `.js` 用 `<script src>` 引入，事件用 `addEventListener` 绑定。
- **脚本必须是经典脚本**：只用 `<script src="./app.js">`，**不要 `type="module"`**，JS 里也不要 `import` / `export`。要拆多个 JS 文件时按依赖顺序写多个 `<script src>`，靠 `window` 命名空间协作，避免 top-level `await`。
- **样式可内联也可外置**：`<style>`、`style="..."`、`<link rel="stylesheet" href="./style.css">` 都行；集成时会被统一内联进工具页。
- **零外部 URL**：全包不得出现任何 `http://` / `https://` 资源引用（CDN、字体、图片、统计脚本等）。SVG 命名空间声明 `xmlns="http://www.w3.org/2000/svg"` 是唯一豁免。
- **无 `<base href>`、无 `<iframe>`、无自建 CSP `<meta>`**。

---

## 5. 工具 UI 规范

工具页运行在站点外壳里（导航 / 面包屑 / 页脚由模板提供），你的 `index.html` 只需要写**工具本体**。要求：

- **样式自包含**：工具的 CSS 必须随包携带（`style.css` 或内联 `<style>`），不得依赖站点 `common.js` / `style.css` 的运行时行为。可以直接复制站点设计 token 到你的 `style.css` 保持视觉一致：

```css
:root {
  --bg-primary: #fbfaf7; --bg-secondary: #f4f2ec; --bg-card: #ffffff;
  --text-primary: #1b2432; --text-secondary: #59637a; --text-muted: #8a93a6;
  --accent: #3557a8; --accent-hover: #2a4689; --accent-soft: #eef1f9;
  --border: #e6e3da; --radius: 10px; --radius-sm: 6px;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #14161c; --bg-secondary: #1a1d25; --bg-card: #1e222c;
    --text-primary: #e8e6e0; --text-secondary: #a8b0c2; --text-muted: #79839a;
    --accent: #7d9be0; --accent-hover: #9ab4ea; --accent-soft: #26314f;
    --border: #2c313d;
  }
}
```

- **class 前缀 `t-`**：工具独有样式一律用 `t-` 前缀的 class（如 `.t-stats`、`.t-error`），避免与站点全局 class 冲突。
- **复制功能（复制契约，必须照此实现）**：包必须自包含复制能力，但要**优先复用站点全局函数**，写法固定为「探测 → 降级」两段式：

```js
function copyText(text) {
  // 集成到 Minitool 站点后，页面会加载 common.js，
  // 提供带全局 toast 反馈的 window.copyToClipboard —— 优先使用
  if (typeof window.copyToClipboard === 'function') {
    window.copyToClipboard(text);
    return;
  }
  // 独立容器（如小红书）内没有 common.js，用包内自带实现兜底
  function showLocalToast(msg) { /* 包内实现一个简单 toast：fixed 定位、2 秒消失 */ }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(function () { showLocalToast('Copied to clipboard'); }, legacy);
  } else { legacy(); }
  function legacy() {
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.cssText = 'position:fixed;opacity:0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
    showLocalToast('Copied to clipboard');
  }
}
```

要点：① 优先调 `window.copyToClipboard`（站点环境有 toast）；② 独立环境的兜底实现**也必须带可见反馈**（toast 或按钮变文案二选一，推荐 toast）；③ 禁止只静默复制无任何反馈。
- **移动端可用**：600px 宽度下正常操作；输入框 / 按钮触控尺寸足够；viewport 含 `width=device-width, initial-scale=1.0`。
- **可访问性**：交互元素可被 Tab 聚焦；输出区用 `aria-live="polite"`。
- **全英文 UI**：按钮、占位符、提示、报错全部英文。文案语气：简短、直接、工程感。
- **`<title>` 写工具名**即可；SEO title / meta 由集成模板从 manifest 生成，包内无需写。

---

## 6. 路径与引用规则

| 规则 | 正确 | 错误 |
| --- | --- | --- |
| 资源引用 | `./app.js`、`./assets/a.png` | `/assets/a.png`（绝对路径）、`assets/a.png`（省略 `./`，允许但推荐显式） |
| 入口 | 根目录 `index.html` | `src/index.html` |
| base | 不使用 | `<base href="...">` |
| 外部资源 | 下载后打进 zip 再相对引用 | 任何 `https://...` 在线引用 |
| 单页 | 一个 `index.html`，视图 JS 切换 | 多 HTML 页面站点 |

---

## 7. 打包前自检

### 包结构

- [ ] `index.html` 与 `manifest.json` 都在 zip 根目录（不在任何子目录里）
- [ ] 解压后顶层直接是文件，**未多套一层目录**（压缩的是目录内容而非目录本身）
- [ ] 仅含白名单文件类型（见 §2），无垃圾文件（`.DS_Store` / `__MACOSX` / `node_modules` / `*.map` / 构建配置）

### manifest.json（见 §3）

- [ ] 9 个字段全部存在；`file` 为 kebab-case；`category` / `icon` 取值合法
- [ ] `desc` ≤60 字符、`metaDescription` ≤155 字符；`faq` 恰好 3 条 `{q,a}`
- [ ] `toolPurpose` 直接说明功能，**不含** “small, focused utility”“there is nothing to install”“type or paste your input” 等模板填充句
- [ ] （强烈推荐）`useCases` 提供 3–4 条且与工具真实场景相关；`audience` 具体，不泛泛
- [ ] 全部英文文案，无拼写错误

### index.html 与资源

- [ ] `<!DOCTYPE html>` + `lang="en"` + `charset=UTF-8`
- [ ] viewport 含 `width=device-width, initial-scale=1.0`
- [ ] 全部资源为相对路径，无 `http(s)://` 外部引用（`xmlns="http://www.w3.org/2000/svg"` 除外）
- [ ] 脚本全部外置：无内联 `<script>`、无 `onclick=` 等行内事件、无 `javascript:` / `eval` / `new Function`
- [ ] 脚本为经典脚本：无 `type="module"`，JS 内无 `import` / `export`
- [ ] 无 `<base href>`、无 `<iframe>` / `<object>`、无自建 CSP `<meta>`

### 工具 UI（见 §5）

- [ ] 样式自包含（token 已复制进包内 CSS），工具独有 class 带 `t-` 前缀
- [ ] 复制契约：优先 `window.copyToClipboard`（站点 toast），包内降级实现带可见反馈
- [ ] 600px 移动端可用；输出区 `aria-live`；全英文 UI

### 正确性（静态自查）

- [ ] JS 无语法错误；关键逻辑通读无明显运行时报错（调用未定义函数、引用 `null` DOM）
- [ ] 多文件 JS 依赖关系 / 加载顺序正确
- [ ] 页面引用的每个资源（脚本 / 样式 / 图片 / 字体）都已打进 zip，且路径正确
- [ ] 核心交互在代码层面自洽：事件有绑定、依赖的 DOM 存在、回调闭环完整

### 体积

- [ ] 总包（zip）不超过 10MB；建议控制在 2MB 以内

### 最后一步

- [ ] `python3 validate_tool.py tool.zip` 全部通过（退出码 0）

## 更新已有工具

如果 `file` 已经上线过，普通集成会被拒绝。使用更新模式可原地覆盖：

```bash
python3 scripts/integrate_tool.py --update tool.zip .
```

更新模式会：

- 重写 `tools/<file>.html`
- 在 `registry.json` 中原地替换该工具条目（保持顺序，"New" 徽章位置不变）
- 更新 `sitemap.xml` 里对应 URL 的 `lastmod`
- 替换 `archive/<file>.zip`

CI 场景下，把 zip 命名为 `<file>-update.zip` 上传到 `incoming/` 即可自动触发更新模式。
