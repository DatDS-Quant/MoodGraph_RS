# MoodGraph: Personalized Movie Recommendation using Knowledge Graphs and Apache Spark

## 1. Giới thiệu tổng quan (Overview)
**MoodGraph** là hệ thống gợi ý phim cá nhân hóa kết hợp sức mạnh biểu diễn tri thức của **Đồ thị tri thức (Knowledge Graphs)** và khả năng xử lý dữ liệu lớn phân tán của **Apache Spark**. Dự án hướng đến việc khai thác các mối quan hệ ngữ nghĩa sâu sắc giữa người dùng, cảm xúc/tâm trạng (mood) và các thuộc tính điện ảnh đa chiều để đưa ra đề xuất chính xác, minh bạch và giàu ngữ cảnh.

## 2. Trạng thái dự án (Current Status)
> [!NOTE]
> **Giai đoạn hiện tại**: Dự án đang trong giai đoạn chuẩn bị (preparation) và kiểm chứng tính khả thi (feasibility validation).
> Cấu trúc thư mục nền tảng đã được thiết lập sẵn sàng cho quá trình nghiên cứu và phát triển thực nghiệm.

## 3. Cấu trúc dự án (Project Structure)
```text
MoodGraph/
├── data/              # Quản lý tập dữ liệu (dataset thô, trung gian và đã qua xử lý)
├── docs/              # Tài liệu thiết kế hệ thống, kiến trúc và nghiên cứu lý thuyết
├── recommender/       # Pipeline Spark, thuật toán gợi ý và mô hình Knowledge Graph
├── web/
│   ├── backend/       # Web API phục vụ gợi ý phim (FastAPI)
│   └── frontend/      # Giao diện người dùng tương tác (Next.js)
├── .gitignore         # Quy tắc loại trừ tệp nhạy cảm, cache và dữ liệu lớn
└── README.md          # Tài liệu giới thiệu dự án
```