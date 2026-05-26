# GEO 品牌查询 (geo-brand-search)

自动化搜索工具：前端输入问题 → Agent 打开 DeepSeek 搜索 → 长截图保存 → 前端查看结果。

## 技术栈

**前端**

| 技术 | 版本 |
|------|------|
| React | 19.2 |
| TypeScript | 6.0 |
| Vite | 8.0 |
| react-markdown | 10.1 |
| remark-gfm | 4.0 |

**后端**

| 技术 | 版本 |
|------|------|
| Python | 3.14 |
| FastAPI | 0.136 |
| Uvicorn | 0.42 |
| SQLAlchemy | 2.0 |
| Pydantic | 2.12 |
| SQLite (aiosqlite) | 0.20 |

**Agent**

| 技术 | 版本 |
|------|------|
| Python | 3.14 |
| LangGraph | 1.2 |
| Playwright | 1.58 |
| Pillow | 12.2 |
| NumPy | 2.4 |

**AI 服务**: DeepSeek Chat

## 项目结构

```
geo-brand-search/
├── frontend/                 # React + TypeScript + Vite
│   └── src/
│       ├── api/              # API 客户端 & WebSocket 类型
│       ├── components/       # UI 组件
│       └── hooks/            # 自定义 hooks
├── backend/                  # Python + FastAPI + SQLite
│   └── app/
│       ├── api/              # REST 路由 & WebSocket
│       ├── models/           # SQLAlchemy 模型
│       ├── schemas/          # Pydantic 模型
│       └── services/         # 业务逻辑 & Agent 桥接
├── agent/                    # LangGraph + Playwright Agent
│   ├── graph/                # LangGraph 状态图
│   │   ├── state.py          # 图状态定义 (TypedDict)
│   │   ├── nodes.py          # 节点工厂函数
│   │   └── builder.py        # 图构建 & 条件边
│   ├── harness/              # Agent 运行时基础设施
│   │   ├── runner.py         # Agent 入口 & 编排
│   │   ├── context.py        # 运行时上下文 (浏览器/页面引用)
│   │   ├── tool_registry.py  # 工具注册表
│   │   ├── state.py          # 运行状态 & 步骤结果
│   │   ├── errors.py         # 自定义异常
│   │   ├── timeout.py        # 超时管理
│   │   └── logger.py         # 结构化日志
│   ├── tools/                # Playwright 工具层
│   │   ├── browser.py        # 浏览器生命周期
│   │   ├── navigation.py     # 页面导航 & 加载等待
│   │   ├── input.py          # 输入提交 & 响应提取
│   │   ├── screenshot.py     # 长截图拼接
│   │   └── sidebar.py        # 侧边栏操作
│   └── main.py               # CLI 入口
└── browser_data/             # Chromium 持久化用户数据
```

## 快速启动

### 1. 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# Agent
cd ../agent
pip install -r requirements.txt
playwright install chromium

# 前端
cd ../frontend
npm install
```

### 2. 启动后端

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 启动前端

```bash
cd frontend
npm run dev
```

### 4. 打开浏览器

访问 `http://localhost:5173`

## 使用方式

1. 在输入框中输入问题，点击"搜索"
2. Agent 自动打开 Chromium 浏览器访问 DeepSeek
3. **首次使用需要在浏览器中登录 DeepSeek 账号**，登录状态会持久保存
4. 登录后 Agent 自动输入问题、等待回答、长截图
5. 任务完成后点击"查看回复"查看思考过程 + AI 回答

## Agent 工作流 (LangGraph)

```
START → launch → navigate → wait_loaded → login → input → wait_response
                                                              ↓
END ← extract ← screenshot ←────────────────────────────── sidebar
```

每个节点失败时通过条件边路由到 `handle_error` → END，sidebar 允许失败继续。

## Agent 独立运行

```bash
cd agent

# 有头模式（默认，可见浏览器窗口）
python -m agent.main --task-id test-001 --query "什么是大语言模型"

# 无头模式
python -m agent.main --task-id test-001 --query "什么是大语言模型" --headless
```
