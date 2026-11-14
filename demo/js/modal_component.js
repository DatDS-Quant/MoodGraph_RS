/**
 * MovieDetailModalComponent — Module Hộp Thoại Chi Tiết Phim & Provenance Explorer
 * Triết lý thiết kế: Taste-Skill & Impeccable (Chống tràn viền, cân đối Grid 12 cột, Accordion tối giản)
 */
(function(window, document) {
  'use strict';

  // Trạng thái đóng/mở của thanh Accordion nguồn gốc giải thích đề xuất (Provenance)
  let isAccordionOpen = false;

  /**
   * Hàm tiện ích làm sạch và mã hóa ký tự HTML đặc biệt để chống lỗ hổng bảo mật XSS khi kết xuất văn bản động.
   * @param {*} str - Chuỗi hoặc giá trị cần mã hóa ký tự đặc biệt
   * @returns {string} Chuỗi an toàn sau khi mã hóa các ký tự &, <, >, ", '
   */
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  /**
   * Đóng hoặc mở thanh mở rộng Accordion hiển thị chi tiết nguồn gốc giải thích gợi ý (Provenance Explorer).
   * Điều khiển hiệu ứng chuyển động chiều cao (max-height), độ mờ (opacity) và xoay biểu tượng mũi tên chevron.
   * @param {boolean} [forceState] - Trạng thái cưỡng chế đóng/mở (tùy chọn)
   */
  function toggleAccordion(forceState) {
    if (typeof forceState === 'boolean') {
      isAccordionOpen = forceState;
    } else {
      isAccordionOpen = !isAccordionOpen;
    }

    const bodyEl = document.getElementById('prov-accordion-body');
    const chevronEl = document.getElementById('prov-accordion-chevron');
    const triggerBtn = document.getElementById('prov-accordion-trigger');

    if (bodyEl) {
      if (isAccordionOpen) {
        bodyEl.classList.remove('max-h-0', 'opacity-0', 'pointer-events-none');
        bodyEl.classList.add('max-h-[600px]', 'opacity-100', 'pointer-events-auto');
      } else {
        bodyEl.classList.add('max-h-0', 'opacity-0', 'pointer-events-none');
        bodyEl.classList.remove('max-h-[600px]', 'opacity-100', 'pointer-events-auto');
      }
    }

    if (chevronEl) {
      if (isAccordionOpen) {
        chevronEl.classList.add('rotate-180');
      } else {
        chevronEl.classList.remove('rotate-180');
      }
    }

    if (triggerBtn) {
      triggerBtn.setAttribute('aria-expanded', isAccordionOpen ? 'true' : 'false');
    }
  }

  /**
   * Kích hoạt hiển thị modal chi tiết bộ phim.
   * Ưu tiên ủy quyền thực thi qua đối tượng toàn cục window.MoodGraphApp; nếu chưa sẵn sàng sẽ thao tác trực tiếp trên DOM.
   * @param {string|number|Object} movieIdOrObj - Mã định danh phim hoặc đối tượng chứa thuộc tính movieId
   */
  function open(movieIdOrObj) {
    if (window.MoodGraphApp && typeof window.MoodGraphApp.openMovieDetailModal === 'function') {
      const id = (typeof movieIdOrObj === 'object' && movieIdOrObj !== null) ? movieIdOrObj.movieId : movieIdOrObj;
      window.MoodGraphApp.openMovieDetailModal(id);
      return;
    }
    const modal = document.getElementById('movie-detail-modal');
    if (modal) modal.classList.add('active');
  }

  /**
   * Ẩn modal chi tiết phim khi người dùng click nút đóng hoặc click vùng nền mờ bên ngoài backdrop.
   * @param {Event} [event] - Sự kiện click chuột từ giao diện người dùng
   */
  function close(event) {
    if (window.MoodGraphApp && typeof window.MoodGraphApp.closeMovieDetailModal === 'function') {
      window.MoodGraphApp.closeMovieDetailModal(event);
      return;
    }
    if (event && event.target && event.target !== event.currentTarget) return;
    const modal = document.getElementById('movie-detail-modal');
    if (modal) modal.classList.remove('active');
  }

  /**
   * Chuyển đổi tab hiển thị nguồn gốc giải thích giữa KG Path (Đồ thị tri thức), ALS Embedding (Không gian tiềm ẩn) và Mood Genome (Hệ gien tâm trạng).
   * @param {string} tabKey - Mã định danh tab cần kích hoạt ('kg_path', 'als_embed', 'mood_genome')
   */
  function switchTab(tabKey) {
    if (window.MoodGraphApp && typeof window.MoodGraphApp.switchProvenanceTab === 'function') {
      window.MoodGraphApp.switchProvenanceTab(tabKey);
    }
  }

  /**
   * Bật hoặc tắt trạng thái lưu bộ phim vào danh sách xem sau (Watchlist) của người dùng hiện tại.
   * @param {string|number} movieId - Mã định danh bộ phim
   */
  function toggleWatchlist(movieId) {
    if (window.MoodGraphApp && typeof window.MoodGraphApp.toggleWatchlist === 'function') {
      window.MoodGraphApp.toggleWatchlist(movieId);
    }
  }

  // Khởi tạo đối tượng thành phần modal chi tiết phim để đăng ký vào phạm vi toàn cục window
  const MovieDetailModalComponent = {
    open,
    close,
    toggleAccordion,
    toggleProvenanceAccordion: toggleAccordion,
    switchTab,
    toggleWatchlist
  };

  // Xuất thành phần ra phạm vi toàn cục window để các mô-đun khác có thể gọi trực tiếp
  window.MovieDetailModalComponent = MovieDetailModalComponent;

})(window, document);

