"""
MoodGraph - Task 3A: Spark ALS
Mô-đun: M04 - Cơ sở lý thuyết ALS, Kiểm chứng Toy Fit & Kiểm toán nhân tố ẩn.

Mô-đun này triển khai nền tảng toán học của Phân rã Ma trận (Matrix Factorization)
bằng thuật toán Alternating Least Squares (ALS) trên phản hồi hiện (explicit feedback):
1. Bộ giải tham chiếu toán học chính xác thuần Python/NumPy (không phụ thuộc Spark).
2. Ví dụ mẫu chuẩn (Golden Example) tính tay từng bước cập nhật tham số.
3. Huấn luyện mô hình PySpark ALS trên toy data, trích xuất nhân tố và so khớp tích vô hướng.
4. Kiểm toán hành vi Cold-Start (chiến lược coldStartStrategy 'nan' vs 'drop').
5. Phân tích hình học nhân tố ẩn: Phản ví dụ khoảng cách Euclidean vs tích vô hướng (Dot Product).
"""

import math
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

if sys.platform.startswith("win"):
    if os.path.exists(r"C:\hadoop"):
        os.environ["HADOOP_HOME"] = r"C:\hadoop"
        os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

import numpy as np
from pyspark.ml.recommendation import ALS, ALSModel
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, StructField, StructType


# ==============================================================================
# I. DETERMINISTIC TOY DATASET
# ==============================================================================

TOY_USERS: Dict[int, Dict[str, Any]] = {
    1: {"name": "An", "type": "warm"},
    2: {"name": "Binh", "type": "warm"},
    3: {"name": "Chi", "type": "warm"},
    4: {"name": "Dung", "type": "warm"},
    5: {"name": "Em", "type": "warm"},
    6: {"name": "Cold_User", "type": "cold"},  # 0 train ratings
}

TOY_MOVIES: Dict[int, Dict[str, Any]] = {
    101: {"title": "Movie_A", "type": "warm"},
    102: {"title": "Movie_B", "type": "warm"},
    103: {"title": "Movie_C", "type": "warm"},
    104: {"title": "Movie_D", "type": "warm"},
    105: {"title": "Movie_E", "type": "warm"},
    106: {"title": "Movie_F", "type": "warm"},
    107: {"title": "Cold_Movie", "type": "cold"},  # 0 train ratings
}

# (userId, movieId, rating)
TOY_TRAIN_RATINGS: List[Tuple[int, int, float]] = [
    # Golden example block (Users 1 & 2 on Movies 101, 102, 103)
    (1, 101, 2.0),
    (1, 102, 4.0),
    (1, 104, 3.5),
    (1, 105, 5.0),
    (2, 101, 1.0),
    (2, 102, 2.0),
    (2, 103, 1.5),
    (2, 104, 2.0),
    (2, 106, 3.0),
    # Additional warm users and movies
    (3, 102, 3.0),
    (3, 103, 4.0),
    (3, 105, 4.5),
    (3, 106, 2.5),
    (4, 101, 4.0),
    (4, 103, 3.0),
    (4, 104, 4.5),
    (4, 105, 2.0),
    (5, 101, 2.5),
    (5, 102, 3.5),
    (5, 104, 1.0),
    (5, 106, 4.0),
]


# ==============================================================================
# II. PURE PYTHON / NUMPY MATHEMATICAL ALS REFERENCE
# ==============================================================================

def compute_dot_product(user_vector: np.ndarray, item_vector: np.ndarray) -> float:
    """
    Tính điểm dự đoán bằng tích vô hướng: r_hat = p_u^T q_i.
    
    Args:
        user_vector: Mảng numpy 1D kích thước (rank,)
        item_vector: Mảng numpy 1D kích thước (rank,)
        
    Returns:
        Giá trị float vô hướng biểu diễn sở thích dự đoán.
    """
    u_vec = np.asarray(user_vector, dtype=np.float64).ravel()
    i_vec = np.asarray(item_vector, dtype=np.float64).ravel()
    if u_vec.shape[0] != i_vec.shape[0]:
        raise ValueError(
            f"Dimension mismatch: user vector shape {u_vec.shape} vs item vector shape {i_vec.shape}"
        )
    return float(np.dot(u_vec, i_vec))


