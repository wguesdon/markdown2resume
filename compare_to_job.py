#!/usr/bin/env python3
"""
Compare resume to job description using keyword analysis (no LLM required).
"""

import argparse
import os
import re
from datetime import datetime
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import markdown
from bs4 import BeautifulSoup

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)


def extract_text_from_markdown(md_file):
    """Extract plain text from markdown file."""
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    html = markdown.markdown(md_content)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    return text.lower(), md_content


def extract_keywords(text, top_n=20):
    """Extract top keywords from text."""
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    tokens = word_tokenize(text)

    stop_words = set(stopwords.words("english"))
    custom_stopwords = {
        "experience", "work", "working", "using", "used", "use",
        "including", "include", "various", "multiple", "able",
        "strong", "excellent", "good", "years", "year",
    }
    stop_words.update(custom_stopwords)

    filtered_tokens = [w for w in tokens if w not in stop_words and len(w) > 2]
    word_freq = Counter(filtered_tokens)

    return word_freq.most_common(top_n)


def extract_skills_and_technologies(text):
    """Extract technical skills and technologies mentioned."""
    tech_patterns = [
        r"\b(python|java|javascript|typescript|c\+\+|cpp|c#|ruby|go|golang|rust|scala|kotlin|swift|php|perl|r|matlab|julia)\b",
        r"\b(react|angular|vue|django|flask|spring|nodejs|express|rails|laravel|tensorflow|pytorch|keras|sklearn|pandas|numpy)\b",
        r"\b(sql|mysql|postgresql|postgres|mongodb|redis|elasticsearch|cassandra|dynamodb|oracle|sqlite)\b",
        r"\b(aws|azure|gcp|docker|kubernetes|jenkins|gitlab|github|terraform|ansible|chef|puppet)\b",
        r"\b(api|rest|restful|graphql|microservices|kafka|rabbitmq|nginx|apache|linux|unix|git|agile|scrum|ci\/cd|devops)\b",
    ]

    skills = set()
    for pattern in tech_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        skills.update([m.lower() for m in matches])

    return skills


def calculate_keyword_match(resume_keywords, job_keywords):
    """Calculate keyword match percentage."""
    resume_words = set([word for word, _ in resume_keywords])
    job_words = set([word for word, _ in job_keywords])

    common_words = resume_words.intersection(job_words)

    if not job_words:
        return 0, common_words

    match_percentage = (len(common_words) / len(job_words)) * 100
    return match_percentage, common_words


def find_missing_keywords(resume_text, job_keywords):
    """Find important keywords from job description missing in resume."""
    missing = []

    for keyword, freq in job_keywords:
        if keyword not in resume_text:
            missing.append((keyword, freq))

    return missing[:10]


def analyze_sections(md_content):
    """Analyze resume sections."""
    sections = {}
    current_section = None
    current_content = []

    lines = md_content.split("\n")

    for line in lines:
        if line.startswith("#"):
            if current_section:
                sections[current_section] = "\n".join(current_content)

            current_section = line.strip("#").strip()
            current_content = []
        else:
            current_content.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_content)

    return sections


