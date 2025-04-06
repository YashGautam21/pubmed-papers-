"""
Module for formatting paper data into various output formats.
"""
import csv
import io
from typing import Dict, List, Any


def papers_to_csv(papers: List[Dict[str, Any]]) -> str:
    """
    Convert a list of papers to CSV format.
    
    Args:
        papers: List of paper dictionaries
        
    Returns:
        CSV string containing the papers data
    """
    if not papers:
        return ""
    
    # Define CSV columns
    fieldnames = [
        "id", "title", "authors", "journal", "year", 
        "pharma_affiliations", "abstract", "doi"
    ]
    
    # Use StringIO to create a CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for paper in papers:
        # Convert list fields to strings for CSV
        paper_row = paper.copy()
        
        # Convert lists to comma-separated strings
        if "authors" in paper_row and isinstance(paper_row["authors"], list):
            paper_row["authors"] = "; ".join(paper_row["authors"])
            
        if "pharma_affiliations" in paper_row and isinstance(paper_row["pharma_affiliations"], list):
            paper_row["pharma_affiliations"] = "; ".join(paper_row["pharma_affiliations"])
        
        writer.writerow(paper_row)
    
    return output.getvalue()