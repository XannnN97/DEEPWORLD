# DEEPWORLD — 项目规范

## 角色
- **生产者（Claude Code / Windows）**：创建分支 → 改代码 → commit → push → 创建 PR
- **审核者（OpenClaw / WSL2）**：Review PR → Approve → Squash Merge → 删除远程分支

## Git 规范
- 分支命名：`feat/<描述>`、`fix/<描述>`、`chore/<描述>`
- commit message：英文，简洁描述变更意图
- PR title：英文，描述本次变更

## 红线
- 审核者不直接 push 到 main，所有变更走 PR
- PR 必须至少 1 个 Approval 才能合并
- 合并方式：Squash and Merge
- 合并后删除远程分支

## 网络
- GitHub 通过代理 127.0.0.1:7078 访问（Windows 端全局 git config 已配）
- WSL2 端需单独配置代理
