"""
Giao diện suy luận gợi ý phim bằng mô hình Spark ALS (Task 3A - Module M10).

Đầu vào: ID người dùng (userId chuẩn int64), số lượng phim cần gợi ý (Top-N/K).
Đầu ra: Danh sách bản ghi ALSRecommendationItem sắp xếp theo điểm số giảm dần.
Cơ chế: Sử dụng phép nhân ma trận BLAS trên CPU, nén lịch sử Train qua CSR
để lọc phim đã xem trong thời gian microsecond, và trả về danh sách rỗng cho người dùng mới.
"""

from __future__ import annotations

import math
import os
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import numpy as np
import pyarrow.parquet as pq

from recommender.als.candidates import (
    ALSCandidateConfig,
    ALSCandidateGenerator,
    ScoreableCatalog,
    UserFactorsContainer,
)
from recommender.als.evaluator import validate_k


# Đường dẫn mặc định trong kho lưu trữ
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_FROZEN_MODEL_DIR = _REPO_ROOT / "artifacts" / "models" / "als" / "m07_tuning" / "ALS_R8_REG0.3_ITER10"
_DEFAULT_MOVIES_PATH = _REPO_ROOT / "data" / "processed" / "core" / "movies"
_DEFAULT_TRAIN_PATH = _REPO_ROOT / "data" / "processed" / "splits" / "train"
_DEFAULT_VAL_PATH = _REPO_ROOT / "data" / "processed" / "splits" / "validation"
_DEFAULT_TRAIN_CSR_PATH = _REPO_ROOT / "artifacts" / "als" / "m10" / "train_seen_csr.npz"


@dataclass(frozen=True)
class ALSRecommendationItem:
    """
    Bản ghi dữ liệu đầu ra chuẩn hóa cho một phim được gợi ý bởi ALS.
    Sử dụng định danh 64-bit gốc của MovieLens (userId, movieId).
    """
    userId: int
    movieId: int
    raw_score: float
    rank: int
    model_name: str = "ALS"
    model_version: str = "ALS_R8_REG0.3_ITER10"
    run_id: Optional[str] = None

    def __post_init__(self) -> None:
        # Kiểm tra tính hợp lệ của kiểu dữ liệu và giá trị số học
        if not isinstance(self.userId, (int, np.integer)):
            raise TypeError(f"userId must be int, got {type(self.userId)}")
        if not isinstance(self.movieId, (int, np.integer)):
            raise TypeError(f"movieId must be int, got {type(self.movieId)}")
        if not math.isfinite(self.raw_score):
            raise ValueError(f"raw_score must be a finite float, got {self.raw_score}")
        if self.rank < 1:
            raise ValueError(f"rank must be >= 1, got {self.rank}")

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi bản ghi sang dictionary chuẩn để phục vụ serialization/JSON."""
        return {
            "userId": int(self.userId),
            "movieId": int(self.movieId),
            "raw_score": float(self.raw_score),
            "rank": int(self.rank),
            "model_name": str(self.model_name),
            "model_version": str(self.model_version),
            "run_id": self.run_id,
        }


@dataclass(frozen=True)
class ModelMetadata:
    """
    Thông tin siêu dữ liệu (metadata) của mô hình ALS đã đăng ký trong hệ thống.
    """
    model_id: str
    model_name: str
    model_family: str
    version: str
    canonical_artifact_path: str
    rank: int
    reg_param: float
    max_iter: int
    num_user_factors: int
    num_item_factors: int
    training_split_provenance: str
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Xuất metadata sang dictionary."""
        return asdict(self)


