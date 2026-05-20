# QuantDash

QuantDash 是一个面向个人投资者的轻量级量化看板。项目目标是把自选股、实时行情、K 线、指数概览和后续舆情/新闻/财务数据整合到一个响应式工作台里，辅助做数据驱动的投资决策。

当前版本已经实现：

- A 股自选池，支持输入 6 位股票代码查询真实行情后添加。
- 个股实时 quote：价格、涨跌幅、成交量、成交额、最高/最低、开盘、昨收。
- 日 K / 周 K 图表，包含 MA5、MA10 和成交量。
- 顶部市场指数：上证指数、深证成指、创业板指、科创 50。
- 前后端分离开发结构，使用 Taskfile 一键并行启动。

仍是占位/待接入真实数据的模块：

- 公告
- 全网舆情热词
- 实时逐笔成交
- 财务估值指标中的 PE/PB 等增强字段

## 技术架构

项目目录：

```text
.
├── backend/                 # FastAPI 行情数据服务
│   ├── app/main.py          # FastAPI 入口
│   └── app/services/        # 数据源适配与清洗
├── frontend/                # Next.js 前端应用
│   ├── src/app/             # App Router 页面与 BFF route handlers
│   ├── src/components/      # 看板与图表组件
│   └── src/lib/             # 前端类型与请求封装
├── docs/                    # 产品文档
└── Taskfile.yml             # 开发任务管理
```

前端：

- Next.js 16 App Router
- React 19
- Tailwind CSS
- Apache ECharts
- lucide-react 图标

后端：

- FastAPI
- Uvicorn
- Pylint 后端代码异味检测
- AkShare A 股行情、K 线、指数、盘口和新闻数据适配

数据链路：

```text
Browser
  -> Next.js UI
  -> Next.js Route Handler (/api/*)
  -> FastAPI Backend (http://127.0.0.1:8000)
  -> AkShare / NewsNow data providers
```

Next.js 的 BFF 路由默认通过 `MARKET_API_BASE_URL` 请求后端；未设置时默认是：

```text
http://127.0.0.1:8000
```

## 启动方式

项目使用 [Task](https://taskfile.dev/) 管理开发命令。需要先安装 `task`：

```bash
brew install go-task
```

首次启动前安装依赖：

```bash
task install
```

如果只需要安装后端依赖：

```bash
task backend:install
```

如果只需要安装前端依赖：

```bash
task frontend:install
```

启动完整开发环境：

```bash
task dev
```

该命令会并行启动：

- 前端：http://localhost:3000
- 后端：http://127.0.0.1:8000

后端健康检查：

```bash
curl http://127.0.0.1:8000/health
```

示例行情接口：

```bash
curl http://localhost:3000/api/stock/quote/600519
curl "http://localhost:3000/api/stock/kline/600519?type=daily"
curl http://localhost:3000/api/market/indexes
```

## 常用命令

```bash
task --list       # 查看所有任务
task dev          # 并行启动前后端
task check        # 后端语法/Pylint 检查 + 前端 lint/build
task backend:lint # 后端 Pylint 异味检测
task lint         # 前端 lint
task build        # 前端生产构建
```

## 备注

后端依赖默认安装在项目根目录的 `.venv` 中，不会写入系统 Python 环境。后端开发依赖声明在 `backend/requirements-dev.txt` 中，包含 Pylint。前端依赖位于 `frontend/node_modules`。
