#!/usr/bin/env python3
"""
AI-powered job fit analysis - Compare resume to job description with intelligent suggestions.
Uses OpenRouter API for LLM access.
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

DEFAULT_MODEL = "anthropic/claude-sonnet-4"


def extract_json(text):
    """Extract JSON from a response that may be wrapped in markdown code fences."""
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

    return text


def analyze_job_fit_with_llm(resume_text, job_text, api_key, model=DEFAULT_MODEL):
    """Use OpenRouter API to analyze job fit and provide suggestions."""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={"HTTP-Referer": "https://github.com/markdown2resume"},
    )

    prompt = """You are an expert career counselor and recruiter specializing in resume optimization.
Analyze the following resume against the job description and provide a comprehensive fit analysis.

Your analysis should include:

1. **Overall Fit Score** (0-100%): Provide a numerical score of how well the candidate matches the job

2. **Strengths**: List 3-5 key strengths where the candidate's experience aligns well with the job requirements

3. **Gaps**: Identify 3-5 areas where the candidate lacks required skills or experience

4. **Keyword Analysis**: List important keywords from the job description that are:
   - Present in the resume
   - Missing from the resume but should be added

5. **Experience Match**: Analyze how well the candidate's work experience matches the job requirements

6. **Skills Assessment**: Compare technical and soft skills requirements vs what the candidate has

7. **Specific Suggestions**: Provide 5-7 actionable suggestions to improve the resume for this specific job

8. **Risk Factors**: Identify any potential red flags or concerns a recruiter might have

9. **Competitive Edge**: What unique value does this candidate bring that others might not?

Return your analysis in JSON format with this structure:
{
    "fit_score": number (0-100),
    "fit_summary": "brief overall assessment",
    "strengths": [
        {"point": "strength description", "relevance": "how it relates to the job"}
    ],
    "gaps": [
        {"gap": "missing skill/experience", "importance": "critical|high|medium|low", "suggestion": "how to address"}
    ],
    "keywords": {
        "matched": ["keyword1", "keyword2"],
        "missing": ["keyword3", "keyword4"],
        "recommended_additions": ["keyword5", "keyword6"]
    },
    "experience_match": {
        "score": number (0-100),
        "analysis": "detailed analysis",
        "relevant_roles": ["role1", "role2"]
    },
    "skills_assessment": {
        "technical_match": number (0-100),
        "soft_skills_match": number (0-100),
        "missing_technical": ["skill1", "skill2"],
        "missing_soft": ["skill3", "skill4"]
    },
    "suggestions": [
        {
            "priority": "high|medium|low",
            "suggestion": "specific actionable suggestion",
            "implementation": "how to implement this suggestion"
        }
    ],
    "risk_factors": [
        {"risk": "description", "mitigation": "how to address"}
    ],
    "competitive_edge": ["unique point 1", "unique point 2"]
}

RESUME:
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert career counselor and recruiter specializing in matching candidates to jobs. Always respond with valid JSON."},
                {"role": "user", "content": prompt + resume_text + "\n\nJOB DESCRIPTION:\n" + job_text},
            ],
            temperature=0.3,
        )

        result = extract_json(response.choices[0].message.content)
        return result

    except Exception as e:
        print(f"Error analyzing job fit: {str(e)}")
        return None


