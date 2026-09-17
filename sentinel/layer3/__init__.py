from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

class ClassifierStatus(Enum):
    UNAVAILABLE = "unavailable"
    NOT_PROMOTED = "not_promoted"
    ACTIVE = "active"

@dataclass
class Exemplar:
    id: str
    label: str  # "clean", "malicious", "suspicious"
    family: Optional[str]
    description: str
    embedding: List[float]

@dataclass
class RetrievalResult:
    exemplar: Exemplar
    similarity: float

@dataclass
class BaselineClassification:
    nearest_exemplars: List[RetrievalResult]
    inferred_label: str
    confidence: float  # [0.0 - 1.0] Based on raw cosine similarity

@dataclass
class AgentImpact:
    affected_surface: str
    affected_behavior: str
    security_mechanism: str
    evidence_chain: List[str]
    structured_summary: str

@dataclass
class ClassifierPrediction:
    label: str
    confidence: float
    status: ClassifierStatus
    model_version: Optional[str]

@dataclass
class Layer3Result:
    baseline_classification: BaselineClassification
    agent_impact: Optional[AgentImpact]
    classifier_prediction: ClassifierPrediction
    escalation_required: bool
