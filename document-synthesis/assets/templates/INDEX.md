# 文档索引

> 人工与 LLM 的默认入口。最后更新：`<YYYY-MM-DD>`；机器路由以 [`llm-manifest.json`](llm-manifest.json) 为准。

## 默认读取边界

- 默认扫描：`<current-entry-list>`。
- 默认排除：drafts、history、archive、snapshots。
- 非当前资料只有在用户明确要求版本对比、迁移、恢复或审计时读取。

## 任务 / 功能 → 必读文档

| 任务或功能 | 当前权威入口 | 技术债 |
|---|---|---|
| `<scope>` | `<current-document-link>` | `<td-link-or-none>` |

## 产品需求与设计

| 入口 | 内容 |
|---|---|
| [`design/README.md`](design/README.md) | PRD、开发步骤、实施计划和审查 |

## 工程协作资料

| 入口 | 内容 |
|---|---|
| [`progress/`](progress/) | 开发进度 |
| [`testing/`](testing/) | 清单、指南和报告 |
| [`VERSIONS.md`](VERSIONS.md) | 产品版本 |

## 契约、缺口与技术债

- 当前契约：[`contract.md`](contract.md)
- 技术债：[`tech-debt.md`](tech-debt.md)
- 已知缺口：`<path-or-needs-input>`

## 维护规则

- 同一范围只保留一个当前权威入口。
- 被替代文档移出默认读取，但保留在 history/archive。
- 缺少证据的内容标记 `needs-input` 或 `needs-review`。
