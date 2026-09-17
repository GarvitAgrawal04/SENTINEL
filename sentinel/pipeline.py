import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
from sentinel.rules.base import ScanResult
from sentinel.scanner import scan_file, scan_multi_files
from sentinel.layer3 import ClassifierStatus
from sentinel.layer3.classifier import NearestNeighborBaseline
from sentinel.layer3.exemplar import ExemplarIndex
from sentinel.layer3.reconstruction import reconstruct_impact
from sentinel.layer4.guide import generate_guide

class PipelineOrchestrator:
    def __init__(self):
        self.layer3_index = None
        self.layer3_baseline = None
        self._init_layer3()

    def _init_layer3(self):
        try:
            # Check for configured corpus path or fallback to local path
            corpus_env = os.environ.get("SENTINEL_CORPUS_PATH")
            if corpus_env:
                corpus_path = Path(corpus_env)
            else:
                # Resolve relative to repo root (sentinel/../)
                repo_root = Path(__file__).parent.parent
                corpus_path = repo_root / "sentinel-test-corpus" / "metadata" / "dataset.json"

            if corpus_path.exists():
                self.layer3_index = ExemplarIndex()
                self.layer3_index.load_from_corpus(corpus_path, max_attack=18, max_clean=18)
                self.layer3_baseline = NearestNeighborBaseline(self.layer3_index)
        except Exception as e:
            print(f"[SENTINEL] Warning: Failed to load Layer 3 corpus: {e}", file=sys.stderr)

    def run_full_pipeline(self, scan_results: List[ScanResult]) -> List[ScanResult]:
        for result in scan_results:
            self._run_single(result)
        return scan_results

    def _run_single(self, result: ScanResult):
        # Layer 2
        path = Path(result.filename)
        l2_res = None
        if path.exists():
            try:
                from sentinel.manifest.sentinel_lock import FileSystemBaseline
                # Find root dir (with .claude)
                root = path.parent
                while root != root.parent and not (root / ".claude").exists():
                    root = root.parent
                if (root / ".claude").exists():
                    baseline = FileSystemBaseline(root)
                    from sentinel.layer2.orchestrator import run_layer2
                    # Wrap the single file in a list
                    l2_res = run_layer2([path.relative_to(root)], baseline, root)
            except Exception as e:
                # e.g. ModelUnavailableError
                pass

            # Attach to result
            if l2_res and l2_res.displacements:
                from sentinel.scoring.formula import DisplacementResult
                d = l2_res.displacements[0]
                result.displacement = DisplacementResult(magnitude=d.cosine_distance, direction=d.direction)
            if self.layer3_baseline:
                # compute embedding for text
                from sentinel.layer2.displacement import compute_embedding
                text = path.read_text(encoding="utf-8", errors="replace")
                try:
                    query_vec = compute_embedding(text).tolist()
                    l3_class = self.layer3_baseline.classify(query_vec)
                    l3_impact = reconstruct_impact(str(path), result.findings, l2_res)
                    
                    result.layer3_result = {
                        "confidence": l3_class.confidence if l3_class.inferred_label == "clean" else 0.0,
                        "inferred_label": l3_class.inferred_label,
                        "agent_impact": l3_impact.to_dict() if l3_impact else None
                    }
                except Exception:
                    pass

        # Layer 4
        guide_result = generate_guide(result)
        # We can attach guide_result to scan_result for downstream JSON/CLI consumption
        result.guide = guide_result

# Singleton
_orchestrator = None

def get_orchestrator() -> PipelineOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator()
    return _orchestrator
