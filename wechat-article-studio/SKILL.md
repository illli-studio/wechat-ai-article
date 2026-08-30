---
name: wechat-article-studio
description: 制作“illli 周报｜超灵感 AI 工作室”微信公众号内容：从选题、写作、排版到亮色封面、GIF 动效、微信兼容 HTML 与草稿箱预检；适合 AI 周报、工具评测、案例拆解和观点文章。
---

# illli 公众号 AI 内容工作室

把一个选题、素材文件夹或 Markdown 稿件，变成可阅读、可预览、可交付的微信公众号文章。默认品牌是 `illli 周报`，视觉方向是亮色、细网格、主紫与薄荷绿、克制的科技感。

## 任务路由

- **只有方向**：先研究近期事实与一手来源，再提出选题、写作并排版。最新事实必须联网核验，不凭记忆编造。
- **已有素材或 Markdown**：优先保留事实与观点，只修复结构、可读性、链接和排版；除非用户要求，不擅自改变结论。
- **只要文章**：选择 `templates/` 中最接近的模板，输出结构化 Markdown；需要视觉时同时做封面和预览。
- **只要排版**：不重写内容，直接运行 HTML 构建器；保留原图比例与来源链接。
- **要发草稿箱**：先生成本地预览和 dry-run，展示标题、摘要、封面、图片数量；只有用户在发送前即时确认，才能调用草稿 API。创建草稿不等于发布。

## 先读取的资源

- 写作或研究：`references/research-and-sourcing.md`
- 品牌、颜色、字体和封面：`references/illli-brand.md`
- 内容模板与文章结构：`references/content-templates.md`
- 微信 HTML、图片上传和草稿流程：`references/wechat-html-and-draft.md`

## 默认内容系统

根据内容选择一种，不机械套用：

1. `templates/weekly.md`：四栏周报，适合多条 AI 资讯、工具、案例和洞察。
2. `templates/deep-dive.md`：一个主题的现象—机制—证据—边界—行动建议。
3. `templates/tool-review.md`：一个 AI 工具的场景、上手、优缺点、适用人群和结论。

写每条内容时，尽量回答：发生了什么、为什么重要、对读者意味着什么。标题要兑现正文，不使用没有证据的“颠覆”“第一”“所有人都在用”等绝对化表述。

## 生成产物

从技能目录运行脚本，使用当前环境可用的 Python：

```bash
python scripts/build_wechat_html.py <article.md> \
  --output <output/article.wechat.html> \
  --preview <output/article.preview.html> \
  --image-prefix ../
```

构建器会把 Markdown 转为：

- `article.wechat.html`：仅含微信公众号正文片段，关键样式写入 `style`，不含脚本、iframe、外部 CSS 或本地绝对路径。
- `article.preview.html`：浏览器预览外壳，可有 CSS 入场/呼吸动画；不提交给微信。

公众号内需要动效时，使用低频、装饰性的 GIF：

```bash
python scripts/create_illli_motion_banner.py --output <output/illli-motion-banner.gif>
```

不要用 JavaScript、CSS 动画、快速滚动文字或高频闪烁替代 GIF。GIF 被放入正文前先在本地预览检查尺寸、清晰度和文字是否被裁切。

## 封面

```bash
python scripts/create_ai_weekly_cover.py \
  --title "不超过两行的主标题" \
  --subtitle "illli 周报 · 灵感不止于想象，超灵感让它落地" \
  --issue "YYYY · MM · DD" \
  --wide <output/cover-wide.jpg> \
  --square <output/cover-square.jpg>
```

默认生成 2.35:1 主封面和 1:1 分享图。标题只保留最强的 2–3 个信息点；Logo 保持比例并留出安全区。具体令牌和视觉决策见品牌参考。

## 草稿预检与发送

先 dry-run：

```bash
python scripts/publish_wechat_draft.py \
  --markdown <article.md> \
  --html <output/article.wechat.html> \
  --cover <output/cover-wide.jpg> \
  --payload-out <output/draft-payload.preview.json> \
  --author "illli 超灵感 AI 工作室"
```

真实写入前向用户明确说明目标公众号、标题、封面、正文图片数量和将要创建的是“草稿”，然后请求即时确认。收到明确确认后，才追加 `--send --confirm-create-draft`。凭据只从 `WECHAT_ACCESS_TOKEN` 或 `WECHAT_APP_ID`/`WECHAT_APP_SECRET` 环境变量读取，不写入文件或日志。

正文图片通过 `media/uploadimg` 上传，封面通过永久素材接口上传，最后调用 `draft/add`；绝不自动调用发布或群发接口。

## 完成检查

- 品牌名称统一为 `illli 周报` 或 `超灵感 AI 工作室`，没有旧模板品牌。
- 预览在桌面和约 390 px 手机宽度下无横向溢出、错位、缺图或过密间距。
- `article.wechat.html` 无 `<script>`、外部 CSS、iframe、本地绝对路径。
- 图片加载正常，GIF 文字不裁切，正文图片不拉伸。
- 标题不超过 64 字，作者不超过 16 字，摘要不超过 120 字。
- dry-run 成功后才能进入草稿确认；成功后只报告草稿 `media_id`，不声称已发布。

默认交付：`article.preview.html`、`article.wechat.html`、`cover-wide.jpg`、`cover-square.jpg`。只有用户点名时才额外交付来源台账或中间文件。
