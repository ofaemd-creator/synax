# SynaxLLM bootstrap corpus

These original synthetic demonstration dialogues were authored by the coding assistant during this implementation and are distributed under the repository's Apache-2.0 license. They are not an independently curated scientific corpus. They contain no patient records, private conversations, or scraped articles.

`bootstrap_train.jsonl` (24 records) and `bootstrap_validation.jsonl` (4 records) are separate. The training loader refuses exact record overlap. This does not detect semantic duplication or establish a robust independent benchmark.

Purpose: demonstrate training our own random-initialized transformer and checkpoint portability. This tiny dataset cannot teach broad conversation, scientific expertise, medical competence or reliable instruction following. It must not be marketed as evidence of those capabilities.

Before scaling: collect licensed multilingual text, document provenance and consent, deduplicate across splits, define held-out general-chat/science/code evaluations, and establish a compute budget. Keep human evaluation independent of training examples. Do not automatically train on user conversations.
