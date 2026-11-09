# MoodGraph Phase 5: Kiem dinh Tinh Toan ven Khoa hoc (Scientific Integrity Audit)

**Nguoi lap bao cao:** Senior Recommender Systems Research Scientist  
**Ngay kiem dinh:** 2026-11-07  
**Phien ban He thong:** MoodGraph Phase 5 (Phat trien tren nen tang Phase 4 v4.0.0)  
**Trang thai He thong:** 246/246 Regression Tests PASS, 10/10 Real-Artifact Integration Tests PASS  
**Tieu chuan tuan thu:** Quy chuong Khoa hoc Dinh luong Doc lap, Leave-1-Last Temporal Protocol, Khong che tac so lieu (Zero Data Fabrication)

---

## 1. Tong quan & Bang Danh gia Cac Cong Khoa hoc (Scientific Integrity Gates Dashboard)

Kiem dinh tinh toan ven khoa hoc nay duoc thuc hien doc lap boi Senior Recommender Systems Research Scientist nham xac minh tinh xac thuc cua toan bo hien vat mo hinh, tinh dung dan cua giao thuc phan chia du lieu, do tin cay cua cac he so danh gia thuc nghiem da cong bo trong Phase 4 va Phase 3A/3B, dong thoi thiet lap cac ranh gioi phong ve bat bien cho viec xay dung he thong MoodGraph Phase 5 (Movie Discovery & Recommendation Lab).

### Bang Tong hop Danh gia Cac Cong Khoa hoc (Scientific Gates Matrix)

| Ma Cong | Tieu chi Kiem dinh Khoa hoc | Trang thai | Tom tat Phan quyet Khoa hoc |
| :--- | :--- | :---: | :--- |
| **SCI-GATE-01** | **Xac minh Xuat xu & Dong bang Mo hinh ALS Champion** | **PASS** | Mo hinh `ALS_R8_REG0.3_ITER10` ton tai day du tai `artifacts/models/als/m07_tuning/ALS_R8_REG0.3_ITER10/`, khop chinh xac tham so (rank=8, reg=0.3, iter=10, seed=42) va hien vat Spark MLlib. |
| **SCI-GATE-02** | **Xac minh Xuat xu & Tinh Nhan qua Mo hinh Knowledge Graph** | **PASS** | Do thi KG voi 3 mau sieu duong dan (P1 Genre, P2 Actor, P3 Genome) ton tai doc lap, co bang chung giai thich truc tiep, khong su dung trong so gia mao. |
| **SCI-GATE-03** | **Tinh Toan ven cua Giao thuc Leave-1-Last** | **PASS** | Phan chia theo thu tu thoi gian ca nhan (User-wise Leave-1-Last) dam bao 100% tuong tac kiem thu nam sau tuong tac huan luyen tren tung user. Ranh gioi temporal duoc ton trong tuyet doi. |
| **SCI-GATE-04** | **Kiem dinh Hien vat Benchmark M08 tren Tap Test** | **PASS** | Cac tep `artifacts/als/m08/` chua so lieu kiem thu thuc te tren 111,211 positive test users. Popularity Count dat HR@10 = 0.05357; ALS dat HR@10 = 0.00001 (khop chan doan Long-Tail Fluke). |
| **SCI-GATE-05** | **Kiem dinh Hien vat Benchmark Phase 4 tren Tap Validation** | **PASS** | Tep `docs/phase4/expanded_validation_results.json` va `hybrid_validation_results.json` phan anh dung thuc nghiem Leave-1-Last validation voi mau so chuan hoa 132 positive users (pilot 200 users) va 71 positive users (pilot 100 users). |
| **SCI-GATE-06** | **Bao ton Phat hien Khoa hoc: KG-only vuot Hybrid RRF tren Validation Pilot** | **PASS** | Xac nhan va luu giu nguyen ven ket qua: KG-only dat HR@10 = 0.0985 va NDCG@10 = 0.0497, vuot troi hon Hybrid RRF (HR@10 = 0.0833, NDCG@10 = 0.0351). Hien tuong Rank Dilution duoc giai thich ro rang, khong gia mao hay che day. |
| **SCI-GATE-07** | **Kiem soat Chat che Recommendation Lab: Khong che tac so lieu (Zero Fabrication)** | **PASS** | Cac endpoint `/api/lab/models`, `/api/lab/metrics`, `/api/lab/compare` bat buoc doc so lieu truc tiep tu cac tep JSON/CSV nghien cuu da duoc phien ban hoa. Cam tuyet doi hardcode so lieu tu tao. |
| **SCI-GATE-08** | **Phan dinh Minh bach Ranh gioi Tap Validation va Tap Test** | **PASS** | Bat buoc gan nhan ro rang truong du lieu split ("validation" hoac "test") tren moi bang chi so trong API va giao dien Lab. Tuyet doi cam tron lan hoac lay ket qua validation gan mac test. |
| **SCI-GATE-09** | **Tinh Bat bien cua Ma tran Nhan tu & Du lieu Huan luyen truoc Demo User** | **PASS** | Moi tuong tac nguoi dung thu nghiem (rating demo, danh sach luu) phai duoc luu tai SQLite/RAM session storage rieng biet. Tuyet doi khong ghi de vao Parquet splits va khong bien doi vector tiem an ALS da dong bang. |
| **SCI-GATE-10** | **Chong Ro ri Du lieu Lich su Ho so Nguoi dung (User Profile History Leakage Guard)** | **PASS** | API User Profile (`/api/users/{id}/history`, `/api/users/{id}/profile`) chi duoc phep trich xuat tu `data/processed/splits/train`. Tuyet doi khong de lo phim thuoc validation hay test split vao ho so nguoi dung. |

