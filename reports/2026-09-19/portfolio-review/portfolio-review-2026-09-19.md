# 跨專案產品工程營運審查與改善計畫（有界修訂版）

> PORTFOLIO REVIEW · BOUNDED REVISION · 2026-09-19 · READ-ONLY（未批准 P1/P2 執行）
>
> **研究報告；保存／提交不代表改善計畫已批准。**
>
> 初稿保留，本次只做有界修訂：校正快照、收斂結論強度、修正優先順序。不新增平台、不新增治理工程、不派工、不關單。

## 修訂摘要

本次修訂後：**保留**交付引擎健康、intake 紀律、舊四項待決；**修正** F1／P1（不預設關單）、F2 證據範圍、portfolio 快照；**撤回**「#3067 未處理」「portfolio-ops 8/14 後無變更」「billing 要求二選一」「30 天恢復保證」「安全 Lead＋Founder 雙批准」等無證據或越界表述。原 P1／P2 的執行均不批准。

## 0. 時間與來源校正（影響決策先讀）

| 項目 | 內容 |
|------|------|
| 三種時間 | **observed_at**（本次修訂讀取：2026-09-19 約 15:00–15:30 +0800）≠ **最後成功取得遠端資料的時間**（本次 `fetch origin main` 成功，FETCH_HEAD=`6594f648`）≠ **commit 時間**（`99022e29` 2026-09-19 11:52:02 +0800；`6594f648` 2026-09-19 12:17:17 +0800）。`6594f648` 只代表本次 fetch 時的遠端值，不當永久現況 |
| main 判定 | 本地 `refs/heads/main` 的存在不足以證明它是當前遠端 main。本次以 fetch 後 `FETCH_HEAD` 為準；原報告的 `0b786397（09-17）` 已被取代 |
| #3079／#3067 | PR #3079 state=closed、merged_at=2026-09-19T03:52:03Z，merge SHA `99022e29`，對應 #3067／in-app #317。#3067 留言 5739203999 明記 merged、not deployed／not resolved，deploy run `35420016188` 等待 Founder `ACTIVATE_PRODUCTION:99022e29`。故 #3067 不再列為未處理新單；後續 #3080（`6594f648`）為同題（#317）跟進提交，內容為 split-slot wrap spacing（只讀 stat，未逐行審） |
| portfolio-ops 衝突 | 原報告「8/14 後無變更」撤回——它是舊快照誤判。本次 fetch 後最新為 `d23f92e`（2026-09-18 #115）、#113、#112、#111（#111／#112 即先前交付紀錄，存在）。無法核對的部分已核對完成，無殘留衝突；但該 repo 的投入結論仍只到「維持現狀」，不外推 |
| 舊快照標示 | 除 AllTrue 與 portfolio-ops 本次已 fetch 外，其餘 6 個 repo 仍為 2026-09-19 14:26 +0800 舊快照，明確標示，不用舊資料判定現在未處理 |
| issue 計數 | 113 為 issues API 含 PR 的總數（分頁 100＋13），本次未排除 PR；引用時不再寫成「113 個純 issue」 |

## 1. 保留／修正／撤回

