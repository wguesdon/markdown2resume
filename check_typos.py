#!/usr/bin/env python3
"""
Check for typos in markdown resume using OpenRouter API.
"""

import argparse
import os
import re
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import markdown
from bs4 import BeautifulSoup

load_dotenv()

DEFAULT_MODEL = "google/gemini-2.5-flash"


def extract_json(text):
    """Extract JSON from a response that may be wrapped in markdown code fences."""
    # Strip markdown code fences if present
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return json.loads(text)


def extract_text_from_markdown(md_file):
    """Extract plain text from markdown file."""
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    html = markdown.markdown(md_content)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    return text, md_content


def split_into_chunks(text, chunk_size=3000):
    """Split text into chunks for API processing."""
    lines = text.split("\n")
    chunks = []
    current_chunk = []
    current_size = 0

    for line in lines:
        line_size = len(line)
        if current_size + line_size > chunk_size and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_size = line_size
        else:
            current_chunk.append(line)
            current_size += line_size + 1

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def check_typos_with_llm(text, api_key, model=DEFAULT_MODEL):
    """Use OpenRouter API to check for typos and grammar issues."""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={"HTTP-Referer": "https://github.com/markdown2resume"},
    )

    prompt = """You are an expert proofreader specializing in professional resumes. Analyze the following text for:

1. Spelling errors
2. Grammar mistakes
3. Punctuation errors
4. Inconsistent formatting (e.g., inconsistent bullet points, capitalization)
5. Common resume mistakes (e.g., using first person, passive voice)
6. Technical term misspellings

For each issue found, provide:
- The exact text with the error
- The line number (approximate)
- The type of error
- The suggested correction
- A brief explanation

Focus on actual errors, not style preferences. Be especially careful with:
- Technical terms and acronyms (which may look like typos but aren't)
- Proper nouns and company names
- Industry-specific terminology

Return your findings in JSON format with this structure:
{
    "errors": [
        {
            "text": "original text with error",
            "line": "approximate line number or section",
            "type": "spelling|grammar|punctuation|formatting|style",
            "correction": "suggested correction",
            "explanation": "brief explanation"
        }
    ],
    "summary": {
        "total_errors": number,
        "spelling_errors": number,
        "grammar_errors": number,
        "other_errors": number
    }
}

If no errors are found, return an empty errors array.

Text to analyze:
"""

    all_errors = []
    chunks = split_into_chunks(text)

    for i, chunk in enumerate(chunks):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional proofreader specializing in resumes. Always respond with valid JSON."},
                    {"role": "user", "content": prompt + chunk},
                ],
                temperature=0.1,
            )

            result = extract_json(response.choices[0].message.content)

            if i > 0 and "errors" in result:
                for error in result["errors"]:
                    if "line" in error and str(error["line"]).isdigit():
                        error["line"] = str(int(error["line"]) + (i * 50))

            if "errors" in result:
                all_errors.extend(result["errors"])

        except Exception as e:
            print(f"Error processing chunk {i + 1}: {str(e)}")
            continue

    return all_errors


def find_error_in_markdown(error_text, md_content):
    """Find the line numbers where an error appears in markdown content."""
    lines = md_content.split("\n")
    occurrences = []

    for i, line in enumerate(lines, 1):
        if error_text in line:
            occurrences.append((i, line.strip()))

    if not occurrences:
        error_lower = error_text.lower()
        for i, line in enumerate(lines, 1):
            if error_lower in line.lower():
                occurrences.append((i, line.strip()))

    return occurrences


def generate_typo_report(md_file, errors, md_content):
    """Generate a markdown report of typos found."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = "# Typo Check Report\n\n"
    report += f"**File:** `{os.path.basename(md_file)}`\n"
    report += f"**Generated:** {timestamp}\n"
    report += f"**Total issues found:** {len(errors)}\n\n"

    if not errors:
        report += "No issues found! Your resume looks great from a spelling and grammar perspective.\n"
    else:
        error_types = {}
        for error in errors:
            error_type = error.get("type", "other")
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error)

        report += "## Summary by Type\n\n"
        for error_type, type_errors in error_types.items():
            report += f"- **{error_type.capitalize()}**: {len(type_errors)} issues\n"
        report += "\n"

        report += "## Detailed Issues\n\n"

        for error_type, type_errors in error_types.items():
            report += f"### {error_type.capitalize()} Issues\n\n"

            for error in type_errors:
                report += f"#### Issue: `{error.get('text', 'N/A')}`\n\n"

                if "text" in error:
                    occurrences = find_error_in_markdown(error["text"], md_content)
                    if occurrences:
                        report += "**Found on lines:**\n"
                        for line_num, line_content in occurrences:
                            if len(line_content) > 80:
                                line_content = line_content[:77] + "..."
                            report += f"- Line {line_num}: `{line_content}`\n"
                    else:
                        report += f"**Location:** {error.get('line', 'Could not determine exact location')}\n"

                report += f"\n**Correction:** `{error.get('correction', 'N/A')}`\n"
                report += f"\n**Explanation:** {error.get('explanation', 'No explanation provided')}\n"
                report += "\n---\n\n"

    report += "## Tips\n\n"
    report += "- This analysis uses AI language models for intelligent proofreading\n"
    report += "- Some technical terms or industry-specific acronyms might be flagged incorrectly\n"
    report += "- Always review suggestions in context before making changes\n"
    report += "- Consider the tone and style appropriate for your industry\n"
    report += "- Pay special attention to consistency throughout your resume\n"

    return report


def main():
    parser = argparse.ArgumentParser(description="Check for typos in markdown resume using OpenRouter")
    parser.add_argument("resume", help="Path to markdown resume file")
    parser.add_argument("-o", "--output", help="Output report file (default: outputs/typo_report_TIMESTAMP.md)")
    parser.add_argument("-k", "--api-key", help="OpenRouter API key (or set OPENROUTER_API_KEY env variable)")
    parser.add_argument("-m", "--model", help=f"Model to use (default: {DEFAULT_MODEL})")

    args = parser.parse_args()

    if not os.path.exists(args.resume):
        print(f"Error: Resume file '{args.resume}' not found")
        return 1

    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OpenRouter API key required.")
        print("Please provide it via one of these methods:")
        print("1. Create a .env file with OPENROUTER_API_KEY=your-key")
        print("2. Set OPENROUTER_API_KEY environment variable")
        print("3. Use --api-key command line option")
        return 1

    model = args.model or os.getenv("OPENROUTER_MODEL_TYPO") or os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)

    print(f"Analyzing {args.resume} for typos using {model}...")
    text, md_content = extract_text_from_markdown(args.resume)

    errors = check_typos_with_llm(text, api_key, model)

    report = generate_typo_report(args.resume, errors, md_content)

    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"outputs/typo_report_{timestamp}.md"

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nTypo check complete!")
    print(f"Report saved to: {output_file}")
    print(f"Found {len(errors)} potential issues")

    return 0


if __name__ == "__main__":
    exit(main())