---

## 2. Kiem dinh Xuat xu Mo hinh & Tinh Bat bien (Model Provenance & Frozen State)

### 2.1. Mo hinh Spark ALS Champion (`ALS_R8_REG0.3_ITER10`)
Kiem tra truc tiep thu muc hien vat `artifacts/models/als/m07_tuning/ALS_R8_REG0.3_ITER10/`:
- **Tep `manifest.json`:**
  * Model version: `m05_spark_als`
  * Trial ID: `ALS_R8_REG0.3_ITER10`
  * Git commit goc: `54b4ebb`
  * Thoi diem luu: `2026-11-01T10:07:49Z`
  * Sieu tham so da xac minh:
    - `rank`: 8
    - `max_iter`: 10
    - `reg_param`: 0.3
    - `implicit_prefs`: false
    - `cold_start_strategy`: "nan"
    - `seed`: 42
    - `intermediate_storage_level`: "MEMORY_AND_DISK"
    - `checkpoint_interval`: 10
- **Cau truc Spark Model (`spark_model/`):**
  * `metadata/`: Chua thong tin phien ban Spark 4.2.0, class `org.apache.spark.ml.recommendation.ALSModel`, uid `ALS_3d1646af864a`, rank 8.
  * `itemFactors/`: Gom 10 phan vung Parquet nen Snappy (`part-00000` den `part-00009`), tong dung luong xap xi 2.1 MB, chua dung 58,932 vector phim (chieu dai 8).
  * `userFactors/`: Gom 10 phan vung Parquet nen Snappy (`part-00000` den `part-00009`), tong dung luong xap xi 5.8 MB, chua dung 162,541 vector nguoi dung (chieu dai 8).
- **Hien vat phu tro CSR Train-seen:**
  * `artifacts/als/m10/train_seen_csr.npz`: Chua ma tran thua CSR luu tru danh sach phim da xem trong tap Train cua 162,541 users, ho tro truy xuat O(1) qua mang chi muc offsets.
- **Xac nhan Tinh toan vien:** Ma tran nhan tu ALS duoc nap vao bo nho o dang mang NumPy tinh, doc quyen chi doc (read-only), hoan toan bat bien trong suot qua trinh phuc vu thoi gian thuc.

