#!/usr/bin/env python3
"""
Convert Markdown resume to ATS-friendly PDF format.
"""

import sys
import argparse
from pathlib import Path
import re
import markdown2
from weasyprint import HTML


# Regex to strip emoji characters from HTML before rendering
EMOJI_RE = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map symbols
    "\U0001f1e0-\U0001f1ff"  # flags
    "\U00002702-\U000027b0"  # dingbats
    "\U0001f900-\U0001f9ff"  # supplemental symbols
    "\U00002600-\U000026ff"  # misc symbols
    "\U0000fe00-\U0000fe0f"  # variation selectors
    "\U0000200d"             # zero width joiner
    "\U00002060"             # word joiner
    "\U0000231a-\U0000231b"  # watch/hourglass
    "]+",
    flags=re.UNICODE,
)


def strip_emojis(text):
    """Remove emoji characters from text."""
    return EMOJI_RE.sub("", text)


def create_styled_html(md_content):
    """Convert markdown to styled HTML with ATS-friendly formatting."""
    html_body = markdown2.markdown(md_content, extras=["fenced-code-blocks", "tables"])

    # Strip emojis from HTML content
    html_body = strip_emojis(html_body)

    # Extract and wrap header section (h1 + subtitle + contact paragraphs)
    header_pattern = r"(<h1>.*?</h1>(?:\s*<p>.*?</p>){1,2})"

    def wrap_header(match):
        return f'<div class="header-box">{match.group(1)}</div>'

    html_body = re.sub(header_pattern, wrap_header, html_body, count=1, flags=re.DOTALL)

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                margin: 0.5in;
                size: letter;
            }}

            body {{
                font-family: 'Arial', 'Calibri', sans-serif;
                font-size: 10pt;
                line-height: 1.3;
                color: #000;
                margin: 0;
                padding: 0;
            }}

            /* Header container with border box */
            .header-box {{
                border: 2px solid #000;
                background-color: #fff;
                padding: 8px 12px;
                margin-bottom: 10px;
            }}

            /* Name in header */
            .header-box h1 {{
                text-align: left;
                font-size: 14pt;
                font-weight: bold;
                margin: 0;
                padding: 0;
                color: #000;
                border: none;
            }}

            /* Contact info in header */
            .header-box p {{
                text-align: left;
                font-size: 9pt;
                margin: 2px 0 0 0;
                line-height: 1.3;
            }}

            /* Section headers */
            h2 {{
                font-size: 12pt;
                font-weight: bold;
                color: #000;
                margin-top: 12px;
                margin-bottom: 4px;
                border-bottom: 2px solid #000;
                padding-bottom: 2px;
                text-transform: uppercase;
            }}

            /* Job titles and subsections */
            h3 {{
                font-size: 11pt;
                font-weight: bold;
                margin-top: 8px;
                margin-bottom: 3px;
                line-height: 1.3;
            }}

            /* Regular paragraphs */
            p {{
                margin: 3px 0;
                text-align: left;
                line-height: 1.3;
            }}

            /* Italic text for dates/locations */
            em {{
                font-style: italic;
                font-size: 9pt;
                color: #333;
            }}

            strong {{
                font-weight: bold;
            }}

            /* Bullet points - disc for ATS compatibility */
            ul {{
                margin: 2px 0;
                padding-left: 18px;
                list-style-type: disc;
            }}

            li {{
                margin-bottom: 3px;
                text-align: left;
                line-height: 1.3;
            }}

            ul li {{
                list-style-type: square;
            }}

            /* Links */
            a {{
                color: #0066cc;
                text-decoration: none;
            }}

            a:hover {{
                text-decoration: underline;
            }}

            /* Prevent page breaks */
            h2, h3 {{
                page-break-after: avoid;
            }}

            p, li {{
                page-break-inside: avoid;
            }}

            ul {{
                page-break-inside: avoid;
            }}

            /* Tighter spacing between sections */
            h2:not(:first-of-type) {{
                margin-top: 10px;
            }}

            /* Special formatting for Summary section */
            h2:first-of-type + ul {{
                margin-top: 4px;
            }}

            /* Job entries - group title and company together */
            h3 + p {{
                margin-top: 0;
                margin-bottom: 3px;
            }}

            /* Reduce spacing after job location/date line */
            p > em:only-child {{
                display: block;
                margin-bottom: 3px;
            }}

            /* Education entries */
            h2 + p {{
                margin-bottom: 2px;
            }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """

    return html_template


def preprocess_markdown(md_content):
    """Preprocess markdown to handle special formatting needs."""
    lines = md_content.split("\n")
    processed_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is a job title line (starts with **text**)
        if line.strip().startswith("**") and "**" in line[2:]:
            # Look ahead for company and date info
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # If next line contains location/date info, format them together
                if next_line and not next_line.startswith("#") and not next_line.startswith("\u25a0"):
                    processed_lines.append(f"### {line}")
                    processed_lines.append(f"*{next_line}*")
                    i += 2
                    continue

        processed_lines.append(line)
        i += 1

    return "\n".join(processed_lines)


def main():
    parser = argparse.ArgumentParser(description="Convert markdown resume to ATS-friendly PDF")
    parser.add_argument("markdown_file", help="Path to markdown resume file")
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Output directory (default: outputs/ in project directory)",
        default=None,
    )

    args = parser.parse_args()

    md_file = Path(args.markdown_file)
    if not md_file.exists():
        print(f"Error: File '{md_file}' not found")
        sys.exit(1)

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        script_dir = Path(__file__).parent
        output_dir = script_dir / "outputs"

    output_dir.mkdir(parents=True, exist_ok=True)

    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    md_content = preprocess_markdown(md_content)
    html_content = create_styled_html(md_content)

    output_file = output_dir / md_file.with_suffix(".pdf").name
    HTML(string=html_content).write_pdf(output_file)

    print(f"Successfully created: {output_file}")


if __name__ == "__main__":
    main()
