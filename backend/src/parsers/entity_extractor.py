"""Entity extraction utilities for parsing candidate resumes."""

import re
from typing import Optional, Tuple, List, Dict


EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', re.IGNORECASE)
PHONE_PATTERNS = [
    # International with 5+5 or 4+6 format, e.g. "+91 73490 41840", "+91-73490-41840"
    re.compile(r'(?:\+\d{1,3}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}'),
    # Standard 10-digit contiguous or with country code, e.g. "+919121763249", "9121763249"
    re.compile(r'(?:\+\d{1,3}[-.\s]?)?\d{10}'),
    # US / International standard 3+3+4, e.g. "+1 (555) 123-4567", "555-123-4567"
    re.compile(r'(?:\+\d{1,3}[-.\s]?)?(?:\(?\d{3,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}'),
]
PHONE_REGEX = PHONE_PATTERNS[0]
GITHUB_REGEX = re.compile(r'github\.com/([a-zA-Z0-9_\-]+)(?:/)?', re.IGNORECASE)
LINKEDIN_REGEX = re.compile(r'linkedin\.com/in/([a-zA-Z0-9_\-]+)(?:/)?', re.IGNORECASE)

# CGPA / Grade patterns
# Expanded separator supporting spaces, colons, hyphens, en-dashes (\u2013), em-dashes (\u2014),
# bullets (\u2022), pipes (|), equals (=), and connector phrases like "of", "is", "with"
CGPA_SEP = r'[\s:–—\-=•|]*(?:(?:of|is|was|at|with|secured|standing|aggregate|cumulative)\s+)?'

CGPA_PATTERNS = [
    # Explicit 10-scale: e.g. "CGPA: 9.28/10", "CGPA – 9.28 / 10", "CGPA of 9.28 out of 10"
    re.compile(rf'(?:cgpa|gpa|grade|score)[\s:–—\-=•|]*(?:(?:of|is|was|at|with|secured)\s+)?([0-9]+(?:\.[0-9]+)?)\s*(?:/|out\s+of)\s*10(?:\.0)?', re.IGNORECASE),
    # Explicit 4-scale: e.g. "GPA: 3.8/4.0", "CGPA – 3.8 / 4"
    re.compile(rf'(?:cgpa|gpa|grade|score)[\s:–—\-=•|]*(?:(?:of|is|was|at|with|secured)\s+)?([0-9]+(?:\.[0-9]+)?)\s*(?:/|out\s+of)\s*4(?:\.0)?', re.IGNORECASE),
    # Forward CGPA/GPA with broad separators: "CGPA – 9.28", "CGPA - 9.71", "CGPA : 8.3", "CGPA of 8.72", "CGPA 6.3"
    re.compile(rf'(?:cgpa|gpa){CGPA_SEP}([0-9]+(?:\.[0-9]+)?)', re.IGNORECASE),
    # Reverse order: "7.55 CGPA", "8.43 CGPA", "9.7 GPA", "9.28 / 10 CGPA"
    re.compile(r'\b([0-9]+(?:\.[0-9]+)?)\s*(?:/|out\s+of)\s*10(?:\.0)?\s*(?:cgpa|gpa)\b', re.IGNORECASE),
    re.compile(r'\b([0-9]+(?:\.[0-9]+)?)\s*(?:/|out\s+of)\s*4(?:\.0)?\s*(?:cgpa|gpa)\b', re.IGNORECASE),
    re.compile(r'\b([0-9]+(?:\.[0-9]+)?)\s*(?:cgpa|gpa)\b', re.IGNORECASE),
    # Naked fractions on 10 or 4 scale: "8.5/10", "9.28/10.0", "3.8/4.0"
    re.compile(r'\b([0-9]\.[0-9]{1,2})\s*/\s*10(?:\.0)?\b', re.IGNORECASE),
    re.compile(r'\b([3-4]\.[0-9]{1,2})\s*/\s*4(?:\.0)?\b', re.IGNORECASE),
    # Percentage patterns: "Percentage: 87%", "85.4%"
    re.compile(r'(?:percentage|aggregate|marks|percent)[\s:–—\-=•|]*([0-9]{2}(?:\.[0-9]+)?)\s*%', re.IGNORECASE),
    re.compile(r'\b([6-9][0-9](?:\.[0-9]+)?)\s*%\b', re.IGNORECASE),
]

