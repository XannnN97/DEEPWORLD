# 协作验证计划

验证 Windows Claude Code 与 WSL2 OpenClaw 之间的 PR 协作链路。

## 测试项

1. **生产者创建分支 + 提交**（Windows → GitHub）
2. **生产者创建 PR**（Windows → GitHub）
3. **审核者 Review + Approve**（WSL2 OpenClaw）
4. **审核者 Squash Merge + 删分支**（WSL2 OpenClaw）

## 协作流程图

```
Windows Claude Code          GitHub                WSL2 OpenClaw
      │                        │                       │
      ├─ git branch ──→        │                       │
      ├─ git commit ──→        │                       │
      ├─ git push ─────→       │                       │
      ├─ gh pr create ──→      │                       │
      │                        ├─ gh pr list ─────→    │
      │                        │←─ gh pr review ──┤    │
      │                        │←─ gh pr merge ───┤    │
      │                        │                       │
```

## 下一步

验证通过后可扩展：
- 自动化：用 scheduled task 自动拉取审核结果
- 冲突处理：生产者更新分支后重新请求 review
- 标签系统：用 labels 标记 PR 状态
