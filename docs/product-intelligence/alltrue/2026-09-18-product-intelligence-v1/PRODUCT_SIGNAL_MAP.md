# PRODUCT_SIGNAL_MAP — AllTrue Product Intelligence V1

- run_id: `2026-09-18-product-intelligence-v1`
- project: `alltrue`
- generated_at: `2026-09-18` (Asia/Taipei)
- source_commit (AllTrue_System main): `7ec7528a` — `ops(in-app): #315 evidence probe + Phase-C expected-behavior closeout (#3055)`
- source_commit (portfolio-ops main): `5479119`
- method: CubeLV cloud-side read-only inspection. Local bare-repo worktrees of `AllTrue_System` and `portfolio-ops` at main tip; product docs (`docs/MODULE_*.md`, `docs/architecture/RFC_*.md`, `docs/STAFF_UPDATES.yml`, `docs/TECH_DEBT.md`, `docs/FAQ.md`, `docs/proposals/`), `git log --oneline -n 60`, `docs/CHANGELOG.md` read via delegated subagents with file paths cited. GitHub issue bodies/comments, CI checks, and production state were NOT observable from CubeLV — marked UNKNOWN where applicable.
- Prior CubeLV evidence reused: truth-reconciliation audit of 9 issues / 17 open PRs (read-only token, 0 writes) and in-app #290 challenge review (`CONDITIONAL_AGREE`, findings F1–F4). Provenance: CubeLV vault notes `事故與稽核` folder.

Evidence classes: OBSERVED (file/commit directly read) · USER_REPORTED (in-app/staff report relayed in docs or commit messages) · INFERRED (planning-stage RFC/proposal) · UNVERIFIED (could not be checked).

## Signals

