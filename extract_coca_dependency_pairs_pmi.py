"""
COCA dependency pair + PMI extraction (single domain).

Run this script once per domain:
  --domain academic|news|spoken|all

Outputs (domain-specific filenames):
1) COCA_dependency_pairs_amod_advmod_dobj_with_PMI_{domain}.csv
2) COCA_lemma_marginal_counts_for_PMI_{domain}.csv

Key invariants for join compatibility:
- Pair string format: "dep_lemma|head_lemma" (dep|head order)
- Pair columns: dependency type, dependency word (dep lemma), dependency word POS,
  head word (head lemma), head word POS, Dependency Pair (dep|head), Frequency, PMI...
"""

import os
import re
import csv
import math
import argparse
from collections import Counter, defaultdict

import spacy
from tqdm import tqdm
from lxml import etree


# =========================
# 0) CLI config
# =========================
INTEREST_DEP_TYPES = {"amod", "advmod", "dobj"}
marginals_option = "ALL_DEP_TYPES"  # keep protocol

BLOCK_SIZE = 6000
SENT_BLOCK_SIZE = 2000


def clean_text(text: str) -> str:
    """
    Clean COCA raw text before parsing:
    - Remove HTML entities like &amp;
    - Try parsing as XML/HTML and extract inner text
    - Remove remaining tags
    - Remove curly-brace segments { ... } if present
    """
    text = re.sub(r"&[a-z]+;", " ", text)
    try:
        tree = etree.fromstring(f"<body>{text}</body>")
        text = "".join(tree.itertext())
    except Exception:
        text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"\{.*?\}", "", text)
    return text.strip()


def iter_txt_files(input_dir: str):
    """Yield full paths to .txt files under input_dir (recursive)."""
    for root, _, files in os.walk(input_dir):
        for fn in files:
            if fn.lower().endswith(".txt"):
                yield os.path.join(root, fn)


def compute_pmi_log2(dep_lemma: str, head_lemma: str, pair_count: int, dep_marginals, head_marginals) -> float:
    """
    PMI computed with event-space:
      N = sum(dep_marginals) = sum(head_marginals) across matched dependency tokens
      PMI = log2( P(pair)/(P(dep)*P(head)) )
    where:
      P(pair) = pair_count / N
      P(dep)  = count(dep_lemma)/N
      P(head) = count(head_lemma)/N
    """
    N = sum(dep_marginals.values())
    if N == 0:
        return float("nan")

    marg_dep = dep_marginals.get(dep_lemma, 0)
    marg_head = head_marginals.get(head_lemma, 0)
    if marg_dep == 0 or marg_head == 0 or pair_count == 0:
        return float("nan")

    p_pair = pair_count / N
    p_dep = marg_dep / N
    p_head = marg_head / N

    ratio = p_pair / (p_dep * p_head)
    if ratio <= 0:
        return float("nan")
    return math.log2(ratio)