DISALLOWED_GITHUB_USERNAMES = {"features", "pricing", "topics", "collections", "trending", "explore", "about", "contact"}

KNOWN_SECTIONS = [
    "summary", "professional summary", "profile", "objective",
    "skills", "technical skills", "core skills", "languages and technologies",
    "experience", "work experience", "professional experience", "internships", "employment",
    "projects", "academic projects", "personal projects", "key projects",
    "education", "academic history", "certifications", "achievements", "coursework"
]


def extract_email(text: str) -> Optional[str]:
    """Extract candidate email from text."""
    match = EMAIL_REGEX.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extract candidate phone number from header lines."""
    for line in text.split("\n")[:15]:
        for pat in PHONE_PATTERNS:
            match = pat.search(line)
            if match:
                raw = match.group(0).strip()
                digits = re.sub(r'\D', '', raw)
                if 10 <= len(digits) <= 13:
                    return raw
    return None


def extract_github(text: str, uri_links: Optional[List[str]] = None) -> Tuple[Optional[str], Optional[str]]:
    """Extract GitHub profile URL and username from text and clickable PDF URIs."""
    # Check clickable PDF URIs first
    if uri_links:
        for uri in uri_links:
            match = GITHUB_REGEX.search(uri)
            if match:
                user = match.group(1).strip()
                if user.lower() not in DISALLOWED_GITHUB_USERNAMES:
                    return f"https://github.com/{user}", user

    # Fallback to text search
    matches = GITHUB_REGEX.finditer(text)
    for match in matches:
        user = match.group(1).strip()
        if user.lower() not in DISALLOWED_GITHUB_USERNAMES:
            return f"https://github.com/{user}", user

    return None, None


def extract_linkedin(text: str, uri_links: Optional[List[str]] = None) -> Optional[str]:
    """Extract LinkedIn profile URL from text and clickable PDF URIs."""
    if uri_links:
        for uri in uri_links:
            match = LINKEDIN_REGEX.search(uri)
            if match:
                return f"https://www.linkedin.com/in/{match.group(1)}"
    match = LINKEDIN_REGEX.search(text)
    return f"https://www.linkedin.com/in/{match.group(1)}" if match else None


def extract_cgpa(text: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Extract CGPA and normalize to a 10.0 scale.
    Handles 10-point scale, 4-point scale, and percentages.
    """
    for pat in CGPA_PATTERNS:
        match = pat.search(text)
        if match:
            raw_val = match.group(1)
            raw_str = match.group(0)
            try:
                val = float(raw_val)
                if val <= 0.0 or val > 100.0:
                    continue
                # Check scale
                if "/ 4" in raw_str.lower() or "/4" in raw_str.lower() or "out of 4" in raw_str.lower():
                    # 4.0 scale -> convert to 10.0 scale
                    normalized = round((val / 4.0) * 10.0, 2)
                    return min(10.0, normalized), raw_str.strip()
                elif "%" in raw_str:
                    # Percentage -> normalize to 10.0 scale
                    normalized = round(val / 10.0, 2)
                    return min(10.0, normalized), raw_str.strip()
                elif val <= 4.0 and "/10" not in raw_str and "10" not in raw_str:
                    # Likely a 4-point scale if <= 4.0 and not on 10 scale
                    normalized = round((val / 4.0) * 10.0, 2)
                    return min(10.0, normalized), raw_str.strip()
                elif val <= 10.0:
                    return round(val, 2), raw_str.strip()
            except ValueError:
                continue
    return None, None