### SIG-001 — 課程堂次缺少行事曆編輯視圖
- source: `docs/proposals/PRODUCT_LOOP_DOGFOOD_001_INAPP_290_CALENDAR_COURSE_SESSION_EDITING.md` + STAFF_UPDATES `staff-2026-09-17-course-session-calendar-v1`
- source_ref: `alltrue:bug_report:290 / GH #2800`
- product_area: scheduling · actor: 主任
- problem_statement: 主任編輯課程時看不到整約的上課日期分佈，無法在行事曆形態下調整堂次。
- evidence: Proposal + Founder Plan Decision (Phase 0+1a GO); impl `a9418513` (#3043) merged; flag `COURSE_SESSION_CALENDAR_V1` default OFF; activation control `28f58b84` (#3044). Delivery state: MERGED, production enablement unverified from CubeLV.
- frequency: UNKNOWN · severity: UNKNOWN (blocks scheduling edits per proposal) · workflow_blocked: yes (course editing)
- possible_duplicates: #2808/#2905/#2906/#2908/#2179 per Founder dedup table — **issue status UNOBSERVED from CubeLV, needs Ubuntu-side recheck (finding F1)**
- confidence: medium · evidence_class: USER_REPORTED + OBSERVED (commits)

### SIG-002 — 同一學校多種寫法造成名冊失準
- source: `docs/STAFF_UPDATES.yml` (`staff-2026-09-17-school-typeahead`, source_refs `github:in-app-296`)
- source_ref: `in-app #296 / GH #2905`
- product_area: students/admissions · actor: 行政/主任
- problem_statement: 學生清單同一學校有多種寫法，期望有學校資料庫＋模糊搜尋。
- evidence: Bounded impl merged `55c2b641` (#3015): curated read-only directory + county detection + typeahead writing canonical display string; no FK, no history rewrite, no admin UI. Canonical school DB explicitly deferred (Plan amendment). Staging/production enablement unverified.
- frequency: UNKNOWN · severity: UNKNOWN · workflow_blocked: no (partially relieved)
- confidence: medium · evidence_class: USER_REPORTED + OBSERVED (commit)

### SIG-003 — 年級升級重複執行風險
- source: STAFF_UPDATES `in-app-297` + commits `c92452d9` (#3023), `386a92e3` (Phase-B.1)
- source_ref: `in-app #297 / GH #2906`
- product_area: students · actor: 主任
- problem_statement: 年級升級若可重複觸發會造成學生年級錯亂；需要預覽＋確認。
- evidence: Phase-A preview+confirm server-side merged; Phase-B.1 schedule-preview + reminder only, auto-confirm default OFF, branch allowlist fail-closed. Phase-B.2 auto-confirm still Founder-gated. Issue body reportedly still says "manual guide only" — stale (per truth audit), needs write-permission fix.
- frequency: UNKNOWN · severity: UNKNOWN · workflow_blocked: no
- confidence: medium · evidence_class: USER_REPORTED + OBSERVED (commits)

### SIG-004 — 未上課評量跟錯老師
- source: STAFF_UPDATES 2026-09-18 (`in-app-314`) + commit `1a413b1d` (#3052)
- source_ref: `in-app #314`
- product_area: learning records · actor: 老師/主任
- problem_statement: 換正班老師後，待填評量仍掛在舊老師名下。
- evidence: Mutable LR ownership merged: 未上課待填跟目前課表老師；已出席/已核准/有實質內容/正式代課不改寫. Phase-C resolved with allowlisted public reply (`41848c37`).
- frequency: UNKNOWN · severity: UNKNOWN · workflow_blocked: no
- confidence: medium · evidence_class: USER_REPORTED + OBSERVED (commit)

### SIG-005 — 跨校忙線誤判為可排課
- source: commit `7ec7528a` (#3055)
- source_ref: `in-app #315`
- product_area: cross-campus workflows/scheduling · actor: 主任
- problem_statement: 老師跨校忙線時段是否真忙，系統判定與主任認知可能不一致。
- evidence: Read-only dump probe (PII-redacted) judged `REAL_CROSS_CAMPUS_BUSY`; public reply explaining leave/reschedule release. No product code changed — ops closeout.
- frequency: UNKNOWN · severity: UNKNOWN · workflow_blocked: UNKNOWN
- confidence: low (single probe) · evidence_class: OBSERVED (commit message only; dump content UNOBSERVED)

### SIG-006 — 已回報≠已入帳：行政登記即 Paid=1 造成假已繳
- source: `docs/architecture/RFC_REPORTED_PAID_ACCOUNTING_SPLIT.md` + `docs/TECH_DEBT.md` (TD-067, TD-068) + open issues #2915/#2916 (status:needs-decision, per truth audit)
- product_area: payment/tuition/receipts · actor: 行政/會計
- problem_statement: 行政「核帳登記」一次寫 Payment＋Invoice結清＋`Paid=1`＋開收據，會計對帳前無法登錄；LINE上家長說已繳會變成帳上已繳。
- evidence: RFC Phase 1+2 on main; TD-068 statutory receipt (immutable/PDF/void) blocked without Founder approval; #2915/#2916 await product decision.
- frequency: UNKNOWN · severity: UNKNOWN (financial semantics — high caution) · workflow_blocked: partial
- confidence: medium · evidence_class: USER_REPORTED (嗨森現場建議 per docs) + INFERRED (RFC)

### SIG-007 — 行事曆拖曳/Modal 後果不可預期＋換週載入慢
- source: `docs/MODULE_CALENDAR_SCHEDULE_UX.md` + `docs/TECH_DEBT.md` (TD-062 Done Phase 1–3+P4, TD-076 Open)
- source_ref: `GH #1601 / Epic #1600` (cited in docs; bodies UNOBSERVED)
- product_area: scheduling · actor: 主任
- problem_statement: 主任在行事曆處理單堂時間/老師/請假/衝突時容易猜測後果；換週全量重抓慢。
- evidence: Spec documents root cause + acceptance criteria; TD-062 largely done; TD-076 chain-model architecture unchanged (downstream dedupe is patch).
- frequency: UNKNOWN · severity: UNKNOWN · workflow_blocked: partial
- confidence: medium · evidence_class: OBSERVED (docs) — issue bodies not read, frequency unmeasured

### SIG-008 — 代課兩步驟盲區與半成功風險
- source: `docs/SUBSTITUTE_UX.md` (PRD 9c058f19, f0cce4d5 ops manual per docs)
- product_area: leave/substitution · actor: 主任
- problem_statement: 原老師請假時需逐堂找代課並避開跨分校衝堂；「先調課再代課」兩步驟有衝堂盲區與半成功風險。
- evidence: PRD + ops manual with API and Undo behavior documented.
- frequency: UNKNOWN · severity: UNKNOWN · workflow_blocked: partial
- confidence: medium · evidence_class: OBSERVED (docs)

### SIG-009 — 刷卡 presence 與出勤/扣堂混淆
- source: `docs/architecture/RFC_RFID_CAMPUS_PRESENCE_V1.md` (Accepted, Founder policy 2026-09-16) + `docs/TECH_DEBT.md` (TD-004–TD-011 Done)
- source_ref: `GH #2809 / in-app #293` (per truth audit: RFID-0 merged `c9c219a8`, RFID-1 #2981 open T3 awaiting Founder squash-merge)
- product_area: attendance · actor: 行政/主任
- problem_statement: 刷卡只能證明「在校」，若直寫出勤/扣堂會產生雙記錄、bounce簽退、孤兒記錄等錯誤。
- evidence: Policy locked: presence ≠ attendance; RFID-0 merged; RFID-1 pending Founder merge.
- frequency: UNKNOWN · severity: UNKNOWN · workflow_blocked: no (policy guardrail in place)
- confidence: medium · evidence_class: USER_REPORTED + OBSERVED (docs/commits)

### SIG-010 — 多角色帳號權限邊界
- source: commit `mergeable_state=dirty` PR #3016 (auth multi-role, #299 per git log) + STAFF_UPDATES (`in-app-300` inbox, `in-app-312` teacher pins, `in-app-311` conflict)
- product_area: admin/permissions · actor: 主任/老師/行政
- problem_statement: 一人身兼多職、改師後舊權限殘留（行事曆卡舊老師、收件匣殘留、衝堂誤判）造成日常卡點。
- evidence: #3016 open + dirty (needs rebase; touches identity boundary — DO NOT TOUCH per audit); several small fixes merged (#2970/#2972/#2942/#2959 per git log).
- frequency: UNKNOWN · severity: UNKNOWN · workflow_blocked: partial
- confidence: low-medium · evidence_class: INFERRED + OBSERVED (commit messages only)

### SIG-011 — 議題內文與交付真相漂移
- source: truth-reconciliation audit (CubeLV vault note 2026-09-18)
- source_ref: `GH #2800, #2905, #2906`
- product_area: product-ops (meta) · actor: Founder/engineering agents
- problem_statement: 3 個 status:ready 議題內文停留在決策前狀態，與已合併/已部署實情矛盾，造成營運混淆。
- evidence: #2800 body ("deferred, keep existing calendar") vs merged #3043 + deployed main; #2905 body ("needs new data model") vs merged #3015 bounded solution; #2906 body ("manual guide only") vs merged #3023/#3026/#3033. Fix blocked on write permission (token read-only, POST 403).
- frequency: 3 issues observed · severity: process confusion · workflow_blocked: no (code), yes (decision clarity)
- confidence: high · evidence_class: OBSERVED

### SIG-012 — 開放 PR 缺 Risk-Class / Autonomy-Tier 宣告
- source: truth-reconciliation audit (17 open PRs checked one by one)
- product_area: product-ops (meta) · actor: engineering
- problem_statement: 9 個開放 PR 缺 Risk-Class/Tier 宣告，累積 fail-closed 風險（尤其 #3016 auth、#2021 billing）。
- evidence: Per-PR body inspection; good examples #2981/#2849. No governance change made, report only.
- frequency: 9 PRs observed · severity: process risk · workflow_blocked: no
- confidence: high · evidence_class: OBSERVED

### SIG-013 — 學習評量三角色共用清單認知負荷
- source: `docs/MODULE_LEARNING_RECORDS_UX.md`, `docs/MODULE_LEARNING_RECORD_CROSS_ROLE_UX.md` (2026-08-01 production read-only review; GH #1611 cited)
- product_area: learning records · actor: 老師/主任/家長
- problem_statement: 單一共用清單同時承載填寫/審核/回饋/搜尋匯出；主任讀正文需開 modal；手機 CTA 藏在橫向捲動表格右側。
- evidence: Production review record in docs; recent splits shipped (#2715 fill/review tabs, in-app-295 no-reply-needed flag per STAFF_UPDATES).
- frequency: UNKNOWN · severity: UNKNOWN · workflow_blocked: no (partially relieved)
- confidence: medium · evidence_class: OBSERVED (docs)

### SIG-014 — 新生問班直建 Student 污染名冊
- source: `docs/architecture/RFC_ADMISSIONS_FUNNEL_V1.md` (runtime activated 2026-09-05; E2E/retention sign-off pending, self-admitted)
- product_area: admissions/onboarding · actor: 主任/家長
- problem_statement: 公開問班無追蹤入口，且問班直建 Student 污染正式名冊。
- evidence: RFC shipped to runtime; sign-off pending.
- frequency: UNKNOWN · severity: UNKNOWN · workflow_blocked: UNKNOWN
- confidence: low-medium · evidence_class: INFERRED (RFC self-report; production verification UNOBSERVED)

## Provenance limits (honest)

- GitHub issue bodies, comments, timelines: UNOBSERVED (bare-repo only; search API reported broken).
- CI/checks truth, deploy logs, production flag values, user verification: UNOBSERVED — MERGED ≠ DEPLOYED ≠ RUNTIME_VERIFIED ≠ PRODUCT_OUTCOME_VERIFIED.
- Frequency / affected-user counts / revenue impact: UNKNOWN throughout (docs carry qualitative descriptions and sampled traces only).
- Competitor docs: secondary sources only (JS-rendered help centers; index snippets verified, bodies unfetched) — see COMPETITOR_PATTERNS.md.
