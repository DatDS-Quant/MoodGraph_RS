# DANH MỤC KIỂM TRA BÀN GIAO & TIÊU CHÍ NGHIỆM THU (HANDOFF CHECKLIST) - PHASE 4

## 1. BẢNG KIỂM TRA TIÊU CHÍ NGHIỆM THU KỸ THUẬT

| STT | Hạng mục kiểm tra | Yêu cầu kỹ thuật | Trạng thái | Bằng chứng thực nghiệm |
| :---: | :--- | :--- | :---: | :--- |
| 1 | **Nhánh Git & Phạm vi** | Phát triển trên `feature/phase4-hybrid-recommender`, không tự ý merge vào `main` | **ĐẠT** | Nhánh hiện tại: `feature/phase4-hybrid-recommender` |
| 2 | **Bảo toàn Test Split** | Tuyệt đối không mở, sửa đổi hay rò rỉ phân vùng `splits/test` | **ĐẠT** | Toàn bộ kiểm thử và benchmark chỉ thực hiện trên `splits/validation` |
| 3 | **Bảo toàn ALS Champion** | Đóng băng mô hình finalist `ALS_R8_REG0.3_ITER10` | **ĐẠT** | Không huấn luyện lại, nạp trực tiếp qua `ALSDeliveryService` |
| 4 | **Candidate Union** | Hợp nhất tập ứng viên: C_hybrid = C_ALS U C_KG | **ĐẠT** | Đã kiểm chứng qua `tests/hybrid/test_candidate_union.py` |
| 5 | **Defense-in-depth Seen** | Lọc triệt để phim đã xem trong Train ở 3 tầng | **ĐẠT** | Đã kiểm chứng qua `tests/hybrid/test_leakage_and_seen.py` |
| 6 | **Fusion RRF (k=60)** | Hiện thực chuẩn RRF, bất biến thang đo điểm | **ĐẠT** | Đối chiếu độc lập qua kiểm thử tính bằng tay `test_03_rrf_hand_calculated_scores` |
| 7 | **Weighted Score Fusion** | Chuẩn hóa Min-Max / Percentile + Imputation | **ĐẠT** | Đối chiếu độc lập qua kiểm thử tính bằng tay `test_04_weighted_score_fusion_hand_calculated` |
| 8 | **Explainability** | Giữ nguyên bằng chứng KG, giải thích ALS trung thực | **ĐẠT** | Đã kiểm chứng qua `tests/hybrid/test_explainability.py` |
| 9 | **Deterministic Tie-break** | Sắp xếp: hybrid_score DESC, movieId ASC | **ĐẠT** | Đã kiểm chứng qua `tests/hybrid/test_determinism.py` |
| 10 | **Cold-Start Handling** | Phục vụ bằng KG nếu khuyết ALS; trả rỗng minh bạch nếu khuyết cả hai | **ĐẠT** | Đã kiểm chứng qua `tests/hybrid/test_engine.py::test_03` |
| 11 | **Serving API (FastAPI)** | Đầy đủ các endpoints `/health`, `/model_info`, `/recommendations/{user_id}` | **ĐẠT** | Đã kiểm chứng 6/6 API tests qua `tests/hybrid/test_api.py` |
| 12 | **In-Memory Cache** | Bounded LRU + TTL, đạt P95 < 200ms cho warm serving | **ĐẠT** | Đạt Warm P95 = 1.20 ms (vượt chuẩn 160 lần), `tests/hybrid/test_cache.py` |
| 13 | **Combined Regression** | Không làm phá vỡ 184 ALS tests và 24 KG tests | **ĐẠT** | Toàn bộ các test cũ và mới đều PASS |

---

## 2. HƯỚNG DẪN TÁI LẬP (REPRODUCIBILITY INSTRUCTIONS)

1. **Kích hoạt môi trường và kiểm tra mã nguồn**:
   ```powershell
   git checkout feature/phase4-hybrid-recommender
   ```
2. **Chạy toàn bộ bộ kiểm thử Hybrid**:
   ```powershell
   python -m pytest tests/hybrid/ -v
   ```
3. **Chạy kiểm thử hồi quy kết hợp**:
   ```powershell
   python -m pytest tests/als/test_delivery.py tests/kg/ tests/hybrid/ -q
   ```
4. **Khởi chạy Serving API thời gian thực**:
   ```powershell
   python -m uvicorn recommender.hybrid.api:app --host 0.0.0.0 --port 8000 --reload
   ```
5. **Chạy benchmark thực nghiệm ngoại tuyến**:
   ```powershell
   python scripts/hybrid_evaluate_validation.py 100
   ```