def compute_als_loss(
    ratings: List[Tuple[int, int, float]],
    user_factors: Dict[int, np.ndarray],
    item_factors: Dict[int, np.ndarray],
    reg_param: float,
) -> float:
    """
    Tính giá trị hàm tổn thất chính xác của ALS trên explicit feedback:
    L = sum_{(u, i) in R} (r_{u,i} - p_u^T q_i)^2 + lambda * (sum_u ||p_u||_2^2 + sum_i ||q_i||_2^2)
    
    Các ô chưa quan sát hoàn toàn bị bỏ qua (KHÔNG coi là bằng 0).
    """
    squared_error_sum = 0.0
    for u, i, r in ratings:
        if u in user_factors and i in item_factors:
            pred = compute_dot_product(user_factors[u], item_factors[i])
            err = r - pred
            squared_error_sum += err * err

    user_reg_sum = sum(
        float(np.sum(np.square(vec))) for vec in user_factors.values()
    )
    item_reg_sum = sum(
        float(np.sum(np.square(vec))) for vec in item_factors.values()
    )

    total_loss = squared_error_sum + reg_param * (user_reg_sum + item_reg_sum)
    return float(total_loss)


def als_update_user_factors(
    ratings_by_user: Dict[int, List[Tuple[int, float]]],
    item_factors: Dict[int, np.ndarray],
    rank: int,
    reg_param: float,
) -> Dict[int, np.ndarray]:
    """
    Thực hiện bước cập nhật nghiệm giải tích ridge regression cho toàn bộ user khi cố định item factors:
    p_u = ( sum_{i in I_u} q_i q_i^T + lambda * I_k )^{-1} ( sum_{i in I_u} r_{u,i} q_i )
    """
    new_user_factors: Dict[int, np.ndarray] = {}
    eye_k = np.eye(rank, dtype=np.float64)

    for u, rated_items in ratings_by_user.items():
        if not rated_items:
            new_user_factors[u] = np.zeros(rank, dtype=np.float64)
            continue

        v_matrix = np.zeros((rank, rank), dtype=np.float64)
        d_vector = np.zeros(rank, dtype=np.float64)

        for i, r in rated_items:
            if i in item_factors:
                q_i = item_factors[i].reshape(rank, 1)
                v_matrix += q_i @ q_i.T
                d_vector += r * item_factors[i].ravel()

        lhs = v_matrix + reg_param * eye_k
        rhs = d_vector
        p_u = np.linalg.solve(lhs, rhs)
        new_user_factors[u] = p_u.ravel()

    return new_user_factors


def als_update_item_factors(
    ratings_by_item: Dict[int, List[Tuple[int, float]]],
    user_factors: Dict[int, np.ndarray],
    rank: int,
    reg_param: float,
) -> Dict[int, np.ndarray]:
    """
    Thực hiện bước cập nhật nghiệm giải tích ridge regression cho toàn bộ item khi cố định user factors:
    q_i = ( sum_{u in U_i} p_u p_u^T + lambda * I_k )^{-1} ( sum_{u in U_i} r_{u,i} p_u )
    """
    new_item_factors: Dict[int, np.ndarray] = {}
    eye_k = np.eye(rank, dtype=np.float64)

    for i, user_ratings in ratings_by_item.items():
        if not user_ratings:
            new_item_factors[i] = np.zeros(rank, dtype=np.float64)
            continue

        w_matrix = np.zeros((rank, rank), dtype=np.float64)
        c_vector = np.zeros(rank, dtype=np.float64)

        for u, r in user_ratings:
            if u in user_factors:
                p_u = user_factors[u].reshape(rank, 1)
                w_matrix += p_u @ p_u.T
                c_vector += r * user_factors[u].ravel()

        lhs = w_matrix + reg_param * eye_k
        rhs = c_vector
        q_i = np.linalg.solve(lhs, rhs)
        new_item_factors[i] = q_i.ravel()

    return new_item_factors


