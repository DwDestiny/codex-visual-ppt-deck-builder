---
name: visual-ppt-deck-builder
description: Build editable PPTX decks from a confirmed topic, outline, visual style, slide plan, generated backgrounds, copy, transparent visual assets, charts, and layouts. Use when the user asks to create a PowerPoint/PPT/PPTX deck, proposal, course deck, report deck, pitch deck, or slide presentation with AI-generated visuals and transparent-background assets.
---

# Visual PPT Deck Builder

## 核心判断

这个 skill 不是“把 Markdown 转成 PPT”。它负责把主题变成可交付的 PPTX：先定故事，再定风格，再逐页生成背景、文案、透明素材、图表和排版。最终交付必须是可编辑 `.pptx`，不能只交一组截图。

需要高 polish 的商业分析、投资人、经营复盘、战略叙事 deck 时，优先配合系统 `Presentations` skill；本 skill 负责更通用的“AI 视觉素材 + PPTX 编排”流程。

## 强制工作流

1. **确认主题**：主题、受众、使用场景、语气、是否有品牌或参考资料。
2. **确认大纲**：先给出章节和叙事顺序，不直接开做页面。
3. **确认风格**：优先走模板仿制或效果图母稿路线。如果用户提供高质量 `.pptx`，先把它当作风格母本，提取版式、字体、颜色、留白和图表语言；如果没有模板，再结合用户偏好和主题，为每套风格直出完整效果图母稿，再从被认可的效果图反拆 clean background、透明素材、坐标蓝图和可编辑 PPT 层。每套候选最终必须包含一页可编辑 PPTX 样板和一张由该 PPTX 导出的 PNG 预览；样板里要带真实标题、正文、指标和图表标签，让用户判断字体、字号层级、排版密度和内容承载效果。默认提供 8 套独立风格，不要把多套风格塞进一张总览图。
4. **确认张数和每页内容**：输出 slide plan，逐页写清标题、核心信息、证明对象、需要生成的背景/透明素材/图表。
5. **逐张生成**：按确认后的风格逐页生成背景、文案、透明 PNG 素材、图表和页面布局。
6. **组合 PPTX**：优先使用可编辑文本、形状、图表和图片层。只有背景大图可以是 raster；正文、图表、关键标签不要糊成整页图。
7. **硬门禁验收**：先跑 deck spec 质量检查，再生成整套 SVG 预览图；未通过前不要交付。
8. **交付**：检查 PPTX 能打开、页数正确、媒体资源存在、文字不溢出、透明素材叠加正常。

## 风格候选要求

### Skywork 对标后的硬规则

参考 Skywork PPT skill 的产品纪律：PPT 生成不能是黑盒的一次性“吐文件”，必须有清晰路由、模板仿制能力、资料补充和长任务进度回传。本 skill 按下面规则执行：

- **有模板先仿模板**：用户给 `.pptx` 时，模板是第一风格来源。先拆模板的页面类型、标题层级、字体、色板、留白、图表语法和图片策略，再生成新主题内容。不要绕开模板重新发明风格。
- **无模板才做 8 套候选**：没有模板时，才走 8 套风格候选。候选必须先有真实图片母稿或真实 raster 背景素材。
- **正式背景必须来自生图或用户素材**：背景、人物、建筑、科技舞台、东方山水、产品场景等主视觉素材必须来自 Codex imagegen、Skywork Design、用户模板反拆或用户提供图片。禁止用 SVG、HTML、Canvas、Pillow 或脚本图形冒充商业设计素材。
- **程序只负责可编辑层**：代码可以生成 PPT 原生文字、形状、图表和坐标落版；不能承担主视觉设计。
- **长任务必须持续回传进度**：搜索、生成母稿、生成 clean background、组装 PPTX、导出预览都要向用户说明当前阶段，不能长时间无声等待。

8 套候选必须走**效果图母稿优先**的真实 PPT 生产路径：先用图片直出完整 PPT 效果图，允许其中带样本文字、指标和图表，用来判断审美、排版、字体、密度和图表语言；用户认可后，再基于这张效果图生成一版移除文字、数字、图表和标签的 clean background，并把角色、装饰、图标等拆成透明素材；最后用可编辑 PPT 文本、形状、图表和图片层重建一页 PPTX，再从 PPTX 导出 PNG 预览给用户选。不要只列文字风格名，也不要用 SVG、HTML、CSS、Canvas 或整页生图冒充最终可编辑页面。默认候选覆盖这些方向：

除了配色和背景之外，候选还必须至少拆成 **6 种不同版式变体**。标题锁定方式、正文语法、指标语法和图表语法不能全部复用同一套骨架，否则就只是模板换皮，不算真正可选的风格库。

商务级风格候选还有一条硬门槛：**禁止容器框思维**。正文区、指标区和图表区必须嵌入背景预留的留白、纸纹、玻璃光带、细线节奏或风格化坐标区域里；不要用两个大面积矩形分别装正文和图表，也不要给指标套描边小框。候选页的大面积正文容器、大面积图表容器和指标描边框数量必须为 0，浅色风格也要通过留白、层次和背景纹理融合，而不是靠卡片遮住背景。

