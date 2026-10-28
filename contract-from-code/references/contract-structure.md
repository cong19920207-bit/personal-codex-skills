# Contract Structure

## Contents

1. Root and routing
2. Managed metadata
3. Manifest
4. Contract entries
5. Uncertainties
6. Preview formats
7. Collision policy
8. Validation and Token rules

## 1. Root and Routing

Use this default fixed root:

```text
docs/code-contracts/
├── INDEX.md
├── contract-manifest.json
├── verification.md
├── core/
│   ├── repository.md
│   ├── architecture.md
│   ├── runtime.md
│   └── security.md
├── surfaces/
│   ├── api.md
│   ├── data.md
│   └── integrations.md
├── modules/
│   └── <actual-module>.md
└── uncertainties/
    ├── INDEX.md
    └── <affected-area>.md
```

Do not create empty or inapplicable detail files.

If an unmanaged collision requires a custom root, use only the exact root separately approved
by the user. Preserve the same internal structure and use that approved root consistently in
the Manifest, links, write preview, and validation.

Default LLM read order:

1. `contract-manifest.json`
2. `INDEX.md`
3. only the relevant core, surface, or module document
4. `uncertainties/` only when the question involves an unresolved fact
5. source evidence only when verifying or changing the contract

`INDEX.md` must state this read order and must not duplicate detail content.

## 2. Managed Metadata

Every managed Markdown file starts with:

```yaml
---
managed_by: contract-from-code
contract_schema_version: 1
verified_commit: <git-commit-or-unavailable>
source_state: clean-or-dirty
scan_mode: full-or-incremental
---
```

Angle-bracket values are generation variables and must be replaced. Use `unavailable` when Git metadata cannot be obtained.

Only a compatible `managed_by` and `contract_schema_version` permit automatic update proposals.

## 3. Manifest

Minimum shape:

```json
{
  "managed_by": "contract-from-code",
  "contract_schema_version": 1,
  "contract_revision": 1,
  "generated_at": "ISO-8601 timestamp",
  "repository": {
    "name": "repository-name"
  },
  "source_revision": {
    "available": true,
    "commit": "40-character commit or null",
    "branch": "branch name or null",
    "dirty": false,
    "changed_files": []
  },
  "scan": {
    "mode": "full",
    "included": [],
    "excluded": []
  },
  "detected_stack": [],
  "modules": [],
  "documents": [
    {
      "path": "docs/code-contracts/core/repository.md",
      "kind": "repository",
      "status": "current",
      "modules": []
    }
  ],
  "uncertainties": {
    "count": 0,
    "index": "docs/code-contracts/uncertainties/INDEX.md"
  },
  "verification": {
    "status": "passed",
    "path": "docs/code-contracts/verification.md"
  }
}
```

Use repository-relative paths. When the worktree is dirty, include the changed-file summary and never call the result a reproducible committed snapshot.

## 4. Contract Entries

Use stable IDs:

- `API:<method-or-kind>:<logical-path>`
- `DATA:<model-or-store>.<field-or-rule>`
- `RULE:<module>.<logical-rule>`
- `RUNTIME:<system>.<key-or-behavior>`
- `SECURITY:<scope>.<rule>`
- `INTEGRATION:<system>.<operation>`

IDs must not depend on line numbers.

Use this fixed field order:

```markdown
## API:POST:/api/projects

Status: verified
Behavior: 创建项目。
Input: `name` 必填；非法 `stage` 使用默认值。
Output: `201` + Project。
Errors: `400` 参数错误；`500` 未处理异常。
SideEffects: 写入 Project 和 ProjectModule。
Dependencies: database.
Evidence: `src/app/api/projects/route.ts#POST`; `src/lib/api.ts#requiredString`.
```

For non-API entries, omit fields that do not apply rather than inventing values. Keep `Status`, `Behavior`, `Dependencies`, and `Evidence`.

Document-level revision metadata must not be repeated in every entry.

## 5. Uncertainties

`uncertainties/INDEX.md` contains only ID, status, area, short summary, and detail link. Details use:

```markdown
## UNCERTAINTY:runtime.feature-x

Status: runtime-required
Question: Feature X 是否在目标环境启用。
Reason: 仓库只声明开关，未提供环境取值。
Evidence: `src/config.ts#FEATURE_X`; `deploy/app.yaml`.
RequiredVerification: 检查目标部署的非敏感开关状态。
Impact: 不能把 Feature X 写成当前启用能力。
```

Never promote an uncertainty automatically.

## 6. Preview Formats

### First Baseline

Use this preview when the concrete write set still needs approval. Existing approval for that exact set remains valid; a preview-only request never authorizes writing.

```text
Mode:
Source revision:
Scope:
Excluded:
Detected stack:
Entrypoints:
Modules:
Proposed files:
Entry counts:
Representative entries:
Uncertainties:
Candidate technical debt:
Status: not written; awaiting user confirmation.
```

### Incremental Sync

| Change | Stable ID | Current code evidence | Existing contract | Impact | Proposed action |
|---|---|---|---|---|---|
| added | `API:POST:/api/projects` | `src/...#POST` | none | new consumer surface | add |

Allowed change values:

- `added`
- `changed`
- `removed`
- `uncertain`
- `unchanged`

List the exact proposed or actual write set below the table. A requested incremental sync of managed files proceeds within its existing scope; ask only for an unapproved root change, unmanaged-file adoption, or material expansion. The table is not itself a new approval gate.

## 7. Collision Policy

Keep `docs/contract.md` and other requirement or document-governance contracts separate.

When the target root or file exists without compatible managed metadata:

1. preserve it;
2. report the path and semantic responsibility;
3. do not write;
4. offer a separately confirmed adoption with archived original, a custom root, or external-reference treatment.

Same basename in a different path is not automatically a collision. If two documents claim the same responsibility, Manifest may route to only one current authoritative implementation contract.

## 8. Validation and Token Rules

Validate:

- Manifest JSON and required fields;
- managed frontmatter;
- unique stable IDs;
- evidence paths for new/changed entries, or all entries in a full baseline;
- INDEX and detail links;
- approved Git diff only;
- disposition of scanner/fixture artifacts created by this run; do not inspect or delete unrelated temporary files.

Combine overlapping checks into one pass. Reuse valid results only while their source, scope, and environment remain unchanged; check the final changed output before claiming completion.

Optimize Token usage:

- keep Manifest and INDEX short;
- store one authoritative copy of each fact;
- use links instead of duplicated explanations;
- do not copy source, tests, PRDs, or large configuration blocks;
- split by real business module, not arbitrary length;
- do not bulk-read every module or uncertainty file.
