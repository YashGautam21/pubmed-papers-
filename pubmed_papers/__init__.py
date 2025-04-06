"""
Tool to fetch research papers from PubMed with authors affiliated with pharmaceutical/biotech companies.
"""

from pubmed_papers.fetcher import get_papers
from pubmed_papers.formatter import papers_to_csv

__all__ = ["get_papers", "papers_to_csv"]