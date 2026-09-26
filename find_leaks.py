import json
from evaluation.scorer import score_case

path = r"results\experiment_2026-09-26T21-30-25.311522+00-00.jsonl"

with open(path, encoding="utf-8") as f:
    entries = [json.loads(line) for line in f if line.strip()]

for e in entries:
    if "error" in e:
        continue
    score = score_case(e)
    if score.is_attack_success:
        config = e["config_name"]
        case_id = e["case_id"]
        category = e["category"]
        response = e["response_text"][:150]
        print(f"{config:20s} | {case_id:6s} | {category:30s} | {response!r}")