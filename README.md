# markdown2resume

A toolkit for converting markdown resumes to professional, ATS-friendly formats (PDF & DOCX) and analyzing them with AI-powered tools via [OpenRouter](https://openrouter.ai/).

## Features

- **ATS-Friendly PDF** - Clean, parseable PDF with standard fonts and simple formatting
- **ATS-Friendly DOCX** - Word document using built-in heading styles that ATS systems recognize
- **AI Typo Checker** - LLM-powered proofreading via OpenRouter
- **Keyword Comparison** - NLTK-based keyword matching (no API key needed)
- **AI Job Fit Analysis** - Comprehensive fit scoring and suggestions via OpenRouter
- **ATS Compliance Checker** - Verify generated PDF/DOCX files pass ATS checks

## Setup

### 1. Install dependencies

Requires [uv](https://docs.astral.sh/uv/) and system dependencies for WeasyPrint:

```bash
# Ubuntu/Debian - WeasyPrint system dependencies
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0

# Install Python dependencies
uv sync
```

### 2. Configure API key (for AI features)

```bash
cp .env.example .env
# Edit .env and add your OpenRouter API key
```

Get your API key from: https://openrouter.ai/keys

## Usage

### Convert to PDF

```bash
uv run python convert_to_pdf.py data/example_resume.md
uv run python convert_to_pdf.py data/example_resume.md -o /path/to/output/dir
```

### Convert to DOCX

```bash
uv run python convert_to_docx.py data/example_resume.md
uv run python convert_to_docx.py data/example_resume.md -o /path/to/output/dir
```

### Check for typos (requires API key)

```bash
uv run python check_typos.py data/example_resume.md
uv run python check_typos.py data/example_resume.md -m openai/gpt-4.1
uv run python check_typos.py data/example_resume.md -o outputs/my_report.md
```

### Compare resume to job description (no API key needed)

```bash
uv run python compare_to_job.py data/example_resume.md data/example_job_offer.md
uv run python compare_to_job.py data/example_resume.md data/example_job_offer.md -o outputs/comparison.md
```

### AI job fit analysis (requires API key)

```bash
uv run python analyze_job_fit.py data/example_resume.md data/example_job_offer.md
uv run python analyze_job_fit.py data/example_resume.md data/example_job_offer.md -m openai/gpt-4.1
```

### Check ATS compliance (no API key needed)

```bash
uv run python check_ats.py outputs/example_resume.pdf outputs/example_resume.docx
```

## Configuration

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | (required for AI tools) | Your OpenRouter API key |
| `OPENROUTER_MODEL` | `anthropic/claude-sonnet-4` | Default model for AI analysis |

### CLI flags

All AI-powered scripts support:
- `-k` / `--api-key` - Override API key
- `-m` / `--model` - Override model (any OpenRouter-supported model)
- `-o` / `--output` - Custom output path

## Project Structure

```
markdown2resume/
├── convert_to_pdf.py       # Markdown -> ATS-friendly PDF
├── convert_to_docx.py      # Markdown -> ATS-friendly DOCX
├── check_typos.py          # LLM-powered proofreading
├── compare_to_job.py       # NLTK keyword matching
├── analyze_job_fit.py      # LLM-powered job fit analysis
├── check_ats.py            # ATS compliance checker for PDF/DOCX
├── data/                   # Input markdown files
│   ├── example_resume.md
│   └── example_job_offer.md
├── outputs/                # Generated files (gitignored)
├── pyproject.toml
├── .env.example
└── .gitignore
```
