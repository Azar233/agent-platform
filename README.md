# VisionPay Agent Platform

基于 YOLOv11 的零售商品自动结账智能体平台（ACO）。融合 LangChain/LangGraph 智能体框架与 YOLOv11 目标检测模型，依托 Retail Product Checkout Dataset 提供的细粒度图像数据，实现收银台多商品堆叠场景下的自动定位、精准品类识别与购物结算清单生成。

**核心能力：**
- 🔍 **商品定位** — 输入收银台真实多商品堆叠图像，自动定位图像中每个商品
- 🏷️ **品类识别** — 精准识别商品的细分品类（种类繁多、外观相似、相互遮挡）
- 🧾 **自动结算** — 生成最终购物结算清单，实现高效准确的自动化结算

## 技术栈

| 层级 | 技术 |
| ---- | ---- |
| 后端框架 | FastAPI + Uvicorn |
| 训练/检测 | Ultralytics YOLOv11 + OpenCV |
| 智能体 | LangChain + LangGraph + OpenAI API |
| 数据库 | PostgreSQL 15 + Pgvector |
| 缓存 | Redis 7 |
| 对象存储 | MinIO |
| 前端 | Vue 3 + Vite + Element Plus + ECharts |
| 容器 | Docker Compose |

## 环境要求

| 工具 | 建议版本 | 验证命令 |
| ---- | -------- | -------- |
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| Docker Desktop | 24+ | `docker --version` |
| Docker Compose | 2+ | `docker compose version` |

## 快速启动

所有命令默认在项目根目录执行：

### 1. 克隆项目

```bash
git clone https://github.com/Azar233/agent-platform
cd agent-platform
```

### 1. 启动基础服务

```powershell
docker compose up -d postgres redis minio
docker compose ps
```

基础服务：

| 服务 | 地址 | 用途 |
| ---- | ---- | ---- |
| PostgreSQL | `localhost:5432` | 用户、场景、训练任务和指标 |
| Redis | `localhost:6379` | 缓存和后续对话历史 |
| MinIO API | `localhost:9000` | 图片和模型文件存储 |
| MinIO Console | <http://localhost:9001> | 存储桶管理，默认 `minioadmin/minioadmin` |

后端 `.env` 中的 `DB_NAME`、`DB_USER`、`DB_PASSWORD` 必须和当前 PostgreSQL 容器实际创建的数据库一致。当前代码默认偏向 Vision Pay 配置：

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vp_agent
DB_USER=vp_admin
DB_PASSWORD=vp_admin
DATABASE_URL=postgresql://vp_admin:vp_admin@localhost:5432/vp_agent

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=vp-images
```

如果你不修改 `docker-compose.yml`，但 compose 中仍是 `my_agent/my_admin`，就要么把 `backend/.env` 改回 `my_agent/my_admin`，要么重建数据库容器并确保里面存在 `vp_agent/vp_admin`。

### 2. 启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

验证：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/health/detail
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

### 3. 启动前端

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

访问：

```text
http://127.0.0.1:5173
```

**`.env` 关键配置项**：

```env
# 后端 API 地址（Vite 开发服务器代理目标）
VITE_API_BASE_URL=http://localhost:8000

# 应用名称
VITE_APP_TITLE=VisionPay Agent Platform

# MinIO 文件访问地址
VITE_MINIO_URL=http://localhost:9000
```

启动前端开发服务器：

```bash
npm run dev
```

访问：<http://localhost:5173>

**前端页面路由**：

| 路由 | 页面 | 说明 |
| ---- | ---- | ---- |
| `/login` | 登录页 | 用户登录表单 |
| `/register` | 注册页 | 用户注册表单 |
| `/chat` | 智能对话 | Day 11 完善 |
| `/detection` | 检测工作台 | Day 8 完善 |
| `/training` | 模型训练 | Day 6 完善 |
| `/history` | 历史记录 | Day 10 完善 |
| `/dashboard` | 数据看板 | Day 10 完善 |

> 未登录状态下访问任何受保护页面会自动跳转到 `/login`；已登录用户访问登录/注册页会自动跳转到首页。

---

## 数据集导入流程

训练数据统一放在：

```text
backend/datasets/vision_pay/
```

标准 YOLO 目录结构：

```text
backend/datasets/vision_pay/
├── data.yaml
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