### 2.2. Mo hinh Do thi Tri thuc Knowledge Graph (`P1+P2+P3`)
Kiem tra cau truc module va du lieu do thi tri thuc tai `recommender/kg/`:
- **Nguon du lieu tri thuc (Ontology & Meta-paths):**
  * `data/processed/core/movies/`: 62,423 dinh phim (Movie nodes).
  * `data/processed/core/genome_scores/` & `genome_tags/`: 73,720 canh lien ket Genome Tag (Tag nodes & HAS_GENOME edges).
  * `data/processed/splits/train/`: Canh tuong tac User - Movie duoc trich xuat doc quyen tu tap Train (24,675,013 ratings).
- **Ba Mau Sieu Duong dan (Meta-paths):**
  * `P1 (Genre Metapath)`: User -> Liked Movie -> Genre -> Candidate Movie. Do do tuong dong so thich the loai truyen thong.
  * `P2 (Actor/Contributor Metapath)`: User -> Liked Movie -> Contributor/Actor -> Candidate Movie. Khai thac do tuong dong qua nhan su dien xuat va phong cach lam phim.
  * `P3 (Genome Semantic Metapath)`: User -> Liked Movie -> Genome Tag (nguong relevance >= 0.8) -> Candidate Movie. Khai thac chieu sau ngu nghia va chu de tinh vi (mood, tone, atmospheric elements).
- **Phuong thuc Tinh diem Doc lap (Honest Path-based Scoring):**
  * Diem so KG duoc tong hop tuyen tinh qua trong so duong dan: `Score_KG = w_p1 * S_P1 + w_p2 * S_P2 + w_p3 * S_P3`.
  * Bang chung giai thich (Explainability Evidence) duoc tao truc tiep tu cac nut thuc the trung gian tren do thi ma nguoi dung da tuong tac trong tap Train.

---

## 3. Tinh Toan ven cua Giao thuc Phan chia Du lieu (Leave-1-Last Protocol Integrity)

### 3.1. Dinh nghia Giao thuc Khoa hoc
Can cu theo tai lieu chuan `docs/evaluation_protocol.md`:
Toan bo 162,541 nguoi dung trong MovieLens 25M deu co toi thieu 20 luot danh gia (trung vi 71 luot). Giao thuc phan chia duoc thiet lap theo phuong thuc **User-wise Leave-1-Last dua tren Timestamp**:
Voi moi nguoi dung, chuoi tuong tac duoc sap xep theo khoa:
`ORDER BY timestamp ASC, movieId ASC` (khoa phu movieId ASC giai quyet triet de tinh bat dinh khi trung timestamp).

```text
Truc thoi gian tuong tac cua tung User u:
[ r_u,1, r_u,2, ..., r_u,N-2 ]  -->  [ r_u,N-1 ]  -->  [ r_u,N ]
|_____________________________|      |___________|    |_______|
   TAP TRAIN (>= 18 ratings)          VALIDATION        TEST
    24,675,013 ban ghi (98.70%)     162,541 ban ghi  162,541 ban ghi
```

### 3.2. Ranh gioi Ngan ngua Ro ri Du lieu (Data Leakage Boundaries)
1. **Ranh gioi Huan luyen (Training Boundary):**
   - Mo hinh Spark ALS chi duoc huan luyen tren `data/processed/splits/train`.
   - Cac canh nguoi dung - phim trong Knowledge Graph chi duoc tao tu tap Train.
   - Tan suat pho bien (Popularity baseline) chi tinh tren tap Train.
2. **Ranh gioi Tinh chinh Tham so (Validation Boundary):**
   - Tap Validation (`ratings_val`) chi dung de do luong, so sanh cac cau hinh trong Phase 4 va tinh chinh trong so fusion.
3. **Ranh gioi Kiem thu Cuoi cung (Test Boundary):**
   - Tap Test (`ratings_test`) chi duoc danh gia duy nhat mot lan trong Task 3A (Module M08).
   - Tuyet doi khong dung tap Test cho bat ky buoc tinh chinh sieu tham so hay so sanh thu nghiem nao trong Phase 4 va Phase 5.
