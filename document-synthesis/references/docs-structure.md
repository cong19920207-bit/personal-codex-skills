# 跨项目 docs 结构参考

## 推荐结构

结构参考当前项目，但逻辑职责比目录名称更重要。旧项目可以映射现有路径，不要求一次迁移。

```text
docs/
├── INDEX.md
├── llm-manifest.json
├── PROJECT_OVERVIEW.md              # 或项目已有的长期现状/配置说明
├── design/
│   ├── README.md
│   └── <topic>/
│       ├── PRD-<topic>-vN.md
│       ├── <topic>_steps.md
│       ├── <topic>_实施计划.md
│       └── <topic>_review.md
├── contract.md                      # 契约路由入口
├── contract/
│   ├── current/<scope>/{api,data,admin-ui}.md
│   ├── drafts/
│   └── history/
├── progress/<topic>_progress.md
├── testing/{checklists,guides,reports}/
├── tech-debt.md                     # 技术债索引
├── tech-debt/{active,archive}/
├── VERSIONS.md
└── archive/                         # 项目没有既有归档位置时使用
```

专题目录内可以像参考项目一样保留扁平文件，也可以映射项目已有子目录。不要仅为匹配结构移动稳定文件。

## 理解项目所需的文档

| 文档 | 解决的问题 | 适用性 |
|---|---|---|
| `INDEX.md` | 从任务或专题应读取哪些当前文档 | 多文档导航需要时使用，已有入口可复用；单文件小改不强制新建 |
| `llm-manifest.json` | 为 Codex 提供机器可读的扫描、排除、状态和关系 | 建议所有长期项目使用 |
| 项目概览/长期配置 | 项目目标、现状、模块、长期约束和术语 | 整体文档治理需要时沿用或补齐，不为局部整理新增长期规则 |
| PRD/决策 | 为什么做、做什么、不做什么、规则与验收 | 有产品需求时必需 |
| 开发步骤 | 如何把已确认需求拆成可验证任务 | 进入开发前需要 |
| 实施计划 | 里程碑、顺序、依赖和阶段验收 | 中大型功能需要 |
| 当前契约 | 当前 API、数据、页面和共享约定真相 | 有稳定实现边界时需要 |
| 进度 | STEP/里程碑实际完成情况与契约更新 | 开发进行中需要 |
| 测试资料 | 怎么验、实际结果和未覆盖项 | 需要交付或回归时使用 |
| 技术债 | 已知缺口、风险、证据、计划和状态 | 存在已知问题时使用 |
| `VERSIONS.md` | 用户可感知的发布切片和已知限制 | 有发布节奏时使用 |
| history/archive | 保留被替代或退出日常读取的原文 | 有版本演进时使用 |

## 权威和读取规则

- `current` / `canonical`：当前权威，可进入默认读取。
- `draft`：未确认，不作为实施依据。
- `history`：曾经生效但已被替代。
- `archive`：保留但退出日常工作流。
- `planned`、`needs-review`、`needs-input`：占位或待确认，不得冒充事实。

同一专题、同一文档职责只有一个当前权威来源。INDEX 面向人和 LLM 路由，manifest 面向机器路由；两者不得互相矛盾。

## Manifest 参考字段

沿用参考项目的简洁模型：

- 顶层：`version`、`scan_roots`、`exclude_roots`、`relation_types`、`documents`。
- 文档：`id`、`path`、`status`、`authority`、`scopes`、`keywords`、`depends_on`、`related_documents`、`related_td`。
- 可选路由：`code_paths`、`route_prefixes`、`max_lines`。从有效文档或已授权定向核实的实现证据填入；无依据时留空，不为填满路由字段扫描整个代码仓。

默认排除 drafts、history、archive、snapshot。仅在用户明确要求版本对比、迁移、恢复或审计时读取。
