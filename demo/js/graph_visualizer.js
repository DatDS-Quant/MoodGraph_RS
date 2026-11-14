/**
 * MoodGraph Mode B: Interactive Knowledge Graph Explorer (vis-network Integration).
 * Trực quan hóa Mạng lưới Đồ thị Tri thức Đa tầng Tương tác (Heterogeneous Knowledge Graph).
 * 
 * Bảng mã màu chuẩn Obsidian Dark Glassmorphism:
 * - User (Khán giả): Vàng Hổ Phách #F59E0B
 * - Liked Movie (Phim Đã Thích): Xanh Cyan #06B6D4
 * - Genre (Thể loại Điện ảnh): Lục Bảo #10B981
 * - Mood/Genome Tag (Thẻ Tâm Trạng Ngữ Nghĩa): Xanh Ngọc #14B8A6
 * - Recommended Movie (Phim Đề Xuất): Tím Thạch Anh #8B5CF6
 */

(function (window) {
  'use strict';

  var KnowledgeGraphVisualizer = {
    network: null,
    container: null,
    nodesDataSet: null,
    edgesDataSet: null,
    currentUserId: 1,
    currentMovieId: 1,
    rawGraphData: null,
    activeHighlightedNodeId: null,

    // Mã màu chuẩn
    COLORS: {
      USER: '#F59E0B',
      LIKED_MOVIE: '#06B6D4',
      GENRE: '#10B981',
      GENOME_TAG: '#14B8A6',
      RECOMMENDED_MOVIE: '#8B5CF6',
      EDGE_DEFAULT: 'rgba(148, 163, 184, 0.35)',
      EDGE_HIGHLIGHT: '#F59E0B'
    },

    /**
     * Khởi tạo vis-network container
     */
    init: function (containerId) {
      this.container = document.getElementById(containerId || 'vis-graph-container');
      if (!this.container) {
        console.warn('KnowledgeGraphVisualizer: Không tìm thấy container #' + (containerId || 'vis-graph-container'));
        return;
      }

      if (typeof vis === 'undefined') {
        console.warn('KnowledgeGraphVisualizer: Thư viện vis-network chưa sẵn sàng.');
        return;
      }

      // Khởi tạo DataSet
      this.nodesDataSet = new vis.DataSet([]);
      this.edgesDataSet = new vis.DataSet([]);

      var data = {
        nodes: this.nodesDataSet,
        edges: this.edgesDataSet
      };

      // Cấu hình vật lý và giao diện trực quan cao cấp
      var options = {
        nodes: {
          shape: 'dot',
          size: 20,
          font: {
            size: 12,
            color: '#F1F5F9',
            face: 'Inter, system-ui, sans-serif',
            strokeWidth: 3,
            strokeColor: '#0B0F14'
          },
          borderWidth: 2,
          shadow: {
            enabled: true,
            color: 'rgba(0,0,0,0.6)',
            size: 10,
            x: 2,
            y: 2
          }
        },
        edges: {
          width: 2,
          color: {
            color: this.COLORS.EDGE_DEFAULT,
            highlight: this.COLORS.EDGE_HIGHLIGHT,
            hover: '#F59E0B'
          },
          smooth: {
            type: 'continuous',
            roundness: 0.2
          },
          font: {
            size: 10,
            color: '#94A3B8',
            strokeWidth: 2,
            strokeColor: '#0B0F14',
            align: 'middle'
          },
          arrows: {
            to: { enabled: true, scaleFactor: 0.6 }
          }
        },
        physics: {
          enabled: true,
          solver: 'barnesHut',
          barnesHut: {
            gravitationalConstant: -3500,
            centralGravity: 0.3,
            springLength: 120,
            springConstant: 0.04,
            damping: 0.09,
            avoidOverlap: 0.2
          },
          stabilization: {
            iterations: 150,
            updateInterval: 25
          }
        },
        interaction: {
          hover: true,
          tooltipDelay: 100,
          hideEdgesOnDrag: false,
          zoomView: true,
          dragView: true
        }
      };

      this.network = new vis.Network(this.container, data, options);
      this.bindEvents();

      // Nạp đồ thị mặc định cho User 1
      this.loadSubgraph(1, 1);
    },

    /**
     * Gắn các sự kiện tương tác: Hover Interlock, Click Focus, Floating Tooltip
     */
    bindEvents: function () {
      var self = this;
      if (!this.network) return;

      // Hover Node: Hiệu ứng Hover Interlock
      this.network.on('hoverNode', function (params) {
        var nodeId = params.node;
        self.highlightConnectedPath(nodeId);
        self.showFloatingTooltip(nodeId, params.pointer.DOM);
      });

      // Blur Node: Hủy hiệu ứng mờ
      this.network.on('blurNode', function () {
        self.resetHighlight();
        self.hideFloatingTooltip();
      });

      // Hover Edge
      this.network.on('hoverEdge', function (params) {
        // Có thể highlight cạnh
      });

      // Click Node: Ghim tiêu điểm
      this.network.on('click', function (params) {
        if (params.nodes.length > 0) {
          var clickedNodeId = params.nodes[0];
          var nodeData = self.nodesDataSet.get(clickedNodeId);
          if (nodeData && (nodeData.type === 'RECOMMENDED_MOVIE' || nodeData.type === 'LIKED_MOVIE')) {
            var mid = nodeData.movieId;
            if (mid && window.MoodGraphApp && typeof window.MoodGraphApp.openMovieDetailModal === 'function') {
              window.MoodGraphApp.openMovieDetailModal(mid);
            }
          }
        }
      });
    },

    /**
     * Nạp dữ liệu đồ thị con từ API hoặc Fallback
     */
    loadSubgraph: function (userId, movieId) {
      this.currentUserId = userId || this.currentUserId;
      this.currentMovieId = movieId || this.currentMovieId;
      var self = this;

      var bannerText = document.getElementById('kg-visualizer-meta-title');
      if (bannerText) {
        bannerText.textContent = 'Đang tải cấu trúc đồ thị cho Khán giả #' + this.currentUserId + '...';
      }

      // Gọi REST API GET /api/lab/graph/subgraph
      var apiUrl = '/api/lab/graph/subgraph?user_id=' + encodeURIComponent(this.currentUserId) + '&movie_id=' + encodeURIComponent(this.currentMovieId);

      fetch(apiUrl)
        .then(function (response) {
          if (!response.ok) {
            throw new Error('API returned ' + response.status);
          }
          return response.json();
        })
        .then(function (data) {
          self.renderGraph(data);
        })
        .catch(function (err) {
          console.warn('API subgraph fetch failed (' + err.message + '). Sử dụng bộ dữ liệu dự phòng chuẩn hóa.');
          self.renderFallbackGraph(self.currentUserId, self.currentMovieId);
        });
    },

    /**
     * Kết xuất các nút và cạnh lên vis-network
     */
    renderGraph: function (graphData) {
      if (!graphData || !graphData.nodes) return;
      this.rawGraphData = graphData;

      var formattedNodes = [];
      var formattedEdges = [];

      for (var i = 0; i < graphData.nodes.length; i++) {
        var n = graphData.nodes[i];
        var size = 18;
        var shape = 'dot';
        var borderWidth = 2;

        if (n.type === 'USER') {
          size = 28;
          shape = 'star';
          borderWidth = 3;
        } else if (n.type === 'RECOMMENDED_MOVIE') {
          size = 24;
          shape = 'diamond';
          borderWidth = 3;
        } else if (n.type === 'LIKED_MOVIE') {
          size = 20;
          shape = 'dot';
        } else if (n.type === 'GENRE') {
          size = 18;
          shape = 'box';
        } else if (n.type === 'GENOME_TAG') {
          size = 16;
          shape = 'hexagon';
        }

        formattedNodes.push({
          id: n.id,
          label: n.label,
          type: n.type,
          color: {
            background: n.color || '#F59E0B',
            border: '#FFFFFF',
            highlight: {
              background: n.color || '#F59E0B',
              border: '#FDE68A'
            }
          },
          size: size,
          shape: shape,
          borderWidth: borderWidth,
          movieId: n.movieId,
          rating: n.rating,
          relevance: n.relevance,
          score: n.score,
          title: n.label + ' (' + n.type + ')'
        });
      }

      for (var j = 0; j < graphData.edges.length; j++) {
        var e = graphData.edges[j];
        var fromId = e.from || e.from_;
        var toId = e.to;
        var width = Math.max(1.5, Math.min(5, (e.weight || 0.5) * 4));

        formattedEdges.push({
          id: 'edge_' + j,
          from: fromId,
          to: toId,
          label: e.label || '',
          weight: e.weight || 1.0,
          type: e.type || '',
          width: width,
          color: {
            color: this.COLORS.EDGE_DEFAULT,
            highlight: this.COLORS.EDGE_HIGHLIGHT
          },
          arrows: { to: { enabled: true, scaleFactor: 0.6 } }
        });
      }

      this.nodesDataSet.clear();
      this.edgesDataSet.clear();
      this.nodesDataSet.add(formattedNodes);
      this.edgesDataSet.add(formattedEdges);

      // Cập nhật thẻ chú thích học thuật
      var expBox = document.getElementById('kg-academic-explanation-text');
      if (expBox) {
        expBox.textContent = graphData.academic_explanation || 'Được gợi ý dựa trên mạng lưới tri thức.';
      }

      var bannerText = document.getElementById('kg-visualizer-meta-title');
      if (bannerText) {
        bannerText.textContent = 'Mạng Tri Thức Đa Tầng • ' + formattedNodes.length + ' Nút • ' + formattedEdges.length + ' Liên Kết';
      }

      // Ổn định và căn giữa góc nhìn
      if (this.network) {
        this.network.fit({ animation: { duration: 800, easingFunction: 'easeInOutQuad' } });
      }
    },

    /**
     * Dữ liệu Fallback khi chưa kết nối được API
     */
    renderFallbackGraph: function (userId, movieId) {
      var candidateTitle = 'Toy Story (1995)';
      if (movieId === 2) candidateTitle = 'Jumanji (1995)';
      if (movieId === 3) candidateTitle = 'Grumpier Old Men (1995)';
      if (movieId === 123) candidateTitle = 'Chungking Express (1994)';
      if (movieId === 8195) candidateTitle = "Avventura, L' (1960)";

      var fallbackData = {
        nodes: [
          { id: 'user_' + userId, label: 'Khán giả #' + userId, type: 'USER', color: '#F59E0B' },
          { id: 'movie_1', label: 'Toy Story (1995)', type: 'LIKED_MOVIE', movieId: 1, rating: 5.0, color: '#06B6D4' },
          { id: 'genre_anim', label: 'Hoạt hình', type: 'GENRE', color: '#10B981' },
          { id: 'genre_comedy', label: 'Hài hước', type: 'GENRE', color: '#10B981' },
          { id: 'tag_pixar', label: 'pixar', type: 'GENOME_TAG', relevance: 0.95, color: '#14B8A6' },
          { id: 'tag_witty', label: 'witty', type: 'GENOME_TAG', relevance: 0.88, color: '#14B8A6' },
          { id: 'cand_' + movieId, label: candidateTitle, type: 'RECOMMENDED_MOVIE', movieId: movieId, score: 0.884, color: '#8B5CF6' }
        ],
        edges: [
          { from: 'user_' + userId, to: 'movie_1', label: 'Đã thích (5.0★)', weight: 1.0, type: 'RATED' },
          { from: 'movie_1', to: 'genre_anim', label: 'Thể loại', weight: 0.72, type: 'HAS_GENRE' },
          { from: 'genre_anim', to: 'cand_' + movieId, label: 'Đồng thể loại', weight: 0.72, type: 'HAS_GENRE' },
          { from: 'movie_1', to: 'genre_comedy', label: 'Thể loại', weight: 0.65, type: 'HAS_GENRE' },
          { from: 'genre_comedy', to: 'cand_' + movieId, label: 'Đồng thể loại', weight: 0.65, type: 'HAS_GENRE' },
          { from: 'movie_1', to: 'tag_pixar', label: 'rel = 0.95', weight: 0.95, type: 'HAS_TAG' },
          { from: 'tag_pixar', to: 'cand_' + movieId, label: 'rel = 0.90', weight: 0.90, type: 'HAS_TAG' },
          { from: 'movie_1', to: 'tag_witty', label: 'rel = 0.88', weight: 0.88, type: 'HAS_TAG' },
          { from: 'tag_witty', to: 'cand_' + movieId, label: 'rel = 0.84', weight: 0.84, type: 'HAS_TAG' }
        ],
        academic_explanation: "Được đề xuất bởi tổ hợp Metapath P1 (Đồng thể loại Hoạt hình, Hài hước, đóng góp 35%) và P2 (Cùng mang đặc trưng ngữ nghĩa pixar, witty với độ tương đồng 0.855, đóng góp 45%)."
      };

      this.renderGraph(fallbackData);
    },

    /**
     * Hiệu ứng Hover Interlock: Sáng bừng chuỗi liên kết và làm mờ các nút khác
     */
    highlightConnectedPath: function (nodeId) {
      if (!this.network || !this.nodesDataSet || !this.edgesDataSet) return;

      var connectedNodes = this.network.getConnectedNodes(nodeId);
      var connectedEdges = this.network.getConnectedEdges(nodeId);

      var activeNodeSet = {};
      activeNodeSet[nodeId] = true;
      for (var i = 0; i < connectedNodes.length; i++) {
        activeNodeSet[connectedNodes[i]] = true;
      }

      var activeEdgeSet = {};
      for (var j = 0; j < connectedEdges.length; j++) {
        activeEdgeSet[connectedEdges[j]] = true;
      }

      // Cập nhật độ đậm nhạt (opacity)
      var allNodes = this.nodesDataSet.get();
      var nodeUpdates = [];
      for (var k = 0; k < allNodes.length; k++) {
        var n = allNodes[k];
        if (activeNodeSet[n.id]) {
          nodeUpdates.push({ id: n.id, opacity: 1.0 });
        } else {
          nodeUpdates.push({ id: n.id, opacity: 0.2 });
        }
      }
      this.nodesDataSet.update(nodeUpdates);

      var allEdges = this.edgesDataSet.get();
      var edgeUpdates = [];
      for (var m = 0; m < allEdges.length; m++) {
        var e = allEdges[m];
        if (activeEdgeSet[e.id]) {
          edgeUpdates.push({
            id: e.id,
            color: { color: this.COLORS.EDGE_HIGHLIGHT, opacity: 1.0 },
            width: e.width + 1.5
          });
        } else {
          edgeUpdates.push({
            id: e.id,
            color: { color: 'rgba(100, 116, 139, 0.15)', opacity: 0.15 }
          });
        }
      }
      this.edgesDataSet.update(edgeUpdates);
    },

    /**
     * Khôi phục trạng thái ban đầu sau khi rê chuột ra ngoài
     */
    resetHighlight: function () {
      if (!this.nodesDataSet || !this.edgesDataSet) return;

      var allNodes = this.nodesDataSet.get();
      var nodeUpdates = allNodes.map(function (n) {
        return { id: n.id, opacity: 1.0 };
      });
      this.nodesDataSet.update(nodeUpdates);

      var allEdges = this.edgesDataSet.get();
      var edgeUpdates = allEdges.map(function (e) {
        return {
          id: e.id,
          color: { color: 'rgba(148, 163, 184, 0.35)', opacity: 1.0 },
          width: Math.max(1.5, Math.min(5, (e.weight || 0.5) * 4))
        };
      });
      this.edgesDataSet.update(edgeUpdates);
    },

    /**
     * Hiển thị Tooltip kính quang học nổi
     */
    showFloatingTooltip: function (nodeId, domPos) {
      var tooltip = document.getElementById('vis-graph-floating-tooltip');
      if (!tooltip) return;

      var node = this.nodesDataSet.get(nodeId);
      if (!node) return;

      var titleEl = document.getElementById('vis-tooltip-title');
      var typeEl = document.getElementById('vis-tooltip-type');
      var detailsEl = document.getElementById('vis-tooltip-details');

      if (titleEl) titleEl.textContent = node.label;
      if (typeEl) {
        typeEl.textContent = node.type;
        typeEl.style.color = node.color ? (node.color.background || node.color) : '#F59E0B';
      }

      if (detailsEl) {
        var html = '';
        if (node.type === 'USER') {
          html = 'Nguồn phát sở thích tích cực (Anchor User). Đã ghi nhận lịch sử tương tác.';
        } else if (node.type === 'RECOMMENDED_MOVIE') {
          html = 'Tác phẩm được đề xuất hàng đầu bởi dung hợp Metapaths P1 (Thể loại) và P2 (Genome).';
        } else if (node.type === 'LIKED_MOVIE') {
          html = 'Phim bạn từng đánh giá <strong>' + (node.rating || 5.0) + '★</strong> trong lịch sử huấn luyện.';
        } else if (node.type === 'GENRE') {
          html = 'Nút cầu nối thể loại điện ảnh (Metapath P1).';
        } else if (node.type === 'GENOME_TAG') {
          html = 'Đặc trưng ngữ nghĩa tâm trạng (Metapath P2). Độ liên quan: <strong>' + (node.relevance || 0.9) + '</strong>.';
        }
        detailsEl.innerHTML = html;
      }

      // Định vị tooltip
      var rect = this.container.getBoundingClientRect();
      var x = domPos.x + 15;
      var y = domPos.y + 15;

      if (x + 260 > rect.width) x = domPos.x - 270;
      if (y + 140 > rect.height) y = domPos.y - 150;

      tooltip.style.left = x + 'px';
      tooltip.style.top = y + 'px';
      tooltip.classList.remove('hidden');
    },

    hideFloatingTooltip: function () {
      var tooltip = document.getElementById('vis-graph-floating-tooltip');
      if (tooltip) tooltip.classList.add('hidden');
    },

    /**
     * Tiện ích công khai: Tiêu điểm vào một phim đề xuất khi người dùng click trên danh sách Top-10
     */
    focusCandidate: function (movieId, title) {
      this.loadSubgraph(this.currentUserId, movieId);
    },

    resetCamera: function () {
      if (this.network) {
        this.network.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
      }
    }
  };

  window.KnowledgeGraphVisualizer = KnowledgeGraphVisualizer;

})(window);
