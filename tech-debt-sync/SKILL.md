---
name: tech-debt-sync
description: |
  Audits and synchronizes a technical debt document (TD-xxx format) against the actual codebase.
  Use when the user explicitly asks to audit or synchronize technical debt, including:
  - Check if existing tech debt items are still valid or already resolved
  - Find new technical debt in the code that isn't documented yet
  - Update or regenerate a tech-debt.md file based on current code
  - Compare their tech debt doc with actual implementation
  - Ask things like "sync tech debt", "check if TD-xxx is still an issue", "audit our tech debt", "update tech-debt docs", "is this debt still valid"
  A TD-xxx identifier or debt document mentioned as background in a code review or general document task does not by itself trigger this skill.
---

# Tech Debt Sync Skill

Audit the requested TD-xxx entries against repository evidence. Discover new debt only when requested; write document updates only within the authorized scope.

---

## Step 0 — Resolve scope and inputs

Distinguish a focused TD check, a full debt audit, new-debt discovery, and an authorized document sync from the request. A focused check covers only named entries and their direct dependencies; a full audit covers all existing entries. Neither implicitly adds new-debt discovery. Read-only requests produce findings without edits.

Locate the debt document from the supplied path, existing context, project index, or a targeted filename search. Read contract, PRD, or field definitions only when needed to judge a scoped item; use the project's declared authority rather than assuming a fixed contract filename. Ask only if multiple plausible targets or a missing necessary decision prevent useful progress.

---

## Step 1 — Build the internal audit table

Extract the scoped TD-xxx entries into an internal audit table. Reuse an existing table when its source and scope remain valid.

For each entry record:
| Field | Source in doc |
|---|---|
| ID | `### [TD-xxx]` heading |
| Title | heading text |
| Interface/route | "接口" field |
| Implementation files | "实现见" references |
| Router/config files | additional file refs in description |
| Todo items | "待处理" numbered list |
| Risk level | "风险等级" field |
| Current status note | "当前处理" field |

Read the referenced implementation and direct dependencies needed to assess each scoped item. Reuse evidence when the relevant source and validation conditions are unchanged. If a needed file does not exist, note it as `FILE_MISSING`.

Do not modify any files in this step.

---

## Step 2 — Audit each TD entry against code

For every TD-xxx in the audit table, check each "待处理" item against the actual code.

**Status labels:**
- `✅ 已完成` — the item meets its acceptance conditions; include evidence locations and any required test/runtime result. Code evidence alone supports only source implementation, not deployment or runtime acceptance
- `⏳ 部分完成` — some sub-items done, some not; detail which
- `❌ 未完成` — no evidence of implementation in code
- `❓ 无法判断` — depends on external decision (product/ops confirmation required), or description too vague

**Output format per entry:**

```
### [TD-xxx] 原标题

- **整体状态**：✅ / ⏳ / ❌ / ❓
- **待处理项核查**：
  - 原待处理项1 → ✅ 已完成，见 `path/to/file.py:行号`
  - 原待处理项2 → ❌ 未完成
  - 原待处理项3 → ❓ 无法判断，原因：需产品确认口径
- **备注**：与文档描述不一致的情况，或代码中额外发现的相关信息
```

Cover every item within the selected scope. Report evidence gaps; do not treat missing evidence as proof of completion or archive an item whose required acceptance remains unverified.

---

## Step 3 — Discover undocumented debt

Run this step only when new-debt discovery is requested. Limit the scan to the requested modules; an incidental out-of-scope finding can be reported without expanding the scan or editing unrelated entries.

Focus on these patterns (adapt to the project's tech stack):

**Interface & service layer**
- Routes/endpoints with response fields missing relative to the applicable authoritative contract
- Calculation logic with hardcoded thresholds or magic numbers
- Missing input validation on API parameters
- Inconsistent field naming across related endpoints (e.g., `open_rate` vs `openRate`)

**Data layer**
- N+1 query patterns
- Raw SQL strings without parameterization
- Missing indexes implied by query patterns

**Frontend / templates**
- Table columns or export fields that don't match backend response fields
- No empty-state or error-state handling
- Hardcoded display strings that should come from config

**General**
- `TODO` / `FIXME` / `HACK` comments not captured in debt doc
- Functions > 50 lines or nesting > 4 levels in core business logic
- `except Exception` / bare `except` swallowing errors silently
- Hardcoded URLs, credentials, or file paths

For each finding, use the project's established entry format. Read `references/td-entry-template.md` only if a new entry needs a fallback format; use applicable fields. Allocate IDs after checking the highest existing TD ID, without auditing unrelated entry bodies.

Only include findings with clear code evidence. Do not speculate.

---

## Step 4 — Generate summary report

Summarize the audited scope and evidence, using only applicable rows:

```
## 技术债同步报告

### 整体完成度
- 满足归档验收条件：X 条 → [TD-001, TD-003, ...]
- 部分完成：X 条 → [TD-002, ...]
- 未完成：X 条 → [TD-004, ...]
- 无法判断：X 条 → [TD-005, ...]
- 新发现（未记录）：X 条

完成度：XX% （已完成 / 总条数）
```

For a read-only audit, report findings and proposed changes without writing. For an authorized sync, apply the scoped updates and report the actual diff; do not ask again merely to start writing. Ask only about new material decisions, uncertain target semantics, or actions beyond the existing authorization. Do not modify application code or runtime data through this skill.

---

## Step 5 — Update tech-debt.md

When document changes are authorized, apply only evidence-supported changes within that scope. Preserve unresolved or deferred decisions; do not create an empty revision when nothing changed:

| Entry status | Action |
|---|---|
| ✅ 全部完成 | Move to bottom "已归档" section; add `归档时间` and `实现位置` |
| ⏳ 部分完成 | Update "当前处理" field; strikethrough completed 待处理 items in markdown |
| ❌ / ❓ 未完成 | Keep original format; optionally update file path references if they changed |
| 🆕 新发现 | Insert in risk-level order (高 → 中 → 低) before the archived section |

Preserve all original field labels and formatting conventions exactly as found in the document.

---

## Daily maintenance prompt (for after each commit)

When the user says they just finished work on a TD item, run a focused check:

1. Read only the relevant TD-xxx entry
2. Inspect the changed files and direct dependencies needed to verify that entry
3. Verify each 待处理 item is actually addressed in the diff
4. Apply the original acceptance conditions: archive only when required evidence is complete; otherwise report source completion, partial progress, or remaining verification separately
5. Write only if the request authorizes synchronization; otherwise report the proposed diff. Existing authorization does not require another confirmation

---

## Reference files

- `references/td-entry-template.md` — fallback format, read only when drafting a new entry without an established project template
