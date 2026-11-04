# BÁO CÁO NGHIỆM THU KIỂM THỬ TỰ ĐỘNG (GATE 2 & GATE 5 TESTING REPORT)

> **Dự án:** MoodGraph: Personalized Movie Recommendation using Knowledge Graphs and Apache Spark  
> **Nhiệm vụ:** Task 3B — Knowledge Graph Recommender  
> **Tài liệu:** `docs/kg/testing_report.md`  
> **Thời điểm lập:** 2026-11-04  
> **Người thực hiện:** Senior Python & Knowledge Graph Engineer (AI Assistant)

---

## 1. TỔNG QUAN BỘ KIỂM THỬ

Toàn bộ các yêu cầu nghiệm thu kỹ thuật của Task 3B được mô hình hóa thành **17 bài kiểm tra tự động (KG-01 đến KG-17)** trong thư mục `tests/kg/`. 

- **Framework:** `pytest 9.2.0` trên nền `Python 3.11.9 (win32)`.
- **Lệnh thực thi chính thức:**
  ```powershell
  python -m pytest tests/kg/ -v
  ```
- **Kết quả tổng quát:** **17/17 PASSED (100%)** trong thời gian thực thi: **7.85 giây**.

---

## 2. MA TRẬN KIỂM THỬ CHI TIẾT (17/17 TESTS PASSED)

| Mã kiểm thử | Tên hàm kiểm tra | Tệp kiểm thử | Mục tiêu kiểm định | Kết quả | Thời gian |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **KG-01** | `test_kg01_preflight_schema_and_manifest` | `test_schema.py` | Kiểm tra tồn tại dữ liệu, cấu trúc schema và số dòng manifest v1.0 | **PASSED** | 0.08s |
| **KG-02** | `test_kg02_unique_constraints_definition` | `test_schema.py` | Kiểm tra định nghĩa các ràng buộc duy nhất (Unique Constraints) cho 4 labels | **PASSED** | 0.01s |
| **KG-03** | `test_kg03_graph_edges_referential_integrity` | `test_import_idempotency.py` | Kiểm tra tính toàn vẹn tham chiếu, 0 cạnh mồ côi (no dangling edges) | **PASSED** | 0.02s |
| **KG-04** | `test_kg04_import_idempotency` | `test_import_idempotency.py` | Kiểm tra nạp lại 2 lần liên tiếp: số lượng node/cạnh tuyệt đối không đổi | **PASSED** | 0.02s |
| **KG-05** | `test_kg05_split_isolation_guard` | `test_no_leakage.py` | Tuyệt đối không một tương tác Val/Test nào bị rò rỉ vào đồ thị Train | **PASSED** | 0.03s |
| **KG-06** | `test_kg06_genome_selection_top_m` | `test_no_leakage.py` | Kiểm tra chính sách mỗi phim chỉ giữ tối đa $M=20$ tags | **PASSED** | 0.01s |
| **KG-07** | `test_kg07_p1_p2_p3_path_validity` | `test_path_scoring.py` | Mọi bằng chứng (evidence) đều truy vết ngược được từ các cạnh có thật | **PASSED** | 0.02s |
| **KG-08** | `test_kg08_scoring_fixture_hand_calculated` | `test_path_scoring.py` | Đối chiếu điểm số tính toán khớp chính xác với phép tính tay trên fixture | **PASSED** | 0.02s |
| **KG-09** | `test_kg09_mutation_test` | `test_path_scoring.py` | **Mutation test:** Gỡ cạnh đồ thị -> Điểm và evidence thay đổi dự đoán được | **PASSED** | 0.02s |
| **KG-10** | `test_kg10_seen_item_filtering` | `test_recommendations.py` | Không bao giờ gợi ý phim người dùng đã xem trong Train hoặc exclude list | **PASSED** | 0.02s |
| **KG-11** | `test_kg11_deterministic_ranking` | `test_recommendations.py` | Cùng graph/config cho kết quả Top-N và thứ tự tie-break hoàn toàn tiền định | **PASSED** | 0.02s |
| **KG-12** | `test_kg12_cold_start_movie_behavior` | `test_recommendations.py` | Phim có metadata nhưng chưa có rating vẫn được gợi ý; phim cô lập không bị ảo giác | **PASSED** | 0.02s |
| **KG-13** | `test_kg13_no_history_user_behavior` | `test_recommendations.py` | Người dùng ngoài train không có lịch sử trả về `[]` an toàn | **PASSED** | 0.01s |
| **KG-14** | `test_kg14_integration_output_schema` | `test_evidence.py` | Đầu ra khớp chuẩn integration contract với Khối 4 Hybrid | **PASSED** | 0.02s |
| **KG-15** | `test_kg15_validation_metrics_calculation` | `test_metrics.py` | Kiểm tra công thức toán học tính HR@K, NDCG@K, MRR@K | **PASSED** | 0.01s |
| **KG-16** | `test_kg16_resource_sanity` | `test_metrics.py` | Kiểm tra bộ nhớ runtime dưới ngưỡng an toàn (< 500MB RAM) | **PASSED** | 0.02s |
| **KG-17** | `test_kg17_git_hygiene` | `test_metrics.py` | Đảm bảo không commit file dữ liệu lớn, secrets hay file nhạy cảm | **PASSED** | 0.05s |