def run_toy_als_reference(
    ratings: List[Tuple[int, int, float]],
    rank: int = 2,
    max_iter: int = 15,
    reg_param: float = 0.05,
    seed: int = 42,
) -> Tuple[Dict[int, np.ndarray], Dict[int, np.ndarray], List[float]]:
    """
    Thực thi bộ giải ALS tham chiếu độc lập trên tập ratings hiện.
    
    Returns:
        (user_factors, item_factors, loss_history)
    """
    rng = np.random.default_rng(seed)

    # Index ratings
    ratings_by_user: Dict[int, List[Tuple[int, float]]] = {}
    ratings_by_item: Dict[int, List[Tuple[int, float]]] = {}
    all_users = set()
    all_items = set()

    for u, i, r in ratings:
        all_users.add(u)
        all_items.add(i)
        ratings_by_user.setdefault(u, []).append((i, r))
        ratings_by_item.setdefault(i, []).append((u, r))

    # Initialize item factors randomly
    item_factors: Dict[int, np.ndarray] = {
        i: rng.normal(loc=0.5, scale=0.1, size=rank).astype(np.float64)
        for i in all_items
    }
    user_factors: Dict[int, np.ndarray] = {
        u: np.zeros(rank, dtype=np.float64) for u in all_users
    }

    loss_history: List[float] = []
    initial_loss = compute_als_loss(ratings, user_factors, item_factors, reg_param)
    loss_history.append(initial_loss)

    for _ in range(max_iter):
        # Update user factors holding items fixed
        user_factors = als_update_user_factors(
            ratings_by_user, item_factors, rank, reg_param
        )
        # Update item factors holding users fixed
        item_factors = als_update_item_factors(
            ratings_by_item, user_factors, rank, reg_param
        )
        current_loss = compute_als_loss(ratings, user_factors, item_factors, reg_param)
        loss_history.append(current_loss)

    return user_factors, item_factors, loss_history


def verify_golden_example_step() -> Dict[str, float]:
    """
    Tính toán và kiểm chứng từng bước của Ví dụ mẫu chuẩn (Golden Example):
    - Người dùng: An (1), Binh (2)
    - Phim: A (101), B (102), C (103)
    - Đánh giá: An -> A:2, B:4; Binh -> A:1, B:2, C:1.5
    - Nhân tố phim khởi tạo: q_A = [1.0], q_B = [2.0], q_C = [1.5]
    - lambda = 0.0, rank = 1
    
    Returns:
        Từ điển chứa các giá trị trung gian và điểm dự đoán sau bước cập nhật.
    """
    q_A = 1.0
    q_B = 2.0
    q_C = 1.5

    # 1. Update p_An:
    # Denominator: q_A^2 + q_B^2 = 1 + 4 = 5.0
    # Numerator: r_{An,A} * q_A + r_{An,B} * q_B = 2(1) + 4(2) = 10.0
    p_An = 10.0 / 5.0  # = 2.0

    # 2. Update p_Binh:
    # Denominator: q_A^2 + q_B^2 + q_C^2 = 1 + 4 + 2.25 = 7.25
    # Numerator: r_{Binh,A} * q_A + r_{Binh,B} * q_B + r_{Binh,C} * q_C = 1(1) + 2(2) + 1.5(1.5) = 7.25
    p_Binh = 7.25 / 7.25  # = 1.0

    # 3. Update q_C holding user factors fixed:
    # Movie C only rated by Binh (r = 1.5)
    # Denominator: p_Binh^2 = 1.0^2 = 1.0
    # Numerator: r_{Binh,C} * p_Binh = 1.5 * 1.0 = 1.5
    q_C_updated = 1.5 / 1.0  # = 1.5

    # 4. Predict rating for An on unseen Movie C:
    # r_hat_{An, C} = p_An * q_C = 2.0 * 1.5 = 3.0
    pred_An_on_C = p_An * q_C_updated

    return {
        "p_An": p_An,
        "p_Binh": p_Binh,
        "q_C_updated": q_C_updated,
        "pred_An_on_C": pred_An_on_C,
    }


