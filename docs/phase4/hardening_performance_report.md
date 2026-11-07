# MoodGraph Phase 4 — Hardening Performance & Serving Latency Report

## 1. Mục tiêu & Phương pháp Khảo sát
Báo cáo đo lường hiệu năng phục vụ thực tế (Real-world Serving Performance) cho Phase 4 Hybrid Engine nhằm khắc phục triệt để hiện tượng nhầm lẫn giữa chi phí tính toán in-memory (fusion overhead) và độ trễ phục vụ toàn trình (end-to-end serving latency).

### Phương pháp Thực nghiệm:
1. **Phân rã 9 giai đoạn (9 Pipeline Stages):** Đo lường riêng biệt thời gian nạp model, sinh ứng viên ALS, duyệt đồ thị KG, gộp ứng viên, dung hợp RRF, dung hợp Weighted, đóng gói JSON và round-trip API.
2. **Đo lường Cold vs Warm Serving:**
   - **Cold Request (Cache Miss):** Chạy toàn bộ luồng ALS + KG Graph Traversal + Fusion.
   - **Warm Request (Cache Hit):** Truy vấn qua bộ nhớ đệm LRU Cache đa luồng.
3. **Thực thi Stress & Load Test:** Gửi 2,000 requests liên tục vào endpoint FastAPI thông qua Starlette TestClient để ghi nhận thông lượng phục vụ tối đa (Requests Per Second - RPS).

---

## 2. Kết quả Phân rã Độ trễ Thành phần (Component Latency Breakdown)

Dữ liệu được trích xuất trực tiếp từ file kết quả kiểm chuẩn: `docs/phase4/hardening_latency_profile.json`.

| Giai đoạn Pipeline | Thời gian Trung bình (Mean) | Phân vị P95 | Đơn vị | Ghi chú kỹ thuật |
| :--- | :--- | :--- | :--- | :--- |
| **1. Nạp ALS Delivery Artifacts** | 534.44 | - | ms | Nạp CSR, factor matrices, user/item index maps vào RAM |
| **2. Nạp KG Pilot Graph** | 9,967.92 | - | ms | 100 users, 62k movies, 73k genome edges |
| **3. Sinh Ứng viên ALS (Top-50)** | 16.02 | 183.03 | ms | Tương quan vector người dùng và ma trận embedding |
| **4. Sinh Ứng viên KG (Top-50)** | 1,565.90 | 6,172.30 | ms | Duyệt đa đường đi P1+P2+P3 trên đồ thị mạng |
| **5. Hợp nhất Ứng viên (Union)** | 0.0133 | - | ms | Set union và loại trừ trùng lặp trong RAM |
| **6. Dung hợp RRF (Top-10)** | 0.1561 | - | ms | Nghịch đảo thứ hạng (k=60), không cần chuẩn hóa điểm |
| **7. Dung hợp Weighted (Top-10)** | 0.2101 | - | ms | Chuẩn hóa Min-Max song song hai danh sách và cộng trọng số |
| **8. Đóng gói JSON & Serialization** | 0.1122 | - | ms | Pydantic response parsing và serialization |

> [!NOTE]
> Kết quả đo lường phân rã khẳng định nguyên nhân gốc rễ của độ trễ: Thuật toán dung hợp (Fusion Overhead) chỉ tốn từ **0.15 đến 0.21 ms**. Điểm nghẽn độ trễ lớn nhất nằm ở giai đoạn **Duyệt đồ thị đa bước của KG (Mean: 1,565.90 ms)**.

---

## 3. Độ trễ Phục vụ API Toàn trình (End-to-End API Latency)

Đo lường trên endpoint `/api/recommendations` thông qua TestClient độc lập:

| Trạng thái Phục vụ | P50 (Median) | P90 | P95 | P99 | Đơn vị |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cold Serving (Cache Miss)** | 1,314.76 | 1,314.76 | 1,314.76 | 1,314.76 | ms |
| **Warm Serving (Cache Hit)** | **3.96** | **4.82** | **5.10** | **89.01** | ms |

- **Nhận xét SLA:**
  - Đối với các yêu cầu đã được lưu vào bộ nhớ đệm (Cache Hit), hệ thống đạt độ trễ cực nhanh: **P50 chỉ 3.96 ms** và **P95 đạt 5.10 ms**, vượt xa tiêu chuẩn công nghiệp (SLA < 50 ms).
  - Đối với các yêu cầu Cold (lần đầu truy vấn), hệ thống cần 1.3s để hoàn tất duyệt đồ thị KG. Do đó, trong môi trường sản xuất, việc kích hoạt cơ chế Pre-warming Cache hoặc chạy tác vụ nền Async KG Candidate Precomputation là chiến lược tối ưu nhất.

---

## 4. Kiểm thử Tải & Đo lường Thông lượng (Stress & Load Testing)

- **Tổng số Requests thử nghiệm:** 2,000 requests.
- **Tổng thời gian hoàn tất:** 10.454 giây.
- **Thông lượng thực tế (Throughput):** **191.3 Requests / Giây (RPS)**.
- **Tỷ lệ lỗi (Error Rate):** 0.00% (2,000 / 2,000 requests HTTP 200 OK).
- **Bộ nhớ đệm (Cache Hit Ratio):** 99.95% trong phiên kiểm thử tải.

---

## 5. Kết luận & Khuyến nghị Vận hành (Production Guidance)
1. **Chiến lược Phục vụ Tối ưu:**
   - Sử dụng **Hybrid RRF** làm cấu hình mặc định (không phụ thuộc vào phân phối điểm tuyệt đối của hai mô hình, tốc độ xử lý nhanh hơn 25% so với Weighted Fusion).
   - Thiết lập kích thước bộ nhớ đệm `cache_maxsize >= 10,000` và `cache_ttl_seconds = 3,600` để đảm bảo phần lớn lưu lượng truy cập của người dùng được phục vụ tại tầng Warm Cache với độ trễ dưới 5 ms.
2. **Kiến trúc Scale:**
   - Khi triển khai phân tán với nhiều Uvicorn workers hoặc Kubernetes pods, khuyến nghị kết nối Redis cluster làm bộ nhớ đệm tập trung để chia sẻ cache giữa các worker processes.
