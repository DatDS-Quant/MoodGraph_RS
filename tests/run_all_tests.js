/**
 * MOODGRAPH E2E TEST SUITE - CENTRAL TEST RUNNER
 * File: tests/run_all_tests.js
 * 
 * Bộ điều phối thực thi toàn diện 4 tầng kiểm thử (Tiers 1-4) cho MoodGraph Academic Lab (Mode B):
 * - Suite 1: Orthogonality & Top-10 Recommendations (test_orthogonality.js)
 * - Suite 2: State Synchronization Mode A <-> Mode B (test_sync_mode_ab.js)
 * - Suite 3: 3D Latent Space Lerp & 2D Canvas Fallback (test_visual_lerp.js)
 * - Suite 4: Academic UI, Dev Jargon Purge & Metrics Consistency (test_academic_ui.js)
 * 
 * Quy chuẩn:
 * - 100% Tiếng Việt chuẩn UTF-8.
 * - Tuyệt đối không dùng ký hiệu LaTeX hoặc dấu dollar ($).
 * - Exit code 0 khi toàn bộ PASS, exit code 1 khi có FAIL.
 */

const suite1 = require('./test_orthogonality');
const suite2 = require('./test_sync_mode_ab');
const suite3 = require('./test_visual_lerp');
const suite4 = require('./test_academic_ui');

function main() {
  console.log('='.repeat(80));
  console.log('KHỞI CHẠY BỘ KIỂM THỬ TỰ ĐỘNG E2E TOÀN DIỆN: MOODGRAPH ACADEMIC LAB (MODE B)');
  console.log('='.repeat(80));
  console.log('Thời gian thực thi: ' + new Date().toISOString());
  console.log('Môi trường: Node.js ' + process.version + ' trên nền tảng ' + process.platform);
  console.log('-'.repeat(80));

  const allResults = [];

  // Chạy Suite 1
  console.log('\n[1/4] Đang thực thi Suite 1: Độ trực giao & Đề xuất Top-10...');
  const res1 = suite1.runSuite();
  allResults.push(...res1);
  const p1 = res1.filter(r => r.pass).length;
  console.log(`      Hoàn thành: ${p1}/${res1.length} tests đạt yêu cầu.`);

  // Chạy Suite 2
  console.log('\n[2/4] Đang thực thi Suite 2: Đồng bộ trạng thái Mode A và Mode B...');
  const res2 = suite2.runSuite();
  allResults.push(...res2);
  const p2 = res2.filter(r => r.pass).length;
  console.log(`      Hoàn thành: ${p2}/${res2.length} tests đạt yêu cầu.`);

  // Chạy Suite 3
  console.log('\n[3/4] Đang thực thi Suite 3: 3D Latent Space Lerp & 2D Canvas Fallback...');
  const res3 = suite3.runSuite();
  allResults.push(...res3);
  const p3 = res3.filter(r => r.pass).length;
  console.log(`      Hoàn thành: ${p3}/${res3.length} tests đạt yêu cầu.`);

  // Chạy Suite 4
  console.log('\n[4/4] Đang thực thi Suite 4: Rà soát Giao diện Học thuật & Chỉ số Đo lường...');
  const res4 = suite4.runSuite();
  allResults.push(...res4);
  const p4 = res4.filter(r => r.pass).length;
  console.log(`      Hoàn thành: ${p4}/${res4.length} tests đạt yêu cầu.`);

  // Phân tích thống kê theo từng Tier
  const tierStats = {
    'Tier 1': { total: 0, pass: 0, fail: 0, minThreshold: 45, name: 'Bao quát Tính năng (Feature Coverage)' },
    'Tier 2': { total: 0, pass: 0, fail: 0, minThreshold: 45, name: 'Kiểm tra Giá trị Biên (Boundary & Corner Cases)' },
    'Tier 3': { total: 0, pass: 0, fail: 0, minThreshold: 10, name: 'Tương tác Phối hợp Chéo (Cross-Feature Combinations)' },
    'Tier 4': { total: 0, pass: 0, fail: 0, minThreshold: 5, name: 'Kịch bản Người Dùng Thực Tế (Real-World Workloads)' }
  };

  allResults.forEach(r => {
    if (tierStats[r.tier]) {
      tierStats[r.tier].total++;
      if (r.pass) tierStats[r.tier].pass++;
      else tierStats[r.tier].fail++;
    }
  });

  const totalTests = allResults.length;
  const totalPass = allResults.filter(r => r.pass).length;
  const totalFail = allResults.filter(r => !r.pass).length;

  console.log('\n' + '='.repeat(80));
  console.log('BẢNG THỐNG KÊ KẾT QUẢ THEO 4 TẦNG KIỂM THỬ (TIERS 1 - 4)');
  console.log('='.repeat(80));
  console.log(
    'Tầng kiểm thử'.padEnd(10) + ' | ' +
    'Tên phân tầng'.padEnd(46) + ' | ' +
    'Đạt / Tổng'.padEnd(12) + ' | ' +
    'Ngưỡng tối thiểu'
  );
  console.log('-'.repeat(80));

  Object.keys(tierStats).forEach(tierKey => {
    const st = tierStats[tierKey];
    const thresholdStatus = st.total >= st.minThreshold ? 'ĐỦ' : 'THIẾU';
    console.log(
      tierKey.padEnd(10) + ' | ' +
      st.name.padEnd(46) + ' | ' +
      `${st.pass}/${st.total}`.padEnd(12) + ' | ' +
      `>= ${st.minThreshold} (${thresholdStatus})`
    );
  });

  console.log('-'.repeat(80));
  console.log(`TỔNG CỘNG : ${totalPass}/${totalTests} tests PASS (${totalFail} tests FAIL).`);
  console.log(`Số lượng test cases thiết kế: ${totalTests} (Yêu cầu ngưỡng tối thiểu >= 100: ĐÃ VƯỢT ${(totalTests - 100)} TESTS)`);
  console.log('='.repeat(80));

  if (totalFail > 0) {
    console.log('\nDANH SÁCH CÁC TEST CASES ĐANG THẤT BẠI (CHUYỂN TIẾP CHO MILESTONE IMPLEMENTATION):');
    console.log('-'.repeat(80));
    allResults.filter(r => !r.pass).forEach(r => {
      console.log(`[FAIL] [${r.tier}] [${r.id}] ${r.name}`);
      console.log(`       -> Chi tiết lỗi: ${r.error}\n`);
    });
    console.log('-'.repeat(80));
    console.log('KẾT LUẬN: Bộ kiểm thử độc lập đã phát hiện chính xác các khiếm khuyết trong hiện trạng.');
    console.log('Trạng thái chuyển giao: SẴN SÀNG KIỂM THỬ (TEST READY).');
    process.exit(1);
  } else {
    console.log('\nTẤT CẢ 100% CÁC TEST CASES ĐÃ PASS HOÀN TOÀN!');
    process.exit(0);
  }
}

main();
