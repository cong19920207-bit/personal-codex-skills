---
name: contract-from-code
description: Use only when the user explicitly invokes $contract-from-code to establish, query, or synchronize a repository implementation contract from current codebase evidence.
---

# Contract From Code

## Purpose

Build and maintain a Repository Implementation Contract: an evidence-backed description of what the current repository implements. Optimize the contract for LLM routing and maintenance while keeping it readable for occasional human review.

This Skill is manually invoked. If the user did not explicitly invoke `$contract-from-code`, stop and do not apply this workflow.

## References by task

Choose query, full baseline, or incremental sync before loading references. Read the applicable evidence and exclusion rules in `references/evidence-rules.md` before scanning or verifying implementation claims. Read the relevant sections of `references/contract-structure.md` when creating, updating, or repairing contract structure; a query does not require authoring templates or schema validation. Reuse already-read rules while unchanged.

## Hard Boundaries

- Treat source code, schemas, migrations, configuration declarations, dependency manifests, tests, build files, and deployment files as candidate evidence.
- Do not use PRDs, requirements, development plans, progress documents, README claims, or comments as implementation facts. README and comments may only locate code that must then prove the claim.
- Do not claim that repository evidence proves production runtime state.
- Do not modify application code, databases, configuration, deployments, requirement documents, `docs/contract.md`, or technical-debt documents.
- A first baseline or a change of contract root needs approval of the concrete write set before writing; reuse approval already given for that set. An explicitly requested incremental sync authorizes ordinary updates to existing managed contracts within its scope, without a second approval gate.
- Do not overwrite, rename, move, merge, or adopt an unmanaged existing file without explicit approval.
- Do not read `.env`, credentials, secret files, or their values.

## Workflow

### 0. Route read-only queries

For a query, locate the requested contract root, read its Manifest/INDEX, then only the relevant contract entries and linked uncertainties. If the user asks what the current code implements or contract freshness is uncertain, verify the necessary source and direct dependencies under the evidence rules. Distinguish recorded contract statements from freshly verified implementation facts. If no contract exists, answer from targeted source evidence when available; do not silently create a baseline. Do not write, scan the whole repository, or ask the user to select a scanner for a query.

### 1. Preflight for authoring

1. Resolve the repository root.
2. Read applicable repository instructions such as `AGENTS.md`.
3. Record Git commit, branch, dirty state, and changed-file summary. If Git is unavailable, continue with `source_revision.available: false`.
4. Check for `contract-manifest.json` under the requested contract root, or under
   `docs/code-contracts/` when the user did not request one.
5. Check whether existing target files declare `managed_by: contract-from-code`.

Use `docs/code-contracts/` as the default contract root. If collision handling leads the user
to approve a different root, treat that exact approved path as the contract root for every
remaining workflow step and validation.

### 2. Resolve mode and scanner

Honor explicit choices. With no managed Manifest, use `full` to prepare the first-baseline proposal; with a managed Manifest and a scoped change or sync request, use `incremental`. Ask only when the scope cannot be inferred and choosing would materially change the result. Use the bundled read-only scanner when a repository inventory is needed, unless the user declines scripts. A focused incremental task can use targeted reads without a whole-repository inventory. No separate scanner approval is required.

### 3. Inventory the Repository

When an inventory is needed, run the bundled scanner from the Skill directory:

```bash
python3 scripts/inventory_repository.py <repository-root> --pretty
```

The scanner writes JSON only to stdout. Do not copy it into the repository. Do not redirect it into a project file.

If the scanner is declined or fails:

1. Report the failure without expanding authority.
2. Fall back to `rg --files`, targeted `rg`, Git, and direct file reads.
3. Apply the same evidence exclusions and safety rules.

Full mode inventories all reachable implementation surfaces after excluding dependencies, generated output, archives, unrelated documentation, binaries, large files, and secrets.

Incremental mode starts from Git diff, then expands to direct imports, callers, entrypoints, schemas, migrations, configuration, tests, and direct consumers needed to explain the changed behavior. A diff-only scan is incomplete.

### 4. Build an Internal Evidence Table

For each candidate fact record:

- stable contract ID;
- behavior or constraint;
- `verified`, `inferred`, `runtime-required`, or `conflicted`;
- repository-relative evidence path and symbol;
- dependencies, side effects, and direct consumers;
- target contract document.

Place `runtime-required` and `conflicted` items under `uncertainties/`; do not present them as formal facts.

### 5. Compare Existing Contracts

Only compare against files that:

- live under the chosen code-contract root; and
- declare a compatible `managed_by: contract-from-code` marker.

Classify semantic changes by stable ID:

- `added`
- `changed`
- `removed`
- `uncertain`
- `unchanged`

Do not assume a code change is correct. An apparent removal may be dead code, a replaced entrypoint, a feature flag, or an incomplete migration.

### 6. Preview Before Writing

For a first baseline, show:

- scan scope and exclusions;
- detected stack, entrypoints, and modules;
- proposed files;
- entry counts and representative entries;
- uncertainties;
- candidate technical debt, if any, as a separate non-writing report.

For an incremental sync, record the semantic changes, evidence, affected consumers, uncertainties, and exact write set. If already authorized, proceed and report the actual changes. If the request is preview-only, do not write. For a first baseline, unmanaged-file adoption, a root change, or a material expansion lacking approval, show the concrete proposal and end with `状态：未写入，等待用户确认。`; continue independent authorized work.

### 7. Write within authorization

When the applicable write set is authorized:

1. Write only approved files under the selected contract root (default: `docs/code-contracts/`).
2. Preserve unrelated managed entries.
3. Update affected contract documents and `verification.md`; update Manifest, INDEX, and uncertainty routes only where their metadata or routing changes. Do not rewrite unrelated files.
4. Do not touch `docs/contract.md`, PRDs, README, or `docs/tech-debt.md`.

If a target path is unmanaged, stop and offer:

- preserve it and choose another root;
- adopt it through a separately approved migration with an archived original;
- preserve it as an external reference.

### 8. Validate

Before claiming success:

- parse `contract-manifest.json`;
- verify required Manifest fields;
- verify managed Markdown frontmatter;
- verify stable IDs are unique;
- verify evidence paths for new or changed entries; for a full baseline validate all entries;
- verify INDEX and detail links resolve;
- verify Git diff contains only approved contract files;
- check only artifacts created by this run: remove disposable scanner/fixture output, preserve requested deliverables, and do not inspect or delete unrelated temporary files;
- record commands, results, failures, and unverified scope in `verification.md`.

Combine overlapping checks into one validation pass. Reuse earlier results only when their inputs, revision/file hashes, scope, and relevant environment remain valid; verify changed output after the final edit. If required validation fails, report the failure and limit the completion claim to what is supported.

## Safety Lessons

Baseline testing showed that an unguided agent may overwrite `docs/contract.md`, use a PRD as implementation evidence, replace an unmanaged code-contract file, modify README, read `.env`, or leave a project-local scanner. Treat every corresponding boundary above as mandatory.

## Completion

Report:

- mode and scanned revision;
- files created or updated;
- verification results;
- unresolved uncertainties;
- candidate technical debt kept outside the contract;
- any remaining task-created temporary artifacts and confirmation that unrelated repository files were preserved.