更高一层的门槛是**可读性先于装饰**。背景图不是气氛图，必须主动给标题、正文、指标和图表留出阅读安全区：低纹理、低噪声、有合适明暗过渡，且不长成矩形卡片。深色背景用白色/浅蓝灰文字和高亮线；浅色背景用近黑/中灰文字和克制强调色。图表主线或主柱必须比背景高一个明确亮度层级，辅助线降低透明度；标签不要压在强光、人物、山水、建筑线条或复杂纹理上。**不能靠加框补救可读性**，如果看不清，优先重做背景安全区、换字色/线色、调整图表落点，而不是加一个框。

风格候选必须保留**坐标蓝图门禁**，但蓝图不是凭空创意起点，而是从已确认的效果图母稿里反拆出来。每个候选都要给出 16:9 页面坐标蓝图，单位为 inches，页面基准为 `13.333 x 7.5`。蓝图至少包含 `title_zone`、`text_zone`、`chart_zone`、`metrics_zone`、`visual_focus_zone`、`protected_empty_zone`，每个区域必须写清 `x/y/w/h`、用途和内容容量。clean background prompt 必须带上这些坐标，要求背景在文字区和图表区主动留出低纹理、低噪声、合适明暗过渡的安全区。PPTX 落版时，标题、正文、指标和图表必须按蓝图坐标放置；如果背景破坏了安全区，重做 clean background；如果内容放不下，先精简文案或调整大纲，不要缩小到看不清，更不要加框遮丑。

- 业务冷静型：适合经营复盘、战略汇报、董事会。
- 编辑杂志型：适合课程、品牌故事、公开演讲。
- 产品演示型：适合 App、SaaS、工具发布。
- 数据图表型：适合行业报告、趋势分析、投融资。
- 视觉叙事型：适合 AI 通识课、故事化培训、创意提案。
- 国潮东方型：适合文化品牌、消费品和东方美学提案。
- 未来科技型：适合 AI 产品发布会、创新方案和科技活动。
- 投资人叙事型：适合融资路演、商业计划和增长故事。

候选图通过后，把被选中的方向固化为 `visual_style`：色板、字体气质、背景策略、图表语言、透明素材策略、禁用元素。

正式生成 8 套真实样板包前，先生成或准备 8 张真实 raster 背景图，文件名必须是 `background-<style-slug>.png`，放在同一个目录，例如：

```text
background-minimal-premium.png
background-playful-anime.png
background-data-analytics.png
background-oriental-heritage.png
background-future-tech.png
background-editorial-magazine.png
background-saas-product.png
background-investor-narrative.png
```

这些背景必须来自 Codex imagegen、Skywork Design、用户模板反拆或用户提供素材。准备好以后运行工具生成 8 套真实样板包：

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/visual-ppt-deck-builder/scripts/build_style_candidates.js" \
  --output-dir /absolute/path/style-candidates \
  --topic "<deck topic>" \
  --background-source-dir /absolute/path/generated-backgrounds
```

如果没有 `--background-source-dir`，工具会直接失败。这是故意的：正式候选不能再自动用程序画背景。只有单元测试或结构验证可以使用 `--allow-placeholder-backgrounds`，该开关生成的结果不得进入 README、风格库展示或商业交付。

工具会生成：

- `style-candidate-spec.json`：8 个风格候选、PPTX 样板路径、PNG 预览路径、背景素材策略和 PPT 图层契约。
- `style-candidates.md`：执行说明和用户确认清单。
- `samples/style-sample-*.pptx`：每个风格一页真实可编辑 PPTX 样板。
- `previews/style-sample-*.png`：从对应 PPTX 样板导出的 PNG 预览。
- `prompts/style-reference-*.md`：用于先直出完整效果图母稿的提示词。
- `prompts/clean-background-*.md`：用于在母稿通过后生成无文字 clean background 的提示词。
- `style-visual-qa.json`：文字区、图表区与背景复杂度的视觉 QA 报告；任何候选失败都不能作为通过样张展示。
- `style-design-qa.json`：主视觉丰富度 QA 报告；防止 8 套候选退化成只换底色。

如果要提高候选质感，先按 `prompts/style-reference-*.md` 逐张调用 Codex 生图能力生成完整效果图母稿；选中方向后，再按 `prompts/clean-background-*.md` 生成 clean background，保存到 `assets/background-*.png` 后重新运行工具。注意：clean background 不能包含标题、正文、数字、字母、图表标签或 UI 文本；这些内容必须由 PPTX 可编辑层承载。

背景 prompt 必须明确三类区域：`text-safe zone`、`chart-safe zone` 和 `low-detail transition area`。这三类区域是为了让 PPT 文本和图表自然嵌入背景，不是为了后续贴卡片。若候选预览出现文字不清、图表不清、小字压复杂纹理或线条压强光，直接判为未通过。

真正给用户看的仍然是 8 张独立 PNG 预览，但这些 PNG 必须由 PPTX 样板导出，而不是直接由整页生图模型生成。风格样张必须展示样本标题、正文、要点、指标和图表标签，用来检查字体气质、标题层级、正文可读性、卡片密度和图表语言。最终 PPT 中这些内容必须复用同一套可编辑文本、形状或图表层实现，不能把正式页面整页截图化。

## 透明素材策略

需要透明背景素材时调用 `$transparent-visual-assets`：

- 人物、物体、图标、贴纸、图表装饰、流程节点、产品插画优先做透明 PNG。
- 背景可以单独生成，但不要把整页正文和图表烤进背景图。
- 图表如果要用户可编辑，优先用 PPT 原生形状或脚本绘制；如果是复杂示意插画，再用透明 PNG。

## PPTX 生成方式

有两条路线：

- **高端 deck 路线**：调用系统 `Presentations` skill，用 artifact-tool presentation JSX 构建、渲染、复核、导出 PPTX。
- **通用确定性路线**：使用本 skill 的 `scripts/build_visual_pptx.js`，从 JSON deck spec 生成可编辑 PPTX。

运行 helper：

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/visual-ppt-deck-builder/scripts/build_visual_pptx.js" \
  --spec /absolute/path/deck_spec.json \
  --output /absolute/path/final_deck.pptx
```

