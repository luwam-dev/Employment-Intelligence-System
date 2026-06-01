import sys
from pathlib import Path

import pandas as pd

from src.discovery import Student
from src.pipeline import (
    apply_result_to_dataframe,
    build_student_from_row,
    detect_columns,
    ensure_output_columns,
    process_student,
)


DEFAULT_UNIVERSITY = "Brunel University London"


def print_cli_info():
    print("Welcome to the Employment Intelligence System\n")


def clean_output(value):
    if value is None or value == "":
        return "N/A"
    return str(value)


def make_student_from_name(name):
    name = name.strip()
    parts = name.split()

    first_name = parts[0] if parts else ""
    last_name = parts[-1] if len(parts) > 1 else ""

    return Student(
        first_name=first_name,
        last_name=last_name,
        full_name=name,
        university=DEFAULT_UNIVERSITY,
    )


def shorten(value, width):
    value = clean_output(value)

    if len(value) > width:
        return value[: width - 3] + "..."

    return value


def print_result(result):
    rows = [
        ("Input name", result.get("input_name")),
        ("Matched name", result.get("matched_name")),
        ("Role", result.get("role")),
        ("Company", result.get("company")),
        ("Location", result.get("location")),
        ("Status", result.get("match_status")),
        ("Person score", result.get("person_match_score")),
        ("Employment score", result.get("employment_evidence_score")),
        ("Final score", result.get("final_score")),
        ("Source title", result.get("source_title")),
        ("Source URL", result.get("source_url")),
    ]

    label_width = 20
    value_width = 85
    line = "+" + "-" * (label_width + 2) + "+" + "-" * (value_width + 2) + "+"

    print("\nResult")
    print(line)
    print(f"| {'Field':<{label_width}} | {'Value':<{value_width}} |")
    print(line)

    for label, value in rows:
        value = shorten(value, value_width)
        print(f"| {label:<{label_width}} | {value:<{value_width}} |")

    print(line)


def print_results_table(results):
    print("\nFinal Results\n")

    if not results:
        print("No results found.")
        return

    for index, result in enumerate(results, start=1):
        print("=" * 70)
        print(f"Result {index}")
        print("=" * 70)

        rows = [
            ("Input name", result.get("input_name")),
            ("Matched name", result.get("matched_name")),
            ("Role", result.get("role")),
            ("Company", result.get("company")),
            ("Location", result.get("location")),
            ("Status", result.get("match_status")),
            ("Person score", result.get("person_match_score")),
            ("Employment score", result.get("employment_evidence_score")),
            ("Final score", result.get("final_score")),
            ("Source title", result.get("source_title")),
            ("Source URL", result.get("source_url")),
        ]

        for label, value in rows:
            print(f"{label:<18}: {clean_output(value)}")

        print()


def process_excel_rows(df):
    detected = detect_columns(df)
    results = []

    for idx, row in df.iterrows():
        student = build_student_from_row(
            row=row,
            row_index=idx,
            detected=detected,
            default_university=DEFAULT_UNIVERSITY,
        )

        result = process_student(student)
        results.append((idx, result))

    return results


def search_single_names():
    while True:
        name = input("Enter name to search, or type q to quit: ").strip()

        if name.lower() in ["q", "quit", "exit"]:
            print("Goodbye!")
            break

        if not name:
            print("Please enter a name.\n")
            continue

        student = make_student_from_name(name)
        result = process_student(student)

        print_result(result)


def search_excel_file(input_file):
    if not input_file.exists():
        print("Input file not found:", input_file)
        return

    df = pd.read_excel(input_file, dtype=object)
    indexed_results = process_excel_rows(df)
    results = [result for _, result in indexed_results]

    print_results_table(results)


def search_excel_file_and_save(input_file, output_file):
    if not input_file.exists():
        print("Input file not found:", input_file)
        return

    df = pd.read_excel(input_file, dtype=object)
    df = ensure_output_columns(df)

    indexed_results = process_excel_rows(df)

    for idx, result in indexed_results:
        apply_result_to_dataframe(df, idx, result)

    results = [result for _, result in indexed_results]
    print_results_table(results)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_file, index=False)

    print("\nResults saved to:", output_file)


def show_usage():
    print("Usage:")
    print("python -m src.cli")
    print("python -m src.cli data/Trial_1.xlsx")
    print("python -m src.cli data/Trial_1.xlsx outputs/results.xlsx")


def main():
    args = sys.argv[1:]
    print_cli_info()

    if len(args) == 0:
        search_single_names()

    elif len(args) == 1:
        input_file = Path(args[0]).resolve()
        search_excel_file(input_file)

    elif len(args) == 2:
        input_file = Path(args[0]).resolve()
        output_file = Path(args[1]).resolve()
        search_excel_file_and_save(input_file, output_file)

    else:
        print("Too many arguments.\n")
        show_usage()


if __name__ == "__main__":
    main()