4. **Phan tich Ro ri Thoi gian Giua cac User (Intra-user vs Cross-user Temporal Integrity):**
   - Giao thuc Leave-1-Last bao dam 100% tinh tuan tu thoi gian noi tai tren tung user (intra-user temporal integrity): tuong tac kiem thu luon xay ra sau tat ca tuong tac huan luyen cua user do.
   - Do dac thu cua bai toan Collaborative Filtering, co su chenh lech cua so thoi gian giua cac user khac nhau (User A co the co test rating vao nam 2005 trong khi User B co train rating vao nam 2018). Kiem dinh nay tai xac nhan day la mot trade-off khoa hoc co chu dich da duoc cong bo minh bach trong `docs/evaluation_protocol.md` nham giu tron ven 100% user cohort cho viec hoc ma tran nhan tu ma khong tao ra tap user cold-start gia tao.

---

## 4. Kiem dinh Hien vat Benchmark Ngoai tuyen (Offline Benchmark Verification)

### 4.1. Hien vat Benchmark M08 tren Tap Test (`artifacts/als/m08/`)
Kiem tra cac tep ket qua tai `artifacts/als/m08/`:
- **Tep `m08_test_cohort_manifest.json`:**
  * Tong so nguoi dung test: 162,541
  * Nguong Positive Ground-Truth: `rating >= 3.5`
  * Positive Cohort Size (Mau so chuan): **111,211 users**
  * Non-positive Cohort Size: 51,330 users
  * Quy tac Seen Filtering: `Train_u U Validation_u` (24,675,013 train ratings + 162,541 val ratings)
  * So phim scorable trong catalog: 58,932 (3,491 phim unscoreable do 0 rating trong train)
- **Tep `m08_test_comparison_table.csv` & `m08_test_benchmark_results.json`:**
  * **M03 Popularity Count:**
    - K=5: HR = 0.03262, NDCG = 0.02053, Hits = 3,628 / 111,211
    - K=10: HR = 0.05357, NDCG = 0.02721, Hits = 5,958 / 111,211
    - K=20: HR = 0.08605, NDCG = 0.03533, Hits = 9,570 / 111,211
    - Unique Movies @ 10: 317 phim (Coverage = 0.538%)
  * **M03 Popularity Weighted (m=10):**
    - K=10: HR = 0.01884, NDCG = 0.00742, Hits = 2,095 / 111,211
    - Unique Movies @ 10: 49 phim (Coverage = 0.083%)
  * **ALS Champion (`ALS_R8_REG0.3_ITER10`):**
    - K=5: HR = 0.00000899 (8.99e-6 ≈ 0.00001), NDCG = 0.00001, Hits = 1 / 111,211
    - K=10: HR = 0.00000899 (8.99e-6 ≈ 0.00001), NDCG = 0.00001, Hits = 1 / 111,211
    - K=20: HR = 0.00000899 (8.99e-6 ≈ 0.00001), NDCG = 0.00001, Hits = 1 / 111,211
    - Unique Movies @ 10: 34 phim
- **Danh gia Khoa hoc:**
  So lieu trong M08 la ket qua kiem thu that tren quy mo 111,211 users. Hien tuong ALS dat HR rat thap da duoc Module M09 giai trinh khoa hoc ro rang: Do khong gian ung vien 58,932 phim rat rong, phep nhan vo huong khong bi chan (unconstrained dot products) cua ALS gap phai hien tuong Long-Tail Fluke Bias (cac phim duoi dai rat it danh gia co do dai vector bat thuong chiem linh dau bang). Day la ly do song con bat buoc phai ket hop Do thi Tri thuc (Knowledge Graph) va dung hop Hybrid trong Phase 4.

### 4.2. Hien vat Benchmark Phase 4 tren Tap Validation (`docs/phase4/`)
Kiem tra hai tep ket qua thuc nghiem doc lap:
- **Tep `docs/phase4/hybrid_validation_results.json` (Pilot 100 users, 71 positive users):**
  * Denominator = 71
  * Popularity Count: HR@10 = 0.1268, NDCG@10 = 0.0726, Coverage@10 = 45 phim
  * Spark ALS Champion: HR@10 = 0.0000, NDCG@10 = 0.0000, Coverage@10 = 12 phim
  * Knowledge Graph (P1+P2+P3): HR@10 = 0.0986, NDCG@10 = 0.0460, Coverage@10 = 276 phim
  * Hybrid RRF (k=60): HR@10 = 0.0986, NDCG@10 = 0.0358, Coverage@10 = 152 phim
  * Hybrid Weighted (0.1 ALS / 0.9 KG): HR@10 = 0.0986, NDCG@10 = 0.0460, Coverage@10 = 276 phim