### 方式一：单个 COCO JSON + images 目录

适用于：

```text
dataset/
├── images/
└── instances_train2019.json
```

执行：

```powershell
cd D:\code\Git\Agent\agent-platform\backend

python tools\convert_coco.py `
  --source D:\path\to\dataset `
  --json instances_train2019.json `
  --output datasets\vision_pay `
  --train-ratio 0.8 `
  --val-ratio 0.1 `
  --test-ratio 0.1 `
  --seed 42 `
  --clean
```

### 方式二：COCO 已分好 train/val/test

适用于：

```text
dataset/
├── train2019/
├── val2019/
├── test2019/
├── instances_train2019.json
├── instances_val2019.json
└── instances_test2019.json
```

执行：

```powershell
cd D:\code\Git\Agent\agent-platform\backend

python tools\convert_coco_splits.py `
  --source D:\path\to\dataset `
  --train-dir train2019 `
  --val-dir val2019 `
  --test-dir test2019 `
  --train-json instances_train2019.json `
  --val-json instances_val2019.json `
  --test-json instances_test2019.json `
  --output datasets\vision_pay `
  --clean
```

### 验证和可视化

导入完成后先验证：

```powershell
cd D:\code\Git\Agent\agent-platform\backend
python tools\verify_dataset.py datasets\vision_pay
```

如果提示 bbox 越界或坐标格式问题：

```powershell
python tools\fix_bbox.py datasets\vision_pay
python tools\verify_dataset.py datasets\vision_pay
```

抽样可视化标注：

```powershell
python tools\visualize_annotations.py --count 10 --output datasets\vision_pay\vis_output
python tools\visualize_annotations.py --grid --output datasets\vision_pay\vis_output\overview.jpg
```

`data.yaml` 是 YOLO 训练入口文件，记录数据集根目录、训练/验证/测试图片目录、类别数量和类别名称。训练服务默认查找：

```text
backend/datasets/vision_pay/data.yaml
```

如果合作者从其他电脑复制了已经生成好的 `datasets/vision_pay`，需要确认 `data.yaml` 里的 `path` 指向当前电脑真实路径；最稳妥的方式是重新运行导入脚本生成。

## 跑通一次训练

训练链路依赖 4 个前置条件：

1. Docker 中 PostgreSQL、Redis、MinIO 已启动。
2. 后端已执行 `alembic upgrade head`。
3. `backend/datasets/vision_pay/data.yaml` 存在且 `verify_dataset.py` 通过。
4. 数据库中存在一个 `DetectionScene`，前端创建训练任务时需要填写它的 `scene_id`。

### 1. 创建 Vision Pay 场景

如果数据库里还没有场景，在 `backend/` 目录执行：

```powershell
python -c "from app.database.session import SessionLocal; from app.entity.db_models import DetectionScene; db=SessionLocal(); s=db.query(DetectionScene).filter_by(name='vision_pay').first(); s=s or DetectionScene(name='vision_pay', display_name='Vision Pay', description='视觉识别购物结算系统', category='retail', class_names=['product']); db.add(s); db.commit(); db.refresh(s); print('scene_id=', s.id); db.close()"
```

记录输出的 `scene_id`，后面前端新建训练任务要用。这里的 `class_names` 只是场景元信息；YOLO 训练实际使用的类别数量和类别名来自 `datasets/vision_pay/data.yaml`。

### 2. 注册和登录

可以在前端页面注册，也可以用 PowerShell 调接口：

```powershell
$body = @{username="trainer";email="trainer@example.com";password="123456"} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/auth/register -ContentType "application/json" -Body $body

