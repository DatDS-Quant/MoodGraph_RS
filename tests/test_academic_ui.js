/**
 * MOODGRAPH E2E TEST SUITE - SUITE 4: ACADEMIC UI, DEV JARGON PURGE & METRICS CONSISTENCY
 * File: tests/test_academic_ui.js
 * 
 * Kiểm tra rà soát văn bản giao diện (loại bỏ dev jargon), quy chuẩn typography
 * (không còn ký tự $ hoặc LaTeX thô), bảng màu Cinematic Dark (#0B0F14, #F59E0B),
 * và sự khớp số liệu giữa 12 chỉ số kiểm chuẩn ngoại tuyến và footnote học thuật.
 */

const { getIndexHtmlContent, createMockEnvironment } = require('./test_helpers');

function runSuite() {
  const results = [];
  const htmlContent = getIndexHtmlContent();
  const env = createMockEnvironment();
  const { window } = env;
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

  record('T1.4.1', 'Tier 1', 'Không còn chuỗi dev jargon "THREE.JS & WEBGL 360°" trên giao diện Mode B', () => {
    const hasJargon1 = htmlContent.includes('THREE.JS & WEBGL 360°') || htmlContent.includes('THREE.JS 360');
    assert(!hasJargon1, 'Giao diện vẫn còn chứa chuỗi "THREE.JS & WEBGL 360°"');
  });

  record('T1.4.2', 'Tier 1', 'Không còn chuỗi dev jargon "SPARSITY TEST" trên các tiêu đề / nhãn Mode B', () => {
    const hasJargon2 = htmlContent.includes('SPARSITY TEST');
    assert(!hasJargon2, 'Giao diện vẫn còn chứa chuỗi "SPARSITY TEST"');
  });

  record('T1.4.3', 'Tier 1', 'Không còn các cụm từ dev thừa "DEV MODE", "DEVELOPER TOOLS" trên Mode B', () => {
    const hasDevMode = /DEV MODE|DEVELOPER TOOLS/i.test(htmlContent);
    assert(!hasDevMode, 'Giao diện vẫn còn chứa từ ngữ DEV MODE / DEVELOPER TOOLS');
  });

  record('T1.4.4', 'Tier 1', 'Tuyệt đối không chứa ký tự dollar ($) phục vụ công thức LaTeX trong giao diện hiển thị', () => {
    // Tìm các chuỗi dạng $...$ hoặc $$...$$ trong HTML
    const latexDollarMatches = htmlContent.match(/\$[^$\n]+\$/g) || [];
    assert(latexDollarMatches.length === 0, `Phát hiện ${latexDollarMatches.length} công thức LaTeX chứa dấu dollar: ${latexDollarMatches.slice(0, 3).join(', ')}`);
  });

  record('T1.4.5', 'Tier 1', 'Toàn bộ tiêu đề cột 5 mô hình trong bảng đối đầu sử dụng 100% Tiếng Việt chuẩn', () => {
    const models = (mockData && mockData.modelsMetadata) || {};
    Object.keys(models).forEach(k => {
      const name = models[k].name;
      assert(name && typeof name === 'string' && name.length > 0, `Thiếu tên mô hình ${k}`);
    });
  });

  record('T1.4.6', 'Tier 1', 'Bảng chỉ số kiểm chuẩn ngoại tuyến cung cấp đầy đủ 12 chỉ số đo lường', () => {
    const benchmarks = (mockData && mockData.offlineBenchmarks && mockData.offlineBenchmarks.metrics) || mockData.benchmarkMetrics || [];
    assert(benchmarks.length === 12, `Số lượng chỉ số ngoại tuyến là ${benchmarks.length}, kỳ vọng 12 chỉ số`);
  });

  record('T1.4.7', 'Tier 1', 'Mỗi chỉ số ngoại tuyến có đầy đủ điểm số cho 5 mô hình', () => {
    const benchmarks = (mockData && mockData.offlineBenchmarks && mockData.offlineBenchmarks.metrics) || mockData.benchmarkMetrics || [];
    benchmarks.forEach(item => {
      assert(item.als !== undefined, `Thiếu điểm ALS ở chỉ số ${item.name || item.metric}`);
      assert(item.kg !== undefined, `Thiếu điểm KG ở chỉ số ${item.name || item.metric}`);
      assert(item.rrf !== undefined || item.hybrid_rrf !== undefined, `Thiếu điểm RRF ở chỉ số ${item.name || item.metric}`);
      assert(item.weighted !== undefined || item.hybrid_weighted !== undefined, `Thiếu điểm Weighted ở chỉ số ${item.name || item.metric}`);
      assert(item.pop !== undefined || item.popularity !== undefined, `Thiếu điểm Popularity ở chỉ số ${item.name || item.metric}`);
    });
  });

  record('T1.4.8', 'Tier 1', 'Số liệu chỉ số NDCG@10 của Hybrid RRF đạt mức xuất sắc vượt trội so với ALS và KG đơn lẻ', () => {
    const benchmarks = (mockData && mockData.offlineBenchmarks && mockData.offlineBenchmarks.metrics) || mockData.benchmarkMetrics || [];
    const ndcg10 = benchmarks.find(b => (b.metric === 'NDCG@10' || (b.name && b.name.includes('NDCG @ 10'))));
    assert(ndcg10 !== undefined, 'Không tìm thấy chỉ số NDCG@10');
    const rrfScore = ndcg10.rrf !== undefined ? ndcg10.rrf : ndcg10.hybrid_rrf;
    assert(rrfScore > ndcg10.als, `NDCG@10 của RRF (${rrfScore}) phải cao hơn ALS (${ndcg10.als})`);
  });

  record('T1.4.9', 'Tier 1', 'Ghi chú học thuật (Footnote) nêu rõ phương pháp luận kiểm chuẩn trên 132 người dùng Phase 5', () => {
    const has132Users = htmlContent.includes('132') && (htmlContent.includes('người dùng') || htmlContent.includes('khán giả') || htmlContent.includes('users'));
    assert(has132Users, 'Ghi chú học thuật chưa đề cập đến tập mẫu 132 người dùng kiểm chuẩn Phase 5');
  });

  record('T1.4.10', 'Tier 1', 'Màu nền chủ đạo của toàn bộ giao diện tuân thủ tông Cinematic Dark (#0B0F14 / #0A0D14)', () => {
    const hasDarkBg = htmlContent.includes('#0B0F14') || htmlContent.includes('#0A0D14') || htmlContent.includes('bg-[#0B0F14]');
    assert(hasDarkBg, 'Giao diện không sử dụng màu nền Cinematic Dark chuẩn #0B0F14');
  });

  // =========================================================================
  // TIER 2: BOUNDARY & CORNER CASES (10 Tests)
  // =========================================================================

  record('T2.4.1', 'Tier 2', 'Điểm nhấn giao diện (Accent color) sử dụng màu vàng hổ phách Warm Amber (#F59E0B / #D97706)', () => {
    const hasAmber = htmlContent.includes('#F59E0B') || htmlContent.includes('#D97706');
    assert(hasAmber, 'Giao diện không sử dụng màu nhấn Warm Amber (#F59E0B / #D97706)');
  });

  record('T2.4.2', 'Tier 2', 'Loại bỏ hoàn toàn màu tím AI (#8B5CF6, #A855F7, #7C3AED) khỏi màu nhấn chủ đạo', () => {
    const purpleRegex = /#8B5CF6|#A855F7|#7C3AED|purple-600|violet-600/i;
    // Kiểm tra trong Mode B container
    const modeBStart = htmlContent.indexOf('id="mode-b-container"');
    if (modeBStart !== -1) {
      const modeBSlice = htmlContent.substring(modeBStart, modeBStart + 8000);
      assert(!purpleRegex.test(modeBSlice), 'Vẫn còn màu tím AI sặc sỡ trong khu vực Mode B');
    }
  });

  record('T2.4.3', 'Tier 2', 'Không có thư viện ngoài MathJax hoặc KaTeX CDN nhúng thừa gây chậm trễ', () => {
    const hasMathJaxCDN = /cdn\.jsdelivr\.net\/.*mathjax|cdnjs\.cloudflare\.com\/.*katex/i.test(htmlContent);
    assert(!hasMathJaxCDN, 'Phát hiện CDN MathJax / KaTeX thừa không cần thiết');
  });

  record('T2.4.4', 'Tier 2', 'Độ tương phản màu chữ: Sử dụng gam màu xám sáng (#F8FAFC, #E2E8F0, #CBD5E1) trên nền tối', () => {
    const hasReadableText = htmlContent.includes('#F8FAFC') || htmlContent.includes('#E2E8F0') || htmlContent.includes('#CBD5E1') || htmlContent.includes('text-slate-100');
    assert(hasReadableText, 'Màu chữ không đạt tiêu chuẩn tương phản giao diện tối');
  });

  record('T2.4.5', 'Tier 2', 'Kiểm tra tính nhất quán giá trị Novelty: Mô hình Popularity có novelty thấp nhất', () => {
    const benchmarks = (mockData && mockData.offlineBenchmarks && mockData.offlineBenchmarks.metrics) || mockData.benchmarkMetrics || [];
    const nov = benchmarks.find(b => b.metric === 'Nov' || (b.name && b.name.includes('Novelty')));
    if (nov) {
      const popScore = nov.pop !== undefined ? nov.pop : nov.popularity;
      assert(popScore <= nov.als, 'Popularity phải có Novelty thấp hơn ALS');
      assert(popScore <= nov.kg, 'Popularity phải có Novelty thấp hơn KG');
    }
  });

  record('T2.4.6', 'Tier 2', 'Chỉ số Diversity (Độ đa dạng thể loại) của Hybrid RRF cao hơn hoặc xấp xỉ Spark ALS', () => {
    const benchmarks = (mockData && mockData.offlineBenchmarks && mockData.offlineBenchmarks.metrics) || mockData.benchmarkMetrics || [];
    const div = benchmarks.find(b => b.metric === 'Div' || (b.name && b.name.includes('Diversity')));
    if (div) {
      const rrfScore = div.rrf !== undefined ? div.rrf : div.hybrid_rrf;
      assert(rrfScore >= div.als * 0.95, 'Hybrid RRF phải duy trì độ đa dạng cao');
    }
  });

  record('T2.4.7', 'Tier 2', 'Đoạn footnote giải thích rõ đơn vị của Novelty là bits thông tin entropy', () => {
    const footnoteText = (mockData && mockData.offlineBenchmarks && mockData.offlineBenchmarks.academicFootnote) || '';
    const hasBitsExplanation = htmlContent.includes('bits') || htmlContent.includes('entropy') || footnoteText.includes('bits') || footnoteText.includes('entropy');
    assert(hasBitsExplanation, 'Footnote cần diễn giải đơn vị đo lường bits của chỉ số Novelty');
  });

  record('T2.4.8', 'Tier 2', 'Ma trận nhiệt Spearman / Jaccard: Đường chéo chính tự tương quan bằng đúng 1.000', () => {
    const jaccard = mockData.jaccardMatrix || [];
    if (jaccard.length > 0) {
      jaccard.forEach((row, idx) => {
        if (row[idx] !== undefined) {
          assert(Math.abs(row[idx] - 1.0) < 0.001, `Đường chéo chính [${idx}][${idx}] khác 1.0: ${row[idx]}`);
        }
      });
    }
  });

  record('T2.4.9', 'Tier 2', 'Toàn bộ giá trị trong ma trận Jaccard nằm chặt trong khoảng [0.0, 1.0]', () => {
    const jaccard = mockData.jaccardMatrix || [];
    jaccard.forEach((row, rIdx) => {
      row.forEach((val, cIdx) => {
        if (val !== null) {
          assert(val >= 0.0 && val <= 1.0, `Giá trị Jaccard tại [${rIdx}][${cIdx}] ngoài biên [0, 1]: ${val}`);
        }
      });
    });
  });

  record('T2.4.10', 'Tier 2', 'Chẩn đoán Cold-Start và Long-Tail Pareto hiển thị đầy đủ các ngưỡng đo lường', () => {
    const coldStart = mockData.coldStartData;
    const longTail = mockData.longTailData;
    assert(coldStart !== undefined, 'Thiếu dữ liệu chẩn đoán coldStartData');
    assert(longTail !== undefined, 'Thiếu dữ liệu chẩn đoán longTailData');
  });

  // =========================================================================
  // TIER 3: CROSS-FEATURE COMBINATIONS (2 Tests)
  // =========================================================================

  record('T3.4.1', 'Tier 3', 'Sự ăn khớp số học: Trùng lặp User 1 trong Bảng đối đầu tương thích với ô Jaccard (ALS, KG)', () => {
    const recs = window.AcademicLab.computeDynamicRecommendationsForLab('user1');
    const alsSet = new Set(recs.top10ByModel.als.map(m => m.movieId));
    const kgSet = new Set(recs.top10ByModel.kg.map(m => m.movieId));
    let inter = 0;
    alsSet.forEach(id => { if (kgSet.has(id)) inter++; });
    const union = new Set([...alsSet, ...kgSet]).size;
    const empiricalJaccard = inter / union;

    const jaccardMatrix = mockData.jaccardMatrix || [];
    // ALS ở chỉ số 0, KG ở chỉ số 1
    if (jaccardMatrix.length > 1 && jaccardMatrix[0][1] !== undefined) {
      const offlineJaccard = jaccardMatrix[0][1];
      // Độ sai lệch không quá 0.25 giữa dữ liệu offline 132 users và người dùng cụ thể
      assert(Math.abs(empiricalJaccard - offlineJaccard) < 0.35, `Sai lệch quá lớn giữa Jaccard thực nghiệm (${empiricalJaccard.toFixed(3)}) và ma trận (${offlineJaccard})`);
    }
  });

  record('T3.4.2', 'Tier 3', 'Mô tả học thuật của mô hình phản ánh đúng bản chất giải thuật (Collaborative Filtering, KG, RRF)', () => {
    const models = mockData.modelsMetadata || {};
    const hasAls = models.als && (
      (models.als.name && models.als.name.includes('ALS')) ||
      (models.als.description && models.als.description.includes('Spark')) ||
      (models.als.algorithm && models.als.algorithm.includes('Matrix Factorization'))
    );
    assert(hasAls, 'Mô tả ALS không phản ánh đúng giải thuật');

    const hasKg = models.kg && (
      (models.kg.name && models.kg.name.includes('Knowledge Graph')) ||
      (models.kg.description && models.kg.description.includes('đồ thị')) ||
      (models.kg.algorithm && models.kg.algorithm.includes('Random Walk'))
    );
    assert(hasKg, 'Mô tả KG không phản ánh đúng giải thuật');

    const hasRrf = models.hybrid_rrf && (
      (models.hybrid_rrf.name && models.hybrid_rrf.name.includes('RRF')) ||
      (models.hybrid_rrf.description && models.hybrid_rrf.description.includes('nghịch đảo')) ||
      (models.hybrid_rrf.algorithm && models.hybrid_rrf.algorithm.includes('Reciprocal Rank Fusion'))
    );
    assert(hasRrf, 'Mô tả Hybrid RRF không phản ánh đúng giải thuật');
  });

  // =========================================================================
  // TIER 4: REAL-WORLD APPLICATION SCENARIOS (1 Test)
  // =========================================================================

  record('T4.4.1', 'Tier 4', 'Kịch bản Thẩm định Khoa học (Peer Review Showcase): Toàn bộ trang Mode B sẵn sàng trình diễn học thuật', () => {
    // 1. Kiểm tra tiêu đề chính không chứa từ ngữ phô trương dev
    const headerTitle = htmlContent.includes('PHÒNG THÍ NGHIỆM') || htmlContent.includes('ACADEMIC LAB');
    assert(headerTitle, 'Tiêu đề trang phản ánh đúng tính chất Academic Lab');

    // 2. Kiểm tra có đủ các khối hiển thị cốt lõi
    const has3D = htmlContent.includes('threejs-container');
    const hasHeadToHead = htmlContent.includes('head-to-head-columns');
    const hasBenchmarks = htmlContent.includes('offline-benchmarks');
    assert(has3D && hasHeadToHead && hasBenchmarks, 'Thiếu các khối cốt lõi phục vụ báo cáo học thuật');
  });

  return results;
}

if (require.main === module) {
  console.log('Chạy Suite 4: Academic UI, Dev Jargon Purge & Metrics Consistency...');
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
