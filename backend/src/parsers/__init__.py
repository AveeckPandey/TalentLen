"""Parsers module."""
from src.parsers.resume_parser import ResumeParser
from src.parsers.entity_extractor import extract_email, extract_github, extract_cgpa

__all__ = ["ResumeParser", "extract_email", "extract_github", "extract_cgpa"]
