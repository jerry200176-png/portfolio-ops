# PRODUCT_PROPOSALS — AllTrue Product Intelligence V1

- run_id: `2026-09-18-product-intelligence-v1`
- 原則: 只為有防守力的機會建卡；不為填報告而製造提案。無分數；只給推理與 tradeoffs。
- Disposition 說明見各卡。Proposal 是產品候選，不是 WorkerInvocation/排程/生產批准。

## PROP-01 — Course Manager 後續整合收尾（#3045 範圍驗證＋啟用驗證）

- problem_id: PC-01 · project: alltrue
- product_outcome: 主任在單一課程工作區完成全部課程異動，不再切換頁面。
- target_actor: 主任
- evidence: #3045 open PR (mergeable=True, Presubmit failure 待修); #3040–#3044 merged (`a9418513`); STAFF_UPDATES calendar/typeahead 條目；另一 worker 持有中（DO NOT TOUCH）。
- proposed_change: 不新增範圍。只做：#3045 合併→修正 Presubmit→Phase 0+1a 啟用驗證→#2800 真相評論+內文狀態區（寫權限恢復後）。
- non_goals: Phase 1b/2/3（未授權）；取消/改時間/改老師（#3043 明確排除）。
- alternatives_considered: 另開新工作區（拒絕：增加入口競爭）；直接全量啟用（拒絕：flag OFF 是刻意 guardrail）。
- why_now: 漂移最大、被引用最多的 umbrella；修好它消除最多營運混淆。
- expected_value: 決策清晰度（定性）；無法量化。
- implementation_complexity_estimate: 流程工作為主，無新產品碼（除 #3045 既有範圍）。
- risk: 低（唯讀驗證+評論），#3045 本體風險由持有方承擔。
- dependencies: #3045 持有方；寫權限 token；Founder 措辭確認。
- success_metrics: #2800 內文與交付一致；啟用驗證證據存在。
- validation_plan: 讀 #3045 merge SHA → 查 Deploy run → staging 探針（Ubuntu 側）→ 更新議題。
- founder_decision_required: 是（#3045 合併/啟用節奏；Phase 1b/2/3 是否另立 Plan）。
- recommended_disposition: NEEDS_FOUNDER_DECISION

## PROP-02 — 學校名錄新增審核漏斗（搜尋優先＋別名表＋待審核池）

- problem_id: PC-02 · project: alltrue
- product_outcome: 新建學生時學校欄位選到 canonical 校名；重複寫法不再增加。
- target_actor: 行政/櫃檯
- evidence: #3015 bounded typeahead 已合併（無 FK/無歷史改寫/無 admin UI）；競品類比 ClassDojo Join School＋Directory（次級來源，見 COMPETITOR_PATTERNS.md）。
- proposed_change: 學校欄位改 search-select（搜尋既有名錄→選不到才新增）；新增進待審核池由行政合併；維護正名＋別名對照。不做：外部學制資料庫對接；歷史資料回填（另議）。
- non_goals: canonical FK 正規化；歷史改寫；school-approved 重審批。
- alternatives_considered: 全面正規化 schema（拒絕：Plan 修正案已明確延後）；維持自由填寫+事後清洗（拒絕：繼續發散）。
- why_now: typeahead 已鋪好 curated 目錄，加漏斗是小增量。
- expected_value: 名冊品質（定性）；無法量化。
- implementation_complexity_estimate: 低（1 表＋表單改＋審核池，約 1–2 天量級，未經估算流程，僅定性）。
- risk: 低；風險在新增太方便→發散（需審核池），或太嚴→櫃檯亂選（需監控自訂比）。
- dependencies: #3015 啟用驗證先完成。
- success_metrics: 自訂輸入佔比下降；重複校名數下降。
- validation_plan: 上線後 2–4 週看自訂比；抽查待審核池。
- founder_decision_required: 否（除非要動歷史資料）。
- recommended_disposition: READY_FOR_ENGINEERING_REVIEW

## PROP-03 — 代課原子流程（調課＋代課單一操作＋衝堂預檢）

- problem_id: PC-03 · project: alltrue
- product_outcome: 老師請假→主任一次操作完成全代課，無半成功、無衝堂盲區。
- target_actor: 主任
- evidence: SUBSTITUTE_UX PRD+手冊（Undo 行為待驗證）；SIG-005 跨校忙線 probe 顯示規則不透明。
- proposed_change: 把「調課+代課」包成單一原子操作，提交前跑跨校衝堂預檢，失敗整批退回；忙線規則文案在 UI 具名（哪條規則、什麼條件）。仍需更多證據才能定範圍（代課衝堂發生率 UNKNOWN）。
- non_goals: 自動找代課老師（不做媒合）；家長自助選代課。
- alternatives_considered: SOP 手冊了事（部分可行，低成本備選）；全自動排代課（拒絕：約束過多，overengineering）。
- why_now: 不急 — 先量測再決定是否值得做。
- expected_value: UNKNOWN（缺頻率數據）。
- implementation_complexity_estimate: 中（狀態機+預檢，未估算）。
- risk: 中（觸及排課核心語意；schedules 鏈模型 TD-076 未動）。
- dependencies: 排課 occurrence 身份（RFC_SCHEDULE_OCCURRENCE_IDENTITY Phase 3）；衝堂率數據。
- success_metrics: 半成功率；衝堂客訴。
- validation_plan: 先加埋點/抽查量測 2–4 週，再定是否立項。
- founder_decision_required: 否（立項前先量測）。
- recommended_disposition: NEEDS_PRODUCT_EVIDENCE

