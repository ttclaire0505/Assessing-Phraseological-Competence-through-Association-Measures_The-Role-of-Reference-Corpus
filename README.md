```markdown
# COCA Dependency Pair PMI Extraction + Learner Mapping

This repository provides a reproducible pipeline to:
1) Extract COCA dependency pair frequency and PMI (log2) for each register/domain (**all / academic / news / spoken**).
2) Extract the same dependency-pair instances from EFL learner transcripts.
3) Left-join COCA reference PMI/frequency onto learner instances to create the final dataset used for downstream analyses (e.g., coverage, ΔPMI, ranking stability).

---

## Repository Contents

- `extract_coca_dependency_pairs_pmi.py`
  - Compute reference dependency pair statistics (+ PMI) from COCA.
  - Run once per domain: `--domain academic|news|spoken|all`

- `extract_learner_dependency_pairs.py`
  - Extract learner dependency pair instances token-level using spaCy dependency parsing.

- `join_reference_pmi_to_learner.py`
  - Left-join COCA reference frequency & PMI onto learner pairs using the shared key `dependency pair`.

---

## Data Requirements & Folder Structure

### 1) COCA reference texts
`extract_coca_dependency_pairs_pmi.py` expects:

```text
COCA_TEXTS_DIR/
  all/
    *.txt
  academic/
    *.txt
  news/
    *.txt
  spoken/
    *.txt
```

Each `.txt` file is parsed and dependency tokens are counted for target dependency types:

- `amod`
- `advmod`
- `dobj`

PMI is computed as log2 PMI using token-level marginals across all target dependency types (i.e., across `amod`, `advmod`, `dobj`).

---

### 2) Learner transcripts
`extract_learner_dependency_pairs.py` expects:

```text
LEARNER_TEXTS_DIR/
  *.txt
```

Each learner file name is used to infer `student_id`:

`12104238400110.txt` → `student_id = "12104238400110"`

---

## Outputs

### A) COCA reference outputs (domain-specific; run once per domain)
When running `extract_coca_dependency_pairs_pmi.py`, the script writes two files per domain:

1. **Dependency pairs + PMI**
   - `COCA_dependency_pairs_amod_advmod_dobj_with_PMI_{domain}.csv`

2. **Lemma marginal counts**
   - `COCA_lemma_marginal_counts_for_PMI_{domain}.csv`

**Join compatibility invariants (COCA):**

- Pair string format: `dep_lemma|head_lemma` (dep|head order)
- Reference columns include:
  - `dependency type`
  - `dependency word (dep lemma)`
  - `dependency word POS`
  - `head word (head lemma)`
  - `head word POS`
  - `Dependency Pair (dep|head)`
  - `Dependency Pair Frequency`
  - `PMI (log2, using token-level marginals across all dep_types)`

---

### B) Learner extraction outputs
`extract_learner_dependency_pairs.py` writes:

- **Token-level learner pairs:**
  - `OUTPUT_DIR/learner_token_level_pairs.csv`

- **Per-student counts by dependency type:**
  - `OUTPUT_DIR/per_student_dep_token_counts.csv`

- **A run log:**
  - `OUTPUT_DIR/run_log.json`

**Key learner columns (used for join):**

- `student_id`
- `dependency type`
- `dependency word`
- `dependency word pos`
- `head word`
- `head word pos`
- `dependency pair` ✅ (join key)

---

### C) Final joined dataset (used downstream for analysis)
`join_reference_pmi_to_learner.py` writes:

- `OUTPUT_DIR/learner_level_pmi_observations.csv`

This includes columns:

- `student_id`
- `dependency type`
- `dependency word`
- `dependency word pos`
- `head word`
- `head word pos`
- `dependency pair`
- `coca_ALL_frequency`, `coca_ALL_pmi`
- `coca_academic_frequency`, `coca_academic_pmi`
- `coca_news_frequency`, `coca_news_pmi`
- `coca_spoken_frequency`, `coca_spoken_pmi`

---

## Join Compatibility (Must-Haves)

The join script assumes the COCA reference CSVs contain:

### Required reference columns
- `Dependency Pair (dep|head)`
- `Dependency Pair Frequency`
- `PMI (log2, using token-level marginals across all dep_types)`

### Required learner columns
- `dependency pair`
- `dependency type`
- `dependency word`
- `dependency word pos`
- `head word`
- `head word pos`
- `student_id`

✅ **Join key:** `dependency pair`  
✅ **Join type:** left join  

If a learner pair does not exist in the COCA reference for a register, the corresponding PMI/frequency becomes missing (`NaN`).

---

## Quick Start (Run Order)

### Step 1: Extract learner dependency pairs
Run once:

```bash
python extract_learner_dependency_pairs.py
```

Make sure at the top of the script you set:

- `LEARNER_INPUT_DIR = "LEARNER_TEXTS_DIR"`
- `OUTPUT_DIR = "OUTPUT_DIR"`

This produces:

- `OUTPUT_DIR/learner_token_level_pairs.csv`

---

### Step 2: Extract COCA reference PMI (run 4 times)
Run reference extraction for each domain:

```bash
python extract_coca_dependency_pairs_pmi.py --domain all --coca_input_root COCA_TEXTS_DIR --output_dir OUTPUT_DIR --spacy_model en_core_web_sm
python extract_coca_dependency_pairs_pmi.py --domain academic --coca_input_root COCA_TEXTS_DIR --output_dir OUTPUT_DIR --spacy_model en_core_web_sm
python extract_coca_dependency_pairs_pmi.py --domain news --coca_input_root COCA_TEXTS_DIR --output_dir OUTPUT_DIR --spacy_model en_core_web_sm
python extract_coca_dependency_pairs_pmi.py --domain spoken --coca_input_root COCA_TEXTS_DIR --output_dir OUTPUT_DIR --spacy_model en_core_web_sm
```

This produces 4 sets of:

- `OUTPUT_DIR/COCA_dependency_pairs_amod_advmod_dobj_with_PMI_{domain}.csv`

---

### Step 3: Join reference PMI onto learner data
Run once:

```bash
python join_reference_pmi_to_learner.py
```

Ensure `join_reference_pmi_to_learner.py` points to:

- `OUTPUT_DIR/learner_token_level_pairs.csv`
- `OUTPUT_DIR/COCA_dependency_pairs_amod_advmod_dobj_with_PMI_{domain}.csv`

Then it outputs:

- `OUTPUT_DIR/learner_level_pmi_observations.csv`

---

## Notes / Reproducibility

- Dependency parsing is performed using spaCy (`en_core_web_sm` by default in your scripts).
- Target dependency types are consistently: `amod`, `advmod`, `dobj` in both COCA and learner extraction.
- Pair strings are lowercased lemmas:
  - `dep_lemma = token.lemma_.lower()`
  - `head_lemma = token.head.lemma_.lower()`
- The join is a left join:
  - if a learner pair does not exist in the COCA reference for a register, the corresponding PMI/frequency becomes missing (`NaN`).

---