def generate_job_fit_report(resume_file, job_file, analysis, model):
    """Generate a markdown report of the job fit analysis."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = "# Job Fit Analysis Report\n\n"
    report += f"**Resume:** `{os.path.basename(resume_file)}`\n"
    report += f"**Job Description:** `{os.path.basename(job_file)}`\n"
    report += f"**Generated:** {timestamp}\n"
    report += f"**Analysis Model:** {model}\n\n"

    # Overall Fit Score
    fit_score = analysis.get("fit_score", 0)
    if fit_score >= 80:
        assessment = "Excellent Match"
    elif fit_score >= 60:
        assessment = "Good Match"
    elif fit_score >= 40:
        assessment = "Moderate Match"
    else:
        assessment = "Poor Match"

    report += f"## Overall Fit: {fit_score}% - {assessment}\n\n"
    report += f"**Summary:** {analysis.get('fit_summary', 'No summary available')}\n\n"

    # Strengths
    report += "## Key Strengths\n\n"
    strengths = analysis.get("strengths", [])
    if strengths:
        for strength in strengths:
            report += f"- **{strength.get('point', '')}**\n"
            report += f"  - *Relevance:* {strength.get('relevance', '')}\n\n"
    else:
        report += "No significant strengths identified.\n\n"

    # Gaps
    report += "## Gaps to Address\n\n"
    gaps = analysis.get("gaps", [])
    if gaps:
        for gap in gaps:
            importance = gap.get("importance", "medium")
            report += f"- **{gap.get('gap', '')}** ({importance} priority)\n"
            report += f"  - *Suggestion:* {gap.get('suggestion', '')}\n\n"
    else:
        report += "No significant gaps identified.\n\n"

    # Keyword Analysis
    report += "## Keyword Analysis\n\n"
    keywords = analysis.get("keywords", {})

    report += "### Matched Keywords\n"
    matched = keywords.get("matched", [])
    if matched:
        report += ", ".join([f"`{kw}`" for kw in matched]) + "\n\n"
    else:
        report += "No matching keywords found.\n\n"

    report += "### Missing Keywords\n"
    missing = keywords.get("missing", [])
    if missing:
        report += ", ".join([f"`{kw}`" for kw in missing]) + "\n\n"
    else:
        report += "All key terms are present.\n\n"

    report += "### Recommended Additions\n"
    recommended = keywords.get("recommended_additions", [])
    if recommended:
        report += "Consider naturally incorporating these terms: "
        report += ", ".join([f"`{kw}`" for kw in recommended]) + "\n\n"

    # Experience Match
    report += "## Experience Match\n\n"
    exp_match = analysis.get("experience_match", {})
    exp_score = exp_match.get("score", 0)
    report += f"**Score:** {exp_score}%\n\n"
    report += f"{exp_match.get('analysis', '')}\n\n"

    relevant_roles = exp_match.get("relevant_roles", [])
    if relevant_roles:
        report += "**Most Relevant Roles:**\n"
        for role in relevant_roles:
            report += f"- {role}\n"
        report += "\n"

    # Skills Assessment
    report += "## Skills Assessment\n\n"
    skills = analysis.get("skills_assessment", {})

    tech_match = skills.get("technical_match", 0)
    soft_match = skills.get("soft_skills_match", 0)

    report += f"- **Technical Skills Match:** {tech_match}%\n"
    report += f"- **Soft Skills Match:** {soft_match}%\n\n"

    missing_tech = skills.get("missing_technical", [])
    if missing_tech:
        report += "**Missing Technical Skills:** "
        report += ", ".join([f"`{skill}`" for skill in missing_tech]) + "\n\n"

    missing_soft = skills.get("missing_soft", [])
    if missing_soft:
        report += "**Missing Soft Skills:** "
        report += ", ".join([f"`{skill}`" for skill in missing_soft]) + "\n\n"

    # Actionable Suggestions
    report += "## Actionable Suggestions\n\n"
    suggestions = analysis.get("suggestions", [])

    priority_order = {"high": 1, "medium": 2, "low": 3}
    suggestions.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 2))

    for i, suggestion in enumerate(suggestions, 1):
        priority = suggestion.get("priority", "medium")
        report += f"{i}. **[{priority.upper()}]** {suggestion.get('suggestion', '')}\n"
        report += f"   - *How to implement:* {suggestion.get('implementation', '')}\n\n"

    # Risk Factors
    risks = analysis.get("risk_factors", [])
    if risks:
        report += "## Risk Factors\n\n"
        for risk in risks:
            report += f"- **Risk:** {risk.get('risk', '')}\n"
            report += f"  - *Mitigation:* {risk.get('mitigation', '')}\n\n"

    # Competitive Edge
    edges = analysis.get("competitive_edge", [])
    if edges:
        report += "## Your Competitive Edge\n\n"
        for edge in edges:
            report += f"- {edge}\n"
        report += "\n"

    # Next Steps
    report += "## Next Steps\n\n"
    report += "1. **Immediate Actions** (Do today):\n"
    report += "   - Review and implement high-priority suggestions\n"
    report += "   - Add missing critical keywords naturally throughout your resume\n"
    report += "   - Update your summary/objective to align with the job requirements\n\n"

    report += "2. **Short-term Actions** (This week):\n"
    report += "   - Reorganize experience bullets to emphasize relevant achievements\n"
    report += "   - Quantify accomplishments where possible\n"
    report += "   - Tailor technical skills section to match job requirements\n\n"

    report += "3. **Before Applying**:\n"
    report += "   - Proofread the updated resume\n"
    report += "   - Ensure formatting is consistent\n"
    report += "   - Write a tailored cover letter addressing any gaps\n\n"

    # Tips
    report += "## Pro Tips\n\n"
    report += "- Don't just add keywords - integrate them naturally into your accomplishments\n"
    report += "- Focus on achievements and impact, not just responsibilities\n"
    report += "- Mirror the language and terminology used in the job description\n"
    report += "- Keep the most relevant information in the top third of your resume\n"
    report += "- Consider reordering sections to highlight your strongest qualifications first\n"

    return report


def main():
    parser = argparse.ArgumentParser(description="AI-powered job fit analysis for your resume")
    parser.add_argument("resume", help="Path to markdown resume file")
    parser.add_argument("job", help="Path to job description markdown file")
    parser.add_argument("-o", "--output", help="Output report file (default: outputs/job_fit_analysis_TIMESTAMP.md)")
    parser.add_argument("-k", "--api-key", help="OpenRouter API key (overrides .env file)")
    parser.add_argument("-m", "--model", help=f"Model to use (default: {DEFAULT_MODEL})")

    args = parser.parse_args()

    if not os.path.exists(args.resume):
        print(f"Error: Resume file '{args.resume}' not found")
        return 1

    if not os.path.exists(args.job):
        print(f"Error: Job description file '{args.job}' not found")
        return 1

    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OpenRouter API key required.")
        print("Please provide it via one of these methods:")
        print("1. Create a .env file with OPENROUTER_API_KEY=your-key")
        print("2. Set OPENROUTER_API_KEY environment variable")
        print("3. Use --api-key command line option")
        return 1

    model = args.model or os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)

    print(f"Analyzing job fit using {model}...")
    print(f"Resume: {args.resume}")
    print(f"Job: {args.job}")

    resume_text = extract_text_from_markdown(args.resume)
    job_text = extract_text_from_markdown(args.job)

    print("\nPerforming AI analysis...")
    analysis = analyze_job_fit_with_llm(resume_text, job_text, api_key, model)

    if not analysis:
        print("Error: Failed to analyze job fit")
        return 1

    report = generate_job_fit_report(args.resume, args.job, analysis, model)

    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"outputs/job_fit_analysis_{timestamp}.md"

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    fit_score = analysis.get("fit_score", 0)
    print(f"\nAnalysis complete!")
    print(f"Report saved to: {output_file}")
    print(f"Fit score: {fit_score}%")

    if fit_score >= 80:
        print("Excellent match! You're a strong candidate for this position.")
    elif fit_score >= 60:
        print("Good match! With some adjustments, you'll be very competitive.")
    elif fit_score >= 40:
        print("Moderate match. Focus on highlighting transferable skills.")
    else:
        print("Significant gaps to address. Consider gaining more relevant experience.")

    return 0


if __name__ == "__main__":
    exit(main())
