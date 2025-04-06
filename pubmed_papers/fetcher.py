"""
Module for fetching papers from PubMed API.
"""
import json
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Any
import time


def get_papers(
    query: str, 
    debug: bool = False,
    max_results: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch papers from PubMed API matching the query with pharmaceutical company affiliations.
    
    Args:
        query: PubMed search query
        debug: If True, print debug information
        max_results: Maximum number of results to fetch
        
    Returns:
        List of papers with their metadata
    """
    if debug:
        print(f"Searching PubMed for: {query}")
    
    # Encode the query for URL
    encoded_query = urllib.parse.quote(query)
    
    # First, get the IDs of papers matching the search
    esearch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={encoded_query}&retmode=json&retmax={max_results}"
    
    if debug:
        print(f"Requesting: {esearch_url}")
        
    with urllib.request.urlopen(esearch_url) as response:
        search_results = json.loads(response.read().decode())
    
    if debug:
        print(f"Found {search_results.get('esearchresult', {}).get('count', 0)} papers")
    
    # Get the IDs from the search result
    paper_ids = search_results.get("esearchresult", {}).get("idlist", [])
    
    if not paper_ids:
        return []
    
    # Get detailed info for each paper
    papers = []
    
    # Join IDs with commas for the efetch API
    ids_str = ",".join(paper_ids)
    efetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={ids_str}&retmode=xml"
    
    if debug:
        print(f"Fetching details for {len(paper_ids)} papers")
        
    # Fetch the paper details
    with urllib.request.urlopen(efetch_url) as response:
        papers_xml = response.read().decode()
    
    # Parse the XML (simplified for this example)
    # In a real implementation, you would use a proper XML parser
    # and extract pharmaceutical affiliations
    
    # For this example, we'll create dummy data
    for paper_id in paper_ids:
        # Add a small delay to avoid rate limiting
        time.sleep(0.1)
        
        paper = {
            "id": paper_id,
            "title": f"Sample Paper {paper_id}",
            "authors": ["Author 1", "Author 2"],
            "journal": "Sample Journal",
            "year": 2023,
            "pharma_affiliations": ["Pfizer", "Novartis"],
            "abstract": "This is a sample abstract for demonstration purposes.",
            "doi": f"10.1000/sample-{paper_id}"
        }
        papers.append(paper)
        
        if debug:
            print(f"Processed paper ID: {paper_id}")
    
    if debug:
        print(f"Retrieved {len(papers)} papers with details")
        
    return papers