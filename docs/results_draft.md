\# Results



\## Experimental Setup



We evaluated five defense configurations (Baseline, Input Screening,

Context Isolation, LLM Guard, Combined) against a 42-case benchmark

spanning six categories: benign factual questions (n=8), direct

instruction-conflict attempts (n=8), roleplay/authority manipulation

(n=8), instructions embedded in retrieved documents (n=6), obfuscated

attack phrasing (n=6), and direct fake-secret disclosure requests (n=6).

All experiments used a single LLM provider (Groq, Llama/GPT-OSS class

model, temperature=0) to isolate the effect of the defense mechanism

itself rather than the underlying model.



\## Core Findings



\*\*Table 1: Defense performance across configurations (single run, n=42)\*\*



| Config | ASR | Defense Success Rate | FPR | Avg Latency (s) |

|---|---|---|---|---|

| A — Baseline | 0.059 | 0.941 | 0.0 | 2.51 |

| B — Input Screening | 0.000 | 1.000 | 0.0 | 1.77 |

| C — Context Isolation | 0.029 | 0.971 | 0.0 | 2.33 |

| D — LLM Guard | 0.000 | 1.000 | 0.0 | 0.58 |

| E — Combined | 0.000 | 1.000 | 0.0 | 0.67 |



All five configurations maintained a false positive rate of 0.0 across the

8-case benign set, indicating no measurable trade-off between defense

strength and benign task usability at this sample size.



\### Finding 1: Attack surface determines defense applicability



Context isolation (Config C) reduced ASR from 0.059 to 0.029 — a 50%

relative reduction — but did not eliminate attacks entirely. Manual

inspection of the single remaining leak (case `d003`, a direct

instruction-override embedded in the user's own query rather than in

retrieved content) confirmed that Config C's isolation mechanism, by

design, only labels and constrains \*retrieved\* context as untrusted; it

provides no protection against attacks originating in the query itself.

This is not a defense failure so much as a scope boundary, and it directly

motivates layering context isolation with query-level defenses (Config E)

rather than relying on any single mechanism.



\### Finding 2: Regex-based screening is exact-phrasing brittle



During evaluation, one attack case (`d005`) initially bypassed Config B's

regex-based input screening entirely, despite being semantically nearly

identical to a caught case (`d003`) — both are direct instruction-override

attempts, differing mainly in surface phrasing ("New instructions:..." vs.

"Forget everything above..."). This was resolved by adding a targeted

regex pattern, after which Config B achieved ASR = 0.0. We report this as

a deliberate illustration of regex screening's core limitation: it

generalizes only as far as its authors anticipated specific phrasings,

and near-synonymous attacks can produce divergent outcomes purely due to

wording.



\### Finding 3: LLM-based guard generalizes better than rule-based screening



Config D (LLM guard alone, no regex) achieved ASR = 0.0 across all

categories — including `d005` — without requiring the manual pattern

addition that Config B needed. This suggests that a classifier-based

approach generalizes across semantically similar attack phrasings more

robustly than exact-match rules, at the cost of an additional LLM call

per request (reflected in Config D's higher latency relative to B, though

still lower than the unguarded baseline and context-isolation configs due

to shorter guard-classification responses vs. full RAG answers).



\## Methodological Notes



Two scoring artifacts were identified and corrected during evaluation,

both through manual inspection of flagged "attack success" cases rather

than automated validation:



1\. A response that translated attack text (and thus contained a

&#x20;  compliance-marker substring like the placeholder secret name) while

&#x20;  explicitly refusing to act on it was initially miscounted as attack

&#x20;  success. Fixed by adding refusal-phrase detection that suppresses a

&#x20;  compliance-marker match when refusal language is co-present.

2\. The refusal-phrase fix above initially failed silently due to a

&#x20;  Unicode smart-quote mismatch between the detection patterns and the

&#x20;  model's actual output formatting (curly vs. straight apostrophes).



We report both because they illustrate a broader point relevant to any

LLM-output-based evaluation pipeline: substring-based automated scoring

is fragile to surface-level text variation in ways that require manual

spot-checking to catch, and this is not specific to our benchmark — it

is a general risk for any project scoring free-text LLM responses

programmatically.



\## Limitations



\[See README.md "Known Limitations" — sample size, single-run reporting,

benign accuracy measured as non-block rather than content-correctness,

no claim of universal security for any configuration.]

