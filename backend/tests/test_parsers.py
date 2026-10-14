"""Tests for resume parsers and entity extractors."""

import pytest
from src.parsers.entity_extractor import (
    extract_email,
    extract_phone,
    extract_github,
    extract_cgpa,
    extract_candidate_name,
)
from src.parsers.resume_parser import ResumeParser


def test_extract_email():
    text = "Contact me at john.doe@example.com or j_doe99@university.edu"
    assert extract_email(text) == "john.doe@example.com"


def test_extract_phone():
    # 5+5 format (Prathamesh Patil)
    text1 = "+91 73490 41840 | Bengaluru, Karnataka\nprathameshpatil330@gmail.com"
    assert extract_phone(text1) == "+91 73490 41840"

    # Standard contiguous format (V Sree Raghu Vardhan)
    text2 = "Hyderabad, India | +91 9121763249 | Linkedin"
    assert extract_phone(text2) == "+91 9121763249"

    # US format
    text3 = "John Doe\n(555) 123-4567\njohn@example.com"
    assert extract_phone(text3) == "(555) 123-4567"


def test_extract_github_from_text():
    text = "GitHub: github.com/octocat | Portfolio: octocat.dev"
    url, username = extract_github(text)
    assert url == "https://github.com/octocat"
    assert username == "octocat"


def test_extract_github_from_uri():
    uris = ["https://linkedin.com/in/someone", "https://github.com/developer123"]
    url, username = extract_github("some text", uris)
    assert url == "https://github.com/developer123"
    assert username == "developer123"


def test_extract_cgpa_10_scale():
    text = "Bachelor of Technology in CS, CGPA: 8.75/10"
    val, raw = extract_cgpa(text)
    assert val == 8.75
    assert "8.75/10" in raw


def test_extract_cgpa_4_scale():
    text = "BS in Computer Science | GPA: 3.8 / 4.0"
    val, raw = extract_cgpa(text)
    # 3.8 / 4 * 10 = 9.5
    assert val == 9.5


def test_extract_cgpa_percentage():
    text = "Academic Performance: Aggregate: 82.5%"
    val, raw = extract_cgpa(text)
    # 82.5% -> 8.25
    assert val == 8.25


def test_extract_cgpa_en_dash_and_hyphen():
    # Candidate 30 actual format with en-dash: "• CGPA – 9.28"
    c30_text = "Chaitanya Bharati Institute of Technology\n• CGPA – 9.28\n• Student Lead"
    val, raw = extract_cgpa(c30_text)
    assert val == 9.28

    # Candidate 38 format with ASCII hyphen: "CGPA - 9.71"
    c38_text = "New Horizon College of Engineering | CGPA - 9.71"
    val, raw = extract_cgpa(c38_text)
    assert val == 9.71


def test_extract_cgpa_inverted_and_prepositions():
    # Candidate 15 & 24 inverted format: "7.55 CGPA", "8.43 CGPA"
    val, _ = extract_cgpa("Completed degree with 7.55 CGPA in 2024")
    assert val == 7.55

    val, _ = extract_cgpa("(2021-2025) - 8.43 CGPA")
    assert val == 8.43

    # Candidate 23 format with preposition: "CGPA of 8.72"
    val, _ = extract_cgpa("Engineering College with a CGPA of 8.72.")
    assert val == 8.72


def test_parser_unreadable_file_tolerance(tmp_path):
    bad_file = tmp_path / "corrupt.pdf"
    bad_file.write_bytes(b"NOT A REAL PDF CONTENT RANDOM BYTES")
    parsed = ResumeParser.parse_file(bad_file)
    assert parsed.parsing_status != "success" or parsed.full_text == ""
