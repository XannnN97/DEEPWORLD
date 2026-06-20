# DEEPWORLD

> 影视制作中间文件转换工具 — EDL/SRT/FCPXML/Resolve XML → Word/Excel/CSV

![Test](https://github.com/XannnN97/DEEPWORLD/actions/workflows/test.yml/badge.svg)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 功能

- 解析 EDL（CMX3600）、SRT 字幕、FCPXML、DaVinci Resolve XML 等多种剪辑中间格式
- 导出为 Word（.docx）、Excel（.xlsx）、CSV 便于制表/报告/校对
- Web 界面（FastAPI + uvicorn），浏览器即可上传转换
- CLI 调用：`deepworld` 命令（需 pip install）

## 快速开始

```bash
pip install -e ".[dev]"
deepworld
# → 访问 http://localhost:8090
```

## 测试

```bash
pytest -v
```

---

## 协作规范

此项目也是 **Windows Claude Code（生产者）↔ WSL2 OpenClaw（审核者）** 的 PR 异步协作测试载体。

### 角色
- **生产者**（Claude Code / Windows）：创建分支 → 改代码 → commit → push → 创建 PR
- **审核者**（OpenClaw / WSL2）：Review PR → Approve → Squash Merge → 删除远程分支

### 详细流程

1. 生产者创建分支 → commit → push
2. 生产者创建 PR，自动指派给审核者
3. 审核者 Review → Approve → Merge
4. 完成一次协作循环

### 规范
- 分支命名：`feat/<描述>`、`fix/<描述>`、`chore/<描述>`
- commit message：英文，简洁描述变更意图
- PR title：英文
- 至少 1 个 Approval 才能合并
- 合并方式：Squash and Merge
- 合并后删除远程分支

详见 [CLAUDE.md](CLAUDE.md) 和 [docs/workflow.md](docs/workflow.md)。

## 目录结构

```
DEEPWORLD/
├── deepworld/           # 核心包
│   ├── core/            # 数据模型、枚举、时间码
│   ├── parsers/         # 解析器（EDL, SRT, FCPXML, Resolve XML）
│   ├── exporters/       # 导出器（Word, Excel, CSV）
│   ├── converter/       # 转换流水线
│   └── web/             # Web 界面（FastAPI）
├── tests/               # pytest 测试
├── samples/             # 示例输入文件
├── docs/                # 文档
│   └── workflow.md      # 协作流程文档
├── CLAUDE.md            # Claude Code 项目规范
├── .github/workflows/   # CI/CD
├── LICENSE
└── README.md
```

## 许可

MIT License — 详见 [LICENSE](LICENSE)。
