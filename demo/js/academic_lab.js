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
    selectedUser: 'user1',
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

      // Dữ liệu vị trí người dùng trung tâm
      this.userCenterPos = { x: 0, y: 5, z: 0 };

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
      // Xóa các đường tia cũ nếu có
      this.rayLines.forEach(l => this.scene.remove(l));
      this.rayLines = [];

      const top10 = (window.MOCK_DATA && window.MOCK_DATA.top10ByModel && window.MOCK_DATA.top10ByModel.hybrid_rrf) || [];
      const top10Ids = new Set(top10.map(m => m.movieId));

      this.movieNodes.forEach(mesh => {
        const mid = mesh.userData.movie.movieId;
        if (top10Ids.has(mid)) {
          const points = [
            new THREE.Vector3(this.userCenterPos.x, this.userCenterPos.y, this.userCenterPos.z),
            mesh.position
          ];
          const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
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

      const time = performance.now() * 0.001;

      // Hiệu ứng thở co giãn hào quang người dùng
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

      // 2. Chiếu tọa độ vector người dùng trung tâm
      const userX = 0, userY = 5, userZ = 0;
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

      // 4. Vẽ tia liên kết tới Top-10
      if (AcademicLabState.show3DRays) {
        ctx.strokeStyle = 'rgba(245, 158, 11, 0.28)';
        ctx.lineWidth = 1;
        const top10 = (window.MOCK_DATA && window.MOCK_DATA.top10ByModel && window.MOCK_DATA.top10ByModel.hybrid_rrf) || [];
        const top10Ids = new Set(top10.map(m => m.movieId));

        sorted.forEach(n => {
          if (top10Ids.has(n.movie.movieId)) {
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
        const explText = (movie.provenanceSummary && movie.provenanceSummary.evidence && movie.provenanceSummary.evidence[0] && movie.provenanceSummary.evidence[0].text) 
          || `Gần cụm sở thích ${genre} của Khán giả 1 qua phép chiếu nhân tử tiềm ẩn ALS và đồ thị tri thức.`;
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
  // 4. BẢNG ĐỐI ĐẦU 5 MÔ HÌNH VỚI HOVER INTERLOCK (HEAD-TO-HEAD COMPARISON)
  // =========================================================================
  function renderHeadToHeadComparison() {
    const container = document.getElementById('head-to-head-columns');
    if (!container || !window.MOCK_DATA || !window.MOCK_DATA.top10ByModel) return;

    const modelsMeta = window.MOCK_DATA.modelsMetadata || {};
    const top10ByModel = window.MOCK_DATA.top10ByModel;
    const coverageMetrics = (window.MOCK_DATA.longTailData && window.MOCK_DATA.longTailData.coverageMetrics) || [];
    const modelKeys = ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'];

    // Đếm tần suất xuất hiện của mỗi bộ phim qua 5 mô hình để gắn badge đồng thuận (Consensus)
    const movieCounts = {};
    modelKeys.forEach(mKey => {
      const items = top10ByModel[mKey] || [];
      items.forEach(it => {
        movieCounts[it.movieId] = (movieCounts[it.movieId] || 0) + 1;
      });
    });

    let html = '';
    const isColdStartUser = AcademicLabState.selectedUser === 'user42';

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
          const genre = movie ? movie.primaryGenre : (it.primaryGenre || 'Điện ảnh');

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
  function initAcademicLab() {
    // 1. Khởi tạo Không gian 3D
    if (!visualizer3D) {
      visualizer3D = new LatentSpace3DVisualizer();
      visualizer3D.init();
    }

    // 2. Render các thành phần học thuật
    renderHeadToHeadComparison();
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
  window.MoodGraphApp.changeLabUser = function (userKey) {
    AcademicLabState.selectedUser = userKey;
    renderHeadToHeadComparison();
    if (window.MoodGraphApp.showToast) {
      const userObj = window.MOCK_DATA.testUsers ? window.MOCK_DATA.testUsers.find(u => 'user' + u.userId === userKey) : null;
      const name = userObj ? userObj.name : userKey.toUpperCase();
      window.MoodGraphApp.showToast("Đã Chuyển Tập Người Dùng", `Đã nạp đoàn hệ kiểm chuẩn: ${name}.`, 'info');
    }
  };

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
    visualizer: visualizer3D,
    init: initAcademicLab,
    renderHeadToHeadComparison,
    renderCorrelationHeatmap,
    renderOfflineBenchmarks,
    renderColdStartDiagnostics,
    renderLongTailDiagnostics,
    getGenreColorInfo,
    calcCosineSimilarity,
    calcEuclideanDistance
  };

})(window, document);
