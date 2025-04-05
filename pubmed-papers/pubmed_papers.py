"""
Module for fetching research papers from PubMed with authors affiliated with pharmaceutical/biotech companies.
"""
from typing import Dict, List, Optional, Tuple, Any
import re
import csv
import logging
import sys
from io import StringIO
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import quote

import requests
from rich.logging import RichHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("pubmed_papers")

# Constants
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_SEARCH_URL = f"{PUBMED_BASE_URL}/esearch.fcgi"
PUBMED_FETCH_URL = f"{PUBMED_BASE_URL}/efetch.fcgi"
PUBMED_SUMMARY_URL = f"{PUBMED_BASE_URL}/esummary.fcgi"

# Non-academic institution patterns
NON_ACADEMIC_PATTERNS = [
    r'(?i)(pharma|biotech|therapeutics|biosciences|laboratories|inc\.|corp\.|ltd\.|llc|gmbh|co\.|biopharma|biopharm)',
    r'(?i)(?<!medical )(company|corporation)',
    r'(?i)(?<!university )labs',
]

# Academic institution patterns to exclude
ACADEMIC_PATTERNS = [
    r'(?i)(university|college|institute|school|academy|medical center|medical school|hospital|clinic|foundation)',
    r'(?i)(department|faculty|division|center for)',
]

@dataclass
class Author:
    """Data class to store author information."""
    name: str
    affiliation: str
    email: Optional[str] = None
    is_corresponding: bool = False

@dataclass
class Paper:
    """Data class to store paper information."""
    pubmed_id: str
    title: str
    publication_date: str
    authors: List[Author]
    non_academic_authors: List[Author]
    
    @property
    def corresponding_author_email(self) -> Optional[str]:
        """Get the email of the corresponding author if available."""
        for author in self.authors:
            if author.is_corresponding and author.email:
                return author.email
        return None
    
    @property
    def company_affiliations(self) -> List[str]:
        """Get unique company affiliations of non-academic authors."""
        return list(set(author.affiliation for author in self.non_academic_authors))