如果在 Codex bundled runtime 里执行，优先使用：

```bash
/Users/dw/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  "${CODEX_HOME:-$HOME/.codex}/skills/visual-ppt-deck-builder/scripts/build_visual_pptx.js" \
  --spec /absolute/path/deck_spec.json \
  --output /absolute/path/final_deck.pptx
```

Deck spec 写法见 `references/deck-spec-schema.md`。

母稿反拆页型已经有一个可运行样例：`reference_visual_trend`。它用于商务、动漫、科技等趋势数据页，把 clean background 作为整页背景，把标题、正文、指标、柱状图、趋势线和标签全部重建成 PPT 可编辑对象。使用这个页型时，`background_image` 只能指向无文字、无图表的 clean background；不要把带完整文案和图表的效果图母稿当背景塞进 PPT。旧别名 `reference_anime_trend` 仍然兼容，但新样张优先用 `reference_visual_trend`。

不同风格不能共用一套死板字色。深色科技、浅色商务、国潮纸纹、活泼动漫等背景必须通过 `overlay_style` 调整标题/正文/指标/图表颜色、图表网格线和 bullet 编号，保证视觉语言跟背景融合，而不是把同一套文字样式硬贴上去。

商用 deck 交付前必须跑质量门禁：

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/visual-ppt-deck-builder/scripts/validate_deck_quality.js" \
  --spec /absolute/path/deck_spec.json \
  --report /absolute/path/qa_report.json
```

同时生成可扫视的整套页面预览：

```bash
node "${CODEX_HOME:-$HOME/.codex}/skills/visual-ppt-deck-builder/scripts/build_deck_preview.js" \
  --spec /absolute/path/deck_spec.json \
  --output-dir /absolute/path/preview
```

预览目录会包含逐页 `slide-01.svg` 和 `contact-sheet.svg`。它不是最终 PPT 渲染，但能快速发现页型重复、空洞页面、模板词、缺来源和信息密度问题。

## 验收标准

- 用户已确认主题、大纲、风格、张数和每页内容。
- 有 8 套风格候选，且每套都包含可编辑 PPTX 样板和由 PPTX 导出的 PNG 预览；最终风格被明确选中。
- 商用 deck 至少 6 页，至少 5 种 layout；必须覆盖结论页、架构/路线页、指标/图表页、对比页、风险与下一步页。
- 除标题/章节/收尾页外，每页必须有 `claim`，也就是这一页真正想证明的一句话。
- PPTX 页数与 slide plan 一致。
- 标题、正文、图表标签是可编辑对象，不能全页截图化。
- 风格候选不能只是“背景 + 两个大白框”，必须通过融合式版面证明该风格能真实延展到商务级 PPT。
- 风格候选的背景来源必须是 Codex imagegen、Skywork Design、用户模板反拆或用户提供 raster 图片；测试用程序背景不能作为正式样张展示。
- 风格候选里的正文、指标和图表不能放进矩形容器；大面积正文容器、大面积图表容器和指标描边框必须为 0。
- 背景必须有阅读安全区、图表安全区和低纹理过渡区；正文对比度目标不低于 4.5:1，图表主线/主柱对比度目标不低于 3:1。
- 风格候选必须生成并检查 `style-visual-qa.json`；如果 `ok=false` 或任一候选 `has_background_overlap_risk=true`，不能验收，也不能把该样张放进 README 展示。
- 如果字或图表看不清，不能靠加框补救；必须重做背景安全区、调整字色/线色或移动元素位置。
- 透明素材边缘干净，叠在深色、浅色背景上都能读清。
- 图表有明确口径；没有来源的数据不能伪装成事实。
- 不允许残留 `Topic`、`Style`、`Assets`、`TODO`、`TBD`、`占位` 这类模板词。
- 最终交付 `.pptx`，同时保留生成用的 deck spec、透明素材和关键源图。

## 需要时读取

- `references/research-notes.md`：开源 PPT 生成方案调研和取舍。
- `references/deck-spec-schema.md`：helper 支持的 JSON spec 格式。