# ==============================================================================
# III. PYSPARK ALS INTEGRATION & FACTOR EXTRACTION
# ==============================================================================

def create_toy_spark_dataframe(
    spark: SparkSession,
    ratings_data: Optional[List[Tuple[int, int, float]]] = None,
) -> DataFrame:
    """
    Chuyển đổi danh sách tuple đánh giá thô thành Spark DataFrame có định kiểu rõ ràng.
    """
    data = ratings_data if ratings_data is not None else TOY_TRAIN_RATINGS
    schema = StructType([
        StructField("userId", IntegerType(), nullable=False),
        StructField("movieId", IntegerType(), nullable=False),
        StructField("rating", DoubleType(), nullable=False),
    ])
    rows = [(int(u), int(m), float(r)) for u, m, r in data]
    return spark.createDataFrame(rows, schema=schema)


def fit_spark_toy_als(
    spark_df: DataFrame,
    rank: int = 2,
    max_iter: int = 15,
    reg_param: float = 0.05,
    seed: int = 42,
    cold_start_strategy: str = "nan",
) -> ALSModel:
    """
    Khớp mô hình PySpark ALS trên toy DataFrame.
    """
    als = ALS(
        userCol="userId",
        itemCol="movieId",
        ratingCol="rating",
        implicitPrefs=False,
        rank=rank,
        maxIter=max_iter,
        regParam=reg_param,
        seed=seed,
        coldStartStrategy=cold_start_strategy,
    )
    return als.fit(spark_df)


def extract_factors(
    model: ALSModel,
) -> Tuple[Dict[int, np.ndarray], Dict[int, np.ndarray]]:
    """
    Trích xuất ma trận nhân tố người dùng và phim từ ALSModel sang từ điển Python.
    
    Returns:
        (user_factors_dict, item_factors_dict) với khóa là ID và giá trị là mảng numpy 1D.
    """
    user_factors_df = model.userFactors
    item_factors_df = model.itemFactors

    user_factors: Dict[int, np.ndarray] = {}
    for row in user_factors_df.collect():
        user_factors[int(row["id"])] = np.array(row["features"], dtype=np.float64)

    item_factors: Dict[int, np.ndarray] = {}
    for row in item_factors_df.collect():
        item_factors[int(row["id"])] = np.array(row["features"], dtype=np.float64)

    return user_factors, item_factors


def verify_spark_vs_manual_dot(
    model: ALSModel,
    spark_df: DataFrame,
    tolerance: float = 1e-4,
) -> Dict[str, Any]:
    """
    Kiểm toán kết quả dự đoán của Spark transform so với tích vô hướng thủ công:
    predicted_spark = model.transform(spark_df)
    predicted_manual = p_u^T q_i
    """
    user_factors, item_factors = extract_factors(model)
    predictions_df = model.transform(spark_df).select("userId", "movieId", "rating", "prediction")
    rows = predictions_df.collect()

    diffs: List[Dict[str, Any]] = []
    max_abs_diff = 0.0
    sum_abs_diff = 0.0

    for r in rows:
        u = int(r["userId"])
        m = int(r["movieId"])
        spark_pred = float(r["prediction"]) if r["prediction"] is not None else float("nan")

        if u in user_factors and m in item_factors:
            manual_pred = compute_dot_product(user_factors[u], item_factors[m])
            diff = abs(spark_pred - manual_pred)
            max_abs_diff = max(max_abs_diff, diff)
            sum_abs_diff += diff
            diffs.append({
                "userId": u,
                "movieId": m,
                "true_rating": float(r["rating"]),
                "spark_prediction": spark_pred,
                "manual_dot": manual_pred,
                "abs_diff": diff,
                "matched": diff <= tolerance,
            })
        else:
            diffs.append({
                "userId": u,
                "movieId": m,
                "true_rating": float(r["rating"]),
                "spark_prediction": spark_pred,
                "manual_dot": None,
                "abs_diff": float("inf"),
                "matched": False,
            })

    num_samples = len(rows)
    mean_abs_diff = sum_abs_diff / num_samples if num_samples > 0 else 0.0
    all_matched = all(d["matched"] for d in diffs)

    return {
        "num_samples": num_samples,
        "max_abs_diff": max_abs_diff,
        "mean_abs_diff": mean_abs_diff,
        "tolerance": tolerance,
        "all_matched": all_matched,
        "details": diffs,
    }


