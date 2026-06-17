# DEEPWORLD

> 协作验证项目：Windows Claude Code（生产者）↔ WSL2 OpenClaw（审核者）的 PR 协作流程测试。

## 目标

验证两个 Agent 通过 GitHub PR 进行异步协作的完整链路：
- Windows 端 Claude Code：**生产者** — 提交代码变更，创建 PR
- WSL2 端 OpenClaw：**审核者** — Review 后合并 PR

## 协作流程

1. 生产者（Claude Code）在单独分支上开发 → commit → push
2. 生产者创建 PR → 自动指派给审核者
3. 审核者（OpenClaw）Review → Approve → Merge
4. 完成一次协作循环

## CLAUDE.md

[CLAUDE.md](CLAUDE.md) 包含项目规范和协作红线，两端 Agent 都应遵守。