class ALSModelRegistry:
    """
    Bộ quản lý đăng ký và tra cứu các phiên bản mô hình ALS phục vụ suy luận.
    """

    def __init__(self, repo_root: Optional[Union[str, Path]] = None) -> None:
        root = Path(repo_root) if repo_root else _REPO_ROOT
        self.root = root
        # Danh mục đăng ký mô hình finalist đã đóng băng từ Sprint M07
        self._registry: Dict[str, ModelMetadata] = {
            "ALS_R8_REG0.3_ITER10": ModelMetadata(
                model_id="ALS_R8_REG0.3_ITER10",
                model_name="Frozen_Spark_ALS_Champion",
                model_family="ALS_ONLY",
                version="ALS_R8_REG0.3_ITER10",
                canonical_artifact_path=str(root / "artifacts" / "models" / "als" / "m07_tuning" / "ALS_R8_REG0.3_ITER10").replace("\\", "/"),
                rank=8,
                reg_param=0.3,
                max_iter=10,
                num_user_factors=162541,
                num_item_factors=58932,
                training_split_provenance="data/processed/splits/train (24,675,013 ratings, seed=42)",
                limitations=[
                    "Cold users (not in Train) have no factors and cannot be scored.",
                    "Unscoreable movies (3,491 movies with 0 train ratings) cannot be recommended.",
                    "Raw scores are unconstrained dot products, not probabilities or clipped ratings.",
                    "Subject to Long-Tail Fluke Bias if unblended with popularity or graph signals.",
                ],
            ),
            "M05_ALS_R16_REG0.1_ITER10": ModelMetadata(
                model_id="M05_ALS_R16_REG0.1_ITER10",
                model_name="Spark_ALS_M05_Baseline",
                model_family="ALS_ONLY",
                version="M05_ALS_R16_REG0.1_ITER10",
                canonical_artifact_path=str(root / "artifacts" / "models" / "als" / "m05_spark_als_rank16").replace("\\", "/"),
                rank=16,
                reg_param=0.1,
                max_iter=10,
                num_user_factors=162541,
                num_item_factors=58932,
                training_split_provenance="data/processed/splits/train (24,675,013 ratings)",
                limitations=["Superseded by M07 champion ALS_R8_REG0.3_ITER10."],
            ),
        }

    def get_model_metadata(self, model_version: Optional[str] = None) -> ModelMetadata:
        """Tra cứu metadata theo phiên bản mô hình; mặc định là finalist ALS_R8_REG0.3_ITER10."""
        key = model_version or "ALS_R8_REG0.3_ITER10"
        if key not in self._registry:
            raise KeyError(
                f"Model version '{key}' not registered. Available: {list(self._registry.keys())}"
            )
        return self._registry[key]

    def list_models(self) -> List[Dict[str, Any]]:
        """Liệt kê toàn bộ danh sách các mô hình ALS đã đăng ký."""
        return [m.to_dict() for m in self._registry.values()]


