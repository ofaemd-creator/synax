---
name: synax-llm
description: Train, evaluate, and converse with SYNAX-LLM (SYNAX-LLM-TR-v2.1), the native Turkish and English conversational language model with subword character-n-gram attention, Turkish agglutinative morphology handling, multi-turn context memory, dynamic math/code synthesis, and 3D Agent Office task routing.
---

# SYNAX-LLM (`synax-llm`) — Native Turkish Conversational & Formal Language Model

Use this skill whenever the user wants to train, fine-tune, or converse in Turkish with SYNAX's native language model (`src/synax/synax_llm.py`).

## Commands
```bash
# Train / update SYNAX-LLM Turkish weights (models/synax_tr_llm_v2.json)
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax/src/synax/synax_llm.py --train

# Converse with SYNAX-LLM in Turkish from CLI
python3 /Users/o.farukaydin/.gemini/antigravity/scratch/synax/src/synax/synax_llm.py --chat "Merhaba SYNAX, yoğun bakım EKG cihazında sapmayı nasıl sıfırlarsın?"
```