| 原結論 | 處置 | 理由與證據 |
|--------|------|------------|
| 交付引擎健康（#3015 等當週合併、CI 綠） | **保留** | 證據未變；新增 #3079／#3080 當日合併，同一判斷延續 |
| Deploy run 35253615248 成功且 `55c2b641` 在 `28f58b84` 祖先內 | **保留並補強** | 正面證據保留；但 run success 只證明 workflow 層成功，不等於該功能完成驗收（見 R1） |
| F1「關單迴路斷裂」→ P1「關 #2905」 | **修正：不預設關單** | #2905 留言 5710306489 已記 MERGED → awaiting DAAN_STAGING_DEPLOYED／STAGING_RUNTIME_VERIFIED；#2906 留言 5710306803 已記 B.1 非 production-active、allowlist＋staging 條件、B.2 Founder-gated。open≠漏關。修訂後只做既有關單條件符合度核對（R1），不實際關單，不新增逐筆批准 |
| F2「B.1 首跑無 run，#2906 不能關」＋自建 GitHub run 門 | **修正證據範圍** | GitHub Actions 搜尋無結果僅代表該搜尋未找到證據，不能推導主機排程未執行；修訂後不自建 GitHub run 驗收門，改列本機補驗規格（R2） |
| F3 billing 孤兒分支要求 Founder drop／revive＋30 天恢復＋零成本 | **撤回並降級** | #1556／#1557 內文：自 #1550 拆出的後端 slice（700 行 presubmit 限制），含 account_last5 授權與 can_view_receipt；diff 為 StudentClassController ＋38／−12、測試 ＋263；仍 NOT_IN_MAIN（本次 fetch 確認）。但 closed-unmerged≠功能缺失，無現行需求或誤執行證據，故保持不動、保留歷史，不要求二選一；刪除恢復保證與成本斷言 |
| F4「#3067 未處理新單」 | **修正** | #3079 已合併、#3080 跟進；#3067 留言已有工程更新（附件 #264 私密審查，不轉述內容）。該筆改為交付中追蹤，不重複 admission |
| portfolio-ops「8/14 後無變更」 | **撤回** | 見 §0，本次 fetch 證明 9/17–9/18 有 #110–#115 |
| 「安全 Lead＋Founder 雙批准」重啟條件 | **撤回** | 新增 gate 越界；改為沿既有授權邊界描述（見 §5） |

## 2. 最新已核實狀態／仍未核實

| 事項 | 已核實 | 仍未核實 |
|------|--------|----------|
| #2905 | merged（55c2b641）＋既有留言記 staging／runtime 待驗；Deploy run 35253615248 Production job 與部署步驟 success | 該功能的必要驗收（staging deploy→runtime verify）紀錄是否已存在；既有關單條件的逐項符合度 |
| #2906 | Phase-A＋B.1 在 main；留言記 allowlist＋staging 條件、B.2 gated | B.1 觸發源（scheduler／主機／服務）與執行紀錄位置；首跑是否發生 |
| #3067／#3079／#3080 | merged（99022e29）＋跟進 6594f648；留言記 not deployed／not resolved、production gate 等待中 | ACTIVATE_PRODUCTION 是否已放行、runtime 驗證結果 |
| billing d2adf0ec | PR 關閉原因（拆分 slice）、diff 範圍、NOT_IN_MAIN；是否被取代未證實 | 現行產品需求是否存在、誤執行風險 |
| 新單其餘（#3065／#3066／#3068–#3075／#3078／#3081） | 沿用既有 issue／PR／工程狀態，不重複 admission（本輪未逐筆重讀） | 附件必要者待既有入口補驗（§4） |

## 3. 跨專案投入建議（限制深度版）

| 專案 | 建議（待驗假設已標） | 仍缺的關鍵價值資料 |
|------|----------------------|--------------------|
| AllTrue_System | **優先穩定（維持）**：先完成 R1／R2 的證據核對再談投入 | 必要驗收紀錄位置；B.1 觸發源位置 |
| sunrise-cafe | **維持，不擴投入（待驗假設）** | 安全 alert 內容需 security_events 權限；控制 PR 去留未核 |
| income-statement-app＋releases | **維持（待驗假設）**：僅守供應鏈，不擴功能 | 實際使用者數／更新成功率（未編造；無則不判 ROI） |
| jerry-cai-todo | **維持收斂（待驗假設）** | 推播＋真機驗證結果 |
| portfolio-ops | **維持現狀**：報告位置，不新增平台 | 無新增需求 |
| engineering-intelligence | **先驗證需求（待驗假設，不封存）**：原「降頻或封存」收斂為假設 | 簡報是否被決策引用（最小補證：問 Founder 一句） |
| exoprotocol | **維持（待驗假設）**：只修誤傷 | 誤傷工單實例 |

README 徽章與提交頻率均不當價值證據；上表凡證據不足者已改為待驗假設。

