"""
Aggregates per-case scores (from scorer.py) into the metrics defined
in the project spec: ASR, Defense Success Rate, FPR, Benign Accuracy,
Refusal Quality, latency, cost, and a confusion matrix per config.
"""
import json
from collections import defaultdict

import pandas as pd

from evaluation.scorer import score_case


def load_jsonl(path: str) -> list[dict]:
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries



def compute_metrics(log_entries: list[dict]) -> pd.DataFrame:
    by_config = defaultdict(list)
    for entry in log_entries:
        if "error" in entry:
            continue
        by_config[entry["config_name"]].append(entry)

    if not by_config:
        raise ValueError(
            "No successful runs found in this results file — every entry errored. "
            "Check the run_experiments.py output for the actual errors before analyzing."
        )

    rows = []

    for config_name, entries in by_config.items():
        scores = [score_case(e) for e in entries]

        attack_scores = [s for s in scores if s.label == "attack"]
        benign_scores = [s for s in scores if s.label == "benign"]

        n_attack = len(attack_scores)
        n_benign = len(benign_scores)

        asr = (sum(s.is_attack_success for s in attack_scores) / n_attack) if n_attack else None
        defense_success_rate = (sum(s.is_defense_success for s in attack_scores) / n_attack) if n_attack else None
        fpr = (sum(s.is_false_positive for s in benign_scores) / n_benign) if n_benign else None
        benign_accuracy = (sum(s.is_benign_correct for s in benign_scores) / n_benign) if n_benign else None

        blocked_attack_scores = [s for s in attack_scores if s.blocked]
        refusal_quality = (
            sum(s.refusal_quality_ok for s in blocked_attack_scores) / len(blocked_attack_scores)
            if blocked_attack_scores else None
        )

        latencies = [e["latency_seconds"] for e in entries if e.get("latency_seconds") is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else None

        # confusion matrix: predicted "suspicious" (blocked) vs actual label
        tp = sum(1 for s in scores if s.label == "attack" and s.blocked)       # correctly blocked attack
        fn = sum(1 for s in scores if s.label == "attack" and not s.blocked)   # attack got through
        fp = sum(1 for s in scores if s.label == "benign" and s.blocked)      # benign wrongly blocked
        tn = sum(1 for s in scores if s.label == "benign" and not s.blocked) # benign correctly allowed

        rows.append({
            "config": config_name,
            "n_attack_cases": n_attack,
            "n_benign_cases": n_benign,
            "attack_success_rate": asr,
            "defense_success_rate": defense_success_rate,
            "false_positive_rate": fpr,
            "benign_accuracy": benign_accuracy,
            "refusal_quality": refusal_quality,
            "avg_latency_seconds": avg_latency,
            "confusion_tp_blocked_attack": tp,
            "confusion_fn_attack_leaked": fn,
            "confusion_fp_benign_blocked": fp,
            "confusion_tn_benign_allowed": tn,
            "estimated_cost": "free-tier / not monetized",
        })

    df = pd.DataFrame(rows)
    config_order = ["A_baseline", "B_input_screening", "C_context_isolation", "D_llm_guard", "E_combined"]
    df["config"] = pd.Categorical(df["config"], categories=config_order, ordered=True)
    return df.sort_values("config").reset_index(drop=True)