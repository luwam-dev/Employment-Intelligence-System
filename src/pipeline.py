import pandas as pd

from src.discovery import Student, discover_candidates
import src.matcher as matcher_module


OUTPUT_TEXT_COLUMNS = [
    "matched_name",
    "source_url",
    "source_title",
    "company",
    "role",
    "location",
    "match_status",
]

OUTPUT_NUMERIC_COLUMNS = [
    "person_match_score",
    "employment_evidence_score",
    "final_score",
]


def clean_string(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass

    return str(value).strip()


def normalise_column_name(name):
    return (
        str(name)
        .strip()
        .lower()
        .replace("\n", " ")
        .replace("-", " ")
        .replace("_", " ")
    )


def find_column(df, possible_names):
    columns = {}

    for column in df.columns:
        columns[normalise_column_name(column)] = column

    for name in possible_names:
        key = normalise_column_name(name)

        if key in columns:
            return columns[key]

    for column_key, original_column in columns.items():
        for name in possible_names:
            name_key = normalise_column_name(name)

            if name_key in column_key or column_key in name_key:
                return original_column

    return None


def detect_columns(df):
    return {
        "full_name": find_column(
            df,
            [
                "full name",
                "student name",
                "name",
                "candidate name",
            ],
        ),
        "first_name": find_column(
            df,
            [
                "first name",
                "firstname",
                "given name",
                "forename",
            ],
        ),
        "last_name": find_column(
            df,
            [
                "last name",
                "lastname",
                "surname",
                "family name",
            ],
        ),
        "course": find_column(
            df,
            [
                "course",
                "programme",
                "program",
                "degree",
            ],
        ),
        "graduation_year": find_column(
            df,
            [
                "graduation year",
                "grad year",
                "year",
                "completion year",
            ],
        ),
        "student_id": find_column(
            df,
            [
                "student id",
                "id",
                "student number",
            ],
        ),
        "university": find_column(
            df,
            [
                "university",
                "institution",
                "school",
            ],
        ),
    }


def get_row_value(row, column_name):
    if not column_name:
        return ""

    if column_name not in row.index:
        return ""

    return clean_string(row[column_name])


def split_full_name(full_name):
    parts = [
        part
        for part in str(full_name or "").split()
        if part.strip()
    ]

    if not parts:
        return "", ""

    if len(parts) == 1:
        return parts[0], ""

    return parts[0], parts[-1]


def build_student_from_row(
    row,
    row_index,
    detected,
    default_university="Brunel University London",
):
    full_name = get_row_value(row, detected.get("full_name"))
    first_name = get_row_value(row, detected.get("first_name"))
    last_name = get_row_value(row, detected.get("last_name"))

    if full_name and not first_name and not last_name:
        first_name, last_name = split_full_name(full_name)

    if not full_name:
        full_name = " ".join(
            part
            for part in [first_name, last_name]
            if part
        ).strip()

    if not full_name:
        full_name = f"Row {row_index + 1}"

    course = get_row_value(row, detected.get("course"))
    graduation_year = get_row_value(row, detected.get("graduation_year"))
    student_id = get_row_value(row, detected.get("student_id"))
    university = (
        get_row_value(row, detected.get("university"))
        or default_university
    )

    return Student(
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        course=course,
        graduation_year=graduation_year,
        student_id=student_id,
        university=university,
    )


def ensure_output_columns(df):
    for column in OUTPUT_TEXT_COLUMNS:
        if column not in df.columns:
            df[column] = ""

        df[column] = df[column].astype("object")

    for column in OUTPUT_NUMERIC_COLUMNS:
        if column not in df.columns:
            df[column] = None

        df[column] = df[column].astype("object")

    return df


def get_attr(obj, name, default=""):
    if obj is None:
        return default

    return getattr(obj, name, default)


def call_matcher(student, candidates):
    if hasattr(matcher_module, "select_best_match"):
        return matcher_module.select_best_match(student, candidates)

    if hasattr(matcher_module, "find_best_match"):
        return matcher_module.find_best_match(student, candidates)

    if hasattr(matcher_module, "match_candidates"):
        matches = matcher_module.match_candidates(student, candidates)

        if not matches:
            return None

        return max(
            matches,
            key=lambda item: get_attr(item, "final_score", 0),
        )

    raise RuntimeError("No supported matcher function found in matcher.py")


def status_from_score(final_score):
    if final_score is None:
        return "no_match"

    if final_score >= 0.80:
        return "matched"

    if final_score >= 0.55:
        return "possible_match"

    return "no_match"


def no_match_result(student):
    return {
        "input_name": student.full_name,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "university": student.university,
        "matched_name": "",
        "source_url": "",
        "source_title": "",
        "company": "",
        "role": "",
        "location": "",
        "match_status": "no_match",
        "person_match_score": None,
        "employment_evidence_score": None,
        "final_score": None,
    }


def result_to_dict(student, match):
    if match is None:
        return no_match_result(student)

    person_score = get_attr(match, "person_match_score", None)
    employment_score = get_attr(
        match,
        "employment_evidence_score",
        None,
    )
    final_score = get_attr(match, "final_score", None)

    if final_score not in ["", None]:
        final_score = round(float(final_score), 4)

    if person_score not in ["", None]:
        person_score = round(float(person_score), 4)

    if employment_score not in ["", None]:
        employment_score = round(float(employment_score), 4)

    match_status = (
        clean_string(get_attr(match, "match_status", ""))
        or clean_string(get_attr(match, "employment_status", ""))
        or status_from_score(final_score)
    )

    return {
        "input_name": student.full_name,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "university": student.university,
        "matched_name": clean_string(
            get_attr(
                match,
                "matched_name",
                student.full_name,
            )
        ),
        "source_url": clean_string(
            get_attr(
                match,
                "source_url",
                get_attr(match, "url", ""),
            )
        ),
        "source_title": clean_string(
            get_attr(
                match,
                "source_title",
                get_attr(match, "title", ""),
            )
        ),
        "company": clean_string(get_attr(match, "company", "")),
        "role": clean_string(get_attr(match, "role", "")),
        "location": clean_string(get_attr(match, "location", "")),
        "match_status": match_status,
        "person_match_score": person_score,
        "employment_evidence_score": employment_score,
        "final_score": final_score,
    }


def apply_result_to_dataframe(df, index, result):
    for column in OUTPUT_TEXT_COLUMNS + OUTPUT_NUMERIC_COLUMNS:
        df.at[index, column] = result.get(column, "")


def process_student(student):
    if not clean_string(student.full_name):
        return no_match_result(student)

    if student.full_name.startswith("Row "):
        return no_match_result(student)

    candidates = discover_candidates(
        student,
        max_search_results=5,
        max_candidates=8,
        sleep_seconds=0.2,
    )

    if not candidates:
        return no_match_result(student)

    best_match = call_matcher(student, candidates)

    return result_to_dict(student, best_match)