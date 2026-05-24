from dataclasses import dataclass
from typing import Iterable

import os
import re
import time

import requests
from dotenv import load_dotenv


load_dotenv()

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


@dataclass
class Student:
    first_name: str
    last_name: str
    full_name: str
    course: str = ""
    graduation_year: str = ""
    student_id: str = ""
    university: str = ""


@dataclass
class CandidatePage:
    url: str
    title: str = ""
    snippet: str = ""
    text: str = ""
    final_url: str | None = None
    page_type: str = "generic"
    discovery_source: str = "brave"
    discovery_score: float = 0.0


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_text(value):
    return clean_text(value).lower()


def compact_name(value):
    return re.sub(r"[^a-zA-Z0-9]+", "", str(value or "").lower())


def unique_values(values: Iterable[str]):
    seen = set()
    output = []

    for value in values:
        value = clean_text(value)

        if value and value not in seen:
            seen.add(value)
            output.append(value)

    return output


def build_search_queries(student: Student):
    first_name = clean_text(student.first_name)
    last_name = clean_text(student.last_name)
    full_name = clean_text(student.full_name)
    compact = compact_name(full_name)

    queries = [
        f"{first_name} {last_name} linkedin",
        f'"{first_name} {last_name}" linkedin',
        f"{first_name} {last_name} github",
        f"{full_name} linkedin",
        f'site:linkedin.com/in "{full_name}"',
        f'site:linkedin.com/in "{first_name} {last_name}"',
        f"{compact} linkedin",
    ]

    return unique_values(queries)


def looks_like_bad_result(url, title, snippet):
    text = f"{url} {title} {snippet}".lower()

    blocked_words = [
        "login",
        "sign in",
        "directory",
        "people search",
    ]

    if "linkedin.com/pub/dir" in text:
        return True

    return any(word in text for word in blocked_words)


def get_page_type(url):
    url = url.lower()

    if "linkedin.com/in/" in url:
        return "linkedin"

    if "github.com/" in url:
        return "github"

    return "generic"


def score_candidate(student: Student, candidate: CandidatePage):
    text = normalize_text(
        f"{candidate.title} {candidate.snippet} {candidate.url}"
    )

    score = 0.0

    if normalize_text(student.full_name) in text:
        score += 1.5

    if student.first_name and student.first_name.lower() in text:
        score += 0.3

    if student.last_name and student.last_name.lower() in text:
        score += 0.5

    if "linkedin.com/in/" in candidate.url:
        score += 1.0

    if "github.com/" in candidate.url:
        score += 0.5

    return score


def search_brave(query, count=10):
    api_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError("Missing BRAVE_SEARCH_API_KEY in .env file")

    response = requests.get(
        BRAVE_SEARCH_URL,
        params={
            "q": query,
            "count": count,
        },
        headers={
            "X-Subscription-Token": api_key,
        },
        timeout=20,
    )

    response.raise_for_status()
    data = response.json()

    results = []

    for item in data.get("web", {}).get("results", []):
        url = item.get("url", "")
        title = item.get("title", "")
        snippet = item.get("description", "")

        if not url:
            continue

        if looks_like_bad_result(url, title, snippet):
            continue

        results.append(
            CandidatePage(
                url=url,
                title=title,
                snippet=snippet,
                page_type=get_page_type(url),
            )
        )

    return results


def remove_duplicate_candidates(candidates):
    unique = {}

    for candidate in candidates:
        if candidate.url not in unique:
            unique[candidate.url] = candidate

    return list(unique.values())


def discover_candidates(
    student: Student,
    max_search_results=8,
    max_candidates=10,
    sleep_seconds=0.2,
):
    queries = build_search_queries(student)

    print(f"   Queries: {len(queries)}")

    candidates = []

    for query in queries:
        try:
            print(f"   Searching: {query}")

            results = search_brave(query, count=max_search_results)
            print(f"   Hits: {len(results)}")

            candidates.extend(results)
            time.sleep(sleep_seconds)

        except Exception as error:
            print(f"   Search error: {error}")

    candidates = remove_duplicate_candidates(candidates)

    for candidate in candidates:
        candidate.discovery_score = score_candidate(student, candidate)

    candidates.sort(
        key=lambda candidate: candidate.discovery_score,
        reverse=True,
    )

    candidates = [
        candidate
        for candidate in candidates
        if candidate.discovery_score > 0.5
    ]

    candidates = candidates[:max_candidates]

    print(f"   Final candidates: {len(candidates)}")

    for index, candidate in enumerate(candidates, start=1):
        print(f"   [{index}] {candidate.discovery_score:.2f} {candidate.url}")

    return candidates