def demonstrate_cold_start_difference(
    model_nan: ALSModel,
    model_drop: ALSModel,
    cold_df: DataFrame,
) -> Dict[str, Any]:
    """
    Kiểm toán hành vi coldStartStrategy='nan' vs 'drop' trên các cặp người dùng/phim chưa từng xuất hiện.
    """
    nan_pred_df = model_nan.transform(cold_df).select("userId", "movieId", "prediction")
    drop_pred_df = model_drop.transform(cold_df).select("userId", "movieId", "prediction")

    nan_rows = nan_pred_df.collect()
    drop_rows = drop_pred_df.collect()

    nan_count = len(nan_rows)
    drop_count = len(drop_rows)
    input_count = cold_df.count()

    nan_null_or_nan_count = sum(
        1 for r in nan_rows if r["prediction"] is None or math.isnan(float(r["prediction"]))
    )

    return {
        "input_row_count": input_count,
        "nan_strategy_output_count": nan_count,
        "nan_strategy_unscorable_count": nan_null_or_nan_count,
        "drop_strategy_output_count": drop_count,
        "dropped_rows_count": input_count - drop_count,
        "evaluation_implication": (
            "coldStartStrategy='drop' silently drops unscorable evaluation rows, which artificially "
            "inflates Top-N recall/precision if the evaluation engine does not preserve the true total "
            "denominator of test targets. Using 'nan' keeps the rows, allowing explicit detection and "
            "correct penalty assignment."
        ),
    }


# ==============================================================================
# IV. LATENT FACTOR GEOMETRY: EUCLIDEAN VS DOT PRODUCT COUNTEREXAMPLE
# ==============================================================================

def verify_euclidean_vs_dot_product_counterexample() -> Dict[str, Any]:
    """
    Chứng minh toán học bằng phản ví dụ: Vì sao khoảng cách gần Euclidean trong không gian ẩn
    KHÔNG THỂ thay thế cho tích vô hướng lớn (p_u^T q_i) trong việc xếp hạng ALS.
    """
    p_u = np.array([2.0, 0.0], dtype=np.float64)
    q_1 = np.array([2.1, 0.1], dtype=np.float64)
    q_2 = np.array([5.0, 0.0], dtype=np.float64)

    dist_1 = float(np.linalg.norm(p_u - q_1))
    dist_2 = float(np.linalg.norm(p_u - q_2))

    dot_1 = float(np.dot(p_u, q_1))
    dot_2 = float(np.dot(p_u, q_2))

    # Item 1 is closer in Euclidean space (dist_1 < dist_2), but Item 2 has higher dot product (dot_2 > dot_1)
    is_counterexample_valid = (dist_1 < dist_2) and (dot_2 > dot_1)

    return {
        "p_u": p_u.tolist(),
        "q_1": q_1.tolist(),
        "q_2": q_2.tolist(),
        "euclidean_dist_item1": dist_1,
        "euclidean_dist_item2": dist_2,
        "dot_product_item1": dot_1,
        "dot_product_item2": dot_2,
        "is_counterexample_valid": is_counterexample_valid,
        "explanation": (
            "Item 1 is geometrically closer to User in latent space (distance 0.14 vs 3.00), "
            "yet Item 2 yields more than double the predicted rating (dot product 10.00 vs 4.20). "
            "Recommendation rank in ALS depends on dot product, which scales with vector norm, "
            "not Euclidean distance."
        ),
    }