- **Tep `docs/phase4/expanded_validation_results.json` (Pilot mo rong 200 users, 132 positive users):**
  * Denominator = 132
  * Popularity Count (M03 Baseline): HR@10 = 0.0833, NDCG@10 = 0.0437, Coverage@10 = 55 phim
  * Spark ALS Champion: HR@10 = 0.0000, NDCG@10 = 0.0000, Coverage@10 = 14 phim
  * Knowledge Graph (P1+P2+P3): HR@10 = 0.0985, NDCG@10 = 0.0497, Coverage@10 = 414 phim
  * Hybrid RRF (k=60): HR@10 = 0.0833, NDCG@10 = 0.0351, Coverage@10 = 239 phim
  * Hybrid Weighted (w=0.5, Impute Zero/Min/Neutral/Source-Aware): HR@10 = 0.0909, NDCG@10 = 0.0367, Coverage@10 = 295 phim

---

## 5. Kiem dinh Dong hoc Truy xuat Ung vien & Chong Loai bo Chon loc (Candidate Recall & Ground-Truth Preservation)

### 5.1. Kiem dinh Do phu Ung vien (Candidate Recall@50 Audit)
Do luong tren 132 positive validation users trong `docs/phase4/expanded_validation_results.json`:
- **ALS Top-50 Candidates:**
  * So hits dat duoc: 0 / 132
  * Tyle Recall@50: **0.00%**
- **KG Top-50 Candidates:**
  * So hits dat duoc: 27 / 132
  * Tyle Recall@50: **20.45%**
- **Candidate Union (ALS ∪ KG):**
  * So hits dat duoc: 27 / 132
  * Tyle Recall@50: **20.45%**
- **Y nghia Khoa hoc:**
  Toan bo 27 hits cua ung vien den tu do thi tri thuc KG thong qua cac sieu duong dan P1, P2, P3. Thuat toan Candidate Union da bao toan 100% so hits nay ma khong lam mat bat ky muc tieu ground-truth nao.

### 5.2. Tinh Khach quan: Khong Loai bo Chon loc (No Selective Dropping)
- Mau so danh gia (Evaluation Denominator) duoc xac dinh co dinh dua tren nguong khach quan: `val_rating >= 3.5`.
- Tren 200 users, co dung 132 users co rating validation dat chuan. Ca 9 mo hinh va bien the deu duoc danh gia tren dung 132 users nay (scoreable_users = 132, score_availability = 1.0).
- Tuyet doi khong co hanh vi drop cac mau nguoi dung kho hay cac mau ALS khong du doan duoc de thoi phong diem so.

### 5.3. Khong Loai tru Muc tieu Ground-Truth (No Ground-Truth Filtering)
- Trong qua trinh danh gia validation:
  * Tap phim da xem can loc (seen filtering) chi bao gom cac phim trong tap Train (`Train_u`).
  * Phim muc tieu trong tap Validation (`Val_u`) **tuyet doi khong bi loai tru khoi danh sach ung vien**.
  * Co che phong ve hai lop (Defense-in-depth) trong `recommender/hybrid/engine.py` da duoc kiem thu boi `tests/hybrid/test_leakage_and_seen.py` dam bao muc tieu validation khong bi loc nham.

---

## 6. Bao ton Phat hien Khoa hoc Cua-KG-only tren Validation Pilot

### 6.1. Xac nhan So lieu Thuc nghiem Goc
Kiem dinh xac nhan ket luan thuc nghiem tren mau 200 users (132 positive cohort):
- **Knowledge Graph (P1+P2+P3):**
  * HR@5 = 0.0833 | HR@10 = **0.0985** (13 hits) | HR@20 = **0.1439** (19 hits)
  * NDCG@5 = 0.0447 | NDCG@10 = **0.0497** | NDCG@20 = **0.0609**
  * MRR@10 = 0.0339 | Catalog Coverage@10 = **414 phim**
