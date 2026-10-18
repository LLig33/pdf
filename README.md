# 纸译 PaperBridge

英文 / 日文 PDF 转简体中文的网站原型。FastAPI + PyMuPDF，原生响应式网页。

## 开发启动

```bash
cd /workspace/pdf
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
```

配置服务器环境变量后启用真实翻译（不要把密钥写进仓库或网页）：

- `TRANSLATION_API_KEY`：支持 OpenAI Chat Completions 的服务密钥。
- `TRANSLATION_BASE_URL`：默认 `https://api.openai.com/v1`。
- `TRANSLATION_MODEL`：默认 `gpt-4.1-mini`，须支持 JSON 对象输出。

不配置密钥仍可上传和逐页预览。翻译会将提取的文字发送至服务商，可能产生费用。图片不会发送至翻译服务。

## 能力与边界

支持最多 30 MB、100 页、带文字层的 PDF，自动识别英文与日文。按文字块翻译，在原位置嵌入简体中文；保留页面尺寸、图片及矢量图形。空间不足的块保留原文并提示。

当前是单进程本地开发版本：最多内存暂存 10 个文档，无持久化；手动删除或服务重启清空。文档地址采用随机令牌，请勿分享。扫描件需要先做 OCR，本版本尚未提供 OCR。复杂杂志的竖排、艺术字体、跨栏、彩色文字与精确字体匹配尚不保证，输出需人工校对。当前译文为黑色，细节排版并非无损复刻。

正式部署前需要增加身份认证、任务队列、文档定时清理、全局内存/并发限制、OCR 与页面版面分析。不要将本开发服务直接暴露到公网。

## 验证

```bash
.venv/bin/python -m unittest discover -s tests -v
```

测试使用本地模拟翻译服务验证导出流程，不调用付费模型；真实模型质量与密钥访问需要配置后单独验证。

## 部署到 Render

仓库包含 `render.yaml`（Blueprint）与非 root Docker 镜像。使用一个实例、一个 worker：文档暂存在进程内存中，不能多副本运行。健康检查为 `/healthz`。

1. 将当前工作区的项目文件提交并推送到你的 GitHub 仓库 `LLig33/pdf`。只有 GitHub 上已经包含项目文件和部署配置，Render 才能构建；仅连接空仓库无法部署。
2. 登录 https://dashboard.render.com ，选择 New → Blueprint，授权并选择该仓库及包含项目文件的分支。
3. 检查资源方案和费用。配置默认使用付费 Starter；创建前以 Render 显示的价格为准。本次未开通付费服务。
4. 在 Render 的安全环境变量输入框设置 `TRANSLATION_API_KEY`，然后创建服务。不要将密钥放入 YAML 或 Git。
5. 等待部署完成，在 Render 提供的 HTTPS 网站地址访问。浏览器弹出登录框时用户名为 `paperbridge`，密码为 Render 自动生成的 `SITE_PASSWORD`（可在该服务的 Environment 页面查看或更换）。
6. 检查 `/healthz` 返回 `{"status":"ok"}`，登录后上传小型文字层 PDF、翻译、预览并下载验证。真实翻译会使用你的 API 额度。

不要删除访问密码后直接开放此原型。当前适合受密码保护的小规模试用，不是多用户 SaaS。重启或重新部署会清空文档；长文档请求可能受平台超时限制。扫描件与复杂版面限制仍然存在。首次部署后需用实际文档验证，当前未完成 Render 端部署验证。
