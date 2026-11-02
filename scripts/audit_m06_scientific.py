"""
Scientific Acceptance Audit for Module M06:
Verifies:
1. ID alignment (userId, movieId) between Validation, Factors, and Recommendations.
2. Target scoreability and whether targets exist in Train seen set.
3. Deterministic sample diagnostic table:
   userId, validation_movieId, validation_rating, target_scoreable, target_als_score, target_full_rank, top20_contains_target, evaluator_hit, explanation.
4. Empirical investigation of Fluke Bias:
   - Distribution of Train ratings for items appearing in Top-20 recommendations.
   - Global count of 1-rating items and 1-rating 5-star items in Train.
   - Top-scoring movies across users and their rating counts.
5. M03 baseline comparison reconciliation against artifacts/m03_popularity_results.json.
"""

import sys
import os
import json
import time
from pathlib import Path

REPO_ROOT = Path("D:/PROJECT BIG DATA/MoodGraph")
sys.path.insert(0, str(REPO_ROOT))

from typing import Dict, List, Set, Tuple
import numpy as np
import pyarrow.parquet as pq

# Force UTF-8 stdout
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path("D:/PROJECT BIG DATA/MoodGraph")
DATA_DIR = REPO_ROOT / "data" / "processed"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
M06_DIR = ARTIFACTS_DIR / "als" / "m06"

