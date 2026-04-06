
```markdown
# OSF Repository: Assessing EFL Learners' Phraseological Competence through Association Measures

This repository contains all code and supplementary materials for the study investigating how reference corpus selection affects PMI-based evaluations of EFL learners' phraseological competence.

---

OSF_Project/

- `README.md` — This file  
- `Code/` — All analysis scripts  
  - `01_extract_learner_dependency_pairs.py`  
  - `02_prepare_coca_pmi_data.py`  
  - `03_pair_level_analysis.py`  
  - `04_prepare_learner_pmi_data.py`  
  - `05_learner_level_analysis.py`  

- `Sample_Data/` — Representative sample data  
  - `LEARNER_TEXTS/` — 2 example learner transcripts  
    - `Sample_Learner_001.txt`  
    - `Sample_Learner_002.txt`  
  - `COCA_TEXTS/` — 2 example COCA texts  
    - `Sample_COCA_001.txt`  
    - `Sample_COCA_002.txt`  
  - `Sample_Outputs/` — Results from sample data  
    - `learner_token_level_pairs_sample.csv`  
    - `COCA_dependency_PMI_sample.csv`  

- `Results/` — Full results from complete dataset  
  - `01_PMI_for_each_dependency_pair in learner texts.xlsx`
  - `02_Number of PMI-eligible pairs in each learner text.csv`
  - `03_Descriptive results for the number of PMI-eligible pairs in each learner text.xlsx`
  - `04_The common set of dependency pairs across reference corpora.xlsx`
  - `05_Median PMI_in each learner text_across_reference corpora.xlsx`
  - `Table 4_Coverage of Dependency Pairs in Learner Texts across Reference Corpora (% Used for PMI Calculation).xlsx`
  - `Table 6_Friedman tests and pairwise Wilcoxon signed-rank tests for median PMI across reference corpora.xlsx`  
  - `Table 7_Distribution of dependency pairs with substantial (∣ΔPMI∣≥1) vs. minor (∣ΔPMI∣1) absolute PMI differences across reference corpora.xlsx`  
  - `Table 8_Friedman tests and Wilcoxon signed-rank post-hoc comparisons for learners’ median PMI scores across reference corpora.csv`  
  - `Table 9_Spearman’s ρ correlations for median PMI rankings across reference corpora.xlsx`  
  - `Table 10_Rank change based on median PMI scores across reference corpora by dependency.csv`

---

## Data Availability Statement

Due to licensing restrictions, **full raw data cannot be shared** in this repository:

| Data Type                      | Restriction                              | Alternative Provided      |
|--------------------------------|------------------------------------------|---------------------------|
| COCA corpus texts              | Proprietary - requires license from BYU  | ✅ 2 example text files    |
| TEM-8 Oral learner transcripts | Restricted - cannot redistribute         | ✅ 2 example text files    |

---

### Representative Sample Data

To ensure reproducibility, we provide:

- **2 example learner transcripts** (`Sample_Data/LEARNER_TEXTS/`)
- **2 example COCA texts** (`Sample_Data/COCA_TEXTS/`)
- **Outputs from these samples** (`Sample_Data/Sample_Outputs/`)

Researchers can run the full analysis pipeline on these examples to verify all computational procedures.

---

### Accessing Full Data for Replication

To replicate the full study:

1. **COCA data**: Obtain a license from [corpus.byu.edu/coca](https://corpus.byu.edu/coca/)
2. **Learner data**: Contact Nanjing University for data access (restricted)

---

## Script Descriptions

| Script                                          | Function                                                              | Input                                               | Output                                                                  |
|-------------------------------------------------|-----------------------------------------------------------------------|-----------------------------------------------------|-------------------------------------------------------------------------|
| `01_extract_learner_dependency_pairs.py`       | Extracts dependency pairs from learner texts                         | `.txt` files in `Data/raw/LEARNER_TEXTS/`           | `learner_token_level_pairs.csv`, `per_student_dep_token_counts.csv`, `run_log.json` |
| `02_prepare_coca_pmi_data.py`                  | Processes COCA texts and calculates PMI                              | `.txt` files in `Data/raw/COCA_TEXTS/`              | `COCA_dependency_PMI.csv`                                               |
| `03_pair_level_analysis.py`                    | Computes coverage statistics (Table 4) and compares PMI distributions across corpora (RQ1) | `Learner_dependency_pairs.csv`, COCA CSV files | `coverage_statistics.xlsx`, `common_set_pairs.xlsx`, `pair_level_analysis.xlsx` |
| `04_prepare_learner_pmi_data.py`               | Prepares learner-level PMI data                                      | `Learner_dependency_pairs.csv`, COCA CSV files      | `student_pmi_eligible_counts_by_type.csv`, `student_pmi_quantiles_summary.csv` |
| `05_learner_level_analysis.py`                 | Analyzes learner ranking stability (RQ2)                             | `Dependency_pairs extracted from learner corpus_with_frequency_PMI.xlsx` | `learner_median_pmi_by_corpus.xlsx`, `learner_level_analysis.xlsx` |

---

## Output Files Summary

| File                                           | Description                                                         | Generated By      |
|------------------------------------------------|---------------------------------------------------------------------|-------------------|
| `learner_token_level_pairs.csv`               | Token-level dependency pairs from learners                          | Script 01         |
| `per_student_dep_token_counts.csv`            | Counts of each dependency type per student                          | Script 01         |
| `run_log.json`                                | Reproducibility log with parameters and versions                    | Script 01         |
| `COCA_dependency_PMI.csv`                     | COCA dependency pairs with PMI scores (11 columns)                  | Script 02         |
| `coverage_statistics.xlsx`                    | Table 4: Coverage of learner pairs across corpora                   | Script 03         |
| `common_set_pairs.xlsx`                       | Dependency pairs present in all four COCA subcorpora                | Script 03         |
| `pair_level_analysis.xlsx`                    | RQ1 results: Friedman + Wilcoxon on common set                      | Script 03         |
| `student_pmi_eligible_counts_by_type.csv`     | Counts of PMI-eligible pairs per student                            | Script 04         |
| `student_pmi_quantiles_summary.csv`           | PMI median, Q1, Q3, IQR per student                                 | Script 04         |
| `learner_median_pmi_by_corpus.xlsx`           | Median PMI per learner (intermediate)                               | Script 05         |
| `learner_level_analysis.xlsx`                 | RQ2 results: Friedman, Spearman, rank shifts                        | Script 05         |

---

## Execution Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Run with Sample Data (Verify Pipeline)

```bash
# Copy sample data to expected locations
cp Sample_Data/LEARNER_TEXTS/*.txt Data/raw/LEARNER_TEXTS/
cp Sample_Data/COCA_TEXTS/*.txt Data/raw/COCA_TEXTS/

# Run all scripts
cd Code/
python 01_extract_learner_dependency_pairs.py
python 02_prepare_coca_pmi_data.py
python 03_pair_level_analysis.py
python 04_prepare_learner_pmi_data.py
python 05_learner_level_analysis.py
```

### 3. Run with Full Data (After Obtaining License)

Place your full data in:

- Learner transcripts: `Data/raw/LEARNER_TEXTS/`
- COCA texts: `Data/raw/COCA_TEXTS/`

Then run scripts in order as above.

---

## Dependencies

### Python Version
Python 3.8 or higher

### Required Packages (`requirements.txt`)

```
pandas>=1.3.0
numpy>=1.21.0
scipy>=1.7.0
statsmodels>=0.13.0
spacy>=3.5.0
tqdm>=4.62.0
openpyxl>=3.0.0
```

### spaCy Model

```bash
python -m spacy download en_core_web_sm
```
