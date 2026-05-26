# GEO 品牌查询 (geo-brand-search)

自动化搜索工具：前端输入问题 → Agent 打开 DeepSeek 搜索 → 长截图保存 → 前端查看结果。

## 项目结构

```
geo-brand-search/
├── frontend/               # React + TypeScript + Vite
├── backend/           # Python + FastAPI + SQLite
├── agent/             # Playwright + ReAct + Plan&Execute
└── backend/data/screenshots/  # 截图存储目录
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
2. Agent 会自动打开 Chromium 浏览器访问 DeepSeek
3. **首次使用需要在浏览器中登录 DeepSeek 账号**，登录状态会持久保存
4. 登录后 Agent 自动输入问题、等待回答、长截图
5. 任务完成后点击"查看截图"查看结果

## Agent 独立运行

```bash
cd agent

# 有头模式（默认，可见浏览器窗口）
python -m agent.main --task-id test-001 --query "什么是大语言模型"

# 无头模式
python -m agent.main --task-id test-001 --query "什么是大语言模型" --headless
```
