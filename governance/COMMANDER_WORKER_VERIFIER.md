# Lightweight Commander → Worker → Verifier Workflow

**Version:** 1.0.0  
**Owner:** Jerry Software Portfolio Ops  
**Scope:** AllTrue, Sunrise, Portfolio Ops

---

## 1. 核心理念

本工作流**不引入任何重型 Agent Orchestration 框架**，完全基於現有 Git、GitHub CLI (`gh`)、Cursor/Codex/Claude 終端與輕量 `agent-control` 工具組 (`agent-start`, `agent-status`, `wait-github-deploy`, `agent-finish`)。

目標是消除多 Session 重工、Dirty Worktree 阻塞、舊 Baseline 覆蓋、錯誤完成回報與過度治理自傷。

---

## 2. 任務生命週期狀態機 (Lifecycle State Machine)

所有 Agent 與任務必須使用以下 7 階標準生命週期，禁止未開 PR 或未經 Founder 核准即回報「已完成／已上線」：

```text
[NOT_STARTED]
      │
      ▼ (Worker: 撰寫程式碼、子任務 commit)
[IMPLEMENTED]
      │
      ▼ (Worker/Verifier: 執行單元/功能測試、agent-preflight)
  [TESTED]
      │
      ▼ (Verifier: 開立 PR / Draft PR，CI Presubmit 綠燈)
[PR_OPENED] ───────────────► 🛑 AGENT 交付邊界 (不可越權宣稱已上線)
      │
      ▼ (Founder: Review & Squash-Merge)
  [MERGED]
      │
      ▼ (GitHub Actions: Deploy to Pi 工作流完成)
 [DEPLOYED]
      │
      ▼ (Founder/Verifier: 驗證 live /version.json 與 health 端點)
[PRODUCTION_VERIFIED]
      │
      ▼ (執行 agent-finish 歸檔 worktree)
 [ARCHIVED]
```

### 狀態判斷與檢查工具

執行 `agent-status [project] [task-id]` 或 `agent-status [project] --all` 可立即取得所有任務之真實生命週期狀態：

| 狀態代碼 | 判斷依據 | 執行者 | 下一步動作 |
|---|---|---|---|
| `NOT_STARTED` | 工作區位於最新 main，無 commit、無程式碼 diff | Commander | 分派給 Worker 開工 |
| `IMPLEMENTED` | 本地有 commits ahead 或未 commit 之產品程式碼 | Worker | 執行測試並 commit 乾淨 |
| `TESTED` | 本地測試通過，`agent-preflight` 通過 | Worker / Verifier | 開立 GitHub PR (或 Draft PR) |
| `PR_OPENED` | GitHub PR 已開立，CI Presubmit 執行中或通過 | Verifier | 匯報 PR 與 CI 證據；**等待 Founder 審核** |
| `MERGED` | PR 已 Squash-Merge 至 `origin/main` | Founder | 追蹤 Deploy 工作流 |
| `DEPLOYED` | GitHub Actions `Deploy to Pi` 成功完成 | 自動化 / Founder | 驗證線上版本 (version.json) |
| `PRODUCTION_VERIFIED` | 線上 `/version.json` 的 `build_sha` / `hash` 與 commit 完全相符 | Founder / Verifier | 執行 `agent-finish` 歸檔清理 |

---

## 3. 三角色職責與交接合約 (Handoff Contract)

### 3.1 Commander (架構、分派與全景監控)
- **職責**：
  1. 釐清需求邊界、影響範圍與 Risk Tier (T0~T3)。
  2. 檢查目前進行中的任務與 PR，避免撞車重工：
     ```bash
     agent-status alltrue --all
     ```
  3. 透過官方入口開闢隔離工作區：
     ```bash
     agent-start alltrue <task-id> --dry-run
     ```
  4. 產出給 Worker 的輕量 Task Brief（定義 Context, Scope, Non-goals, 驗證清單）。

### 3.2 Worker (實作與最小變更)
- **職責**：
  1. 嚴格在指定之任務工作區 (`/home/jerry/workspace/tasks/<project>/<task-id>/`) 工作。
  2. 遵守 Minimal Diff 原則，不可整包重寫，不隨意變更非相關檔案。
  3. 獨立子任務及時 commit：
     ```bash
     git commit -m "<type>(<scope>): <summary>"
     ```
  4. 實作完成後執行本地 targeted tests。
  5. 狀態進展至 `IMPLEMENTED` → `TESTED`。

### 3.3 Verifier (獨立驗證與 PR 準備)
- **職責**：
  1. 執行 preflight 檢查：
     ```bash
     bash scripts/agent-preflight.sh
     ```
  2. 使用 `local-heavy-gate` 串行化保護大型測試／Build，避免跨 Session I/O 死鎖：
     ```bash
     local-heavy-gate -- npm run test:unit
     ```
  3. 開立 GitHub PR，並檢查 CI Presubmit：
     ```bash
     gh pr create --title "<type>(<scope>): <summary>" --body "<evidence>"
     gh pr checks <pr-number>
     ```
  4. 匯報真實完成狀態（告知 PR #、CI 狀態；明確聲明待 Founder 審核 Merge）。

---

## 4. Founder Approval Gate (絕對保留之不可逆閘門)

以下操作**嚴禁 Agent 自行授權或宣稱已執行**，必須保留 Founder 在 Session 內的即時明確指令：

1. **GitHub PR Squash-Merge**（除符合 T0/T1 safe auto-merge 且 CI 全綠之白名單外）。
2. **Production 部署與線上正式啟用** (`deploy.yml` 觸發或正式切換)。
3. **Database Migration、Schema Cutover、Destructive Operations**。
4. **Billing、金流、繳費認列、堂數計算**（防止超扣或重認）。
5. **身份認證 (Auth)、權限邊界 (RBAC)、LINE 綁定邏輯**。
6. **Production Data Mutation、線上資料手動修復 (POP Repair)**。
7. **Git 歷史重寫 (Rebase/Force-push)、Credential 輪換或金鑰異動**。

---

## 5. 治理簡化與防死鎖原則 (Simplified Controls)

為避免 Agent 因工具與暫存檔案自傷，以下規則已優化：

1. **Preflight 暫存檔自清與防死鎖**：
   - 僅對實際產品程式碼 (`backend/`, `frontend/src/`, `config/`, `.github/` 等) 嚴格檢查 Dirty。
   - Session 紀錄 (`.agent-session/`)、分析草稿 (`docs/analysis/`, `out/`)、除錯紀錄 (`debug*.log`, `*.log`)、快取 (`.pytest_cache/`, `node_modules/`, `vendor/`) 不觸發 Fail-Closed 死鎖。
2. **靈活的 Base Freshness 檢查**：
   - 於開發期間，若 `origin/main` 前進但無衝突，輸出 Warning 提醒 Rebase，不直接中斷 Session 或迫使 Agent 拋棄 Worktree。
3. **智慧 Worktree 歸檔清理**：
   - `agent-finish` 能辨識已 Merge 之 PR，自動清除 disposable 暫存檔。
   - 支援 `--kill-active` 終止測試留下的 Vite/Node 殘留行程。
   - 支援 `--prune` 一鍵清理所有已 Merge 且無未提交程式碼的工作區。
