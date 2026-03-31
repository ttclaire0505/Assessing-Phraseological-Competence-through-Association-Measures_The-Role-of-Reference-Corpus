"""
LEARNER-LEVEL TOKEN-LEVEL DEPENDENCY PAIR EXTRACTION

This script extracts dependency pair instances from EFL learner transcripts
using spaCy dependency parsing and produces token-level data suitable for
downstream token/marginal counting and PMI mapping.

Target dependency relations:
- amod
- advmod
- dobj

For each dependency token instance matching one target relation:
- dependency word  := dep token lemma (lowercased)
- head word         := head token lemma (lowercased)
- dependency pair   := "{dependency word}|{head word}"
- dependency pair pos := "{dependency word POS}|{head word POS}" (best-effort)

OUTPUTS
1) learner_token_level_pairs.csv
   A token-level table with the following columns:
     student_id
     dependency type
     dependency word
     dependency word pos
     head word
     head word pos
     dependency pair
     dependency pair pos

2) per_student_dep_token_counts.csv
   Per-student aggregated token counts for each dependency type.

3) run_log.json
   Reproducibility log: spaCy versions, model, and key filtering rules.

INPUTS
- Learner transcripts as .txt files under LEARNER_INPUT_DIR.
- Student ID is inferred from the file name (the substring before ".txt").
  Example: 12104238400110.txt -> student_id = "12104238400110".

NOTES ON PREPROCESSING
- Learner transcripts are assumed to be plain .txt (no HTML).
- We only normalize whitespace to make tokenization stable.
"""

import os
import re
import csv
import json
from datetime import datetime
from collections import defaultdict

import spacy
from tqdm import tqdm


# =========================
# 0) Configuration (symbolic paths)
# =========================
LEARNER_INPUT_DIR = "LEARNER_TEXTS_DIR"   # set relative path in your repo
OUTPUT_DIR = "OUTPUT_DIR"                # set relative path in your repo
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_TOKEN_LEVEL_CSV = os.path.join(OUTPUT_DIR, "learner_token_level_pairs.csv")
OUTPUT_PER_STUDENT_COUNTS_CSV = os.path.join(OUTPUT_DIR, "per_student_dep_token_counts.csv")
OUTPUT_RUN_LOG_JSON = os.path.join(OUTPUT_DIR, "run_log.json")

TARGET_DEP_TYPES = {"amod", "advmod", "dobj"}

# spaCy model
SPACY_MODEL = "en_core_web_sm"

# Performance parameters
BATCH_SIZE = 32
DISABLE_PIPES = ["ner"]  # keep dependency parser active


# =========================
# 1) Text preprocessing
# =========================
def preprocess_learner_text(raw_text: str) -> str:
    """
    Minimal preprocessing for learner transcripts.

    Learner files are assumed to be plain .txt without HTML tags.
    We only normalize whitespace.
    """
    raw_text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    raw_text = re.sub(r"\s+", " ", raw_text).strip()
    return raw_text


# =========================
# 2) Student ID extraction
# =========================
def get_student_id_from_filename(filename: str) -> str:
    """
    Extract student ID from filename by removing the ".txt" suffix.

    Example:
      12104238400110.txt -> 12104238400110
    """
    base = os.path.basename(filename)
    if base.lower().endswith(".txt"):
        return base[:-4]
    return os.path.splitext(base)[0]


# =========================
# 3) File iteration
# =========================
def iter_txt_files(input_dir: str):
    """Yield full paths to .txt files recursively under input_dir."""
    for root, _, files in os.walk(input_dir):
        for fn in files:
            if fn.lower().endswith(".txt"):
                yield os.path.join(root, fn)