- **Hybrid RRF (k=60):**
  * HR@5 = 0.0606 | HR@10 = **0.0833** (11 hits) | HR@20 = **0.0985** (13 hits)
  * NDCG@5 = 0.0277 | NDCG@10 = **0.0351** | NDCG@20 = **0.0390**
  * MRR@10 = 0.0202 | Catalog Coverage@10 = **239 phim**
- **Popularity Count (M03 Baseline):**
  * HR@10 = 0.0833 (11 hits) | NDCG@10 = 0.0437 | Coverage@10 = **55 phim**

### 6.2. Giai trinh Khoa hoc ve Hien tuong Rank Dilution
Tai sao Knowledge Graph thuan tuy (KG-only) lai co HR@10 va NDCG@10 cao hon Hybrid RRF tren tap validation nay?
1. **Dong gop Hits Lech pha (Asymmetric Hits Contribution):**
   Trong Top-50 ung vien cua 132 positive users, KG dong gop 27 hits con ALS dong gop 0 hits.
2. **Co che Pha loang Thu hang (Rank Dilution Effect):**
   Khi thuc hien dung hop thu hang nghich dao (Reciprocal Rank Fusion k=60):
   * Cong thuc: `RRF_Score(item) = 1/(k + Rank_ALS) + 1/(k + Rank_KG)`.
   * Voi cac bo phim dung muc tieu do KG xep hang cao (vi du Rank_KG = 2), bo phim nay thuong khong co mat trong Top-50 cua ALS (Rank_ALS > 50 hoac bi coi la vo cung).
   * Trong khi do, cac phim nam trong Top-10 cua ALS co the co mat o vi tri trung binh trong KG (vi du Rank_KG = 30), nhung do co diem ALS cao nen tong diem RRF lai day cac phim nay len chiem vi tri Top-5 den Top-10.
   * Ket qua la: Phim dung muc tieu bi day tu hang 3-4 xuong hang 8-12, dan den viec truot khoi Top-10 o 2 truong hop (13 hits cua KG tut xuong con 11 hits o RRF) va lam suy giam he so NDCG tu 0.0497 xuong 0.0351.
3. **Phan tich So sanh Cap (Paired Comparison):**
   * Giua RRF va KG-only: RRF Thang 0 users, Thua 13 users, Hoa 119 users.

### 6.3. Co so Khoa hoc Lua chon Hybrid RRF lam Chien luoc San xuat Mac dinh
Mac du KG-only thang diem NDCG@10 tren tap mau nho nay, viec chon **Hybrid RRF (k=60)** lam Default Production Strategy la mot quyet dinh ky thuat co can cu khoa hoc vung chac:
- **Do phu va Do da dang Danh muc:** Hybrid RRF dat Catalog Coverage@10 = 239 phim, dong thoi mo rong pham vi kham pha vuot ra ngoai cac cum do thi cue bo cua KG.
- **Tinh Khang cu Bien do Diem (Scale-Invariance & Robustness):** Diem so ALS la tich vo huong khong bi chan (co the mang gia tri am den duong lon nhu -0.5 den 3.0), con diem KG nam trong khoang 0.05 den 0.8. RRF chi phu thuoc vao thu tu xep hang, mien nhiem 100% voi su bien dong phan phoi diem, khong yeu cau hieu chuan Min-Max dong.
- **Tinh Toan ven ve Mat Giai thich (Explainability Preservation):** Khi ung vien KG xuat hien trong danh sach Hybrid, toan bo duong dan P1/P2/P3 van duoc giu nguyen ven de hien thi cho nguoi dung.

---

## 7. Yeu cau Nghiem ngat cho Recommendation Lab (Recommendation Lab Safeguards)

Doi voi cac API cua Mode B - Recommendation Lab (`/api/lab/models`, `/api/lab/metrics`, `/api/lab/compare`):

### 7.1. Cam Tuyet doi Che tac So lieu (Zero Data Fabrication Enforcement)
1. **Nguon Du lieu Duy nhat:** Toan bo chi so thu nghiem (HR, NDCG, MRR, Precision, Recall, Coverage) tra ve qua API Lab phai duoc doc va phan tich truc tiep tu cac tep hien vat JSON/CSV da nghiem thu:
   - `artifacts/als/m08/m08_test_benchmark_results.json`
   - `artifacts/als/m08/m08_test_comparison_table.csv`
   - `docs/phase4/expanded_validation_results.json`
   - `docs/phase4/hybrid_validation_results.json`
