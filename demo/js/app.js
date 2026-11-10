/**
 * MOODGRAPH — TẠP CHÍ & PHÒNG THÍ NGHIỆM HỆ GỢI Ý PHIM ĐIỆN ẢNH
 * File: js/app.js
 * 
 * Bộ Điều Khiển Giao Diện Tương Tác & Động Cơ Tính Điểm Khám Phá (App Controller)
 * Đảm bảo 100% Client-Side, độc lập hoàn toàn, không phụ thuộc máy chủ backend, 60 FPS mượt mà.
 * 
 * Quy chuẩn nghiêm ngặt:
 * - 100% Tiếng Việt toàn diện, chuẩn mực học thuật và điện ảnh cao cấp.
 * - Tuyệt đối không dùng ký hiệu LaTeX và dấu dollar ($) trong chuỗi hiển thị.
 * - Triệt tiêu hoàn toàn màu xanh tím AI và cyan neon; áp dụng chuẩn bảng màu
 *   Dark Charcoal (#0B0F14, #141A24, #1B2230) & Warm Amber / Antique Bronze (#D97706, #F59E0B, #FDE68A).
 * - Typography chuẩn Editorial / Claude (Newsreader Serif + Plus Jakarta Sans).
 */

(function (window, document) {
  'use strict';

  // =========================================================================
  // 1. ĐỊNH NGHĨA TRẠNG THÁI TOÀN CỤC & TỰ ĐỘNG KHỞI TẠO (STATE STORE)
  // =========================================================================
  
  // Hàm tải dữ liệu an toàn từ LocalStorage
  function loadStorageJson(key, defaultValue) {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const item = window.localStorage.getItem(key);
        if (item) return JSON.parse(item);
      }
    } catch (e) {
      console.warn("Không thể đọc từ localStorage:", e);
    }
    return defaultValue;
  }

  // Hàm lưu dữ liệu an toàn vào LocalStorage
  function saveStorageJson(key, value) {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(key, JSON.stringify(value));
      }
    } catch (e) {
      console.warn("Không thể ghi vào localStorage:", e);
    }
  }

  const MoodGraphState = {
    // Chế độ xem: "modeA" (Trải Nghiệm Điện Ảnh) | "modeB" (Phòng Thí Nghiệm Học Thuật)
    activeMode: "modeA",

    // Persona đang kích hoạt trên Trang 1 ("user1" | "user2" | "user_cold")
    activePersonaId: "user1",
    currentUser: null, // Được gán động theo presetPersonas
    boostedGenres: [], // Thể loại được tăng cường thời gian thực khi chấm 4-5 sao (Closed-Loop)
    isColdStart: false, // Cờ nhận diện trạng thái Cold-Start

    // Tâm trạng điện ảnh đang kích hoạt ("all" hoặc id tâm trạng)
    activeMood: "all",

    // 4 Thanh trượt thử nghiệm gu thẩm mỹ (giá trị 0.0 - 1.0)
    sliders: {
      depth: 0.75,   // Chiều sâu cốt truyện (mặc định 75%)
      pacing: 0.60,  // Nhịp độ diễn biến (mặc định 60%)
      auteur: 0.85,  // Bản sắc tác giả (mặc định 85%)
      tone: 0.50     // Sắc thái cảm xúc (mặc định 50%)
    },

    // Bộ lọc thể loại trong danh mục
    activeGenre: "all",

    // Từ khóa tìm kiếm tức thì
    searchQuery: "",

    // Danh sách phim muốn xem (lưu trữ movieId)
    watchlist: loadStorageJson("moodgraph_watchlist", [318, 858, 1208, 6016]),

    // Điểm số người dùng đánh giá (lưu trữ { movieId: score })
    userRatings: loadStorageJson("moodgraph_user_ratings", {
      318: 5.0,
      858: 5.0,
      1208: 4.5,
      6016: 5.0
    }),

    // Trạng thái cho Mode B (Phòng Thí Nghiệm)
    selectedLabUser: "user1",
    consensusFilter: "all", // "all" | "overlap" | "unique"
    heatmapMetric: "spearman", // "spearman" | "jaccard"
    activeInterlockMovieId: null,

    // Bộ nhớ đệm danh sách phim đã chấm điểm theo slider & mood
    dynamicRankedMovies: []
  };

  // Công khai trạng thái toàn cục để kiểm thử và liên kết
  window.MoodGraphState = MoodGraphState;

  // Bảng nhãn cảm xúc điện ảnh chuẩn mực cho thang điểm 1-5 sao
  const RATING_LABELS = {
    1.0: "1.0★ — Rất thất vọng / Không đọng lại gì",
    1.5: "1.5★ — Dưới kỳ vọng",
    2.0: "2.0★ — Kịch bản gượng gạo / Xem tạm",
    2.5: "2.5★ — Mức trung bình điện ảnh",
    3.0: "3.0★ — Khá / Có điểm sáng nhất định",
    3.5: "3.5★ — Hay / Rất đáng thưởng thức",
    4.0: "4.0★ — Rất hay / Đậm dấu ấn nghệ thuật",
    4.5: "4.5★ — Tác phẩm xuất sắc / Cảm xúc sâu sắc",
    5.0: "5.0★ — Kiệt tác điện ảnh đỉnh cao"
  };

  // =========================================================================
  // 2. HÀM TIỆN ÍCH TRỢ GIÚP (HELPER UTILITIES)
  // =========================================================================

  function getMovieById(movieId) {
    if (!window.MOCK_DATA || !window.MOCK_DATA.catalog) return null;
    const mid = Number(movieId);
    return window.MOCK_DATA.catalog.find(m => m.movieId === mid) || null;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  // Khử dấu tiếng Việt để tìm kiếm không dấu
  function removeVietnameseTones(str) {
    if (!str) return '';
    let s = str.toLowerCase();
    s = s.replace(/à|á|ạ|ả|ã|â|ầ|ấ|ậ|ẩ|ẫ|ă|ằ|ắ|ặ|ẳ|ẵ/g, 'a');
    s = s.replace(/è|é|ẹ|ẻ|ẽ|ê|ề|ế|ệ|ể|ễ/g, 'e');
    s = s.replace(/ì|í|ị|ỉ|ĩ/g, 'i');
    s = s.replace(/ò|ó|ọ|ỏ|õ|ô|ồ|ố|ộ|ổ|ỗ|ơ|ờ|ớ|ợ|ở|ỡ/g, 'o');
    s = s.replace(/ù|ú|ụ|ủ|ũ|ư|ừ|ứ|ự|ử|ữ/g, 'u');
    s = s.replace(/ỳ|ý|ỵ|ỷ|ỹ/g, 'y');
    s = s.replace(/đ/g, 'd');
    s = s.replace(/\u0300|\u0301|\u0303|\u0309|\u0323/g, '');
    s = s.replace(/\u02C6|\u0306|\u031B/g, '');
    return s;
  }

  // Tạo thẻ poster an toàn: Nếu ảnh ngoài bị lỗi hoặc offline thì nạp ngay poster SVG độc lập
  function renderPosterImgHtml(movie, extraClass) {
    const titleSafe = escapeHtml(movie.vietnameseTitle || movie.cleanTitle || movie.title);
    const posterClass = extraClass || 'movie-poster-img';
    const fallbackSvg = movie.posterFallbackSvg || generateFallbackSvg(movie);

    return `
      <img src="${movie.posterUrl}" 
           alt="${titleSafe}" 
           loading="lazy"
           class="${posterClass}" 
           onerror="this.onerror=null; this.src='${fallbackSvg}';">
    `;
  }

  // Tạo SVG poster tự chứa bền vững theo chuẩn phong cách Editorial
  function generateFallbackSvg(movie) {
    const title = escapeHtml(movie.vietnameseTitle || movie.cleanTitle || 'Phim Điện Ảnh');
    const year = movie.year || '';
    const genre = movie.primaryGenre || 'Điện ảnh';
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450">
        <defs>
          <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0B0F14"/>
            <stop offset="50%" stop-color="#141A24"/>
            <stop offset="100%" stop-color="#0F141C"/>
          </linearGradient>
        </defs>
        <rect width="300" height="450" fill="url(#bgGrad)"/>
        <rect x="12" y="12" width="276" height="426" fill="none" stroke="rgba(217,119,6,0.35)" stroke-width="1.5" rx="8"/>
        <circle cx="150" cy="180" r="42" fill="none" stroke="rgba(245,158,11,0.25)" stroke-width="1"/>
        <polygon points="144,165 162,180 144,195" fill="#D97706"/>
        <text x="150" y="270" font-family="Georgia, serif" font-size="16" font-weight="600" fill="#F8FAFC" text-anchor="middle">${title}</text>
        <text x="150" y="300" font-family="sans-serif" font-size="12" fill="#94A3B8" text-anchor="middle">${genre}</text>
        <text x="150" y="340" font-family="monospace" font-size="12" fill="#F59E0B" text-anchor="middle" letter-spacing="2">${year}</text>
        <text x="150" y="415" font-family="sans-serif" font-size="10" fill="#64748B" text-anchor="middle">MOODGRAPH EDITORIAL ARCHIVE</text>
      </svg>
    `.trim().replace(/\s+/g, ' ');
    return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
  }

  // =========================================================================
  // 3. TOAST THÔNG BÁO TIẾNG VIỆT THANH LỊCH (EDITORIAL TOAST ENGINE)
  // =========================================================================

  function showToast(title, message, iconType) {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'fixed bottom-5 right-5 z-[200] flex flex-col gap-2.5 max-w-sm pointer-events-none';
      document.body.appendChild(container);
    }

    let iconSvg = '';
    if (iconType === 'star') {
      iconSvg = `
        <svg class="w-5 h-5 text-[#F59E0B] shrink-0 mt-0.5" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
        </svg>
      `;
    } else if (iconType === 'remove') {
      iconSvg = `
        <svg class="w-5 h-5 text-[#E11D48] shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
      `;
    } else {
      // Default: Emerald Success / Amber Info
      iconSvg = `
        <svg class="w-5 h-5 text-[#10B981] shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
      `;
    }

    const toast = document.createElement('div');
    toast.className = 'pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl bg-[#141A24] border border-[rgba(217,119,6,0.35)] shadow-2xl transition-all duration-300 transform translate-y-3 opacity-0';
    toast.innerHTML = `
      ${iconSvg}
      <div class="flex-1 min-w-0">
        <h4 class="text-xs font-semibold text-white tracking-tight">${escapeHtml(title)}</h4>
        <p class="text-[11px] text-[#94A3B8] mt-0.5 leading-snug">${escapeHtml(message)}</p>
      </div>
      <button onclick="this.parentElement.remove()" class="text-[#64748B] hover:text-white text-xs p-1">✕</button>
    `;

    if (container && typeof container.appendChild === 'function') {
      container.appendChild(toast);
    }

    const safeRaf = typeof requestAnimationFrame === 'function' ? requestAnimationFrame : (cb => setTimeout(cb, 16));
    safeRaf(() => {
      toast.classList.remove('translate-y-3', 'opacity-0');
      toast.classList.add('translate-y-0', 'opacity-100');
    });

    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-x-4');
      setTimeout(() => {
        if (toast.parentElement) toast.remove();
      }, 300);
    }, 3500);
  }

  // =========================================================================
  // 4. BỘ ĐIỀU PHỐI GIAO DIỆN & BỘ CHUYỂN CHẾ ĐỘ (VIEW SWITCHER 2 TRANG)
  // =========================================================================

  function switchMode(targetMode) {
    MoodGraphState.activeMode = targetMode;

    const btnModeA = document.getElementById('nav-btn-mode-a') || document.getElementById('tab-mode-a');
    const btnModeB = document.getElementById('nav-btn-mode-b') || document.getElementById('tab-mode-b');
    const containerModeA = document.getElementById('mode-a-container');
    const containerModeB = document.getElementById('mode-b-container');

    if (targetMode === 'modeA') {
      if (btnModeA) btnModeA.classList.add('active');
      if (btnModeB) btnModeB.classList.remove('active');

      if (containerModeA) {
        containerModeA.classList.remove('hidden');
      }
      if (containerModeB) {
        containerModeB.classList.add('hidden');
      }
      // Đảm bảo dữ liệu Trang 1 luôn tươi mới
      updateDynamicRecommendations();
    } else {
      if (btnModeA) btnModeA.classList.remove('active');
      if (btnModeB) btnModeB.classList.add('active');

      if (containerModeA) {
        containerModeA.classList.add('hidden');
      }
      if (containerModeB) {
        containerModeB.classList.remove('hidden');
      }

      // Khởi động các thành phần Trang 2 nếu có sẵn
      if (window.AcademicLab && typeof window.AcademicLab.init === 'function') {
        window.AcademicLab.init();
      } else {
        // Fallback tự kết xuất các bảng đo lường học thuật của Mode B nếu academic_lab.js chưa tải
        renderHeadToHeadComparison();
        renderCorrelationHeatmap();
        renderOfflineBenchmarks();
        renderColdStartDiagnostics();
        renderLongTailDiagnostics();
      }
    }
  }

  // =========================================================================
  // 5. BỘ CHỌN TÂM TRẠNG ĐIỆN ẢNH (MOOD SELECTOR — 7 MIỀN CẢM XÚC)
  // =========================================================================

  function renderMoodChips() {
    const container = document.getElementById('mood-chips-container');
    if (!container || !window.MOCK_DATA || !window.MOCK_DATA.moods) return;

    const moods = window.MOCK_DATA.moods;
    const currentMood = MoodGraphState.activeMood;

    let html = `
      <button onclick="MoodGraphApp.selectMood('all')" 
              class="mood-chip-btn ${currentMood === 'all' ? 'active' : ''}">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <polygon points="12 8 8 12 12 16 16 12 12 8"></polygon>
        </svg>
        <span>Tất cả tâm trạng</span>
      </button>
    `;

    moods.forEach(m => {
      const isActive = currentMood === m.id;
      html += `
        <button onclick="MoodGraphApp.selectMood('${m.id}')" 
                class="mood-chip-btn ${isActive ? 'active' : ''}"
                title="${escapeHtml(m.description)}">
          ${m.iconSvg || ''}
          <span>${escapeHtml(m.name)}</span>
        </button>
      `;
    });

    container.innerHTML = html;

    // Cập nhật nhãn văn bản hiển thị tâm trạng hiện tại
    const displayEl = document.getElementById('active-mood-display');
    if (displayEl) {
      if (currentMood === 'all') {
        displayEl.textContent = "Tất cả tâm trạng";
      } else {
        const found = moods.find(x => x.id === currentMood);
        displayEl.textContent = found ? found.name : currentMood;
      }
    }
  }

  function selectMood(moodId) {
    if (MoodGraphState.activeMood === moodId && moodId !== 'all') {
      // Toggle off nếu nhấn lại mood đang active
      MoodGraphState.activeMood = 'all';
    } else {
      MoodGraphState.activeMood = moodId;
    }

    // Nếu chọn một mood cụ thể, tự động tinh chỉnh nhẹ các giá trị thanh trượt tương ứng
    if (MoodGraphState.activeMood !== 'all' && window.MOCK_DATA && window.MOCK_DATA.moods) {
      const moodObj = window.MOCK_DATA.moods.find(m => m.id === MoodGraphState.activeMood);
      if (moodObj && moodObj.targetWeights) {
        const tw = moodObj.targetWeights;
        MoodGraphState.sliders.depth = tw.depth;
        MoodGraphState.sliders.pacing = tw.pacing;
        MoodGraphState.sliders.auteur = tw.auteur;
        MoodGraphState.sliders.tone = tw.tone;

        // Cập nhật giá trị trên DOM
        syncSliderInputs();
      }
    }

    renderMoodChips();
    updateDynamicRecommendations();

    const moodName = MoodGraphState.activeMood === 'all' 
      ? 'Tất cả tâm trạng' 
      : (window.MOCK_DATA.moods.find(m => m.id === MoodGraphState.activeMood)?.name || MoodGraphState.activeMood);

    showToast("Đã Chuyển Tâm Trạng", `Không gian gợi ý đã đồng bộ theo miền cảm xúc: ${moodName}.`, 'info');
  }

  // =========================================================================
  // 6. THANH TRƯỢT THỬ NGHIỆM ĐỔI GU THỜI GIAN THỰC (LIVE PREFERENCE SLIDERS)
  // Phản hồi siêu tốc < 5ms (60 FPS) thông qua hàm MoodEngine.calculateDynamicScores
  // Bổ sung chú giải ngữ nghĩa động (Item 3)
  // =========================================================================

  const SEMANTIC_SLIDER_DESCRIPTIONS = {
    depth: {
      low: "Ưu tiên kịch bản trực diện, giải trí nhẹ nhàng, thư giãn đầu óc",
      mid: "Cốt truyện cân bằng giữa tính giải trí và chiều sâu xung đột tâm lý",
      high: "Đang ưu tiên kịch bản triết lý, đa tầng suy ngẫm"
    },
    pacing: {
      low: "Tiết tấu chậm rãi, nhiều khoảng lặng suy tưởng và chiêm nghiệm",
      mid: "Nhịp phim vừa phải, đan xen kịch tính và chiều sâu",
      high: "Đang ưu tiên phim hành động, nghẹt thở, cao trào liên tục dồn dập"
    },
    auteur: {
      low: "Phong cách bom tấn đại chúng, cấu trúc Hollywood kinh điển",
      mid: "Giao thoa hài hòa giữa thị hiếu đại chúng và góc nhìn nghệ thuật độc lập",
      high: "Đậm chất auteur cá tính, phong cách đạo diễn độc bản"
    },
    tone: {
      low: "Không khí u tối, tâm lý gai góc, hiện thực trần trụi và giằng xé",
      mid: "Cân bằng hiện thực sâu sắc, gam màu trung tính",
      high: "Đang ưu tiên cảm xúc sâu lắng, ấm áp, truyền cảm hứng sống tích cực"
    }
  };

  function updateSliderSemanticHint(axis, valNum) {
    const descEl = document.getElementById(`desc-${axis}`);
    if (!descEl) return;
    const txtSpan = descEl.querySelector('span');
    const texts = SEMANTIC_SLIDER_DESCRIPTIONS[axis];
    if (!texts) return;

    let text = texts.mid;
    if (valNum < 35) {
      text = texts.low;
    } else if (valNum >= 70) {
      text = texts.high;
    }

    if (txtSpan) {
      txtSpan.textContent = text;
    } else {
      descEl.textContent = text;
    }
  }

  function updateAllSliderSemanticHints() {
    ['depth', 'pacing', 'auteur', 'tone'].forEach(axis => {
      const valPct = Math.round((MoodGraphState.sliders[axis] || 0.5) * 100);
      updateSliderSemanticHint(axis, valPct);
    });
  }

  function syncSliderInputs() {
    const axes = ['depth', 'pacing', 'auteur', 'tone'];
    axes.forEach(axis => {
      const sliderEl = document.getElementById(`slider-${axis}`);
      const valEl = document.getElementById(`val-${axis}`);
      const valPct = Math.round(MoodGraphState.sliders[axis] * 100);

      if (sliderEl) sliderEl.value = valPct;
      if (valEl) valEl.textContent = `${valPct}%`;
      updateSliderSemanticHint(axis, valPct);
    });
  }

  function onSliderChange(axis, value) {
    const valNum = Number(value);
    MoodGraphState.sliders[axis] = valNum / 100.0;

    // Cập nhật nhãn số %
    const valEl = document.getElementById(`val-${axis}`);
    if (valEl) {
      valEl.textContent = `${valNum}%`;
    }

    // Cập nhật chú giải ngữ nghĩa động tức thì (Item 3)
    updateSliderSemanticHint(axis, valNum);

    // Tái tính toán điểm số gợi ý động tức thì
    updateDynamicRecommendations();
  }

  function resetSliders() {
    MoodGraphState.sliders = {
      depth: 0.75,
      pacing: 0.60,
      auteur: 0.85,
      tone: 0.50
    };
    MoodGraphState.activeMood = 'all';

    syncSliderInputs();
    renderMoodChips();
    updateDynamicRecommendations();

    showToast("Đã Đặt Lại Gu Mặc Định", "Các thanh trượt thẩm mỹ đã được đưa về cấu hình cân bằng ban đầu.", 'info');
  }

  // =========================================================================
  // 7. ĐỘNG CƠ TÁI TÍNH TOÁN ĐIỂM SỐ GỢI Ý ĐỘNG (DYNAMIC CALCULATION ENGINE)
  // =========================================================================

  function updateDynamicRecommendations() {
    if (!window.MoodEngine || !window.MOCK_DATA || !window.MOCK_DATA.catalog) return;

    const tStart = performance.now();

    // Chuẩn bị tham số tùy biến động theo Người dùng & Phản hồi Closed-Loop
    const userOpts = {
      boostedGenres: MoodGraphState.boostedGenres || [],
      favoriteGenres: (MoodGraphState.currentUser && MoodGraphState.currentUser.topFavoriteGenres) 
        ? MoodGraphState.currentUser.topFavoriteGenres 
        : [],
      isColdStart: Boolean(MoodGraphState.isColdStart)
    };

    // Gọi trực tiếp thuật toán Cosine Similarity + Hybrid RRF trong mock_data.js
    const scoredList = window.MoodEngine.calculateDynamicScores(
      MoodGraphState.sliders,
      MoodGraphState.activeMood,
      window.MOCK_DATA.catalog,
      userOpts
    );

    const tEnd = performance.now();
    const latencyMs = (tEnd - tStart).toFixed(1);

    // Cập nhật huy hiệu đo lường độ trễ thực nghiệm
    const badge = document.getElementById('tuner-latency-badge');
    if (badge) {
      badge.textContent = `Độ trễ: ${latencyMs} ms`;
    }

    MoodGraphState.dynamicRankedMovies = scoredList;

    // Lọc theo từ khóa tìm kiếm nếu có
    let filteredList = scoredList;
    if (MoodGraphState.searchQuery && MoodGraphState.searchQuery.trim() !== '') {
      const q = removeVietnameseTones(MoodGraphState.searchQuery.trim());
      filteredList = scoredList.filter(m => {
        const vnTitle = removeVietnameseTones(m.vietnameseTitle || '');
        const cleanTitle = removeVietnameseTones(m.cleanTitle || m.title || '');
        const director = removeVietnameseTones(m.director || '');
        return vnTitle.includes(q) || cleanTitle.includes(q) || director.includes(q);
      });
    }

    // Tái kết xuất Hero Banner (Top 1) và Lưới Phim Gợi Ý (Top 2-11)
    if (filteredList.length > 0) {
      renderHeroBanner(filteredList[0]);
      renderRecommendationsGrid(filteredList.slice(1, 11));
    } else {
      // Trường hợp tìm kiếm không ra kết quả
      renderHeroBanner(null);
      renderRecommendationsGrid([]);
    }

    // Cập nhật lại danh mục phim Catalog
    renderCatalogGrid();
  }

  // =========================================================================
  // 8. KẾT XUẤT HERO BANNER (TOP 1 PERSONALIZED SHOWCASE)
  // =========================================================================

  function renderHeroBanner(topMovie) {
    const container = document.getElementById('hero-banner-section');
    if (!container) return;

    if (!topMovie) {
      container.innerHTML = `
        <div class="p-8 text-center text-[#94A3B8] font-mono text-xs">
          Không tìm thấy tác phẩm đề xuất phù hợp với từ khóa "${escapeHtml(MoodGraphState.searchQuery)}".
        </div>
      `;
      return;
    }

    const inWatchlist = MoodGraphState.watchlist.includes(topMovie.movieId);
    const titleVn = escapeHtml(topMovie.vietnameseTitle || topMovie.cleanTitle || topMovie.title);
    const titleEn = escapeHtml(topMovie.cleanTitle || topMovie.title);
    const matchPct = topMovie.compatibilityPct || 98;
    const ratingScore = MoodGraphState.userRatings[topMovie.movieId] || 0;

    // Xây dựng dòng giải thích lý do gợi ý Provenance bằng tiếng Việt sâu sắc
    let provenanceExplanation = topMovie.provenanceSummary;
    if (!provenanceExplanation) {
      provenanceExplanation = `Khớp ${matchPct}% gu thẩm mỹ tác giả của đạo diễn ${topMovie.director || 'hàng đầu'}, hội tụ chiều sâu cốt truyện và đặc trưng nhịp độ bạn tìm kiếm.`;
    }

    const backdropImg = topMovie.backdropUrl || topMovie.posterUrl;

    container.innerHTML = `
      <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#0F141C] via-[#141A24] to-[#0B0F14] border border-[rgba(245,158,11,0.3)] shadow-2xl">
        
        <!-- Ảnh nền mờ phía sau tạo chiều sâu điện ảnh -->
        <div class="absolute inset-0 opacity-20 bg-cover bg-center filter blur-md pointer-events-none" 
             style="background-image: url('${backdropImg}');"></div>
        <div class="absolute inset-0 bg-gradient-to-t from-[#0B0F14] via-[rgba(11,15,20,0.85)] to-transparent pointer-events-none"></div>

        <div class="relative z-10 p-6 sm:p-8 lg:p-10 flex flex-col lg:flex-row items-center gap-8">
          
          <!-- Poster Phim Đứng Đầu -->
          <div class="w-48 sm:w-56 lg:w-64 shrink-0 rounded-xl overflow-hidden shadow-2xl border border-[rgba(217,119,6,0.4)] aspect-[2/3] bg-[#0A0D14] cursor-pointer group"
               onclick="MoodGraphApp.openMovieDetailModal(${topMovie.movieId})">
            ${renderPosterImgHtml(topMovie, 'w-full h-full object-cover transition-transform duration-500 group-hover:scale-105')}
          </div>

          <!-- Thông Tin Chi Tiết & Giải Thích Provenance -->
          <div class="flex-1 space-y-4 text-left">
            
            <!-- Badges Hàng Đầu -->
            <div class="flex flex-wrap items-center gap-2">
              <span class="px-2.5 py-1 rounded-full text-[11px] font-bold tracking-wider uppercase bg-[rgba(217,119,6,0.15)] text-[#FDE68A] border border-[rgba(217,119,6,0.4)] flex items-center gap-1.5 font-mono">
                <span>👑</span>
                <span>LỰA CHỌN TỐI ƯU SỐ 1 CHO BẠN</span>
              </span>
              <span class="px-2.5 py-1 rounded-full text-[11px] font-mono font-bold bg-[#1B2230] text-[#10B981] border border-[rgba(16,185,129,0.35)]">
                ĐỘ PHÙ HỢP ${matchPct}%
              </span>
              <span class="px-2.5 py-1 rounded-full text-[11px] font-mono text-[#FBBF24] bg-[#141A24] border border-[rgba(255,255,255,0.08)]">
                ${topMovie.moodLabel || 'Điện ảnh đặc sắc'}
              </span>
            </div>

            <!-- Tiêu Đề Phim Chuẩn Editorial Serif -->
            <div>
              <h1 class="text-2xl sm:text-3xl lg:text-4xl font-semibold text-white tracking-tight leading-tight font-serif">
                ${titleVn}
              </h1>
              <div class="text-xs sm:text-sm text-[#94A3B8] italic mt-0.5">
                ${titleEn} • ${topMovie.year} • Đạo diễn: <strong class="text-white not-italic">${topMovie.director || 'N/A'}</strong>
              </div>
            </div>

            <!-- Thông Số Kỹ Thuật -->
            <div class="flex flex-wrap items-center gap-3 text-xs text-[#CBD5E1]">
              <span class="text-[#F59E0B] font-mono font-bold flex items-center gap-1">
                <svg class="w-3.5 h-3.5 fill-[#F59E0B]" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                IMDb ${topMovie.ratingAvg || 4.5} / 5.0
              </span>
              <span>•</span>
              <span class="font-mono">${topMovie.duration || '120 phút'}</span>
              <span>•</span>
              <span class="text-[#94A3B8]">${(topMovie.genres || []).join(', ')}</span>
            </div>

            <!-- Tóm Tắt Cốt Truyện -->
            <p class="text-xs sm:text-sm text-[#CBD5E1] line-clamp-3 leading-relaxed max-w-2xl">
              ${escapeHtml(topMovie.synopsis || 'Tác phẩm điện ảnh sâu sắc với giá trị nghệ thuật và nhân văn vượt thời gian.')}
            </p>

            <!-- Thẻ Giải Thích Nguồn Gốc Gợi Ý (Provenance Box) -->
            <div class="p-3 rounded-lg bg-[#0F141C] border border-[rgba(217,119,6,0.3)] space-y-1">
              <div class="flex items-center gap-1.5 text-[11px] font-mono text-[#F59E0B] font-semibold">
                <span>🔍 Minh chứng gợi ý:</span>
                <span class="text-[#A7F3D0]">${topMovie.primaryGenre || 'Điện ảnh'}</span>
                <span class="text-[#64748B]">•</span>
                <span class="text-[#FDE68A]">Cosine ${(topMovie.cosineSimilarity ? topMovie.cosineSimilarity.toFixed(3) : '0.945')}</span>
              </div>
              <p class="text-xs text-[#E2E8F0] leading-snug">
                ${escapeHtml(provenanceExplanation)}
              </p>
            </div>

            <!-- Nút Hành Động -->
            <div class="flex flex-wrap items-center gap-3 pt-2">
              <button onclick="MoodGraphApp.openMovieDetailModal(${topMovie.movieId})" 
                      class="btn-primary text-xs sm:text-sm px-4 py-2">
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="16" x2="12" y2="12"></line>
                  <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                <span>Khám Phá Chi Tiết & Tọa Độ 3D</span>
              </button>

              <button onclick="MoodGraphApp.toggleWatchlist(${topMovie.movieId})" 
                      class="btn-secondary text-xs sm:text-sm px-4 py-2 ${inWatchlist ? 'border-[#10B981] text-[#10B981]' : ''}">
                <svg class="w-4 h-4 ${inWatchlist ? 'text-[#10B981]' : ''}" viewBox="0 0 24 24" fill="${inWatchlist ? '#10B981' : 'none'}" stroke="currentColor" stroke-width="2">
                  <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                </svg>
                <span>${inWatchlist ? 'Đã Lưu Trong Danh Sách Xem ✓' : '+ Thêm Vào Danh Sách Xem'}</span>
              </button>
            </div>

          </div>

        </div>

      </div>
    `;
  }

  // =========================================================================
  // 9. KẾT XUẤT LƯỚI PHIM GỢI Ý (ADAPTIVE RECOMMENDATIONS GRID)
  // =========================================================================

  function renderRecommendationsGrid(movies) {
    const container = document.getElementById('recommendations-grid');
    if (!container) return;

    if (!movies || movies.length === 0) {
      container.innerHTML = `
        <div class="col-span-full py-10 text-center text-[#94A3B8] text-xs font-mono">
          Không có thêm tác phẩm đề xuất phù hợp trong bộ lọc này.
        </div>
      `;
      return;
    }

    let html = '';
    movies.forEach(movie => {
      const inWatchlist = MoodGraphState.watchlist.includes(movie.movieId);
      const titleVn = escapeHtml(movie.vietnameseTitle || movie.cleanTitle || movie.title);
      const titleEn = escapeHtml(movie.cleanTitle || movie.title);
      const matchPct = movie.compatibilityPct || 92;
      const userRating = MoodGraphState.userRatings[movie.movieId] || 0;

      // Xây dựng nhãn tóm tắt lý do gợi ý súc tích
      let reasonBadge = movie.primaryMood 
        ? (window.MOCK_DATA.moods.find(m => m.id === movie.primaryMood)?.shortName || 'Tâm lý') 
        : (movie.primaryGenre || 'Điện ảnh');

      let explanationText = movie.provenanceSummary;
      if (!explanationText) {
        explanationText = `Khớp ${matchPct}% gu cốt truyện & phong cách đạo diễn ${movie.director || 'tác giả'}.`;
      }

      html += `
        <div class="movie-card group" onclick="MoodGraphApp.openMovieDetailModal(${movie.movieId})">
          
          <!-- Hộp Poster -->
          <div class="movie-poster-box">
            ${renderPosterImgHtml(movie)}
            
            <!-- Huy hiệu độ tương thích -->
            <div class="compatibility-badge">
              <span class="w-1.5 h-1.5 rounded-full bg-[#10B981]"></span>
              <span>${matchPct}%</span>
            </div>

            <!-- Nút Lưu Nhanh Vào Danh Sách Xem -->
            <button onclick="event.stopPropagation(); MoodGraphApp.toggleWatchlist(${movie.movieId})" 
                    class="absolute top-2 left-2 p-1.5 rounded-lg bg-[rgba(11,15,20,0.85)] hover:bg-[#1B2230] border border-[rgba(255,255,255,0.1)] text-white transition-all"
                    title="${inWatchlist ? 'Xóa khỏi Danh Sách Xem' : 'Lưu vào Danh Sách Xem'}">
              <svg class="w-4 h-4 ${inWatchlist ? 'text-[#10B981]' : 'text-white'}" viewBox="0 0 24 24" fill="${inWatchlist ? '#10B981' : 'none'}" stroke="currentColor" stroke-width="2">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
              </svg>
            </button>
          </div>

          <!-- Nội Dung Thẻ Phim -->
          <div class="p-3.5 space-y-2 flex-1 flex flex-col justify-between">
            
            <div class="space-y-1">
              <div class="flex items-center justify-between text-[11px] text-[#94A3B8] font-mono">
                <span>${movie.year} • ${movie.primaryGenre || 'Film'}</span>
                <span class="text-[#F59E0B] font-bold flex items-center gap-0.5">
                  ★ ${movie.ratingAvg || 4.2}
                </span>
              </div>

              <h3 class="text-sm font-semibold text-white leading-tight font-serif line-clamp-1 group-hover:text-[#FBBF24] transition-colors">
                ${titleVn}
              </h3>
              <div class="text-[11px] text-[#94A3B8] italic truncate">
                ${titleEn}
              </div>
            </div>

            <!-- Thẻ Provenance Tinh Tế -->
            <div class="pt-1.5 border-t border-[rgba(255,255,255,0.06)] space-y-1.5">
              <div class="flex items-center gap-1.5">
                <span class="provenance-tag p1-genre">${reasonBadge}</span>
                <span class="text-[10px] text-[#94A3B8] truncate">${movie.director || ''}</span>
              </div>
              <p class="text-[10px] text-[#94A3B8] line-clamp-2 leading-relaxed">
                ${escapeHtml(explanationText)}
              </p>
            </div>

            <!-- Widget Chấm Điểm Sao 1-5 Sao -->
            <div class="pt-2 border-t border-[rgba(255,255,255,0.06)] flex items-center justify-between" onclick="event.stopPropagation()">
              <span class="text-[10px] text-[#64748B] font-mono">Đánh giá:</span>
              <div class="flex items-center gap-0.5">
                ${[1, 2, 3, 4, 5].map(starVal => {
                  const isFilled = userRating >= starVal;
                  return `
                    <button onclick="MoodGraphApp.submitRating(${movie.movieId}, ${starVal})" 
                            class="p-0.5 text-xs transition-transform hover:scale-125 focus:outline-none" 
                            title="${starVal} sao — ${RATING_LABELS[starVal]}">
                      <svg class="w-3.5 h-3.5 ${isFilled ? 'text-[#F59E0B] fill-[#F59E0B]' : 'text-[#475569] fill-none'}" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                      </svg>
                    </button>
                  `;
                }).join('')}
              </div>
            </div>

          </div>

        </div>
      `;
    });

    container.innerHTML = html;
  }

  // =========================================================================
  // 10. KẾT XUẤT BỘ LỌC 19 THỂ LOẠI & DANH MỤC TOÀN BỘ PHIM (CATALOG)
  // =========================================================================

  function renderGenreFilters() {
    const container = document.getElementById('genre-filter-track');
    if (!container || !window.MOCK_DATA || !window.MOCK_DATA.genres) return;

    const genres = window.MOCK_DATA.genres;
    const currentGenre = MoodGraphState.activeGenre;

    let html = '';
    genres.forEach(g => {
      const isActive = currentGenre === g.id;
      html += `
        <button onclick="MoodGraphApp.selectGenreFilter('${g.id}')" 
                class="px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all border ${
                  isActive 
                    ? 'bg-[#D97706] text-white border-[#D97706] shadow-md shadow-[#D97706]/20 font-semibold' 
                    : 'bg-[#141A24] text-[#94A3B8] border-[rgba(255,255,255,0.08)] hover:text-white hover:border-[#D97706]'
                }">
          ${escapeHtml(g.name)}
        </button>
      `;
    });

    container.innerHTML = html;
  }

  function selectGenreFilter(genreId) {
    MoodGraphState.activeGenre = genreId;
    renderGenreFilters();
    renderCatalogGrid();
  }

  function renderCatalogGrid() {
    const container = document.getElementById('catalog-grid');
    const emptyState = document.getElementById('catalog-empty-state');
    const badge = document.getElementById('catalog-count-badge');
    if (!container || !window.MOCK_DATA || !window.MOCK_DATA.catalog) return;

    const allMovies = window.MOCK_DATA.catalog;
    let filtered = allMovies;

    // Lọc theo thể loại
    if (MoodGraphState.activeGenre !== 'all') {
      const gObj = (window.MOCK_DATA.genres || []).find(g => g.id === MoodGraphState.activeGenre);
      const genreEn = gObj ? gObj.enName : MoodGraphState.activeGenre;
      filtered = filtered.filter(m => (m.genres || []).includes(genreEn));
    }

    // Lọc theo từ khóa tìm kiếm
    if (MoodGraphState.searchQuery && MoodGraphState.searchQuery.trim() !== '') {
      const q = removeVietnameseTones(MoodGraphState.searchQuery.trim());
      filtered = filtered.filter(m => {
        const vnTitle = removeVietnameseTones(m.vietnameseTitle || '');
        const cleanTitle = removeVietnameseTones(m.cleanTitle || m.title || '');
        const director = removeVietnameseTones(m.director || '');
        return vnTitle.includes(q) || cleanTitle.includes(q) || director.includes(q);
      });
    }

    // Cập nhật số lượng
    if (badge) {
      badge.textContent = `Hiển thị ${filtered.length} / ${allMovies.length} tác phẩm`;
    }

    if (filtered.length === 0) {
      container.classList.add('hidden');
      if (emptyState) emptyState.classList.remove('hidden');
      return;
    }

    container.classList.remove('hidden');
    if (emptyState) emptyState.classList.add('hidden');

    let html = '';
    filtered.forEach(movie => {
      const inWatchlist = MoodGraphState.watchlist.includes(movie.movieId);
      const titleVn = escapeHtml(movie.vietnameseTitle || movie.cleanTitle || movie.title);
      const titleEn = escapeHtml(movie.cleanTitle || movie.title);
      const userRating = MoodGraphState.userRatings[movie.movieId] || 0;

      html += `
        <div class="movie-card group" onclick="MoodGraphApp.openMovieDetailModal(${movie.movieId})">
          <div class="movie-poster-box">
            ${renderPosterImgHtml(movie)}
            
            <button onclick="event.stopPropagation(); MoodGraphApp.toggleWatchlist(${movie.movieId})" 
                    class="absolute top-2 right-2 p-1.5 rounded-lg bg-[rgba(11,15,20,0.85)] hover:bg-[#1B2230] border border-[rgba(255,255,255,0.1)] text-white transition-all"
                    title="${inWatchlist ? 'Xóa khỏi Danh Sách Xem' : 'Lưu vào Danh Sách Xem'}">
              <svg class="w-4 h-4 ${inWatchlist ? 'text-[#10B981]' : 'text-white'}" viewBox="0 0 24 24" fill="${inWatchlist ? '#10B981' : 'none'}" stroke="currentColor" stroke-width="2">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
              </svg>
            </button>
          </div>

          <div class="p-3 space-y-1.5 flex-1 flex flex-col justify-between">
            <div>
              <div class="flex items-center justify-between text-[10px] text-[#94A3B8] font-mono">
                <span>${movie.year}</span>
                <span class="text-[#F59E0B] font-bold">★ ${movie.ratingAvg || 4.0}</span>
              </div>
              <h3 class="text-xs font-semibold text-white leading-tight font-serif line-clamp-1 group-hover:text-[#FBBF24]">
                ${titleVn}
              </h3>
              <div class="text-[10px] text-[#94A3B8] italic truncate">
                ${titleEn}
              </div>
            </div>

            <div class="pt-1.5 border-t border-[rgba(255,255,255,0.06)] flex items-center justify-between text-[10px] text-[#64748B]">
              <span>${movie.primaryGenre || 'Drama'}</span>
              <span class="truncate max-w-[100px]">${movie.director || ''}</span>
            </div>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
  }

  function resetFilters() {
    MoodGraphState.activeGenre = 'all';
    MoodGraphState.searchQuery = '';
    
    const searchInputs = [
      document.getElementById('global-search-input'),
      document.getElementById('movie-search-input')
    ];
    searchInputs.forEach(input => {
      if (input) input.value = '';
    });

    renderGenreFilters();
    updateDynamicRecommendations();
    showToast("Đã Đặt Lại Bộ Lọc", "Đã xóa toàn bộ từ khóa tìm kiếm và đưa thể loại về Tất cả.", 'info');
  }

  // =========================================================================
  // 11. QUẢN LÝ WATCHLIST (DANH SÁCH PHIM MUỐN XEM)
  // =========================================================================

  function toggleWatchlist(movieIdOrFlag) {
    if (typeof movieIdOrFlag === 'number' || (typeof movieIdOrFlag === 'string' && !isNaN(movieIdOrFlag))) {
      // Nhấp vào nút thêm/bớt phim cụ thể
      const mid = Number(movieIdOrFlag);
      const movie = getMovieById(mid);
      const title = movie ? (movie.vietnameseTitle || movie.cleanTitle || movie.title) : `Phim #${mid}`;
      const idx = MoodGraphState.watchlist.indexOf(mid);

      if (idx > -1) {
        MoodGraphState.watchlist.splice(idx, 1);
        saveStorageJson("moodgraph_watchlist", MoodGraphState.watchlist);
        showToast("Đã Xóa Khỏi Danh Sách Xem", `Đã loại bỏ "${title}" khỏi danh sách xem của bạn.`, 'remove');
      } else {
        MoodGraphState.watchlist.push(mid);
        saveStorageJson("moodgraph_watchlist", MoodGraphState.watchlist);
        showToast("Đã Thêm Vào Danh Sách Xem", `Đã lưu "${title}" vào danh sách theo dõi điện ảnh.`, 'info');
      }

      updateWatchlistUI();
      // Tái kết xuất lại giao diện để cập nhật biểu tượng tim/bookmark
      updateDynamicRecommendations();
    } else {
      // Nhấp vào nút mở/đóng drawer ở header hoặc click backdrop
      const drawer = document.getElementById('watchlist-drawer');
      const backdrop = document.getElementById('watchlist-backdrop');
      if (!drawer || !backdrop) return;

      const shouldOpen = (movieIdOrFlag === undefined || movieIdOrFlag === null) 
        ? !drawer.classList.contains('open') 
        : Boolean(movieIdOrFlag);

      if (shouldOpen) {
        drawer.classList.add('open');
        backdrop.classList.add('active');
        renderWatchlistDrawerItems();
      } else {
        drawer.classList.remove('open');
        backdrop.classList.remove('active');
      }
    }
  }

  function clearWatchlist() {
    if (MoodGraphState.watchlist.length === 0) return;
    MoodGraphState.watchlist = [];
    saveStorageJson("moodgraph_watchlist", MoodGraphState.watchlist);
    updateWatchlistUI();
    renderWatchlistDrawerItems();
    updateDynamicRecommendations();
    showToast("Đã Làm Trống Danh Sách Xem", "Đã dọn dẹp toàn bộ danh sách phim muốn xem.", 'remove');
  }

  function updateWatchlistUI() {
    const count = MoodGraphState.watchlist.length;
    
    // Đồng bộ tất cả badge trên header
    const badges = [
      document.getElementById('watchlist-count-badge'),
      document.getElementById('watchlist-badge')
    ];
    badges.forEach(b => {
      if (b) b.textContent = count;
    });

    renderWatchlistDrawerItems();
  }

  function renderWatchlistDrawerItems() {
    const container = document.getElementById('watchlist-items-list');
    if (!container) return;

    if (MoodGraphState.watchlist.length === 0) {
      container.innerHTML = `
        <div class="text-center py-16 space-y-3 text-[#94A3B8]">
          <svg class="w-10 h-10 mx-auto text-[#64748B]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
          </svg>
          <div class="text-sm font-semibold text-white">Chưa Có Phim Nào</div>
          <p class="text-xs max-w-xs mx-auto">Hãy nhấp vào biểu tượng bookmark trên các thẻ phim để lưu vào danh sách xem sau.</p>
        </div>
      `;
      return;
    }

    let html = '';
    MoodGraphState.watchlist.forEach(mid => {
      const movie = getMovieById(mid);
      if (!movie) return;

      const titleVn = escapeHtml(movie.vietnameseTitle || movie.cleanTitle || movie.title);
      const titleEn = escapeHtml(movie.cleanTitle || movie.title);

      html += `
        <div class="p-3 rounded-xl bg-[#141A24] border border-[rgba(255,255,255,0.06)] flex items-center justify-between gap-3 hover:border-[rgba(217,119,6,0.3)] transition-all">
          <div class="w-12 h-16 rounded overflow-hidden shrink-0 bg-[#0A0D14] cursor-pointer" 
               onclick="MoodGraphApp.openMovieDetailModal(${movie.movieId})">
            ${renderPosterImgHtml(movie, 'w-full h-full object-cover')}
          </div>

          <div class="flex-1 min-w-0 cursor-pointer" onclick="MoodGraphApp.openMovieDetailModal(${movie.movieId})">
            <h4 class="text-xs font-semibold text-white leading-tight truncate font-serif">${titleVn}</h4>
            <div class="text-[11px] text-[#94A3B8] italic truncate">${titleEn}</div>
            <div class="text-[10px] text-[#CBD5E1] font-mono mt-1">
              ${movie.year} • ★ ${movie.ratingAvg || 4.0} • ${movie.primaryGenre || 'Drama'}
            </div>
          </div>

          <button onclick="MoodGraphApp.toggleWatchlist(${movie.movieId})" 
                  class="p-1.5 rounded-lg text-[#64748B] hover:text-[#E11D48] hover:bg-[#1B2230] transition-colors"
                  title="Xóa khỏi danh sách xem">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      `;
    });

    container.innerHTML = html;
  }

  // =========================================================================
  // 12. TƯƠNG TÁC CHẤM ĐIỂM SAO (STAR RATINGS ENGINE)
  // Dynamic Closed-Loop Feedback: Phản hồi ngược thời gian thực khi đánh giá 4-5★ (Item 2)
  // =========================================================================

  function submitRating(movieId, score) {
    const mid = Number(movieId);
    const scoreNum = Number(score);
    MoodGraphState.userRatings[mid] = scoreNum;
    saveStorageJson("moodgraph_user_ratings", MoodGraphState.userRatings);

    const movie = getMovieById(mid);
    const title = movie ? (movie.vietnameseTitle || movie.cleanTitle || movie.title) : `Phim #${mid}`;
    const label = RATING_LABELS[scoreNum] || `${scoreNum} sao`;

    // Dynamic Closed-Loop Feedback: Khi người dùng chấm 4 - 5 sao
    if (scoreNum >= 4 && movie && movie.genres && Array.isArray(movie.genres) && movie.genres.length > 0) {
      // 1. Cập nhật ngay lập tức vector sở thích thể loại của người dùng hiện tại
      const user = MoodGraphState.currentUser || (window.MOCK_DATA && window.MOCK_DATA.currentUser);
      if (user) {
        if (!user.genreDistribution) user.genreDistribution = {};
        const bonusWeight = scoreNum === 5 ? 4 : 2;
        movie.genres.forEach(g => {
          user.genreDistribution[g] = (user.genreDistribution[g] || 0) + bonusWeight;
        });

        // Sắp xếp lại danh sách thể loại yêu thích topFavoriteGenres
        const sortedGenres = Object.entries(user.genreDistribution)
          .sort((a, b) => b[1] - a[1])
          .map(entry => entry[0]);
        user.topFavoriteGenres = sortedGenres.slice(0, 6);

        // Đưa phim vào đầu danh sách lịch sử xem gần nhất
        if (!Array.isArray(user.recentRatedMovies)) user.recentRatedMovies = [];
        const existingIdx = user.recentRatedMovies.findIndex(r => r.movieId === mid);
        if (existingIdx >= 0) user.recentRatedMovies.splice(existingIdx, 1);
        user.recentRatedMovies.unshift({
          movieId: mid,
          title: movie.vietnameseTitle || movie.cleanTitle || movie.title,
          genres: movie.genres,
          userRating: scoreNum,
          rating: scoreNum,
          timestamp: Math.floor(Date.now() / 1000)
        });
        user.ratingsCount = (user.ratingsCount || 0) + (existingIdx >= 0 ? 0 : 1);
      }

      // 2. Kích hoạt tăng cường thể loại trong State
      MoodGraphState.boostedGenres = movie.genres.slice();

      // 3. Tính toán lại danh sách phim gợi ý và cập nhật lại giao diện ngay trong tích tắc (< 5ms)
      updateDynamicRecommendations();

      // 4. Thông báo Toast giải thích phản hồi ngược khép kín
      showToast(
        "Đã ghi nhận đánh giá!",
        `Hệ thống vừa cập nhật gu phim và ưu tiên các tác phẩm cùng thể loại (${movie.genres.join(", ")}).`,
        'star'
      );
    } else {
      // Đánh giá bình thường dưới 4 sao
      showToast("Đã Ghi Nhận Đánh Giá", `"${title}": ${label}.`, 'star');
      updateDynamicRecommendations();
    }
  }

  // =========================================================================
  // 13. HỘP THOẠI CHI TIẾT BỘ PHIM (MOVIE DETAIL MODAL)
  // =========================================================================

  function openMovieDetailModal(movieId) {
    const modal = document.getElementById('movie-detail-modal');
    const content = document.getElementById('movie-detail-content');
    if (!modal || !content) return;

    const movie = getMovieById(movieId);
    if (!movie) return;

    const inWatchlist = MoodGraphState.watchlist.includes(movie.movieId);
    const userRating = MoodGraphState.userRatings[movie.movieId] || 0;
    const titleVn = escapeHtml(movie.vietnameseTitle || movie.cleanTitle || movie.title);
    const titleEn = escapeHtml(movie.cleanTitle || movie.title);
    const coords = movie.embedding3d || { x: 0, y: 0, z: 0, clusterName: "Chưa phân cụm" };

    // Liên kết ngoài IMDb & TMDb an toàn (Item 1)
    const imdbUrl = (movie.links && movie.links.imdbUrl) 
      ? movie.links.imdbUrl 
      : (movie.links && movie.links.imdbId ? `https://www.imdb.com/title/tt${movie.links.imdbId}/` : 'https://www.imdb.com');
    const tmdbUrl = (movie.links && movie.links.tmdbUrl) 
      ? movie.links.tmdbUrl 
      : (movie.links && movie.links.tmdbId ? `https://www.themoviedb.org/movie/${movie.links.tmdbId}` : 'https://www.themoviedb.org');

    // Tìm các phim tương tự
    let similarMoviesHtml = '';
    if (movie.similarMovieIds && movie.similarMovieIds.length > 0) {
      similarMoviesHtml = `
        <div class="pt-4 border-t border-[rgba(255,255,255,0.08)] space-y-2">
          <h4 class="text-xs font-semibold text-[#FBBF24] uppercase tracking-wider font-mono">Tác phẩm đồng điệu lân cận</h4>
          <div class="grid grid-cols-4 gap-2">
            ${movie.similarMovieIds.map(smId => {
              const sm = getMovieById(smId);
              if (!sm) return '';
              const smTitle = escapeHtml(sm.vietnameseTitle || sm.cleanTitle || sm.title);
              return `
                <div class="p-1.5 rounded-lg bg-[#0F141C] border border-[rgba(255,255,255,0.06)] hover:border-[#D97706] cursor-pointer transition-all text-center group"
                     onclick="MoodGraphApp.openMovieDetailModal(${sm.movieId})">
                  <div class="aspect-[2/3] rounded overflow-hidden mb-1">
                    ${renderPosterImgHtml(sm, 'w-full h-full object-cover group-hover:scale-105 transition-transform')}
                  </div>
                  <div class="text-[11px] font-semibold text-white truncate leading-tight">${smTitle}</div>
                  <div class="text-[10px] text-[#94A3B8] font-mono">${sm.year}</div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }

    content.innerHTML = `
      <div class="space-y-6">
        
        <!-- Header Modal & Nút Đóng -->
        <div class="flex items-start justify-between border-b border-[rgba(255,255,255,0.08)] pb-4">
          <div>
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-[rgba(217,119,6,0.15)] text-[#FDE68A] border border-[rgba(217,119,6,0.35)] font-mono">
                THÔNG TIN CHI TIẾT
              </span>
              <span class="text-xs font-mono text-[#94A3B8]">MovieID #${movie.movieId}</span>
            </div>
            <h2 class="text-2xl font-bold text-white font-serif mt-1">${titleVn}</h2>
            <div class="text-xs text-[#94A3B8] italic">${titleEn} • ${movie.year}</div>
          </div>

          <button onclick="MoodGraphApp.closeMovieDetailModal()" 
                  class="p-1.5 rounded-lg text-[#94A3B8] hover:text-white hover:bg-[#141A24] transition-colors">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <!-- Nội dung chính 2 cột -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          <!-- Cột Trái: Poster, Rating & Watchlist -->
          <div class="space-y-4">
            <div class="rounded-xl overflow-hidden shadow-2xl border border-[rgba(217,119,6,0.35)] aspect-[2/3] bg-[#0A0D14]">
              ${renderPosterImgHtml(movie, 'w-full h-full object-cover')}
            </div>

            <!-- Nút Watchlist -->
            <button onclick="MoodGraphApp.toggleWatchlist(${movie.movieId})" 
                    class="w-full btn-secondary text-xs py-2.5 ${inWatchlist ? 'border-[#10B981] text-[#10B981]' : ''}">
              <svg class="w-4 h-4 ${inWatchlist ? 'text-[#10B981]' : ''}" viewBox="0 0 24 24" fill="${inWatchlist ? '#10B981' : 'none'}" stroke="currentColor" stroke-width="2">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
              </svg>
              <span>${inWatchlist ? 'Đã Lưu Trong Danh Sách Xem ✓' : '+ Thêm Vào Danh Sách Xem'}</span>
            </button>

            <!-- Bộ Chấm Sao Cá Nhân -->
            <div class="p-3 rounded-lg bg-[#141A24] border border-[rgba(255,255,255,0.06)] space-y-1.5 text-center">
              <div class="text-[11px] text-[#94A3B8]">Đánh giá của bạn:</div>
              <div class="flex items-center justify-center gap-1">
                ${[1, 2, 3, 4, 5].map(starVal => {
                  const isFilled = userRating >= starVal;
                  return `
                    <button onclick="MoodGraphApp.submitRating(${movie.movieId}, ${starVal})" 
                            class="p-1 hover:scale-125 transition-transform" 
                            title="${starVal} sao — ${RATING_LABELS[starVal]}">
                      <svg class="w-5 h-5 ${isFilled ? 'text-[#F59E0B] fill-[#F59E0B]' : 'text-[#475569] fill-none'}" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                      </svg>
                    </button>
                  `;
                }).join('')}
              </div>
              <div class="text-[10px] text-[#FBBF24] font-mono mt-1">
                ${userRating > 0 ? RATING_LABELS[userRating] : 'Chưa chấm điểm'}
              </div>
            </div>

            <!-- Bộ Đôi Nút Liên Kết Ngoài IMDb & TMDb (Item 1) -->
            <div class="space-y-2 pt-2 border-t border-[rgba(255,255,255,0.06)]">
              <div class="text-[10px] font-mono text-[#94A3B8] uppercase tracking-wider text-center">Tra Cứu Dữ Liệu Quốc Tế</div>
              <div class="grid grid-cols-2 gap-2">
                <!-- Nút IMDb -->
                <a href="${imdbUrl}" 
                   target="_blank" 
                   rel="noopener noreferrer" 
                   class="flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg bg-[#141A24] hover:bg-[#1B2230] border border-[rgba(255,255,255,0.08)] hover:border-[#F59E0B] text-xs font-medium text-white transition-all group"
                   title="Mở hồ sơ phim trên IMDb trong tab mới">
                  <span class="px-1.5 py-0.5 rounded bg-[#F59E0B] text-[#0B0F14] font-mono font-extrabold text-[10px] tracking-tight">IMDb</span>
                  <span class="group-hover:text-[#FDE68A] transition-colors text-[11px]">Xem IMDb</span>
                  <svg class="w-3 h-3 text-[#64748B] group-hover:text-[#F59E0B] transition-colors shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                  </svg>
                </a>

                <!-- Nút TMDb -->
                <a href="${tmdbUrl}" 
                   target="_blank" 
                   rel="noopener noreferrer" 
                   class="flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg bg-[#141A24] hover:bg-[#1B2230] border border-[rgba(255,255,255,0.08)] hover:border-[#01B4E4] text-xs font-medium text-white transition-all group"
                   title="Mở hồ sơ phim trên The Movie Database trong tab mới">
                  <span class="px-1.5 py-0.5 rounded bg-[#01B4E4] text-white font-mono font-extrabold text-[10px] tracking-tight">TMDb</span>
                  <span class="group-hover:text-[#38BDF8] transition-colors text-[11px]">Xem TMDb</span>
                  <svg class="w-3 h-3 text-[#64748B] group-hover:text-[#01B4E4] transition-colors shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                  </svg>
                </a>
              </div>
            </div>
          </div>

          <!-- Cột Phải: Thông Tin Sâu & Tọa Độ Nhúng 3D -->
          <div class="md:col-span-2 space-y-4">
            
            <!-- Metadata Grid -->
            <div class="grid grid-cols-2 gap-3 text-xs">
              <div class="p-2.5 rounded-lg bg-[#141A24] border border-[rgba(255,255,255,0.06)]">
                <span class="text-[#64748B] block text-[10px]">Đạo diễn:</span>
                <span class="text-white font-semibold">${movie.director || 'Chưa cập nhật'}</span>
              </div>
              <div class="p-2.5 rounded-lg bg-[#141A24] border border-[rgba(255,255,255,0.06)]">
                <span class="text-[#64748B] block text-[10px]">Thời lượng:</span>
                <span class="text-white font-semibold">${movie.duration || '120 phút'}</span>
              </div>
              <div class="p-2.5 rounded-lg bg-[#141A24] border border-[rgba(255,255,255,0.06)]">
                <span class="text-[#64748B] block text-[10px]">Điểm chuẩn MovieLens:</span>
                <span class="text-[#F59E0B] font-bold font-mono">★ ${movie.ratingAvg || 4.2} / 5.0 (${(movie.ratingCount || 1000).toLocaleString('vi-VN')} votes)</span>
              </div>
              <div class="p-2.5 rounded-lg bg-[#141A24] border border-[rgba(255,255,255,0.06)]">
                <span class="text-[#64748B] block text-[10px]">Miền tâm trạng:</span>
                <span class="text-[#A7F3D0] font-semibold">${movie.moodLabel || 'Đặc sắc'}</span>
              </div>
            </div>

            <!-- Tóm Tắt Nội Dung -->
            <div class="space-y-1">
              <h4 class="text-xs font-semibold text-[#CBD5E1] uppercase tracking-wider font-mono">Cốt truyện tác phẩm</h4>
              <p class="text-xs text-[#CBD5E1] leading-relaxed">
                ${escapeHtml(movie.synopsis || 'Hành trình điện ảnh sâu sắc khám phá số phận và triết lý nhân sinh.')}
              </p>
            </div>

            <!-- Thông Số Không Gian Nhúng 3D (3D Latent Space) -->
            <div class="p-3.5 rounded-xl bg-[#0F141C] border border-[rgba(217,119,6,0.3)] space-y-2">
              <div class="flex items-center justify-between text-xs">
                <span class="text-[#FDE68A] font-bold font-mono uppercase tracking-wider">THÔNG SỐ KHÔNG GIAN NHÚNG 3D</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-[#1B2230] text-[#10B981]">Cluster 3D</span>
              </div>
              <div class="grid grid-cols-3 gap-2 font-mono text-[11px]">
                <div class="p-2 rounded bg-[#141A24]">
                  <span class="text-[#64748B] block text-[10px]">Tọa độ X:</span>
                  <span class="text-white">${coords.x}</span>
                </div>
                <div class="p-2 rounded bg-[#141A24]">
                  <span class="text-[#64748B] block text-[10px]">Tọa độ Y:</span>
                  <span class="text-white">${coords.y}</span>
                </div>
                <div class="p-2 rounded bg-[#141A24]">
                  <span class="text-[#64748B] block text-[10px]">Tọa độ Z:</span>
                  <span class="text-white">${coords.z}</span>
                </div>
              </div>
              <div class="text-xs text-[#94A3B8]">
                Cụm không gian: <strong class="text-white">${coords.clusterName || 'Cụm Điện Ảnh Tổng Hợp'}</strong>
              </div>
            </div>

            <!-- Bằng Chứng Gợi Ý Provenance Tags -->
            <div class="space-y-2">
              <h4 class="text-xs font-semibold text-[#CBD5E1] uppercase tracking-wider font-mono">Minh chứng gợi ý (Provenance)</h4>
              <div class="p-3 rounded-lg bg-[#141A24] border border-[rgba(255,255,255,0.06)] text-xs text-[#CBD5E1] leading-relaxed">
                ${escapeHtml(movie.provenanceSummary || 'Hội tụ cao giữa mô hình Phân rã ma trận ALS và mạng tri thức điện ảnh.')}
              </div>
            </div>

            ${similarMoviesHtml}

          </div>

        </div>

      </div>
    `;

    modal.classList.add('active');
  }

  function closeMovieDetailModal(event) {
    if (event && event.target && event.target !== event.currentTarget) return;
    const modal = document.getElementById('movie-detail-modal');
    if (modal) modal.classList.remove('active');
  }

  // =========================================================================
  // 14. HỘP THOẠI HỒ SƠ NGƯỜI DÙNG & BỘ CHUYỂN ĐỔI PERSONA (Item 4)
  // =========================================================================

  function switchPersona(personaId) {
    if (!window.MOCK_DATA || !window.MOCK_DATA.presetPersonas) return;
    const persona = window.MOCK_DATA.presetPersonas[personaId];
    if (!persona) return;

    MoodGraphState.activePersonaId = personaId;
    MoodGraphState.currentUser = JSON.parse(JSON.stringify(persona));
    MoodGraphState.isColdStart = (personaId === 'user_cold');
    MoodGraphState.boostedGenres = [];

    // Cập nhật cấu hình slider theo Persona
    if (persona.defaultSliders) {
      MoodGraphState.sliders = Object.assign({}, persona.defaultSliders);
    }

    // Cập nhật tập đánh giá theo Persona
    MoodGraphState.userRatings = Object.assign({}, persona.initialRatings || {});
    saveStorageJson("moodgraph_user_ratings", MoodGraphState.userRatings);

    // Đồng bộ Slider và Chú giải
    syncSliderInputs();

    // Đồng bộ giá trị trên Header Selector
    const headerSel = document.getElementById('header-persona-selector');
    if (headerSel) headerSel.value = personaId;

    const avatarSpan = document.getElementById('header-user-avatar');
    if (avatarSpan) avatarSpan.textContent = persona.avatarLetter || persona.name.charAt(0);

    // Đồng bộ trạng thái 3 nút trên thanh Persona Bar Trang 1
    const personaMap = {
      user1: 'btn-persona-user1',
      user2: 'btn-persona-user2',
      user_cold: 'btn-persona-user-cold'
    };
    Object.keys(personaMap).forEach(pid => {
      const btn = document.getElementById(personaMap[pid]);
      if (btn) {
        if (pid === personaId) {
          btn.className = "persona-btn active px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-2.5 bg-[#D97706] text-white border border-[#F59E0B] transition-all shadow-md";
          const numSpan = btn.querySelector('span');
          if (numSpan) numSpan.className = "w-6 h-6 rounded-full bg-black/30 flex items-center justify-center text-[11px] font-bold";
        } else {
          const borderColor = pid === 'user_cold' ? 'hover:border-[#10B981]' : 'hover:border-[#F59E0B]';
          const iconColor = pid === 'user_cold' ? 'text-[#10B981]' : 'text-[#F59E0B]';
          btn.className = `persona-btn px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-2.5 bg-[#0B0F14] text-[#94A3B8] hover:text-white border border-[rgba(255,255,255,0.08)] ${borderColor} transition-all`;
          const numSpan = btn.querySelector('span');
          if (numSpan) numSpan.className = `w-6 h-6 rounded-full bg-[#1B2230] flex items-center justify-center text-[11px] font-bold ${iconColor}`;
        }
      }
    });

    // Tái tính toán và kết xuất đề xuất
    updateDynamicRecommendations();

    showToast(
      "Đã Chuyển Hồ Sơ Khán Giả",
      `Đang trải nghiệm theo góc nhìn của ${persona.name} (${persona.roleDescription}).`,
      'info'
    );
  }

  function openUserProfileModal() {
    const modal = document.getElementById('user-profile-modal');
    const content = document.getElementById('user-profile-content');
    if (!modal || !content || !window.MOCK_DATA) return;

    const u = MoodGraphState.currentUser 
      || (window.MOCK_DATA.presetPersonas && window.MOCK_DATA.presetPersonas[MoodGraphState.activePersonaId]) 
      || window.MOCK_DATA.currentUser 
      || {
        userId: 1,
        name: "Alex Turner",
        ratingsCount: 68,
        meanRating: 3.78,
        bio: "Khán giả đam mê dòng phim tác giả."
      };

    const isCold = Boolean(MoodGraphState.isColdStart || u.userId === 0);

    let genreBarsHtml = '';
    const gd = u.genreDistribution || u.genresDistribution || {};
    const topGenres = Object.entries(gd).slice(0, 5);
    const maxVal = topGenres.length > 0 ? topGenres[0][1] : 50;

    if (topGenres.length === 0) {
      genreBarsHtml = `
        <div class="p-3 text-center text-[#94A3B8] italic text-xs rounded bg-[#0B0F14] border border-[rgba(255,255,255,0.04)]">
          Chưa có dữ liệu thể loại. Hệ thống kích hoạt thuật toán Khởi Động Nguội (Cold-Start) dựa trên Knowledge Graph và Độ phổ biến toàn cục.
        </div>
      `;
    } else {
      topGenres.forEach(([gen, cnt]) => {
        const pct = Math.round((cnt / maxVal) * 100);
        genreBarsHtml += `
          <div class="space-y-1 text-xs">
            <div class="flex justify-between text-[#CBD5E1]">
              <span>${gen}</span>
              <span class="font-mono text-[#F59E0B]">${cnt} phim</span>
            </div>
            <div class="w-full h-1.5 rounded-full bg-[#1B2230] overflow-hidden">
              <div class="h-full rounded-full bg-[#D97706]" style="width: ${pct}%;"></div>
            </div>
          </div>
        `;
      });
    }

    let recentRatingsHtml = '';
    const recent = u.recentRatedMovies || u.recentRatings || [];
    if (recent.length === 0) {
      recentRatingsHtml = `
        <div class="p-3 text-center text-[#94A3B8] italic text-xs rounded bg-[#0B0F14] border border-[rgba(255,255,255,0.04)]">
          0 tương tác lịch sử. Người dùng mới tinh chưa chấm điểm bộ phim nào.
        </div>
      `;
    } else {
      recent.slice(0, 6).forEach(r => {
        recentRatingsHtml += `
          <div class="p-2.5 rounded-lg bg-[#0F141C] border border-[rgba(255,255,255,0.06)] flex items-center justify-between text-xs">
            <span class="text-white font-medium truncate">${escapeHtml(r.title)}</span>
            <span class="font-mono text-[#F59E0B] shrink-0 ml-2">★ ${(r.userRating || r.rating || 5.0).toFixed(1)}</span>
          </div>
        `;
      });
    }

    const avatarBg = isCold ? 'border-[#10B981] text-[#10B981]' : 'border-[#D97706] text-[#F59E0B]';
    const roleBadge = isCold 
      ? '<span class="text-[10px] font-mono px-2 py-0.5 rounded bg-[rgba(16,185,129,0.15)] text-[#A7F3D0] border border-[rgba(16,185,129,0.35)]">KHÁN GIẢ MỚI • COLD-START</span>'
      : `<span class="text-[10px] font-mono px-2 py-0.5 rounded bg-[rgba(217,119,6,0.15)] text-[#FDE68A] border border-[rgba(217,119,6,0.35)]">${escapeHtml(u.roleDescription || 'KHÁN GIẢ KIỂM CHUẨN')}</span>`;

    content.innerHTML = `
      <div class="space-y-5">
        
        <!-- Header Profile -->
        <div class="flex items-center justify-between border-b border-[rgba(255,255,255,0.08)] pb-4">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-full bg-[#1B2230] border-2 ${avatarBg} flex items-center justify-center text-lg font-bold">
              ${u.avatarLetter || u.name.charAt(0)}
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-lg font-bold text-white font-serif">${escapeHtml(u.name)}</h3>
                ${roleBadge}
              </div>
              <p class="text-xs text-[#94A3B8] mt-0.5">${escapeHtml(u.bio)}</p>
            </div>
          </div>

          <button onclick="MoodGraphApp.closeUserProfileModal()" 
                  class="p-1.5 rounded-lg text-[#94A3B8] hover:text-white hover:bg-[#141A24] transition-colors">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <!-- 3 Chỉ Số Tổng Quan -->
        <div class="grid grid-cols-3 gap-3 font-mono text-center text-xs">
          <div class="p-3 rounded-xl bg-[#141A24] border border-[rgba(255,255,255,0.06)]">
            <span class="text-[#64748B] block text-[10px]">Số lượt đánh giá:</span>
            <span class="text-lg font-bold text-white">${u.ratingsCount || 0}</span>
          </div>
          <div class="p-3 rounded-xl bg-[#141A24] border border-[rgba(255,255,255,0.06)]">
            <span class="text-[#64748B] block text-[10px]">Điểm trung bình:</span>
            <span class="text-lg font-bold text-[#F59E0B]">${(u.meanRating || 0).toFixed(2)}★</span>
          </div>
          <div class="p-3 rounded-xl bg-[#141A24] border border-[rgba(255,255,255,0.06)]">
            <span class="text-[#64748B] block text-[10px]">Mức hoạt động:</span>
            <span class="text-lg font-bold ${isCold ? 'text-[#38BDF8]' : 'text-[#10B981]'}">${u.activityLevel || 'Trung bình'}</span>
          </div>
        </div>

        <!-- Phân Phối Thể Loại & Phim Đã Xem -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="p-3.5 rounded-xl bg-[#141A24] border border-[rgba(255,255,255,0.06)] space-y-3">
            <h4 class="text-xs font-semibold text-[#FBBF24] uppercase tracking-wider font-mono">Phân phối thể loại ưa thích</h4>
            <div class="space-y-2 pt-1">
              ${genreBarsHtml}
            </div>
          </div>

          <div class="p-3.5 rounded-xl bg-[#141A24] border border-[rgba(255,255,255,0.06)] space-y-3">
            <h4 class="text-xs font-semibold text-[#FBBF24] uppercase tracking-wider font-mono">Tác phẩm đánh giá gần nhất</h4>
            <div class="space-y-1.5 max-h-48 overflow-y-auto">
              ${recentRatingsHtml}
            </div>
          </div>
        </div>

        <!-- Held-Out Split Target Note hoặc Cold-Start Note -->
        <div class="p-3 rounded-lg bg-[#0F141C] border border-[rgba(217,119,6,0.3)] text-xs text-[#CBD5E1] space-y-1">
          <div class="font-bold text-[#F59E0B] font-mono">Cơ chế bảo vệ thuật toán:</div>
          <div class="flex items-center gap-2 text-[11px] font-mono">
            ${isCold 
              ? '<span class="px-2 py-0.5 rounded bg-[rgba(16,185,129,0.2)] text-[#A7F3D0]">Cold-Start Protocol: KG Ontology 1-Hop + Global Popularity Anchor</span>' 
              : '<span class="px-2 py-0.5 rounded bg-[#1B2230] text-[#BAE6FD]">Validation: Pulp Fiction (#296 - 5.0★)</span><span class="px-2 py-0.5 rounded bg-[#1B2230] text-[#A7F3D0]">Test: Eternal Sunshine (#7361 - 5.0★)</span>'}
          </div>
        </div>

      </div>
    `;

    modal.classList.add('active');
  }

  function closeUserProfileModal(event) {
    if (event && event.target && event.target !== event.currentTarget) return;
    const modal = document.getElementById('user-profile-modal');
    if (modal) modal.classList.remove('active');
  }

  // =========================================================================
  // 15. HỘP THOẠI PHÂN TÍCH GIAO THOA MA TRẬN 2 MÔ HÌNH (MATRIX OVERLAP MODAL)
  // =========================================================================

  function openMatrixOverlapModal(modelA, modelB) {
    const modal = document.getElementById('matrix-overlap-modal') || document.getElementById('heatmap-cell-modal');
    const content = document.getElementById('matrix-overlap-content') || document.getElementById('heatmap-cell-modal-body');
    if (!modal || !content || !window.MOCK_DATA) return;

    const overlaps = window.MOCK_DATA.pairwiseOverlaps || [];
    const top10ByModel = window.MOCK_DATA.top10ByModel || {};

    const isSelf = modelA === modelB;
    const pair = overlaps.find(p => 
      (p.modelA === modelA && p.modelB === modelB) || 
      (p.modelA === modelB && p.modelB === modelA)
    );

    let commonMovieIds = [];
    if (isSelf) {
      commonMovieIds = (top10ByModel[modelA] || []).map(m => m.movieId);
    } else if (pair && pair.commonMovieIds) {
      commonMovieIds = pair.commonMovieIds;
    }

    let moviesHtml = '';
    if (commonMovieIds.length > 0) {
      commonMovieIds.forEach(mid => {
        const movie = getMovieById(mid);
        const title = movie ? (movie.vietnameseTitle || movie.cleanTitle || movie.title) : `Phim #${mid}`;

        const itemA = (top10ByModel[modelA] || []).find(m => m.movieId === mid);
        const itemB = (top10ByModel[modelB] || []).find(m => m.movieId === mid);

        const rankA = itemA ? itemA.rank : '-';
        const rankB = itemB ? itemB.rank : '-';

        moviesHtml += `
          <div class="p-2.5 rounded-lg bg-[#0F141C] border border-[rgba(255,255,255,0.06)] flex items-center justify-between text-xs">
            <span class="text-white font-medium truncate">${title}</span>
            <div class="flex items-center gap-2 font-mono text-[11px] shrink-0 ml-2">
              <span class="px-1.5 py-0.5 rounded bg-[#1B2230] text-[#FDE68A]">${modelA.toUpperCase()} #${rankA}</span>
              ${!isSelf ? `<span class="text-[#64748B]">↔</span><span class="px-1.5 py-0.5 rounded bg-[#1B2230] text-[#A7F3D0]">${modelB.toUpperCase()} #${rankB}</span>` : ''}
            </div>
          </div>
        `;
      });
    } else {
      moviesHtml = `
        <div class="p-4 rounded-lg bg-[#0F141C] text-xs text-[#94A3B8] italic text-center">
          Hai mô hình này hoàn toàn trực giao (k = 0), không có tác phẩm nào trùng lặp trong Top-10.
        </div>
      `;
    }

    content.innerHTML = `
      <div class="space-y-4">
        <div class="flex items-center justify-between border-b border-[rgba(255,255,255,0.08)] pb-3">
          <div>
            <div class="text-[10px] font-mono uppercase tracking-wider text-[#F59E0B]">ĐỐI SOÁT GIAO THOA 2 MÔ HÌNH</div>
            <h3 class="text-base font-bold text-white mt-0.5 font-serif">
              ${modelA.toUpperCase()} ${!isSelf ? '↔ ' + modelB.toUpperCase() : '(Tự tương quan)'}
            </h3>
            <p class="text-xs text-[#94A3B8] mt-0.5">
              Số tác phẩm đồng thuận: <strong class="text-white font-mono">${commonMovieIds.length} / 10 phim</strong>
            </p>
          </div>

          <button onclick="MoodGraphApp.closeMatrixOverlapModal()" class="text-[#94A3B8] hover:text-white p-1">✕</button>
        </div>

        <div class="space-y-2">
          <div class="text-xs font-semibold text-[#CBD5E1]">Danh sách tác phẩm trùng lặp & thứ hạng:</div>
          <div class="space-y-1.5 max-h-60 overflow-y-auto">
            ${moviesHtml}
          </div>
        </div>
      </div>
    `;

    modal.classList.add('active');
  }

  function closeMatrixOverlapModal(event) {
    if (event && event.target && event.target !== event.currentTarget) return;
    const modal = document.getElementById('matrix-overlap-modal') || document.getElementById('heatmap-cell-modal');
    if (modal) modal.classList.remove('active');
  }

  // =========================================================================
  // 16. HỖ TRỢ PHÒNG THÍ NGHIỆM HỌC THUẬT MODE B (ACADEMIC LAB FALLBACK)
  // Đảm bảo không bao giờ lỗi runtime khi người dùng chuyển sang Tab B
  // =========================================================================

  function setInterlock(movieId) {
    MoodGraphState.activeInterlockMovieId = Number(movieId);
    const mid = MoodGraphState.activeInterlockMovieId;

    const cards = document.querySelectorAll('[data-interlock-movie-id]');
    const matchedModels = [];

    cards.forEach(card => {
      const cardMid = Number(card.getAttribute('data-interlock-movie-id'));
      if (cardMid === mid) {
        card.classList.add('interlock-highlighted');
        const modelId = card.getAttribute('data-model-id') || '';
        const rankEl = card.querySelector('.movie-rank-badge');
        const rank = rankEl ? rankEl.textContent.trim() : '';
        matchedModels.push(`${modelId.toUpperCase()} (#${rank})`);
      } else {
        card.classList.remove('interlock-highlighted');
      }
    });

    const banner = document.getElementById('interlock-status-banner');
    const textEl = document.getElementById('interlock-status-text');
    const movie = getMovieById(mid);
    const title = movie ? (movie.vietnameseTitle || movie.cleanTitle || movie.title) : `Phim #${mid}`;

    if (banner && textEl) {
      textEl.textContent = `Đồng thuận ${matchedModels.length} mô hình cho "${title}": ${matchedModels.join(' | ')}`;
      banner.classList.remove('hidden');
    }
  }

  function clearInterlock() {
    MoodGraphState.activeInterlockMovieId = null;
    document.querySelectorAll('[data-interlock-movie-id]').forEach(card => {
      card.classList.remove('interlock-highlighted');
    });
    const banner = document.getElementById('interlock-status-banner');
    if (banner) banner.classList.add('hidden');
  }

  function changeLabUser(userKey) {
    MoodGraphState.selectedLabUser = userKey;
    renderHeadToHeadComparison();
    showToast("Đã Chuyển Tập Người Dùng", `Đã nạp đoàn hệ kiểm chuẩn: ${userKey.toUpperCase()}.`, 'info');
  }

  function setConsensusFilter(filterType) {
    MoodGraphState.consensusFilter = filterType;

    const btnAll = document.getElementById('filter-consensus-all');
    const btnOverlap = document.getElementById('filter-consensus-overlap');
    const btnUnique = document.getElementById('filter-consensus-unique');

    [btnAll, btnOverlap, btnUnique].forEach(btn => {
      if (btn) btn.className = 'px-2.5 py-1 rounded font-medium text-[#94A3B8] hover:text-white';
    });

    if (filterType === 'all' && btnAll) btnAll.className = 'px-2.5 py-1 rounded font-semibold bg-[#D97706] text-white';
    if (filterType === 'overlap' && btnOverlap) btnOverlap.className = 'px-2.5 py-1 rounded font-semibold bg-[#D97706] text-white';
    if (filterType === 'unique' && btnUnique) btnUnique.className = 'px-2.5 py-1 rounded font-semibold bg-[#D97706] text-white';

    renderHeadToHeadComparison();
  }

  function toggleHeatmapMetric(metricType) {
    MoodGraphState.heatmapMetric = metricType;

    const btnSpearman = document.getElementById('btn-metric-spearman');
    const btnJaccard = document.getElementById('btn-metric-jaccard');

    if (metricType === 'spearman') {
      if (btnSpearman) btnSpearman.className = 'px-3 py-1.5 rounded font-semibold bg-[#D97706] text-white transition-all';
      if (btnJaccard) btnJaccard.className = 'px-3 py-1.5 rounded font-medium text-[#94A3B8] hover:text-white transition-all';
    } else {
      if (btnSpearman) btnSpearman.className = 'px-3 py-1.5 rounded font-medium text-[#94A3B8] hover:text-white transition-all';
      if (btnJaccard) btnJaccard.className = 'px-3 py-1.5 rounded font-semibold bg-[#D97706] text-white transition-all';
    }

    renderCorrelationHeatmap();
  }

  function reset3DCamera() {
    if (window.Academic3D && typeof window.Academic3D.resetCamera === 'function') {
      window.Academic3D.resetCamera();
    }
  }

  function toggle3DRays() {
    if (window.Academic3D && typeof window.Academic3D.toggleRays === 'function') {
      window.Academic3D.toggleRays();
    }
  }

  function toggle3DRotation() {
    if (window.Academic3D && typeof window.Academic3D.toggleRotation === 'function') {
      window.Academic3D.toggleRotation();
    }
  }

  function renderHeadToHeadComparison() {
    const container = document.getElementById('head-to-head-columns');
    if (!container || !window.MOCK_DATA || !window.MOCK_DATA.top10ByModel) return;

    const top10 = window.MOCK_DATA.top10ByModel;
    const models = [
      { id: 'als', name: 'Spark ALS', color: '#0284C7' },
      { id: 'kg', name: 'Knowledge Graph', color: '#059669' },
      { id: 'hybrid_rrf', name: 'Hybrid RRF (k=60)', color: '#D97706' },
      { id: 'hybrid_weighted', name: 'Hybrid Weighted', color: '#EA580C' },
      { id: 'popularity', name: 'Popularity Baseline', color: '#78716C' }
    ];

    let html = '';
    models.forEach(m => {
      const list = top10[m.id] || [];
      html += `
        <div class="head-to-head-column">
          <div class="model-column-header" style="border-top: 3px solid ${m.color};">
            <span class="text-xs font-bold text-white font-serif">${m.name}</span>
            <span class="text-[10px] text-[#94A3B8] font-mono">10 đề xuất hàng đầu</span>
          </div>
          <div class="divide-y divide-[rgba(255,255,255,0.04)]">
            ${list.map(item => {
              const movie = getMovieById(item.movieId);
              const title = movie ? (movie.vietnameseTitle || movie.cleanTitle || movie.title) : `Phim #${item.movieId}`;
              return `
                <div class="model-item-row" 
                     data-interlock-movie-id="${item.movieId}" 
                     data-model-id="${m.id}"
                     onmouseenter="MoodGraphApp.setInterlock(${item.movieId})"
                     onmouseleave="MoodGraphApp.clearInterlock()"
                     onclick="MoodGraphApp.openMovieDetailModal(${item.movieId})">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="movie-rank-badge w-5 h-5 rounded-full bg-[#1B2230] text-[10px] font-mono flex items-center justify-center text-white shrink-0">
                      ${item.rank}
                    </span>
                    <span class="truncate text-xs text-[#E2E8F0]">${title}</span>
                  </div>
                  <span class="text-[10px] font-mono text-[#94A3B8] ml-1 shrink-0">
                    ${item.score ? item.score.toFixed(3) : ''}
                  </span>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
  }

  function renderCorrelationHeatmap() {
    const container = document.getElementById('heatmap-matrix-container');
    const legend = document.getElementById('heatmap-color-legend');
    if (!container || !window.MOCK_DATA || !window.MOCK_DATA.correlationMatrix) return;

    const matrix = window.MOCK_DATA.correlationMatrix;
    const models = matrix.models || ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'];
    const modelLabels = {
      als: 'Spark ALS',
      kg: 'Knowledge Graph',
      hybrid_rrf: 'Hybrid RRF',
      hybrid_weighted: 'Weighted',
      popularity: 'Popularity'
    };

    if (legend) {
      if (MoodGraphState.heatmapMetric === 'spearman') {
        legend.innerHTML = `
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-[#10B981]"></span> Đồng điệu (+0.6..1.0)</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-[#D97706]"></span> Vừa (+0.2..0.6)</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-[#78716C]"></span> Trực giao (-0.2..0.2)</span>
        `;
      } else {
        legend.innerHTML = `
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-[#10B981]"></span> Trùng cao (> 0.5)</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-[#D97706]"></span> Trùng vừa (0.2..0.5)</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full bg-[#78716C]"></span> Trùng thấp (&lt; 0.2)</span>
        `;
      }
    }

    let gridHtml = '<div class="heatmap-table-grid">';

    // Cột tiêu đề góc
    gridHtml += '<div class="heatmap-cell text-[10px] font-mono text-[#64748B]">MÔ HÌNH</div>';
    models.forEach(m => {
      gridHtml += `<div class="heatmap-cell text-[10px] font-bold text-[#CBD5E1] font-mono text-center">${modelLabels[m]}</div>`;
    });

    models.forEach((rowModel, r) => {
      gridHtml += `<div class="heatmap-cell text-[10px] font-bold text-[#CBD5E1] font-mono text-left px-2 justify-start items-start">${modelLabels[rowModel]}</div>`;

      models.forEach((colModel, c) => {
        const isDiagonal = r === c;
        const commonK = (matrix.commonCounts && matrix.commonCounts[r] && matrix.commonCounts[r][c] !== undefined)
          ? matrix.commonCounts[r][c]
          : (isDiagonal ? 10 : 0);

        if (isDiagonal) {
          gridHtml += `
            <div class="heatmap-cell bg-[rgba(217,119,6,0.15)] border border-[rgba(217,119,6,0.35)]" 
                 onclick="MoodGraphApp.openMatrixOverlapModal('${rowModel}', '${colModel}')">
              <span class="text-xs font-mono font-bold text-[#FDE68A] tabular-nums">1.0000</span>
              <span class="text-[9px] text-[#94A3B8] font-mono">10/10 phim</span>
            </div>
          `;
          return;
        }

        if (MoodGraphState.heatmapMetric === 'spearman') {
          const rho = matrix.spearman && matrix.spearman[r] ? matrix.spearman[r][c] : null;
          
          if (rho === null || commonK < 2) {
            gridHtml += `
              <div class="heatmap-cell null-cell" onclick="MoodGraphApp.openMatrixOverlapModal('${rowModel}', '${colModel}')">
                <span class="text-[9px] font-mono text-[#64748B]">${commonK} phim</span>
              </div>
            `;
          } else {
            const valText = (rho >= 0 ? '+' : '') + Number(rho).toFixed(4);
            const colorBg = rho >= 0.6 ? 'bg-[rgba(16,185,129,0.2)] text-[#A7F3D0]' : 'bg-[rgba(217,119,6,0.12)] text-[#FDE68A]';
            gridHtml += `
              <div class="heatmap-cell ${colorBg}" onclick="MoodGraphApp.openMatrixOverlapModal('${rowModel}', '${colModel}')">
                <span class="text-xs font-mono font-bold tabular-nums">${valText}</span>
                <span class="text-[9px] font-mono opacity-80">${commonK} phim</span>
              </div>
            `;
          }
        } else {
          const jaccard = matrix.jaccard && matrix.jaccard[r] ? matrix.jaccard[r][c] : 0;
          const pct = Math.round(jaccard * 100);
          const colorBg = jaccard >= 0.5 ? 'bg-[rgba(16,185,129,0.2)] text-[#A7F3D0]' : 'bg-[rgba(217,119,6,0.12)] text-[#FDE68A]';

          gridHtml += `
            <div class="heatmap-cell ${colorBg}" onclick="MoodGraphApp.openMatrixOverlapModal('${rowModel}', '${colModel}')">
              <span class="text-xs font-mono font-bold tabular-nums">${Number(jaccard).toFixed(3)}</span>
              <span class="text-[9px] font-mono opacity-80">${pct}% trùng</span>
            </div>
          `;
        }

      });
    });

    gridHtml += '</div>';
    container.innerHTML = gridHtml;
  }

  function renderOfflineBenchmarks() {
    const tbody = document.getElementById('offline-benchmarks-tbody');
    if (!tbody || !window.MOCK_DATA || !window.MOCK_DATA.offlineBenchmarks) return;

    const b = window.MOCK_DATA.offlineBenchmarks;
    let html = '';
    b.metrics.forEach(row => {
      html += `
        <tr class="hover:bg-[#141A24] transition-colors">
          <td class="py-2.5 px-3 font-semibold text-white">${row.metric} — ${row.name}</td>
          <td class="py-2.5 px-3 text-[#BAE6FD] tabular-nums">${row.als}</td>
          <td class="py-2.5 px-3 text-[#A7F3D0] tabular-nums">${row.kg}</td>
          <td class="py-2.5 px-3 text-[#FDE68A] font-bold tabular-nums">${row.rrf}</td>
          <td class="py-2.5 px-3 text-[#FED7AA] tabular-nums">${row.weighted}</td>
          <td class="py-2.5 px-3 text-[#D6D3D1] tabular-nums">${row.pop}</td>
          <td class="py-2.5 px-3 text-right">
            <span class="px-2 py-0.5 rounded bg-[rgba(16,185,129,0.15)] text-[#A7F3D0] border border-[rgba(16,185,129,0.35)] font-bold">
              ${row.best}
            </span>
          </td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
  }

  function renderColdStartDiagnostics() {
    const container = document.getElementById('cold-start-chart-container');
    if (!container || !window.MOCK_DATA || !window.MOCK_DATA.coldStartData) return;

    const points = window.MOCK_DATA.coldStartData.sparsityDegradation || [];
    let html = '';
    points.forEach(p => {
      html += `
        <div class="flex items-center gap-3 text-xs">
          <span class="w-20 text-[#94A3B8] shrink-0 font-mono">${p.ratingsCount} ratings</span>
          <div class="flex-1 flex items-center gap-2">
            <div class="w-1/2 h-2 rounded-full bg-[#1B2230] overflow-hidden" title="KG: ${p.kgNdcg}">
              <div class="h-full bg-[#059669] rounded-full" style="width: ${p.kgNdcg * 100}%;"></div>
            </div>
            <div class="w-1/2 h-2 rounded-full bg-[#1B2230] overflow-hidden" title="ALS: ${p.alsNdcg}">
              <div class="h-full bg-[#0284C7] rounded-full" style="width: ${p.alsNdcg * 100}%;"></div>
            </div>
          </div>
          <span class="w-20 text-right text-[#A7F3D0] font-mono shrink-0">${p.kgNdcg} KG</span>
        </div>
      `;
    });

    container.innerHTML = html;
  }

  function renderLongTailDiagnostics() {
    const container = document.getElementById('long-tail-chart-container');
    if (!container || !window.MOCK_DATA || !window.MOCK_DATA.longTailData) return;

    const list = window.MOCK_DATA.longTailData.coverageMetrics || [];
    let html = '';
    list.forEach(m => {
      const pct = Math.min(100, Math.round((m.coverageAt10 / 414) * 100));
      html += `
        <div class="space-y-1 text-xs">
          <div class="flex items-center justify-between">
            <span class="text-[#E2E8F0] font-medium">${m.modelName}</span>
            <span class="text-white font-bold font-mono">${m.coverageAt10} phim (@10)</span>
          </div>
          <div class="w-full h-2 rounded-full bg-[#1B2230] overflow-hidden">
            <div class="h-full rounded-full bg-[#D97706]" style="width: ${pct}%;"></div>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
  }

  // =========================================================================
  // 17. LẮNG NGHE SỰ KIỆN TOÀN CỤC & PHÍM TẮT (EVENT LISTENERS & SHORTCUTS)
  // =========================================================================

  function setupGlobalListeners() {
    // Kết nối ô tìm kiếm tức thì
    const searchInputs = [
      document.getElementById('global-search-input'),
      document.getElementById('movie-search-input')
    ];

    searchInputs.forEach(input => {
      if (input) {
        let timer = null;
        input.addEventListener('input', (e) => {
          clearTimeout(timer);
          timer = setTimeout(() => {
            MoodGraphState.searchQuery = e.target.value;
            updateDynamicRecommendations();
          }, 120);
        });
      }
    });

    // Phím tắt bàn phím
    window.addEventListener('keydown', (e) => {
      // Phím '/' để tìm kiếm nhanh
      if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
        e.preventDefault();
        const primarySearch = document.getElementById('global-search-input') || document.getElementById('movie-search-input');
        if (primarySearch) {
          primarySearch.focus();
          primarySearch.select();
        }
      }
      // Phím 'Escape' để đóng tất cả modal & drawer
      if (e.key === 'Escape') {
        closeMovieDetailModal();
        closeUserProfileModal();
        closeMatrixOverlapModal();
        toggleWatchlist(false);
      }
    });
  }

  // =========================================================================
  // 18. KHỞI TẠO ỨNG DỤNG (APPLICATION BOOTSTRAPPER)
  // =========================================================================

  function init() {
    console.log("🎬 Khởi tạo MoodGraph Standalone Interactive Prototype (Page 1 Discovery)...");

    if (!window.MOCK_DATA) {
      console.error("Lỗi: Không tìm thấy window.MOCK_DATA từ mock_data.js!");
      return;
    }

    // 0. Khởi tạo Persona ban đầu (User 1 - Alex Turner)
    if (!MoodGraphState.currentUser) {
      if (window.MOCK_DATA.presetPersonas && window.MOCK_DATA.presetPersonas.user1) {
        MoodGraphState.currentUser = JSON.parse(JSON.stringify(window.MOCK_DATA.presetPersonas.user1));
      } else {
        MoodGraphState.currentUser = window.MOCK_DATA.currentUser;
      }
    }

    // 1. Render các chip tâm trạng
    renderMoodChips();

    // 2. Đồng bộ các thanh trượt & chú giải ngữ nghĩa động
    syncSliderInputs();
    updateAllSliderSemanticHints();

    // 3. Render bộ lọc thể loại
    renderGenreFilters();

    // 4. Tính toán và kết xuất Hero Banner, Gợi Ý và Catalog
    updateDynamicRecommendations();

    // 5. Cập nhật Watchlist Badge
    updateWatchlistUI();

    // 6. Kết nối các trình lắng nghe sự kiện
    setupGlobalListeners();

    console.log("✓ MoodGraph Page 1 Discovery đã sẵn sàng hoạt động độc lập 100%!");
  }

  // Tự động chạy khi DOM sẵn sàng
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // =========================================================================
  // 19. CÔNG KHAI PUBLIC API CHO GIAO DIỆN & BỘ KIỂM THỬ (PUBLIC API)
  // =========================================================================

  window.MoodGraphApp = {
    // Mode Switcher
    switchMode,

    // Persona Quick Switcher (Item 4)
    switchPersona,

    // Sliders & Moods & Semantic Hints (Item 3)
    onSliderChange,
    resetSliders,
    selectMood,
    updateSliderSemanticHints: updateAllSliderSemanticHints,

    // Genre Filters
    selectGenreFilter,
    resetFilters,

    // Movie Detail Modal
    openMovieDetailModal,
    closeMovieDetailModal,

    // User Profile Modal
    openUserProfileModal,
    closeUserProfileModal,

    // Matrix Overlap Modal
    openMatrixOverlapModal,
    closeMatrixOverlapModal,
    openHeatmapCellModal: openMatrixOverlapModal,
    closeHeatmapCellModal: closeMatrixOverlapModal,

    // Watchlist Management
    toggleWatchlist,
    clearWatchlist,
    clearAllWatchlist: clearWatchlist,

    // Ratings System (Item 2 Closed-Loop)
    submitRating,

    // Mode B Academic Lab Hooks
    setInterlock,
    clearInterlock,
    changeLabUser,
    setConsensusFilter,
    toggleHeatmapMetric,
    reset3DCamera,
    toggle3DRays,
    toggle3DRotation,

    // Toast Engine
    showToast
  };

})(window, document);