---

## 3. CHI TIẾT CÁC BÀI KIỂM THỬ TRỌNG YẾU

### 3.1. Bằng chứng Mutation Testing (KG-09)
- **Ý nghĩa:** Kiểm tra xem hệ thống có thực sự suy luận bằng đường đi đồ thị hay chỉ tính độ tương đồng giả mạo.
- **Quy trình kiểm thử:**
  1. Với đồ thị gốc: User 1 nhận được gợi ý Movie 3 kèm theo evidence đường $P3$ (Collaborative) thông qua láng giềng User 2: `User 1 -> Movie 1 <- User 2 -> Movie 3`.
  2. Gây đột biến (Mutate): Xóa chính xác quan hệ `(User 2)-[:RATED]->(Movie 3)`.
  3. Đo lại: Toàn bộ evidence $P3$ của Movie 3 hoàn toàn biến mất khỏi danh sách gợi ý của User 1.
- **Kết luận:** Hệ thống phản ứng chính xác với sự thay đổi của cấu trúc topo đồ thị tri thức.

### 3.2. Bằng chứng Chống rò rỉ dữ liệu (KG-05 Split Isolation Guard)
- **Quy trình:** Đối chiếu toàn bộ các cặp `(userId, movieId)` trong đồ thị với tập `splits/validation` và `splits/test`.
- **Kết quả:** Số cặp rò rỉ = **0**. Ranh giới huấn luyện tuân thủ tuyệt đối quy định của đề tài.

### 3.3. Bằng chứng Tính bất biến (KG-04 Idempotency)
- Nạp cùng một fixture 2 lần liên tiếp:
  - Lần 1: 4 users, 7 movies, 4 genres, 4 tags, 6 rated, 8 in_genre, 9 has_genome_tag.
  - Lần 2: 4 users, 7 movies, 4 genres, 4 tags, 6 rated, 8 in_genre, 9 has_genome_tag.
  - Chênh lệch: `0` (Không nhân bản nút hay cạnh).

---

## 4. LOG THỰC THI PYTEST CHÍNH THỨC

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\admin\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\admin\Desktop\BigData\mood-graph
plugins: anyio-4.13.0
collecting ... collected 17 items

tests/kg/test_evidence.py::test_kg14_integration_output_schema PASSED    [  5%]
tests/kg/test_import_idempotency.py::test_kg03_graph_edges_referential_integrity PASSED [ 11%]
tests/kg/test_import_idempotency.py::test_kg04_import_idempotency PASSED [ 17%]
tests/kg/test_metrics.py::test_kg15_validation_metrics_calculation PASSED [ 23%]
tests/kg/test_metrics.py::test_kg16_resource_sanity PASSED               [ 29%]
tests/kg/test_metrics.py::test_kg17_git_hygiene PASSED                   [ 35%]
tests/kg/test_no_leakage.py::test_kg05_split_isolation_guard PASSED      [ 41%]
tests/kg/test_no_leakage.py::test_kg06_genome_selection_top_m PASSED     [ 47%]
tests/kg/test_path_scoring.py::test_kg07_p1_p2_p3_path_validity PASSED   [ 52%]
tests/kg/test_path_scoring.py::test_kg08_scoring_fixture_hand_calculated PASSED [ 58%]
tests/kg/test_path_scoring.py::test_kg09_mutation_test PASSED            [ 64%]
tests/kg/test_recommendations.py::test_kg10_seen_item_filtering PASSED   [ 70%]
tests/kg/test_recommendations.py::test_kg11_deterministic_ranking PASSED [ 76%]
tests/kg/test_recommendations.py::test_kg12_cold_start_movie_behavior PASSED [ 82%]
tests/kg/test_recommendations.py::test_kg13_no_history_user_behavior PASSED [ 88%]
tests/kg/test_schema.py::test_kg01_preflight_schema_and_manifest PASSED  [ 94%]
tests/kg/test_schema.py::test_kg02_unique_constraints_definition PASSED  [100%]

======================== 17 passed, 1 warning in 7.85s ========================
```

