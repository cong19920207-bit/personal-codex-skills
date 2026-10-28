# 调用方托管的 STEP 文档修复

仅在审核方交接已授权的 STEP 结构修复时读取。

输入必须包含 `audit_path`、`source_digest`、`candidate_input_path`、
`authorized_finding_ids`、`expected_target_per_id`、`allowed_scope_per_id`、
`forbidden_changes_per_id`、`verification_per_id`、`output_candidate_path`。

- 审计报告和输入 STEP 只读；先核对来源摘要，再按授权 finding ID 修复。
- 同一轮只写一个新候选，不覆盖原 STEP，不修改 PRD、验收或业务语义。
- 来源摘要不匹配、目标不唯一或必须改变需求语义时，暂停受影响修复并交回审核方；
  审核方可在既有授权内核验版本和重新绑定，实质决策仍由用户决定。
- 相邻未授权问题只记录，不纳入修复；它阻塞当前项或有共享影响时才暂停。
- 返回 `finding_id → changed_location → verification_evidence → item_status`、
  候选 `candidate_sha256` 和 `handoff_state = STEP_REVIEW_READY`。

调用方维护唯一审计与状态记录，不另建 `execution/`。工作项 `VERIFIED` 只证明授权
修复项已执行；必须交回审核方对最终候选完整复审后才能签发 `STEPS_VERIFIED`。
交接不要求用户重新点名；当前修复与复审授权仍有效时，由调用方继续完成。
