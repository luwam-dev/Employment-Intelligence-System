from dataclasses import dataclass, field


@dataclass
class Student:
    first_name: str
    last_name: str
    full_name: str
    university: str = ""
    course: str = ""
    graduation_year: str = ""
    student_id: str = ""


@dataclass
class CandidatePage:
    url: str
    title: str = ""
    snippet: str = ""
    text: str = ""
    final_url: str | None = None
    page_type: str = "generic"
    discovery_source: str = "unknown"
    discovery_score: float = 0.0
    status_code: int = 0
    content_type: str = ""


@dataclass
class MatchResult:
    person_match_score: float = 0.0
    employment_evidence_score: float = 0.0
    final_score: float = 0.0

    matched_name: str = ""
    source_url: str = ""
    source_title: str = ""
    page_type: str = ""

    company: str = ""
    role: str = ""
    location: str = ""

    match_status: str = "not_found"
    review_flag: str = "manual_review"
    review_reason: str = ""

    evidence: str = ""
    confidence: float = 0.0

    matched_signals: list[str] = field(default_factory=list)
    evidence_snippets: list[str] = field(default_factory=list)