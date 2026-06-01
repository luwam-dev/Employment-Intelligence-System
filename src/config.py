from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    input_file: Path = Path("data/Trial_1.xlsx")
    output_file: Path = Path("outputs/results.xlsx")

    use_llm: bool = True
    ollama_model: str = "llama3.1:latest"

    request_timeout: int = 20
    min_text_length: int = 120
    max_text_for_llm: int = 6000

    max_search_results: int = 5
    max_candidates: int = 8
    search_pause_seconds: float = 0.2

    # Matching thresholds used to decide whether a profile is reliable enough.
    min_person_match_score: float = 0.50
    min_employment_evidence_score: float = 0.15
    min_final_score_for_profile: float = 0.50
    min_final_score_for_employment: float = 0.65
    min_llm_confidence_for_accept: float = 0.40


SETTINGS = Settings()