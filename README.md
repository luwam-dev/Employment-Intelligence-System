# Employment Intelligence System

The Employment Intelligence System is a command-line application that searches publicly available online sources to identify an individual's current employment information, including role, company, and location.

The system uses search results, text extraction, matching algorithms, and optional LLM processing to identify the most relevant profile and calculate confidence scores.

## Features

- Search using a person's name
- Search multiple public sources
- Extract text from webpages
- Match profiles using scoring logic
- Detect role, company, and location
- Process a single person or Excel file input
- Export results to Excel
- Optional Ollama LLM support

## Project Structure

```text
Employment-Intelligence-System
│
├── src
│   ├── cli.py
│   ├── pipeline.py
│   ├── config.py
│   ├── discovery.py
│   ├── extractor.py
│   ├── llm_processor.py
│   ├── matcher.py
│   ├── models.py
│   └── scorer.py
│
├── data
├── outputs
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

Install required packages:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```text
BRAVE_SEARCH_API_KEY=your_api_key
```

## Run

### Search one person

```bash
python -m src.cli
```

Example:

```text
Enter name to search: Arthur Money
```

### Search from Excel file

```bash
python -m src.cli data/Trial_1.xlsx
```

### Search and save results

```bash
python -m src.cli data/Trial_1.xlsx outputs/results.xlsx
```

## Output

The system returns:

- Input name
- Matched profile name
- Role
- Company
- Location
- Match status
- Person score
- Employment score
- Final score
- Source URL

## Requirements

- Python 3.10+
- Brave Search API key
- Ollama (optional)
