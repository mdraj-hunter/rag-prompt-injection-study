"""
Experiment runner: executes every benchmark case through every defense
config and logs raw results to JSONL. Supports --dry-run and MAX_CASES
for cheap pilot runs before scaling up.
"""
import argparse
import json
import os
import time
from datetime import datetime, timezone

import pandas as pd

from app.rag_pipeline import RAGPipeline
from app.config import settings

CONFIGS = {
    "A_baseline": lambda pipeline, query: pipeline.run_baseline(query),
    "B_input_screening": lambda pipeline, query: pipeline.run_input_screening(query),
    "C_context_isolation": lambda pipeline, query: pipeline.run_context_isolation(query),
    "D_llm_guard": lambda pipeline, query: pipeline.run_llm_guard(query),
    "E_combined": lambda pipeline, query: pipeline.run_combined(query),
}


def load_benchmark(csv_path: str = "data/benchmark_prompts.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if settings.max_cases and 0 < settings.max_cases < len(df):
        frac = settings.max_cases / len(df)
        parts = []
        for _, group in df.groupby("label"):
            n = max(1, round(len(group) * frac))
            n = min(n, len(group))
            parts.append(group.sample(n=n, random_state=42))
        df = pd.concat(parts).reset_index(drop=True)
    return df


def result_to_log_dict(row, config_name: str, result, run_timestamp: str) -> dict:
    return {
        "timestamp": run_timestamp,
        "case_id": row["id"],
        "category": row["category"],
        "label": row["label"],
        "expected_behavior": row["expected_behavior"],
        "config_name": config_name,
        "prompt_version": result.prompt_version,
        "model": settings.groq_model if settings.llm_provider == "groq" else (
            settings.gemini_model if settings.llm_provider == "gemini" else settings.openai_model
        ),
        "provider": settings.llm_provider,
        "query": result.query,
        "blocked": result.blocked,
        "block_reason": result.block_reason,
        "guard_decision": (
            {
                "risk_level": result.guard_decision.risk_level,
                "action": result.guard_decision.action,
                "reason": result.guard_decision.reason,
            }
            if result.guard_decision else None
        ),
        "retrieved_chunk_ids": [c.id for c in result.retrieved_chunks],
        "response_text": result.response_text,
        "latency_seconds": result.latency_seconds,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "estimated_cost": result.estimated_cost,
    }


def run_experiments(dry_run: bool = False, output_path: str | None = None):
    df = load_benchmark()
    run_timestamp = datetime.now(timezone.utc).isoformat()

    if output_path is None:
        os.makedirs("results", exist_ok=True)
        safe_ts = run_timestamp.replace(":", "-")
        output_path = f"results/experiment_{safe_ts}.jsonl"

    total_runs = len(df) * len(CONFIGS)
    print(f"Loaded {len(df)} benchmark cases -> {total_runs} total runs across {len(CONFIGS)} configs.")

    if dry_run:
        print("[DRY RUN] Validating inputs only, no API calls will be made.")
        for _, row in df.iterrows():
            assert isinstance(row["prompt"], str) and row["prompt"].strip(), f"Empty prompt in row {row['id']}"
        print("[DRY RUN] All prompts validated successfully. No API calls made.")
        return

    pipeline = RAGPipeline()
    run_count = 0
    error_count = 0

    with open(output_path, "a", encoding="utf-8") as f:
        for _, row in df.iterrows():
            for config_name, config_fn in CONFIGS.items():
                run_count += 1
                print(f"[{run_count}/{total_runs}] {row['id']} :: {config_name}", end=" ")
                try:
                    result = config_fn(pipeline, row["prompt"])
                    log_entry = result_to_log_dict(row, config_name, result, run_timestamp)
                    f.write(json.dumps(log_entry) + "\n")
                    f.flush()
                    print(f"-> OK (blocked={result.blocked}, {result.latency_seconds:.2f}s)")
                except Exception as e:
                    error_count += 1
                    error_entry = {
                        "timestamp": run_timestamp,
                        "case_id": row["id"],
                        "config_name": config_name,
                        "error": str(e),
                    }
                    f.write(json.dumps(error_entry) + "\n")
                    f.flush()
                    print(f"-> ERROR: {e}")

    print(f"\nDone. {run_count - error_count}/{run_count} succeeded, {error_count} errors.")
    print(f"Results written to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without making API calls")
    parser.add_argument("--output", type=str, default=None, help="Output JSONL path")
    args = parser.parse_args()

    run_experiments(dry_run=args.dry_run, output_path=args.output)