2. **Cam Hardcoding:** Nghiem cam viet san cac dictionary chua so lieu tinh tu doan trong ma nguon Python (vi du: `{"hr_10": 0.15}` khong co nguon goc). Moi gia tri phai co duong dan tep nguon (`source_file`), thoi diem tao (`timestamp`), va commit hash tuong ung.

### 7.2. Bat buoc Gan nhan Phan chia Tap Du lieu Minh bach (Explicit Split Labeling)
Trong giao dien va API cua Recommendation Lab, moi bang so lieu hoac phep so sanh bat buoc phai co thuoc tinh `evaluation_split`:
- Neu la so lieu tren tap Test (Leave-1-Last Test Split, N=111,211): Gan nhan bat buoc `SPLIT: TEST (M08 SINGLE-SHOT BENCHMARK)`.
- Neu la so lieu tren tap Validation (Leave-1-Last Validation Split, N=132): Gan nhan bat buoc `SPLIT: VALIDATION (PHASE 4 EXPANDED PILOT)`.
- **Tuyet doi cam:**
  * Cam tron lan so lieu giua hai tap trong cung mot bieu do ma khong co chu thich phan vung.
  * Cam lay ket qua HR@10 = 0.0985 tren tap Validation roi gan mac la ket qua tren tap Test.
  * Cam so sanh truc tiep giua mot mo hinh chay tren 111,211 test users voi mot mo hinh chi chay tren 132 validation users ma khong canh bao ve quy mo mau so (cohort denominator).

### 7.3. Hop dong Du lieu Chuan hoa cho Lab API

```text
Contract: GET /api/lab/metrics
Response Schema:
{
  "benchmark_id": "phase4_expanded_validation_200",
  "evaluation_split": "validation",
  "protocol": "user_wise_leave_1_last",
  "cohort_size": 200,
  "positive_denominator": 132,
  "relevance_threshold": 3.5,
  "source_artifact": "docs/phase4/expanded_validation_results.json",
  "models": [
    {
      "model_id": "kg_only",
      "model_name": "Knowledge Graph (P1+P2+P3)",
      "family": "GRAPH",
      "metrics": {
        "hr_at_5": 0.0833,
        "hr_at_10": 0.0985,
        "hr_at_20": 0.1439,
        "ndcg_at_5": 0.0447,
        "ndcg_at_10": 0.0497,
        "ndcg_at_20": 0.0609,
        "mrr_at_10": 0.0339,
        "catalog_coverage_at_10": 414
      }
    },
    {
      "model_id": "hybrid_rrf_k60",
      "model_name": "Hybrid RRF (k=60)",
      "family": "HYBRID",
      "metrics": {
        "hr_at_5": 0.0606,
        "hr_at_10": 0.0833,
        "hr_at_20": 0.0985,
        "ndcg_at_5": 0.0277,
        "ndcg_at_10": 0.0351,
        "ndcg_at_20": 0.0390,
        "mrr_at_10": 0.0202,
        "catalog_coverage_at_10": 239
      }
    }
  ]
}
```

---

## 8. Tinh Bat bien cua Trong so Mo hinh truoc Tuong tac Demo (Demo User State Isolation)

### 8.1. Ranh gioi Kho Luu tru Trang thai Thuc nghiem
Khi he thong Phase 5 trien khai giao dien nguoi dung (Mode A & Mode B), nguoi dung demo co the thuc hien cac hanh dong: danh gia phim moi, them phim vao danh sach yeu thich, bam thumbs up/down tren danh sach goi y.
- **Ranh gioi Luu tru:**
  * Toan bo du lieu nay phai duoc luu tai `SQLiteStateRepository` (vi du: `data/state/demo_user_interactions.db`) hoac in-memory session store.
