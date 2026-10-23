# COMPETITOR_PATTERNS — AllTrue Product Intelligence V1

- run_id: `2026-09-18-product-intelligence-v1`
- 方法: web_search 索引片段＋可抓取靜態頁。官方幫助中心多為 JS 渲染（web_fetch 回空/403），以下來源標「次級來源（僅索引片段）」表示只驗證標題＋摘要存在、未讀內文。不硬編細節。
- 要求: 不做通用功能矩陣；每個基準回答 8 問。

## 1. 課程行事曆 — Jackrabbit Class（Activity Calendar＋補課/代課流程）

1. 解決什麼問題：每週固定開課＋散落的缺席補課/代課/約課，行政需單一視圖處理異動。
2. 工作流程：Activity Calendar 統管 classes/events/appointments；缺席從 Class Record 按 Schedule Makeup 開補課；獨立 Substitute Instructors 流程；家長端 Parent Portal 自助預約補課。
3. 為何在其規模有效：把「例外」做成從原紀錄出發的一鍵流程；家長自助分擔行政負載。
4. 可轉移：單一週曆多狀態色塊；缺席紀錄掛「安排補課」動作；家長自助請假＋選補課時段。
5. Overengineering：多設施 appointments、私人課計費串接、Legacy/新版雙軌。
6. 複雜度：中（session 狀態機＋日曆渲染，不碰金流約一週量級）。
7. 負面誘因：自助補課無上限會超收；事件塞太多老師手機端看不懂。
8. 不抄：雙軌並存；設施維度排程（AllTrue 以班級為單位）。
- 來源（次級）: https://help.jackrabbitclass.com/help/the-activity-calendar-overview · https://help.jackrabbitclass.com/help/schedule-makeup-class-record · https://help.jackrabbitclass.com/help/substitutes

## 2. 課程行事曆 — iClassPro（CALENDAR Page）

1–3. 團體課＋一對一約課同一日曆、不同物件建模；官方原話 "visual interactive representation"。
4. 可轉移：一對一補課/試聽用「約課物件≠團體課物件」分離建模。
5–8. 不抄 camps/parties 物件；物件一多報表點名各寫一次；複雜度中低。
- 來源（次級）: https://support.iclasspro.com/hc/en-us/articles/360012097333-What-is-the-CALENDAR-Page · https://support.iclasspro.com/hc/en-us/articles/9037388577175-What-is-the-Appointments-Feature

## 3. 學校名稱正規化 — ClassDojo（Join School＋School Directory，類比）

- 先說結論：找不到任何成熟產品為「補習班學校名正規化」做 typeahead/directory 官方文件；此為通用名錄模式，無直接競品。
1. 問題：入學表單同一學校 N 種寫法。
2. 類比流程：搜尋學校→有則 Join（school-approved 審核）→無則自建→Directory 匯入班級。
3. 有效點：「搜尋優先、建新為例外且走審核」漏斗。
4. 可轉移：search-select＋新增走待審核池＋正名/別名對照表。
5. Overengineering：全校審批制（AllTrue 行政事後合併即可）。
6. 複雜度：低（1 表＋表單改，1–2 天量級）。
7. 負面誘因：新增太方便→發散；太嚴→櫃檯亂選。
8. 不抄：重審批；以學校為組織邊界；外部學制資料庫。
- 來源（次級）: https://help.classdojo.com/hc/en-us/articles/204365159-Join-Your-School · https://help.classdojo.com/hc/en-us/articles/23101743056271-Joining-Multiple-Schools-FAQ

## 4. 出勤 — Teachmint（白板點名；Smart Attendance 人臉版）

1–3. 點名吃掉上課時間→嵌入老師已在用的上課介面（白板標記，自動整理）。
4. 可轉移：老師端「開課畫面＝點名畫面」（到/假/缺滑動標記；離線可記）。
5–8. 不抄人臉辨識（個資/家長同意/硬體/失敗處理；省 3 分鐘不值法務風險）；不抄綁定專屬硬體。
- 來源（次級）: https://www.teachmint.com/features/attendance-management-system · https://www.teachmint.com/glossary/a/attendance-management/

## 5. 出勤 — Procare＋brightwheel（托育簽到光譜）

1–3. 門口大量進出要快又要留痕：紙本→kiosk/QR/PIN 自助→location guard；核心是 presence 與 attendance 分開。
4. 可轉移：RFID 只做門口 presence log；點名仍老師課堂確認；無硬體先 QR＋PIN fallback。
5–8. 不抄美國托育合規報表；不上無 fallback 的純硬體方案；RFID 在上述產品無官方文件（AllTrue RFID 當自研整合案）。
- 來源（次級）: https://www.procaresoftware.com/blog/your-questions-about-child-care-attendance-tracking-answered/ · https://mybrightwheel.com/childcare-centers/tracking-attendance-manually-large-centers/

## 6. 多角色權限 — TutorBird（Tutor Privileges 等級制）

1–3. 一人兼多職＋離職斷權，小團隊不想維護 RBAC→3–4 個固定等級包，開帳號選等級定生死。
4. 可轉移：三級（主任全校區＋財務／行政排課點名客服無財務／老師只見自己班）；一人多職＝多個 role assignment，不做疊加公式。
5–8. 不抄逐項勾選矩陣；不抄綁個人的 ad-hoc 加權；等級太粗會有借帳號→用稽核 log 制衡。
- 來源（次級）: https://support.tutorbird.com/en/articles/875-what-do-the-different-tutor-privileges-do

## 7. 多角色權限 — PowerSchool SIS（User Access Roles，大規模參照）

1–3. 大學區多校多職種共存→角色＋頁面權限＋操作審批理由三層（法規稽核）。
4. 唯一可抄：敏感操作（改已送出點名、退費）填理由＋留 log。
5–8. 其餘幾乎全是 overengineering（學區層級模型、permission 附錄矩陣、事事審批→現場會繞過用 LINE）。
- 來源（次級）: https://ps.powerschool-docs.com/pssis-admin/latest/user-access-roles · https://support.powerschool.com/help/sms/800/districtuser/Content/Topics/Appendices/Attendance_permissions.htm

## 四句話總結

1. 日曆抄 Jackrabbit「例外從原紀錄出發＋家長自助」，不抄設施維度。
2. 學校名抄 ClassDojo「搜尋優先、新增走審核」漏斗，不抄重審批。
3. 出勤拆門口 presence＋課堂點名兩層，不碰人臉辨識。
4. 權限用三級固定包＋敏感操作留理由 log，不做勾選矩陣。
