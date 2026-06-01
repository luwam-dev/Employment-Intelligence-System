# Employment Intelligence System

The Employment Intelligence System is a command-line application that searches publicly available online sources to identify an individual's current employment information, including role, company, and location.

The system uses search results, text extraction, matching algorithms, and optional LLM processing to identify the most relevant profile and calculate confidence scores.

> [!NOTE]
> This tool uses publicly available online information. Results depend on what can be found through search and extracted from accessible webpages.

## Features

- Search using a person's name
- Search multiple public sources
- Extract text from webpages
- Match profiles using scoring logic
- Detect role, company, and location
- Process a single person or Excel file input
- Export results to Excel
- Optional Ollama LLM support

## Getting Started

### Requirements

- Python 3.10+
- [Brave Search API key](https://brave.com/search/api/)
- [Ollama](https://ollama.com/)
- [llama3.1:latest](https://ollama.com/library/llama3.1) model

> [!IMPORTANT]
> You need a valid Brave Search API key in your `.env` file before running the system.

## Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/luwam-dev/Employment-Intelligence-System.git
```
### 2. Change directory as so:
``` bash
cd Employment-Intelligence-System
```

### 3. Setup .env file
Create a `.env` file:
``` env
BRAVE_SEARCH_API_KEY=your_brave_api_key
```
> [!WARNING]
> Do not share your `.env` file or expose your API key in screenshots, GitHub commits, or public documents.

### 4. Install required packages:

```bash
pip install -r requirements.txt
```

## Usage

### Search one person

```bash
python -m src.cli
```

Example:

```text
Enter name to search, or type q to quit: Arthur Money
```

### Search from Excel file

```bash
python -m src.cli data/Trial_1.xlsx
```

### Search and save results

```bash
python -m src.cli data/Trial_1.xlsx outputs/results.xlsx
```

## Expected Data Input:
> [!IMPORTANT]
>  Save your `.xlsx` file inside the `data` folder before running the Excel search command.

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

### Output
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
When an output file is provided, the results are saved to an Excel file in the `outputs` folder.

> [!CAUTION]
> The system calculates confidence scores using available evidence, but results should still be reviewed manually before being used for important decisions.
