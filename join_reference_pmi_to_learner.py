"""
join_reference_pmi_to_learner_multi_domains.py

Left-join COCA reference dependency-pair frequency & PMI onto learner extracted pairs,
producing learner-level PMI observations with columns:

student id
dependency type
dependency word
dependency word pos
head word
head word pos
dependency pair
coca_ALL_frequency
coca_ALL_pmi
coca_academic_frequency
coca_academic_pmi
coca_news_frequency
coca_news_pmi
coca_spoken_frequency
coca_spoken_pmi

Join key (confirmed): "dependency pair" from the learner CSV.
This script assumes reference CSVs also contain the dependency pair column:
"Dependency Pair (dep|head)"
and the numeric columns:
"Dependency Pair Frequency"
"PMI (log2, using token-level marginals across all dep_types)"
"""

import os
import pandas as pd


# =========================
# Configuration (symbolic paths)
# =========================
LEARNER_TOKEN_PAIRS_CSV = os.path.join("OUTPUT_DIR", "learner_token_level_pairs.csv")

REF_ALL_CSV = os.path.join(
    "OUTPUT_DIR",
    "COCA_dependency_pairs_amod_advmod_dobj_with_PMI_ALL.csv"
)
REF_ACADEMIC_CSV = os.path.join(
    "OUTPUT_DIR",
    "COCA_dependency_pairs_amod_advmod_dobj_with_PMI_academic.csv"
)
REF_NEWS_CSV = os.path.join(
    "OUTPUT_DIR",
    "COCA_dependency_pairs_amod_advmod_dobj_with_PMI_news.csv"
)
REF_SPOKEN_CSV = os.path.join(
    "OUTPUT_DIR",
    "COCA_dependency_pairs_amod_advmod_dobj_with_PMI_spoken.csv"
)

OUTPUT_JOINED_CSV = os.path.join("OUTPUT_DIR", "learner_level_pmi_observations.csv")


# =========================
# Reference column names
# =========================
REF_COL_PAIR = "Dependency Pair (dep|head)"
REF_COL_FREQ = "Dependency Pair Frequency"
REF_COL_PMI = "PMI (log2, using token-level marginals across all dep_types)"


def normalize_pair_string(x):
    if pd.isna(x):
        return x
    return str(x).strip()


def load_reference_domain(ref_csv_path: str, domain_prefix: str) -> pd.DataFrame:
    ref = pd.read_csv(ref_csv_path, dtype=str)

    for c in [REF_COL_PAIR, REF_COL_FREQ, REF_COL_PMI]:
        if c not in ref.columns:
            raise ValueError(
                f"Reference file missing column '{c}': {ref_csv_path}\n"
                f"Got columns (first 30): {list(ref.columns)[:30]}"
            )

    ref[REF_COL_PAIR] = ref[REF_COL_PAIR].apply(normalize_pair_string)

    ref[REF_COL_FREQ] = pd.to_numeric(ref[REF_COL_FREQ], errors="coerce")
    ref[REF_COL_PMI] = pd.to_numeric(ref[REF_COL_PMI], errors="coerce")

    return ref[[REF_COL_PAIR, REF_COL_FREQ, REF_COL_PMI]].rename(columns={
        REF_COL_PAIR: "dependency pair",
        REF_COL_FREQ: f"coca_{domain_prefix}_frequency",
        REF_COL_PMI: f"coca_{domain_prefix}_pmi",
    })


def main():
    # ---- Load learner ----
    learner = pd.read_csv(LEARNER_TOKEN_PAIRS_CSV, dtype=str)

    learner_required = [
        "student_id",
        "dependency type",
        "dependency word",
        "dependency word pos",
        "head word",
        "head word pos",
        "dependency pair",
    ]
    missing = [c for c in learner_required if c not in learner.columns]
    if missing:
        raise ValueError(
            f"Learner file missing required columns: {missing}\n"
            f"Got columns (first 40): {list(learner.columns)[:40]}"
        )

    learner["dependency pair"] = learner["dependency pair"].apply(normalize_pair_string)

    # ---- Load references ----
    ref_all = load_reference_domain(REF_ALL_CSV, "ALL")
    ref_academic = load_reference_domain(REF_ACADEMIC_CSV, "academic")
    ref_news = load_reference_domain(REF_NEWS_CSV, "news")
    ref_spoken = load_reference_domain(REF_SPOKEN_CSV, "spoken")

    # ---- Left joins onto learner ----
    out = learner.merge(ref_all, on="dependency pair", how="left")
    out = out.merge(ref_academic, on="dependency pair", how="left")
    out = out.merge(ref_news, on="dependency pair", how="left")
    out = out.merge(ref_spoken, on="dependency pair", how="left")

    # ---- Select/order final columns ----
    final_cols = [
        "student_id",
        "dependency type",
        "dependency word",
        "dependency word pos",
        "head word",
        "head word pos",
        "dependency pair",
        "coca_ALL_frequency",
        "coca_ALL_pmi",
        "coca_academic_frequency",
        "coca_academic_pmi",
        "coca_news_frequency",
        "coca_news_pmi",
        "coca_spoken_frequency",
        "coca_spoken_pmi",
    ]
    out = out[[c for c in final_cols if c in out.columns]]

    out.to_csv(OUTPUT_JOINED_CSV, index=False, encoding="utf-8-sig")
    print(f"Saved: {OUTPUT_JOINED_CSV}")


if __name__ == "__main__":
    main()