### Lab 1 — Reflected XSS

1. 進入 `/lab1`。
2. 搜尋 `<script>alert(1)</script>`。
3. 伺服器不安全地將 `q` 放入 HTML 本文，瀏覽器解析並觸發對話框。
4. 關閉對話框後，頁面會顯示 `Challenge Complete!` 和 Flag（驗證有短暫延遲）。

### Lab 2 — Cookie

1. 進入 `/lab2`。
2. F12 → Application（應用程式）→ Storage → Cookies → `http://127.0.0.1:8765`。
3. 查看名稱 `lab2_treasure` 的 Value 欄位，直接取得 Flag。

### Lab 3 — 事件型 XSS

1. 進入 `/lab3`。
2. 用 `<script>alert(1)</script>` 測試，會被不完整的 script 標籤黑名單移除。
3. 改用 `<img src=1 onerror=alert(1)>`；圖片載入失敗，onerror 執行。
4. 關閉對話框後，頁面會顯示 `Challenge Complete!` 和 Flag。

### Lab 4 — 屬性注入

1. 進入 `/lab4`。
2. 搜尋內容放在 `<body data-search="USER_INPUT">`。
3. `<`、`>`、`&` 被編碼，但雙引號沒有編碼。
4. 搜尋 `" onload="alert(1)`，HTML 成為 `<body data-search="" onload="alert(1)">`。
5. 觸發 body load 事件，關閉對話框後可在頁面看到 Flag。

### Lab 5 — 前端驗證繞過、POST

1. 進入 `/lab5`，嘗試解鎖失敗。
2. F12 → Elements，發現隱藏表單 `#secretForm`，`method="POST"`，`action="/lab5/secret-room"`，隱藏欄位 `action=unlock`。
3. 在 Sources 查看 `/static/lab5.js`，發現密碼檢查只在前端，通過後呼叫 `document.getElementById('secretForm').submit()`。
4. 在 Console 執行 `document.getElementById('secretForm').submit()` 即可直接提交 POST。
5. 後端只檢查 `action=unlock`，沒有身分驗證，因此回傳 Flag。
6. 也可在前端原始碼中看見測試密碼 `cobra_admin_2026`，直接輸入密碼同樣能進入，作為替代解法。若希望唯一預期解法為繞過前端驗證，需重新設計前端機制。
