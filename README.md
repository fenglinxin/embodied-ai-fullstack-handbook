# 具身智能工业级全栈工程落地手册

数据 → 模型 → 仿真 → 硬件 → 部署 → 产品化：六层全栈教程合集（53 篇）。

- 站点：`https://<你的用户名>.github.io/embodied-ai-fullstack-handbook/`
- 技术栈：MkDocs Material + GitHub Actions 自动构建部署
- 内容源：`docs/`（按六层归档）

## 配套代码库

除站点文章外，仓库根目录 `embodied-fullstack-code/` 内含 **45 个可运行代码包（第 1–44 章 + 评测工程）**：每包 L1 极简 Demo / L2 工程标准版 / L3 高阶优化版三个脚本 + README（参数白皮书、Top5 踩坑、改造指南），全部 Python 3.10+ 零第三方依赖，可直接下载运行。

- 目录：`embodied-fullstack-code/chapters/{data,model,simulation,hardware,deployment,evaluation}`
- 规范与进度：`embodied-fullstack-code/00-代码落地总规范.md`、`PROGRESS.md`
- 在线浏览：https://github.com/fenglinxin/embodied-ai-fullstack-handbook/tree/main/embodied-fullstack-code

## 本地预览

```bash
pip install -r requirements.txt
mkdocs serve
```

## 部署说明

1. 推送 `main` 分支后，GitHub Actions 会自动构建并发布；
2. 首次请在仓库 **Settings → Pages** 中把 Source 设为 **GitHub Actions**；
3. 站点地址即 `https://<用户名>.github.io/embodied-ai-fullstack-handbook/`。

## 目录

| 层 | 章节 | 目录 |
| --- | --- | --- |
| 数据层 | 第 1–12 章 | `docs/data-layer` |
| 模型层 | 第 13–24 章 | `docs/model-layer` |
| 仿真层 | 第 25–31 章 | `docs/simulation-layer` |
| 硬件层 | 第 32–37 章 | `docs/hardware-layer` |
| 部署层 | 第 38–44 章 | `docs/deployment-layer` |
| 产品产业层 | 第 45–52 章 | `docs/product-layer` |
