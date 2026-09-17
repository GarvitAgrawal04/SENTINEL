import json
from pathlib import Path
from typing import List, Optional

from sentinel.layer3 import Exemplar

# In a real deployment, these would be pre-embedded in a vectorized index (e.g., ONNX / Faiss)
# For V1, we simply hold them in memory.
class ExemplarIndex:
    def __init__(self):
        self.exemplars: List[Exemplar] = []

    def load_from_corpus(self, corpus_json_path: Path, max_attack: int = 18, max_clean: int = 18):
        """
        Build index strictly from 'train' split.
        Must NOT leak 'test' or 'holdout' samples into the reference index.
        """
        with open(corpus_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        attack_count = 0
        clean_count = 0
        
        # We need a function to compute embeddings if not pre-computed.
        # But we must mock/lazy-load BGE-M3 so we don't stall.
        from sentinel.layer2.displacement import compute_embedding

        for sample in data.get("samples", []):
            if attack_count >= max_attack and clean_count >= max_clean:
                break
                
            # LEAKAGE CONTROL: Explicitly reject non-train splits
            if sample.get("split") != "train":
                continue
                
            # Skip if it is part of a holdout family just to be safe
            if "HOLDOUT" in sample.get("id", ""):
                continue

            label = sample.get("label", "unknown")
            text = sample.get("text", "")
            if not text:
                continue

            if label in ["malicious", "suspicious"] and attack_count < max_attack:
                emb = compute_embedding(text).tolist()
                ex = Exemplar(
                    id=sample["id"],
                    label="malicious",
                    family=sample.get("family"),
                    description=f"ATK: {sample.get('family', 'Unknown')} pattern",
                    embedding=emb
                )
                self.exemplars.append(ex)
                attack_count += 1

            elif label == "benign" and clean_count < max_clean:
                emb = compute_embedding(text).tolist()
                ex = Exemplar(
                    id=sample["id"],
                    label="clean",
                    family=sample.get("family"),
                    description="Verified clean baseline",
                    embedding=emb
                )
                self.exemplars.append(ex)
                clean_count += 1