"""
PubMed Papers - Tool to fetch research papers from PubMed with authors affiliated with 
pharmaceutical/biotech companies.
"""

from .pubmed_papers import (
    get_papers,
    papers_to_csv,
    Paper,
    Author,
    PubMedClient,
)

__all__ = [
    "get_papers",
    "papers_to_csv",
    "Paper",
    "Author",
    "PubMedClient",
]