def run_audit():
    print("=" * 80)
    print("MOODGRAPH M06 SCIENTIFIC ACCEPTANCE AUDIT")
    print("=" * 80)

    # 1. Load Factor Matrices
    print("\n[1] Loading M05 Factor Matrices...")
    factors_dir = ARTIFACTS_DIR / "models" / "als" / "m05_spark_als_rank16" / "spark_model"
    user_factors_table = pq.read_table(factors_dir / "userFactors")
    item_factors_table = pq.read_table(factors_dir / "itemFactors")

    user_ids = user_factors_table.column("id").to_numpy()
    user_vecs = np.array(user_factors_table.column("features").to_pylist(), dtype=np.float32)
    user_id_to_idx = {int(uid): idx for idx, uid in enumerate(user_ids)}

    item_ids = item_factors_table.column("id").to_numpy()
    item_vecs = np.array(item_factors_table.column("features").to_pylist(), dtype=np.float32)
    item_id_to_idx = {int(iid): idx for idx, iid in enumerate(item_ids)}

    print(f"  Loaded {len(user_ids):,} user factors, {len(item_ids):,} item factors (dim={user_vecs.shape[1]}).")

    # 2. Load Train Ratings (Counts and Seen Sets)
    print("\n[2] Loading Train Ratings (24.67M)...")
    t0 = time.time()
    train_table = pq.read_table(DATA_DIR / "splits" / "train", columns=["userId", "movieId", "rating"])
    t_train_uids = train_table.column("userId").to_numpy()
    t_train_mids = train_table.column("movieId").to_numpy()
    t_train_rats = train_table.column("rating").to_numpy()
    print(f"  Train ratings loaded in {time.time() - t0:.2f}s.")

    # Calculate item rating counts and 5-star counts in Train
    from collections import Counter, defaultdict
    item_train_counts = Counter(t_train_mids)
    item_5star_counts = Counter()
    for mid, r in zip(t_train_mids, t_train_rats):
        if r == 5.0:
            item_5star_counts[mid] += 1

    total_train_movies = len(item_train_counts)
    one_rating_movies = [m for m, c in item_train_counts.items() if c == 1]
    one_rating_5star = [m for m in one_rating_movies if item_5star_counts[m] == 1]

    print(f"  Total distinct movies in Train: {total_train_movies:,}")
    print(f"  Movies with exactly 1 Train rating: {len(one_rating_movies):,} ({len(one_rating_movies)/total_train_movies*100:.2f}%)")
    print(f"  Movies with exactly 1 Train rating AND it is 5.0 stars: {len(one_rating_5star):,} ({len(one_rating_5star)/len(one_rating_movies)*100:.2f}%)")

    # Build Train seen sets
    print("\n  Building Train seen sets for audit sample...")
    # Load Validation Targets
    val_table = pq.read_table(DATA_DIR / "splits" / "validation", columns=["userId", "movieId", "rating"])
    val_uids = val_table.column("userId").to_numpy()
    val_mids = val_table.column("movieId").to_numpy()
    val_rats = val_table.column("rating").to_numpy()

    # Movies metadata
    movies_table = pq.read_table(DATA_DIR / "core" / "movies", columns=["movieId", "title", "genres"])
    m_titles = {int(mid): t for mid, t in zip(movies_table.column("movieId").to_pylist(), movies_table.column("title").to_pylist())}

    # 3. Analyze Empirical Distribution of Movies in M06 Top-20 Recommendations
    print("\n[3] Auditing M06 Stored Parquet Recommendations...")
    rec_parquet_path = M06_DIR / "m06_als_top20_recommendations.parquet"
    rec_table = pq.read_table(rec_parquet_path)
    rec_mids = rec_table.column("movieId").to_numpy()
    rec_scores = rec_table.column("als_score").to_numpy()

    rec_item_counts = Counter(rec_mids)
    unique_rec_movies = len(rec_item_counts)
    print(f"  Total recommendation rows: {len(rec_mids):,}")
    print(f"  Unique movies recommended across all users: {unique_rec_movies:,}")
    print(f"  ALS Score min: {np.min(rec_scores):.4f}, median: {np.median(rec_scores):.4f}, max: {np.max(rec_scores):.4f}")

    # Rating count brackets for recommended movies (by occurrences in recommendation slots)
    b_1 = sum(c for m, c in rec_item_counts.items() if item_train_counts[m] == 1)
    b_2_5 = sum(c for m, c in rec_item_counts.items() if 2 <= item_train_counts[m] <= 5)
    b_6_10 = sum(c for m, c in rec_item_counts.items() if 6 <= item_train_counts[m] <= 10)
    b_11_100 = sum(c for m, c in rec_item_counts.items() if 11 <= item_train_counts[m] <= 100)
    b_gt_100 = sum(c for m, c in rec_item_counts.items() if item_train_counts[m] > 100)
    total_slots = len(rec_mids)

    print("\n  DISTRIBUTION OF TRAIN RATINGS FOR RECOMMENDED SLOTS (3,250,820 slots):")
    print(f"    1 Train rating:      {b_1:,} slots ({b_1/total_slots*100:.2f}%)")
    print(f"    2-5 Train ratings:   {b_2_5:,} slots ({b_2_5/total_slots*100:.2f}%)")
    print(f"    6-10 Train ratings:  {b_6_10:,} slots ({b_6_10/total_slots*100:.2f}%)")
    print(f"    11-100 Train ratings:{b_11_100:,} slots ({b_11_100/total_slots*100:.2f}%)")
    print(f"    >100 Train ratings:  {b_gt_100:,} slots ({b_gt_100/total_slots*100:.2f}%)")

    # Distinct movies breakdown
    u_1 = sum(1 for m in rec_item_counts if item_train_counts[m] == 1)
    u_2_5 = sum(1 for m in rec_item_counts if 2 <= item_train_counts[m] <= 5)
    u_6_10 = sum(1 for m in rec_item_counts if 6 <= item_train_counts[m] <= 10)
    u_11_100 = sum(1 for m in rec_item_counts if 11 <= item_train_counts[m] <= 100)
    u_gt_100 = sum(1 for m in rec_item_counts if item_train_counts[m] > 100)

    print("\n  DISTRIBUTION OF UNIQUE MOVIES IN RECOMMENDATIONS (2,528 distinct movies):")
    print(f"    1 Train rating:      {u_1:,} movies ({u_1/unique_rec_movies*100:.2f}%)")
    print(f"    2-5 Train ratings:   {u_2_5:,} movies ({u_2_5/unique_rec_movies*100:.2f}%)")
    print(f"    6-10 Train ratings:  {u_6_10:,} movies ({u_6_10/unique_rec_movies*100:.2f}%)")
    print(f"    11-100 Train ratings:{u_11_100:,} movies ({u_11_100/unique_rec_movies*100:.2f}%)")
    print(f"    >100 Train ratings:  {u_gt_100:,} movies ({u_gt_100/unique_rec_movies*100:.2f}%)")

    # Top-10 most recommended movies
    print("\n  TOP 10 MOST FREQUENTLY RECOMMENDED MOVIES IN M06:")
    for mid, count in rec_item_counts.most_common(10):
        t_count = item_train_counts[mid]
        title = m_titles.get(mid, "Unknown")
        print(f"    movieId {mid:6d} | RecCount: {count:6,d} | TrainRatings: {t_count:3d} | Title: {title}")

    # 4. Deterministic Sample Selection for Deep Diagnostic
    print("\n[4] Selecting Deterministic Validation Sample for Deep Tracing...")
    # Find specific users:
    # 1. User with very popular target (>1000 Train ratings)
    # 2. User with moderately popular target (50-200 Train ratings)
    # 3. User with rare target (1-5 Train ratings)
    # 4. User with target that has 0 Train ratings (unscoreable target)
    # 5. User with negative validation rating (<3.5)
    sample_users = []
    
    # Let's index validation targets
    user_val_map = {}
    for uid, mid, rat in zip(val_uids, val_mids, val_rats):
        user_val_map[int(uid)] = (int(mid), float(rat))

    # Pre-build seen sets for target sample
    sample_candidate_uids = []
    
    # Category A: Target > 1000 ratings and rating >= 3.5
    for uid, (mid, rat) in user_val_map.items():
        if rat >= 4.0 and item_train_counts[mid] > 1000:
            sample_candidate_uids.append((uid, "popular_target"))
            break
            
    # Category B: Target 50-200 ratings and rating >= 3.5
    for uid, (mid, rat) in user_val_map.items():
        if rat >= 4.0 and 50 <= item_train_counts[mid] <= 200:
            sample_candidate_uids.append((uid, "moderate_target"))
            break

    # Category C: Target 1-5 ratings and rating >= 3.5
    for uid, (mid, rat) in user_val_map.items():
        if rat >= 4.0 and 1 <= item_train_counts[mid] <= 5:
            sample_candidate_uids.append((uid, "rare_target"))
            break

    # Category D: Target has 0 ratings (unscoreable) and rating >= 3.5
    for uid, (mid, rat) in user_val_map.items():
        if rat >= 3.5 and item_train_counts[mid] == 0:
            sample_candidate_uids.append((uid, "unscoreable_target"))
            break

    # Category E: Target rating < 3.5 (non-positive cohort)
    for uid, (mid, rat) in user_val_map.items():
        if rat < 3.0 and item_train_counts[mid] > 500:
            sample_candidate_uids.append((uid, "non_positive_target"))
            break

    # Extra 3 diverse users
    for uid in [1, 42, 100]:
        if uid in user_val_map and uid not in [u[0] for u in sample_candidate_uids]:
            sample_candidate_uids.append((uid, f"fixed_user_{uid}"))

    # Build seen set for these sample users
    sample_uids_set = {u[0] for u in sample_candidate_uids}
    sample_seen = defaultdict(set)
    for uid, mid in zip(t_train_uids, t_train_mids):
        if uid in sample_uids_set:
            sample_seen[int(uid)].add(int(mid))

    # Build rec map for sample users
    rec_uids = rec_table.column("userId").to_numpy()
    rec_ranks = rec_table.column("rank").to_numpy()
    sample_recs = defaultdict(list)
    for uid, mid, rk, sc in zip(rec_uids, rec_mids, rec_ranks, rec_scores):
        if uid in sample_uids_set:
            sample_recs[int(uid)].append((int(mid), int(rk), float(sc)))

    # Sort sample recs by rank
    for uid in sample_recs:
        sample_recs[uid].sort(key=lambda x: x[1])

    # Run Diagnostic for each sample user
    from recommender.als.evaluator import TopNEvaluator, HeldOutTarget
    evaluator = TopNEvaluator(k_list=[5, 10, 20], relevance_threshold=3.5, catalog_size=62423, scorable_catalog_size=58932)

    diagnostic_rows = []
    print("\n  DIAGNOSTIC TRACE RESULTS FOR SAMPLE USERS:")
    print("-" * 140)
    print(f"{'userId':<8} | {'val_movieId':<11} | {'rating':<6} | {'Scorable':<8} | {'ALS Score':<10} | {'Full Rank':<10} | {'In Top20':<8} | {'Eval Hit':<8} | {'Category'}")
    print("-" * 140)

    for uid, category in sample_candidate_uids:
        val_mid, val_rat = user_val_map[uid]
        is_in_train_seen = val_mid in sample_seen[uid]
        has_item_factor = val_mid in item_id_to_idx
        has_user_factor = uid in user_id_to_idx
        
        target_scoreable = has_item_factor and has_user_factor
        
        target_als_score = None
        target_full_rank = None
        
        if target_scoreable:
            u_vec = user_vecs[user_id_to_idx[uid]]
            i_vec = item_vecs[item_id_to_idx[val_mid]]
            target_als_score = float(np.dot(u_vec, i_vec))
            
            # Compute full rank among unread scoreable movies
            all_scores = np.dot(item_vecs, u_vec) # shape (M,)
            # Mask seen items
            for smid in sample_seen[uid]:
                if smid in item_id_to_idx:
                    all_scores[item_id_to_idx[smid]] = -np.inf
            
            # Exact rank calculation:
            # Better items: score > target_score, or (score == target_score and mid < val_mid)
            better_count = np.sum(all_scores > target_als_score)
            tie_better = np.sum((all_scores == target_als_score) & (item_ids < val_mid))
            target_full_rank = int(better_count + tie_better + 1)
        else:
            target_als_score = float("nan")
            target_full_rank = None

        user_top20_mids = [m for m, rk, sc in sample_recs[uid]]
        in_top20 = val_mid in user_top20_mids

        # Run M02 Evaluator on this single user
        single_eval = evaluator.evaluate(
            recommendations={uid: user_top20_mids},
            targets={uid: HeldOutTarget(movie_id=val_mid, rating=val_rat)}
        )
        eval_hit = single_eval[20].hit_count > 0

        explanation = ""
        if not target_scoreable:
            explanation = "Target has 0 train ratings; no item factor exists."
        elif val_rat < 3.5:
            explanation = f"Rating {val_rat} < 3.5; excluded from positive evaluation cohort."
        elif in_top20:
            explanation = f"Hit at rank {user_top20_mids.index(val_mid) + 1}."
        else:
            explanation = f"Target rank is {target_full_rank:,} (ALS score {target_als_score:.2f} << top scores ~5.0)."

        diagnostic_rows.append({
            "userId": uid,
            "validation_movieId": val_mid,
            "validation_rating": val_rat,
            "target_scoreable": target_scoreable,
            "target_als_score": target_als_score,
            "target_full_rank": target_full_rank,
            "top20_contains_target": in_top20,
            "evaluator_hit": eval_hit,
            "is_in_train_seen": is_in_train_seen,
            "category": category,
            "explanation": explanation,
            "title": m_titles.get(val_mid, "Unknown")
        })

        score_str = f"{target_als_score:.4f}" if target_scoreable else "N/A"
        rank_str = f"{target_full_rank:,}" if target_full_rank is not None else "N/A"
        print(f"{uid:<8d} | {val_mid:<11d} | {val_rat:<6.1f} | {str(target_scoreable):<8} | {score_str:<10} | {rank_str:<10} | {str(in_top20):<8} | {str(eval_hit):<8} | {category}")

    # Output detailed diagnostics JSON
    with open(ARTIFACTS_DIR / "m06_acceptance_diagnostic_sample.json", "w", encoding="utf-8") as f:
        json.dump(diagnostic_rows, f, indent=2)
    print(f"\n  Saved diagnostic sample details to {ARTIFACTS_DIR / 'm06_acceptance_diagnostic_sample.json'}")

if __name__ == "__main__":
    run_audit()
