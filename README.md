# Bili Lucky

Bilibili 抽奖专栏解析、动态发现与子动态追踪工具。

## 原自动化入口

```bash
python3 article_choujiang.py
```

入口会读取 `BILI_COOKIE`、`article_id`、`MAILLQQ` 和 `MAILLSECRET` 等环境变量。

## 本地 UI

UI 使用 Flask 提供只读数据 API，React + Vite 提供液态玻璃风格界面。原有自动化入口保持不变。

### 安装与构建

需要 Python 3.8+ 和 Node.js 20+。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd ui
npm install
npm run build
cd ..
```

### 启动

```bash
python3 bili_ui.py
```

浏览器打开：<http://127.0.0.1:8765>

可选参数：

```bash
python3 bili_ui.py --host 127.0.0.1 --port 8765 --debug
```

### 前端开发模式

分别启动 Flask API 与 Vite：

```bash
# 终端 1
python3 bili_ui.py

# 终端 2
cd ui
npm run dev
```

开发页面：<http://127.0.0.1:5173>

## UI 工作流

1. 选择预设 Article UID，或输入自定义 UID。
2. 左栏选择 Article。
3. 中栏查看专栏解析出的抽奖动态。
4. 右栏查看从转发链恢复出的官方子动态。
5. 点击任意动态，查看文本、媒体、统计、关联 ID 与完整原始 JSON。
6. 勾选中栏或右栏动态，通过“一键关转评”批量执行关注、转发和评论。

批量关转评提交前会显示二次确认；每次最多处理 30 条，并按选择顺序串行执行。