## PROP-04 — 帳務語意拆分決策包（#2915/#2916＋收據法定債）

- problem_id: PC-05 · project: alltrue
- product_outcome: 行政登記≠會計入帳在系統中有區分；收據開立符合法務要求。
- target_actor: 行政/會計（Founder 決策）
- evidence: RFC_REPORTED_PAID_ACCOUNTING_SPLIT Phase 1+2 on main; TD-068 blocked; #2915/#2916 needs-decision; TD-081 對帳命名過載。
- proposed_change: 本卡不提解法，只組決策包：把「已回報/已入帳/收據」三語意的選項、法務約束、月結影響寫成 Founder DecisionPacket，決策後才有工程卡。
- non_goals: 任何帳務碼變更（決策前不動）。
- alternatives_considered: 工程先拆再說（拒絕：財務語意，錯了不可逆）。
- why_now: 半吊子狀態（UI 藏、API 開）拖越久越危險。
- expected_value: 避險（定性）。
- implementation_complexity_estimate: 決策包撰寫（小）；實作待決策後估。
- risk: 高若誤動帳務；本卡本身零風險（只寫文件）。
- dependencies: Founder 時間；法務/會計輸入。
- success_metrics: 決策做出；對帳差異筆數（決策後追）。
- validation_plan: DecisionPacket → Founder 簽核 → 另立工程 Goal。
- founder_decision_required: 是（核心）。
- recommended_disposition: NEEDS_FOUNDER_DECISION

## PROP-05 — 出勤雙層確認（門口 presence＋課堂點名對帳）

- problem_id: PC-04 · project: alltrue
- product_outcome: 漏刷/代刷不再變成幽靈缺席；人在校區但沒進教室有明確對帳規則。
- target_actor: 行政/老師
- evidence: RFID 政策已鎖定（presence≠attendance）；RFID-0 merged；RFID-1 #2981 待 Founder 合併；競品 Procare/brightwheel 分層模式（次級來源）。
- proposed_change: presence log 與課堂點名對帳規則（差異清單＋一鍵確認）；QR/PIN fallback（卡片遺失時）。不做：人臉辨識；美國合規報表。
- non_goals: 用刷卡自動扣堂；自動點名。
- alternatives_considered: 維持現狀（可行，RFID-1 上線後再看）；人臉辨識（拒絕：法務+成本）。
- why_now: 不急 — 等 RFID-1 合併後看數據。
- expected_value: UNKNOWN。
- implementation_complexity_estimate: 中（對帳規則是魔鬼細節）。
- risk: 中（觸及出勤語意）。
- dependencies: RFID-1 合併；漏刷率數據。
- success_metrics: 幽靈缺席追單數；對帳差異率。
- validation_plan: RFID-1 上線後量測 1 個月再定範圍。
- founder_decision_required: 否（範圍確定後按常規）。
- recommended_disposition: NEEDS_PRODUCT_EVIDENCE

## PROP-06 — 議題真相修復批（#2800/#2905/#2906 評論＋內文狀態區）

- problem_id: PC-08 · project: alltrue
- product_outcome: 議題內文與交付真相一致；agent 不再誤判。
- target_actor: Founder/engineering agents
- evidence: 真相校準報告備妥文案；寫權限缺失（POST 403）是唯一 blocker。
- proposed_change: 有寫權限者執行三則真相評論＋內文狀態區（不關閉、不改標籤）。純 ops，不碰產品碼。
- non_goals: 關閉議題；改標籤 taxonomy；碰 #3045/#3016/#2981 本體。
- alternatives_considered: 無（唯一解）。
- why_now: 最高價值下一步（#2800 先）。
- expected_value: 決策清晰度。
- implementation_complexity_estimate: 極低（貼文案）。
- risk: 極低（評論可修正；措辭需 Founder 確認）。
- dependencies: 寫權限 token 或 Founder 手動。
- success_metrics: 三議題內文與 MERGED/DEPLOYED 一致。
- validation_plan: 發布後複讀確認。
- founder_decision_required: 是（措辭確認，輕量）。
- recommended_disposition: OPS_CHANGE_NOT_CODE

## 明確 REJECT（不建工程卡）

- 人臉辨識點名（法務＋成本＋家長疑慮；見競品研究）。
- 逐功能勾選權限矩陣（小團隊維護不起；用三級固定包＋敏感操作留理由 log 即可，#3016 範圍外不另立）。
- 設施維度排程 / camps-parties 物件（美國體操館場景，AllTrue 不需要）。
- 全面學校 FK 正規化＋歷史改寫（Plan 修正案已延後；先做 PROP-02 漏斗）。
- 全自動代課媒合（約束過多；先量測再說）。

## ALREADY_SOLVED（供 Engineering OS 去重）

- TD-004–TD-011 刷卡系列；TD-062 行事曆 Phase 1–3+P4；問班 funnel 上線（待 sign-off）。
- #3052 LR 歸屬；#2715 評量標籤拆分；in-app #295/#300/#311/#312 小修（見 STAFF_UPDATES）。

## DEFERRED（延後追蹤）

- RFC_BRANCH_HEALTH_V1（Proposed，未上線；總部看板另議）。
- RFC_LEARNING_ASSESSMENT_MVP（Slice 1 未開始；等評量債數據）。
- RFC_COURSE_CONTINUITY（Draft；續報合約另議）。
- RFC_SCHEDULE_OCCURRENCE_IDENTITY Phase 3（gated；排課根治另議）。
- RFID-1 #2981（Founder squash-merge 待辦；非本輪）。
