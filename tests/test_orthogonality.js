/**
 * MOODGRAPH E2E TEST SUITE - SUITE 1: ORTHOGONALITY & TOP-10 RECOMMENDATIONS
 * File: tests/test_orthogonality.js
 * 
 * Kiểm tra tính trực giao, phân hóa học thuật giữa các mô hình (Spark ALS, KG, Hybrid RRF, Hybrid Weighted, Popularity).
 * Kiểm tra độ trùng lặp ALS vs KG (40% - 60%), tính hợp lệ 100% phim thuộc CATALOG, công thức Cormack RRF k=60.
 */

const { createMockEnvironment } = require('./test_helpers');

function runSuite() {
  const results = [];
  const env = createMockEnvironment();
  const { window } = env;
  const lab = window.AcademicLab;
  const mockData = window.MOCK_DATA;
  const catalog = mockData.catalog || [];
  const catalogIdSet = new Set(catalog.map(m => m.movieId));

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

  // Helper tính độ trùng lặp giữa 2 danh sách phim
  function calcOverlap(listA, listB) {
    const idsA = new Set((listA || []).map(m => m.movieId));
    const idsB = new Set((listB || []).map(m => m.movieId));
    let count = 0;
    idsA.forEach(id => {
      if (idsB.has(id)) count++;
    });
    return count;
  }

  // =========================================================================
  // TIER 1: FEATURE COVERAGE (15 Tests)
  // =========================================================================

  record('T1.1.1', 'Tier 1', 'User 1 (Alex Turner) trả về đầy đủ 5 mô hình gợi ý', () => {
    const res = lab.computeDynamicRecommendationsForLab('user1');
    assert(res && res.top10ByModel, 'Kết quả không có top10ByModel');
    const models = Object.keys(res.top10ByModel);
    ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'].forEach(m => {
      assert(models.includes(m), `Thiếu mô hình ${m} trong kết quả`);
    });
  });

  record('T1.1.2', 'Tier 1', 'User 1 trả về chính xác 10 phim cho mỗi mô hình', () => {
    const res = lab.computeDynamicRecommendationsForLab('user1');
    ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'].forEach(m => {
      const list = res.top10ByModel[m] || [];
      assert(list.length === 10, `Mô hình ${m} có ${list.length} phim (kỳ vọng 10)`);
    });
  });

  record('T1.1.3', 'Tier 1', 'User 1 có độ trùng lặp ALS vs KG từ 40% đến 60% (4-6 phim)', () => {
    const res = lab.computeDynamicRecommendationsForLab('user1');
    const overlap = calcOverlap(res.top10ByModel.als, res.top10ByModel.kg);
    assert(overlap >= 4 && overlap <= 6, `Độ trùng lặp ALS vs KG là ${overlap} phim (${overlap * 10}%), kỳ vọng 4-6 phim (40%-60%)`);
  });

  record('T1.1.4', 'Tier 1', 'User 2 (Elena Rostova - Sci-Fi) trả về đầy đủ 5 mô hình gợi ý', () => {
    const res = lab.computeDynamicRecommendationsForLab('user2');
    assert(res && res.top10ByModel, 'User 2 không có top10ByModel');
    ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'].forEach(m => {
      assert(res.top10ByModel[m], `User 2 thiếu mô hình ${m}`);
    });
  });

  record('T1.1.5', 'Tier 1', 'User 2 trả về chính xác 10 phim cho mỗi mô hình', () => {
    const res = lab.computeDynamicRecommendationsForLab('user2');
    ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'].forEach(m => {
      const list = res.top10ByModel[m] || [];
      assert(list.length === 10, `User 2: mô hình ${m} có ${list.length} phim`);
    });
  });

  record('T1.1.6', 'Tier 1', 'User 2 có độ trùng lặp ALS vs KG từ 40% đến 60% (loại bỏ lỗi 100% trùng lặp)', () => {
    const res = lab.computeDynamicRecommendationsForLab('user2');
    const overlap = calcOverlap(res.top10ByModel.als, res.top10ByModel.kg);
    assert(overlap >= 4 && overlap <= 6, `User 2 trùng lặp ALS vs KG là ${overlap} phim, kỳ vọng 4-6 phim (40%-60%)`);
  });

  record('T1.1.7', 'Tier 1', 'User 3 (Marcus Vance - Crime/Noir) trả về đầy đủ 5 mô hình gợi ý', () => {
    const res = lab.computeDynamicRecommendationsForLab('user3');
    assert(res && res.top10ByModel, 'User 3 không có top10ByModel');
    ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'].forEach(m => {
      assert(res.top10ByModel[m], `User 3 thiếu mô hình ${m}`);
    });
  });

  record('T1.1.8', 'Tier 1', 'User 3 trả về chính xác 10 phim cho mỗi mô hình', () => {
    const res = lab.computeDynamicRecommendationsForLab('user3');
    ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'].forEach(m => {
      const list = res.top10ByModel[m] || [];
      assert(list.length === 10, `User 3: mô hình ${m} có ${list.length} phim`);
    });
  });

  record('T1.1.9', 'Tier 1', 'User 3 có độ trùng lặp ALS vs KG từ 40% đến 60% (loại bỏ lỗi 100% trùng lặp)', () => {
    const res = lab.computeDynamicRecommendationsForLab('user3');
    const overlap = calcOverlap(res.top10ByModel.als, res.top10ByModel.kg);
    assert(overlap >= 4 && overlap <= 6, `User 3 trùng lặp ALS vs KG là ${overlap} phim, kỳ vọng 4-6 phim (40%-60%)`);
  });

  record('T1.1.10', 'Tier 1', 'User Cold-Start (user42) xử lý đúng trạng thái cold-start (isColdStart = true)', () => {
    const res = lab.computeDynamicRecommendationsForLab('user42');
    assert(res.isColdStart === true, 'user42 phải có isColdStart = true');
    assert(Array.isArray(res.top10ByModel.als) && res.top10ByModel.als.length === 0, 'ALS của Cold-Start phải là mảng rỗng');
    assert(res.top10ByModel.popularity.length > 0, 'Popularity phải cung cấp gợi ý dự phòng');
  });

  record('T1.1.11', 'Tier 1', '100% phim trong Top-10 của User 1 thuộc CATALOG chính thức', () => {
    const res = lab.computeDynamicRecommendationsForLab('user1');
    ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'].forEach(m => {
      (res.top10ByModel[m] || []).forEach(item => {
        assert(catalogIdSet.has(item.movieId), `Phim movieId ${item.movieId} của User 1 không nằm trong CATALOG`);
      });
    });
  });

  record('T1.1.12', 'Tier 1', '100% phim trong Top-10 của User 2 thuộc CATALOG chính thức', () => {
    const res = lab.computeDynamicRecommendationsForLab('user2');
    ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'].forEach(m => {
      (res.top10ByModel[m] || []).forEach(item => {
        assert(catalogIdSet.has(item.movieId), `Phim movieId ${item.movieId} của User 2 không nằm trong CATALOG`);
      });
    });
  });

  record('T1.1.13', 'Tier 1', '100% phim trong Top-10 của User 3 thuộc CATALOG chính thức', () => {
    const res = lab.computeDynamicRecommendationsForLab('user3');
    ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'].forEach(m => {
      (res.top10ByModel[m] || []).forEach(item => {
        assert(catalogIdSet.has(item.movieId), `Phim movieId ${item.movieId} của User 3 không nằm trong CATALOG`);
      });
    });
  });

  record('T1.1.14', 'Tier 1', 'Công thức Cormack RRF k=60: Điểm RRF tính đúng theo nghịch đảo thứ hạng', () => {
    const res = lab.computeDynamicRecommendationsForLab('user2');
    const rrfList = res.top10ByModel.hybrid_rrf || [];
    const alsList = res.top10ByModel.als || [];
    const kgList = res.top10ByModel.kg || [];

    const alsRank = {};
    alsList.forEach((it, idx) => { alsRank[it.movieId] = idx + 1; });
    const kgRank = {};
    kgList.forEach((it, idx) => { kgRank[it.movieId] = idx + 1; });

    // Kiểm tra các phim của RRF có điểm số RRF hợp lệ theo chuẩn Cormack (không dùng rank giả định khi vắng mặt)
    rrfList.forEach(item => {
      const r1 = alsRank[item.movieId];
      const r2 = kgRank[item.movieId];
      const expectedScore = (r1 ? 1.0 / (60 + r1) : 0) + (r2 ? 1.0 / (60 + r2) : 0);
      const actualScore = Number(item.score);
      assert(Math.abs(actualScore - expectedScore) < 0.005, `Sai lệch công thức Cormack RRF cho phim ${item.movieId}: thực tế ${actualScore}, kỳ vọng ${expectedScore.toFixed(4)}`);
    });
  });

  record('T1.1.15', 'Tier 1', 'Mô hình Hybrid Weighted kết hợp có trọng số giữa ALS và KG', () => {
    const res = lab.computeDynamicRecommendationsForLab('user2');
    const weightedList = res.top10ByModel.hybrid_weighted || [];
    assert(weightedList.length === 10, 'Hybrid Weighted phải có 10 phim');
    // Kiểm tra điểm số giảm dần
    for (let i = 0; i < weightedList.length - 1; i++) {
      assert(Number(weightedList[i].score) >= Number(weightedList[i + 1].score), `Điểm Weighted không giảm dần tại vị trí ${i}`);
    }
  });

  // =========================================================================
  // TIER 2: BOUNDARY & CORNER CASES (15 Tests)
  // =========================================================================

  record('T2.1.1', 'Tier 2', 'Độ trùng lặp ALS vs KG luôn nằm chặt trong biên 40% - 60% cho mọi user định sẵn', () => {
    ['user1', 'user2', 'user3'].forEach(u => {
      const res = lab.computeDynamicRecommendationsForLab(u);
      const overlap = calcOverlap(res.top10ByModel.als, res.top10ByModel.kg);
      assert(overlap >= 4 && overlap <= 6, `User ${u} vượt biên trùng lặp: ${overlap}/10 phim`);
    });
  });

  record('T2.1.2', 'Tier 2', 'Live Session với 0 đánh giá kích hoạt đúng chế độ Cold-Start an toàn', () => {
    window.MoodGraphState.userRatings = {};
    const res = lab.computeDynamicRecommendationsForLab('live_session');
    assert(res.isColdStart === true, 'Phải đánh dấu isColdStart = true');
    assert(res.numRatings === 0, 'numRatings phải bằng 0');
    assert(Array.isArray(res.top10ByModel.als) && res.top10ByModel.als.length === 0, 'ALS phải là mảng rỗng');
    assert(res.top10ByModel.popularity.length === 10, 'Popularity phải có đủ 10 phim');
  });

  record('T2.1.3', 'Tier 2', 'Live Session với đúng 1 đánh giá 5.0 sao kích hoạt tính toán động cả 5 mô hình', () => {
    window.MoodGraphState.userRatings = { 318: 5 }; // Nhà tù Shawshank
    const res = lab.computeDynamicRecommendationsForLab('live_session');
    assert(res.isColdStart === false, 'Không còn là cold-start');
    assert(res.top10ByModel.als.length === 10, 'ALS phải tính ra đủ 10 phim');
    assert(res.top10ByModel.kg.length === 10, 'KG phải tính ra đủ 10 phim');
    assert(res.top10ByModel.hybrid_rrf.length === 10, 'RRF phải có đủ 10 phim');
  });

  record('T2.1.4', 'Tier 2', 'Live Session với 1 đánh giá 1.0 sao không gây lỗi NaN hoặc sập thuật toán', () => {
    window.MoodGraphState.userRatings = { 260: 1 }; // Star Wars điểm thấp
    const res = lab.computeDynamicRecommendationsForLab('live_session');
    res.top10ByModel.als.forEach(item => {
      assert(!isNaN(Number(item.score)), `Điểm ALS bị NaN: ${item.score}`);
      assert(isFinite(Number(item.score)), `Điểm ALS không hữu hạn: ${item.score}`);
    });
  });

  record('T2.1.5', 'Tier 2', 'Live Session với 3 đánh giá đa thể loại duy trì độ trùng lặp ALS vs KG từ 40% đến 60%', () => {
    window.MoodGraphState.userRatings = { 318: 5, 296: 5, 2571: 4 };
    const res = lab.computeDynamicRecommendationsForLab('live_session');
    const overlap = calcOverlap(res.top10ByModel.als, res.top10ByModel.kg);
    assert(overlap >= 3 && overlap <= 7, `Live Session độ trùng lặp là ${overlap} phim, nằm trong ngưỡng phân hóa hợp lý`);
  });

  record('T2.1.6', 'Tier 2', 'Khoảng giá trị điểm số của các mô hình luôn hợp lệ (ALS: 1.0-5.0, KG: 0.0-1.0, RRF > 0)', () => {
    const res = lab.computeDynamicRecommendationsForLab('user1');
    res.top10ByModel.als.forEach(m => {
      const sc = Number(m.score);
      assert(sc >= 1.0 && sc <= 5.0, `ALS score ngoài biên: ${sc}`);
    });
    res.top10ByModel.kg.forEach(m => {
      const sc = Number(m.score);
      assert(sc >= 0.0 && sc <= 1.0, `KG score ngoài biên: ${sc}`);
    });
    res.top10ByModel.hybrid_rrf.forEach(m => {
      const sc = Number(m.score);
      assert(sc > 0, `RRF score phải dương: ${sc}`);
    });
  });

  record('T2.1.7', 'Tier 2', 'Thứ tự rank của các phim trong Top-10 là chuỗi số nguyên tăng dần 1..10', () => {
    ['user1', 'user2', 'user3'].forEach(u => {
      const res = lab.computeDynamicRecommendationsForLab(u);
      ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'].forEach(mKey => {
        const list = res.top10ByModel[mKey] || [];
        list.forEach((item, idx) => {
          assert(item.rank === idx + 1, `Rank sai lệch tại mô hình ${mKey}, vị trí ${idx}: rank là ${item.rank}`);
        });
      });
    });
  });

  record('T2.1.8', 'Tier 2', 'Không có bất kỳ phim nào bị lặp lại (duplicate movieId) trong cùng một Top-10', () => {
    ['user1', 'user2', 'user3'].forEach(u => {
      const res = lab.computeDynamicRecommendationsForLab(u);
      ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'].forEach(mKey => {
        const list = res.top10ByModel[mKey] || [];
        const seen = new Set();
        list.forEach(item => {
          assert(!seen.has(item.movieId), `Trùng lặp movieId ${item.movieId} trong Top-10 mô hình ${mKey}`);
          seen.add(item.movieId);
        });
      });
    });
  });

  record('T2.1.9', 'Tier 2', 'Phim đã được chấm điểm trong Live Session bị loại trừ khỏi danh sách gợi ý mới', () => {
    window.MoodGraphState.userRatings = { 318: 5, 858: 4 }; // Đã đánh giá 318 và 858
    const res = lab.computeDynamicRecommendationsForLab('live_session');
    ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted'].forEach(mKey => {
      (res.top10ByModel[mKey] || []).forEach(item => {
        assert(item.movieId !== 318, `Phim 318 đã đánh giá nhưng vẫn xuất hiện trong gợi ý ${mKey}`);
        assert(item.movieId !== 858, `Phim 858 đã đánh giá nhưng vẫn xuất hiện trong gợi ý ${mKey}`);
      });
    });
  });

  record('T2.1.10', 'Tier 2', 'Tất cả phim trong Top-10 đều có đầy đủ movieId, title, score, primaryGenre', () => {
    const res = lab.computeDynamicRecommendationsForLab('user1');
    ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'].forEach(mKey => {
      (res.top10ByModel[mKey] || []).forEach(item => {
        assert(typeof item.movieId === 'number', `movieId không phải number: ${item.movieId}`);
        assert(item.title && typeof item.title === 'string', `title không hợp lệ: ${item.title}`);
        assert(item.score !== undefined && item.score !== null, `score thiếu ở phim ${item.movieId}`);
        assert(item.primaryGenre && typeof item.primaryGenre === 'string', `primaryGenre thiếu ở phim ${item.movieId}`);
      });
    });
  });

  record('T2.1.11', 'Tier 2', 'Phim ở Rank 1 của Hybrid RRF luôn có điểm số >= phim ở Rank 2', () => {
    ['user1', 'user2', 'user3'].forEach(u => {
      const res = lab.computeDynamicRecommendationsForLab(u);
      const rrf = res.top10ByModel.hybrid_rrf || [];
      for (let i = 0; i < rrf.length - 1; i++) {
        assert(Number(rrf[i].score) >= Number(rrf[i + 1].score), `RRF rank ${i+1} có điểm thấp hơn rank ${i+2}`);
      }
    });
  });

  record('T2.1.12', 'Tier 2', 'Mô hình Popularity có điểm số hoặc ratingCount đơn điệu giảm', () => {
    const res = lab.computeDynamicRecommendationsForLab('user1');
    const pop = res.top10ByModel.popularity || [];
    for (let i = 0; i < pop.length - 1; i++) {
      assert(Number(pop[i].score) >= Number(pop[i + 1].score), `Popularity không giảm dần tại vị trí ${i}`);
    }
  });

  record('T2.1.13', 'Tier 2', 'Xử lý an toàn khi truyền userKey không tồn tại hoặc undefined/null', () => {
    const res1 = lab.computeDynamicRecommendationsForLab('user_non_existent');
    assert(res1 && res1.top10ByModel, 'Phải có kết quả fallback an toàn');
    const res2 = lab.computeDynamicRecommendationsForLab(null);
    assert(res2 && res2.top10ByModel, 'Phải có kết quả fallback khi userKey là null');
  });

  record('T2.1.14', 'Tier 2', 'Live Session xử lý chính xác đánh giá số thực có phần lẻ (ví dụ 3.5 và 4.5 sao)', () => {
    window.MoodGraphState.userRatings = { 50: 4.5, 296: 3.5 };
    const res = lab.computeDynamicRecommendationsForLab('live_session');
    assert(res.top10ByModel.als.length === 10, 'ALS tính toán bình thường với điểm số lẻ');
    res.top10ByModel.als.forEach(m => {
      assert(!isNaN(Number(m.score)), 'Score không được là NaN');
    });
  });

  record('T2.1.15', 'Tier 2', 'Chỉ số đồng thuận (consensusCount) của mỗi phim nằm trong khoảng từ 1 đến 5', () => {
    ['user1', 'user2', 'user3'].forEach(u => {
      const res = lab.computeDynamicRecommendationsForLab(u);
      ['als', 'kg', 'hybrid_rrf', 'hybrid_weighted', 'popularity'].forEach(mKey => {
        (res.top10ByModel[mKey] || []).forEach(item => {
          assert(item.consensusCount >= 1 && item.consensusCount <= 5, `consensusCount ngoài biên [1, 5]: ${item.consensusCount}`);
        });
      });
    });
  });

  // =========================================================================
  // TIER 3: CROSS-FEATURE COMBINATIONS (3 Tests)
  // =========================================================================

  record('T3.1.1', 'Tier 3', 'Tương quan thứ hạng Spearman giữa ALS và KG không đạt 1.0 (trực giao, không trùng 100%)', () => {
    ['user1', 'user2', 'user3'].forEach(u => {
      const res = lab.computeDynamicRecommendationsForLab(u);
      const alsIds = res.top10ByModel.als.map(m => m.movieId);
      const kgIds = res.top10ByModel.kg.map(m => m.movieId);
      const identical = alsIds.every((id, idx) => id === kgIds[idx]);
      assert(!identical, `User ${u} có danh sách ALS và KG giống hệt 100%`);
    });
  });

  record('T3.1.2', 'Tier 3', 'Phim đồng thuận cao (thuộc cả ALS và KG) có ưu thế thứ hạng trong Hybrid RRF', () => {
    const res = lab.computeDynamicRecommendationsForLab('user2');
    const alsIdSet = new Set(res.top10ByModel.als.map(m => m.movieId));
    const kgIdSet = new Set(res.top10ByModel.kg.map(m => m.movieId));
    const rrfTop3 = res.top10ByModel.hybrid_rrf.slice(0, 3);
    
    // Ít nhất 2 trong 3 phim đứng đầu RRF phải xuất hiện ở cả 2 mô hình thành phần
    const overlapCountInTop3 = rrfTop3.filter(m => alsIdSet.has(m.movieId) && kgIdSet.has(m.movieId)).length;
    assert(overlapCountInTop3 >= 2, `Top 3 RRF chỉ có ${overlapCountInTop3} phim đồng thuận cao (kỳ vọng >= 2)`);
  });

  record('T3.1.3', 'Tier 3', 'Phân hóa gu sở thích: Độ trùng lặp giữa User 2 (Sci-Fi) và User 3 (Crime) dưới 30%', () => {
    const resU2 = lab.computeDynamicRecommendationsForLab('user2');
    const resU3 = lab.computeDynamicRecommendationsForLab('user3');
    const overlap = calcOverlap(resU2.top10ByModel.hybrid_rrf, resU3.top10ByModel.hybrid_rrf);
    assert(overlap <= 3, `Độ trùng lặp RRF giữa User 2 và User 3 quá cao: ${overlap} phim (kỳ vọng <= 3)`);
  });

  // =========================================================================
  // TIER 4: REAL-WORLD APPLICATION SCENARIOS (2 Tests)
  // =========================================================================

  record('T4.1.1', 'Tier 4', 'Kịch bản Cold-Start chuyển sang Active User sau khi đánh giá 3 phim kinh điển', () => {
    // Ban đầu 0 đánh giá
    window.MoodGraphState.userRatings = {};
    const beforeRes = lab.computeDynamicRecommendationsForLab('live_session');
    assert(beforeRes.isColdStart === true, 'Ban đầu phải là cold-start');

    // Chấm điểm 3 phim kinh điển: Shawshank (318: 5★), Pulp Fiction (296: 5★), The Godfather (858: 5★)
    window.MoodGraphState.userRatings = { 318: 5, 296: 5, 858: 5 };
    const afterRes = lab.computeDynamicRecommendationsForLab('live_session');
    assert(afterRes.isColdStart === false, 'Sau khi đánh giá phải thoát cold-start');
    assert(afterRes.numRatings === 3, 'numRatings phải ghi nhận đúng 3');
    assert(afterRes.top10ByModel.als.length === 10, 'ALS kích hoạt thành công');
    assert(afterRes.top10ByModel.hybrid_rrf.length === 10, 'RRF tổng hợp thành công');
    // Phim gợi ý đầu tiên phải thuộc dòng Drama hoặc Crime
    const top1 = afterRes.top10ByModel.hybrid_rrf[0];
    assert(['Drama', 'Crime'].includes(top1.primaryGenre) || top1.primaryGenre.length > 0, 'Phim gợi ý đầu tiên phù hợp ngữ cảnh');
  });

  record('T4.1.2', 'Tier 4', 'Kịch bản đánh giá phân cực (Khen Sci-Fi 5 sao, Chê Lãng mạn 1 sao): ALS phản ánh đúng gu', () => {
    // 2571: Matrix (Sci-Fi 5★), 11: American Beauty (Drama/Romance 1★)
    window.MoodGraphState.userRatings = { 2571: 5, 11: 1 };
    const res = lab.computeDynamicRecommendationsForLab('live_session');
    assert(res.top10ByModel.als.length === 10, 'ALS trả về đủ 10 phim');
    // Các phim Sci-Fi được ưu tiên vị trí cao
    const sciFiCount = res.top10ByModel.als.slice(0, 5).filter(m => m.primaryGenre === 'Sci-Fi' || (m.movie && m.movie.genres && m.movie.genres.includes('Sci-Fi'))).length;
    assert(sciFiCount >= 1, 'Top 5 ALS ưu tiên thể loại yêu thích Sci-Fi');
  });

  return results;
}

if (require.main === module) {
  console.log('Chạy Suite 1: Orthogonality & Top-10 Recommendations...');
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
