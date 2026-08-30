# 微信 HTML 与草稿箱规范

## 产物

- `article.wechat.html`：正文片段，可提交给草稿 API。
- `article.preview.html`：本地浏览器预览，不提交。
- `cover-wide.jpg`：2.35:1 主封面。
- `cover-square.jpg`：1:1 分享裁切参考。
- `draft-payload.preview.json`：dry-run 请求预览，不包含真实凭据。

## 微信兼容 HTML

- 使用语义化 `section`、`p`、`strong`、`blockquote`、`ul/li`、`a` 和 `img`。
- 所有关键样式写在元素 `style` 属性中；不用 JavaScript、iframe、表单、外部字体或远程 CSS。
- 标题、作者、摘要和封面是草稿字段，不重复塞入正文 HTML。
- 正文中本地图片必须在创建草稿前上传并替换为微信返回的图片 URL。
- 微信接口对格式与大小的限制会调整；执行真实发送前应核对当前官方文档和账号接口权限。

## API 流程

1. 用 `WECHAT_ACCESS_TOKEN`，或通过 `WECHAT_APP_ID`、`WECHAT_APP_SECRET` 获取访问令牌。
2. 本地正文图片调用 `POST /cgi-bin/media/uploadimg`，把返回 URL 写回 HTML。
3. 封面调用 `POST /cgi-bin/material/add_material?type=image`，取得永久素材 `media_id`。
4. 调用 `POST /cgi-bin/draft/add`，正文放在 `articles[0].content`，封面 ID 放在 `thumb_media_id`。
5. 保存返回的草稿 `media_id`。不要自动调用发布或群发接口。

当前官方入口：

- 新增草稿：`https://developers.weixin.qq.com/doc/subscription/api/draftbox/draftmanage/api_draft_add.html`
- 草稿接口地址：`https://api.weixin.qq.com/cgi-bin/draft/add?access_token=ACCESS_TOKEN`
- 正文图片接口：`https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=ACCESS_TOKEN`
- 永久素材接口：`https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=ACCESS_TOKEN&type=image`

## 安全与确认

- dry-run 不联网、不需要凭据，可随时运行。
- 真正发送必须同时传入 `--send --confirm-create-draft`，并且执行者已在发送前获得用户即时确认。
- 凭据只放在环境变量或受控密钥服务中，不写入文件。
- 创建草稿是外部写操作，但不是公开发布。更新、删除、发布和群发需要各自单独授权。
- GIF 默认保留以支持公众号内可见动效；WebP 会转换为静态 PNG。若当前账号接口拒绝 GIF，脚本或接口会失败，应改为静态 PNG 或由公众号后台手工上传，不要用未验证的绕过方式。