$body = @{username="trainer";password="123456"} | ConvertTo-Json
$login = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/auth/login -ContentType "application/json" -Body $body
$token = $login.access_token
```

### 3. 用 API 启动一次小训练

第一次建议只跑 1 个 epoch，先验证流程：

```powershell
$headers = @{Authorization="Bearer $token"}
$body = @{
  scene_id = 1
  model_name = "yolov11n"
  epochs = 1
  batch_size = 2
  img_size = 640
  device = "cpu"
  optimizer = "SGD"
  lr0 = 0.01
  dataset_path = "datasets/vision_pay"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/training/start -Headers $headers -ContentType "application/json" -Body $body
```

把 `scene_id = 1` 换成上一节实际输出的值。

训练服务会在后台线程中调用 Ultralytics，项目内部模型名 `yolov11n` 会映射为 Ultralytics 权重 `yolo11n.pt`。首次训练可能需要联网下载权重；如果下载失败，可以手动把 `yolo11n.pt` 放到后端工作目录或 Ultralytics 缓存位置后重试。

训练输出目录：

```text
backend/runs/train/task_<task_uuid>/
├── results.csv
├── weights/
│   ├── best.pt
│   └── last.pt
└── ...
```

### 4. 前端启动训练并查看图表

1. 启动后端：`cd backend && uvicorn main:app --host 127.0.0.1 --port 8000 --reload`
2. 启动前端：`cd frontend && npm run dev -- --host 127.0.0.1`
3. 打开 <http://127.0.0.1:5173>
4. 注册或登录用户。
5. 进入左侧「模型训练」页面。
6. 点击「新建训练任务」。
7. 填写参数：

```text
检测场景: 上面创建的 scene_id
基础模型: YOLOv11n
训练轮数: 1 或 5
批次大小: 2 或 4
图像尺寸: 640
训练设备: CPU
优化器: SGD
初始学习率: 0.01
数据集目录: datasets/vision_pay
```

8. 点击「启动训练」。
9. 在任务列表点击「监控」。

前端训练监控页会每 5 秒轮询：

| 接口 | 作用 |
| ---- | ---- |
| `GET /api/training/tasks` | 获取训练任务列表 |
| `GET /api/training/status/{task_id}` | 获取任务状态和最新 epoch 指标 |
| `GET /api/training/metrics/{task_id}` | 获取所有 epoch 指标 |

图表说明：

| 图表 | 指标 |
| ---- | ---- |
| 训练损失曲线 | `Box Loss`、`Cls Loss`、`DFL Loss` |
| 评估指标曲线 | `mAP@50`、`mAP@50-95`、`Precision`、`Recall` |

训练完成后，任务状态会变为「已完成」，可以点击「结果」下载 `results.csv`。

### 5. 训练相关 API

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| `POST` | `/api/training/start` | 创建并启动训练任务 |
| `GET` | `/api/training/tasks` | 获取当前用户训练任务 |
| `GET` | `/api/training/status/{task_id}` | 查询任务状态和最新指标 |
| `GET` | `/api/training/metrics/{task_id}` | 查询训练指标历史 |
| `POST` | `/api/training/stop/{task_id}` | 停止运行中的训练任务 |
| `GET` | `/api/training/results/{task_uuid}` | 下载 `results.csv` |

所有训练接口都需要登录后的 JWT：`Authorization: Bearer <token>`。

## 项目结构

```text
agent-platform/
├── docker-compose.yml
├── README.md
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── health.py
│   │   │   └── training.py
│   │   ├── config/
│   │   │   └── settings.py
│   │   ├── core/
│   │   │   ├── exceptions.py
│   │   │   ├── logger.py
│   │   │   └── security.py
│   │   ├── database/
│   │   │   └── session.py
│   │   ├── entity/
│   │   │   ├── db_models.py
│   │   │   └── schemas.py
│   │   ├── middleware/
│   │   │   └── request_logger.py
│   │   ├── services/
│   │   │   └── user_service.py
│   │   ├── storage/
│   │   │   └── minio_client.py
│   │   └── training/
│   │       ├── data_converter.py
│   │       ├── dataset_splitter.py
│   │       └── training_service.py
│   ├── tools/
│   │   ├── convert_coco.py
│   │   ├── convert_coco_splits.py
│   │   ├── fix_bbox.py
│   │   ├── verify_dataset.py
│   │   └── visualize_annotations.py
│   ├── datasets/
│   │   └── vision_pay/
│   └── runs/
│       └── train/
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── api/
        │   ├── auth.js
        │   └── training.js
        ├── assets/
        │   └── styles/
        ├── components/
        │   └── layout/
        ├── router/
        │   └── index.js
        ├── stores/
        ├── utils/
        │   ├── markdown.js
        │   ├── request.js
        │   └── stream.js
        └── views/
            ├── ChatPage.vue
            ├── DashboardPage.vue
            ├── DetectionPage.vue
            ├── HistoryPage.vue
            ├── LoginPage.vue
            ├── RegisterPage.vue
            └── TrainingPage.vue
```

`backend/datasets/`、`backend/runs/`、`backend/.ultralytics/`、模型权重和日志属于本地运行产物，不提交 Git。


## 常用命令

### Docker

```powershell
docker compose up -d postgres redis minio
docker compose ps
docker compose logs -f postgres
docker compose logs -f redis
docker compose logs -f minio
docker compose down
```

### 后端开发

```bash
cd backend
.venv\Scripts\activate         # 激活虚拟环境（Windows）
python main.py                 # 启动后端（端口 8000）
alembic revision --autogenerate -m "描述"  # 生成迁移
alembic upgrade head           # 执行迁移
alembic downgrade -1           # 回滚上一版本
```

### 前端开发

```bash
cd frontend
npm install                    # 安装依赖
npm run dev                    # 启动开发服务器（端口 5173）
npm run build                  # 构建生产版本
npm run preview                # 预览生产构建
```

### 服务验证

```bash
# 验证 Redis
docker compose exec redis redis-cli ping
# 期望：PONG

# 验证 PostgreSQL
docker compose exec postgres psql -U vp_admin -d vp_agent -c "SELECT version();"

# 验证 MinIO — 浏览器访问 http://localhost:9001 （见下方 MinIO Console 链接）
```

---

## 环境验证清单

### 基础环境

```bash
git --version                  # ✅ git version 2.x.x
python --version               # ✅ Python 3.10+
node --version                 # ✅ v18+
docker --version               # ✅ Docker version 24.0+
docker compose version         # ✅ Docker Compose v2.x+
docker compose ps              # ✅ 所有服务状态为 Up / healthy
```

### API 接口验证（PowerShell）

```powershell
# 1. 基础健康检查
Invoke-RestMethod -Uri http://localhost:8000/api/health
# 预期：{"status":"healthy","app_name":"VisionPay Agent Platform","version":"0.1.0"}

# 2. 详细健康检查（数据库 + Redis + MinIO 连通性）
Invoke-RestMethod -Uri http://localhost:8000/api/health/detail
# 预期：{"code":200,"message":"ok","data":{"status":"healthy",...}}

# 3. 注册用户
$body = @{username="verify_user";email="verify@test.com";password="123456"} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/auth/register -ContentType "application/json" -Body $body
# 预期：返回 201，包含用户信息

# 4. 登录获取 Token
$body = @{username="verify_user";password="123456"} | ConvertTo-Json
$resp = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/auth/login -ContentType "application/json" -Body $body
$resp.access_token
# 预期：输出 access_token 字符串

# 5. 用 Token 获取当前用户信息（用上一步输出的 Token 替换 YOUR_TOKEN）
Invoke-RestMethod -Uri http://localhost:8000/api/auth/me -Headers @{"Authorization"="Bearer YOUR_TOKEN"}
# 预期：返回当前用户信息

# 6. 全局异常处理验证 — 故意发送过短的用户名（不足 3 字符）
$body = @{username="ab";email="test@test.com";password="123456"} | ConvertTo-Json
try { Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/auth/register -ContentType "application/json" -Body $body } catch { $_.Exception.Message }
# 预期：返回 422 + 友好 JSON 错误（非原始 500 错误）
```

### 后端

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pytest -q
```

### 测试框架验证

```bash
# 后端测试（pytest）
cd backend
pytest
# 预期：13 passed（11 auth + 2 health）

# 前端测试（Vitest）
cd frontend
npm run test:run
# 预期：5 passed（4 request.test.js + 1 AppHeader.test.js）
```

### 日志系统验证

```bash
# 查看后端日志文件（发起几次 API 请求后检查）
cat backend/logs/app.log
# 预期：看到格式化日志，包含时间戳 | 级别 | 模块:函数:行号 | 消息

# 观察请求日志中间件输出（后端终端中应包含）
# 预期格式：POST /api/auth/login from 127.0.0.1 → 200 (12.34ms)
```

### 前端页面验证

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1
npm run build
```

### 数据集

```powershell
cd backend
python tools\verify_dataset.py datasets\vision_pay
python tools\fix_bbox.py datasets\vision_pay
python tools\visualize_annotations.py --count 10 --output datasets\vision_pay\vis_output
```

## 验证清单

提交 Day6 更新前建议至少跑：

```powershell
cd D:\code\Git\Agent\agent-platform\backend
pytest -q

cd D:\code\Git\Agent\agent-platform\frontend
npm run build
```

运行环境检查：

| 检查项 | 命令或页面 | 预期 |
| ------ | ---------- | ---- |
| Docker 服务 | `docker compose ps` | PostgreSQL、Redis、MinIO 为 Up/healthy |
| 后端健康 | `http://127.0.0.1:8000/api/health` | 返回 `status=healthy` |
| 详细健康 | `http://127.0.0.1:8000/api/health/detail` | database、redis、minio 正常 |
| 前端 | `http://127.0.0.1:5173` | 可打开登录页 |
| 数据集 | `python tools\verify_dataset.py datasets\vision_pay` | 无格式错误 |
| 训练页 | `/training` | 可新建任务、查看任务列表和曲线 |

## 常见问题

### 后端连不上 PostgreSQL

优先检查三处是否一致：

```text
docker-compose.yml 中 POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD
backend/.env 中 DB_NAME / DB_USER / DB_PASSWORD
当前 Docker volume 里已经初始化过的数据库
```

PostgreSQL 官方镜像只会在数据卷第一次创建时初始化数据库。修改 `docker-compose.yml` 后，如果旧 volume 还在，数据库名和用户不会自动变化。

### `/api/training/start` 返回 `data.yaml 不存在`

确认数据集目录存在：

```powershell
cd backend
Test-Path datasets\vision_pay\data.yaml
python tools\verify_dataset.py datasets\vision_pay
```

前端训练表单里的「数据集目录」使用相对路径：

```text
datasets/vision_pay
```

### 首次训练卡在下载权重

`yolov11n` 会映射为 Ultralytics 的 `yolo11n.pt`。首次训练可能联网下载权重，网络不可用时会失败。可以提前手动下载 `yolo11n.pt` 并放到后端工作目录或 Ultralytics 缓存目录后重试。

### 前端没有训练曲线

先确认任务不是刚创建还没进入第一个 epoch。曲线数据来自 `training_metrics` 表，训练 callback 或最终 `results.csv` 解析后才会出现。若任务状态为 `failed`，查看后端终端日志和 `training_tasks.error_message`。

### 点击「结果」下载失败

只有 `completed` 状态且 `backend/runs/train/task_<task_uuid>/results.csv` 存在时才可下载。下载接口需要登录态，前端会通过 Axios 自动携带 JWT。