class PubMedClient:
    """Client for interacting with the PubMed API."""
    
    def __init__(self, debug: bool = False):
        """Initialize the PubMed client.
        
        Args:
            debug: Whether to enable debug logging.
        """
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)
    
    def search_papers(self, query: str, max_results: int = 100) -> List[str]:
        """Search for papers matching the query.
        
        Args:
            query: The search query using PubMed query syntax.
            max_results: Maximum number of results to return.
            
        Returns:
            List of PubMed IDs.
        """
        logger.debug(f"Searching for papers with query: {query}")
        
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results,
        }
        
        try:
            response = requests.get(PUBMED_SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "esearchresult" not in data or "idlist" not in data["esearchresult"]:
                logger.warning("No search results found or unexpected API response format")
                return []
            
            paper_ids = data["esearchresult"]["idlist"]
            logger.debug(f"Found {len(paper_ids)} papers")
            return paper_ids
            
        except requests.RequestException as e:
            logger.error(f"Error searching PubMed: {e}")
            return []
    
    def fetch_paper_details(self, paper_ids: List[str]) -> List[Paper]:
        """Fetch detailed information for the given paper IDs.
        
        Args:
            paper_ids: List of PubMed IDs.
            
        Returns:
            List of Paper objects.
        """
        if not paper_ids:
            return []
        
        logger.debug(f"Fetching details for {len(paper_ids)} papers")
        
        # Process in batches of 50 to avoid API limitations
        batch_size = 50
        all_papers = []
        
        for i in range(0, len(paper_ids), batch_size):
            batch_ids = paper_ids[i:i+batch_size]
            batch_papers = self._fetch_batch(batch_ids)
            all_papers.extend(batch_papers)
            
        return all_papers
    
    def _fetch_batch(self, paper_ids: List[str]) -> List[Paper]:
        """Fetch a batch of paper details from PubMed.
        
        Args:
            paper_ids: List of PubMed IDs in the batch.
            
        Returns:
            List of Paper objects.
        """
        id_str = ",".join(paper_ids)
        params = {
            "db": "pubmed",
            "id": id_str,
            "retmode": "xml",
        }
        
        try:
            response = requests.get(PUBMED_FETCH_URL, params=params)
            response.raise_for_status()
            
            return self._parse_xml_response(response.text)
            
        except requests.RequestException as e:
            logger.error(f"Error fetching paper details: {e}")
            return []
    
    def _parse_xml_response(self, xml_text: str) -> List[Paper]:
        """Parse the XML response from PubMed.
        
        Args:
            xml_text: XML response text.
            
        Returns:
            List of Paper objects.
        """
        papers = []
        
        try:
            root = ET.fromstring(xml_text)
            article_elements = root.findall(".//PubmedArticle")
            
            for article in article_elements:
                try:
                    paper = self._parse_article(article)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    pmid = article.find(".//PMID")
                    pmid_text = pmid.text if pmid is not None else "unknown"
                    logger.error(f"Error parsing article (PMID: {pmid_text}): {e}")
                    continue
                    
        except ET.ParseError as e:
            logger.error(f"Error parsing XML response: {e}")
        
        return papers
    
    def _parse_article(self, article_element: ET.Element) -> Optional[Paper]:
        """Parse a single PubmedArticle element.
        
        Args:
            article_element: The PubmedArticle XML element.
            
        Returns:
            Paper object if parsing is successful, None otherwise.
        """
        # Extract PMID
        pmid_elem = article_element.find(".//PMID")
        if pmid_elem is None:
            logger.warning("Article missing PMID, skipping")
            return None
        
        pubmed_id = pmid_elem.text
        
        # Extract title
        title_elem = article_element.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else "No title available"
        
        # Extract publication date
        pub_date = self._extract_publication_date(article_element)
        
        # Extract authors
        authors = self._extract_authors(article_element)
        
        # Filter non-academic authors
        non_academic_authors = [
            author for author in authors 
            if author.affiliation and self._is_non_academic_affiliation(author.affiliation)
        ]
        
        # Only include papers with at least one non-academic author
        if not non_academic_authors:
            logger.debug(f"PMID {pubmed_id}: No non-academic authors found, skipping")
            return None
        
        return Paper(
            pubmed_id=pubmed_id,
            title=title,
            publication_date=pub_date,
            authors=authors,
            non_academic_authors=non_academic_authors
        )
    
    def _extract_publication_date(self, article_element: ET.Element) -> str:
        """Extract the publication date from the article.
        
        Args:
            article_element: The PubmedArticle XML element.
            
        Returns:
            Formatted publication date string.
        """
        # Try PubDate first
        pub_date_elem = article_element.find(".//PubDate")
        if pub_date_elem is not None:
            year_elem = pub_date_elem.find("Year")
            month_elem = pub_date_elem.find("Month")
            day_elem = pub_date_elem.find("Day")
            
            year = year_elem.text if year_elem is not None else ""
            month = month_elem.text if month_elem is not None else ""
            day = day_elem.text if day_elem is not None else ""
            
            # Convert month name to number if needed
            if month.isalpha():
                try:
                    from datetime import datetime
                    month = str(datetime.strptime(month[:3], "%b").month).zfill(2)
                except ValueError:
                    month = ""
            
            if year and month and day:
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            elif year and month:
                return f"{year}-{month.zfill(2)}"
            elif year:
                return year
        
        # Fallback to MedlineDate
        medline_date_elem = article_element.find(".//MedlineDate")
        if medline_date_elem is not None and medline_date_elem.text:
            return medline_date_elem.text
        
        return "Unknown date"
    
    def _extract_authors(self, article_element: ET.Element) -> List[Author]:
        """Extract authors and their affiliations from the article.
        
        Args:
            article_element: The PubmedArticle XML element.
            
        Returns:
            List of Author objects.
        """
        authors = []
        author_list = article_element.find(".//AuthorList")
        
        if author_list is None:
            return authors
        
        for author_elem in author_list.findall("Author"):
            name_parts = []
            
            last_name = author_elem.find("LastName")
            if last_name is not None and last_name.text:
                name_parts.append(last_name.text)
                
            fore_name = author_elem.find("ForeName")
            if fore_name is not None and fore_name.text:
                name_parts.append(fore_name.text)
            else:
                initials = author_elem.find("Initials")
                if initials is not None and initials.text:
                    name_parts.append(initials.text)
            
            # Handle collective author name
            if not name_parts:
                collective_name = author_elem.find("CollectiveName")
                if collective_name is not None and collective_name.text:
                    name_parts.append(collective_name.text)
            
            name = " ".join(reversed(name_parts)) if name_parts else "Unknown Author"
            
            # Extract affiliation
            affiliation = self._extract_affiliation(author_elem)
            
            # Extract email (if available) and check if corresponding author
            email, is_corresponding = self._extract_email_and_correspondence(author_elem, article_element)
            
            authors.append(Author(
                name=name,
                affiliation=affiliation,
                email=email,
                is_corresponding=is_corresponding
            ))
        
        # If no clear corresponding author, try to infer from other metadata
        if not any(author.is_corresponding for author in authors) and authors:
            # Try to find correspondence info in article
            correspondence_elem = article_element.find(".//Correspondence")
            if correspondence_elem is not None and correspondence_elem.text:
                # Try to match email in correspondence to an author
                email_match = re.search(r'[\w\.-]+@[\w\.-]+', correspondence_elem.text)
                if email_match:
                    email = email_match.group(0)
                    # Update the first author if no matches
                    authors[0].email = email
                    authors[0].is_corresponding = True
            else:
                # Default to first author as corresponding if nothing else
                authors[0].is_corresponding = True
        
        return authors
    
    def _extract_affiliation(self, author_elem: ET.Element) -> str:
        """Extract affiliation from the author element.
        
        Args:
            author_elem: The Author XML element.
            
        Returns:
            Affiliation string.
        """
        # Try new format first (AffiliationInfo)
        affiliation_info = author_elem.find(".//AffiliationInfo/Affiliation")
        if affiliation_info is not None and affiliation_info.text:
            return affiliation_info.text
        
        # Try old format (direct Affiliation)
        affiliation = author_elem.find("Affiliation")
        if affiliation is not None and affiliation.text:
            return affiliation.text
        
        return ""
    
    def _extract_email_and_correspondence(self, author_elem: ET.Element, article_element: ET.Element) -> Tuple[Optional[str], bool]:
        """Extract email and check if the author is the corresponding author.
        
        Args:
            author_elem: The Author XML element.
            article_element: The full PubmedArticle XML element.
            
        Returns:
            Tuple of (email, is_corresponding)
        """
        email = None
        is_corresponding = False
        
        # Check for email in affiliation text
        affiliation = self._extract_affiliation(author_elem)
        if affiliation:
            email_match = re.search(r'[\w\.-]+@[\w\.-]+', affiliation)
            if email_match:
                email = email_match.group(0)
                # If email is in affiliation, likely a corresponding author
                is_corresponding = True
        
        # Check EqualContrib attribute (some articles use this)
        equal_contrib = author_elem.get("EqualContrib")
        if equal_contrib and equal_contrib.lower() == "yes":
            is_corresponding = True
        
        # Check CorrespAuthor attribute
        corresp_author = author_elem.get("CorrespAuthor")
        if corresp_author and corresp_author.lower() == "yes":
            is_corresponding = True
        
        return email, is_corresponding
    
    def _is_non_academic_affiliation(self, affiliation: str) -> bool:
        """Determine if the affiliation is a non-academic institution.
        
        Args:
            affiliation: The affiliation string.
            
        Returns:
            True if the affiliation is non-academic, False otherwise.
        """
        # Check if matches non-academic pattern
        for pattern in NON_ACADEMIC_PATTERNS:
            if re.search(pattern, affiliation):
                # Make sure it's not actually academic
                is_academic = any(re.search(acad_pattern, affiliation) for acad_pattern in ACADEMIC_PATTERNS)
                if not is_academic:
                    return True
        
        return False


def get_papers(query: str, debug: bool = False) -> List[Paper]:
    """Search for papers and filter for those with non-academic authors.
    
    Args:
        query: The search query.
        debug: Whether to enable debug logging.
        
    Returns:
        List of Paper objects meeting the criteria.
    """
    client = PubMedClient(debug=debug)
    paper_ids = client.search_papers(query)
    papers = client.fetch_paper_details(paper_ids)
    
    logger.info(f"Found {len(papers)} papers with non-academic authors")
    return papers


def papers_to_csv(papers: List[Paper]) -> str:
    """Convert papers to CSV format.
    
    Args:
        papers: List of Paper objects.
        
    Returns:
        CSV formatted string.
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "PubmedID", 
        "Title", 
        "Publication Date", 
        "Non-academic Author(s)", 
        "Company Affiliation(s)", 
        "Corresponding Author Email"
    ])
    
    # Write data rows
    for paper in papers:
        writer.writerow([
            paper.pubmed_id,
            paper.title,
            paper.publication_date,
            "; ".join(author.name for author in paper.non_academic_authors),
            "; ".join(paper.company_affiliations),
            paper.corresponding_author_email or ""
        ])
    
    return output.getvalue()