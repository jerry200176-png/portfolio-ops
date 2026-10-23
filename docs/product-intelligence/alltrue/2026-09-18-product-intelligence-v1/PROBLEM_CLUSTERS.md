# PROBLEM_CLUSTERS — AllTrue Product Intelligence V1

- run_id: `2026-09-18-product-intelligence-v1`
- project: `alltrue`
- source: `PRODUCT_SIGNAL_MAP.md` (SIG-001…SIG-014)

Observed problem vs root-cause hypothesis are separated in each card. Hypotheses are NOT facts.

## PC-01 — 課程異動缺少統一編輯面（行事曆＋Course Manager 整合中）

- affected_actor: 主任
- current_user_journey: 主任在課程管理看到一條請假/異動通知 → 切到行事曆看堂次 → 回課程管理編輯 → 兩邊資訊對不上。
- observed_problem: 編輯課程時看不到整約上課日期分佈，無法在行事曆形態下調整堂次 (SIG-001); 家長請假後主任不知去哪按、無法核對原堂次 (SIG-007-in-part). Course Manager V1 workspace (`8f764cc4`, polish `3eaaafeb`, activation `1a4168b8`) 正在把 Edit/More/Details 收斂為單一入口，但 #3045 實作中 + Presubmit failure。
- supporting_signals: SIG-001, SIG-007, SIG-011(#2800 漂移)
- root_cause_hypotheses (H,未驗證): H1: 編輯入口歷史上是多個競爭入口疊加，而非單一工作區設計。H2: 堂次狀態機（正常/請假/補課/代課/取消）沒有統一視圖。
- current_workarounds: 在行事曆與課程管理之間來回切換；Phase 0+1a 只讀+新增未來堂先頂著。
- user_cost: UNKNOWN (頻率未量測) · business_cost: UNKNOWN
- unknowns: #2800 剩餘範圍 (#3045 整合+啟用驗證) 何時完成；Phase 1b/2/3 是否仍需要。
- success_metric_candidates: 編輯任務完成時間；切換頁面次數；請假→核對→處理完成率。(皆待儀表化，目前無數字)

## PC-02 — 名冊正規化債（學校寫法發散 → bounded typeahead 緩解，正規化延後）

- affected_actor: 行政/主任
- current_user_journey: 櫃檯建學生檔 → 學校欄位自由填 → 同一學校 N 種寫法 → 分校統計失準。
- observed_problem: 同一學校多種寫法 (SIG-002)。Bounded typeahead (`55c2b641`) 已讓「實用層」可用，但 canonical DB/正規化架構明確延後，無 admin UI、無歷史改寫。
- supporting_signals: SIG-002, SIG-014 (問班直建污染名冊同源)
- root_cause_hypotheses: H1: 學校欄位從來不是名錄引用而是自由字串。H2: 新增路徑（問班/入學）沒有「搜尋優先、新增走審核」漏斗。
- current_workarounds: typeahead 選 canonical 顯示字串；仍可自訂（會繼續發散）。
- user_cost/business_cost: UNKNOWN
- unknowns: 名錄覆蓋率；自訂比例是否下降；歷史資料是否需回填。
- success_metric_candidates: 自訂輸入佔比；重複校名數；搜尋→選取轉換率。

## PC-03 — 代課/調課例外流程脆弱（兩步驟盲區＋跨校衝堂）

- affected_actor: 主任
- current_user_journey: 老師請假 → 主任逐堂找代課 → 避開跨分校衝堂 → 可能先調課再代課 → 半成功或衝堂。
- observed_problem: 「先調課再代課」兩步驟有衝堂盲區與半成功風險 (SIG-008); 跨校忙線判定曾與主任認知不一致，需 dump probe 才能定案 (SIG-005)。
- supporting_signals: SIG-008, SIG-005
- root_cause_hypotheses: H1: 調課與代課是兩個獨立操作而非單一原子流程。H2: 跨校忙線規則（leave/reschedule 釋放語意）不透明。
- current_workarounds: ops 個案探針 + 公開回覆；Undo 行為（文件稱有，需驗證）。
- user_cost/business_cost: UNKNOWN
- unknowns: 代課衝堂發生率；跨校規則是否已被主任理解。
- success_metric_candidates: 代課操作半成功率；衝堂客訴數；單次請假→全代課完成時間。

## PC-04 — 出勤語意混淆（presence vs attendance；刷卡直寫風險）

- affected_actor: 行政/主任/老師
- current_user_journey: 學生刷卡進校 → 系統若直寫出勤 → 請假/缺席/遲到/跨日記錄錯亂 → 行政逐一追。
- observed_problem: 刷卡只能證明在校，不能等於出勤/扣堂；歷史上雙記錄/bounce/孤兒記錄等一串問題 (SIG-009, TD-004–TD-011 Done)。政策已鎖定 (Founder 2026-09-16)，RFID-0 merged，RFID-1 (#2981, T3) 待 Founder squash-merge。
- supporting_signals: SIG-009
- root_cause_hypotheses: H1: 早期把 presence 事件直接當 attendance 寫。H2: 門口 presence 與課堂點名沒有分層對帳規則。
- current_workarounds: 政策 guardrail；老師課堂點名為準。
- user_cost/business_cost: UNKNOWN
- unknowns: RFID-1 何時合併啟用；漏刷「幽靈缺席」率。
- success_metric_candidates: 幽靈缺席追單數；presence-attendance 對帳差異率。

## PC-05 — 帳務語意高危（已回報 vs 已入帳；收據法定債）

- affected_actor: 行政/會計/家長
- current_user_journey: 家長 LINE 說已繳 → 行政登記 → 系統 Paid=1+開收據 → 會計對帳前無法區分真假已繳。
- observed_problem: 登記即 Paid=1＋開收據導致假已繳 (SIG-006)。RFC Phase 1+2 已上 main；法定收據 (immutable/PDF/void, TD-068) blocked 待 Founder 批准；#2915/#2916 needs-decision。
- supporting_signals: SIG-006
- root_cause_hypotheses: H1: Payment/Invoice/Paid/Receipt 綁在單一寫操作。H2: 「對帳」一詞跨領域過載 (TD-081)，語意從未拆開。
- current_workarounds: UI 已隱藏部分（TD-067），API 仍 open — 半吊子狀態。
- user_cost/business_cost: UNKNOWN (財務語意，謹慎為上)
- unknowns: #2915/#2916 決策；收據法務要求細節。
- success_metric_candidates: 對帳差異筆數；假已繳客訴；月結耗時。

## PC-06 — 學習評量工作台過載（三角色一清單 → 拆分中）

- affected_actor: 老師/主任/家長
- current_user_journey: 老師填寫、主任審核、家長回饋擠在同一清單 → 主任讀正文要開 modal → 手機 CTA 藏在橫向捲動右側。
- observed_problem: 共用清單認知負荷 (SIG-013)。已部分緩解：填寫/審核標籤分開 (#2715)、家長回饋可標不需回覆 (in-app-295)、LR 歸屬跟課表老師 (#3052)。
- supporting_signals: SIG-013, SIG-004
- root_cause_hypotheses: H1: LearningRecord 綁定出勤/核准/扣堂，診斷性檢測無處可記（→ RFC_LEARNING_ASSESSMENT_MVP 提議獨立 bounded context）。
- current_workarounds: 標籤拆分；待辦各自過濾。
- user_cost/business_cost: UNKNOWN
- unknowns: 老師填寫耗時是否下降；家長回覆率。
- success_metric_candidates: 待辦清空時間；modal 開啟率；手機任務完成率。

## PC-07 — 權限/身份邊界債（一人多職＋殘留權限）

- affected_actor: 主任/老師/行政
- current_user_journey: 老師兼行政/換校區 → 舊角色殘留（行事曆卡舊老師、收件匣殘留、衝堂誤判）→ 借帳號文化風險。
- observed_problem: 多個小修 (#2970/#2972/#2942/#2959) 逐一滅火；大解 #3016 (auth multi-role) open + dirty 待 rebase，觸及 identity 邊界 (SIG-010)。
- supporting_signals: SIG-010
- root_cause_hypotheses: H1: 權限跟著人走而非 role assignment。H2: 換師/離職沒有交接清除流程。
- current_workarounds: 逐案小修；#3016 不碰（另一方持有）。
- user_cost/business_cost: UNKNOWN
- unknowns: #3016 何時 rebase 合併；借帳號是否普遍。
- success_metric_candidates: 權限相關客訴；殘留權限稽核差異數。

## PC-08 — 產品營運元債（議題漂移＋PR 證據缺口）— 流程型，非產品功能

- affected_actor: Founder/engineering agents
- current_user_journey: Agent 讀議題內文做決策 → 內文是決策前狀態 → 誤判範圍 → 重工或誤關。
- observed_problem: 3 議題內文過時 (SIG-011)；9 PR 缺 Risk/Tier 宣告 (SIG-012)。修復被寫權限卡住（唯讀 token，POST 403）。
- supporting_signals: SIG-011, SIG-012
- root_cause_hypotheses: H1: 議題內文被當一次性提案而非活文件。H2: PR 模板宣告是事後稽核而非合併門檻。
- current_workarounds: 真相校準報告（唯讀）+ 待執行文案等有寫權限者貼上。
- unknowns: 寫權限何時恢復；label taxonomy 是否重設計。
- success_metric_candidates: 議題內文與 MERGED/DEPLOYED 一致率；PR 宣告完整率。

## 明確檢出的非工程處置

- 症狀 vs 根因: SIG-005（跨校忙線單一個案）是規則解釋問題，用 probe+回覆解決，不應直接建功能。
- 重複: #2808/#2905/#2906/#2908/#2179 與 #2800 的去重關係待 Ubuntu 側複核（F1），CubeLV 不擅自標 duplicate。
- 已解決: RFID TD-004–TD-011 Done；行事曆 TD-062 Done；問班 funnel 已上線（待 sign-off）。
- 應拒絕: 人臉辨識點名；逐功能勾選權限矩陣；設施維度排程（見 COMPETITOR_PATTERNS.md）。
- 需更多證據: 全部頻率/人數/營收影響（UNKNOWN）；#2915/#2916 帳務語意待 Founder 決策。
