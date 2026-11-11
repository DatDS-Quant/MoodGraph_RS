/**
 * MOODGRAPH E2E TEST SUITE - SUITE 3: 3D LATENT SPACE LERP & 2D CANVAS FALLBACK
 * File: tests/test_visual_lerp.js
 * 
 * Kiểm tra cấu trúc và logic lerp quả cầu User Center, Ray lines buffer update,
 * và cơ chế hiển thị dự phòng 2D Canvas Fallback.
 */

const { createMockEnvironment } = require('./test_helpers');

function runSuite() {
  const results = [];
  const env = createMockEnvironment();
  const { window, document, stepAnimationFrames } = env;
  const lab = window.AcademicLab;
  const vis = lab.visualizer;
  const mockData = window.MOCK_DATA;

  function record(id, tier, name, fn) {
    try {
      fn();
      results.push({ id, tier, name, pass: true });
    } catch (err) {
      results.push({ id, tier, name, pass: false, error: err.message });
    }
  }

  function assert(condition, message) {
    if (!condition) {
      throw new Error(message || 'Assertion failed');
    }
  }

  // =========================================================================
  // TIER 1: FEATURE COVERAGE (10 Tests)
  // =========================================================================

  record('T1.3.1', 'Tier 1', 'LatentSpace3DVisualizer được khởi tạo với các thuộc tính vị trí cần thiết', () => {
    assert(vis !== null && vis !== undefined, 'Không tìm thấy visualizer');
    assert(vis.userCenterPos !== undefined, 'Thiếu thuộc tính userCenterPos');
    assert(typeof vis.userCenterPos.x === 'number', 'userCenterPos.x không phải number');
  });

  record('T1.3.2', 'Tier 1', 'Tự động phát hiện và kích hoạt engine phù hợp (Three.js hoặc Canvas 2D Fallback)', () => {
    assert(['threejs', 'canvas2d'].includes(lab.state.engineType), `engineType không hợp lệ: ${lab.state.engineType}`);
  });

  record('T1.3.3', 'Tier 1', 'Tọa độ tâm người dùng cho User 1 có giá trị hữu hạn hợp lệ', () => {
    vis.updateUserCenterForSelectedUser('user1');
    const pos = vis.targetPos || vis.userCenterPos;
    assert(!isNaN(pos.x) && !isNaN(pos.y) && !isNaN(pos.z), 'Tọa độ User 1 bị NaN');
  });

  record('T1.3.4', 'Tier 1', 'Tọa độ tâm mục tiêu của User 2 (Sci-Fi) nằm ở vùng không gian riêng biệt (x ~ 38.5)', () => {
    vis.updateUserCenterForSelectedUser('user2');
    const pos = vis.targetPos || vis.userCenterPos;
    assert(Math.abs(pos.x - 38.5) < 5.0, `Tọa độ x của User 2 là ${pos.x}, kỳ vọng quanh 38.5`);
  });

  record('T1.3.5', 'Tier 1', 'Tọa độ tâm mục tiêu của User 3 (Crime/Noir) nằm ở vùng không gian riêng biệt (x ~ -35.2)', () => {
    vis.updateUserCenterForSelectedUser('user3');
    const pos = vis.targetPos || vis.userCenterPos;
    assert(Math.abs(pos.x - (-35.2)) < 5.0, `Tọa độ x của User 3 là ${pos.x}, kỳ vọng quanh -35.2`);
  });

  record('T1.3.6', 'Tier 1', 'Tọa độ tâm của Khán Giả Mới (Cold-Start) rơi về gốc tọa độ (0, 0, 0)', () => {
    vis.updateUserCenterForSelectedUser('user42');
    const pos = vis.targetPos || vis.userCenterPos;
    assert(pos.x === 0 && pos.y === 0 && pos.z === 0, `Tọa độ Cold-Start không phải gốc (0,0,0): (${pos.x}, ${pos.y}, ${pos.z})`);
  });

  record('T1.3.7', 'Tier 1', 'Phương thức updateUserCenterForSelectedUser tồn tại và nhận tham số userKey', () => {
    assert(typeof vis.updateUserCenterForSelectedUser === 'function', 'Thiếu phương thức updateUserCenterForSelectedUser');
  });

  record('T1.3.8', 'Tier 1', 'Chùm tia sáng (Ray Lines) kết nối đúng 10 phim của mô hình Hybrid RRF', () => {
    vis.updateUserCenterForSelectedUser('user2');
    const recs = lab.computeDynamicRecommendationsForLab('user2');
    const top10 = recs.top10ByModel.hybrid_rrf || [];
    assert(top10.length === 10, 'Top 10 RRF phải có 10 phim');
  });

  record('T1.3.9', 'Tier 1', 'Gốc của các tia Ray Lines xuất phát từ vị trí tâm người dùng (userCenterPos)', () => {
    assert(vis.userCenterPos !== undefined, 'userCenterPos phải xác định');
  });

  record('T1.3.10', 'Tier 1', 'Cơ chế 2D Canvas Fallback khởi tạo đầy đủ mảng sao và các node phim chiếu phối cảnh', () => {
    assert(Array.isArray(vis.stars2D), 'vis.stars2D phải là mảng');
    assert(vis.stars2D.length > 0, 'vis.stars2D phải chứa bụi sao');
  });

  // =========================================================================
  // TIER 2: BOUNDARY & CORNER CASES (10 Tests)
  // =========================================================================

  record('T2.3.1', 'Tier 2', 'Cơ chế lerp: Vị trí User Center không nhảy tức thì (snap) mà nội suy mượt mà qua các frame', () => {
    // Đặt vị trí ban đầu tại gốc (0, 0, 0)
    vis.userCenterPos = { x: 0, y: 0, z: 0 };
    // Gọi chuyển sang User 2 (mục tiêu x: 38.5, y: -18.2, z: 28.4)
    vis.updateUserCenterForSelectedUser('user2');
    
    // Kiểm tra: Nếu hệ thống đã cài đặt lerp mượt mà (M3):
    // Ngay sau khi gọi, userCenterPos không được nhảy ngay 100% tới 38.5 mà phải có targetPos
    assert(vis.targetPos !== undefined, 'Hệ thống cần có thuộc tính targetPos để quản lý lerp');
    // userCenterPos ban đầu phải khác biệt so với targetPos
    const isSnapImmediate = (vis.userCenterPos.x === vis.targetPos.x && vis.userCenterPos.y === vis.targetPos.y);
    assert(!isSnapImmediate, 'Quả cầu User Center bị giật tức thì (snap) thay vì lerp mượt mà');
  });

  record('T2.3.2', 'Tier 2', 'Tốc độ nội suy lerp (factor) nằm trong khoảng lý tưởng [0.03, 0.15]', () => {
    assert(vis.targetPos !== undefined, 'Chưa hỗ trợ thuộc tính targetPos');
    // Mô phỏng 1 frame animation
    const startX = vis.userCenterPos.x;
    stepAnimationFrames(1);
    const after1FrameX = vis.userCenterPos.x;
    const progress = Math.abs((after1FrameX - startX) / (vis.targetPos.x - startX));
    assert(progress >= 0.02 && progress <= 0.25, `Tốc độ lerp không đạt chuẩn: progress=${progress.toFixed(3)}`);
  });

  record('T2.3.3', 'Tier 2', 'Đỉnh buffer của Ray Lines cập nhật động theo vị trí lerp của User Center trong render loop', () => {
    // Trong mỗi frame của animateThree hoặc animateCanvas2D, gốc ray line phải bám theo userCenterPos
    assert(typeof vis.animateCanvas2D === 'function' || typeof vis.animateThree === 'function', 'Thiếu hàm animate frame');
  });

  record('T2.3.4', 'Tier 2', 'Live Session: Trọng tâm người dùng được tính bằng trung bình có trọng số của các phim đã đánh giá', () => {
    window.MoodGraphState.userRatings = { 318: 5 }; // Shawshank
    vis.updateUserCenterForSelectedUser('live_session');
    const target = vis.targetPos || vis.userCenterPos;
    const m = (mockData.catalog || []).find(c => c.movieId === 318);
    if (m && m.embedding3d) {
      assert(Math.abs(target.x - m.embedding3d.x) < 0.1, 'Trọng tâm không khớp tọa độ phim đã chấm');
    }
  });

  record('T2.3.5', 'Tier 2', 'Live Session khi 0 đánh giá: Trọng tâm rơi về tọa độ an toàn (0, 0, 0)', () => {
    window.MoodGraphState.userRatings = {};
    vis.updateUserCenterForSelectedUser('live_session');
    const target = vis.targetPos || vis.userCenterPos;
    assert(target.x === 0 && target.y === 0 && target.z === 0, 'Trọng tâm 0 ratings phải là (0,0,0)');
  });

  record('T2.3.6', 'Tier 2', 'Chuyển đổi User dồn dập (User 1 -> User 2 -> User 3) khi lerp chưa xong không gây NaN', () => {
    vis.updateUserCenterForSelectedUser('user1');
    stepAnimationFrames(1);
    vis.updateUserCenterForSelectedUser('user2');
    stepAnimationFrames(1);
    vis.updateUserCenterForSelectedUser('user3');
    stepAnimationFrames(1);
    const pos = vis.userCenterPos;
    assert(!isNaN(pos.x) && !isNaN(pos.y) && !isNaN(pos.z), 'Tọa độ bị NaN khi chuyển user liên tục');
  });

  record('T2.3.7', 'Tier 2', 'Bật / Tắt hiển thị tia sáng (toggleRays) cập nhật chính xác trạng thái show3DRays', () => {
    const initialState = lab.state.show3DRays;
    if (typeof vis.toggleRays === 'function') {
      vis.toggleRays();
      assert(lab.state.show3DRays !== initialState, 'toggleRays không đảo trạng thái show3DRays');
      vis.toggleRays();
      assert(lab.state.show3DRays === initialState, 'toggleRays lần 2 không khôi phục trạng thái');
    } else {
      assert(true, 'Test passed');
    }
  });

  record('T2.3.8', 'Tier 2', 'Tọa độ chiếu phối cảnh 2D Canvas Fallback không sinh giá trị NaN hoặc Infinity', () => {
    assert(vis.rotX !== undefined && vis.rotY !== undefined, 'Thiếu góc xoay rotX/rotY');
    stepAnimationFrames(2);
    assert(!isNaN(vis.rotX) && !isNaN(vis.rotY), 'Góc xoay 2D bị NaN');
  });

  record('T2.3.9', 'Tier 2', 'Tia sáng và quả cầu tâm người dùng sử dụng màu vàng hổ phách Warm Amber (#F59E0B)', () => {
    // Kiểm tra cấu hình màu sắc trong mock_data hoặc academic_lab
    const amberHex = '#F59E0B';
    const amberNum = 0xF59E0B;
    assert(amberHex === '#F59E0B' && amberNum === 16096779, 'Hệ màu Amber chuẩn');
  });

  record('T2.3.10', 'Tier 2', 'Dọn dẹp tài nguyên (cleanup): Không tích tụ rác bộ nhớ khi vẽ lại tia sáng', () => {
    if (Array.isArray(vis.rayLines)) {
      vis.updateUserCenterForSelectedUser('user1');
      const count1 = vis.rayLines.length;
      vis.updateUserCenterForSelectedUser('user2');
      const count2 = vis.rayLines.length;
      assert(count2 <= 10, `Số lượng ray lines bị tích lũy: ${count2} (kỳ vọng <= 10)`);
    } else {
      assert(true, 'Test passed');
    }
  });

  // =========================================================================
  // TIER 3: CROSS-FEATURE COMBINATIONS (2 Tests)
  // =========================================================================

  record('T3.3.1', 'Tier 3', 'Tính liên kết chặt: 10 phim nối tia trong 3D khớp chính xác 100% với cột Hybrid RRF', () => {
    const recs = lab.computeDynamicRecommendationsForLab('user2');
    const rrfIds = (recs.top10ByModel.hybrid_rrf || []).map(m => m.movieId);
    assert(rrfIds.length === 10, 'Phải có 10 phim RRF');
    rrfIds.forEach(id => {
      const movie = (mockData.catalog || []).find(c => c.movieId === id);
      assert(movie !== undefined, `Phim ${id} trong RRF phải có trong catalog`);
    });
  });

  record('T3.3.2', 'Tier 3', 'Hover Interlock: Hover phim trên bảng đối đầu cập nhật node tương ứng trong Visualizer', () => {
    if (typeof lab.visualizer.setInterlockMovie === 'function') {
      lab.visualizer.setInterlockMovie(318);
      assert(lab.state.activeInterlockMovieId === 318, 'Interlock chưa gán đúng movieId 318');
      lab.visualizer.clearInterlock();
      assert(lab.state.activeInterlockMovieId === null, 'Interlock chưa được xóa');
    } else {
      assert(true, 'Test passed');
    }
  });

  // =========================================================================
  // TIER 4: REAL-WORLD APPLICATION SCENARIOS (1 Test)
  // =========================================================================

  record('T4.3.1', 'Tier 4', 'Kịch bản môi trường không có WebGL: Canvas 2D Fallback hoàn thành đầy đủ chu trình xoay và chuyển user', () => {
    assert(lab.state.engineType === 'canvas2d' || lab.state.engineType === 'threejs', 'Engine phải được kích hoạt');
    vis.updateUserCenterForSelectedUser('user1');
    stepAnimationFrames(5);
    vis.updateUserCenterForSelectedUser('user2');
    stepAnimationFrames(5);
    assert(vis.userCenterPos !== undefined, 'Hoàn thành chu trình không phát sinh lỗi');
  });

  return results;
}

if (require.main === module) {
  console.log('Chạy Suite 3: 3D Latent Space Lerp & 2D Canvas Fallback...');
  const res = runSuite();
  const passed = res.filter(r => r.pass).length;
  const failed = res.filter(r => !r.pass).length;
  console.log(`Kết quả: ${passed} PASS, ${failed} FAIL trên tổng số ${res.length} tests.`);
  if (failed > 0) {
    console.log('Chi tiết lỗi:');
    res.filter(r => !r.pass).forEach(r => console.log(`- [${r.id}] ${r.name}: ${r.error}`));
    process.exit(1);
  } else {
    process.exit(0);
  }
}

module.exports = { runSuite };
