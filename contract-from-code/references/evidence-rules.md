# Evidence Rules

## Contents

1. Contract meaning
2. Evidence classes
3. Confidence states
4. Reachability
5. Conflicts
6. Incremental scope
7. Excluded sources
8. Safety and secrets
9. Technical debt

## 1. Contract Meaning

A Repository Implementation Contract describes behavior and constraints that the current repository can support with evidence. It is an as-built repository baseline, not a product-requirement contract and not proof of production runtime state.

Use repository-relative paths. Prefer symbols, routes, model names, migration names, configuration keys, and logical identifiers over line numbers.

## 2. Evidence Classes

| Evidence | Can prove | Cannot prove alone |
|---|---|---|
| Reachable entrypoint and call chain | Current implemented behavior, validation, response, side effects | Deployment has enabled or exercised it |
| Types and validators | Static shape and accepted/rejected values | Runtime data already conforms |
| Schema and migrations | Repository-declared data structure and evolution | Deployed database is current |
| Configuration declaration | Supported key, default, branch, feature flag | Real environment value |
| Build and deployment files | Repository-declared packaging and topology | Current deployed revision |
| Tests | Reproducible expected behavior when consistent with implementation | Untested paths or production state |
| Dependency manifests | Declared libraries and versions | Code actually exercises every dependency |

## 3. Confidence States

### `verified`

Use only when direct, reachable, mutually consistent evidence proves the fact.

### `inferred`

Use when at least two repository relationships support the conclusion but no single authoritative implementation states it. Write the inference chain in `Evidence`.

### `runtime-required`

Use when confirmation requires a running service, deployed revision, real database, external system, feature-flag value, or production data. Store it only under `uncertainties/`.

### `conflicted`

Use when source, schema, migrations, configuration, or tests disagree. Store it only under `uncertainties/` and cite both sides.

## 4. Reachability

Before promoting source code to a formal contract:

1. Find the application, route, CLI, worker, job, plugin, or registry entrypoint.
2. Trace the direct call or registration path.
3. Check configuration and feature flags that gate the path.
4. Check whether another implementation shadows or replaces it.
5. If reachability remains unclear, classify it as `runtime-required` or `conflicted`.

Do not promote:

- unregistered handlers;
- unused exports;
- examples and fixtures;
- archived code;
- generated candidates whose runtime consumer is unknown;
- comments describing absent behavior.

## 5. Conflicts

Move the item to `uncertainties/` when any of these disagree:

- source and tests;
- ORM schema and migrations;
- route validation and domain validation;
- configuration default and deployment manifest;
- multiple entrypoints implementing the same logical operation differently;

A managed contract is comparison input, not repository evidence. When consistent repository
evidence differs from a managed entry, classify the semantic result as `changed` or `removed`.
Use `conflicted` only when repository evidence itself disagrees or cannot establish which
implementation is authoritative. Do not choose the newest file by timestamp or filename.

## 6. Incremental Scope

Start with changed files, then include the minimum evidence needed from:

- direct imports and callees;
- direct callers and registered consumers;
- route, CLI, job, or event entrypoints;
- related validators and serializers;
- schema, migration, transaction, cache, queue, and storage logic;
- directly related tests;
- configuration and feature flags;
- output consumers whose contract may break.

If a change crosses a module boundary, expand to that direct module boundary and report the expansion. Do not silently turn an incremental scan into an unrelated full audit.

## 7. Excluded Sources

Never use these as implementation facts:

- PRD and requirement documents;
- development plans and design proposals;
- progress and release claims;
- README claims;
- code comments;
- historical or archived documents;
- technical-debt descriptions.

README and comments may identify a symbol or command. The referenced executable artifact must independently prove the fact.

Existing files under the selected code-contract root may be read only for comparison and routing. They do not prove current implementation without code evidence.

## 8. Safety and Secrets

- Do not open `.env`, `.env.local`, `.env.production`, credential files, private keys, token files, or secret-manager exports.
- Safe example files may be used only to identify declared key names after confirming they contain no real values; prefer code declarations and deployment templates.
- Never report whether a secret is set, its length, prefix, hash, or value.
- Do not follow symlinks outside the repository.
- Do not install dependencies or access the network.
- Do not create a scanner in the target repository.
- Use the bundled scanner or direct read-only tools.

## 9. Technical Debt

A code contract records current behavior neutrally. Technical debt records a confirmed quality or maintainability problem accepted for later work.

- Keep candidate debt out of formal entries.
- Report candidates separately with code evidence.
- Do not create or modify `docs/tech-debt.md` without a separate explicit request.
- Do not label an implementation as debt merely because it is unfashionable or could be refactored.
- An uncertainty is missing or conflicting evidence, not technical debt.
