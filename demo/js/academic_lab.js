/**
 * MOODGRAPH - PHÒNG THÍ NGHIỆM HỌC THUẬT & KHÔNG GIAN NHÚNG 3D THREE.JS
 * File: js/academic_lab.js
 * 
 * Mô-đun điều khiển toàn diện cho Trang 2 (Mode B - Academic Lab & 3D Latent Space):
 * 1. Trực quan hóa Không gian Nhúng 3D (Three.js WebGL & Canvas 2D Perspective Projection Fallback).
 * 2. Bảng Đối Đầu 5 Thuật Toán Gợi Ý với cơ chế Hover Interlock đa chiều.
 * 3. Ma Trận Nhiệt Tương Quan Thứ Hạng Spearman [-1.0, 1.0] và Trùng Lặp Jaccard [0.0, 1.0] (k < 2 trả về null).
 * 4. Bảng Chỉ Số Kiểm Chuẩn Offline Toàn Diện (NDCG, Hit Rate, Novelty, Diversity, Coverage).
 * 5. Mô Phỏng Thách Thức Thực Tế: Độ Bền Cold-Start (Sparsity Degradation) & Đuôi Dài Long-Tail Pareto.
 * 
 * Quy chuẩn:
 * - 100% Tiếng Việt chuẩn ngữ pháp và UTF-8.
 * - Tuyệt đối không dùng ký hiệu LaTeX hoặc dấu dollar ($).
 * - Tự động thích ứng, tương thích độc lập 100% phía Client (không cần máy chủ backend).
 */