抽查的 PR 合併與 CI 證據正常；端到端交付健康尚未完整驗證。

## 4. 修訂後第一批（只兩項，不湊三項）

**R1．既有關單條件符合度核對（#2905／#2906／#3067 系；只建議、不關單）。**
按既有 lifecycle 逐項對：批准 scope → 對應實作 → 目標環境部署 → 必要驗收 → 既有關單條件 → 回寫狀態。先找已存在的驗收紀錄；輸出「待交付／待驗收／已驗收未回寫」三態映射，不新增狀態框架。前置依賴：需讀 staging／runtime 驗收紀錄位置（理由：沒有它無法判定符合度）。成本：約半天唯讀核對（前提：紀錄位置已知；未知則先停，轉本機補驗）。

**R2．B.1 觸發源與執行紀錄位置確認（本機補驗規格；不啟用、不觸發）。**
精確缺口交既有承接入口（本機 Codex／Cursor）：(1) B.1 由哪個 scheduler／主機／服務觸發；(2) 執行紀錄存在哪裡、保留多久；(3) 上次觸發時間。GitHub 無結果只記為該搜尋未找到，不下主機未執行結論。前置依賴：本機入口可讀 Pi／staging（理由：雲端側無此可見性）。成本：約 1 小時只讀查找。

附件處理：僅當附件是必要依據時，在現有授權與私密邊界內讀取；做不到則列缺口與補驗入口，不公開個資或秘密，不做確定分類。

### 後續候選（觸發條件）

- B.1 首跑驗證：觸發＝R2 位置確認＋首個執行紀錄出現。
- #3067 production 放行追蹤：觸發＝ACTIVATE_PRODUCTION 決議（既有 gate，不新增）。
- EI 存廢：觸發＝連兩週簡報無決策引用（維持假設，不先判）。

### 現在不做

原 P1 關單執行、原 P2 drop／revive、新平台／新框架、全域重稽、history rewrite、憑證操作、資料修復、帳務語意變更、分支刪除、migration、production 啟用、CI／測試 gate 變更、批量開 issue——重啟條件一律為 Founder 在既有授權邊界內明示。

## 5. Founder 決策（既有授權邊界內）

- 本次修訂不新增任何批准需求；B.2 auto-confirm 與 production activation（ACTIVATE_PRODUCTION）沿既有 Founder gate，不重寫。
- 真正需要 Founder 的（維持既有入口）：(a) R2 本機補驗可否讀 Pi／staging 排程位置；(b) #3067 production 放行與否（既有 gate）；(c) EI 簡報是否仍要（回答一句即可）。(a)(b) 可由既有本機入口先備齊證據再呈批，不轉成 Founder 待辦清單。
- 權限現況分開描述：Issues 寫入（無，CubeLV App 權限頁實證）／repo 檔案寫入（本任務 non-scope，不驗）／PR 建立（本任務 non-scope，不驗）。不由其中一項推導其他全部不可用；不新增 gate。

## 6. 保存狀態

本次修訂已更新 vault 內原 NOTE（工程日報／跨專案產品工程營運審查與改善計畫），GitHub 保存走本分支報告流程。

- 目標 repo：portfolio-ops；分支：`chore/task-portfolio-review-20260919`（自遠端 default branch 最新 `d23f92e` 建立，未動其他分支）。
- 本次變更：僅新增本報告 Markdown；未動 CI／測試／allowlist／排程／計費／身分／權限／產品 code。
- GitHub read-back：推送後以遠端檔案＋SHA 回讀確認。
- R1／R2 的執行、關單、drop／revive、merge、production 啟用：本次均未執行。

## Evidence（本次修訂的關鍵取值）

- AllTrue 遠端 main（本次 fetch）：`6594f648`，2026-09-19 12:17 +0800（#3080）。
- #3079（#3067）：已合併，`99022e29`，09-19 11:52 +0800。
- GitHub 寫入：本次修訂為唯讀；同步走報告專用分支流程。
- 修訂後第一批：2 項（不足三項不湊數）。