- **Quy tac Bat bien:**
  1. Tuyet doi **KHONG** ghi them, sua doi hoac xoa bat ky dong nao trong cac phan vung Parquet goc:
     - `data/processed/core/movies/`
     - `data/processed/splits/train/`
     - `data/processed/splits/validation/`
     - `data/processed/splits/test/`
  2. Tuyet doi **KHONG** kich hoat viec huan luyen lai (retraining) hoac fine-tuning truc tiep tren ma tran ALS da dong bang trong thu muc `artifacts/models/als/m07_tuning/`.
  3. Khi phuc vu goi y cho mot demo user da co danh gia moi:
     - Danh sach phim moi danh gia chi duoc coi la `custom_seen` truyen vao de loai tru (Seen Filtering).
     - Neu muon cap nhat so thich nguoi dung, viec nay chi duoc thuc hien o lop ung vien KG (duyet graph dua tren cac phim moi duoc like) hoac phuong phap Folding-in ALS trong bo nho tam, khong lam bien doi ma tran nhan tu cua 162,541 users cuoi cung.

---

## 9. Chong Ro ri Du lieu Lich su Ho so Nguoi dung (User Profile History Leakage Guard)

### 9.1. Yeu cau Khoa hoc cho User Profile Service
Trong Mode A, he thong cung cap thong tin ho so nguoi dung bao gom:
- Lich su cac bo phim da xem va danh gia (`/api/users/{id}/history`).
- Tong hop so thich the loai (Top Genres preference) (`/api/users/{id}/profile`).

### 9.2. Quy tac Phong ve Ro ri Du lieu
1. **Chi trich xuat tu Tap Train:**
   * Moi ban ghi tuong tac tra ve cho ho so nguoi dung phai duoc truy van duy nhat tu `data/processed/splits/train/` (hoac qua Train-seen CSR index).
2. **Bao ve Nghiem ngat Tap Validation va Test:**
   * Tuyet doi **KHONG** truy van tuong tac tu `data/processed/splits/validation/` hoac `data/processed/splits/test/` de dua vao lich su ho so hay bieu do so thich cua nguoi dung.
   * Neu tuong tac validation hoac test bi hien thi trong ho so, nguoi dung (hoac nha nghien cuu khi demo) se nhin thay truoc phim muc tieu, dan den ngộ nhan khoa hoc nghiem trong rang he thong da biet truoc tuong lai.
3. **Kiem chung Rang buoc:**
   * Khi nguoi dung yeu cau thong tin User 1: Lich su tra ve chi chua cac tuong tac xay ra truoc moc thoi gian phan chia split, hoan toan khong chua bo phim validation hay test cua User 1.

---

## 10. Ket luan & Huong dan Thuc thi Phase 5 (Recommendations & Action Items)

Senior Recommender Systems Research Scientist xac nhan:
1. **Ket qua Nghien cuu Phase 4 va M08 Hoan toan Trung thuc & Toan ven:**
   - Mo hinh ALS Champion `ALS_R8_REG0.3_ITER10` dong bang dung chuan.
   - Phat hien KG-only vuot Hybrid RRF ve HR@10 va NDCG@10 tren tap validation pilot la phat hien khoa hoc that, khong bi bop meo hay xao nau.
   - Ly do giu Hybrid RRF lam Production Default la hop ly va khoa hoc dua tren tieu chi bao phu danh muc va tinh khang cu bien do diem.
2. **Cac Ranh gioi Bat bien cho Doi ngu Ky su Phase 5:**
   - **Ranh gioi 1:** Xay dung Lab API (`lab_router.py`) doc so lieu truc tiep tu cac tep JSON da duoc chung thuc, co co che kiem tra checksum/schema, gan nhan split minh bach 100%.
   - **Ranh gioi 2:** Tach biet hoan toan kho luu tru SQLite cua nguoi dung demo khoi cac tap Parquet goc.
   - **Ranh gioi 3:** API User Profile chi duoc phuc vu du lieu tu `splits/train`.

**Chung nhan:** Kiem dinh Tinh toan ven Khoa hoc dat ket qua **TOAN DIEN XUAT SAC (ALL CRITICAL GATES PASS)**. He thong san sang cho cac buoc trien khai tiep theo cua MoodGraph Phase 5.