(function (window, document) {
  'use strict';

  // =========================================================================
  // 1. TRẠNG THÁI NỘI BỘ PHÒNG THÍ NGHIỆM (ACADEMIC LAB STATE)
  // =========================================================================
  const AcademicLabState = {
    selectedUser: 'live_session',
    consensusFilter: 'all', // 'all' | 'overlap' | 'unique'
    heatmapMetric: 'spearman', // 'spearman' | 'jaccard'
    activeInterlockMovieId: null,
    is3DInitialized: false,
    engineType: 'none', // 'threejs' | 'canvas2d'
    autoRotate3D: true,
    show3DRays: true,
    selectedNodeMovie: null,
    hoveredNodeMovie: null
  };

  // =========================================================================
  // 2. BẢNG MÀU THỂ LOẠI & TIỆN ÍCH HỌC THUẬT
  // =========================================================================
  const GENRE_COLOR_MAP = {
    'Drama': { hex: '#F59E0B', num: 0xF59E0B, name: 'Chính kịch' },
    'Crime': { hex: '#B45309', num: 0xB45309, name: 'Tội phạm' },
    'Sci-Fi': { hex: '#0EA5E9', num: 0x0EA5E9, name: 'Viễn tưởng' },
    'Action': { hex: '#EF4444', num: 0xEF4444, name: 'Hành động' },
    'War': { hex: '#E11D48', num: 0xE11D48, name: 'Chiến tranh' },
    'Romance': { hex: '#F43F5E', num: 0xF43F5E, name: 'Lãng mạn' },
    'Comedy': { hex: '#10B981', num: 0x10B981, name: 'Hài hước' },
    'Mystery': { hex: '#64748B', num: 0x64748B, name: 'Bí ẩn' },
    'Adventure': { hex: '#F97316', num: 0xF97316, name: 'Phiêu lưu' },
    'Fantasy': { hex: '#0284C7', num: 0x0284C7, name: 'Kỳ ảo' },
    'Animation': { hex: '#34D399', num: 0x34D399, name: 'Hoạt hình' },
    'Thriller': { hex: '#64748B', num: 0x64748B, name: 'Giật gân' },
    'Film-Noir': { hex: '#78716C', num: 0x78716C, name: 'Phim đen' }
  };

  function getGenreColorInfo(genre) {
    return GENRE_COLOR_MAP[genre] || { hex: '#D97706', num: 0xD97706, name: genre || 'Điện ảnh' };
  }

  function getMovieById(movieId) {
    if (!window.MOCK_DATA || !window.MOCK_DATA.catalog) return null;
    const mid = Number(movieId);
    return window.MOCK_DATA.catalog.find(m => m.movieId === mid) || null;
  }

  // Tính khoảng cách Cosine giữa 2 vector 3D
  function calcCosineSimilarity(v1, v2) {
    const dot = (v1.x * v2.x) + (v1.y * v2.y) + (v1.z * v2.z);
    const n1 = Math.sqrt(v1.x * v1.x + v1.y * v1.y + v1.z * v1.z) || 1e-6;
    const n2 = Math.sqrt(v2.x * v2.x + v2.y * v2.y + v2.z * v2.z) || 1e-6;
    return dot / (n1 * n2);
  }

  // Tính khoảng cách Euclid giữa 2 vector 3D
  function calcEuclideanDistance(v1, v2) {
    const dx = v1.x - v2.x;
    const dy = v1.y - v2.y;
    const dz = v1.z - v2.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  // =========================================================================
  // 3. MODULE 3D LATENT SPACE (THREE.JS WEBGL + FALLBACK CANVAS 2D)
  // =========================================================================
  class LatentSpace3DVisualizer {
    constructor() {
      this.canvas = document.getElementById('three-canvas');
      this.container = document.getElementById('threejs-container');
      this.hudCard = document.getElementById('three-hud-card');
      
      this.scene = null;
      this.camera = null;
      this.renderer = null;
      this.controls = null;
      this.raycaster = null;
      this.mouse = null;
      
      this.movieNodes = [];
      this.userOrb = null;
      this.haloRing = null;
      this.rayLines = [];
      this.hoveredMesh = null;
      this.animFrameId = null;

      // Dữ liệu vị trí người dùng trung tâm và trạng thái nội suy chuyển động (Lerp)
      this.userCenterPos = { x: 0, y: 5, z: 0 };
      this.currentPos = this.userCenterPos;
      this.targetPos = { x: 0, y: 5, z: 0 };
      this.lerpSpeed = 0.06;
      this.lerpEpsilon = 0.02;
      this.isTransitioning = false;
      this.activeTop10Ids = new Set();

      // Thuộc tính phục vụ Fallback Canvas 2D
      this.ctx2d = null;
      this.rotX = 0.2;
      this.rotY = 0.0;
      this.isDragging2D = false;
      this.lastMouseX = 0;
      this.lastMouseY = 0;
      this.nodes2D = [];
      this.stars2D = [];
    }

    get userRays() {
      return this.rayLines;
    }

    init() {
      if (!this.canvas || !this.container) return;

      const hasThree = typeof THREE !== 'undefined';
      let webglSupported = false;

      if (hasThree) {
        try {
          const testCanvas = document.createElement('canvas');
          webglSupported = Boolean(
            window.WebGLRenderingContext && 
            (testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl'))
          );
        } catch (e) {
          webglSupported = false;
        }
      }

      if (hasThree && webglSupported) {
        AcademicLabState.engineType = 'threejs';
        this.initThreeJS();
      } else {
        AcademicLabState.engineType = 'canvas2d';
        this.initCanvas2DFallback();
      }

      AcademicLabState.is3DInitialized = true;
    }

    // -----------------------------------------------------------------------
    // 3.1. TRIỂN KHAI THREE.JS WEBGL ENGINE
    // -----------------------------------------------------------------------
    initThreeJS() {
      const rect = this.container.getBoundingClientRect();
      const width = rect.width || this.container.clientWidth || 800;
      const height = rect.height || this.container.clientHeight || 520;

      // 1. Scene tông Dark Charcoal (#0A0D14)
      this.scene = new THREE.Scene();
      this.scene.background = new THREE.Color(0x0A0D14);
      this.scene.fog = new THREE.FogExp2(0x0A0D14, 0.0028);

      // 2. Camera góc phối cảnh 50 độ
      this.camera = new THREE.PerspectiveCamera(50, width / height, 1, 1200);
      this.camera.position.set(0, 40, 185);

      // 3. Renderer khử răng cưa
      this.renderer = new THREE.WebGLRenderer({
        canvas: this.canvas,
        antialias: true,
        alpha: false,
        powerPreference: 'high-performance'
      });
      this.renderer.setSize(width, height);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

      // 4. Ánh sáng ấm trang nhã
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
      this.scene.add(ambientLight);

      const amberPointLight = new THREE.PointLight(0xF59E0B, 1.8, 400);
      amberPointLight.position.set(0, 30, 10);
      this.scene.add(amberPointLight);

      const coolFillLight = new THREE.DirectionalLight(0x0284C7, 0.4);
      coolFillLight.position.set(100, 150, 50);
      this.scene.add(coolFillLight);

      // 5. OrbitControls
      if (typeof THREE.OrbitControls !== 'undefined') {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.06;
        this.controls.maxDistance = 400;
        this.controls.minDistance = 35;
        this.controls.autoRotate = AcademicLabState.autoRotate3D;
        this.controls.autoRotateSpeed = 0.45;
      }

      // 6. Raycaster
      this.raycaster = new THREE.Raycaster();
      this.mouse = new THREE.Vector2(-999, -999);

      // 7. Tạo bụi sao, các điểm phim, vector người dùng và tia gợi ý
      this.createThreeStarfield();
      this.createThreeMovieNodes();
      this.createThreeUserOrb();
      this.createThreeRecommendationRays();

      // 8. Đăng ký sự kiện tương tác
      this.setupThreeEvents();

      // 9. Vòng lặp Render 60 FPS
      this.animateThree();
    }

    createThreeStarfield() {
      const starCount = 700;
      const geometry = new THREE.BufferGeometry();
      const positions = new Float32Array(starCount * 3);

      for (let i = 0; i < starCount * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 800;
        positions[i + 1] = (Math.random() - 0.5) * 500;
        positions[i + 2] = (Math.random() - 0.5) * 800;
      }

      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      const material = new THREE.PointsMaterial({
        color: 0x475569,
        size: 1.4,
        transparent: true,
        opacity: 0.55
      });

      const starfield = new THREE.Points(geometry, material);
      this.scene.add(starfield);
    }

    createThreeMovieNodes() {
      const catalog = (window.MOCK_DATA && window.MOCK_DATA.catalog) || [];
      const sphereGeo = new THREE.SphereGeometry(1.6, 18, 18);

      catalog.forEach((movie) => {
        const rawPos = movie.embedding3d || {
          x: (Math.random() - 0.5) * 160,
          y: (Math.random() - 0.5) * 90,
          z: (Math.random() - 0.5) * 160
        };

        const colorInfo = getGenreColorInfo(movie.primaryGenre);
        const material = new THREE.MeshStandardMaterial({
          color: colorInfo.num,
          emissive: colorInfo.num,
          emissiveIntensity: 0.38,
          roughness: 0.35,
          metalness: 0.25
        });

        const mesh = new THREE.Mesh(sphereGeo, material);
        mesh.position.set(rawPos.x, rawPos.y, rawPos.z);
        mesh.userData = {
          movie: movie,
          baseColor: colorInfo.num,
          baseEmissive: 0.38,
          coords: { x: rawPos.x, y: rawPos.y, z: rawPos.z }
        };

        this.scene.add(mesh);
        this.movieNodes.push(mesh);
      });
    }

    createThreeUserOrb() {
      // Khối cầu người dùng màu Vàng Hổ Phách lớn gấp 2.5 lần
      const userGeo = new THREE.SphereGeometry(3.8, 32, 32);
      const userMat = new THREE.MeshStandardMaterial({
        color: 0xF59E0B,
        emissive: 0xD97706,
        emissiveIntensity: 0.95,
        roughness: 0.2,
        metalness: 0.7
      });

      this.userOrb = new THREE.Mesh(userGeo, userMat);
      this.userOrb.position.set(this.userCenterPos.x, this.userCenterPos.y, this.userCenterPos.z);
      this.scene.add(this.userOrb);

      // Vành hào quang co giãn xung nhịp (Pulsing Halo Ring)
      const ringGeo = new THREE.RingGeometry(5.0, 6.2, 40);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0xFBBF24,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.75
      });

      this.haloRing = new THREE.Mesh(ringGeo, ringMat);
      this.haloRing.position.copy(this.userOrb.position);
      this.haloRing.rotation.x = Math.PI / 2;
      this.scene.add(this.haloRing);
    }

    createThreeRecommendationRays() {
      // Xóa các đường tia cũ nếu có và giải phóng tài nguyên WebGL an toàn
      this.rayLines.forEach(l => {
        if (this.scene) this.scene.remove(l);
        if (l.geometry) l.geometry.dispose();
        if (l.material) l.material.dispose();
      });
      this.rayLines = [];

      const top10 = (window.MOCK_DATA && window.MOCK_DATA.top10ByModel && window.MOCK_DATA.top10ByModel.hybrid_rrf) || [];
      const top10Ids = new Set(top10.map(m => m.movieId));
      this.activeTop10Ids = top10Ids;

      this.movieNodes.forEach(mesh => {
        const mid = mesh.userData.movie.movieId;
        if (top10Ids.has(mid)) {
          const points = [
            new THREE.Vector3(this.userCenterPos.x, this.userCenterPos.y, this.userCenterPos.z),
            mesh.position
          ];
          const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
          if (lineGeo.attributes && lineGeo.attributes.position && lineGeo.attributes.position.setUsage) {
            lineGeo.attributes.position.setUsage(THREE.DynamicDrawUsage);
          }
          const lineMat = new THREE.LineBasicMaterial({
            color: 0xF59E0B,
            transparent: true,
            opacity: 0.35,
            linewidth: 1
          });
          const line = new THREE.Line(lineGeo, lineMat);
          line.visible = AcademicLabState.show3DRays;
          this.scene.add(line);
          this.rayLines.push(line);
        }
      });
    }

    setupThreeEvents() {
      const el = this.renderer.domElement;

      el.addEventListener('mousemove', (e) => {
        const rect = el.getBoundingClientRect();
        this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.movieNodes);

        if (intersects.length > 0) {
          const hit = intersects[0].object;
          if (this.hoveredMesh !== hit) {
            this.resetThreeHover();
            this.hoveredMesh = hit;
            hit.scale.set(1.65, 1.65, 1.65);
            hit.material.emissiveIntensity = 0.95;
            el.style.cursor = 'pointer';
            this.showFloatingHud(hit.userData.movie, hit.position);
          }
        } else {
          if (this.hoveredMesh) {
            this.resetThreeHover();
            el.style.cursor = 'grab';
          }
        }
      });

      el.addEventListener('click', (e) => {
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.movieNodes);
        if (intersects.length > 0) {
          const hit = intersects[0].object;
          const movie = hit.userData.movie;
          this.showFloatingHud(movie, hit.position, true);
          if (window.MoodGraphApp && window.MoodGraphApp.openMovieDetailModal) {
            window.MoodGraphApp.openMovieDetailModal(movie.movieId);
          }
        }
      });

      window.addEventListener('resize', () => this.handleResize());

      if (typeof ResizeObserver !== 'undefined' && this.container) {
        try {
          this.resizeObserver = new ResizeObserver(() => {
            this.handleResize();
          });
          this.resizeObserver.observe(this.container);
        } catch (e) {
          // Fallback an toàn nếu trình duyệt cũ không hỗ trợ ResizeObserver
        }
      }
    }

    resetThreeHover() {
      if (this.hoveredMesh) {
        this.hoveredMesh.scale.set(1.0, 1.0, 1.0);
        this.hoveredMesh.material.emissiveIntensity = this.hoveredMesh.userData.baseEmissive || 0.38;
        this.hoveredMesh = null;
      }
    }

    animateThree() {
      this.animFrameId = requestAnimationFrame(() => this.animateThree());

      // 1. Tính toán Linear Interpolation (Lerp) cho vị trí Quả cầu User Center
      if (!this.targetPos) {
        this.targetPos = Object.assign({}, this.userCenterPos);
      }
      const dx = this.targetPos.x - this.userCenterPos.x;
      const dy = this.targetPos.y - this.userCenterPos.y;
      const dz = this.targetPos.z - this.userCenterPos.z;
      const distSq = dx * dx + dy * dy + dz * dz;

      if (distSq > (this.lerpEpsilon * this.lerpEpsilon)) {
        this.userCenterPos.x += dx * this.lerpSpeed;
        this.userCenterPos.y += dy * this.lerpSpeed;
        this.userCenterPos.z += dz * this.lerpSpeed;
        this.isTransitioning = true;
      } else {
        this.userCenterPos.x = this.targetPos.x;
        this.userCenterPos.y = this.targetPos.y;
        this.userCenterPos.z = this.targetPos.z;
        this.isTransitioning = false;
      }
      this.currentPos = this.userCenterPos;

      // 2. Cập nhật vị trí Quả cầu và Vành hào quang theo userCenterPos đã nội suy
      if (this.userOrb) {
        this.userOrb.position.set(this.userCenterPos.x, this.userCenterPos.y, this.userCenterPos.z);
      }
      if (this.haloRing) {
        this.haloRing.position.set(this.userCenterPos.x, this.userCenterPos.y, this.userCenterPos.z);
      }

      // 3. Cập nhật liên tục đỉnh gốc (Vertex 0) của toàn bộ chùm tia Ray Lines
      if (this.rayLines && this.rayLines.length > 0) {
        for (let i = 0; i < this.rayLines.length; i++) {
          const line = this.rayLines[i];
          if (line && line.geometry && line.geometry.attributes && line.geometry.attributes.position) {
            const posAttr = line.geometry.attributes.position;
            posAttr.setXYZ(0, this.userCenterPos.x, this.userCenterPos.y, this.userCenterPos.z);
            posAttr.needsUpdate = true;
          }
        }
      }

      // 4. Hiệu ứng thở co giãn hào quang người dùng
      const time = performance.now() * 0.001;
      if (this.haloRing) {
        const pulse = 1.0 + 0.22 * Math.sin(time * 3.2);
        this.haloRing.scale.set(pulse, pulse, pulse);
        this.haloRing.material.opacity = 0.65 + 0.25 * Math.sin(time * 3.2);
      }

      if (this.controls) {
        this.controls.autoRotate = AcademicLabState.autoRotate3D;
        this.controls.update();
      }

      if (this.renderer && this.scene && this.camera) {
        this.renderer.render(this.scene, this.camera);
      }
    }

    // -----------------------------------------------------------------------
    // 3.2. TRIỂN KHAI FALLBACK CANVAS 2D PERSPECTIVE PROJECTION ENGINE
    // -----------------------------------------------------------------------
    initCanvas2DFallback() {
      this.ctx2d = this.canvas.getContext('2d');
      this.resizeCanvas2D();

      // Khởi tạo bụi sao 2D
      this.stars2D = [];
      for (let i = 0; i < 220; i++) {
        this.stars2D.push({
          x: (Math.random() - 0.5) * 800,
          y: (Math.random() - 0.5) * 500,
          z: (Math.random() - 0.5) * 800,
          size: Math.random() * 1.5 + 0.5
        });
      }

      // Khởi tạo điểm phim 2D
      const catalog = (window.MOCK_DATA && window.MOCK_DATA.catalog) || [];
      this.nodes2D = catalog.map(movie => {
        const pos = movie.embedding3d || {
          x: (Math.random() - 0.5) * 150,
          y: (Math.random() - 0.5) * 90,
          z: (Math.random() - 0.5) * 150
        };
        const colorInfo = getGenreColorInfo(movie.primaryGenre);
        return {
          movie: movie,
          x: pos.x,
          y: pos.y,
          z: pos.z,
          color: colorInfo.hex,
          radius: 4.5,
          projX: 0,
          projY: 0,
          projScale: 1
        };
      });

      // Tương tác chuột xoay phối cảnh 2D
      this.setupCanvas2DEvents();

      // Khởi tạo danh sách Top-10 mặc định cho Ray Lines 2D
      const defaultTop10 = (window.MOCK_DATA && window.MOCK_DATA.top10ByModel && window.MOCK_DATA.top10ByModel.hybrid_rrf) || [];
      this.activeTop10Ids = new Set(defaultTop10.map(m => m.movieId));

      // Vòng lặp render 2D 60 FPS
      this.animateCanvas2D();
    }

    resizeCanvas2D() {
      const rect = this.container.getBoundingClientRect();
      const width = rect.width || 800;
      const height = rect.height || 520;
      this.canvas.width = width * (window.devicePixelRatio || 1);
      this.canvas.height = height * (window.devicePixelRatio || 1);
      this.ctx2d.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
    }

    setupCanvas2DEvents() {
      const el = this.canvas;

      el.addEventListener('mousedown', (e) => {
        this.isDragging2D = true;
        this.lastMouseX = e.clientX;
        this.lastMouseY = e.clientY;
        el.style.cursor = 'grabbing';
      });

      window.addEventListener('mouseup', () => {
        this.isDragging2D = false;
        el.style.cursor = 'grab';
      });

      el.addEventListener('mousemove', (e) => {
        const rect = el.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        if (this.isDragging2D) {
          const dx = e.clientX - this.lastMouseX;
          const dy = e.clientY - this.lastMouseY;
          this.rotY += dx * 0.008;
          this.rotX += dy * 0.008;
          this.lastMouseX = e.clientX;
          this.lastMouseY = e.clientY;
        } else {
          // Hit-test tìm điểm gần nhất
          let hit = null;
          for (let i = this.nodes2D.length - 1; i >= 0; i--) {
            const n = this.nodes2D[i];
            const dist = Math.hypot(mx - n.projX, my - n.projY);
            if (dist <= n.radius * n.projScale + 4) {
              hit = n;
              break;
            }
          }

          if (hit) {
            el.style.cursor = 'pointer';
            this.showFloatingHud(hit.movie, { x: hit.x, y: hit.y, z: hit.z });
          } else {
            el.style.cursor = 'grab';
          }
        }
      });

      el.addEventListener('click', (e) => {
        const rect = el.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        for (let i = this.nodes2D.length - 1; i >= 0; i--) {
          const n = this.nodes2D[i];
          const dist = Math.hypot(mx - n.projX, my - n.projY);
          if (dist <= n.radius * n.projScale + 4) {
            if (window.MoodGraphApp && window.MoodGraphApp.openMovieDetailModal) {
              window.MoodGraphApp.openMovieDetailModal(n.movie.movieId);
            }
            break;
          }
        }
      });

      window.addEventListener('resize', () => this.resizeCanvas2D());
    }

    animateCanvas2D() {
      this.animFrameId = requestAnimationFrame(() => this.animateCanvas2D());

      // 0. Tính toán Linear Interpolation (Lerp) cho vị trí Quả cầu User Center
      if (!this.targetPos) {
        this.targetPos = Object.assign({}, this.userCenterPos);
      }
      const dx = this.targetPos.x - this.userCenterPos.x;
      const dy = this.targetPos.y - this.userCenterPos.y;
      const dz = this.targetPos.z - this.userCenterPos.z;
      const distSq = dx * dx + dy * dy + dz * dz;

      if (distSq > (this.lerpEpsilon * this.lerpEpsilon)) {
        this.userCenterPos.x += dx * this.lerpSpeed;
        this.userCenterPos.y += dy * this.lerpSpeed;
        this.userCenterPos.z += dz * this.lerpSpeed;
        this.isTransitioning = true;
      } else {
        this.userCenterPos.x = this.targetPos.x;
        this.userCenterPos.y = this.targetPos.y;
        this.userCenterPos.z = this.targetPos.z;
        this.isTransitioning = false;
      }
      this.currentPos = this.userCenterPos;

      const rect = this.container.getBoundingClientRect();
      const w = rect.width || 800;
      const h = rect.height || 520;
      const ctx = this.ctx2d;

      // Xóa nền màu Dark Charcoal
      ctx.fillStyle = '#0A0D14';
      ctx.fillRect(0, 0, w, h);

      // Tự động xoay nếu được bật
      if (AcademicLabState.autoRotate3D && !this.isDragging2D) {
        this.rotY += 0.0035;
      }

      const cx = w / 2;
      const cy = h / 2;
      const fov = 260;

      // 1. Vẽ sao bụi
      ctx.fillStyle = '#475569';
      this.stars2D.forEach(s => {
        const x1 = s.x * Math.cos(this.rotY) - s.z * Math.sin(this.rotY);
        const z1 = s.x * Math.sin(this.rotY) + s.z * Math.cos(this.rotY);
        const y2 = s.y * Math.cos(this.rotX) - z1 * Math.sin(this.rotX);
        const z2 = s.y * Math.sin(this.rotX) + z1 * Math.cos(this.rotX);

        if (z2 + fov > 10) {
          const scale = fov / (fov + z2);
          const px = cx + x1 * scale;
          const py = cy + y2 * scale;
          ctx.beginPath();
          ctx.arc(px, py, s.size * scale, 0, Math.PI * 2);
          ctx.fill();
        }
      });

      // 2. Chiếu tọa độ vector người dùng trung tâm theo vị trí lerp động
      const userX = this.userCenterPos.x;
      const userY = this.userCenterPos.y;
      const userZ = this.userCenterPos.z;
      const ux1 = userX * Math.cos(this.rotY) - userZ * Math.sin(this.rotY);
      const uz1 = userX * Math.sin(this.rotY) + userZ * Math.cos(this.rotY);
      const uy2 = userY * Math.cos(this.rotX) - uz1 * Math.sin(this.rotX);
      const uz2 = userY * Math.sin(this.rotX) + uz1 * Math.cos(this.rotX);
      const uScale = fov / (fov + uz2);
      const uPx = cx + ux1 * uScale;
      const uPy = cy + uy2 * uScale;

      // 3. Chiếu tọa độ các điểm phim
      this.nodes2D.forEach(n => {
        const x1 = n.x * Math.cos(this.rotY) - n.z * Math.sin(this.rotY);
        const z1 = n.x * Math.sin(this.rotY) + n.z * Math.cos(this.rotY);
        const y2 = n.y * Math.cos(this.rotX) - z1 * Math.sin(this.rotX);
        const z2 = n.y * Math.sin(this.rotX) + z1 * Math.cos(this.rotX);

        const scale = fov / (fov + z2);
        n.projX = cx + x1 * scale;
        n.projY = cy + y2 * scale;
        n.projScale = scale;
        n.depth = z2;
      });

      // Sắp xếp z-index từ xa tới gần
      const sorted = this.nodes2D.slice().sort((a, b) => b.depth - a.depth);

      // 4. Vẽ tia liên kết tới Top-10 Hybrid RRF
      if (AcademicLabState.show3DRays) {
        ctx.strokeStyle = 'rgba(245, 158, 11, 0.32)';
        ctx.lineWidth = 1.2;

        let activeIds = this.activeTop10Ids;
        if (!activeIds || activeIds.size === 0) {
          const defaultTop10 = (window.MOCK_DATA && window.MOCK_DATA.top10ByModel && window.MOCK_DATA.top10ByModel.hybrid_rrf) || [];
          activeIds = new Set(defaultTop10.map(m => m.movieId));
        }

        sorted.forEach(n => {
          if (activeIds.has(n.movie.movieId)) {
            ctx.beginPath();
            ctx.moveTo(uPx, uPy);
            ctx.lineTo(n.projX, n.projY);
            ctx.stroke();
          }
        });
      }

      // 5. Vẽ khối cầu người dùng trung tâm
      const time = performance.now() * 0.001;
      const haloR = (14 + 4 * Math.sin(time * 3.0)) * uScale;

      // Vòng hào quang xung nhịp
      ctx.beginPath();
      ctx.arc(uPx, uPy, haloR, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(251, 191, 36, 0.55)';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Tâm vàng hổ phách
      ctx.beginPath();
      ctx.arc(uPx, uPy, 8 * uScale, 0, Math.PI * 2);
      ctx.fillStyle = '#F59E0B';
      ctx.shadowColor = '#F59E0B';
      ctx.shadowBlur = 16;
      ctx.fill();
      ctx.shadowBlur = 0;

      // 6. Vẽ các điểm phim
      sorted.forEach(n => {
        const r = Math.max(2, n.radius * n.projScale);
        ctx.beginPath();
        ctx.arc(n.projX, n.projY, r, 0, Math.PI * 2);
        ctx.fillStyle = n.color;
        ctx.shadowColor = n.color;
        ctx.shadowBlur = 8;
        ctx.fill();
        ctx.shadowBlur = 0;
      });
    }

    // -----------------------------------------------------------------------
    // 3.3. THẺ NỔI HUD HỌC THUẬT (ACADEMIC FLOATING HUD)
    // -----------------------------------------------------------------------
    showFloatingHud(movie, coords, pinState) {
      if (!this.hudCard || !movie) return;

      const titleEl = document.getElementById('hud-movie-title');
      const metaEl = document.getElementById('hud-movie-meta');
      const coordsEl = document.getElementById('hud-coords');
      const cosineEl = document.getElementById('hud-cosine');
      const explEl = document.getElementById('hud-explanation');

      const movieTitle = movie.vietnameseTitle || movie.cleanTitle || movie.title;
      const year = movie.year ? `(${movie.year})` : '';
      const genre = movie.primaryGenre || (movie.genres && movie.genres[0]) || 'Điện ảnh';
      const director = movie.director || 'Chưa cập nhật';

      if (titleEl) titleEl.textContent = `${movieTitle} ${year}`;
      if (metaEl) metaEl.textContent = `${genre} • Đạo diễn: ${director}`;

      const pos = coords || movie.embedding3d || { x: 0, y: 0, z: 0 };
      if (coordsEl) {
        coordsEl.textContent = `x: ${pos.x.toFixed(1)}, y: ${pos.y.toFixed(1)}, z: ${pos.z.toFixed(1)}`;
      }

      // Tính khoảng cách Cosine và Euclid
      const cosine = calcCosineSimilarity(this.userCenterPos, pos);
      const euclid = calcEuclideanDistance(this.userCenterPos, pos);

      if (cosineEl) {
        const simScore = Math.max(0, Math.min(0.999, (cosine + 1) / 2));
        cosineEl.textContent = `${simScore.toFixed(3)} (Euclid: ${euclid.toFixed(1)})`;
      }

      if (explEl) {
        let targetUserName = 'khán giả được chọn';
        const currentSelectedUser = AcademicLabState && AcademicLabState.selectedUser;
        if (currentSelectedUser === 'live_session') {
          targetUserName = 'phiên làm việc trực tiếp của bạn';
        } else if (currentSelectedUser === 'user1') {
          targetUserName = 'Khán giả 1 (Alex Turner)';
        } else if (currentSelectedUser === 'user2') {
          targetUserName = 'Khán giả 2 (Sarah Jenkins)';
        } else if (currentSelectedUser === 'user3') {
          targetUserName = 'Khán giả 3 (Marcus Vance)';
        } else if (currentSelectedUser === 'user42' || currentSelectedUser === 'user_cold') {
          targetUserName = 'Khán giả mới (Cold-Start)';
        }
        const genreName = getGenreColorInfo(genre).name;
        const explText = (movie.provenanceSummary && movie.provenanceSummary.evidence && movie.provenanceSummary.evidence[0] && movie.provenanceSummary.evidence[0].text) 
          || `Gần cụm sở thích ${genreName} của ${targetUserName} qua phép chiếu nhân tử tiềm ẩn ALS và đồ thị tri thức.`;
        explEl.textContent = explText;
      }

      this.hudCard.classList.remove('hidden');
    }

    handleResize() {
      if (!this.container) return;
      const rect = this.container.getBoundingClientRect();
      const width = rect.width || 800;
      const height = rect.height || 520;

      if (this.camera && this.renderer) {
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
      } else if (this.ctx2d) {
        this.resizeCanvas2D();
      }
    }

    // Cập nhật mượt mà tâm điểm người dùng và các đường tia kết nối khi đổi user
    updateUserCenterForSelectedUser(userKey) {
      let targetPos = { x: 2.3, y: 5.6, z: 1.2 };

      if (userKey === 'user2') {
        targetPos = { x: 38.5, y: -18.2, z: 28.4 };
      } else if (userKey === 'user3') {
        targetPos = { x: -35.2, y: 22.0, z: -26.8 };
      } else if (userKey === 'user42') {
        targetPos = { x: 0.0, y: 0.0, z: 0.0 };
      } else if (userKey === 'live_session') {
        const userRatings = (window.MoodGraphState && window.MoodGraphState.userRatings) || {};
        const ratedIds = Object.keys(userRatings).map(Number);
        if (ratedIds.length > 0) {
          let sX = 0, sY = 0, sZ = 0, sW = 0;
          ratedIds.forEach(mid => {
            const m = getMovieById(mid);
            if (m && m.embedding3d) {
              const w = Number(userRatings[mid]) || 1;
              sX += m.embedding3d.x * w;
              sY += m.embedding3d.y * w;
              sZ += m.embedding3d.z * w;
              sW += w;
            }
          });
          if (sW > 0) {
            targetPos = { x: sX / sW, y: sY / sW, z: sZ / sW };
          }
        } else {
          targetPos = { x: 0.0, y: 0.0, z: 0.0 };
        }
      }

      // Kích hoạt trạng thái chuyển động nội suy tuyến tính (Lerp) mượt mà
      if (!this.userCenterPos) {
        this.userCenterPos = { x: 0, y: 5, z: 0 };
      }
      this.currentPos = this.userCenterPos;
      this.targetPos = Object.assign({}, targetPos);
      this.isTransitioning = true;

      // Lấy danh sách Top-10 phim Hybrid RRF của user mới
      const recs = computeDynamicRecommendationsForLab(userKey);
      const top10 = (recs.top10ByModel && recs.top10ByModel.hybrid_rrf) || [];
      const top10Ids = new Set(top10.map(m => m.movieId));
      this.activeTop10Ids = top10Ids;

      // Cập nhật lại chùm tia sáng (Ray Lines) Three.js kết nối đến Top-10 Hybrid RRF
      if (Array.isArray(this.rayLines)) {
        this.rayLines.forEach(l => {
          if (this.scene) this.scene.remove(l);
          if (l.geometry) l.geometry.dispose();
          if (l.material) l.material.dispose();
        });
        this.rayLines = [];
      }

      // Tái tạo chùm tia mới xuất phát từ vị trí hiện tại của quả cầu
      if (this.movieNodes && this.scene && typeof THREE !== 'undefined') {
        const startPos = (this.userOrb && this.userOrb.position) 
          ? this.userOrb.position 
          : new THREE.Vector3(this.userCenterPos.x, this.userCenterPos.y, this.userCenterPos.z);

        this.movieNodes.forEach(mesh => {
          const mid = mesh.userData.movie.movieId;
          if (top10Ids.has(mid)) {
            const points = [
              new THREE.Vector3(startPos.x, startPos.y, startPos.z),
              mesh.position
            ];
            const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
            if (lineGeo.attributes && lineGeo.attributes.position && lineGeo.attributes.position.setUsage) {
              lineGeo.attributes.position.setUsage(THREE.DynamicDrawUsage);
            }
            const lineMat = new THREE.LineBasicMaterial({
              color: 0xF59E0B,
              transparent: true,
              opacity: 0.45,
              linewidth: 1
            });
            const line = new THREE.Line(lineGeo, lineMat);
            line.visible = AcademicLabState.show3DRays;
            this.scene.add(line);
            this.rayLines.push(line);
          }
        });
      }

      // Canvas 2D Fallback tự động vẽ lại trong vòng lặp animateCanvas2D
      // dựa trên this.activeTop10Ids và vị trí lerp của userCenterPos
    }

    resetCamera() {
      if (this.camera && this.controls) {
        this.camera.position.set(0, 40, 185);
        this.controls.target.set(0, 5, 0);
        this.controls.update();
      } else {
        this.rotX = 0.2;
        this.rotY = 0.0;
      }
    }

    toggleRays() {
      AcademicLabState.show3DRays = !AcademicLabState.show3DRays;
      this.rayLines.forEach(l => {
        l.visible = AcademicLabState.show3DRays;
      });
      return AcademicLabState.show3DRays;
    }

    toggleRotation() {
      AcademicLabState.autoRotate3D = !AcademicLabState.autoRotate3D;
      if (this.controls) {
        this.controls.autoRotate = AcademicLabState.autoRotate3D;
      }
      return AcademicLabState.autoRotate3D;
    }
  }

  // Khởi tạo visualizer toàn cục
  let visualizer3D = null;

  // =========================================================================
  // 3.0 CÔNG CỤ TÍNH TOÁN VÀ DỮ LIỆU TOP-10 CHUẨN HỌC THUẬT (ORTHOGONAL TOP-10 ENGINE)
  // Tuân thủ 100% công thức Cormack et al. (SIGIR 2009) & Trực giao RecSys (40% - 60%)
  // 100% ID phim thuộc 53 phim trong CATALOG, triệt tiêu phim ma và bảo toàn tính toàn vẹn 3D
  // =========================================================================

  function formatMovieItem(movieId, rank, score, rawScoreText, fallbackGenre) {
    const catalog = (window.MOCK_DATA && window.MOCK_DATA.catalog) || [];
    const m = getMovieById(movieId) || catalog.find(c => c.movieId === movieId);
    const title = m ? (m.vietnameseTitle || m.cleanTitle || m.title) : ('Phim #' + movieId);
    const cleanTitle = m ? (m.cleanTitle || m.title) : title;
    const year = m ? m.year : 2000;
    const genre = m ? (m.primaryGenre || (m.genres && m.genres[0]) || fallbackGenre) : fallbackGenre;
    return {
      id: movieId,
      movieId: movieId,
      rank: rank,
      title: title,
      cleanTitle: cleanTitle,
      year: year,
      score: typeof score === 'number' ? Number(score.toFixed(4)) : score,
      rawScoreText: rawScoreText || (typeof score === 'number' ? score.toFixed(4) : String(score)),
      primaryGenre: genre,
      genre: genre,
      consensusCount: 1,
      movie: m || { movieId: movieId, title: title, primaryGenre: genre, year: year }
    };
  }

  // Thuật toán Reciprocal Rank Fusion chuẩn Cormack et al. (SIGIR 2009):
  // RRF(d) = sum_{m in M} 1 / (60 + r_m(d))
  // Nếu d không xuất hiện trong top của mô hình m, điểm đóng góp từ m bằng 0 (không dùng rank giả định 45 hay 50)
  function computeCormackRRF(topALS, topKG) {
    const rankMapALS = {};
    (topALS || []).forEach((it, idx) => { rankMapALS[it.movieId] = idx + 1; });
    const rankMapKG = {};
    (topKG || []).forEach((it, idx) => { rankMapKG[it.movieId] = idx + 1; });

    const allIds = Array.from(new Set([
      ...(topALS || []).map(it => it.movieId),
      ...(topKG || []).map(it => it.movieId)
    ]));

    const scored = allIds.map(mid => {
      const r1 = rankMapALS[mid];
      const r2 = rankMapKG[mid];
      let score = 0;
      if (r1 && r1 <= 10) score += (1.0 / (60 + r1));
      if (r2 && r2 <= 10) score += (1.0 / (60 + r2));

      const ref = (topALS || []).find(it => it.movieId === mid) || (topKG || []).find(it => it.movieId === mid);
      return {
        movieId: mid,
        score: score,
        fallbackGenre: ref ? (ref.primaryGenre || ref.genre) : 'Điện ảnh'
      };
    });

    // Sắp xếp giảm dần theo điểm RRF
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, 10).map((it, idx) => {
      return formatMovieItem(it.movieId, idx + 1, Number(it.score.toFixed(4)), it.score.toFixed(4), it.fallbackGenre);
    });
  }

  // Thuật toán Hybrid Weighted tuyến tính dựa trên thứ hạng chuẩn hóa
  function computeWeightedFusion(topA, topB, weightA = 0.55, weightB = 0.45) {
    const rankMapA = {};
    (topA || []).forEach((it, idx) => { rankMapA[it.movieId] = idx + 1; });
    const rankMapB = {};
    (topB || []).forEach((it, idx) => { rankMapB[it.movieId] = idx + 1; });

    const allIds = Array.from(new Set([
      ...(topA || []).map(it => it.movieId),
      ...(topB || []).map(it => it.movieId)
    ]));

    const scored = allIds.map(mid => {
      const r1 = rankMapA[mid];
      const r2 = rankMapB[mid];
      const norm1 = (r1 && r1 <= 10) ? (11 - r1) / 10 : 0;
      const norm2 = (r2 && r2 <= 10) ? (11 - r2) / 10 : 0;
      const score = (weightA * norm1) + (weightB * norm2);

      const ref = (topA || []).find(it => it.movieId === mid) || (topB || []).find(it => it.movieId === mid);
      return {
        movieId: mid,
        score: score,
        fallbackGenre: ref ? (ref.primaryGenre || ref.genre) : 'Điện ảnh'
      };
    });

    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, 10).map((it, idx) => {
      return formatMovieItem(it.movieId, idx + 1, Number(it.score.toFixed(4)), it.score.toFixed(4), it.fallbackGenre);
    });
  }

  // Tính toán đồng thuận (Consensus count) qua các cột mô hình
  function applyConsensusBadges(top10ByModel) {
    const countMap = {};
    Object.values(top10ByModel).forEach(list => {
      if (Array.isArray(list)) {
        list.forEach(it => {
          if (it && it.movieId) {
            countMap[it.movieId] = (countMap[it.movieId] || 0) + 1;
          }
        });
      }
    });
    Object.values(top10ByModel).forEach(list => {
      if (Array.isArray(list)) {
        list.forEach(it => {
          if (it && it.movieId) {
            it.consensusCount = countMap[it.movieId] || 1;
          }
        });
      }
    });
  }

  // Danh mục Phim Phổ Biến Toàn Cục (Popularity Baseline chuẩn M03)
  const GLOBAL_POPULARITY_IDS = [318, 356, 593, 2571, 260, 480, 110, 589, 1, 4993];
  const GLOBAL_POPULARITY_COUNTS = [80448, 80375, 73109, 71787, 68083, 63268, 58266, 57379, 57342, 56400];
  function getGlobalPopularityList() {
    const list = GLOBAL_POPULARITY_IDS.map((mid, idx) => {
      const rawCount = GLOBAL_POPULARITY_COUNTS[idx] || (80000 - idx * 2500);
      const score = Math.max(0.65, Math.min(0.99, rawCount / 80500));
      return {
        movieId: mid,
        score: Number(score.toFixed(4)),
        rawScoreText: rawCount.toLocaleString('en-US'),
        primaryGenre: 'Điện ảnh'
      };
    });
    list.sort((a, b) => Number(b.score) - Number(a.score));
    return list.map((it, idx) => {
      return formatMovieItem(it.movieId, idx + 1, it.score, it.rawScoreText, it.primaryGenre);
    });
  }

  // =========================================================================
  // 3.1 BỘ TÍNH TOÁN GỢI Ý ĐỘNG CHO PHÒNG THÍ NGHIỆM (LIVE LAB RECOMMENDER)
  // Tính toán thời gian thực Top-10 cho cả 5 mô hình dựa trên tương tác thực tế
  // Phân hóa học thuật trực giao giữa ALS và KG: tỷ lệ trùng lặp đạt đúng 40% - 60%
  // =========================================================================
  function computeDynamicRecommendationsForLab(userKey) {
    const catalog = (window.MOCK_DATA && window.MOCK_DATA.catalog) || [];

    // 1. Trường hợp Khán Giả 1 (Alex Turner • Cinephile Auteur Enthusiast)
    // Gu điện ảnh kinh điển nghệ thuật châu Âu, chiều sâu tâm lý cao (Drama/Crime)
    if (userKey === 'user1') {
      const alsIds = [318, 858, 50, 527, 1221, 1193, 912, 904, 111, 1213];
      const alsScores = [4.412, 4.385, 4.298, 4.251, 4.210, 4.180, 4.150, 4.120, 4.095, 4.050];
      const kgIds = [318, 1208, 858, 1217, 1221, 1178, 111, 1237, 904, 4144];
      const kgScores = [0.892, 0.845, 0.820, 0.795, 0.760, 0.740, 0.715, 0.690, 0.670, 0.650];

      const topALS = alsIds.map((mid, idx) => formatMovieItem(mid, idx + 1, alsScores[idx], alsScores[idx].toFixed(4), 'Drama'));
      const topKG = kgIds.map((mid, idx) => formatMovieItem(mid, idx + 1, kgScores[idx], kgScores[idx].toFixed(4), 'Drama'));

      const topRRF = computeCormackRRF(topALS, topKG);
      const topWeighted = computeWeightedFusion(topALS, topKG, 0.55, 0.45);
      const topPop = getGlobalPopularityList();

      const top10Map = {
        als: topALS,
        kg: topKG,
        hybrid_rrf: topRRF,
        hybrid_weighted: topWeighted,
        popularity: topPop
      };
      applyConsensusBadges(top10Map);

      return {
        isColdStart: false,
        userBadge: "Khán giả 1 (Alex Turner • 68 phim Train)",
        top10ByModel: top10Map
      };
    }

    // 2. Trường hợp Khán Giả 42 (Mô phỏng Cold-Start thuần túy 0 đánh giá)
    // Phân hóa rõ rệt: ALS rỗng kích hoạt card; KG onboarding đa dạng; RRF & Weighted dung hợp thông minh
    if (userKey === 'user42') {
      const kgIds = [318, 858, 296, 527, 260, 2571, 593, 1193, 912, 1208];
      const kgScores = [0.930, 0.905, 0.880, 0.855, 0.830, 0.810, 0.785, 0.760, 0.735, 0.710];
      const topKG = kgIds.map((mid, idx) => formatMovieItem(mid, idx + 1, kgScores[idx], kgScores[idx].toFixed(4), 'Điện ảnh'));

      const topPop = getGlobalPopularityList();
      const topRRF = computeCormackRRF(topKG, topPop);
      const topWeighted = computeWeightedFusion(topPop, topKG, 0.60, 0.40);

      const top10Map = {
        als: [],
        kg: topKG,
        hybrid_rrf: topRRF,
        hybrid_weighted: topWeighted,
        popularity: topPop
      };
      applyConsensusBadges(top10Map);

      return {
        isColdStart: true,
        numRatings: 0,
        userBadge: "Khán giả 42 (Cold-Start thuần túy • 0 đánh giá)",
        top10ByModel: top10Map
      };
    }

    // 3. Trường hợp Khán Giả 2 (Elena Rostova - Sci-Fi & Cyberpunk Explorer)
    // Đảm bảo 100% ID phim trong CATALOG, trùng lặp ALS vs KG đạt đúng 6/10 (60%)
    if (userKey === 'user2') {
      const alsIds = [2571, 260, 589, 480, 79132, 109487, 2959, 4993, 7153, 110];
      const alsScores = [4.480, 4.420, 4.385, 4.350, 4.310, 4.275, 4.230, 4.190, 4.150, 4.110];
      const kgIds = [109487, 79132, 7361, 2571, 260, 589, 1219, 593, 1258, 4993];
      const kgScores = [0.925, 0.905, 0.880, 0.855, 0.830, 0.810, 0.785, 0.760, 0.735, 0.710];

      const topALS = alsIds.map((mid, idx) => formatMovieItem(mid, idx + 1, alsScores[idx], alsScores[idx].toFixed(4), 'Sci-Fi'));
      const topKG = kgIds.map((mid, idx) => formatMovieItem(mid, idx + 1, kgScores[idx], kgScores[idx].toFixed(4), 'Sci-Fi'));

      const topRRF = computeCormackRRF(topALS, topKG);
      const topWeighted = computeWeightedFusion(topALS, topKG, 0.55, 0.45);
      const topPop = getGlobalPopularityList();

      const top10Map = {
        als: topALS,
        kg: topKG,
        hybrid_rrf: topRRF,
        hybrid_weighted: topWeighted,
        popularity: topPop
      };
      applyConsensusBadges(top10Map);

      return {
        isColdStart: false,
        userBadge: "Khán giả 2 (Elena Rostova • 142 phim Train)",
        top10ByModel: top10Map
      };
    }

    // 4. Trường hợp Khán Giả 3 (Marcus Vance - Classic Crime & Noir Aficionado)
    // Đảm bảo 100% ID phim trong CATALOG, trùng lặp ALS vs KG đạt đúng 5/10 (50%)
    if (userKey === 'user3') {
      const alsIds = [858, 1221, 296, 1213, 50, 111, 47, 6016, 318, 593];
      const alsScores = [4.450, 4.410, 4.370, 4.335, 4.290, 4.250, 4.210, 4.170, 4.130, 4.090];
      const kgIds = [913, 1212, 858, 1221, 111, 1213, 904, 50, 1258, 1219];
      const kgScores = [0.930, 0.910, 0.885, 0.860, 0.835, 0.810, 0.785, 0.760, 0.735, 0.710];

      const topALS = alsIds.map((mid, idx) => formatMovieItem(mid, idx + 1, alsScores[idx], alsScores[idx].toFixed(4), 'Crime'));
      const topKG = kgIds.map((mid, idx) => formatMovieItem(mid, idx + 1, kgScores[idx], kgScores[idx].toFixed(4), 'Crime'));

      const topRRF = computeCormackRRF(topALS, topKG);
      const topWeighted = computeWeightedFusion(topALS, topKG, 0.55, 0.45);
      const topPop = getGlobalPopularityList();

      const top10Map = {
        als: topALS,
        kg: topKG,
        hybrid_rrf: topRRF,
        hybrid_weighted: topWeighted,
        popularity: topPop
      };
      applyConsensusBadges(top10Map);

      return {
        isColdStart: false,
        userBadge: "Khán giả 3 (Marcus Vance • 89 phim Train)",
        top10ByModel: top10Map
      };
    }

    // 5. TRƯỜNG HỢP CỐT LÕI: LIVE SESSION (TÀI KHOẢN TRỰC TIẾP CỦA BẠN)
    const userRatings = (window.MoodGraphState && window.MoodGraphState.userRatings) || {};
    const ratedMovieIds = Object.keys(userRatings).map(Number);
    const numRatings = ratedMovieIds.length;

    // Nếu người dùng THỰC SỰ chưa có đánh giá nào (numRatings === 0)
    if (numRatings === 0) {
      const kgIds = [318, 858, 296, 527, 260, 2571, 593, 1193, 912, 1208];
      const kgScores = [0.930, 0.905, 0.880, 0.855, 0.830, 0.810, 0.785, 0.760, 0.735, 0.710];
      const topKG = kgIds.map((mid, idx) => formatMovieItem(mid, idx + 1, kgScores[idx], kgScores[idx].toFixed(4), 'Điện ảnh'));

      const topPop = getGlobalPopularityList();
      const topRRF = computeCormackRRF(topKG, topPop);
      const topWeighted = computeWeightedFusion(topPop, topKG, 0.60, 0.40);

      const top10Map = {
        als: [],
        kg: topKG,
        hybrid_rrf: topRRF,
        hybrid_weighted: topWeighted,
        popularity: topPop
      };
      applyConsensusBadges(top10Map);

      return {
        isColdStart: true,
        numRatings: 0,
        ratedMovies: [],
        userBadge: "Khán giả thực tế (Live Session • 0 đánh giá)",
        top10ByModel: top10Map
      };
    }

    // NẾU NGƯỜI DÙNG ĐÃ ĐÁNH GIÁ TỪ 1 PHIM TRỞ LÊN (numRatings >= 1) -> TÍNH TOÁN ĐỘNG CẢ 5 MÔ HÌNH!
    const ratedEntries = ratedMovieIds.map(mid => ({
      movieId: mid,
      score: Number(userRatings[mid]),
      movie: getMovieById(mid)
    })).filter(e => e.movie);

    // Lọc danh sách phim ứng viên (loại trừ các phim đã đánh giá để gợi ý phim mới)
    const candidates = catalog.filter(m => !userRatings[m.movieId]);

    // [Mô hình 1: Spark ALS Collaborative Filtering]
    const alsScored = candidates.map(c => {
      let totalSim = 0;
      let totalWeight = 0;
      ratedEntries.forEach(r => {
        const weight = (r.score - 2.5); // Điểm đánh giá cao tạo sức hút mạnh
        let sim = 0;
        // Liên kết phim tương đồng (Item-Item / Matrix Factorization)
        if (r.movie.similarMovieIds && r.movie.similarMovieIds.includes(c.movieId)) {
          sim += 0.90;
        }
        // Khoảng cách trong không gian nhúng 3D
        if (r.movie.embedding3d && c.embedding3d) {
          const cos3d = calcCosineSimilarity(r.movie.embedding3d, c.embedding3d);
          sim += Math.max(0, cos3d) * 0.45;
        }
        // Gu thẩm mỹ tasteFeatures
        if (r.movie.tasteFeatures && c.tasteFeatures) {
          const tfA = r.movie.tasteFeatures;
          const tfB = c.tasteFeatures;
          const dot = (tfA.depth * tfB.depth) + (tfA.pacing * tfB.pacing) + (tfA.auteur * tfB.auteur) + (tfA.tone * tfB.tone);
          const normA = Math.sqrt(tfA.depth**2 + tfA.pacing**2 + tfA.auteur**2 + tfA.tone**2) || 1;
          const normB = Math.sqrt(tfB.depth**2 + tfB.pacing**2 + tfB.auteur**2 + tfB.tone**2) || 1;
          sim += Math.max(0, dot / (normA * normB)) * 0.35;
        }
        totalSim += weight * sim;
        totalWeight += Math.abs(weight) || 1;
      });

      const predictedScore = Math.min(4.92, Math.max(3.20, 3.90 + (totalSim / (totalWeight || 1)) * 0.95));
      return {
        movieId: c.movieId,
        score: predictedScore,
        rawScoreText: predictedScore.toFixed(4),
        primaryGenre: c.primaryGenre || 'Điện ảnh'
      };
    });
    alsScored.sort((a, b) => b.score - a.score);
    const top10ALS = alsScored.slice(0, 10).map((it, idx) => {
      return formatMovieItem(it.movieId, idx + 1, it.score, it.rawScoreText, it.primaryGenre);
    });

    // [Mô hình 2: Knowledge Graph (KG)]
    const kgScored = candidates.map(c => {
      let kgScore = 0;
      const targetRated = ratedEntries.filter(r => r.score >= 3.0);
      const useEntries = targetRated.length > 0 ? targetRated : ratedEntries;

      useEntries.forEach(r => {
        const w = r.score / 5.0;
        if (r.movie.director && c.director && r.movie.director === c.director) {
          kgScore += 0.45 * w;
        }
        if (r.movie.primaryGenre && c.primaryGenre && r.movie.primaryGenre === c.primaryGenre) {
          kgScore += 0.30 * w;
        }
        const sharedGenres = (r.movie.genres || []).filter(g => (c.genres || []).includes(g)).length;
        kgScore += (sharedGenres * 0.12) * w;
        if (r.movie.primaryMood && c.primaryMood && r.movie.primaryMood === c.primaryMood) {
          kgScore += 0.15 * w;
        }
      });

      const normKg = Math.min(0.975, Math.max(0.620, 0.680 + Math.tanh(kgScore) * 0.280));
      return {
        movieId: c.movieId,
        score: normKg,
        rawScoreText: normKg.toFixed(4),
        primaryGenre: c.primaryGenre || 'Điện ảnh'
      };
    });
    kgScored.sort((a, b) => b.score - a.score);
    const top10KG = kgScored.slice(0, 10).map((it, idx) => {
      return formatMovieItem(it.movieId, idx + 1, it.score, it.rawScoreText, it.primaryGenre);
    });

    // [Mô hình 3: Hybrid RRF (Reciprocal Rank Fusion - Chuẩn Cormack k=60)]
    const top10RRF = computeCormackRRF(top10ALS, top10KG);

    // [Mô hình 4: Hybrid Weighted (0.55 ALS + 0.45 KG)]
    const top10Weighted = computeWeightedFusion(top10ALS, top10KG, 0.55, 0.45);

    // [Mô hình 5: Popularity]
    const popScored = candidates.slice().sort((a, b) => {
      const popA = (a.ratingCount || 1000) * (a.ratingAvg || 4.0);
      const popB = (b.ratingCount || 1000) * (b.ratingAvg || 4.0);
      return popB - popA;
    });
    const top10Pop = popScored.slice(0, 10).map((c, idx) => {
      const rawCount = c.ratingCount || 1000;
      const score = Math.max(0.65, Math.min(0.99, rawCount / 80500));
      return formatMovieItem(c.movieId, idx + 1, Number(score.toFixed(4)), rawCount.toLocaleString('en-US'), c.primaryGenre || 'Điện ảnh');
    });

    const top10Map = {
      als: top10ALS,
      kg: top10KG,
      hybrid_rrf: top10RRF,
      hybrid_weighted: top10Weighted,
      popularity: top10Pop
    };
    applyConsensusBadges(top10Map);

    return {
      isColdStart: false,
      numRatings: numRatings,
      ratedMovies: ratedEntries,
      userBadge: `Khán giả thực tế (Live Session • ${numRatings} đánh giá)`,
      top10ByModel: top10Map
    };
  }

  // =========================================================================
  // 3.2 HÀM TRUY XUẤT TOP-10 CHUẨN GIAO DIỆN HỌC THUẬT (PUBLIC TOP-10 GETTER)
  // Đảm bảo 100% ID nằm trong CATALOG, tỷ lệ trùng lặp ALS vs KG từ 40% - 60%
  // =========================================================================
  function getTop10ForModelAndUser(modelKey, userId) {
    let userKey = 'live_session';
    if (userId === 1 || userId === '1' || userId === 'user1') userKey = 'user1';
    else if (userId === 2 || userId === '2' || userId === 'user2') userKey = 'user2';
    else if (userId === 3 || userId === '3' || userId === 'user3') userKey = 'user3';
    else if (userId === 42 || userId === '42' || userId === 'user42') userKey = 'user42';
    else if (userId === 'live_session' || userId === 'live') userKey = 'live_session';
    else if (typeof userId === 'string' && userId.startsWith('user')) userKey = userId;

    const recsResult = computeDynamicRecommendationsForLab(userKey);
    const top10Map = recsResult.top10ByModel || {};

    const normModel = String(modelKey || '').toLowerCase();
    let modelId = 'hybrid_rrf';
    if (normModel === 'als' || normModel === 'spark_als') modelId = 'als';
    else if (normModel === 'kg' || normModel === 'knowledge_graph') modelId = 'kg';
    else if (normModel === 'hybrid_rrf' || normModel === 'rrf') modelId = 'hybrid_rrf';
    else if (normModel === 'hybrid_weighted' || normModel === 'weighted') modelId = 'hybrid_weighted';
    else if (normModel === 'popularity' || normModel === 'pop') modelId = 'popularity';
    else if (top10Map[modelKey]) modelId = modelKey;

    const list = top10Map[modelId] || [];
    return list.map(item => {
      const movie = getMovieById(item.movieId || item.id);
      return {
        id: item.movieId || item.id,
        movieId: item.movieId || item.id,
        rank: item.rank,
        title: item.title || (movie ? (movie.vietnameseTitle || movie.cleanTitle || movie.title) : ('Phim #' + (item.movieId || item.id))),
        cleanTitle: movie ? movie.cleanTitle : item.cleanTitle,
        year: item.year || (movie ? movie.year : 2000),
        genre: item.primaryGenre || item.genre || (movie ? movie.primaryGenre : 'Điện ảnh'),
        primaryGenre: item.primaryGenre || item.genre || (movie ? movie.primaryGenre : 'Điện ảnh'),
        score: item.score,
        rawScoreText: item.rawScoreText,
        consensusCount: item.consensusCount || 1,
        movie: movie || item.movie
      };
    });
  }

  // =========================================================================
  // 4. BẢNG ĐỐI ĐẦU 5 MÔ HÌNH VỚI HOVER INTERLOCK (HEAD-TO-HEAD COMPARISON)
  // =========================================================================
  function renderHeadToHeadComparison(targetUser) {
    if (targetUser) {
      AcademicLabState.selectedUser = targetUser;
      const selector = document.getElementById('lab-user-selector');
      if (selector && selector.value !== targetUser) {
        selector.value = targetUser;
      }
    }
    const container = document.getElementById('head-to-head-columns');
    if (!container || !window.MOCK_DATA) return;

    const modelsMeta = window.MOCK_DATA.modelsMetadata || {};
    const recsResult = computeDynamicRecommendationsForLab(AcademicLabState.selectedUser);
    const top10ByModel = recsResult.top10ByModel || {};
    const isColdStartUser = Boolean(recsResult.isColdStart);
    const coverageMetrics = (window.MOCK_DATA.longTailData && window.MOCK_DATA.longTailData.coverageMetrics) || [];
    const modelKeys = ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'];

    // Kết xuất Banner trạng thái trực tiếp
    const bannerContainer = document.getElementById('live-session-status-banner');
    if (bannerContainer) {
      if (AcademicLabState.selectedUser === 'live_session') {
        const numR = recsResult.numRatings || 0;
        if (numR > 0) {
          const sampleList = (recsResult.ratedMovies || []).slice(0, 4).map(r => `<span class="px-1.5 py-0.5 rounded bg-black/40 text-[#FDE68A]">${r.movie ? (r.movie.vietnameseTitle || r.movie.cleanTitle || r.movie.title) : ('Phim #' + r.movieId)} (${r.score}★)</span>`).join(' ');
          bannerContainer.innerHTML = `
            <div class="p-3 rounded-xl bg-[rgba(217,119,6,0.12)] border border-[rgba(217,119,6,0.35)] flex flex-wrap items-center justify-between gap-3 text-xs shadow-md">
              <div class="flex flex-wrap items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-[#10B981] animate-pulse"></span>
                <span class="font-bold text-[#FDE68A] uppercase tracking-wide">Phiên Thực Hành Trực Tiếp (Live Session):</span>
                <span class="text-[#CBD5E1]">Đã ghi nhận <strong>${numR}</strong> đánh giá: ${sampleList}</span>
              </div>
              <button onclick="MoodGraphApp.switchMode('modeA')" class="px-3 py-1 rounded-lg bg-[#D97706] hover:bg-[#B45309] text-white text-[11px] font-semibold transition-all cursor-pointer shadow">
                + Đánh Giá Thêm Ở Trang 1
              </button>
            </div>
          `;
        } else {
          bannerContainer.innerHTML = `
            <div class="p-3 rounded-xl bg-[rgba(148,163,184,0.08)] border border-[rgba(148,163,184,0.2)] flex flex-wrap items-center justify-between gap-3 text-xs shadow-sm">
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-[#F59E0B]"></span>
                <span class="font-bold text-white uppercase tracking-wide">Tài Khoản Mới (Cold-Start):</span>
                <span class="text-[#94A3B8]">Bạn chưa chấm điểm phim nào. Mô hình Spark ALS cần ít nhất 1 đánh giá để phân tích vector sở thích.</span>
              </div>
              <button onclick="MoodGraphApp.switchMode('modeA')" class="px-3 py-1 rounded-lg bg-[#D97706] hover:bg-[#B45309] text-white text-[11px] font-semibold transition-all cursor-pointer shadow">
                ← Sang Trang 1 Chấm Điểm Thử Ngay
              </button>
            </div>
          `;
        }
      } else {
        bannerContainer.innerHTML = '';
      }
    }

    // Đếm tần suất xuất hiện của mỗi bộ phim qua 5 mô hình để gắn badge đồng thuận (Consensus)
    const movieCounts = {};
    modelKeys.forEach(mKey => {
      const items = top10ByModel[mKey] || [];
      items.forEach(it => {
        movieCounts[it.movieId] = (movieCounts[it.movieId] || 0) + 1;
      });
    });

    let html = '';

    modelKeys.forEach(mKey => {
      const meta = modelsMeta[mKey] || {
        badgeText: mKey.toUpperCase(),
        name: mKey,
        hexColor: '#D97706',
        executionTimeMs: 3.0,
        noveltyBitsAvg: 8.0,
        longTailRatio: 0.3
      };

      let items = (top10ByModel[mKey] || []).slice();

      // Áp dụng bộ lọc đồng thuận
      if (AcademicLabState.consensusFilter === 'overlap') {
        items = items.filter(it => (movieCounts[it.movieId] || 0) >= 2);
      } else if (AcademicLabState.consensusFilter === 'unique') {
        items = items.filter(it => (movieCounts[it.movieId] || 0) === 1);
      }

      // Thông số chẩn đoán chân cột
      const cov = coverageMetrics.find(c => c.modelId === mKey) || {};
      const avgNovelty = cov.noveltyBitsAvg || meta.noveltyBitsAvg || 0;
      const longTailPct = Math.round((cov.longTailRatio !== undefined ? cov.longTailRatio : (meta.longTailRatio || 0)) * 100);

      let itemsHtml = '';

      // Xử lý kịch bản Cold-Start cho Spark ALS
      if (isColdStartUser && mKey === 'als') {
        itemsHtml = `
          <div class="p-4 my-4 rounded-xl bg-[rgba(217,119,6,0.12)] border border-[rgba(217,119,6,0.35)] text-center space-y-2.5 shadow-lg">
            <span class="text-[#FDE68A] font-mono text-xs font-bold block flex items-center justify-center gap-1.5">
              <span>ℹ️</span> CHƯA CÓ LỊCH SỬ ĐÁNH GIÁ (COLD-START)
            </span>
            <p class="text-[11px] text-[#CBD5E1] leading-relaxed">
              Mô hình Lọc cộng tác (Spark ALS) cần lịch sử tương tác để học sở thích điện ảnh của bạn.
            </p>
            <p class="text-[10px] text-[#94A3B8] leading-relaxed">
              Vui lòng quay lại <strong class="text-white">Trang 1</strong> để chấm điểm một vài bộ phim yêu thích, hoặc xem các đề xuất từ <strong class="text-[#A7F3D0]">Đồ Thị Tri Thức</strong> và <strong class="text-[#FED7AA]">Phim Phổ Biến</strong> ở các cột bên cạnh.
            </p>
            <button onclick="MoodGraphApp.switchMode('modeA')" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#D97706] hover:bg-[#B45309] text-white text-[11px] font-semibold transition-all shadow cursor-pointer mt-1">
              <span>←</span> Sang Trang 1 Chấm Điểm Phim
            </button>
          </div>
        `;
      } else {
        items.forEach(it => {
          const movie = getMovieById(it.movieId);
          const count = it.consensusCount || movieCounts[it.movieId] || 1;
          const consensusBadge = count >= 2 
            ? `<span class="px-1.5 py-0.2 rounded bg-[rgba(217,119,6,0.2)] text-[#FDE68A] border border-[rgba(217,119,6,0.4)] text-[10px] font-mono font-bold" title="Đồng thuận ${count} mô hình">x${count}</span>` 
            : '';
          const title = movie ? (movie.vietnameseTitle || movie.cleanTitle || movie.title) : it.title;
          const year = movie ? movie.year : '';
          const rawGenre = movie ? movie.primaryGenre : (it.primaryGenre || 'Điện ảnh');
          const genre = getGenreColorInfo(rawGenre).name;

          itemsHtml += `
            <div class="model-item-row group rounded-md" 
                 data-model-id="${mKey}"
                 data-interlock-movie-id="${it.movieId}"
                 onmouseenter="MoodGraphApp.setInterlock(${it.movieId})"
                 onmouseleave="MoodGraphApp.clearInterlock()"
                 onclick="MoodGraphApp.openMovieDetailModal(${it.movieId})">
              
              <!-- Bên trái: Thứ hạng & Tiêu đề -->
              <div class="flex items-center gap-2 min-w-0">
                <span class="movie-rank-badge w-5 h-5 rounded flex items-center justify-center text-xs font-mono font-bold shrink-0 bg-[#1B2230] text-[#94A3B8]">
                  ${it.rank}
                </span>
                <div class="min-w-0">
                  <div class="text-xs font-semibold text-white truncate max-w-[130px] sm:max-w-[140px] group-hover:text-[#F59E0B] transition-colors">
                    ${title}
                  </div>
                  <div class="text-[10px] text-[#64748B] flex items-center gap-1">
                    <span>${year}</span>
                    <span>•</span>
                    <span class="truncate">${genre}</span>
                  </div>
                </div>
              </div>

              <!-- Bên phải: Điểm thô & Huy hiệu đồng thuận -->
              <div class="text-right shrink-0">
                <div class="font-mono text-xs font-bold text-[#E2E8F0] tabular-nums">
                  ${it.rawScoreText || (typeof it.score === 'number' ? it.score.toFixed(3) : it.score)}
                </div>
                <div class="mt-0.5">${consensusBadge}</div>
              </div>

            </div>
          `;
        });
      }

      html += `
        <div class="head-to-head-column justify-between">
          <div>
            <!-- Đầu Cột -->
            <div class="model-column-header">
              <div class="flex items-center justify-between">
                <span class="text-[10px] font-mono font-bold uppercase tracking-wider text-[#F59E0B]">
                  ${meta.badgeText || mKey.toUpperCase()}
                </span>
                <span class="text-[10px] font-mono text-[#94A3B8]">
                  ${meta.executionTimeMs} ms
                </span>
              </div>
              <h3 class="text-xs font-bold text-white mt-0.5 truncate">${meta.name}</h3>
            </div>

            <!-- Danh Sách Phim -->
            <div class="p-1.5 space-y-1">
              ${itemsHtml || '<div class="text-xs text-[#64748B] py-8 text-center italic">Không có phim thỏa bộ lọc</div>'}
            </div>
          </div>

          <!-- Chân Cột Chẩn Đoán -->
          <div class="p-3 border-t border-[rgba(255,255,255,0.06)] text-[11px] font-mono text-[#94A3B8] space-y-1 bg-[#0F141C]">
            <div class="flex items-center justify-between">
              <span>Độ mới lạ:</span>
              <span class="text-white font-bold">${avgNovelty} bits</span>
            </div>
            <div class="flex items-center justify-between">
              <span>Tỷ lệ đuôi dài:</span>
              <span class="${longTailPct >= 40 ? 'text-[#10B981]' : 'text-[#E2E8F0]'} font-bold">${longTailPct}%</span>
            </div>
          </div>

        </div>
      `;
    });

    container.innerHTML = html;
  }

  // Cơ chế Hover Interlock
  function setInterlock(movieId) {
    AcademicLabState.activeInterlockMovieId = Number(movieId);
    const mid = AcademicLabState.activeInterlockMovieId;

    const cards = document.querySelectorAll('[data-interlock-movie-id]');
    const matchedModels = [];

    cards.forEach(card => {
      const cardMid = Number(card.getAttribute('data-interlock-movie-id'));
      if (cardMid === mid) {
        card.classList.add('interlock-highlighted');
        card.style.opacity = '1.0';

        const modelId = card.getAttribute('data-model-id') || '';
        const rankEl = card.querySelector('.movie-rank-badge');
        const rank = rankEl ? rankEl.textContent.trim() : '';
        matchedModels.push(`${modelId.toUpperCase()} (#${rank})`);
      } else {
        card.classList.remove('interlock-highlighted');
        card.style.opacity = '0.35';
      }
    });

    // Cập nhật biểu ngữ đồng thuận
    const banner = document.getElementById('interlock-status-banner');
    const textEl = document.getElementById('interlock-status-text');
    const movie = getMovieById(mid);
    const title = movie ? (movie.vietnameseTitle || movie.cleanTitle || movie.title) : `Phim #${mid}`;

    if (banner && textEl) {
      textEl.textContent = `Đồng thuận ${matchedModels.length}/5 mô hình cho "${title}": ${matchedModels.join(' • ')}`;
      banner.classList.remove('hidden');
    }
  }

  function clearInterlock() {
    AcademicLabState.activeInterlockMovieId = null;

    document.querySelectorAll('[data-interlock-movie-id]').forEach(card => {
      card.classList.remove('interlock-highlighted');
      card.style.opacity = '1.0';
    });

    const banner = document.getElementById('interlock-status-banner');
    if (banner) banner.classList.add('hidden');
  }

  // =========================================================================
  // 5. MA TRẬN NHIỆT TƯƠNG QUAN THỨ HẠNG & TƯƠNG ĐỒNG (5X5 HEATMAP)
  // =========================================================================
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
      hybrid_weighted: 'Hybrid Weighted',
      popularity: 'Popularity'
    };

    // Cập nhật Chú giải Màu Động
    if (legend) {
      if (AcademicLabState.heatmapMetric === 'spearman') {
        legend.innerHTML = `
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded bg-[rgba(16,185,129,0.7)] inline-block"></span> Đồng điệu (+0.6..1.0)</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded bg-[rgba(2,132,199,0.7)] inline-block"></span> Vừa (+0.2..0.6)</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded bg-[#141A24] inline-block border border-white/10"></span> k &lt; 2 (null)</span>
        `;
      } else {
        legend.innerHTML = `
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded bg-[rgba(217,119,6,0.7)] inline-block"></span> Trùng cao (&ge; 60%)</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded bg-[rgba(217,119,6,0.35)] inline-block"></span> Trùng vừa (15..59%)</span>
          <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded bg-[#141A24] inline-block border border-white/10"></span> Trực giao (0%)</span>
        `;
      }
    }

    let gridHtml = '<div class="heatmap-table-grid">';

    // Dòng Tiêu Đề Cột Trên Cùng
    gridHtml += '<div class="heatmap-cell text-[11px] font-bold text-[#64748B] bg-[#0B0F14]">Mô Hình</div>';
    models.forEach(m => {
      gridHtml += `<div class="heatmap-cell text-[11px] font-bold text-white text-center font-mono bg-[#141A24]">${modelLabels[m]}</div>`;
    });

    // Các Hàng Ma Trận
    models.forEach((rowModel, r) => {
      // Tiêu đề đầu hàng
      gridHtml += `<div class="heatmap-cell text-[11px] font-bold text-[#E2E8F0] font-mono text-left px-2 justify-center items-start bg-[#141A24]">${modelLabels[rowModel]}</div>`;

      models.forEach((colModel, c) => {
        const isDiagonal = r === c;
        const commonK = (matrix.commonCounts && matrix.commonCounts[r] && matrix.commonCounts[r][c] !== undefined)
          ? matrix.commonCounts[r][c]
          : (isDiagonal ? 10 : 0);

        if (isDiagonal) {
          gridHtml += `
            <div class="heatmap-cell bg-[rgba(217,119,6,0.2)] border border-[rgba(217,119,6,0.4)]" onclick="MoodGraphApp.openMatrixOverlapModal('${rowModel}', '${colModel}')" title="Tự tương quan hoàn hảo">
              <span class="text-xs font-mono font-bold text-[#FDE68A] tabular-nums">1.0000</span>
              <span class="text-[9px] text-[#94A3B8] font-mono">10/10 phim</span>
            </div>
          `;
          return;
        }

        if (AcademicLabState.heatmapMetric === 'spearman') {
          const rho = matrix.spearman && matrix.spearman[r] ? matrix.spearman[r][c] : null;

          // Tuân thủ triệt để quy chuẩn liêm chính toán học: k < 2 => null
          if (rho === null || commonK < 2) {
            gridHtml += `
              <div class="heatmap-cell null-cell" onclick="MoodGraphApp.openMatrixOverlapModal('${rowModel}', '${colModel}')" title="Số phim chung k < 2 không đủ cơ sở thống kê tính Spearman">
                <span class="text-xs font-mono font-bold tabular-nums text-[#64748B]">null</span>
                <span class="text-[9px] font-mono opacity-60">k=${commonK} phim</span>
              </div>
            `;
          } else {
            const valText = (rho >= 0 ? '+' : '') + Number(rho).toFixed(4);
            let bgStyle = 'background-color: rgba(2, 132, 199, 0.25); color: #BAE6FD;';
            if (rho >= 0.6) {
              bgStyle = 'background-color: rgba(16, 185, 129, 0.25); color: #A7F3D0;';
            }

            gridHtml += `
              <div class="heatmap-cell" style="${bgStyle}" onclick="MoodGraphApp.openMatrixOverlapModal('${rowModel}', '${colModel}')" title="Hệ số Spearman: ${valText}">
                <span class="text-xs font-mono font-bold tabular-nums">${valText}</span>
                <span class="text-[9px] font-mono opacity-80">${commonK} phim chung</span>
              </div>
            `;
          }
        } else {
          // Chỉ số trùng lặp Jaccard
          const jaccard = matrix.jaccard && matrix.jaccard[r] ? matrix.jaccard[r][c] : 0;
          const pct = Math.round(jaccard * 100);
          let bgStyle = 'background-color: #141A24; color: #64748B;';

          if (jaccard >= 0.6) {
            bgStyle = 'background-color: rgba(217, 119, 6, 0.35); color: #FDE68A;';
          } else if (jaccard > 0.05) {
            bgStyle = 'background-color: rgba(217, 119, 6, 0.15); color: #FED7AA;';
          }

          gridHtml += `
            <div class="heatmap-cell" style="${bgStyle}" onclick="MoodGraphApp.openMatrixOverlapModal('${rowModel}', '${colModel}')" title="Jaccard: ${Number(jaccard).toFixed(3)}">
              <span class="text-xs font-mono font-bold tabular-nums">${Number(jaccard).toFixed(3)} (${pct}%)</span>
              <span class="text-[9px] font-mono opacity-80">${commonK} phim chung</span>
            </div>
          `;
        }

      });
    });

    gridHtml += '</div>';
    container.innerHTML = gridHtml;
  }

  // Mở Modal Phân Tích Giao Thoa Giữa 2 Mô Hình
  function openMatrixOverlapModal(modelA, modelB) {
    const modal = document.getElementById('matrix-overlap-modal') || document.getElementById('heatmap-cell-modal');
    const content = document.getElementById('matrix-overlap-content') || document.getElementById('heatmap-cell-modal-body');
    if (!modal || !content || !window.MOCK_DATA) return;

    const overlaps = window.MOCK_DATA.pairwiseOverlaps || [];
    const top10ByModel = window.MOCK_DATA.top10ByModel || {};
    const modelsMeta = window.MOCK_DATA.modelsMetadata || {};

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

    const nameA = modelsMeta[modelA] ? modelsMeta[modelA].name : modelA.toUpperCase();
    const nameB = modelsMeta[modelB] ? modelsMeta[modelB].name : modelB.toUpperCase();

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
              <span class="px-2 py-0.5 rounded bg-[#1B2230] text-[#BAE6FD] border border-[rgba(2,132,199,0.35)]">${modelA.toUpperCase()} #${rankA}</span>
              ${!isSelf ? `<span class="text-[#64748B]">↔</span><span class="px-2 py-0.5 rounded bg-[#1B2230] text-[#FDE68A] border border-[rgba(217,119,6,0.35)]">${modelB.toUpperCase()} #${rankB}</span>` : ''}
            </div>
          </div>
        `;
      });
    } else {
      moviesHtml = `
        <div class="p-5 rounded-lg bg-[#0F141C] border border-[rgba(255,255,255,0.06)] text-xs text-[#94A3B8] italic text-center leading-relaxed">
          Hai mô hình này hoàn toàn trực giao (k = 0 phim chung). Hệ số Spearman không xác định (null). Điều này phản ánh sự phân ly rõ rệt giữa cơ chế đại chúng và hệ thống cá nhân hóa chuyên sâu.
        </div>
      `;
    }

    content.innerHTML = `
      <div class="space-y-4">
        <div class="border-b border-[rgba(255,255,255,0.08)] pb-3">
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-mono uppercase tracking-wider text-[#F59E0B] font-bold">ĐỐI THOẠI HỌC THUẬT SONG PHƯƠNG</span>
            <button onclick="MoodGraphApp.closeMatrixOverlapModal()" class="text-[#94A3B8] hover:text-white p-1 rounded">✕</button>
          </div>
          <h3 class="text-base font-bold text-white mt-1 font-serif">
            ${nameA} ${!isSelf ? '↔ ' + nameB : '(Tự tương quan)'}
          </h3>
          <div class="flex items-center gap-4 text-xs text-[#94A3B8] mt-1.5 font-mono">
            <span>Số phim chung: <strong class="text-[#F59E0B]">${commonMovieIds.length} / 10</strong></span>
            <span>Jaccard: <strong class="text-white">${pair ? (pair.jaccard * 100).toFixed(1) : (isSelf ? '100.0' : '0.0')}%</strong></span>
            <span>Spearman ρ: <strong class="text-white">${pair && pair.spearman !== null ? pair.spearman.toFixed(4) : (isSelf ? '1.0000' : 'null')}</strong></span>
          </div>
          ${pair && pair.scientificNote ? `<p class="text-xs text-[#CBD5E1] mt-2 italic bg-[rgba(217,119,6,0.1)] p-2 rounded border border-[rgba(217,119,6,0.25)]">${pair.scientificNote}</p>` : ''}
        </div>

        <div class="space-y-2">
          <div class="text-xs font-semibold text-white">Danh sách phim trùng lặp & thứ bậc đối chiếu:</div>
          <div class="space-y-1.5 max-h-60 overflow-y-auto pr-1">
            ${moviesHtml}
          </div>
        </div>
      </div>
    `;

    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }

  function closeMatrixOverlapModal() {
    const modal = document.getElementById('matrix-overlap-modal') || document.getElementById('heatmap-cell-modal');
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
  }

  // =========================================================================
  // 6. BẢNG CHỈ SỐ KIỂM CHUẨN OFFLINE (OFFLINE BENCHMARKS TABLE)
  // =========================================================================
  function renderOfflineBenchmarks() {
    const tbody = document.getElementById('offline-benchmarks-tbody');
    if (!tbody || !window.MOCK_DATA || !window.MOCK_DATA.offlineBenchmarks) return;

    const b = window.MOCK_DATA.offlineBenchmarks;
    const metrics = b.metrics || [];

    let rowsHtml = '';
    metrics.forEach(row => {
      const bestModel = row.best || 'KG';
      rowsHtml += `
        <tr class="hover:bg-[rgba(255,255,255,0.03)] transition-colors">
          <td class="py-2.5 px-3 font-semibold text-white">
            <div>${row.name}</div>
            <div class="text-[10px] text-[#64748B] font-mono">${row.metric}</div>
          </td>
          <td class="py-2.5 px-3 text-[#BAE6FD] tabular-nums">${row.als}</td>
          <td class="py-2.5 px-3 text-[#A7F3D0] tabular-nums font-semibold">${row.kg}</td>
          <td class="py-2.5 px-3 text-[#FDE68A] tabular-nums font-semibold">${row.rrf}</td>
          <td class="py-2.5 px-3 text-[#FED7AA] tabular-nums">${row.weighted}</td>
          <td class="py-2.5 px-3 text-[#D6D3D1] tabular-nums">${row.pop}</td>
          <td class="py-2.5 px-3 text-right">
            <span class="px-2 py-0.5 rounded bg-[rgba(16,185,129,0.15)] text-[#A7F3D0] border border-[rgba(16,185,129,0.35)] font-bold text-[11px]">
              ${bestModel}
            </span>
          </td>
        </tr>
      `;
    });

    tbody.innerHTML = rowsHtml;
  }

  // =========================================================================
  // 7. MÔ PHỎNG THÁCH THỨC COLD-START & LONG-TAIL PARETO
  // =========================================================================
  function renderColdStartDiagnostics() {
    const container = document.getElementById('cold-start-chart-container');
    if (!container || !window.MOCK_DATA || !window.MOCK_DATA.coldStartData) return;

    const cs = window.MOCK_DATA.coldStartData;
    const points = cs.sparsityDegradation || (cs.scenarios && cs.scenarios[1] ? cs.scenarios[1].curvePoints : []) || [];

    let barsHtml = '';
    points.forEach(p => {
      const kgWidth = Math.round((p.kgNdcg / 0.082) * 100);
      const alsWidth = Math.round((p.alsNdcg / 0.082) * 100);
      const rrfWidth = Math.round((p.rrfNdcg / 0.082) * 100);

      barsHtml += `
        <div class="space-y-1 border-b border-[rgba(255,255,255,0.04)] pb-2">
          <div class="flex items-center justify-between text-[11px]">
            <span class="text-white font-semibold">N = ${p.ratingsCount} lượt đánh giá</span>
            <div class="flex items-center gap-3 font-mono text-[10px]">
              <span class="text-[#A7F3D0]">KG: ${p.kgNdcg.toFixed(3)}</span>
              <span class="text-[#FDE68A]">RRF: ${p.rrfNdcg.toFixed(3)}</span>
              <span class="${p.alsNdcg === 0 ? 'text-[#FDA4AF] font-bold' : 'text-[#BAE6FD]'}">ALS: ${p.alsNdcg.toFixed(3)}</span>
            </div>
          </div>
          
          <!-- Thanh so sánh 3 đường cong -->
          <div class="space-y-1">
            <div class="w-full h-1.5 rounded bg-[#141A24] overflow-hidden flex" title="Knowledge Graph">
              <div class="h-full bg-[#10B981] rounded" style="width: ${Math.max(2, kgWidth)}%;"></div>
            </div>
            <div class="w-full h-1.5 rounded bg-[#141A24] overflow-hidden flex" title="Hybrid RRF">
              <div class="h-full bg-[#D97706] rounded" style="width: ${Math.max(2, rrfWidth)}%;"></div>
            </div>
            <div class="w-full h-1.5 rounded bg-[#141A24] overflow-hidden flex" title="Spark ALS">
              <div class="h-full ${p.alsNdcg === 0 ? 'bg-[#E11D48]' : 'bg-[#0284C7]'} rounded" style="width: ${Math.max(0, alsWidth)}%;"></div>
            </div>
          </div>
        </div>
      `;
    });

    container.innerHTML = barsHtml;
  }

  function renderLongTailDiagnostics() {
    const container = document.getElementById('long-tail-chart-container');
    if (!container || !window.MOCK_DATA || !window.MOCK_DATA.longTailData) return;

    const lt = window.MOCK_DATA.longTailData;
    const metrics = lt.coverageMetrics || [];

    let barsHtml = '';
    metrics.forEach(m => {
      const headPct = Math.round(m.shortHeadRatio * 100);
      const tailPct = Math.round(m.longTailRatio * 100);

      barsHtml += `
        <div class="space-y-1.5 border-b border-[rgba(255,255,255,0.04)] pb-2.5">
          <div class="flex items-center justify-between text-[11px]">
            <span class="text-white font-semibold">${m.modelName}</span>
            <div class="flex items-center gap-2 font-mono text-[10px]">
              <span class="text-[#E2E8F0]">${m.coverageAt10} phim (@10)</span>
              <span class="text-[#94A3B8]">•</span>
              <span class="text-[#F59E0B]">${m.noveltyBitsAvg} bits</span>
              <span class="text-[#94A3B8]">•</span>
              <span class="text-[#10B981]">Gini: ${m.giniIndex}</span>
            </div>
          </div>

          <!-- Phân bổ Short-head vs Long-tail -->
          <div class="w-full h-2.5 rounded bg-[#141A24] overflow-hidden flex text-[9px] font-bold">
            <div class="h-full bg-[#334155] text-[#CBD5E1] flex items-center justify-center" style="width: ${headPct}%;" title="Phim đại chúng (Short-head): ${headPct}%">
              ${headPct >= 20 ? headPct + '%' : ''}
            </div>
            <div class="h-full bg-[#10B981] text-[#0A0D14] flex items-center justify-center font-bold" style="width: ${tailPct}%;" title="Phim ngách (Long-tail): ${tailPct}%">
              ${tailPct >= 20 ? tailPct + '%' : ''}
            </div>
          </div>
        </div>
      `;
    });

    container.innerHTML = barsHtml;
  }

  // =========================================================================
  // 8. TÍCH HỢP HỆ THỐNG VÀO WINDOW.MOODGRAPHAPP
  // =========================================================================

  // =========================================================================
  // 9. CÁC TÍNH NĂNG MỞ RỘNG TỪ BỐ CỤC WIREFRAME (FILMSTRIP, BAR CHART, KG)
  // =========================================================================

  const WIREFRAME_ALGORITHMS = [
    { id: 'popularity',      name: 'Popularity Baseline', shortName: 'Popularity' },
    { id: 'als',             name: 'Spark ALS',           shortName: 'Spark ALS' },
    { id: 'kg',              name: 'Knowledge Graph',     shortName: 'Knowledge Graph' },
    { id: 'hybrid_rrf',      name: 'Hybrid RRF (k=60)',   shortName: 'Hybrid RRF' },
    { id: 'hybrid_weighted', name: 'Hybrid Weighted',     shortName: 'Hybrid Weighted' }
  ];

  let currentSelectedAlgorithm = 'kg';
  let currentTargetMovieId = 101;

  const WIREFRAME_BENCHMARKS = [
    { id: 'popularity',      name: 'Popularity',      recall: 0.12, ndcg: 0.18, coverage: 0.22 },
    { id: 'als',             name: 'Spark ALS',       recall: 0.46, ndcg: 0.51, coverage: 0.38 },
    { id: 'kg',              name: 'Knowledge Graph', recall: 0.43, ndcg: 0.48, coverage: 0.86 },
    { id: 'hybrid_rrf',      name: 'Hybrid RRF',      recall: 0.54, ndcg: 0.61, coverage: 0.78 },
    { id: 'hybrid_weighted', name: 'Hybrid Weighted', recall: 0.52, ndcg: 0.58, coverage: 0.74 }
  ];

  const USER_BENCHMARKS_MAP = {
    user1: [ // Alex Turner - Gu Nghệ Thuật & Auteur
      { id: 'popularity',      name: 'Popularity',      recall: 0.12, ndcg: 0.18, coverage: 0.22 },
      { id: 'als',             name: 'Spark ALS',       recall: 0.46, ndcg: 0.51, coverage: 0.38 },
      { id: 'kg',              name: 'Knowledge Graph', recall: 0.43, ndcg: 0.48, coverage: 0.86 },
      { id: 'hybrid_rrf',      name: 'Hybrid RRF',      recall: 0.54, ndcg: 0.61, coverage: 0.78 },
      { id: 'hybrid_weighted', name: 'Hybrid Weighted', recall: 0.52, ndcg: 0.58, coverage: 0.74 }
    ],
    user2: [ // Elena Rostova - Gu Sci-Fi / Logic
      { id: 'popularity',      name: 'Popularity',      recall: 0.14, ndcg: 0.20, coverage: 0.24 },
      { id: 'als',             name: 'Spark ALS',       recall: 0.49, ndcg: 0.54, coverage: 0.40 },
      { id: 'kg',              name: 'Knowledge Graph', recall: 0.45, ndcg: 0.50, coverage: 0.84 },
      { id: 'hybrid_rrf',      name: 'Hybrid RRF',      recall: 0.57, ndcg: 0.63, coverage: 0.81 },
      { id: 'hybrid_weighted', name: 'Hybrid Weighted', recall: 0.55, ndcg: 0.61, coverage: 0.78 }
    ],
    user3: [ // Marcus Vance - Gu Hành Động / Đại chúng
      { id: 'popularity',      name: 'Popularity',      recall: 0.26, ndcg: 0.32, coverage: 0.30 },
      { id: 'als',             name: 'Spark ALS',       recall: 0.47, ndcg: 0.52, coverage: 0.36 },
      { id: 'kg',              name: 'Knowledge Graph', recall: 0.39, ndcg: 0.44, coverage: 0.82 },
      { id: 'hybrid_rrf',      name: 'Hybrid RRF',      recall: 0.52, ndcg: 0.59, coverage: 0.75 },
      { id: 'hybrid_weighted', name: 'Hybrid Weighted', recall: 0.50, ndcg: 0.57, coverage: 0.72 }
    ],
    user42: [ // Cold-Start - Thiếu tương tác (ALS suy giảm, KG & Hybrid cứu cánh)
      { id: 'popularity',      name: 'Popularity',      recall: 0.30, ndcg: 0.38, coverage: 0.25 },
      { id: 'als',             name: 'Spark ALS',       recall: 0.00, ndcg: 0.00, coverage: 0.02 },
      { id: 'kg',              name: 'Knowledge Graph', recall: 0.38, ndcg: 0.44, coverage: 0.88 },
      { id: 'hybrid_rrf',      name: 'Hybrid RRF',      recall: 0.40, ndcg: 0.46, coverage: 0.85 },
      { id: 'hybrid_weighted', name: 'Hybrid Weighted', recall: 0.39, ndcg: 0.45, coverage: 0.84 }
    ],
    live_session: [ // Tài khoản trực tiếp
      { id: 'popularity',      name: 'Popularity',      recall: 0.15, ndcg: 0.22, coverage: 0.23 },
      { id: 'als',             name: 'Spark ALS',       recall: 0.42, ndcg: 0.48, coverage: 0.38 },
      { id: 'kg',              name: 'Knowledge Graph', recall: 0.42, ndcg: 0.47, coverage: 0.85 },
      { id: 'hybrid_rrf',      name: 'Hybrid RRF',      recall: 0.53, ndcg: 0.60, coverage: 0.79 },
      { id: 'hybrid_weighted', name: 'Hybrid Weighted', recall: 0.51, ndcg: 0.58, coverage: 0.76 }
    ]
  };

  const WIREFRAME_MOVIES_CATALOG = [
    {
      movieId: 101,
      title: 'The Martian',
      cleanTitle: 'The Martian',
      score: 0.85,
      year: 2015,
      genres: ['Sci-Fi', 'Adventure', 'Drama'],
      tags: ['Space', 'Survival', 'Mars'],
      posterUrl: 'https://image.tmdb.org/t/p/w500/5BHuvQ6p9kfc091Z8RiFNhCwL4b.jpg'
    },
    {
      movieId: 102,
      title: 'Avatar',
      cleanTitle: 'Avatar',
      score: 0.79,
      year: 2009,
      genres: ['Action', 'Adventure', 'Sci-Fi'],
      tags: ['Alien', 'Future', 'Space'],
      posterUrl: 'https://image.tmdb.org/t/p/w500/kyeqWdyUXW608qlYkRqosgbbJyK.jpg'
    },
    {
      movieId: 79132,
      title: 'Inception',
      cleanTitle: 'Inception',
      score: 0.76,
      year: 2010,
      genres: ['Action', 'Sci-Fi', 'Thriller'],
      tags: ['Mind-bending', 'Dreams'],
      posterUrl: 'https://image.tmdb.org/t/p/w500/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg'
    },
    {
      movieId: 104,
      title: 'Gravity',
      cleanTitle: 'Gravity',
      score: 0.72,
      year: 2013,
      genres: ['Sci-Fi', 'Drama', 'Thriller'],
      tags: ['Space', 'Survival'],
      posterUrl: 'https://image.tmdb.org/t/p/w500/a2n6bKD7qhCPCAEALgsAhWOAQcc.jpg'
    },
    {
      movieId: 2571,
      title: 'The Matrix',
      cleanTitle: 'The Matrix',
      score: 0.68,
      year: 1999,
      genres: ['Action', 'Sci-Fi'],
      tags: ['Cyberpunk', 'Simulation', 'Virtual Reality'],
      posterUrl: 'https://image.tmdb.org/t/p/w500/dXNAPwY7VrqMAo51EKhhCJfaGb5.jpg'
    },
    {
      movieId: 106,
      title: 'Gladiator',
      cleanTitle: 'Gladiator',
      score: 0.65,
      year: 2000,
      genres: ['Action', 'Adventure', 'Drama'],
      tags: ['Rome', 'Revenge'],
      posterUrl: 'https://image.tmdb.org/t/p/w500/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg'
    },
    {
      movieId: 107,
      title: 'Arrival',
      cleanTitle: 'Arrival',
      score: 0.65,
      year: 2016,
      genres: ['Drama', 'Mystery', 'Sci-Fi'],
      tags: ['Language', 'Alien Contact'],
      posterUrl: 'https://image.tmdb.org/t/p/w500/x2FJsf1ElAgr63Y3PNPtJrcmpoe.jpg'
    },
    {
      movieId: 108,
      title: 'Dune',
      cleanTitle: 'Dune: Part One',
      score: 0.58,
      year: 2021,
      genres: ['Action', 'Adventure', 'Sci-Fi'],
      tags: ['Desert', 'Space'],
      posterUrl: 'https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg'
    },
    {
      movieId: 109,
      title: 'Tenet',
      cleanTitle: 'Tenet',
      score: 0.55,
      year: 2020,
      genres: ['Action', 'Sci-Fi', 'Thriller'],
      tags: ['Time Inversion', 'Physics'],
      posterUrl: 'https://image.tmdb.org/t/p/w500/k68nPLbIST6NP96JmTxmZijEvCA.jpg'
    },
    {
      movieId: 109487,
      title: 'Interstellar',
      cleanTitle: 'Interstellar',
      score: 0.55,
      year: 2014,
      genres: ['Adventure', 'Drama', 'Sci-Fi'],
      tags: ['Space', 'Black Hole', 'Relativity'],
      posterUrl: 'https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg'
    }
  ];

  function renderAlgorithmPills() {
    const container = document.getElementById('algorithm-pills-container');
    if (!container) return;

    let html = '';
    WIREFRAME_ALGORITHMS.forEach(algo => {
      const isActive = algo.id === currentSelectedAlgorithm;
      html += `
        <button type="button" 
                onclick="AcademicLab.selectAlgorithm('${algo.id}')"
                class="px-3 py-1.5 rounded-xl transition-all whitespace-nowrap cursor-pointer border ${
                  isActive 
                    ? 'bg-blue-600 text-white font-semibold border-blue-500 shadow-md shadow-blue-500/25' 
                    : 'bg-white/[0.03] hover:bg-white/[0.08] text-slate-300 hover:text-white border-white/10'
                }">
          <span>${algo.name}</span>
        </button>
      `;
    });
    container.innerHTML = html;
  }

  function updatePerformanceTableHighlight() {
    const table = document.getElementById('pyspark-performance-table');
    if (!table) return;
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(r => {
      r.classList.remove('bg-blue-500/15', 'border-l-2', 'border-l-blue-500');
    });
    const targetRow = document.getElementById(`perf-row-${currentSelectedAlgorithm}`);
    if (targetRow) {
      targetRow.classList.add('bg-blue-500/15', 'border-l-2', 'border-l-blue-500');
    }
  }

  function selectAlgorithm(algoId) {
    currentSelectedAlgorithm = algoId;
    renderAlgorithmPills();
    renderTop10Filmstrip();
    renderEvaluationChart();
    renderKnowledgeGraphDiagram();
    updatePerformanceTableHighlight();

    const algo = WIREFRAME_ALGORITHMS.find(a => a.id === algoId);
    const badge = document.getElementById('active-algorithm-badge');
    if (badge && algo) {
      badge.textContent = `${algo.name}`;
    }
    updateSidebarMeta();
  }

  function renderTop10Filmstrip() {
    const grid = document.getElementById('lab-filmstrip-grid');
    if (!grid) return;

    const recsResult = computeDynamicRecommendationsForLab(AcademicLabState.selectedUser);
    const top10ByModel = recsResult.top10ByModel || {};
    const items = top10ByModel[currentSelectedAlgorithm] || [];

    // Trường hợp Cold-Start (ví dụ: user42 khi chọn Spark ALS)
    if (items.length === 0) {
      grid.innerHTML = `
        <div class="col-span-full py-8 px-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-center space-y-2">
          <div class="inline-flex items-center gap-2 text-amber-400 font-mono text-xs font-bold uppercase tracking-wider">
            <span>⚠️</span> Thách Thức Ma Trận Thưa (Cold-Start - 0 Đánh Giá)
          </div>
          <p class="text-xs text-slate-300 max-w-lg mx-auto">
            Mô hình Lọc cộng tác (Spark ALS) chưa có đủ dữ liệu tương tác từ người dùng này để phân rã ma trận ẩn.
          </p>
          <p class="text-[11px] text-slate-400">
            Hãy chọn <strong>Knowledge Graph</strong>, <strong>Hybrid RRF</strong> hoặc <strong>Popularity Baseline</strong> ở các nút bên trên để xem đề xuất chất lượng cao.
          </p>
        </div>
      `;
      return;
    }

    const movies = items.map((it, idx) => {
      const catalogMovie = getMovieById(it.movieId);
      const title = catalogMovie ? (catalogMovie.vietnameseTitle || catalogMovie.cleanTitle || catalogMovie.title) : it.title;
      const cleanTitle = catalogMovie ? (catalogMovie.cleanTitle || catalogMovie.title) : it.title;
      const score = it.rawScoreText || (typeof it.score === 'number' ? it.score.toFixed(2) : String(it.score));
      const posterUrl = catalogMovie && catalogMovie.poster_path
        ? ('https://image.tmdb.org/t/p/w500' + catalogMovie.poster_path)
        : (catalogMovie && catalogMovie.posterUrl ? catalogMovie.posterUrl : 'https://image.tmdb.org/t/p/w500/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg');
      
      return {
        rank: it.rank || (idx + 1),
        movieId: it.movieId,
        title: title,
        cleanTitle: cleanTitle,
        score: score,
        posterUrl: posterUrl,
        primaryGenre: it.primaryGenre || (catalogMovie ? catalogMovie.primaryGenre : 'Điện ảnh'),
        consensusCount: it.consensusCount || 1,
        genres: catalogMovie ? (catalogMovie.genres || [catalogMovie.primaryGenre]) : [it.primaryGenre || 'Điện ảnh'],
        tags: catalogMovie ? (catalogMovie.tags || [catalogMovie.moodFit || 'Cinema']) : ['Điện ảnh']
      };
    });

    if (!movies.some(m => m.movieId === currentTargetMovieId)) {
      currentTargetMovieId = movies[0].movieId;
    }

    let html = '';
    movies.forEach((movie, idx) => {
      const isSelected = movie.movieId === currentTargetMovieId;

      html += `
        <div onclick="AcademicLab.selectTargetMovie(${movie.movieId})" 
             class="group relative flex flex-col cursor-pointer transition-all duration-200 select-none ${
               isSelected ? 'scale-[1.02]' : 'hover:scale-[1.01]'
             }">
          <div class="relative aspect-[2/3] w-full rounded-lg overflow-hidden bg-slate-900 border transition-all ${
            isSelected 
              ? 'border-amber-400 ring-2 ring-amber-400/80 shadow-lg shadow-amber-500/20' 
              : 'border-white/10 group-hover:border-white/30'
          }">
            <img src="${movie.posterUrl}" 
                 alt="${movie.title}" 
                 loading="lazy"
                 class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                 onerror="this.onerror=null; this.src='https://image.tmdb.org/t/p/w500/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg';">
            
            <div class="absolute top-1 left-1 w-5 h-5 rounded flex items-center justify-center text-[10px] font-mono font-bold ${
              isSelected ? 'bg-amber-400 text-black' : 'bg-black/60 text-slate-300 backdrop-blur-sm'
            }">
              #${movie.rank}
            </div>

            ${isSelected ? `
              <div class="absolute top-1 right-1 px-1.5 py-0.5 rounded bg-amber-500 text-black font-mono font-bold text-[9px] uppercase tracking-wider shadow">
                TARGET
              </div>
            ` : ''}
          </div>

          <div class="text-[11px] font-medium text-slate-200 group-hover:text-amber-300 transition-colors truncate mt-1.5" title="${movie.title}">
            ${movie.cleanTitle || movie.title}
          </div>

          <div class="flex items-center justify-between text-[11px] font-mono mt-0.5">
            <span class="text-slate-400 text-[10px]">Score:</span>
            <span class="font-bold text-amber-400 font-mono">${movie.score}</span>
          </div>
        </div>
      `;
    });

    grid.innerHTML = html;
  }

  function selectTargetMovie(movieId) {
    currentTargetMovieId = movieId;
    renderTop10Filmstrip();
    renderKnowledgeGraphDiagram();
  }

  function renderEvaluationChart() {
    const container = document.getElementById('evaluation-chart-container');
    if (!container) return;

    const benchmarks = USER_BENCHMARKS_MAP[AcademicLabState.selectedUser] || WIREFRAME_BENCHMARKS;

    const svgWidth = 640;
    const svgHeight = 220;
    const padLeft = 40;
    const padRight = 20;
    const padTop = 20;
    const padBottom = 35;

    const chartWidth = svgWidth - padLeft - padRight;
    const chartHeight = svgHeight - padTop - padBottom;

    const numGroups = benchmarks.length;
    const groupWidth = chartWidth / numGroups;
    const barWidth = 16;
    const barGap = 4;

    let gridLines = '';
    const yTicks = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0];
    yTicks.forEach(tick => {
      const y = padTop + chartHeight - (tick * chartHeight);
      gridLines += `
        <line x1="${padLeft}" y1="${y}" x2="${svgWidth - padRight}" y2="${y}" stroke="rgba(255,255,255,0.08)" stroke-dasharray="3,3" />
        <text x="${padLeft - 8}" y="${y + 4}" fill="#64748B" font-size="10" font-family="monospace" text-anchor="end">${tick.toFixed(1)}</text>
      `;
    });

    let barsSvg = '';
    benchmarks.forEach((item, idx) => {
      const isSelectedAlgo = item.id === currentSelectedAlgorithm;
      const groupCenterX = padLeft + (idx * groupWidth) + (groupWidth / 2);
      const startX = groupCenterX - ((3 * barWidth + 2 * barGap) / 2);

      const hRecall = item.recall * chartHeight;
      const yRecall = padTop + chartHeight - hRecall;
      const xRecall = startX;

      const hNdcg = item.ndcg * chartHeight;
      const yNdcg = padTop + chartHeight - hNdcg;
      const xNdcg = startX + barWidth + barGap;

      const hCoverage = item.coverage * chartHeight;
      const yCoverage = padTop + chartHeight - hCoverage;
      const xCoverage = startX + 2 * (barWidth + barGap);

      // Nếu là thuật toán đang chọn, vẽ viền highlight nhẹ
      const highlightRect = isSelectedAlgo ? `
        <rect x="${startX - 6}" y="${padTop}" width="${3 * barWidth + 2 * barGap + 12}" height="${chartHeight + 2}" rx="6" fill="rgba(59, 130, 246, 0.08)" stroke="rgba(59, 130, 246, 0.45)" stroke-width="1.5" stroke-dasharray="3,2" />
      ` : '';

      barsSvg += `
        <g class="chart-bar-group cursor-pointer" onclick="AcademicLab.selectAlgorithm('${item.id}')">
          ${highlightRect}
          <rect x="${xRecall}" y="${yRecall}" width="${barWidth}" height="${hRecall}" rx="3" fill="#3B82F6" class="hover:opacity-80 transition-opacity">
            <title>${item.name} — Recall@10: ${(item.recall * 100).toFixed(1)}%</title>
          </rect>
          <rect x="${xNdcg}" y="${yNdcg}" width="${barWidth}" height="${hNdcg}" rx="3" fill="#F59E0B" class="hover:opacity-80 transition-opacity">
            <title>${item.name} — NDCG@10: ${(item.ndcg * 100).toFixed(1)}%</title>
          </rect>
          <rect x="${xCoverage}" y="${yCoverage}" width="${barWidth}" height="${hCoverage}" rx="3" fill="#10B981" class="hover:opacity-80 transition-opacity">
            <title>${item.name} — Coverage: ${(item.coverage * 100).toFixed(1)}%</title>
          </rect>
          <text x="${groupCenterX}" y="${svgHeight - 12}" fill="${isSelectedAlgo ? '#FDE68A' : '#94A3B8'}" font-size="${isSelectedAlgo ? '11' : '10.5'}" font-family="monospace" text-anchor="middle" font-weight="${isSelectedAlgo ? 'bold' : '500'}">
            ${item.name}
          </text>
        </g>
      `;
    });

    container.innerHTML = `
      <svg viewBox="0 0 ${svgWidth} ${svgHeight}" class="w-full h-full overflow-visible select-none">
        ${gridLines}
        ${barsSvg}
      </svg>
    `;

    // Cập nhật câu kết luận thực nghiệm tương ứng với đoàn hệ
    const conclusionEl = document.getElementById('evaluation-conclusion-box');
    if (conclusionEl) {
      if (AcademicLabState.selectedUser === 'user42') {
        conclusionEl.innerHTML = `<span class="text-rose-400 font-semibold">Thách thức Cold-Start (Khán giả 42):</span> Do chưa có lịch sử tương tác, mô hình ma trận Spark ALS bị suy giảm hoàn toàn (NDCG: 0.00). Ngược lại, Knowledge Graph và Hybrid RRF đóng vai trò cứu cánh với độ bao phủ đạt 88%, loại bỏ điểm mù đề xuất.`;
      } else {
        const alsItem = benchmarks.find(b => b.id === 'als') || { ndcg: 0.51 };
        const kgItem = benchmarks.find(b => b.id === 'kg') || { coverage: 0.86 };
        const rrfItem = benchmarks.find(b => b.id === 'hybrid_rrf') || { ndcg: 0.61, coverage: 0.78 };
        conclusionEl.innerHTML = `<span class="text-amber-400 font-semibold">Kết luận thực nghiệm 5 mô hình:</span> Spark ALS đạt độ chính xác cao trên tương tác thưa (NDCG@10: ${alsItem.ndcg.toFixed(2)}), trong khi Knowledge Graph vượt trội về độ bao phủ danh mục (Coverage: ${(kgItem.coverage * 100).toFixed(0)}%). Mô hình Hybrid RRF kết hợp sức mạnh cả hai đạt trạng thái cân bằng Pareto tối ưu (NDCG@10: ${rrfItem.ndcg.toFixed(2)}, Coverage: ${(rrfItem.coverage * 100).toFixed(0)}%).`;
      }
    }
  }

  function renderKnowledgeGraphDiagram() {
    const container = document.getElementById('kg-explanation-diagram');
    const badge = document.getElementById('kg-target-movie-badge');
    const textBox = document.getElementById('kg-explanation-text-box');
    if (!container) return;

    const catalogMovie = getMovieById(currentTargetMovieId);
    const wireframeFallback = WIREFRAME_MOVIES_CATALOG.find(m => m.movieId === currentTargetMovieId) || WIREFRAME_MOVIES_CATALOG[0];
    const targetMovie = catalogMovie || wireframeFallback;
    
    // Tìm nhãn user đang chọn
    let userDisplay = 'Khán giả 1 (Alex)';
    let likedMovie = 'Interstellar (2014)';
    if (AcademicLabState.selectedUser === 'user2') {
      userDisplay = 'Khán giả 2 (Elena)';
      likedMovie = 'The Matrix (1999)';
    } else if (AcademicLabState.selectedUser === 'user3') {
      userDisplay = 'Khán giả 3 (Marcus)';
      likedMovie = 'The Godfather (1972)';
    } else if (AcademicLabState.selectedUser === 'user42') {
      userDisplay = 'Khán giả 42 (Cold-Start)';
      likedMovie = 'Inception (2010)';
    } else if (AcademicLabState.selectedUser === 'live_session') {
      userDisplay = 'Tài khoản của bạn';
      likedMovie = 'The Shawshank Redemption (1994)';
    }

    const movieTitle = targetMovie.cleanTitle || targetMovie.title || 'Movie';
    if (badge) {
      badge.textContent = `Target: ${movieTitle}`;
    }

    const mainGenre = (targetMovie.genres && targetMovie.genres[0]) || targetMovie.primaryGenre || 'Sci-Fi';
    const mainTag = (targetMovie.tags && targetMovie.tags[0]) || (targetMovie.moodFit) || 'Space';
    
    // Tìm điểm số tương đồng tương ứng
    let simScore = '0.85';
    const recsResult = computeDynamicRecommendationsForLab(AcademicLabState.selectedUser);
    const top10 = (recsResult.top10ByModel && recsResult.top10ByModel[currentSelectedAlgorithm]) || [];
    const found = top10.find(it => it.movieId === targetMovie.movieId);
    if (found) {
      simScore = found.rawScoreText || (typeof found.score === 'number' ? found.score.toFixed(2) : String(found.score));
    } else if (targetMovie.score) {
      simScore = typeof targetMovie.score === 'number' ? targetMovie.score.toFixed(2) : String(targetMovie.score);
    }

    container.innerHTML = `
      <svg viewBox="0 0 620 220" class="w-full h-full select-none overflow-visible">
        <defs>
          <marker id="arrow-purple" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#A855F7" />
          </marker>
          <marker id="arrow-cyan" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#06B6D4" />
          </marker>
          <marker id="arrow-emerald" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#10B981" />
          </marker>
          <marker id="arrow-amber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#F59E0B" />
          </marker>
        </defs>

        <!-- Nối User -> Liked Movie -->
        <line x1="85" y1="110" x2="165" y2="110" stroke="#A855F7" stroke-width="2" stroke-dasharray="4,2" marker-end="url(#arrow-purple)" />
        <text x="125" y="102" fill="#C084FC" font-size="10" font-family="monospace" text-anchor="middle" font-weight="600">liked</text>

        <!-- Nối Liked Movie -> Nodes trung gian -->
        <path d="M 235 90 C 270 90, 275 55, 315 55" fill="none" stroke="#06B6D4" stroke-width="1.8" marker-end="url(#arrow-cyan)" />
        <text x="275" y="65" fill="#22D3EE" font-size="9.5" font-family="monospace" text-anchor="middle">has genre</text>

        <line x1="235" y1="110" x2="315" y2="110" stroke="#10B981" stroke-width="1.8" marker-end="url(#arrow-emerald)" />
        <text x="275" y="104" fill="#34D399" font-size="9.5" font-family="monospace" text-anchor="middle">has tag</text>

        <path d="M 235 130 C 270 130, 275 165, 315 165" fill="none" stroke="#F59E0B" stroke-width="1.8" marker-end="url(#arrow-amber)" />
        <text x="275" y="160" fill="#FBBF24" font-size="9.5" font-family="monospace" text-anchor="middle">similar to</text>

        <!-- Nối Nodes trung gian -> Phim đích -->
        <path d="M 395 55 C 435 55, 440 90, 475 90" fill="none" stroke="#06B6D4" stroke-width="1.8" marker-end="url(#arrow-cyan)" />
        <text x="435" y="65" fill="#22D3EE" font-size="9.5" font-family="monospace" text-anchor="middle">has genre</text>

        <line x1="395" y1="110" x2="475" y2="110" stroke="#10B981" stroke-width="1.8" marker-end="url(#arrow-emerald)" />
        <text x="435" y="104" fill="#34D399" font-size="9.5" font-family="monospace" text-anchor="middle">has tag</text>

        <path d="M 395 165 C 435 165, 440 130, 475 130" fill="none" stroke="#F59E0B" stroke-width="1.8" marker-end="url(#arrow-amber)" />
        <text x="435" y="160" fill="#FBBF24" font-size="9.5" font-family="monospace" text-anchor="middle">sim: ${simScore}</text>

        <!-- Nodes -->
        <g transform="translate(25, 80)">
          <rect width="60" height="60" rx="14" fill="#581C87" stroke="#A855F7" stroke-width="2" />
          <text x="30" y="28" font-size="16" text-anchor="middle">👤</text>
          <text x="30" y="47" fill="#F3E8FF" font-size="8.5" font-family="monospace" font-weight="bold" text-anchor="middle">${userDisplay.split(' ')[0]}</text>
        </g>

        <g transform="translate(170, 75)">
          <rect width="65" height="70" rx="10" fill="#0B132B" stroke="#38BDF8" stroke-width="1.5" />
          <text x="32" y="24" font-size="14" text-anchor="middle">🎬</text>
          <text x="32" y="43" fill="#E0F2FE" font-size="8" font-family="sans-serif" font-weight="bold" text-anchor="middle">${likedMovie.split(' ')[0]}</text>
          <text x="32" y="58" fill="#38BDF8" font-size="8" font-family="monospace" text-anchor="middle">Favorite</text>
        </g>

        <g transform="translate(320, 35)">
          <rect width="75" height="40" rx="8" fill="#083344" stroke="#06B6D4" stroke-width="1.5" />
          <text x="37" y="24" fill="#CFFAFE" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">${mainGenre}</text>
        </g>

        <g transform="translate(320, 90)">
          <rect width="75" height="40" rx="8" fill="#064E3B" stroke="#10B981" stroke-width="1.5" />
          <text x="37" y="24" fill="#D1FAE5" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">${mainTag}</text>
        </g>

        <g transform="translate(320, 145)">
          <rect width="75" height="40" rx="8" fill="#451A03" stroke="#F59E0B" stroke-width="1.5" />
          <text x="37" y="24" fill="#FEF3C7" font-size="9.5" font-family="monospace" font-weight="bold" text-anchor="middle">Cosine Sim</text>
        </g>

        <g transform="translate(480, 75)">
          <rect width="90" height="70" rx="12" fill="#78350F" stroke="#F59E0B" stroke-width="2.5" class="animate-pulse" />
          <text x="45" y="24" font-size="14" text-anchor="middle">🚀</text>
          <text x="45" y="43" fill="#FFFBEB" font-size="9" font-family="sans-serif" font-weight="bold" text-anchor="middle">${movieTitle.length > 12 ? movieTitle.substring(0, 11) + '…' : movieTitle}</text>
          <text x="45" y="58" fill="#FDE68A" font-size="8.5" font-family="monospace" font-weight="bold" text-anchor="middle">Score: ${simScore}</text>
        </g>
      </svg>
    `;

    if (textBox) {
      textBox.innerHTML = `
        <span class="text-amber-400 font-semibold">Knowledge Path:</span> ${userDisplay} đã thích 
        <span class="text-sky-300 font-bold">${likedMovie}</span> (${mainGenre}, ${mainTag}), chia sẻ thuộc tính đạo diễn/thể loại và liên kết ngữ nghĩa chặt chẽ với bộ phim được đề xuất 
        <span class="text-amber-300 font-bold">${movieTitle}</span> (Độ tương đồng: ${simScore}).
      `;
    }
  }

  function updateSidebarMeta() {
    const userLabel = document.getElementById('side-meta-user');
    const algoLabel = document.getElementById('side-meta-algo');

    let uName = 'Khán giả 1';
    if (AcademicLabState.selectedUser === 'user2') uName = 'Khán giả 2';
    else if (AcademicLabState.selectedUser === 'user3') uName = 'Khán giả 3';
    else if (AcademicLabState.selectedUser === 'user42') uName = 'Khán giả 42';
    else if (AcademicLabState.selectedUser === 'live_session') uName = 'Tài khoản của bạn';

    const algo = WIREFRAME_ALGORITHMS.find(a => a.id === currentSelectedAlgorithm);

    if (userLabel) userLabel.textContent = uName;
    if (algoLabel && algo) algoLabel.textContent = algo.name;
  }

  function initAcademicLab() {
    // Khởi tạo các khối mở rộng từ wireframe
    renderAlgorithmPills();
    renderTop10Filmstrip();
    renderEvaluationChart();
    renderKnowledgeGraphDiagram();
    updatePerformanceTableHighlight();
    updateSidebarMeta();

    // 1. Khởi tạo Không gian 3D
    if (!visualizer3D) {
      visualizer3D = new LatentSpace3DVisualizer();
      visualizer3D.init();
    } else {
      visualizer3D.handleResize();
    }

    // 2. Render các thành phần học thuật
    renderHeadToHeadComparison();
    renderTop10Filmstrip();
    renderEvaluationChart();
    renderKnowledgeGraphDiagram();
    updatePerformanceTableHighlight();
    updateSidebarMeta();
    renderCorrelationHeatmap();
    renderOfflineBenchmarks();
    renderColdStartDiagnostics();
    renderLongTailDiagnostics();
  }

  // Mở rộng các phương thức tương tác cho window.MoodGraphApp
  window.MoodGraphApp = window.MoodGraphApp || {};

  // Điều khiển Camera 3D
  window.MoodGraphApp.reset3DCamera = function () {
    if (visualizer3D) visualizer3D.resetCamera();
  };

  window.MoodGraphApp.toggle3DRays = function () {
    if (visualizer3D) visualizer3D.toggleRays();
  };

  window.MoodGraphApp.toggle3DRotation = function () {
    if (visualizer3D) visualizer3D.toggleRotation();
  };

  // Hover Interlock
  window.MoodGraphApp.setInterlock = function (movieId) {
    setInterlock(movieId);
  };

  window.MoodGraphApp.clearInterlock = function () {
    clearInterlock();
  };

  // Đổi người dùng kiểm chuẩn
  window.MoodGraphApp.changeLabUser = function (userKey, silent) {
    AcademicLabState.selectedUser = userKey;
    const selector = document.getElementById('lab-user-selector');
    if (selector && selector.value !== userKey) {
      selector.value = userKey;
    }
    const selector6 = document.getElementById('block6-user-selector');
    if (selector6 && selector6.value !== userKey) {
      selector6.value = userKey;
    }

    // Đồng bộ lên Header Selector
    const headerSel = document.getElementById('header-persona-selector');
    if (headerSel && headerSel.value !== userKey) {
      headerSel.value = userKey;
    }
    const avatarSpan = document.getElementById('header-user-avatar');
    if (avatarSpan) {
      let letter = 'A';
      if (userKey === 'user2') letter = 'S';
      else if (userKey === 'user3') letter = 'M';
      else if (userKey === 'user42' || userKey === 'user_cold') letter = '4';
      else if (userKey === 'live_session') letter = '🎬';
      avatarSpan.textContent = letter;
    }

    // Cập nhật nhãn option live nếu có
    const optLive = document.getElementById('opt-lab-live');
    const numR = (window.MoodGraphState && window.MoodGraphState.userRatings) ? Object.keys(window.MoodGraphState.userRatings).length : 0;
    if (optLive) {
      optLive.textContent = `🎬 Tài khoản của bạn (Live Session • ${numR} đánh giá)`;
    }
    const optLive6 = document.getElementById('opt-block6-live');
    if (optLive6) {
      optLive6.textContent = `🎬 Tài khoản của bạn (Live Session • ${numR} đánh giá)`;
    }
    const optLiveH = document.getElementById('opt-header-live');
    if (optLiveH) {
      optLiveH.textContent = `🎬 Tài khoản của bạn (${numR} đánh giá)`;
    }

    renderHeadToHeadComparison();
    renderTop10Filmstrip();
    renderEvaluationChart();
    renderKnowledgeGraphDiagram();
    updatePerformanceTableHighlight();
    updateSidebarMeta();

    // Cập nhật tọa độ tâm trong 3D Scene
    if (visualizer3D && typeof visualizer3D.updateUserCenterForSelectedUser === 'function') {
      visualizer3D.updateUserCenterForSelectedUser(userKey);
    }

    // Đồng bộ sang Mode A Persona nếu khác
    if (window.MoodGraphState && window.MoodGraphState.activePersonaId !== userKey) {
      if (typeof window.MoodGraphApp.switchPersona === 'function') {
        window.MoodGraphApp.switchPersona(userKey, true);
      }
    }

    if (!silent && window.MoodGraphApp.showToast) {
      const userObj = window.MOCK_DATA.testUsers ? window.MOCK_DATA.testUsers.find(u => 'user' + u.userId === userKey) : null;
      const name = userKey === 'live_session' ? `Tài khoản trực tiếp (${numR} đánh giá)` : (userObj ? userObj.name : userKey.toUpperCase());
      window.MoodGraphApp.showToast("Đã Đồng Bộ Người Dùng", `Đang phân tích gợi ý cho: ${name}.`, 'info');
    }
  };

  // Callback khi người dùng đánh giá phim ở Trang 1
  function onUserRatingsChanged() {
    const optLive = document.getElementById('opt-lab-live');
    const numR = (window.MoodGraphState && window.MoodGraphState.userRatings) ? Object.keys(window.MoodGraphState.userRatings).length : 0;
    if (optLive) {
      optLive.textContent = `🎬 Tài khoản của bạn (Live Session • ${numR} đánh giá)`;
    }
    if (AcademicLabState.selectedUser === 'live_session') {
      renderHeadToHeadComparison();
      if (visualizer3D && typeof visualizer3D.updateUserCenterForSelectedUser === 'function') {
        visualizer3D.updateUserCenterForSelectedUser('live_session');
      }
    }
  }

  // Lọc đồng thuận
  window.MoodGraphApp.setConsensusFilter = function (filterType) {
    AcademicLabState.consensusFilter = filterType;

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
  };

  // Chuyển đổi chỉ số ma trận Spearman / Jaccard
  window.MoodGraphApp.toggleHeatmapMetric = function (metricType) {
    AcademicLabState.heatmapMetric = metricType;

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
  };

  // Mở/Đóng Modal giao thoa ma trận
  window.MoodGraphApp.openMatrixOverlapModal = openMatrixOverlapModal;
  window.MoodGraphApp.openHeatmapCellModal = openMatrixOverlapModal;
  window.MoodGraphApp.closeMatrixOverlapModal = closeMatrixOverlapModal;
  window.MoodGraphApp.closeHeatmapCellModal = closeMatrixOverlapModal;

  // Mở rộng switchMode để tự động nạp Trang 2 khi chuyển tab
  const originalSwitchMode = window.MoodGraphApp.switchMode;
  window.MoodGraphApp.switchMode = function (targetMode) {
    if (typeof originalSwitchMode === 'function') {
      originalSwitchMode(targetMode);
    }

    if (targetMode === 'modeB') {
      requestAnimationFrame(() => {
        initAcademicLab();
        if (visualizer3D) {
          visualizer3D.handleResize();
        }
      });
    }
  };

  // Tự động kích hoạt khi DOM sẵn sàng
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      // Nếu Trang 2 đang hiển thị sẵn thì khởi tạo ngay
      const modeBContainer = document.getElementById('mode-b-container');
      if (modeBContainer && !modeBContainer.classList.contains('hidden')) {
        initAcademicLab();
      }
    });
  } else {
    const modeBContainer = document.getElementById('mode-b-container');
    if (modeBContainer && !modeBContainer.classList.contains('hidden')) {
      initAcademicLab();
    }
  }

  // Công khai đối tượng AcademicLab phục vụ kiểm thử và giám sát
  window.AcademicLab = {
    state: AcademicLabState,
    get visualizer() { return visualizer3D; },
    init: initAcademicLab,
    onUserRatingsChanged: onUserRatingsChanged,
    computeDynamicRecommendationsForLab: computeDynamicRecommendationsForLab,
    getTop10ForModelAndUser: getTop10ForModelAndUser,
    renderHeadToHeadComparison,
    renderCorrelationHeatmap,
    renderOfflineBenchmarks,
    renderColdStartDiagnostics,
    renderLongTailDiagnostics,
    selectAlgorithm: selectAlgorithm,
    selectTargetMovie: selectTargetMovie,
    renderGroupedBarChart: renderEvaluationChart,
    renderKnowledgeGraphDiagram: renderKnowledgeGraphDiagram,
    renderTop10Filmstrip: renderTop10Filmstrip,

    getGenreColorInfo,
    calcCosineSimilarity,
    calcEuclideanDistance
  };

  // Công khai hàm truy xuất Top-10 chuẩn hóa cho toàn cục
  window.getTop10ForModelAndUser = getTop10ForModelAndUser;
  if (window.MoodGraphApp) {
    window.MoodGraphApp.getTop10ForModelAndUser = getTop10ForModelAndUser;
  }

})(window, document);
