# GEO 品牌查询 (geo-brand-search)

输入搜索问题 → Agent 打开 DeepSeek 搜索 → AI 分析品牌排名 + 提取信源 → 前端查看结果。

## 功能特性

- **品牌搜索**：输入问题 + 可选品牌关键词，Agent 自动打开 DeepSeek 搜索
- **双排名分析**：综合排名（AI 驱动）+ 提及顺序排名（按 AI 回答中首次出现顺序）
- **品牌排名定位**：填写品牌关键词后，显示该品牌在两个排名中各排第几名
- **信源提取**：自动抓取 DeepSeek 信源面板中的网站列表（logo / 标题 / 日期 / 摘要）
- **详情页**：点击任务卡片进入详情，信源分页展示，支持 URL 直链 `/{taskId}`
- **长截图**：全页滚动截图保存
- **输入过滤**：自动拒绝非品牌/产品评价类查询

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
│   │   ├── runner.py         # Agent 入口 & 编排 (含排名分析)
│   │   ├── context.py        # 运行时上下文 (浏览器/页面引用)
│   │   ├── input_filter.py   # 输入过滤 & 品牌校验 (DeepSeek AI)
│   │   ├── state.py          # 运行状态 & 步骤结果
│   │   ├── errors.py         # 自定义异常
│   │   ├── timeout.py        # 超时管理
│   │   └── logger.py         # 结构化日志
│   ├── ranking/              # 排名分析 (综合排名 + 提及顺序排名)
│   │   ├── runner.py         # RankingRunner & 品牌排名查询
│   │   ├── api_client.py     # DeepSeek API 调用封装
│   │   ├── react/loop.py     # ReAct 循环引擎
│   │   ├── planner/          # 规划器 (计划模板 & 执行器)
│   │   ├── tools/llm_api.py  # LLM 工具接口
│   │   └── harness/cleaner.py  # JSON 提取 & 校验 & Markdown 转换
│   ├── tools/                # Playwright 工具层
│   │   ├── browser.py        # 浏览器生命周期
│   │   ├── navigation.py     # 页面导航 & 加载等待
│   │   ├── input.py          # 输入提交 & 响应/信源提取
│   │   ├── screenshot.py     # 长截图拼接
│   │   └── sidebar.py        # 侧边栏操作
│   └── main.py               # CLI 入口 (--task-id --query --brand-keyword)
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

1. 在输入框中输入问题（如"哪个手机好"），可选填品牌关键词（如"华为"）
2. Agent 自动打开 Chromium 浏览器访问 DeepSeek
3. **首次使用需要在浏览器中登录 DeepSeek 账号**，登录状态会持久保存
4. 登录后 Agent 自动输入问题、等待回答、提取信源、分析排名
5. 任务完成后点击"查看详情"进入详情页，可查看回复 / 排名 / 截图 / 信源列表
6. 填写品牌关键词时，详情页顶部显示品牌在两个排名中的位置

## Agent 工作流 (LangGraph)

```
START → launch → navigate → wait_loaded → login → input → wait_response
                                                              ↓
END ← extract (响应 + 信源) ← screenshot ←────────────── sidebar
                                   ↓
                              ranking_analysis
                              (综合排名 + 提及顺序排名)
```

每个节点失败时通过条件边路由到 `handle_error` → END，sidebar 允许失败继续。

## Agent 独立运行

```bash
cd agent

# 基本搜索
python -m agent.main --task-id test-001 --query "什么是大语言模型"

# 带品牌关键词（排名分析 + 品牌定位）
python -m agent.main --task-id test-001 --query "哪个手机好" --brand-keyword "华为"

# 无头模式
python -m agent.main --task-id test-001 --query "哪个手机好" --headless
```
