# Front-End Design & Engineering System (Taste + Impeccable)

## I. Visual & Taste Standards (Kế thừa từ Taste-Skill)
1. **Visual Hierarchy & Typography**:
   - Sử dụng font Sans-serif hiện đại (Inter, Plus Jakarta Sans) cho giao diện và Monospace (`JetBrains Mono`, `tabular-nums`) cho dữ liệu số liệu, thời gian, điểm số và metrics.
   - Khoảng cách dòng, tỷ lệ cỡ chữ (Scale Ratio) tuân thủ nhịp điệu 8pt grid.
2. **Surface & Materials**:
   - Tone nền tối Obsidian Dark kết hợp hiệu ứng Optical Glassmorphism (`backdrop-blur-xl`, border mờ tinh xảo `border-white/10`).
   - Phân cấp chiều sâu (Elevation) rõ ràng qua lớp nền (`#070A0F`, `#090D14`, `#131B2E`) thay vì dùng bóng đổ đậm màu.
3. **Micro-Interactions**:
   - Mọi trạng thái tương tác (hover, active, focus) đều có phản hồi mượt mà trong khoảng 150ms – 250ms (`ease-out`).
   - Sử dụng hiệu ứng phản hồi xúc giác thị giác (visual feedback) như pulse animation, glowing border khi có thay đổi trạng thái.

## II. Quality, A11y & Architecture (Kế thừa từ Impeccable)
1. **Semantic & Accessibility (WCAG AA/AAA)**:
   - Sử dụng thẻ HTML ngữ nghĩa (`<main>`, `<header>`, `<nav>`, `<section>`, `<article>`).
   - Tỷ lệ tương phản chữ trên nền tối thiểu 4.5:1 (với body text) và 7:1 (với số liệu quan trọng).
   - Hỗ trợ phím tắt điều hướng (`Esc` đóng modal/drawer, `/` hoặc `Ctrl+K` kích hoạt search) và `aria-label` đầy đủ cho các icon button.
2. **Responsive & Fallback Resilience**:
   - Tương thích tốt trên các kích thước màn hình từ Desktop đến Tablet/Mobile.
   - Luôn có cơ chế Fallback (dự phòng): nếu ảnh poster lỗi mạng phải hiển thị vector SVG gradient; nếu WebGL không bật phải tự động chuyển sang 2D Canvas.
3. **Zero Runtime Errors & Clean Code**:
   - Không xuất hiện lỗi hay cảnh báo đỏ trên Browser Console.
   - Code tách bạch: HTML (cấu trúc) - Tailwind/CSS (giao diện) - Vanilla JS/Component (logic trạng thái).