def run_domain(domain: str, COCA_INPUT_ROOT: str, OUTPUT_DIR: str, spacy_model: str):
    split_input_dir = os.path.join(COCA_INPUT_ROOT, domain)
    if not os.path.isdir(split_input_dir):
        raise FileNotFoundError(
            f"Input directory for domain not found: {split_input_dir}\n"
            f"Expected structure: {COCA_INPUT_ROOT}/{domain}/*.txt"
        )

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_dep_pairs_csv = os.path.join(
        OUTPUT_DIR,
        f"COCA_dependency_pairs_amod_advmod_dobj_with_PMI_{domain}.csv"
    )
    output_word_freq_csv = os.path.join(
        OUTPUT_DIR,
        f"COCA_lemma_marginal_counts_for_PMI_{domain}.csv"
    )

    # Counters
    pair_counter_by_type = {dt: Counter() for dt in INTEREST_DEP_TYPES}
    dep_marginals = Counter()
    head_marginals = Counter()
    lemma_pos = {}
    pair_range = defaultdict(set)  # (dep_type, dep_lemma, head_lemma) -> set(filenames)

    nlp = spacy.load(spacy_model)
    nlp.max_length = 3_000_000

    # update counts
    def update_counts_from_token(token, filename: str):
        dep_type = token.dep_
        if dep_type not in INTEREST_DEP_TYPES:
            return

        head = token.head
        if head == token or head.is_punct or head.is_space:
            return

        dep_lemma = token.lemma_.lower()
        head_lemma = head.lemma_.lower()

        pair_counter_by_type[dep_type][(dep_lemma, head_lemma)] += 1

        if marginals_option == "ALL_DEP_TYPES":
            dep_marginals[dep_lemma] += 1
            head_marginals[head_lemma] += 1
        else:
            raise ValueError("Only marginals_option='ALL_DEP_TYPES' is implemented.")

        lemma_pos.setdefault(dep_lemma, token.pos_)
        lemma_pos.setdefault(head_lemma, head.pos_)

        pair_range[(dep_type, dep_lemma, head_lemma)].add(filename)

    # main processing
    files_list = list(iter_txt_files(split_input_dir))
    for fpath in tqdm(files_list, total=len(files_list), desc=f"Processing COCA domain={domain}"):
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        txt = clean_text(raw)
        if not txt:
            continue

        for block_start in range(0, len(txt), BLOCK_SIZE):
            block = txt[block_start:block_start + BLOCK_SIZE]

            curr_block_sents = [sent for sent in nlp(block).sents]

            curr_chunk = []
            char_count = 0

            for sent in curr_block_sents:
                stext = sent.text
                curr_chunk.append(stext)
                char_count += len(stext)

                if char_count > SENT_BLOCK_SIZE:
                    docs = list(nlp.pipe(curr_chunk, batch_size=32, disable=["ner"]))
                    for doc in docs:
                        for token in doc:
                            if token.is_punct or token.is_space:
                                continue
                            update_counts_from_token(token, fname)
                    curr_chunk, char_count = [], 0

            # flush remaining
            if curr_chunk:
                docs = list(nlp.pipe(curr_chunk, batch_size=32, disable=["ner"]))
                for doc in docs:
                    for token in doc:
                        if token.is_punct or token.is_space:
                            continue
                        update_counts_from_token(token, fname)

    # Output pair + PMI
    with open(output_dep_pairs_csv, "w", encoding="utf-8", newline="") as out_csv:
        writer = csv.writer(out_csv)
        writer.writerow([
            "dependency type",
            "dependency word (dep lemma)",
            "dependency word POS",
            "head word (head lemma)",
            "head word POS",
            "Dependency Pair (dep|head)",  # IMPORTANT: dep|head order
            "Dependency Pair Frequency",
            "dep marginal count",
            "head marginal count",
            "N (total dependency tokens across ALL dep_types in interest set)",
            "PMI (log2, using token-level marginals across all dep_types)",
            "Dependency Pair Range (number of distinct source files)"
        ])

        N_all = sum(dep_marginals.values())

        for dep_type in sorted(INTEREST_DEP_TYPES):
            for (dep_lemma, head_lemma), cnt in pair_counter_by_type[dep_type].items():
                dep_pos = lemma_pos.get(dep_lemma, "")
                head_pos = lemma_pos.get(head_lemma, "")
                dep_marg = dep_marginals.get(dep_lemma, 0)
                head_marg = head_marginals.get(head_lemma, 0)
                pmi = compute_pmi_log2(dep_lemma, head_lemma, cnt, dep_marginals, head_marginals)
                range_num = len(pair_range.get((dep_type, dep_lemma, head_lemma), set()))

                writer.writerow([
                    dep_type,
                    dep_lemma,
                    dep_pos,
                    head_lemma,
                    head_pos,
                    f"{dep_lemma}|{head_lemma}",  # dep|head (matches learner join key)
                    cnt,
                    dep_marg,
                    head_marg,
                    N_all,
                    pmi,
                    range_num
                ])

    print(f"[{domain}] Pair+PMI output written to: {output_dep_pairs_csv}")

    # Output lemma marginal counts
    with open(output_word_freq_csv, "w", encoding="utf-8", newline="") as out_freq:
        writer = csv.writer(out_freq)
        writer.writerow([
            "lemma",
            "POS",
            "dep marginal count",
            "head marginal count",
            "total marginal count"
        ])

        lemmas = set(dep_marginals.keys()) | set(head_marginals.keys())
        for lemma in sorted(lemmas):
            dep_m = dep_marginals.get(lemma, 0)
            head_m = head_marginals.get(lemma, 0)
            total_m = dep_m + head_m
            writer.writerow([
                lemma,
                lemma_pos.get(lemma, ""),
                dep_m,
                head_m,
                total_m
            ])

    print(f"[{domain}] Lemma marginal output written to: {output_word_freq_csv}")
    print(f"[{domain}] Done.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str, required=True,
                        help="One of: academic | news | spoken | all")
    parser.add_argument("--coca_input_root", type=str, default="COCA_TEXTS_DIR",
                        help="Root folder containing domain subfolders")
    parser.add_argument("--output_dir", type=str, default="OUTPUT_DIR",
                        help="Output folder")
    parser.add_argument("--spacy_model", type=str, default="en_core_web_sm",
                        help="spaCy model name")
    args = parser.parse_args()

    domain = args.domain.strip().lower()
    if domain not in {"academic", "news", "spoken", "all"}:
        raise ValueError("domain must be one of: academic, news, spoken, all")

    run_domain(
        domain=domain,
        COCA_INPUT_ROOT=args.coca_input_root,
        OUTPUT_DIR=args.output_dir,
        spacy_model=args.spacy_model
    )


if __name__ == "__main__":
    main()