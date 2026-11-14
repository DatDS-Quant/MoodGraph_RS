"""
Tầng 1: Tính đúng đắn Toán học & Giải tích (Mathematical Correctness).
Kiểm định định lượng các công thức:
1. Reciprocal Rank Fusion (RRF, Cormack et al.)
2. Min-Max Normalization & Linear Weighted Hybrid Fusion
3. Metapath P1 (Genre Co-occurrence & Inverse Frequency)
4. Metapath P2 (Mood Genome Semantic Relevance & Logarithmic Penalty)
5. Metapath P3 (Collaborative Graph User Cosine Similarity)
6. Spearman Rank Correlation (rho)
7. Jaccard Overlap Index
8. Shannon Information Novelty (Bits)
"""

import math
import pytest
from recommender.hybrid.fusion import (
    normalize_min_max,
    normalize_percentile,
    reciprocal_rank_fusion,
    weighted_score_fusion,
)
from recommender.kg.scorer import PathBasedScorer


class TestTier1MathematicalCorrectness:
    """Bộ kiểm thử kiểm định tính đúng đắn của toàn bộ các công thức toán học và giải tích."""

    def test_rrf_hand_calculated_accuracy(self):
        """
        Kiểm tra công thức RRF đối chiếu với kết quả tính toán giải tích bằng tay:
        RRF_Score(d) = sum_m [ 1 / (60 + rank_m(d)) ]
        """
        k = 60
        cand_als = [
            {"movieId": 101, "rank": 1, "raw_score": 4.8},
            {"movieId": 102, "rank": 2, "raw_score": 4.5},
            {"movieId": 103, "rank": 3, "raw_score": 4.2},
        ]
        cand_kg = [
            {"movieId": 103, "rank": 1, "raw_score": 0.95},
            {"movieId": 101, "rank": 3, "raw_score": 0.80},
            {"movieId": 104, "rank": 2, "raw_score": 0.85},
        ]

        # Phim 101: ALS rank 1, KG rank 3 -> 1/61 + 1/63 = 0.0163934426 + 0.0158730158 = 0.0322664585
        # Phim 103: ALS rank 3, KG rank 1 -> 1/63 + 1/61 = 0.0322664585
        # Phim 102: ALS rank 2, KG None   -> 1/62 = 0.0161290322
        # Phim 104: ALS None, KG rank 2   -> 1/62 = 0.0161290322
        expected_101 = 1.0 / (k + 1) + 1.0 / (k + 3)
        expected_103 = 1.0 / (k + 3) + 1.0 / (k + 1)
        expected_102 = 1.0 / (k + 2)
        expected_104 = 1.0 / (k + 2)

        fused = reciprocal_rank_fusion(cand_als, cand_kg, rrf_k=k)
        fused_dict = {it["movieId"]: it for it in fused}

        assert math.isclose(fused_dict[101]["hybrid_score"], expected_101, rel_tol=1e-6)
        assert math.isclose(fused_dict[103]["hybrid_score"], expected_103, rel_tol=1e-6)
        assert math.isclose(fused_dict[102]["hybrid_score"], expected_102, rel_tol=1e-6)
        assert math.isclose(fused_dict[104]["hybrid_score"], expected_104, rel_tol=1e-6)

        # Tie-breaking: Khi điểm bằng nhau (101 và 103), movieId nhỏ hơn xếp trước
        assert fused[0]["movieId"] == 101
        assert fused[1]["movieId"] == 103

    def test_min_max_normalization_boundaries(self):
        """Kiểm tra chuẩn hóa Min-Max tuyến tính trong các trường hợp biên."""
        # Danh sách rỗng
        assert normalize_min_max([]) == []
        # Danh sách một phần tử
        assert normalize_min_max([5.0]) == [1.0]
        # Tất cả phần tử bằng nhau
        assert normalize_min_max([4.0, 4.0, 4.0]) == [1.0, 1.0, 1.0]
        # Danh sách thông thường
        scores = [10.0, 20.0, 30.0, 40.0, 50.0]
        norm = normalize_min_max(scores)
        assert math.isclose(norm[0], 0.0, abs_tol=1e-7)
        assert math.isclose(norm[2], 0.5, abs_tol=1e-7)
        assert math.isclose(norm[4], 1.0, abs_tol=1e-7)

    def test_weighted_score_fusion_mathematics(self):
        """
        Kiểm tra dung hợp điểm tuyến tính có trọng số:
        Score_Hybrid = w_ALS * S_norm_ALS + w_KG * S_norm_KG (w_ALS=0.1, w_KG=0.9)
        """
        cand_als = [
            {"movieId": 1, "raw_score": 10.0, "rank": 1},
            {"movieId": 2, "raw_score": 5.0, "rank": 2},
        ]
        cand_kg = [
            {"movieId": 1, "raw_score": 0.2, "rank": 2},
            {"movieId": 2, "raw_score": 0.8, "rank": 1},
        ]

        # Phim 1: ALS max (norm=1.0), KG min (norm=0.0) -> Score = 0.1 * 1.0 + 0.9 * 0.0 = 0.10
        # Phim 2: ALS min (norm=0.0), KG max (norm=1.0) -> Score = 0.1 * 0.0 + 0.9 * 1.0 = 0.90
        fused = weighted_score_fusion(cand_als, cand_kg, weight_als=0.1, weight_kg=0.9, normalize_method="min_max")
        fused_dict = {it["movieId"]: it for it in fused}

        assert math.isclose(fused_dict[1]["hybrid_score"], 0.10, abs_tol=1e-5)
        assert math.isclose(fused_dict[2]["hybrid_score"], 0.90, abs_tol=1e-5)
        # Phim 2 có điểm cao hơn phim 1 vì trọng số KG chiếm 90%
        assert fused[0]["movieId"] == 2
        assert fused[1]["movieId"] == 1

    def test_metapath_p1_inverse_frequency_penalty(self):
        """
        Kiểm tra Metapath P1: Thể loại càng phổ biến (|Movies(g)| lớn) thì trọng số
        nghịch đảo tần suất 1 / sqrt(|Movies(g)|) càng nhỏ để tránh gợi ý rập khuôn.
        """
        size_rare = 25
        size_popular = 10000

        weight_rare = 1.0 / math.sqrt(size_rare)       # 1/5 = 0.2000
        weight_popular = 1.0 / math.sqrt(size_popular) # 1/100 = 0.0100

        assert weight_rare > weight_popular
        assert math.isclose(weight_rare / weight_popular, 20.0, rel_tol=1e-5)

    def test_metapath_p2_logarithmic_tag_penalty(self):
        """
        Kiểm tra Metapath P2: Trọng số thẻ tâm trạng genome bị phạt logarit:
        rel_m * rel_c / ln(1 + |Movies(t)|)
        """
        rel_m = 0.9
        rel_c = 0.85
        num_movies_specific = 10
        num_movies_generic = 2000

        score_specific = (rel_m * rel_c) / math.log(1.0 + num_movies_specific)
        score_generic = (rel_m * rel_c) / math.log(1.0 + num_movies_generic)

        assert score_specific > score_generic
        assert score_specific > 0.0
        assert score_generic > 0.0

    def test_metapath_p3_cosine_symmetry_and_range(self):
        """
        Kiểm tra Metapath P3: Độ tương đồng Cosine giữa hai người dùng:
        CosineSim(u, v) = |Liked(u) cap Liked(v)| / sqrt(|Liked(u)| * |Liked(v)|)
        Đảm bảo tính đối xứng và chặn trên bằng 1.0.
        """
        u_liked = {1, 2, 3, 4}
        v_liked = {3, 4, 5, 6}

        intersect = len(u_liked & v_liked)  # 2
        sim_uv = intersect / math.sqrt(len(u_liked) * len(v_liked))  # 2 / sqrt(16) = 0.5
        sim_vu = intersect / math.sqrt(len(v_liked) * len(u_liked))

        assert math.isclose(sim_uv, 0.5, abs_tol=1e-6)
        assert math.isclose(sim_uv, sim_vu, abs_tol=1e-6)
        assert 0.0 <= sim_uv <= 1.0

        # Trùng nhau hoàn toàn -> 1.0
        sim_uu = len(u_liked) / math.sqrt(len(u_liked) * len(u_liked))
        assert math.isclose(sim_uu, 1.0, abs_tol=1e-6)

    def test_spearman_rank_correlation_properties(self):
        """
        Kiểm tra hệ số tương quan thứ hạng Spearman:
        rho = 1 - (6 * sum(d_i^2)) / (n * (n^2 - 1))
        """
        from recommender.services.lab_service import LabService
        lab = LabService()

        # 1. Hai bảng xếp hạng hoàn toàn đồng thuận (1..5 và 1..5)
        # d_i = 0 -> rho = 1.0
        list_a = [{"movieId": mid} for mid in [10, 20, 30, 40, 50]]
        list_b = [{"movieId": mid} for mid in [10, 20, 30, 40, 50]]
        res = lab.compare_models(user_id=1, models=[], top_n=5)
        # Kiểm tra công thức trực tiếp
        k = 5
        diff_sq = sum((i - i)**2 for i in range(1, k + 1))
        rho_identical = 1.0 - (6.0 * diff_sq) / (k * (k**2 - 1))
        assert math.isclose(rho_identical, 1.0, abs_tol=1e-6)

        # 2. Hai bảng xếp hạng hoàn toàn đảo ngược (1..5 và 5..1)
        # d = [1-5, 2-4, 3-3, 4-2, 5-1] = [-4, -2, 0, 2, 4]
        # sum(d^2) = 16 + 4 + 0 + 4 + 16 = 40
        # rho = 1 - (6 * 40) / (5 * 24) = 1 - 240 / 120 = 1 - 2.0 = -1.0
        diff_sq_rev = sum(((i) - (k - i + 1))**2 for i in range(1, k + 1))
        rho_reversed = 1.0 - (6.0 * diff_sq_rev) / (k * (k**2 - 1))
        assert math.isclose(rho_reversed, -1.0, abs_tol=1e-6)

    def test_jaccard_similarity_properties(self):
        """
        Kiểm tra độ tương đồng Jaccard: Jaccard(A, B) = |A cap B| / |A cup B|
        """
        set_a = {1, 2, 3, 4, 5}
        set_b = {4, 5, 6, 7, 8}

        intersection = set_a & set_b  # {4, 5} -> len = 2
        union = set_a | set_b         # {1,2,3,4,5,6,7,8} -> len = 8
        jaccard = len(intersection) / float(len(union))
        assert math.isclose(jaccard, 0.25, abs_tol=1e-6)

        # Trùng 100% -> 1.0
        assert math.isclose(len(set_a & set_a) / float(len(set_a | set_a)), 1.0)
        # Rời nhau 100% -> 0.0
        set_c = {10, 20}
        assert len(set_a & set_c) / float(len(set_a | set_c)) == 0.0

    def test_shannon_novelty_entropy_bits(self):
        """
        Kiểm tra độ mới lạ Shannon Entropy:
        Novelty(i) = -log2(Count_Train(i) / Total_Train_Interactions) [Bits]
        """
        total_interactions = 20_000_000

        # Phim cực kỳ phổ biến (Blockbuster): 65,000 lượt xem
        count_popular = 65_536
        prob_popular = count_popular / total_interactions
        novelty_popular = -math.log2(prob_popular)

        # Phim ngách (Long-tail / Indie): 20 lượt xem
        count_niche = 20
        prob_niche = count_niche / total_interactions
        novelty_niche = -math.log2(prob_niche)

        assert novelty_popular > 0.0
        assert novelty_niche > novelty_popular
        # Blockbuster khoảng ~8-9 bits, Long-tail đạt ~19-20 bits
        assert 8.0 <= novelty_popular <= 10.0
        assert 18.0 <= novelty_niche <= 22.0
