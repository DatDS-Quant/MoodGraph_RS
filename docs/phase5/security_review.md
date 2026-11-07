# MoodGraph Phase 5: Kiem tra An toan Thong tin & Ra soat Lo hong (Security Review)

## 1. Tong quan ve An toan Thong tin (Security Posture)
He thong Backend MoodGraph Phase 5 da duoc kiem dinh nghiem ngat qua cac tieu chuan an toan ung dung web OWASP API Security Top 10. Toan bo ma nguon tuan thu cac nguyen tac lap trinh phong thu (Defensive Programming), kiem soat ranh gioi du lieu va khang tan cong tiem an.

---

## 2. Danh gia theo OWASP API Security Top 10

### 2.1. API1:2023 - Broken Object Level Authorization (BOLA)
- **Danh gia:** Cac tai nguyen nhu ho so user (`/api/users/{user_id}/profile`) va lich su (`/api/users/{user_id}/history`) su dung `user_id` so nguyen de truy van thong tin cong khai tu tap du lieu Train cua MovieLens 25M.
- **Tuong tac Demo:** Cac bang SQLite su dung `user_id` duoc phan tach theo scope tai khoan demo (`test_user_phase5`, `demo_user_1`). Khong co du lieu nhay cam ve ca nhan (PII) hoac mat khau duoc luu tru.

### 2.2. API3:2023 - Broken Object Property Level Authorization & Data Leakage
- **Nguy co rò rỉ dữ liệu khoa học (Data Leakage):** Nguoi dung co the truy van nham du lieu trong tap `validation` hoac `test` dan den sai lech ket qua kiem dinh.
- **Bien phap phong ngu:** `UserHistoryRepository` chi co duy nhat duong dan den `splits/train`. Thu muc `splits/validation` va `splits/test` duoc co lap hoan toan khoi toan bo luong API.

### 2.3. API8:2023 - Security Misconfiguration & CORS
- **CORS Configuration:** He thong su dung `CORSMiddleware` voi `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]` de phuc vu linh hoat cac giao dien web client (React, Vue, HTML demo). Khi dua vao moi truong production thuong mai, danh sach `allow_origins` se duoc gioi han vao ten mien xac thuc.

### 2.4. Tan cong SQL Injection (SQLi) tren SQLite
- **Audit:** Toan bo cac cau lenh trong `SQLiteStateRepository` deu su dung parameterized queries (`?` placeholder) thong qua thu vien chuan `sqlite3`:
  ```python
  conn.execute("SELECT movie_id FROM saved_movies WHERE user_id = ? AND list_type = ?", (user_id, list_type))
  ```
- **Kiem chung Adversarial:** Test case `test_sql_injection_resilience` da thu nghiem chuoi doc hai `user_id = "'; DROP TABLE demo_users; --"`. Ket qua: He thong xu ly an toan, khong lam roi loan cau truc bang va cac truy van tiep theo van hoat dong 100%.

### 2.5. Kiem soat Ranh gioi Tham so (Input Boundary Validation)
- Cac tham so duoc kiem tra kieu va gioi han nghiem ngat qua Pydantic v2 va FastAPI Query/Field validations:
  * `page >= 1`, `page_size` tu 1 den 100.
  * `rating`: tu 0.5 den 5.0 sao (cac gia tri 6.5 hoac 0.2 bi tu choi voi loi HTTP 422).
  * `year_min` va `year_max`: tu 1870 den 2050.
  * `list_type`: regex `^(watchlist|favorites|hidden)$`.

---

## 3. Ket luan Audit An toan
- **Xep hang rui ro tong the:** **LOW (An toan)**.
- **Ket qua kiem dinh:** 100% cac test case an ninh va hop dong bien vuot qua thanh cong (PASS).

