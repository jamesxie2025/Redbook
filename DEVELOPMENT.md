# 红墨 AI图文生成器 - 开发指南

## 项目概述

红墨是一个用于生成小红书风格图文内容的 AI 应用，支持文本和图像生成。

## 项目结构

```
.
├── backend/              # 后端代码 (Python/Flask)
├── frontend/             # 前端代码 (Vue 3/TypeScript)
├── docker/               # Docker 配置文件
├── history/              # 历史记录目录
├── output/               # 输出目录
├── .env                  # 环境变量配置文件
├── .gitignore            # Git 忽略文件
├── Dockerfile            # Docker 构建文件
├── docker-compose.yml    # Docker Compose 配置
├── pyproject.toml        # Python 项目配置
├── README.md             # 项目说明
└── DEVELOPMENT.md        # 开发指南 (本文件)
```

## 环境配置

### 1. 环境变量配置

项目使用 `.env` 文件来管理敏感配置信息。请参考 `.env` 文件中的说明配置您的 API 密钥和其他设置。

### 2. 配置文件

- `text_providers.yaml`: 文本生成服务商配置
- `image_providers.yaml`: 图片生成服务商配置

这两个文件支持使用环境变量，格式为 `${VARIABLE_NAME}`。

## 本地开发

### 前置要求

- Python 3.11+
- Node.js 18+
- pnpm
- uv

### 安装依赖

1. 后端依赖:
   ```bash
   uv sync
   ```

2. 前端依赖:
   ```bash
   cd frontend
   pnpm install
   ```

### 启动服务

#### 后端服务

```bash
uv run python -m backend.app
```

默认端口: `12398`

#### 前端服务

```bash
cd frontend
pnpm dev
```

默认端口: `5173`

### 一键启动

在项目根目录下，您可以使用启动脚本:

- **macOS/Linux**: `./start.sh`
- **Windows**: 双击 `start.bat`

## Docker 部署

### 构建镜像

```bash
docker build -t redink .
```

### 运行容器

```bash
docker run -d -p 12398:12398 \
  -v ./history:/app/history \
  -v ./output:/app/output \
  --env-file .env \
  redink
```

或者使用 docker-compose:

```bash
docker-compose up -d
```

## 配置说明

### 文本生成配置

在 `text_providers.yaml` 中配置:

```yaml
active_provider: openai  # 激活的服务商

providers:
  openai:
    type: openai_compatible
    api_key: ${OPENAI_API_KEY}  # 使用环境变量
    base_url: ${OPENAI_BASE_URL}
    model: gpt-4o
```

### 图片生成配置

在 `image_providers.yaml` 中配置:

```yaml
active_provider: gemini  # 激活的服务商

providers:
  gemini:
    type: google_genai
    api_key: ${GOOGLE_GEMINI_API_KEY}  # 使用环境变量
    model: gemini-3-pro-image-preview
    high_concurrency: false
```

## API 文档

启动后端服务后，API 文档可通过以下端点访问:

- 健康检查: `GET /api/health`
- 大纲生成: `POST /api/outline`
- 内容生成: `POST /api/generate`
- 图片服务: `GET /api/images/<filename>`

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 协议进行开源。
