# Vision Pay Agent Platform

Vision Pay 是一个基于 YOLOv11 的视觉识别购物结算系统。当前项目已经完成到 Day 6：数据集导入与验证、YOLO 本地训练服务、训练监控 API、前端 ECharts 训练曲线页面。

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

```powershell
cd D:\code\Git\Agent\agent-platform
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
REDIS_HOST=localhost
REDIS_PORT=6379
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

前端请求封装使用 `baseURL: /api`，Vite 会把 `/api/*` 代理到 `http://localhost:8000`。

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

### 后端

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pytest -q
```

### 前端

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