def extract_candidate_name(text: str, file_name: str, author_metadata: Optional[str] = None) -> str:
    """Extract candidate name from top lines of resume, author metadata, or fallback to file stem."""
    raw_lines = [l.strip() for l in text.split("\n") if l.strip()]
    ignored_keywords = {
        "resume", "curriculum vitae", "cv", "portfolio", "profile", "contact",
        "phone", "email", "github", "linkedin", "leetcode", "hackerrank",
        "objective", "summary", "skills", "experience", "education",
        "motivated", "developer", "engineer", "software", "contribute"
    }

    # Case 1: First two lines are single name parts (e.g. 'Prathamesh' on line 0, 'Patil' on line 1)
    if len(raw_lines) >= 2:
        w0 = raw_lines[0].split()
        w1 = raw_lines[1].split()
        if len(w0) == 1 and len(w1) == 1:
            if not any(k in raw_lines[0].lower() or k in raw_lines[1].lower() for k in ignored_keywords):
                if raw_lines[0].isalpha() and raw_lines[1].isalpha():
                    return f"{raw_lines[0].capitalize()} {raw_lines[1].capitalize()}"

    # Case 2: Scan first 8 lines for 2 to 4 name words
    for line in raw_lines[:8]:
        cleaned = re.sub(r'[^\w\s]', ' ', line).strip()
        words = cleaned.split()
        if 2 <= len(words) <= 4:
            lower = cleaned.lower()
            if not any(k in lower for k in ignored_keywords):
                if not re.search(r'\d', cleaned) and "@" not in cleaned and "http" not in lower:
                    if all(w.isalpha() for w in words):
                        return " ".join([w.capitalize() for w in words])

    # Case 3: Check author metadata if valid
    if author_metadata and author_metadata.strip():
        auth = author_metadata.strip()
        if 2 <= len(auth.split()) <= 4 and not any(k in auth.lower() for k in ignored_keywords):
            if not re.search(r'\d', auth) and "@" not in auth:
                return auth.title()

    # Fallback to filename
    base = re.sub(r'candidate_0*(\d+)', r'Candidate \1', file_name.replace('.pdf', '').replace('.docx', '').replace('.txt', ''))
    return base.replace('_', ' ').replace('-', ' ').title()


def segment_sections(text: str) -> Dict[str, str]:
    """Segment resume text into logical sections based on headings."""
    sections: Dict[str, List[str]] = {
        "header": [],
        "summary": [],
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
        "other": []
    }

    current_section = "header"
    lines = text.split("\n")

    for line in lines:
        cleaned = line.strip().lower()
        matched = False
        for heading in KNOWN_SECTIONS:
            # Check if line looks like a section header (short line matching heading)
            if cleaned == heading or cleaned.startswith(f"{heading}:") or cleaned.startswith(f"{heading} -"):
                matched = True
                if "skill" in heading or "language" in heading:
                    current_section = "skills"
                elif "project" in heading:
                    current_section = "projects"
                elif "experience" in heading or "internship" in heading or "employment" in heading:
                    current_section = "experience"
                elif "summary" in heading or "objective" in heading or "profile" in heading:
                    current_section = "summary"
                elif "education" in heading or "coursework" in heading:
                    current_section = "education"
                else:
                    current_section = "other"
                break
        
        if not matched:
            sections[current_section].append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items()}


def detect_related_experience(text: str, experience_text: str) -> Tuple[bool, float]:
    """Detect if candidate has industry/internship experience and estimate years."""
    combined = (experience_text + "\n" + text).lower()
    
    exp_indicators = [
        "software engineer intern", "sde intern", "ai intern", "ml intern",
        "backend intern", "software developer intern", "research intern",
        "software engineer", "backend developer", "full stack developer",
        "data science intern", "machine learning intern", "contractor"
    ]
    
    has_role = any(role in combined for role in exp_indicators)
    
    # Estimate duration if mentions months/years
    years = 0.0
    month_match = re.search(r'(\d+)\s*(?:month|mos|months)', combined)
    if month_match:
        years += float(month_match.group(1)) / 12.0

    year_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:year|yrs|years)', combined)
    if year_match:
        years += float(year_match.group(1))

    if has_role and years == 0.0:
        years = 0.5  # default 6-month internship estimate if role found

    return has_role, round(years, 1)
