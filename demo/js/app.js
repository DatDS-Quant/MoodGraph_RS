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

    // Lưu trữ ratings của phiên tương tác trực tiếp Live Session tách biệt
    liveSessionRatings: loadStorageJson("moodgraph_live_user_ratings", {}),
    hasUserRatedInLiveSession: false,

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

  // Đảm bảo đầy đủ 5 Persona trong presetPersonas: user1, user2, user3, user42/user_cold, live_session
  function ensurePresetPersonas() {
    if (!window.MOCK_DATA) return;
    if (!window.MOCK_DATA.presetPersonas) {
      window.MOCK_DATA.presetPersonas = {};
    }
    const pp = window.MOCK_DATA.presetPersonas;

    // Bổ sung Khán giả 3 (Marcus Vance - Phim Đen Tội Phạm Cổ Điển)
    if (!pp.user3) {
      pp.user3 = {
        id: "user3",
        userId: 3,
        name: "Marcus Vance",
        displayName: "Marcus Vance (Crime & Film-Noir)",
        roleDescription: "Phim Đen & Tội Phạm Cổ Điển",
        avatarLetter: "M",
        avatarUrl: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop&q=80",
        bio: "Khán giả đam mê dòng phim tội phạm kinh điển, Neo-Noir, các cuộc điều tra tâm lý gai góc và những kiệt tác gangster thế kỷ 20.",
        ratingsCount: 89,
        meanRating: 4.10,
        activityLevel: "high",
        isInAlsTrain: true,
        defaultSliders: { depth: 0.85, pacing: 0.45, auteur: 0.80, tone: 0.30 },
        initialRatings: { 858: 5.0, 50: 5.0, 296: 4.5, 1213: 5.0, 111: 4.5, 6016: 5.0 },
        genreDistribution: {
          "Crime": 48, "Drama": 42, "Film-Noir": 30, "Mystery": 25, "Thriller": 22
        },
        topFavoriteGenres: ["Crime", "Drama", "Film-Noir", "Mystery", "Thriller"],
        recentRatedMovies: [
          { movieId: 858, title: "The Godfather (1972)", genres: ["Crime", "Drama"], userRating: 5.0, rating: 5.0, timestamp: 1250000000 },
          { movieId: 50, title: "The Usual Suspects (1995)", genres: ["Crime", "Mystery", "Thriller"], userRating: 5.0, rating: 5.0, timestamp: 1250100000 },
          { movieId: 1213, title: "Goodfellas (1990)", genres: ["Biography", "Crime", "Drama"], userRating: 5.0, rating: 5.0, timestamp: 1250200000 }
        ]
      };
    }

    // Bổ sung bí danh user42 cho Khán giả Mới
    if (!pp.user42 && pp.user_cold) {
      pp.user42 = Object.assign({}, pp.user_cold, { id: "user42", userId: 42 });
    }

    // Bổ sung Tài Khoản Trực Tiếp (Live Session)
    if (!pp.live_session) {
      const liveCount = Object.keys(MoodGraphState.liveSessionRatings || {}).length;
      pp.live_session = {
        id: "live_session",
        userId: 9999,
        name: "Tài Khoản Trực Tiếp",
        displayName: "Tài Khoản Trực Tiếp (Live Session)",
        roleDescription: `Phiên Tương Tác Trực Tiếp • ${liveCount} đánh giá`,
        avatarLetter: "L",
        avatarUrl: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=200&auto=format&fit=crop&q=80",
        bio: "Phiên làm việc trực tiếp của người dùng. Hệ thống tự động thu thập và suy luận gợi ý theo thời gian thực khép kín.",
        ratingsCount: liveCount,
        meanRating: 0.0,
        activityLevel: "live",
        isInAlsTrain: false,
        defaultSliders: { depth: 0.75, pacing: 0.60, auteur: 0.85, tone: 0.50 },
        initialRatings: {},
        genreDistribution: {},
        topFavoriteGenres: [],
        recentRatedMovies: []
      };
    }
  }
  ensurePresetPersonas();

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

      // Đồng bộ giá trị hiển thị trên Header Selector
      const headerSel = document.getElementById('header-persona-selector');
      if (headerSel && MoodGraphState.activePersonaId) {
        headerSel.value = (MoodGraphState.activePersonaId === 'user42') ? 'user_cold' : MoodGraphState.activePersonaId;
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
        // Tự động đồng bộ Persona từ Trang 1 sang Trang 2 chuẩn xác
        let targetLabUser = 'user1';
        if (MoodGraphState.activePersonaId === 'user2') {
          targetLabUser = 'user2';
        } else if (MoodGraphState.activePersonaId === 'user3') {
          targetLabUser = 'user3';
        } else if (MoodGraphState.activePersonaId === 'live_session') {
          targetLabUser = 'live_session';
        } else if (MoodGraphState.activePersonaId === 'user_cold' || MoodGraphState.activePersonaId === 'user42') {
          // Chỉ chuyển sang live_session khi người dùng thực sự có đánh giá trực tiếp trong phiên
          const liveRatingsCount = Object.keys(MoodGraphState.liveSessionRatings || {}).length;
          const userRatingsCount = Object.keys(MoodGraphState.userRatings || {}).length;
          if (MoodGraphState.hasUserRatedInLiveSession || liveRatingsCount > 0 || userRatingsCount > 0) {
            targetLabUser = 'live_session';
          } else {
            targetLabUser = 'user42';
          }
        } else {
          targetLabUser = MoodGraphState.activePersonaId || 'user1';
        }

        if (typeof window.MoodGraphApp.changeLabUser === 'function') {
          window.MoodGraphApp.changeLabUser(targetLabUser, true);
        } else if (typeof changeLabUser === 'function') {
          changeLabUser(targetLabUser, true);
        }
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

    // Nhãn rút gọn cho giao diện Sidebar gọn gàng
    const shortNames = {
      'mind_bending': 'Trí tuệ',
      'suspense': 'Hồi hộp',
      'reflective': 'Sâu lắng',
      'epic_adventure': 'Phiêu lưu',
      'uplifting': 'Thư giãn',
      'romantic': 'Lãng mạn',
      'dark_noir': 'U tối'
    };

    let html = `
      <button onclick="MoodGraphApp.selectMood('all')" 
              data-mood="all"
              class="mood-chip-btn ${currentMood === 'all' ? 'active' : ''}">
        <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <polygon points="12 8 8 12 12 16 16 12 12 8"></polygon>
        </svg>
        <span>Tất cả</span>
      </button>
    `;

    moods.forEach(m => {
      const isActive = currentMood === m.id;
      const label = shortNames[m.id] || m.name;
      html += `
        <button onclick="MoodGraphApp.selectMood('${m.id}')" 
                data-mood="${m.id}"
                class="mood-chip-btn ${isActive ? 'active' : ''}"
                title="${escapeHtml(m.description || m.name)}">
          <span>${escapeHtml(label)}</span>
        </button>
      `;
    });

    container.innerHTML = html;

    // Cập nhật nhãn văn bản hiển thị tâm trạng hiện tại nếu có
    const displayEl = document.getElementById('active-mood-display');
    if (displayEl) {
      if (currentMood === 'all') {
        displayEl.textContent = "Tất cả";
      } else {
        const found = moods.find(x => x.id === currentMood);
        displayEl.textContent = found ? (shortNames[found.id] || found.name) : currentMood;
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
      const valEl = document.getElementById(`val-slider-${axis}`) || document.getElementById(`val-${axis}`);
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
    const valEl = document.getElementById(`val-slider-${axis}`) || document.getElementById(`val-${axis}`);
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
    const backdropImg = topMovie.backdropUrl || topMovie.posterUrl;

    container.innerHTML = `
      <div class="relative overflow-hidden rounded-2xl border border-white/10 bg-[#070A0F] shadow-2xl min-h-[420px] group">
        
        <!-- Backdrop 16:9 Tràn Viền Toàn Bộ Nền -->
        <div class="absolute inset-0 z-0 overflow-hidden">
          <img src="${backdropImg}" 
               alt="${titleVn}" 
               class="w-full h-full object-cover object-center filter brightness-[0.7] contrast-[1.05] transition-transform duration-1000 ease-out group-hover:scale-105"
               onerror="this.onerror=null; this.src='${topMovie.posterUrl}';">
        </div>

        <!-- Scrim Gradient Phủ Từ Trái Sang -->
        <div class="absolute inset-0 z-[1] bg-gradient-to-r from-[#070A0F] via-[#070A0F]/90 via-45% to-transparent pointer-events-none"></div>

        <!-- Scrim Gradient Phủ Từ Dưới Lên -->
        <div class="absolute inset-0 z-[2] bg-gradient-to-t from-[#070A0F] via-[#070A0F]/75 via-35% to-transparent pointer-events-none"></div>

        <!-- Nội Dung Hero Banner Tối Giản -->
        <div class="relative z-10 p-8 sm:p-12 lg:p-16 flex flex-col justify-end min-h-[420px] max-w-2xl space-y-3.5 text-left">
          
          <!-- Badges Gọn Gàng -->
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 rounded text-[11px] font-mono font-bold uppercase tracking-wider bg-amber-500/15 text-amber-300 border border-amber-500/30 tabular-nums shrink-0 whitespace-nowrap inline-flex items-center justify-center">
              TOP ĐỀ XUẤT • ${matchPct}% MATCH
            </span>
            <span class="text-xs text-[#94A3B8] font-mono shrink-0 whitespace-nowrap">${topMovie.primaryGenre || 'Drama'}</span>
          </div>

          <!-- Tiêu Đề Lớn -->
          <h1 class="text-3xl sm:text-4xl lg:text-5xl font-black text-white tracking-tight leading-tight font-serif drop-shadow-md">
            ${titleVn}
          </h1>

          <!-- Năm / Thời Lượng / Đạo Diễn / Rating -->
          <div class="flex flex-wrap items-center gap-2 text-xs sm:text-sm text-[#94A3B8] font-mono tabular-nums">
            <span class="shrink-0 whitespace-nowrap">${topMovie.year}</span>
            <span class="text-white/30 shrink-0">•</span>
            <span class="shrink-0 whitespace-nowrap">${topMovie.duration || '142 phút'}</span>
            <span class="text-white/30 shrink-0">•</span>
            <span class="shrink-0 whitespace-nowrap">Đạo diễn: <strong class="text-white not-italic font-sans">${topMovie.director || 'Frank Darabont'}</strong></span>
            <span class="text-white/30 shrink-0">•</span>
            <span class="text-[#F59E0B] font-bold shrink-0 whitespace-nowrap inline-flex items-center gap-1">★ ${topMovie.ratingAvg || 4.4}</span>
          </div>

          <!-- 2 Dòng Tóm Tắt Ngắn -->
          <p class="text-xs sm:text-sm text-[#CBD5E1] line-clamp-2 leading-relaxed max-w-xl font-sans">
            ${escapeHtml(topMovie.synopsis || 'Tác phẩm điện ảnh sâu sắc với giá trị nghệ thuật và triết lý nhân sinh vượt thời gian.')}
          </p>

          <!-- 2 Nút Bấm Gọn Gàng -->
          <div class="flex items-center gap-3 pt-2">
            <button onclick="MoodGraphApp.openMovieDetailModal(${topMovie.movieId})" 
                    class="px-5 py-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-black font-semibold text-xs sm:text-sm tracking-wide shadow-lg shadow-amber-500/20 active:scale-95 transition-all inline-flex items-center justify-center gap-2 shrink-0 whitespace-nowrap">
              <svg class="w-4 h-4 fill-black shrink-0" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              <span class="whitespace-nowrap">Xem Chi Tiết</span>
            </button>

            <button onclick="MoodGraphApp.toggleWatchlist(${topMovie.movieId})" 
                    id="hero-watchlist-btn"
                    data-movie-id="${topMovie.movieId}"
                    class="px-4 py-2.5 rounded-lg border backdrop-blur-md text-xs sm:text-sm font-medium active:scale-95 transition-all inline-flex items-center justify-center gap-2 shrink-0 whitespace-nowrap ${inWatchlist ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/15' : 'bg-white/10 hover:bg-white/15 border-white/10 text-white'}">
              <svg class="w-4 h-4 shrink-0 ${inWatchlist ? 'text-emerald-400 fill-emerald-400' : 'text-white fill-none'}" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
              </svg>
              <span class="whitespace-nowrap">${inWatchlist ? 'Đã Lưu Watchlist ✓' : '+ Thêm Vào Watchlist'}</span>
            </button>
          </div>

        </div>

      </div>
    `;
  }

  // =========================================================================
  // 9. KẾT XUẤT DANH SÁCH GỢI Ý XẾP HẠNG (SIDE RANKING RECOMMENDATION PANEL)
  // =========================================================================

  function renderRecommendationsGrid(movies) {
    const container = document.getElementById('recommendations-grid');
    if (!container) return;

    if (!movies || movies.length === 0) {
      container.innerHTML = `
        <div class="py-10 text-center text-[#94A3B8] text-xs font-mono">
          Không có tác phẩm đề xuất phù hợp trong bộ lọc hiện tại.
        </div>
      `;
      return;
    }

    // Đảm bảo sắp xếp nghiêm ngặt theo Match Score từ cao xuống thấp
    const sortedMovies = [...movies].sort((a, b) => {
      const scoreA = Number(a.compatibilityPct != null ? a.compatibilityPct : (a.matchScore != null ? a.matchScore * 100 : 90));
      const scoreB = Number(b.compatibilityPct != null ? b.compatibilityPct : (b.matchScore != null ? b.matchScore * 100 : 90));
      return scoreB - scoreA;
    });

    let html = '';
    sortedMovies.forEach((movie, index) => {
      const rankNum = index + 1;
      const inWatchlist = MoodGraphState.watchlist.includes(movie.movieId);
      const titleVn = escapeHtml(movie.vietnameseTitle || movie.cleanTitle || movie.title);
      const titleEn = escapeHtml(movie.cleanTitle || movie.title);
      const matchPct = Number(movie.compatibilityPct != null ? movie.compatibilityPct : 92).toFixed(1);
      const matchNum = parseFloat(matchPct);
      const imdbScore = movie.ratingAvg ? Number(movie.ratingAvg).toFixed(1) : '4.0';

      // Kiểu huy hiệu thứ hạng: Top 1-3 nổi bật với Amber/Gold mạ sang trọng
      let rankBadgeClass = 'bg-white/5 text-slate-400 border-white/10';
      if (rankNum === 1) {
        rankBadgeClass = 'bg-gradient-to-br from-amber-400/25 to-amber-600/30 text-amber-300 border-amber-400/50 font-bold shadow-md shadow-amber-500/10 scale-105';
      } else if (rankNum === 2) {
        rankBadgeClass = 'bg-gradient-to-br from-amber-300/20 to-amber-500/25 text-amber-200 border-amber-400/40 font-bold shadow-sm';
      } else if (rankNum === 3) {
        rankBadgeClass = 'bg-gradient-to-br from-amber-500/15 to-amber-700/20 text-amber-300/90 border-amber-500/35 font-semibold';
      }

      // Xác định Provenance Chip ngắn gọn
      let provChipText = 'P1 Thể Loại';
      let provChipClass = 'bg-purple-500/15 text-purple-300 border-purple-500/30';
      
      const recObj = (window.MOCK_DATA && window.MOCK_DATA.recommendationsModeA)
        ? window.MOCK_DATA.recommendationsModeA.find(r => r.movieId === movie.movieId)
        : null;

      if (recObj && recObj.provenanceTags && recObj.provenanceTags.length > 0) {
        const firstTag = recObj.provenanceTags[0];
        if (firstTag.type === 'P1_GENRE') {
          provChipText = 'P1 Thể Loại';
          provChipClass = 'bg-purple-500/15 text-purple-300 border-purple-500/30';
        } else if (firstTag.type === 'P2_GENOME') {
          provChipText = 'P2 Tâm Trạng';
          provChipClass = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
        } else if (firstTag.type === 'P3_COLLABORATIVE') {
          provChipText = 'P3 Đồng Gu';
          provChipClass = 'bg-sky-500/15 text-sky-300 border-sky-500/30';
        } else if (firstTag.type === 'LATENT_AFFINITY') {
          provChipText = 'ALS Vector';
          provChipClass = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
        }
      } else {
        const fallbackTypes = [
          { text: 'P1 Thể Loại', cls: 'bg-purple-500/15 text-purple-300 border-purple-500/30' },
          { text: 'P2 Tâm Trạng', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
          { text: 'P3 Đồng Gu', cls: 'bg-sky-500/15 text-sky-300 border-sky-500/30' },
          { text: 'ALS Vector', cls: 'bg-rose-500/15 text-rose-300 border-rose-500/30' }
        ];
        const pick = fallbackTypes[movie.movieId % fallbackTypes.length];
        provChipText = pick.text;
        provChipClass = pick.cls;
      }

      html += `
        <div class="group relative flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 hover:border-white/15 transition-all duration-200 cursor-pointer"
             onclick="MoodGraphApp.openMovieDetailModal(${movie.movieId})">
          
          <!-- Badge Thứ Hạng #1, #2, #3... (Kích thước lớn hơn, nổi bật hơn) -->
          <div class="w-7 h-7 rounded-lg border flex items-center justify-center text-xs font-mono shrink-0 whitespace-nowrap ${rankBadgeClass}">
            #${rankNum}
          </div>

          <!-- Poster Nhỏ Chuẩn 2:3 Sắc Nét -->
          <div class="relative w-14 aspect-[2/3] rounded-md overflow-hidden bg-[#070A0F] border border-white/10 shrink-0 shadow-md">
            ${renderPosterImgHtml(movie, 'w-full h-full object-cover group-hover:scale-105 transition-transform duration-200')}
          </div>

          <!-- Khối Thông Tin Chi Tiết Rộng Rãi -->
          <div class="flex-1 min-w-0 space-y-1.5">
            <div class="flex items-start justify-between gap-2">
              <h3 class="text-xs sm:text-sm font-semibold text-white leading-tight truncate group-hover:text-amber-400 transition-colors" title="${titleVn}">
                ${titleVn}
              </h3>
              
              <!-- Nút Bookmark Nhanh -->
              <button onclick="event.stopPropagation(); MoodGraphApp.toggleWatchlist(${movie.movieId})" 
                      class="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-colors shrink-0 whitespace-nowrap inline-flex items-center justify-center focus:outline-none"
                      title="${inWatchlist ? 'Xóa khỏi Danh Sách Xem' : 'Lưu vào Danh Sách Xem'}">
                <svg class="w-3.5 h-3.5 shrink-0 ${inWatchlist ? 'text-emerald-400 fill-emerald-400' : 'text-slate-400 fill-none'}" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                </svg>
              </button>
            </div>

            <!-- Meta: Năm • Thể loại • IMDb (Dàn đều 1 hàng ngang thoáng đãng) -->
            <div class="flex items-center gap-2 text-[11px] text-slate-400 font-mono tabular-nums shrink-0 whitespace-nowrap">
              <span>${movie.year}</span>
              <span class="text-white/20">•</span>
              <span class="truncate max-w-[110px] text-slate-300">${movie.primaryGenre || 'Drama'}</span>
              <span class="text-white/20">•</span>
              <span class="text-amber-400 font-bold inline-flex items-center gap-0.5">★ ${imdbScore}</span>
            </div>

            <!-- Match Score % + Mini Progress Bar + Provenance Chip Trên 1 Hàng Ngang Thoáng -->
            <div class="flex items-center justify-between gap-2.5 pt-0.5">
              <div class="flex items-center gap-2 min-w-0 flex-1">
                <span class="text-[11px] font-mono font-bold text-emerald-400 tabular-nums shrink-0 whitespace-nowrap">
                  ${matchPct}%
                </span>
                <div class="w-full max-w-[80px] h-1.5 bg-white/10 rounded-full overflow-hidden shrink-0">
                  <div class="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full" style="width: ${Math.min(100, matchNum)}%"></div>
                </div>
              </div>

              <!-- Provenance Chip Gọn Gàng -->
              <span class="px-2 py-0.5 rounded text-[10px] font-mono border whitespace-nowrap shrink-0 inline-flex items-center justify-center ${provChipClass}">
                ${provChipText}
              </span>
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
                class="px-3.5 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all border ${
                  isActive 
                    ? 'bg-white/15 text-white border-white/30 font-semibold shadow-sm backdrop-blur-md' 
                    : 'bg-[#141A24] text-[#94A3B8] border-white/10 hover:text-white hover:border-white/25'
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
      badge.innerHTML = `Hiển thị <span class="text-white font-bold">${filtered.length} / ${allMovies.length}</span> phim mẫu (ml-25m)`;
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

      html += `
        <div class="movie-card group" onclick="MoodGraphApp.openMovieDetailModal(${movie.movieId})">
          <div class="movie-poster-box">
            ${renderPosterImgHtml(movie)}
            
            <!-- Overlay tối nhẹ khi hover -->
            <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none"></div>

            <!-- Badge Thể Loại -->
            <div class="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-[rgba(11,15,20,0.85)] backdrop-blur-md border border-[rgba(255,255,255,0.1)] text-[10px] font-mono text-white/80 shrink-0 whitespace-nowrap inline-flex items-center justify-center">
              ${movie.primaryGenre || 'Film'}
            </div>

            <!-- Nút Bookmark nhanh -->
            <button onclick="event.stopPropagation(); MoodGraphApp.toggleWatchlist(${movie.movieId})" 
                    class="absolute top-2 right-2 p-1.5 rounded-lg bg-[rgba(11,15,20,0.85)] hover:bg-[#1B2230] border border-[rgba(255,255,255,0.1)] text-white transition-all focus:outline-none shrink-0 inline-flex items-center justify-center"
                    title="${inWatchlist ? 'Xóa khỏi Danh Sách Xem' : 'Lưu vào Danh Sách Xem'}">
              <svg class="w-3.5 h-3.5 shrink-0 ${inWatchlist ? 'text-[#10B981] fill-[#10B981]' : 'text-white/80 fill-none'}" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
              </svg>
            </button>
          </div>

          <!-- Bên dưới ảnh: Tên phim, Năm • Thể loại chính • Điểm IMDb -->
          <div class="pt-2 px-0.5 space-y-0.5 min-w-0">
            <h3 class="text-sm font-semibold text-white leading-tight truncate block w-full group-hover:text-[#FBBF24] transition-colors" title="${titleVn}">
              ${titleVn}
            </h3>
            <div class="flex items-center gap-1.5 text-[11px] text-[#94A3B8] font-mono tabular-nums shrink-0 whitespace-nowrap">
              <span class="shrink-0 whitespace-nowrap">${movie.year}</span>
              <span class="text-white/20 shrink-0">•</span>
              <span class="truncate max-w-[85px]">${movie.primaryGenre || 'Drama'}</span>
              <span class="text-white/20 shrink-0">•</span>
              <span class="text-[#F59E0B] font-bold shrink-0 whitespace-nowrap inline-flex items-center gap-0.5">★ ${movie.ratingAvg ? Number(movie.ratingAvg).toFixed(1) : '4.0'}</span>
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

      // Đồng bộ trực tiếp nút trong Modal nếu đang hiển thị phim này
      const modalWatchlistBtn = document.getElementById('modal-watchlist-btn');
      if (modalWatchlistBtn && modalWatchlistBtn.getAttribute('data-movie-id') == mid) {
        const isNowInWatchlist = MoodGraphState.watchlist.includes(mid);
        modalWatchlistBtn.className = `w-full px-4 py-2.5 rounded-lg border transition-all duration-150 inline-flex items-center justify-center gap-2 shrink-0 whitespace-nowrap ${isNowInWatchlist ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/15' : 'bg-white/5 border-white/10 hover:border-white/20 text-white hover:bg-white/10'}`;
        modalWatchlistBtn.innerHTML = `
          <svg class="w-4 h-4 shrink-0 ${isNowInWatchlist ? 'text-emerald-400 fill-emerald-400' : 'text-white'}" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
          </svg>
          <span class="whitespace-nowrap font-semibold text-xs">${isNowInWatchlist ? 'Đã Lưu Watchlist ✓' : '+ Thêm Vào Watchlist'}</span>
        `;
      }

      // Đồng bộ nút trên Hero Banner nếu đang hiển thị phim này
      const heroWatchlistBtn = document.getElementById('hero-watchlist-btn');
      if (heroWatchlistBtn && heroWatchlistBtn.getAttribute('data-movie-id') == mid) {
        const isNowInWatchlist = MoodGraphState.watchlist.includes(mid);
        heroWatchlistBtn.className = `px-4 py-2.5 rounded-lg border backdrop-blur-md text-xs sm:text-sm font-medium active:scale-95 transition-all inline-flex items-center justify-center gap-2 shrink-0 whitespace-nowrap ${isNowInWatchlist ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/15' : 'bg-white/10 hover:bg-white/15 border-white/10 text-white'}`;
        heroWatchlistBtn.innerHTML = `
          <svg class="w-4 h-4 shrink-0 ${isNowInWatchlist ? 'text-emerald-400 fill-emerald-400' : 'text-white fill-none'}" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
          </svg>
          <span class="whitespace-nowrap">${isNowInWatchlist ? 'Đã Lưu Watchlist ✓' : '+ Thêm Vào Watchlist'}</span>
        `;
      }

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

    // 1. Cập nhật vào userRatings hiện hành
    MoodGraphState.userRatings[mid] = scoreNum;
    saveStorageJson("moodgraph_user_ratings", MoodGraphState.userRatings);

    // 2. Bảo toàn độc lập vào liveSessionRatings của Live Session
    if (!MoodGraphState.liveSessionRatings) {
      MoodGraphState.liveSessionRatings = {};
    }
    MoodGraphState.liveSessionRatings[mid] = scoreNum;
    MoodGraphState.hasUserRatedInLiveSession = true;
    saveStorageJson("moodgraph_live_user_ratings", MoodGraphState.liveSessionRatings);

    // Nếu đang ở Persona Khán giả Mới, người dùng đã có tương tác nên không còn là cold-start
    if (MoodGraphState.activePersonaId === 'user_cold' || MoodGraphState.activePersonaId === 'user42') {
      MoodGraphState.isColdStart = false;
    }

    // 3. Đồng bộ nhãn dropdown Live Session trên Mode B và phụ đề nút Persona
    try {
      const optLive = document.getElementById('opt-lab-live');
      const liveCount = Object.keys(MoodGraphState.liveSessionRatings).length;
      if (optLive) {
        optLive.textContent = `🎬 Tài khoản của bạn (Live Session • ${liveCount} đánh giá)`;
      }
      const liveSub = document.getElementById('btn-live-session-subtitle');
      if (liveSub) {
        liveSub.textContent = `${liveCount} đánh giá`;
      }

      // Cập nhật persona live_session trong presetPersonas nếu có
      if (window.MOCK_DATA && window.MOCK_DATA.presetPersonas && window.MOCK_DATA.presetPersonas.live_session) {
        window.MOCK_DATA.presetPersonas.live_session.ratingsCount = liveCount;
        window.MOCK_DATA.presetPersonas.live_session.roleDescription = `Phiên Tương Tác Trực Tiếp • ${liveCount} đánh giá`;
      }

      // Nếu AcademicLab đang mở ở chế độ live_session, tự động cập nhật lại bảng đối đầu
      if (window.AcademicLab && typeof window.AcademicLab.onUserRatingsChanged === 'function') {
        window.AcademicLab.onUserRatingsChanged();
      }
    } catch (e) {
      console.warn("Lỗi đồng bộ Live Session sang Trang 2:", e);
    }

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
  // 13. HỘP THOẠI CHI TIẾT BỘ PHIM (MOVIE DETAIL MODAL) & PROVENANCE EXPLORER
  // =========================================================================

  let isProvenanceAccordionOpen = false;
  let activeProvenanceData = null;

  function toggleProvenanceAccordion(forceState) {
    if (typeof forceState === 'boolean') {
      isProvenanceAccordionOpen = forceState;
    } else {
      isProvenanceAccordionOpen = !isProvenanceAccordionOpen;
    }

    const bodyEl = document.getElementById('prov-accordion-body');
    const chevronEl = document.getElementById('prov-accordion-chevron');
    const triggerBtn = document.getElementById('prov-accordion-trigger');

    if (bodyEl) {
      if (isProvenanceAccordionOpen) {
        bodyEl.classList.remove('max-h-0', 'opacity-0', 'pointer-events-none');
        bodyEl.classList.add('max-h-[600px]', 'opacity-100', 'pointer-events-auto', 'mt-3');
      } else {
        bodyEl.classList.add('max-h-0', 'opacity-0', 'pointer-events-none');
        bodyEl.classList.remove('max-h-[600px]', 'opacity-100', 'pointer-events-auto', 'mt-3');
      }
    }

    if (chevronEl) {
      if (isProvenanceAccordionOpen) {
        chevronEl.classList.add('rotate-180');
      } else {
        chevronEl.classList.remove('rotate-180');
      }
    }

    if (triggerBtn) {
      triggerBtn.setAttribute('aria-expanded', isProvenanceAccordionOpen ? 'true' : 'false');
    }
  }

  function buildMovieProvenance(movie) {
    const genresStr = (movie.genres || []).join(' • ') || (movie.primaryGenre || 'Chính Kịch');
    const titleClean = movie.cleanTitle || movie.title;
    const moodName = movie.moodLabel || ((window.MOCK_DATA && window.MOCK_DATA.moods) ? (window.MOCK_DATA.moods.find(m => m.id === movie.primaryMood)?.name || 'Chiều Sâu / Triết Lý') : 'Chiều Sâu / Triết Lý');
    const dotProduct = (3.8 + ((movie.movieId * 7) % 15) / 10).toFixed(3);
    const peerId = 1000 + (movie.movieId * 17) % 899;
    const matchPct = movie.compatibilityPct || 94;

    // Kiểm tra xem phim có dữ liệu provenanceTags sẵn trong RECOMMENDATIONS_MODE_A không
    const recObj = (window.MOCK_DATA && window.MOCK_DATA.recommendationsModeA) 
      ? window.MOCK_DATA.recommendationsModeA.find(r => r.movieId === movie.movieId) 
      : null;

    let p1Text = `Duyệt đồ thị tri thức trực tiếp nối từ các tác phẩm bạn từng chấm 5.0★ sang thể loại <strong>${genresStr}</strong> của phim này.`;
    let p2Text = `Thuộc tính cảm xúc và sắc thái điện ảnh tương đồng cao với miền tâm trạng <strong>${moodName}</strong> trong không gian Genome.`;
    let p3Text = `Khán giả <strong>#${peerId}</strong> và các cụm người dùng có hành vi chấm điểm giống bạn trên MovieLens 25M đều đồng thuận đánh giá cao tác phẩm này.`;
    let p4Text = `Tích vô hướng giữa vector người dùng và vector phim trong không gian nhân tử tiềm ẩn ALS 32 chiều đạt <strong>${dotProduct}</strong> (Top 2% toàn danh mục).`;

    if (recObj && recObj.provenanceTags) {
      const tagP1 = recObj.provenanceTags.find(t => t.type === 'P1_GENRE');
      if (tagP1 && tagP1.text) p1Text = escapeHtml(tagP1.text);

      const tagP2 = recObj.provenanceTags.find(t => t.type === 'P2_GENOME');
      if (tagP2 && tagP2.text) p2Text = escapeHtml(tagP2.text);

      const tagP3 = recObj.provenanceTags.find(t => t.type === 'P3_COLLABORATIVE');
      if (tagP3 && tagP3.text) p3Text = escapeHtml(tagP3.text);

      const tagP4 = recObj.provenanceTags.find(t => t.type === 'LATENT_AFFINITY');
      if (tagP4 && tagP4.text) p4Text = escapeHtml(tagP4.text);
    } else if (movie.provenanceSummary) {
      p1Text = `${escapeHtml(movie.provenanceSummary)} Đường đi đồ thị khớp trực tiếp qua thuộc tính ${genresStr}.`;
    }

    return {
      p1: {
        title: "Đồ Thị Thể Loại (P1)",
        badge: "GRAPH TRAVERSAL",
        badgeColor: "bg-amber-500/10 text-amber-300 border-amber-500/20",
        pathNodes: ["Hồ Sơ Của Bạn (5.0★)", genresStr, titleClean],
        metricLabel: "Độ tin cậy RRF",
        metricValue: `${matchPct}%`,
        description: p1Text
      },
      p2: {
        title: "Tâm Trạng & Genome (P2)",
        badge: "TAG GENOME 1128-D",
        badgeColor: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
        pathNodes: ["Vector Cảm Xúc", moodName, "Khớp Genome: 89.2%"],
        metricLabel: "Độ khớp Genome",
        metricValue: "0.892",
        description: p2Text
      },
      p3: {
        title: "Cộng Đồng Đồng Gu (P3)",
        badge: "COLLABORATIVE FILTERING",
        badgeColor: "bg-sky-500/10 text-sky-300 border-sky-500/20",
        pathNodes: ["Khán Giả Tương Đồng", `User #${peerId}`, "Đồng Thuận 5.0★"],
        metricLabel: "Hệ số tương quan",
        metricValue: "r = 0.88",
        description: p3Text
      },
      p4: {
        title: "Nhân Tử Tiềm Ẩn ALS (P4)",
        badge: "MATRIX FACTORIZATION",
        badgeColor: "bg-rose-500/10 text-rose-300 border-rose-500/20",
        pathNodes: ["Vector Nhúng 32-D", `Dot Product = ${dotProduct}`, "Top 2% Toàn Kho"],
        metricLabel: "Tích vô hướng nhúng",
        metricValue: dotProduct,
        description: p4Text
      }
    };
  }

  function renderProvenanceTabBody(tabKey) {
    if (!activeProvenanceData || !activeProvenanceData[tabKey]) return '';
    const data = activeProvenanceData[tabKey];

    const nodesHtml = data.pathNodes.map((n, i) => {
      const isLast = i === data.pathNodes.length - 1;
      return `
        <span class="inline-flex items-center gap-1.5 shrink-0 whitespace-nowrap ${isLast ? 'text-white font-semibold' : 'text-slate-300'}">
          <span class="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-[11px] font-mono shrink-0 whitespace-nowrap">${escapeHtml(n)}</span>
          ${!isLast ? '<span class="text-slate-500 text-xs shrink-0">→</span>' : ''}
        </span>
      `;
    }).join('');

    return `
      <div class="flex items-center justify-between text-xs">
        <span class="font-semibold text-white flex items-center gap-1.5 font-mono shrink-0 whitespace-nowrap">
          ${data.title}
        </span>
        <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${data.badgeColor} shrink-0 whitespace-nowrap inline-flex items-center justify-center">
          ${data.badge}
        </span>
      </div>

      <!-- Chuỗi Đường Đi Đồ Thị / Thuộc Tính -->
      <div class="flex flex-wrap items-center gap-1.5 pt-1">
        ${nodesHtml}
      </div>

      <!-- Mô Tả Ngữ Nghĩa & Chỉ Số Đo Lường -->
      <div class="pt-2 border-t border-white/5 flex items-start justify-between gap-3 text-xs">
        <p class="text-slate-300 leading-relaxed font-sans text-[11px]">
          ${data.description}
        </p>
        <div class="text-right shrink-0 font-mono text-[11px] tabular-nums bg-white/5 px-2 py-1 rounded border border-white/5 whitespace-nowrap">
          <span class="text-slate-400 block text-[9px] uppercase tracking-wider whitespace-nowrap">${data.metricLabel}</span>
          <span class="text-amber-400 font-bold text-xs whitespace-nowrap">${data.metricValue}</span>
        </div>
      </div>
    `;
  }

  function switchProvenanceTab(tabKey) {
    ['p1', 'p2', 'p3', 'p4'].forEach(k => {
      const btn = document.getElementById('prov-tab-btn-' + k);
      if (btn) {
        if (k === tabKey) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      }
    });

    const container = document.getElementById('prov-tab-content-container');
    if (container) {
      container.innerHTML = renderProvenanceTabBody(tabKey);
    }
  }

  function renderProvenanceExplorerHtml(movie) {
    activeProvenanceData = buildMovieProvenance(movie);

    return `
      <!-- Container bọc thanh accordion: w-full overflow-hidden rounded-xl border border-white/10 bg-[#141A24]/60 -->
      <div class="provenance-explorer-box w-full overflow-hidden rounded-xl border border-white/10 bg-[#141A24]/60 transition-all duration-300">
        <!-- Nút bấm accordion header: w-full flex items-center justify-between gap-3 p-3.5 text-left -->
        <button type="button" 
                id="prov-accordion-trigger"
                onclick="MoodGraphApp.toggleProvenanceAccordion()"
                aria-expanded="${isProvenanceAccordionOpen ? 'true' : 'false'}"
                class="w-full flex items-center justify-between gap-3 p-3.5 text-left hover:bg-white/[0.04] transition-colors focus:outline-none cursor-pointer group">
          
          <!-- Cụm tiêu đề bên trái: min-w-0 flex items-center gap-2 truncate -->
          <div class="min-w-0 flex items-center gap-2 truncate">
            <div class="w-6 h-6 rounded-md bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 shrink-0">
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
            </div>
            <span class="text-xs font-semibold text-white truncate">
              Tại sao gợi ý phim này? (Why this movie?)
            </span>
          </div>

          <!-- Cụm badge bên phải: shrink-0 flex items-center gap-1.5 -->
          <div class="shrink-0 flex items-center gap-1.5">
            <span class="px-2 py-0.5 rounded text-[10px] font-mono whitespace-nowrap bg-purple-500/15 text-purple-300 border border-purple-500/30">
              P1 Thể Loại
            </span>
            <svg id="prov-accordion-chevron" 
                 class="w-4 h-4 text-slate-400 group-hover:text-white transition-transform duration-200 shrink-0 ${isProvenanceAccordionOpen ? 'rotate-180' : ''}" 
                 viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>
        </button>

        <!-- Accordion Body (Thu gọn mặc định) -->
        <div id="prov-accordion-body" 
             class="overflow-hidden transition-all duration-300 ease-in-out ${isProvenanceAccordionOpen ? 'max-h-[600px] opacity-100 pointer-events-auto' : 'max-h-0 opacity-0 pointer-events-none'}">
          <div class="p-3.5 space-y-3 border-t border-white/10">
            <!-- 4 Tab Switcher Gọn Gàng -->
            <div class="grid grid-cols-4 gap-1 p-1 bg-white/[0.03] border border-white/5 rounded-lg text-xs font-mono">
              <button type="button" onclick="MoodGraphApp.switchProvenanceTab('p1')" id="prov-tab-btn-p1" class="prov-tab-btn active shrink-0 whitespace-nowrap inline-flex items-center justify-center">
                P1 Thể Loại
              </button>
              <button type="button" onclick="MoodGraphApp.switchProvenanceTab('p2')" id="prov-tab-btn-p2" class="prov-tab-btn shrink-0 whitespace-nowrap inline-flex items-center justify-center">
                P2 Tâm Trạng
              </button>
              <button type="button" onclick="MoodGraphApp.switchProvenanceTab('p3')" id="prov-tab-btn-p3" class="prov-tab-btn shrink-0 whitespace-nowrap inline-flex items-center justify-center">
                P3 Cộng Tác
              </button>
              <button type="button" onclick="MoodGraphApp.switchProvenanceTab('p4')" id="prov-tab-btn-p4" class="prov-tab-btn shrink-0 whitespace-nowrap inline-flex items-center justify-center">
                P4 Vector ALS
              </button>
            </div>

            <!-- Khung Nội Dung Tab Động -->
            <div id="prov-tab-content-container" class="p-3 rounded-lg bg-white/[0.02] border border-white/5 space-y-2">
              ${renderProvenanceTabBody('p1')}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  function openMovieDetailModal(movieId) {
    const modal = document.getElementById('movie-detail-modal');
    const content = document.getElementById('movie-detail-content');
    if (!modal || !content) return;

    const movie = getMovieById(movieId);
    if (!movie) return;

    // Khởi tạo trạng thái Accordion Why this movie luôn thu gọn mặc định khi mở modal
    isProvenanceAccordionOpen = false;

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
        <div class="pt-4 border-t border-white/10 space-y-2.5 w-full overflow-hidden">
          <h4 class="text-xs font-semibold text-amber-400 uppercase tracking-wider font-mono shrink-0 whitespace-nowrap">Tác phẩm đồng điệu lân cận</h4>
          <div class="grid grid-cols-4 gap-2.5 w-full overflow-hidden">
            ${movie.similarMovieIds.map(smId => {
              const sm = getMovieById(smId);
              if (!sm) return '';
              const smTitle = escapeHtml(sm.vietnameseTitle || sm.cleanTitle || sm.title);
              return `
                <div class="p-1.5 rounded-lg bg-[#0F141C] border border-white/5 hover:border-amber-500/40 cursor-pointer transition-all text-center group min-w-0 flex flex-col justify-between"
                     onclick="MoodGraphApp.openMovieDetailModal(${sm.movieId})">
                  <div class="aspect-[2/3] w-full rounded-lg overflow-hidden border border-white/10 mb-1.5 bg-[#0A0D14]">
                    ${renderPosterImgHtml(sm, 'w-full h-full object-cover group-hover:scale-105 transition-transform duration-200')}
                  </div>
                  <div class="min-w-0 w-full space-y-0.5">
                    <span class="truncate block text-xs text-white group-hover:text-amber-300 transition-colors leading-tight" title="${smTitle}">${smTitle}</span>
                    <span class="text-[10px] text-slate-500 font-mono block shrink-0 whitespace-nowrap">${sm.year}</span>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }

    content.innerHTML = `
      <!-- Header Modal & Nút Đóng (Cố định ở trên) -->
      <div class="flex items-start justify-between border-b border-white/10 px-6 py-4 bg-[#0E1420] shrink-0">
        <div class="min-w-0 pr-4">
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-500/15 text-amber-300 border border-amber-500/35 font-mono shrink-0 whitespace-nowrap inline-flex items-center justify-center">
              THÔNG TIN CHI TIẾT
            </span>
            <span class="text-xs font-mono text-slate-400 shrink-0 whitespace-nowrap">MovieID #${movie.movieId}</span>
          </div>
          <h2 class="text-2xl font-bold text-white font-serif mt-1 truncate" title="${titleVn}">${titleVn}</h2>
          <div class="text-xs text-slate-400 italic truncate">${titleEn} • ${movie.year}</div>
        </div>

        <button onclick="MoodGraphApp.closeMovieDetailModal()" 
                class="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors shrink-0"
                title="Đóng hộp thoại">
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <!-- Body cuộn: overflow-y-auto p-6 space-y-6 flex-1 custom-scrollbar -->
      <div class="overflow-y-auto p-6 space-y-6 flex-1 custom-scrollbar">
        <!-- Grid 2 cột: grid grid-cols-1 md:grid-cols-12 gap-6 items-start -->
        <div class="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
          
          <!-- Cột Trái (Media): md:col-span-4 space-y-4 min-w-0 -->
          <div class="md:col-span-4 space-y-4 min-w-0">
            <div class="rounded-xl overflow-hidden shadow-2xl border border-white/10 aspect-[2/3] bg-[#0A0D14] w-full">
              ${renderPosterImgHtml(movie, 'w-full h-full object-cover')}
            </div>

            <!-- Nút Watchlist -->
            <button id="modal-watchlist-btn"
                    data-movie-id="${movie.movieId}"
                    onclick="MoodGraphApp.toggleWatchlist(${movie.movieId})" 
                    class="w-full px-4 py-2.5 rounded-lg border transition-all duration-150 inline-flex items-center justify-center gap-2 shrink-0 whitespace-nowrap ${inWatchlist ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/15' : 'bg-white/5 border-white/10 hover:border-white/20 text-white hover:bg-white/10'}">
              <svg class="w-4 h-4 shrink-0 ${inWatchlist ? 'text-emerald-400 fill-emerald-400' : 'text-white'}" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
              </svg>
              <span class="whitespace-nowrap font-semibold text-xs">${inWatchlist ? 'Đã Lưu Watchlist ✓' : '+ Thêm Vào Watchlist'}</span>
            </button>

            <!-- Bộ Chấm Sao Cá Nhân -->
            <div class="p-3 rounded-lg bg-[#141A24] border border-white/10 space-y-1.5 text-center">
              <div class="text-[11px] text-slate-400 shrink-0 whitespace-nowrap">Đánh giá của bạn:</div>
              <div class="flex items-center justify-center gap-1">
                ${[1, 2, 3, 4, 5].map(starVal => {
                  const isFilled = userRating >= starVal;
                  return `
                    <button onclick="MoodGraphApp.submitRating(${movie.movieId}, ${starVal})" 
                            class="p-1 hover:scale-125 transition-transform" 
                            title="${starVal} sao — ${RATING_LABELS[starVal]}">
                      <svg class="w-5 h-5 ${isFilled ? 'text-amber-400 fill-amber-400' : 'text-slate-600 fill-none'}" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                      </svg>
                    </button>
                  `;
                }).join('')}
              </div>
              <div class="text-[10px] text-amber-300 font-mono mt-1 shrink-0 whitespace-nowrap">
                ${userRating > 0 ? RATING_LABELS[userRating] : 'Chưa chấm điểm'}
              </div>
            </div>

            <!-- Bộ Đôi Nút Liên Kết Ngoài IMDb & TMDb -->
            <div class="space-y-2 pt-2 border-t border-white/10">
              <div class="text-[10px] font-mono text-slate-400 uppercase tracking-wider text-center shrink-0 whitespace-nowrap">Tra Cứu Dữ Liệu Quốc Tế</div>
              <div class="grid grid-cols-2 gap-2">
                <!-- Nút IMDb -->
                <a href="${imdbUrl}" 
                   target="_blank" 
                   rel="noopener noreferrer" 
                   class="inline-flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg bg-[#141A24] hover:bg-[#1B2230] border border-white/10 hover:border-amber-400 text-xs font-medium text-white transition-all shrink-0 whitespace-nowrap group"
                   title="Mở hồ sơ phim trên IMDb trong tab mới">
                  <span class="px-1.5 py-0.5 rounded bg-amber-500 text-slate-950 font-mono font-extrabold text-[10px] tracking-tight shrink-0">IMDb</span>
                  <span class="group-hover:text-amber-300 transition-colors text-[11px] font-medium shrink-0 whitespace-nowrap">Xem IMDb</span>
                  <svg class="w-3 h-3 text-slate-500 group-hover:text-amber-400 transition-colors shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                  </svg>
                </a>

                <!-- Nút TMDb -->
                <a href="${tmdbUrl}" 
                   target="_blank" 
                   rel="noopener noreferrer" 
                   class="inline-flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg bg-[#141A24] hover:bg-[#1B2230] border border-white/10 hover:border-sky-400 text-xs font-medium text-white transition-all shrink-0 whitespace-nowrap group"
                   title="Mở hồ sơ phim trên The Movie Database trong tab mới">
                  <span class="px-1.5 py-0.5 rounded bg-[#01B4E4] text-white font-mono font-extrabold text-[10px] tracking-tight shrink-0">TMDb</span>
                  <span class="group-hover:text-sky-300 transition-colors text-[11px] font-medium shrink-0 whitespace-nowrap">Xem TMDb</span>
                  <svg class="w-3 h-3 text-slate-500 group-hover:text-sky-400 transition-colors shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                  </svg>
                </a>
              </div>
            </div>
          </div>

          <!-- Cột Phải (Chi tiết): md:col-span-8 space-y-4 min-w-0 overflow-hidden -->
          <div class="md:col-span-8 space-y-4 min-w-0 overflow-hidden">
            
            <!-- Metadata Grid -->
            <div class="grid grid-cols-2 gap-3 text-xs">
              <div class="p-2.5 rounded-lg bg-[#141A24] border border-white/10 min-w-0">
                <span class="text-slate-400 block text-[10px] shrink-0 whitespace-nowrap">Đạo diễn:</span>
                <span class="text-white font-semibold truncate block">${movie.director || 'Chưa cập nhật'}</span>
              </div>
              <div class="p-2.5 rounded-lg bg-[#141A24] border border-white/10 min-w-0">
                <span class="text-slate-400 block text-[10px] shrink-0 whitespace-nowrap">Thời lượng:</span>
                <span class="text-white font-semibold shrink-0 whitespace-nowrap">${movie.duration || '120 phút'}</span>
              </div>
              <div class="p-2.5 rounded-lg bg-[#141A24] border border-white/10 min-w-0">
                <span class="text-slate-400 block text-[10px] shrink-0 whitespace-nowrap">Điểm chuẩn MovieLens:</span>
                <span class="text-amber-400 font-bold font-mono shrink-0 whitespace-nowrap">★ ${movie.ratingAvg || 4.2} / 5.0 (${(movie.ratingCount || 1000).toLocaleString('vi-VN')} votes)</span>
              </div>
              <div class="p-2.5 rounded-lg bg-[#141A24] border border-white/10 min-w-0">
                <span class="text-slate-400 block text-[10px] shrink-0 whitespace-nowrap">Miền tâm trạng:</span>
                <span class="text-emerald-300 font-semibold truncate block">${movie.moodLabel || 'Đặc sắc'}</span>
              </div>
            </div>

            <!-- Tóm Tắt Nội Dung -->
            <div class="space-y-1">
              <h4 class="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono shrink-0 whitespace-nowrap">Cốt truyện tác phẩm</h4>
              <p class="text-xs text-slate-300 leading-relaxed">
                ${escapeHtml(movie.synopsis || 'Hành trình điện ảnh sâu sắc khám phá số phận và triết lý nhân sinh.')}
              </p>
            </div>

            <!-- Thông Số Không Gian Nhúng 3D (3D Latent Space) -->
            <div class="p-3.5 rounded-xl bg-[#0F141C] border border-white/10 space-y-2">
              <div class="flex items-center justify-between text-xs">
                <span class="text-amber-300 font-bold font-mono uppercase tracking-wider shrink-0 whitespace-nowrap">THÔNG SỐ KHÔNG GIAN NHÚNG 3D</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-[#1B2230] text-emerald-400 shrink-0 whitespace-nowrap">Cluster 3D</span>
              </div>
              <div class="grid grid-cols-3 gap-2 font-mono text-[11px]">
                <div class="p-2 rounded bg-[#141A24]">
                  <span class="text-slate-400 block text-[10px] shrink-0 whitespace-nowrap">Tọa độ X:</span>
                  <span class="text-white tabular-nums">${coords.x}</span>
                </div>
                <div class="p-2 rounded bg-[#141A24]">
                  <span class="text-slate-400 block text-[10px] shrink-0 whitespace-nowrap">Tọa độ Y:</span>
                  <span class="text-white tabular-nums">${coords.y}</span>
                </div>
                <div class="p-2 rounded bg-[#141A24]">
                  <span class="text-slate-400 block text-[10px] shrink-0 whitespace-nowrap">Tọa độ Z:</span>
                  <span class="text-white tabular-nums">${coords.z}</span>
                </div>
              </div>
              <div class="flex items-center gap-2 text-xs text-slate-400">
                <span class="shrink-0 whitespace-nowrap">Cụm không gian:</span>
                <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-[#141A24] border border-white/10 text-white font-medium text-[11px] min-w-0 max-w-[280px]">
                  <svg class="w-3.5 h-3.5 text-amber-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                  </svg>
                  <span class="truncate">${coords.clusterName || 'Cụm Điện Ảnh Tổng Hợp'}</span>
                </span>
              </div>
            </div>

            <!-- Bộ 4 Tab Kiểm Chứng Nguồn Gốc (Why this movie? Provenance Explorer) -->
            ${renderProvenanceExplorerHtml(movie)}

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

  function switchPersona(personaId, silent) {
    let pid = personaId;
    if (pid === 'user42') pid = 'user_cold';

    ensurePresetPersonas();

    if (!window.MOCK_DATA || !window.MOCK_DATA.presetPersonas) return;
    const persona = window.MOCK_DATA.presetPersonas[pid] || window.MOCK_DATA.presetPersonas[personaId];
    if (!persona) return;

    MoodGraphState.activePersonaId = pid;
    MoodGraphState.currentUser = JSON.parse(JSON.stringify(persona));
    MoodGraphState.isColdStart = (pid === 'user_cold' || pid === 'user42');
    MoodGraphState.boostedGenres = [];

    // Cập nhật cấu hình slider theo Persona
    if (persona.defaultSliders) {
      MoodGraphState.sliders = Object.assign({}, persona.defaultSliders);
    }

    // Bảo toàn tách biệt dữ liệu đánh giá:
    // Nếu chọn live_session: nạp lại tập đánh giá trực tiếp của Live Session
    // Nếu chọn user_cold / user42: rỗng {} (cold-start)
    // Nếu chọn user1, user2, user3: nạp initialRatings mẫu của persona đó
    if (pid === 'live_session') {
      MoodGraphState.userRatings = Object.assign({}, MoodGraphState.liveSessionRatings || {});
      MoodGraphState.isColdStart = Object.keys(MoodGraphState.userRatings).length === 0;
    } else if (pid === 'user_cold' || pid === 'user42') {
      MoodGraphState.userRatings = {};
      MoodGraphState.isColdStart = true;
    } else {
      MoodGraphState.userRatings = Object.assign({}, persona.initialRatings || {});
      MoodGraphState.isColdStart = false;
    }
    saveStorageJson("moodgraph_user_ratings", MoodGraphState.userRatings);

    // Đồng bộ Slider và Chú giải
    syncSliderInputs();

    // Đồng bộ giá trị trên Header Selector
    const headerSel = document.getElementById('header-persona-selector');
    if (headerSel) {
      headerSel.value = personaId;
      if (headerSel.value !== personaId) {
        headerSel.value = (pid === 'user42') ? 'user_cold' : pid;
      }
    }

    const avatarSpan = document.getElementById('header-user-avatar');
    if (avatarSpan) avatarSpan.textContent = persona.avatarLetter || persona.name.charAt(0);

    // Đồng bộ trạng thái 5 nút trên thanh Persona Bar Trang 1
    const personaMap = {
      user1: 'btn-persona-user1',
      user2: 'btn-persona-user2',
      user3: 'btn-persona-user3',
      user_cold: 'btn-persona-user-cold',
      live_session: 'btn-persona-live'
    };
    Object.keys(personaMap).forEach(key => {
      const btn = document.getElementById(personaMap[key]);
      if (btn) {
        if (key === pid || (key === 'user_cold' && pid === 'user42')) {
          btn.className = "persona-btn active px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-2.5 bg-[#D97706] text-white border border-[#F59E0B] transition-all shadow-md";
          const numSpan = btn.querySelector('span');
          if (numSpan) numSpan.className = "w-6 h-6 rounded-full bg-black/30 flex items-center justify-center text-[11px] font-bold";
        } else {
          const borderColor = key === 'user_cold' ? 'hover:border-[#10B981]' : (key === 'live_session' ? 'hover:border-[#38BDF8]' : 'hover:border-[#F59E0B]');
          const iconColor = key === 'user_cold' ? 'text-[#10B981]' : (key === 'live_session' ? 'text-[#38BDF8]' : 'text-[#F59E0B]');
          btn.className = `persona-btn px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-2.5 bg-[#0B0F14] text-[#94A3B8] hover:text-white border border-[rgba(255,255,255,0.08)] ${borderColor} transition-all`;
          const numSpan = btn.querySelector('span');
          if (numSpan) numSpan.className = `w-6 h-6 rounded-full bg-[#1B2230] flex items-center justify-center text-[11px] font-bold ${iconColor}`;
        }
      }
    });

    // Đồng bộ sang Mode B nếu có
    const mapToLab = {
      user1: 'user1',
      user2: 'user2',
      user3: 'user3',
      user_cold: 'user42',
      user42: 'user42',
      live_session: 'live_session'
    };
    const targetLabUser = mapToLab[pid] || 'user1';
    MoodGraphState.selectedLabUser = targetLabUser;
    const labSel = document.getElementById('lab-user-selector');
    if (labSel && labSel.value !== targetLabUser) {
      labSel.value = targetLabUser;
    }
    if (window.AcademicLab && window.AcademicLab.state) {
      window.AcademicLab.state.selectedUser = targetLabUser;
    }

    // Tái tính toán và kết xuất đề xuất
    updateDynamicRecommendations();

    // Đồng bộ sang Mode B (Phòng Thí Nghiệm Học Thuật)
    if (window.MoodGraphApp && typeof window.MoodGraphApp.changeLabUser === 'function') {
      const labState = window.AcademicLab && window.AcademicLab.state;
      if (labState && labState.selectedUser !== personaId) {
        window.MoodGraphApp.changeLabUser(personaId, true);
      }
    }

    if (!silent) {
      showToast(
        "Đã Chuyển Hồ Sơ Khán Giả",
        `Đang trải nghiệm theo góc nhìn của ${persona.name} (${persona.roleDescription}).`,
        'info'
      );
    }
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

  function changeLabUser(userKey, silent) {
    MoodGraphState.selectedLabUser = userKey;

    // 1. Đồng bộ sang AcademicLabState nếu tồn tại
    if (window.AcademicLab && window.AcademicLab.state) {
      window.AcademicLab.state.selectedUser = userKey;
    }

    // 2. Đồng bộ dropdown lab-user-selector
    const selector = document.getElementById('lab-user-selector');
    if (selector && selector.value !== userKey) {
      selector.value = userKey;
    }

    // 3. Đồng bộ ngược lại Mode A (activePersonaId và header selector)
    const mapToApp = {
      'user1': 'user1',
      'user2': 'user2',
      'user3': 'user3',
      'user42': 'user_cold',
      'live_session': 'live_session'
    };
    const appPersonaId = mapToApp[userKey] || userKey;
    MoodGraphState.activePersonaId = appPersonaId;
    MoodGraphState.isColdStart = (appPersonaId === 'user_cold');

    // Cập nhật header selector
    const headerSel = document.getElementById('header-persona-selector');
    if (headerSel && headerSel.value !== appPersonaId) {
      headerSel.value = appPersonaId;
    }

    // Cập nhật avatar trên header
    const avatarSpan = document.getElementById('header-user-avatar');
    if (avatarSpan && window.MOCK_DATA && window.MOCK_DATA.presetPersonas) {
      const p = window.MOCK_DATA.presetPersonas[appPersonaId];
      if (p) {
        avatarSpan.textContent = p.avatarLetter || p.name.charAt(0);
      }
    }

    // Cập nhật nhãn option live nếu có
    const optLive = document.getElementById('opt-lab-live');
    const liveCount = (MoodGraphState.liveSessionRatings) ? Object.keys(MoodGraphState.liveSessionRatings).length : 0;
    if (optLive) {
      optLive.textContent = `🎬 Tài khoản của bạn (Live Session • ${liveCount} đánh giá)`;
    }

    // 4. Gọi kết xuất Mode B nếu có
    if (window.AcademicLab && typeof window.AcademicLab.renderHeadToHeadComparison === 'function') {
      window.AcademicLab.renderHeadToHeadComparison(userKey);
    } else {
      renderHeadToHeadComparison(userKey);
    }

    // 5. Cập nhật vị trí trọng tâm trong 3D / 2D
    if (window.AcademicLab && window.AcademicLab.visualizer && typeof window.AcademicLab.visualizer.updateUserCenterForSelectedUser === 'function') {
      window.AcademicLab.visualizer.updateUserCenterForSelectedUser(userKey);
    }

    if (!silent) {
      showToast("Đã Chuyển Tập Người Dùng", `Đã nạp đoàn hệ kiểm chuẩn: ${userKey.toUpperCase()}.`, 'info');
    }
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

    renderHeadToHeadComparison(MoodGraphState.selectedLabUser);
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

  function renderHeadToHeadComparison(userId) {
    const container = document.getElementById('head-to-head-columns');
    if (!container) return;

    // Xác định userKey: ưu tiên tham số truyền vào
    const targetUser = userId || MoodGraphState.selectedLabUser || (window.AcademicLab && window.AcademicLab.state && window.AcademicLab.state.selectedUser) || 'live_session';
    MoodGraphState.selectedLabUser = targetUser;

    // Nếu AcademicLab chuyên sâu đã sẵn sàng, ủy quyền trực tiếp cho academic_lab.js
    if (window.AcademicLab && typeof window.AcademicLab.renderHeadToHeadComparison === 'function') {
      if (window.AcademicLab.state) {
        window.AcademicLab.state.selectedUser = targetUser;
      }
      window.AcademicLab.renderHeadToHeadComparison(targetUser);
      return;
    }

    // Cơ chế dự phòng khi AcademicLab chưa tải xong: gọi hàm truy xuất Top-10 chuẩn hóa
    const models = [
      { id: 'als', name: 'Spark ALS', color: '#0284C7' },
      { id: 'kg', name: 'Knowledge Graph', color: '#059669' },
      { id: 'hybrid_rrf', name: 'Hybrid RRF (k=60)', color: '#D97706' },
      { id: 'hybrid_weighted', name: 'Hybrid Weighted', color: '#EA580C' },
      { id: 'popularity', name: 'Popularity Baseline', color: '#78716C' }
    ];

    let html = '';
    models.forEach(m => {
      let list = [];
      if (typeof window.getTop10ForModelAndUser === 'function') {
        list = window.getTop10ForModelAndUser(m.id, targetUser);
      } else if (window.AcademicLab && typeof window.AcademicLab.getTop10ForModelAndUser === 'function') {
        list = window.AcademicLab.getTop10ForModelAndUser(m.id, targetUser);
      } else if (window.MOCK_DATA && window.MOCK_DATA.top10ByModel) {
        list = window.MOCK_DATA.top10ByModel[m.id] || [];
      }

      html += `
        <div class="head-to-head-column">
          <div class="model-column-header" style="border-top: 3px solid ${m.color};">
            <span class="text-xs font-bold text-white font-serif">${m.name}</span>
            <span class="text-[10px] text-[#94A3B8] font-mono">10 đề xuất hàng đầu</span>
          </div>
          <div class="divide-y divide-[rgba(255,255,255,0.04)]">
            ${list.map(item => {
              const movie = getMovieById(item.movieId || item.id);
              const title = movie ? (movie.vietnameseTitle || movie.cleanTitle || movie.title) : (item.title || `Phim #${item.movieId || item.id}`);
              return `
                <div class="model-item-row" 
                     data-interlock-movie-id="${item.movieId || item.id}" 
                     data-model-id="${m.id}"
                     onmouseenter="MoodGraphApp.setInterlock(${item.movieId || item.id})"
                     onmouseleave="MoodGraphApp.clearInterlock()"
                     onclick="MoodGraphApp.openMovieDetailModal(${item.movieId || item.id})">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="movie-rank-badge w-5 h-5 rounded-full bg-[#1B2230] text-[10px] font-mono flex items-center justify-center text-white shrink-0">
                      ${item.rank}
                    </span>
                    <span class="truncate text-xs text-[#E2E8F0]">${title}</span>
                  </div>
                  <span class="text-[10px] font-mono text-[#94A3B8] ml-1 shrink-0">
                    ${item.rawScoreText || (item.score ? (typeof item.score === 'number' ? item.score.toFixed(3) : item.score) : '')}
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

  const existingApp = (typeof window !== 'undefined' && window.MoodGraphApp) || {};
  window.MoodGraphApp = Object.assign(existingApp, {
    // Mode Switcher
    switchMode,

    // Persona Quick Switcher (Item 4)
    switchPersona,

    // Sliders & Moods & Semantic Hints (Item 3)
    onSliderChange,
    resetSliders,
    selectMood,
    updateSliderSemanticHints: updateAllSliderSemanticHints,
    updateSlider: function (name, val) {
      if (MoodGraphState.sliders && MoodGraphState.sliders[name] !== undefined) {
        MoodGraphState.sliders[name] = Math.max(0.0, Math.min(1.0, Number(val)));
        syncSliderInputs();
      }
    },

    // Genre Filters & Closed-Loop Boost
    selectGenreFilter,
    resetFilters,
    toggleGenreBoost: function (genre) {
      if (!Array.isArray(MoodGraphState.boostedGenres)) MoodGraphState.boostedGenres = [];
      const idx = MoodGraphState.boostedGenres.indexOf(genre);
      if (idx >= 0) {
        MoodGraphState.boostedGenres.splice(idx, 1);
      } else {
        MoodGraphState.boostedGenres.push(genre);
      }
    },

    // Movie Detail Modal & Provenance Explorer
    openMovieDetailModal,
    closeMovieDetailModal,
    switchProvenanceTab,
    toggleProvenanceAccordion,

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
  });

  // Khởi tạo alias Module MovieDetailModalComponent để tương thích tối đa với các module ngoài
  window.MovieDetailModalComponent = {
    open: openMovieDetailModal,
    close: closeMovieDetailModal,
    toggleWatchlist: toggleWatchlist,
    switchTab: switchProvenanceTab,
    toggleAccordion: toggleProvenanceAccordion
  };

})(window, document);