def generate_comparison_report(resume_file, job_file, analysis_results):
    """Generate a markdown report comparing resume to job description."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = "# Resume vs Job Description Analysis\n\n"
    report += f"**Resume:** `{os.path.basename(resume_file)}`\n"
    report += f"**Job Description:** `{os.path.basename(job_file)}`\n"
    report += f"**Generated:** {timestamp}\n\n"

    report += f"## Overall Match Score: {analysis_results['match_percentage']:.1f}%\n\n"

    if analysis_results["match_percentage"] >= 70:
        report += "**Excellent match!** Your resume aligns well with the job requirements.\n\n"
    elif analysis_results["match_percentage"] >= 50:
        report += "**Good match** with room for improvement. Consider the suggestions below.\n\n"
    else:
        report += "**Low match.** Significant improvements needed to align with job requirements.\n\n"

    report += "## Matched Keywords\n\n"
    if analysis_results["matched_keywords"]:
        report += "These important keywords appear in both your resume and the job description:\n\n"
        matched_sorted = sorted(analysis_results["matched_keywords"])
        report += ", ".join([f"`{kw}`" for kw in matched_sorted]) + "\n\n"
    else:
        report += "No significant keyword matches found.\n\n"

    report += "## Missing Keywords\n\n"
    if analysis_results["missing_keywords"]:
        report += "Consider incorporating these keywords from the job description:\n\n"
        for keyword, freq in analysis_results["missing_keywords"]:
            report += f"- `{keyword}` (appears {freq} times in job description)\n"
        report += "\n"
    else:
        report += "All major keywords are covered!\n\n"

    report += "## Technical Skills Analysis\n\n"

    missing_skills = analysis_results["job_skills"] - analysis_results["resume_skills"]
    if missing_skills:
        report += "### Missing Technical Skills\n\n"
        report += "The job description mentions these technical skills not found in your resume:\n\n"
        for skill in sorted(missing_skills):
            report += f"- `{skill}`\n"
        report += "\n"

    common_skills = analysis_results["resume_skills"].intersection(analysis_results["job_skills"])
    if common_skills:
        report += "### Matched Technical Skills\n\n"
        report += "Great! You have these required technical skills:\n\n"
        for skill in sorted(common_skills):
            report += f"- `{skill}`\n"
        report += "\n"

    report += "## Top Keywords from Job Description\n\n"
    report += "Focus on these frequently mentioned terms:\n\n"
    for keyword, freq in analysis_results["job_keywords"][:15]:
        report += f"- `{keyword}` ({freq} occurrences)\n"
    report += "\n"

    report += "## Recommendations\n\n"

    recommendations = []

    if analysis_results["match_percentage"] < 50:
        recommendations.append("- **Major revision needed**: Your resume needs significant updates to match this position")

    if len(missing_skills) > 5:
        recommendations.append("- **Skills gap**: Consider adding relevant technical skills or gaining experience in missing areas")
    elif len(missing_skills) > 0:
        recommendations.append("- **Add missing skills**: Include any of the missing technical skills you have experience with")

    if analysis_results["missing_keywords"]:
        recommendations.append("- **Incorporate keywords**: Naturally include missing keywords in your experience descriptions")

    recommendations.extend([
        "- **Quantify achievements**: Use numbers and metrics to demonstrate impact",
        "- **Mirror language**: Use similar terminology and phrases from the job description",
        "- **Customize sections**: Ensure your resume sections align with job requirements",
        "- **Highlight relevant experience**: Emphasize experiences that match the job requirements",
    ])

    for rec in recommendations:
        report += rec + "\n"

    report += "\n## Tips for Improvement\n\n"
    report += "1. **Don't just add keywords** - Integrate them naturally into your experience descriptions\n"
    report += "2. **Be honest** - Only include skills and keywords that accurately reflect your experience\n"
    report += "3. **Prioritize relevance** - Put the most relevant experience and skills first\n"
    report += "4. **Use action verbs** - Start bullet points with strong action verbs\n"
    report += "5. **Keep it concise** - Focus on achievements and impact, not just responsibilities\n"

    return report


def main():
    parser = argparse.ArgumentParser(description="Compare resume to job description")
    parser.add_argument("resume", help="Path to markdown resume file")
    parser.add_argument("job", help="Path to job description markdown file")
    parser.add_argument("-o", "--output", help="Output report file (default: outputs/comparison_report_TIMESTAMP.md)")

    args = parser.parse_args()

    if not os.path.exists(args.resume):
        print(f"Error: Resume file '{args.resume}' not found")
        return 1

    if not os.path.exists(args.job):
        print(f"Error: Job description file '{args.job}' not found")
        return 1

    print("Analyzing resume against job description...")

    resume_text, resume_md = extract_text_from_markdown(args.resume)
    job_text, job_md = extract_text_from_markdown(args.job)

    resume_keywords = extract_keywords(resume_text, 30)
    job_keywords = extract_keywords(job_text, 30)

    resume_skills = extract_skills_and_technologies(resume_text)
    job_skills = extract_skills_and_technologies(job_text)

    match_percentage, matched_keywords = calculate_keyword_match(resume_keywords, job_keywords)

    missing_keywords = find_missing_keywords(resume_text, job_keywords)

    analysis_results = {
        "match_percentage": match_percentage,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "resume_keywords": resume_keywords,
        "job_keywords": job_keywords,
        "resume_skills": resume_skills,
        "job_skills": job_skills,
        "resume_sections": analyze_sections(resume_md),
    }

    report = generate_comparison_report(args.resume, args.job, analysis_results)

    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"outputs/comparison_report_{timestamp}.md"

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nAnalysis complete!")
    print(f"Report saved to: {output_file}")
    print(f"Match score: {match_percentage:.1f}%")

    return 0


if __name__ == "__main__":
    exit(main())