# =========================
# 4) Main extraction
# =========================
def main():
    nlp = spacy.load(SPACY_MODEL)
    nlp.max_length = 3_000_000

    run_log = {
        "run_timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "spacy_model": SPACY_MODEL,
        "spacy_version": spacy.__version__,
        "target_dep_types": sorted(list(TARGET_DEP_TYPES)),
        "batch_size": BATCH_SIZE,
        "disable_pipes": DISABLE_PIPES,
        "filter_rules": {
            "keep_dep_types_only": True,
            "skip_punct_and_space_tokens": True,
            "skip_cases_where_head_is_token_or_punct_or_space": True,
            "lemma_lowercasing": True
        },
        "student_id_mode": "filename_without_suffix",
        "notes": "Token-level learner dependency pair extraction for PMI/marginal counting."
    }

    # Per-student counts: student_id -> dep_type -> count
    per_student_counts = defaultdict(lambda: defaultdict(int))

    # Token-level rows
    token_level_rows = []

    files = list(iter_txt_files(LEARNER_INPUT_DIR))
    for fpath in tqdm(files, desc="Extracting learner dependency pairs"):
        fname = os.path.basename(fpath)
        student_id = get_student_id_from_filename(fname)

        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
        text = preprocess_learner_text(raw_text)
        if not text:
            continue

        # Parse (single doc per file)
        doc = nlp(text)

        for token in doc:
            dep_type = token.dep_
            if dep_type not in TARGET_DEP_TYPES:
                continue

            # Skip punctuation/space
            if token.is_punct or token.is_space:
                continue

            head = token.head
            if head is token or head.is_punct or head.is_space:
                continue

            dep_lemma = token.lemma_.lower()
            head_lemma = head.lemma_.lower()

            dep_pos = token.pos_
            head_pos = head.pos_

            dep_pair = f"{dep_lemma}|{head_lemma}"
            dep_pair_pos = f"{dep_pos}|{head_pos}"

            # Per-student aggregation
            per_student_counts[student_id][dep_type] += 1

            # Token-level row
            token_level_rows.append({
                "student_id": student_id,
                "dependency type": dep_type,
                "dependency word": dep_lemma,
                "dependency word pos": dep_pos,
                "head word": head_lemma,
                "head word pos": head_pos,
                "dependency pair": dep_pair,
                "dependency pair pos": dep_pair_pos
            })

    # Write learner token-level pair table
    with open(OUTPUT_TOKEN_LEVEL_CSV, "w", encoding="utf-8", newline="") as out_csv:
        fieldnames = [
            "student_id",
            "dependency type",
            "dependency word",
            "dependency word pos",
            "head word",
            "head word pos",
            "dependency pair",
            "dependency pair pos"
        ]
        writer = csv.DictWriter(out_csv, fieldnames=fieldnames)
        writer.writeheader()
        for row in token_level_rows:
            writer.writerow(row)

    # Write per-student dependency token counts
    with open(OUTPUT_PER_STUDENT_COUNTS_CSV, "w", encoding="utf-8", newline="") as out_csv:
        fieldnames = ["student_id"] + sorted(list(TARGET_DEP_TYPES))
        writer = csv.DictWriter(out_csv, fieldnames=fieldnames)
        writer.writeheader()

        for student_id in sorted(per_student_counts.keys()):
            row = {"student_id": student_id}
            for dt in TARGET_DEP_TYPES:
                row[dt] = per_student_counts[student_id].get(dt, 0)
            writer.writerow(row)

    # Finalize run log
    run_log["num_students_with_any_extractions"] = len(per_student_counts)
    run_log["num_token_level_instances_extracted"] = len(token_level_rows)
    run_log["output_files"] = {
        "learner_token_level_pairs.csv": OUTPUT_TOKEN_LEVEL_CSV,
        "per_student_dep_token_counts.csv": OUTPUT_PER_STUDENT_COUNTS_CSV
    }

    with open(OUTPUT_RUN_LOG_JSON, "w", encoding="utf-8") as f:
        json.dump(run_log, f, ensure_ascii=False, indent=2)

    print("Done.")
    print(f"- learner token-level pairs: {OUTPUT_TOKEN_LEVEL_CSV}")
    print(f"- per-student dep token counts: {OUTPUT_PER_STUDENT_COUNTS_CSV}")
    print(f"- run log: {OUTPUT_RUN_LOG_JSON}")


if __name__ == "__main__":
    main()