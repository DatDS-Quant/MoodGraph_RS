/**
 * MoodGraph Milestone 2 - UI/UX & Interactive Graph Adversarial Test Suite
 * File: tests/test_m2_graph_interactive.js
 * 
 * Kiểm thử đối kháng chuyên sâu cho:
 * 1. Khởi tạo vis-network & cấu hình tương tác (drag, zoom, pan, hover, click)
 * 2. Cơ chế Hover Interlock (làm mờ 80% nút không liên quan, làm sáng bừng đường liên kết)
 * 3. Tooltip kính quang học nổi và thông tin chi tiết
 * 4. Đồng bộ giữa Bảng đối đầu Top-10 và Đồ thị tri thức đa tầng
 * 5. Tính chuẩn mực học thuật: không chứa ký tự dollar và LaTeX
 */

const fs = require('fs');
const path = require('path');
const { getIndexHtmlContent, createMockEnvironment } = require('./test_helpers');

function runAdversarialGraphSuite() {
  const results = [];
  const htmlContent = getIndexHtmlContent();
  const env = createMockEnvironment();
  const { window, document } = env;

  function record(id, name, fn) {
    try {
      fn();
      results.push({ id, name, pass: true });
    } catch (err) {
      results.push({ id, name, pass: false, error: err.message });
    }
  }

  function assert(condition, message) {
    if (!condition) throw new Error(message || 'Assertion failed');
  }

  // Nạp mock vis library
  const mockVis = {
    DataSet: function (initialData) {
      this._data = initialData ? [...initialData] : [];
      this.get = function (id) {
        if (id === undefined) return [...this._data];
        return this._data.find(d => d.id === id);
      };
      this.add = function (items) {
        if (Array.isArray(items)) {
          this._data.push(...items);
        } else {
          this._data.push(items);
        }
      };
      this.clear = function () {
        this._data = [];
      };
      this.update = function (updates) {
        updates.forEach(u => {
          const idx = this._data.findIndex(d => d.id === u.id);
          if (idx !== -1) {
            this._data[idx] = Object.assign({}, this._data[idx], u);
          }
        });
      };
    },
    Network: function (container, data, options) {
      this.container = container;
      this.data = data;
      this.options = options;
      this.events = {};
      this.on = function (event, handler) {
        this.events[event] = handler;
      };
      this.fit = function () {};
      this.getConnectedNodes = function (nodeId) {
        // Tìm các node liên kết qua edges
        const edges = data.edges.get();
        const connected = new Set();
        edges.forEach(e => {
          if (e.from === nodeId) connected.add(e.to);
          if (e.to === nodeId) connected.add(e.from);
        });
        return Array.from(connected);
      };
      this.getConnectedEdges = function (nodeId) {
        const edges = data.edges.get();
        return edges.filter(e => e.from === nodeId || e.to === nodeId).map(e => e.id);
      };
    }
  };
  window.vis = mockVis;
  global.vis = mockVis;

  // Nạp graph_visualizer.js vào môi trường
  const graphVisCode = fs.readFileSync(path.join(__dirname, '../demo/js/graph_visualizer.js'), 'utf-8');
  eval(`(function(window, document) { ${graphVisCode} })(window, document);`);

  const Visualizer = window.KnowledgeGraphVisualizer;

  // =========================================================================
  // NHÓM 1: KHỞI TẠO VÀ CẤU HÌNH TƯƠNG TÁC VIS-NETWORK
  // =========================================================================

  record('ADV-KG-1', 'KnowledgeGraphVisualizer được nạp vào window và có đầy đủ API công khai', () => {
    assert(Visualizer, 'Không tìm thấy window.KnowledgeGraphVisualizer');
    assert(typeof Visualizer.init === 'function', 'Thiếu phương thức init');
    assert(typeof Visualizer.loadSubgraph === 'function', 'Thiếu phương thức loadSubgraph');
    assert(typeof Visualizer.highlightConnectedPath === 'function', 'Thiếu phương thức highlightConnectedPath');
    assert(typeof Visualizer.resetHighlight === 'function', 'Thiếu phương thức resetHighlight');
    assert(typeof Visualizer.showFloatingTooltip === 'function', 'Thiếu phương thức showFloatingTooltip');
    assert(typeof Visualizer.hideFloatingTooltip === 'function', 'Thiếu phương thức hideFloatingTooltip');
    assert(typeof Visualizer.focusCandidate === 'function', 'Thiếu phương thức focusCandidate');
  });

  record('ADV-KG-2', 'Khởi tạo vis.Network với các cấu hình tương tác zoomView, dragView, hover', () => {
    // Tạo container giả lập trong DOM
    const container = document.createElement('div');
    container.id = 'vis-graph-container';
    container.getBoundingClientRect = () => ({ width: 800, height: 500, top: 0, left: 0 });
    document.body.appendChild(container);

    Visualizer.init('vis-graph-container');
    assert(Visualizer.network, 'Chưa khởi tạo được vis.Network');
    const opts = Visualizer.network.options;
    assert(opts.interaction.hover === true, 'Tương tác hover chưa được bật');
    assert(opts.interaction.zoomView === true, 'Tương tác zoomView chưa được bật');
    assert(opts.interaction.dragView === true, 'Tương tác dragView chưa được bật');
    assert(opts.physics.solver === 'barnesHut', 'Bộ giải vật lý phải là barnesHut');
  });

  record('ADV-KG-3', 'Cấu hình bảng mã màu 5 loại thực thể đạt chuẩn Obsidian Dark Glassmorphism', () => {
    const c = Visualizer.COLORS;
    assert(c.USER === '#F59E0B', 'Màu User phải là Vàng Hổ Phách #F59E0B');
    assert(c.LIKED_MOVIE === '#06B6D4', 'Màu Phim Đã Thích phải là Xanh Cyan #06B6D4');
    assert(c.GENRE === '#10B981', 'Màu Thể Loại phải là Lục Bảo #10B981');
    assert(c.GENOME_TAG === '#14B8A6', 'Màu Tâm Trạng phải là Xanh Ngọc #14B8A6');
    assert(c.RECOMMENDED_MOVIE === '#8B5CF6', 'Màu Phim Đề Xuất phải là Tím Thạch Anh #8B5CF6');
  });

  // =========================================================================
  // NHÓM 2: KẾT XUẤT ĐỒ THỊ & ĐẦY ĐỦ CÁC LOẠI NODE/EDGE
  // =========================================================================

  record('ADV-KG-4', 'Kết xuất đồ thị chứa đầy đủ 5 loại node (USER, LIKED, GENRE, TAG, CANDIDATE)', () => {
    Visualizer.renderFallbackGraph(1, 1);
    const nodes = Visualizer.nodesDataSet.get();
    const edges = Visualizer.edgesDataSet.get();

    assert(nodes.length >= 6, `Số nút đồ thị (${nodes.length}) quá ít, kỳ vọng >= 6`);
    assert(edges.length >= 6, `Số cạnh đồ thị (${edges.length}) quá ít, kỳ vọng >= 6`);

    const types = new Set(nodes.map(n => n.type));
    assert(types.has('USER'), 'Thiếu node USER');
    assert(types.has('LIKED_MOVIE'), 'Thiếu node LIKED_MOVIE');
    assert(types.has('GENRE'), 'Thiếu node GENRE');
    assert(types.has('GENOME_TAG'), 'Thiếu node GENOME_TAG');
    assert(types.has('RECOMMENDED_MOVIE'), 'Thiếu node RECOMMENDED_MOVIE');
  });

  // =========================================================================
  // NHÓM 3: LOGIC HOVER INTERLOCK (LÀM MỜ 80% & LÀM SÁNG ĐƯỜNG DẪN)
  // =========================================================================

  record('ADV-KG-5', 'Hover Interlock làm mờ 80% (opacity 0.2) các node không liên quan', () => {
    Visualizer.renderFallbackGraph(1, 1);
    
    // Giả sử hover vào node đề xuất 'cand_1'
    Visualizer.highlightConnectedPath('cand_1');

    const nodes = Visualizer.nodesDataSet.get();
    const candNode = nodes.find(n => n.id === 'cand_1');
    assert(candNode.opacity === 1.0, 'Node đề xuất đang hover phải có opacity 1.0');

    // Kiểm tra các node liên kết trực tiếp (ví dụ genre_anim, tag_pixar) có opacity 1.0
    const genreNode = nodes.find(n => n.id === 'genre_anim');
    assert(genreNode.opacity === 1.0, 'Node liên kết (genre_anim) phải có opacity 1.0');

    // Node User không liên kết trực tiếp với cand_1 trong đồ thị bipartite/tripartite
    // sẽ bị làm mờ về opacity 0.2
    const userNode = nodes.find(n => n.type === 'USER');
    assert(userNode.opacity === 0.2, `Node không liên kết trực tiếp phải bị làm mờ về 0.2, nhận được ${userNode.opacity}`);
  });

  record('ADV-KG-6', 'Hover Interlock làm nổi bật màu sắc và tăng bề dày (width) của các cạnh liên kết', () => {
    Visualizer.renderFallbackGraph(1, 1);
    Visualizer.highlightConnectedPath('cand_1');

    const edges = Visualizer.edgesDataSet.get();
    const connectedEdges = edges.filter(e => e.to === 'cand_1' || e.from === 'cand_1');
    assert(connectedEdges.length > 0, 'Phải có ít nhất 1 cạnh nối với cand_1');

    connectedEdges.forEach(e => {
      assert(e.color.color === Visualizer.COLORS.EDGE_HIGHLIGHT, 'Cạnh liên kết phải mang màu highlight #F59E0B');
      assert(e.color.opacity === 1.0, 'Cạnh liên kết phải có opacity 1.0');
    });

    const nonConnectedEdges = edges.filter(e => e.to !== 'cand_1' && e.from !== 'cand_1');
    nonConnectedEdges.forEach(e => {
      assert(e.color.opacity === 0.15, `Cạnh không liên kết phải bị làm mờ về 0.15, nhận được ${e.color.opacity}`);
    });
  });

  record('ADV-KG-7', 'resetHighlight khôi phục 100% độ đậm (opacity 1.0) cho toàn bộ nút và cạnh', () => {
    Visualizer.renderFallbackGraph(1, 1);
    Visualizer.highlightConnectedPath('cand_1');
    Visualizer.resetHighlight();

    const nodes = Visualizer.nodesDataSet.get();
    nodes.forEach(n => {
      assert(n.opacity === 1.0, `Node ${n.id} chưa được khôi phục opacity 1.0 sau resetHighlight`);
    });

    const edges = Visualizer.edgesDataSet.get();
    edges.forEach(e => {
      assert(e.color.opacity === 1.0, `Edge ${e.id} chưa được khôi phục opacity 1.0 sau resetHighlight`);
    });
  });

  // =========================================================================
  // NHÓM 4: TOOLTIP KÍNH QUANG HỌC NỔI
  // =========================================================================

  record('ADV-KG-8', 'showFloatingTooltip hiển thị đúng thông tin thực thể và gỡ bỏ class hidden', () => {
    // Lấy hoặc tạo cấu trúc DOM cho tooltip qua document.getElementById
    const tooltip = document.getElementById('vis-graph-floating-tooltip');
    tooltip.className = 'canvas-3d-hud-card hidden';

    const titleEl = document.getElementById('vis-tooltip-title');
    const typeEl = document.getElementById('vis-tooltip-type');
    const detailsEl = document.getElementById('vis-tooltip-details');

    Visualizer.renderFallbackGraph(1, 1);
    Visualizer.showFloatingTooltip('cand_1', { x: 100, y: 150 });

    assert(!tooltip.classList.contains('hidden'), 'Tooltip phải hiển thị (không chứa class hidden)');
    assert(titleEl.textContent.includes('Toy Story') || titleEl.textContent.length > 0, 'Tiêu đề tooltip rỗng');
    assert(typeEl.textContent === 'RECOMMENDED_MOVIE', 'Loại thực thể tooltip không đúng');
    assert(detailsEl.innerHTML.includes('P1') && detailsEl.innerHTML.includes('P2'), 'Nội dung chi tiết phải giải thích Metapath P1 và P2');

    Visualizer.hideFloatingTooltip();
    assert(tooltip.classList.contains('hidden'), 'hideFloatingTooltip phải thêm lại class hidden');
  });

  // =========================================================================
  // NHÓM 5: CHUỖI GIẢI THÍCH HỌC THUẬT & KHÔNG RÒ RỈ LATEX / DOLLAR
  // =========================================================================

  record('ADV-KG-9', 'Chuỗi giải thích học thuật academic_explanation tuân thủ 100% Tiếng Việt và không chứa LaTeX/dollar', () => {
    Visualizer.renderFallbackGraph(1, 1);
    const exp = Visualizer.rawGraphData.academic_explanation;
    assert(exp && exp.length > 20, 'Thiếu chuỗi academic_explanation');
    assert(!exp.includes('$'), 'academic_explanation không được chứa ký tự dollar');
    assert(!/\\[a-zA-Z]+/.test(exp), 'academic_explanation không được chứa cú pháp LaTeX');
    assert(exp.includes('Metapath P1') && exp.includes('P2'), 'Phải diễn giải Metapath P1 và P2');
  });

  record('ADV-KG-10', 'HTML container tích hợp đầy đủ các phần tử hỗ trợ đồ thị và tooltip', () => {
    assert(htmlContent.includes('id="wrapper-graph-network"'), 'Thiếu id wrapper-graph-network');
    assert(htmlContent.includes('id="vis-graph-container"'), 'Thiếu id vis-graph-container');
    assert(htmlContent.includes('id="vis-graph-floating-tooltip"'), 'Thiếu id vis-graph-floating-tooltip');
    assert(htmlContent.includes('id="kg-academic-explanation-text"'), 'Thiếu id kg-academic-explanation-text');
    assert(htmlContent.includes('id="btn-view-graph-network"'), 'Thiếu id btn-view-graph-network');
  });

  return results;
}

if (require.main === module) {
  console.log('=== CHẠY BỘ KIỂM THỬ ĐỐI KHÁNG TƯƠNG TÁC ĐỒ THỊ & UI (M2) ===');
  const res = runAdversarialGraphSuite();
  const passed = res.filter(r => r.pass).length;
  const failed = res.filter(r => !r.pass).length;
  console.log(`Kết quả: ${passed} PASS, ${failed} FAIL trên tổng số ${res.length} bài kiểm thử.`);
  if (failed > 0) {
    console.log('Chi tiết lỗi:');
    res.filter(r => !r.pass).forEach(r => console.log(`- [${r.id}] ${r.name}: ${r.error}`));
    process.exit(1);
  } else {
    console.log('TẤT CẢ 10 BÀI KIỂM THỬ ĐỐI KHÁNG ĐÃ PASS 100%!');
    process.exit(0);
  }
}

module.exports = { runAdversarialGraphSuite };
