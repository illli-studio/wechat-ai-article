# illli 公众号 AI 内容工作室

一个面向 Codex 的公众号内容生产 Skill：把 AI 资讯、产品素材或 Markdown 稿件，变成有品牌感的微信公众号文章。

> 用 AI 点燃创意，把灵感快速变成可上线的产品。

## 特色

- `weekly`：AI 周报与行业快讯
- `deep-dive`：趋势、案例和观点拆解
- `tool-review`：AI 工具体验与评测
- 微信兼容 HTML + 桌面/移动预览
- 亮色 illli 封面、1:1 分享图和低频 GIF 动效
- dry-run 后，经确认写入微信公众号草稿箱

## 安装

将 `wechat-article-studio/` 复制到：

```text
%USERPROFILE%\.codex\skills\wechat-article-studio
```

然后重启 Codex 或新建任务，并使用：

```text
使用 $wechat-article-studio，把这份素材制作成 illli 周报。
```

完整安装说明见 [INSTALL-AND-USAGE-GUIDE.zh-CN.md](INSTALL-AND-USAGE-GUIDE.zh-CN.md)。

## 本地生成

```bash
python wechat-article-studio/scripts/build_wechat_html.py article.md \
  --output output/article.wechat.html \
  --preview output/article.preview.html \
  --image-prefix ../
```

封面和动效：

```bash
python wechat-article-studio/scripts/create_ai_weekly_cover.py \
  --title "AI 资讯与灵感实践" \
  --subtitle "illli 周报 · 灵感不止于想象，超灵感让它落地" \
  --issue "2026 · 08 · 30" \
  --wide output/cover-wide.jpg \
  --square output/cover-square.jpg

python wechat-article-studio/scripts/create_illli_motion_banner.py \
  --output output/illli-motion-banner.gif
```

## 模板

模板位于 `wechat-article-studio/templates/`：

- `weekly.md`：四栏周报
- `deep-dive.md`：单主题深度文章
- `tool-review.md`：AI 工具评测

## 发送草稿

先执行 dry-run，确认标题、作者、摘要、封面和图片数量后，再在用户即时确认的前提下使用 `--send --confirm-create-draft`。此 Skill 只创建草稿，不发布文章。

## 品牌

illli Ai studio｜超灵感 AI 工作室专注智能工具、动画设计、数据可视化和 AI 产品落地。视觉令牌与写作边界见 `wechat-article-studio/references/`。
