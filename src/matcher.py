from dataclasses import dataclass
import re

from src.discovery import CandidatePage, Student, normalize_text


ROLE_KEYWORDS = [
    "data engineer",
    "data analyst",
    "data scientist",
    "software engineer",
    "software developer",
    "machine learning engineer",
    "analytics engineer",
    "business analyst",
    "researcher",
    "consultant",
    "manager",
    "intern",
    "reader",
    "lecturer",
]

LOCATION_PATTERNS = [
    r"location:\s*([A-Za-z0-9,\-\.\s]+)",
    r"([A-Z][A-Za-z\-\s]+,\s*[A-Z][A-Za-z\-\s]+,\s*[A-Z][A-Za-z\-\s]+)",
    r"([A-Z][A-Za-z\-\s]+,\s*[A-Z][A-Za-z\-\s]+)",
]


@dataclass
class MatchResult:
    matched_name: str = ""
    source_url: str = ""
    source_title: str = ""

    person_match_score: float = 0.0
    employment_evidence_score: float = 0.0
    final_score: float = 0.0

    company: str = ""
    role: str = ""
    location: str = ""

    evidence: str = ""
    confidence: float = 0.0
    match_status: str = "not_found"


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def split_title(title):
    if not title:
        return []

    parts = re.split(r"\s+[|\-–·]\s+", title)
    return [clean_text(part) for part in parts if clean_text(part)]


def get_name_tokens(name):
    return re.findall(r"[a-z]+", normalize_text(name))


def calculate_token_overlap(student, text):
    student_tokens = set(get_name_tokens(student.full_name))
    text_tokens = set(get_name_tokens(text))

    if not student_tokens:
        return 0

    overlap = len(student_tokens & text_tokens)

    return overlap / len(student_tokens)


def calculate_person_score(student, candidate):
    blob = clean_text(
        f"{candidate.title} "
        f"{candidate.snippet} "
        f"{candidate.text} "
        f"{candidate.url}"
    )

    blob = normalize_text(blob)

    score = 0

    full_name = normalize_text(student.full_name)
    first_name = normalize_text(student.first_name)
    last_name = normalize_text(student.last_name)

    if full_name and full_name in blob:
        score += 0.70

    if first_name and first_name in blob:
        score += 0.15

    if last_name and last_name in blob:
        score += 0.20

    score += calculate_token_overlap(student, blob) * 0.40

    return round(min(score, 1.0), 4)


def extract_role(text):
    text = clean_text(text)

    for role in ROLE_KEYWORDS:
        if re.search(rf"\b{re.escape(role)}\b", text, re.I):
            return role

    return ""


def extract_company(title, student):
    parts = split_title(title)

    if len(parts) < 2:
        return ""

    first_part = normalize_text(parts[0])

    if (
        normalize_text(student.first_name) in first_part
        or normalize_text(student.last_name) in first_part
    ):
        return parts[1]

    return ""


def extract_location(text):
    text = clean_text(text)

    for pattern in LOCATION_PATTERNS:
        match = re.search(pattern, text)

        if match:
            return clean_text(match.group(1))

    return ""


def get_employment_fields(student, candidate):
    title = clean_text(candidate.title)
    snippet = clean_text(candidate.snippet)
    text = clean_text(candidate.text)

    combined_text = f"{title} {snippet} {text}"

    company = extract_company(title, student)
    role = extract_role(combined_text)
    location = extract_location(combined_text)

    evidence = f"{title} | {snippet[:150]}"

    return company, role, location, evidence


def calculate_employment_score(
    candidate,
    company,
    role,
    location,
):
    score = 0

    if company:
        score += 0.45

    if role:
        score += 0.30

    if location:
        score += 0.10

    return round(min(score, 1.0), 4)


def match_candidate(student, candidate):
    company, role, location, evidence = get_employment_fields(
        student,
        candidate,
    )

    person_score = calculate_person_score(
        student,
        candidate,
    )

    employment_score = calculate_employment_score(
        candidate,
        company,
        role,
        location,
    )

    final_score = round(
        min(
            1.0,
            (person_score * 0.60)
            + (employment_score * 0.30)
            + (candidate.discovery_score * 0.10),
        ),
        4,
    )

    if final_score >= 0.80:
        status = "matched"

    elif final_score >= 0.55:
        status = "possible_match"

    else:
        status = "not_found"

    return MatchResult(
        matched_name=student.full_name,
        source_url=candidate.url,
        source_title=candidate.title,
        person_match_score=person_score,
        employment_evidence_score=employment_score,
        final_score=final_score,
        company=company,
        role=role,
        location=location,
        evidence=evidence,
        confidence=final_score,
        match_status=status,
    )


def select_best_match(student, candidates):
    if not candidates:
        return MatchResult()

    results = []

    for candidate in candidates:
        results.append(
            match_candidate(
                student,
                candidate,
            )
        )

    results.sort(
        key=lambda result: result.final_score,
        reverse=True,
    )

    return results[0]