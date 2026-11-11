# CUBELV_RESPONSIBILITY_BOUNDARY — Product Intelligence dogfood 結論

- run_id: `2026-09-18-product-intelligence-v1`
- 原則: 最小可用邊界；CubeLV 可替換；永不成為 runtime 權威。

## 建議常設職責（小集合）

1. GitHub issue intelligence（唯讀）：議題真相校準（內文 vs MERGED/DEPLOYED/驗證狀態）、stale 議題複查。
2. In-app feedback synthesis：STAFF/PARENT Updates 來源回報 → Signal 正規化（本輪 14 signals 模板可重用）。
3. Duplicate detection（建議級，非判定）：候選去重表＋需 Ubuntu/寫權限側複核（如 F1）。
4. Problem clustering：多票同源合併為 ProblemCard（本輪 8 clusters）。
5. ProposalCard generation：只為防守力足的機會建卡＋recommended_disposition（7 值）。
6. Competitive research（按需）：高價值 ProblemCard 才做，不做通用矩陣。
7. Founder DecisionPacket 準備：帳務語意（PROP-04 類）、Phase 升級（1b/2/3 類）、合併/啟用節奏。
8. Post-release product outcome review：STAFF_UPDATES 條目 vs 議題關閉狀態對帳（outcome 是否真發生）。

## 節奏建議

- 議題真相校準：雙週或有大合併後觸發。
- 完整 Product Intelligence run（含競品）：月度或 Founder 召喚。
- DecisionPacket：按需（有 NEEDS_FOUNDER_DECISION 即產）。

## CubeLV 永不負責（硬邊界）

Goal/Run 生命週期、任務執行狀態、leases、fencing、WorkerRun、dispatch、部署、生產啟用、生產變更、runtime 健康、營運驗收、本地工程機器狀態。GitHub 是知識/證據 substrate，不是 runtime orchestration 真相源。

## 交接契約（CubeLV → Engineering OS）

CubeLV → Signal/ProblemCard/ProposalCard → GitHub durable artifacts（本目錄＋RESULT.json＋LATEST.json）→ Engineering OS / Founder policy → GoalContract → Codex/Cursor workers。CubeLV 永不直接叫 Cursor 實作功能；工程 agent 必須獨立驗證證據後才動工。

## Open SWE / MetaGPT / OpenHands 模式處置

- Open SWE — ADAPT：借「plan 先行＋review 關卡」；不借非同步自主執行（AllTrue 只需關卡，不需自主寫碼管線）。
- MetaGPT — REFERENCE_ONLY：取「需求→結構化 PRD→再動工」紀律；重型角色鏈對單一課務功能殺雞用牛刀。
- OpenHands — REJECT：它是自主寫碼平台，解決「自動寫碼」而非「需求釐清與交接」；當前導入只會把定義不清變成自動爛 PR。
- 來源: https://www.langchain.com/blog/introducing-open-swe-an-open-source-asynchronous-coding-agent · https://github.com/langchain-ai/open-swe · https://www.ibm.com/think/topics/metagpt · https://arxiv.org/html/2308.00352v7 · https://www.openhands.dev · https://arxiv.org/html/2511.03690v1
