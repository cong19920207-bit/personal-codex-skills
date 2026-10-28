# 契约文档入口

- 文档 ID：`contract-index`
- 权威状态：`canonical`（只负责路由；正文以 `contract/current/` 为准）
- 机器入口：[`llm-manifest.json`](llm-manifest.json)

## 按功能路由

| 功能 | 当前权威文档 |
|---|---|
| `<scope>` | `<api-link>` · `<data-link>` · `<admin-ui-link-if-applicable>` |

## 共享约定

- `<shared-conventions-link>`
- `<auth-and-rbac-link>`

## 非默认来源

- `contract/drafts/`：未确认草案。
- `contract/history/`：被替代版本。
- `<known-gaps-link>`：已知缺口和待确认项。

## 维护规则

- 当前功能变化更新 `contract/current/` 与 manifest。
- 草案确认后再合并；被替代正文保留在 history。