class ALSDeliveryService:
    """
    Dịch vụ suy luận gợi ý ALS hiệu năng cao, tối ưu bộ nhớ cho môi trường phục vụ.
    Nạp sẵn ma trận vector tiềm ẩn vào RAM để tính điểm nhanh qua thư viện BLAS.
    """

    def __init__(
        self,
        model_dir: Optional[Union[str, Path]] = None,
        movies_parquet_path: Optional[Union[str, Path]] = None,
        train_parquet_path: Optional[Union[str, Path]] = None,
        val_parquet_path: Optional[Union[str, Path]] = None,
        train_csr_path: Optional[Union[str, Path]] = None,
        batch_size: int = 2500,
        model_version: str = "ALS_R8_REG0.3_ITER10",
    ) -> None:
        self.model_dir = Path(model_dir) if model_dir else _DEFAULT_FROZEN_MODEL_DIR
        self.movies_path = Path(movies_parquet_path) if movies_parquet_path else _DEFAULT_MOVIES_PATH
        self.train_path = Path(train_parquet_path) if train_parquet_path else _DEFAULT_TRAIN_PATH
        self.val_path = Path(val_parquet_path) if val_parquet_path else _DEFAULT_VAL_PATH
        self.train_csr_path = Path(train_csr_path) if train_csr_path else _DEFAULT_TRAIN_CSR_PATH
        self.batch_size = batch_size
        self.model_version = model_version

        # 1. Khởi tạo Candidate Generator và nạp factor ma trận vào RAM
        self.generator = ALSCandidateGenerator(
            ALSCandidateConfig(k_list=(5, 10, 20), batch_size=batch_size, model_version=model_version)
        )
        self.generator.load_catalog_and_factors(
            model_dir=self.model_dir,
            movies_parquet_path=self.movies_path if self.movies_path.exists() else None,
        )

        # 2. Bộ nhớ đệm chỉ số CSR và lịch sử tương tác đã xem
        self._csr_offsets: Optional[np.ndarray] = None
        self._csr_mids: Optional[np.ndarray] = None
        self._train_seen_cache: Optional[Dict[int, Set[int]]] = None
        self._test_seen_cache: Optional[Dict[int, Set[int]]] = None

    @property
    def rank(self) -> int:
        """Số chiều của không gian tiềm ẩn (Latent Factor Rank)."""
        return self.generator.catalog.rank

    @property
    def num_scoreable_items(self) -> int:
        """Số lượng phim có vector tiềm ẩn để tính điểm (58,932 phim)."""
        return self.generator.catalog.num_movies

    @property
    def num_known_users(self) -> int:
        """Số lượng người dùng đã học được vector trong tập Train (162,541 users)."""
        return self.generator.user_factors.num_users

    def _load_csr_if_available(self) -> bool:
        """Nạp chỉ số CSR nén của lịch sử tương tác Train nếu file tồn tại."""
        if self._csr_offsets is not None and self._csr_mids is not None:
            return True
        if self.train_csr_path.exists():
            data = np.load(self.train_csr_path)
            self._csr_offsets = data["offsets"]
            self._csr_mids = data["movie_ids"]
            return True
        return False

    def get_train_seen_for_user(self, user_id: int) -> Set[int]:
        """Truy xuất toàn bộ danh sách phim đã xem trong Train của 1 user theo thời gian microsecond."""
        if self._load_csr_if_available():
            if self._csr_offsets is not None and self._csr_mids is not None:
                if 1 <= user_id < len(self._csr_offsets):
                    start = self._csr_offsets[user_id]
                    end = self._csr_offsets[user_id + 1]
                    return set(self._csr_mids[start:end].tolist())
                return set()
        return self._get_train_seen().get(user_id, set())

    def _get_train_seen(self) -> Dict[int, Set[int]]:
        """
        Tải lười toàn bộ lịch sử xem của tập Train từ file CSR hoặc file Parquet phân vùng.
        Nghiêm cấm tự ý chuyển hướng sang fixture mẫu trong môi trường sản xuất.
        """
        if self._train_seen_cache is None:
            if self._load_csr_if_available():
                if self._csr_offsets is not None and self._csr_mids is not None:
                    histories: Dict[int, Set[int]] = {}
                    num_users = len(self._csr_offsets) - 1
                    for u in range(1, num_users):
                        start = self._csr_offsets[u]
                        end = self._csr_offsets[u + 1]
                        if end > start:
                            histories[u] = set(self._csr_mids[start:end].tolist())
                    self._train_seen_cache = histories
                    return self._train_seen_cache

            if not self.train_path.exists():
                raise FileNotFoundError(
                    f"Full Train split data not found at {self.train_path} or {self.train_csr_path}. "
                    "Refusing to fall back to partial sample fixtures in production serving."
                )
            tbl = pq.read_table(self.train_path, columns=["userId", "movieId"])
            uids = tbl["userId"].to_numpy()
            mids = tbl["movieId"].to_numpy()
            histories: Dict[int, Set[int]] = {}
            for u, m in zip(uids, mids):
                u_int = int(u)
                if u_int not in histories:
                    histories[u_int] = set()
                histories[u_int].add(int(m))
            self._train_seen_cache = histories
        return self._train_seen_cache

    def _get_test_stage_seen(self) -> Dict[int, Set[int]]:
        """
        Tải lịch sử xem phục vụ đánh giá giai đoạn Test (gồm Train + Validation).
        Tuyệt đối không truy cập rating mục tiêu của tập Test để chống rò rỉ dữ liệu.
        """
        if self._test_seen_cache is None:
            combined = {k: set(v) for k, v in self._get_train_seen().items()}
            if self.val_path.exists():
                tbl_val = pq.read_table(self.val_path, columns=["userId", "movieId"])
                v_uids = tbl_val["userId"].to_numpy()
                v_mids = tbl_val["movieId"].to_numpy()
                for u, m in zip(v_uids, v_mids):
                    u_int = int(u)
                    if u_int not in combined:
                        combined[u_int] = set()
                    combined[u_int].add(int(m))
            self._test_seen_cache = combined
        return self._test_seen_cache

    def get_seen_history(
        self,
        user_ids: Sequence[int],
        stage: str = "production",
        custom_histories: Optional[Dict[int, Set[int]]] = None,
    ) -> Dict[int, Set[int]]:
        """Lấy tập hợp phim đã xem cho danh sách người dùng theo ngữ cảnh vận hành cụ thể."""
        if custom_histories is not None:
            return {uid: custom_histories.get(uid, set()) for uid in user_ids}

        if stage in ("production", "validation"):
            if self._load_csr_if_available() and self._csr_offsets is not None and self._csr_mids is not None:
                res: Dict[int, Set[int]] = {}
                num_offsets = len(self._csr_offsets)
                for uid in user_ids:
                    if 1 <= uid < num_offsets:
                        start = self._csr_offsets[uid]
                        end = self._csr_offsets[uid + 1]
                        res[uid] = set(self._csr_mids[start:end].tolist())
                    else:
                        res[uid] = set()
                return res
            train_seen = self._get_train_seen()
            return {uid: train_seen.get(uid, set()) for uid in user_ids}
        elif stage == "test":
            test_seen = self._get_test_stage_seen()
            return {uid: test_seen.get(uid, set()) for uid in user_ids}
        else:
            raise ValueError(f"Unknown stage: {stage}")
            raise ValueError(f"Unknown stage '{stage}'. Must be one of ['production', 'validation', 'test']")

    def recommend(
        self,
        user_id: int,
        top_n: int = 20,
        stage: str = "production",
        custom_seen: Optional[Set[int]] = None,
        run_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Sinh danh sách Top-N gợi ý cho một người dùng đơn lẻ.
        Xử lý Cold-Start: Trả về danh sách rỗng [] nếu người dùng chưa từng có tương tác trong Train.
        """
        if top_n <= 0:
            raise ValueError(f"top_n must be positive, got {top_n}")

        batch_result = self.recommend_batch(
            user_ids=[user_id],
            top_n=top_n,
            stage=stage,
            custom_user_histories={user_id: custom_seen} if custom_seen is not None else None,
            run_id=run_id,
        )
        return batch_result.get(user_id, [])

    def recommend_batch(
        self,
        user_ids: Sequence[int],
        top_n: int = 20,
        stage: str = "production",
        custom_user_histories: Optional[Dict[int, Set[int]]] = None,
        run_id: Optional[str] = None,
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Sinh danh sách Top-N gợi ý cho một lô (batch) người dùng thông qua phép nhân ma trận BLAS.
        Đảm bảo thứ tự xếp hạng chính xác: raw_score giảm dần, tie-break bằng movieId tăng dần.
        """
        if top_n <= 0:
            raise ValueError(f"top_n must be positive, got {top_n}")
        if not user_ids:
            return {}

        active_run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
        user_id_list = [int(u) for u in user_ids]

        # Phân chia người dùng thành nhóm đã biết (có factors) và nhóm cold-start
        known_user_factors = self.generator.user_factors
        known_uids = [u for u in user_id_list if u in known_user_factors.user_to_idx]
        cold_uids = [u for u in user_id_list if u not in known_user_factors.user_to_idx]

        results: Dict[int, List[Dict[str, Any]]] = {}

        # 1. Người dùng mới (Cold-Start): Trả về danh sách rỗng theo hợp đồng minh bạch
        for u in cold_uids:
            results[u] = []

        if not known_uids:
            return results

        # 2. Lấy lịch sử phim đã xem để chuẩn bị loại trừ
        user_histories = self.get_seen_history(
            user_ids=known_uids, stage=stage, custom_histories=custom_user_histories
        )

        # 3. Tính điểm qua BLAS và chọn Top-K bằng thuật toán phân vùng O(N)
        raw_recs = self.generator.generate_recommendations(
            target_user_ids=known_uids,
            user_histories=user_histories,
            k=top_n,
            batch_size=self.batch_size,
        )

        # 4. Đóng gói kết quả vào đối tượng ALSRecommendationItem chuẩn
        for uid in known_uids:
            item_list = raw_recs.get(uid, [])
            formatted_items: List[Dict[str, Any]] = []
            for rank_idx, (mid, score) in enumerate(item_list, start=1):
                rec_item = ALSRecommendationItem(
                    userId=uid,
                    movieId=int(mid),
                    raw_score=float(score),
                    rank=rank_idx,
                    model_name="ALS",
                    model_version=self.model_version,
                    run_id=active_run_id,
                )
                formatted_items.append(rec_item.to_dict())
            results[uid] = formatted_items

        return results


# Thể hiện singleton của dịch vụ suy luận ở cấp module
_SERVICE_INSTANCE: Optional[ALSDeliveryService] = None


def get_delivery_service(
    model_dir: Optional[Union[str, Path]] = None,
    movies_path: Optional[Union[str, Path]] = None,
) -> ALSDeliveryService:
    """Lấy hoặc khởi tạo thể hiện singleton của ALSDeliveryService."""
    global _SERVICE_INSTANCE
    if _SERVICE_INSTANCE is None:
        _SERVICE_INSTANCE = ALSDeliveryService(
            model_dir=model_dir, movies_parquet_path=movies_path
        )
    return _SERVICE_INSTANCE


def recommend_als(
    user_id: int,
    top_n: int = 20,
    k: Optional[int] = None,
    filter_seen: bool = True,
    stage: str = "production",
    model_version: Optional[str] = None,
    service: Optional[ALSDeliveryService] = None,
    custom_seen: Optional[Set[int]] = None,
) -> List[Dict[str, Any]]:
    """
    Giao diện hàm công khai: Sinh danh sách Top-N gợi ý cho một người dùng.
    Hỗ trợ linh hoạt cả tham số 'top_n' và alias 'k'. Có thể tắt lọc phim đã xem bằng filter_seen=False.
    """
    effective_top_n = k if k is not None else top_n
    svc = service or get_delivery_service()
    effective_custom_seen = custom_seen if filter_seen else set()
    return svc.recommend(
        user_id=user_id, top_n=effective_top_n, stage=stage, custom_seen=effective_custom_seen
    )


def recommend_als_batch(
    user_ids: Sequence[int],
    top_n: int = 20,
    k: Optional[int] = None,
    filter_seen: bool = True,
    stage: str = "production",
    model_version: Optional[str] = None,
    service: Optional[ALSDeliveryService] = None,
    custom_user_histories: Optional[Dict[int, Set[int]]] = None,
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Giao diện hàm công khai: Sinh danh sách Top-N gợi ý cho một lô (batch) người dùng.
    Hỗ trợ linh hoạt cả tham số 'top_n' và alias 'k'. Có thể tắt lọc phim đã xem bằng filter_seen=False.
    """
    effective_top_n = k if k is not None else top_n
    svc = service or get_delivery_service()
    effective_histories = (
        custom_user_histories if filter_seen else {u: set() for u in user_ids}
    )
    return svc.recommend_batch(
        user_ids=user_ids,
        top_n=effective_top_n,
        stage=stage,
        custom_user_histories=effective_histories,
    )


# ==============================================================================
# HÀM ORACLE TỔNG HỢP PHỤC VỤ KIỂM THỬ ĐỘC LẬP
# ==============================================================================

def synthetic_delivery_oracle(
    user_factor: np.ndarray,
    item_factors: np.ndarray,
    movie_ids: np.ndarray,
    seen_movie_ids: Set[int],
    top_n: int,
) -> List[Dict[str, Any]]:
    """
    Hàm đối chiếu tham chiếu (Oracle): Tính tích vô hướng vô hướng tuần tự,
    lọc phim đã xem và sắp xếp tất định theo (-score, movieId) để đối soát thuật toán phân vùng.
    """
    if user_factor.ndim != 1 or item_factors.ndim != 2:
        raise ValueError("Invalid factor dimensions")
    if user_factor.shape[0] != item_factors.shape[1]:
        raise ValueError("Rank mismatch between user and item factors")

    candidates: List[Tuple[float, int]] = []
    seen = set(seen_movie_ids)
    for idx, mid in enumerate(movie_ids):
        mid_int = int(mid)
        if mid_int in seen:
            continue
        # Tích vô hướng Python thuần
        score = float(sum(float(u) * float(v) for u, v in zip(user_factor, item_factors[idx])))
        candidates.append((score, mid_int))

    # Sắp xếp tất định: Điểm giảm dần, tie-break bằng ID phim tăng dần
    candidates.sort(key=lambda x: (-x[0], x[1]))

    out: List[Dict[str, Any]] = []
    for rank, (score, mid) in enumerate(candidates[:top_n], start=1):
        item = ALSRecommendationItem(
            userId=1,
            movieId=mid,
            raw_score=score,
            rank=rank,
            model_name="ALS",
            model_version="SYNTHETIC_ORACLE",
        )
        out.append(item.to_dict())
    return out
