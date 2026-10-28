# TD Entry Template

Use this fallback only when drafting new debt entries without an established project template. Preserve the project's labels and ordering when present; include applicable fields without inventing content for irrelevant ones.

---

```markdown
### [TD-xxx] 简短标题（动词+对象，如"统计报表：缺按日 open_rate 字段"）

- **接口**：`METHOD /api/path`（及相关导出接口）；实现见 `path/to/service.py` → `function_name`；路由 `path/to/router.py` 中 `CONSTANT_NAME`。
- **问题**：当前代码的具体问题。说明缺了什么、错了什么，引用字段名/函数名/行号让问题可复现。
- **关联**：涉及的其他文件（如 `docs/contract.md` 对应小节、前端模板路径）。
- **当前处理**：代码目前实际的状态（不是应该怎样，是现在怎样）。
- **待处理**：
  1. 第一个需要做的具体事项（指向文件/函数/常量）
  2. 第二个事项
  3. ...（如涉及产品确认，注明"口径需产品确认：XXX"）
- **触发时机**：建议在什么条件/里程碑下排期，例如"与运营报表字段对齐时"。
- **风险等级**：**高 / 中 / 低**（一句话说明原因，如"缺列不影响现有逻辑"）
```

---

## Field writing rules

| Field | Rule |
|---|---|
| 接口 | For HTTP debt, include the method and path of affected endpoints. For non-HTTP debt, use the relevant module boundary or omit this field. |
| 问题 | Be specific: name the missing field, the wrong function, the inconsistency. Avoid vague phrases like "有问题". |
| 关联 | Only list files that are directly affected, not the whole project. |
| 当前处理 | Describe the *current* state, not the desired state. Useful for tracking drift over time. |
| 待处理 | Each item should be independently actionable. If an item needs external input, say so explicitly. |
| 触发时机 | Helps the team decide when to schedule. Tie to a business event or milestone, not just "when we have time". |
| 风险等级 | 高 = data loss / user-visible bug. 中 = maintainability / hidden inconsistency. 低 = cosmetic / future-proofing. |

## Numbering

Continue from the highest existing TD number + 1.
If the document has TD-001 through TD-009, the next new entry is TD-010.
