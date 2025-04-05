#!/usr/bin/env python
"""
Command-line program to fetch research papers from PubMed with authors affiliated with 
pharmaceutical/biotech companies.
"""
import argparse
import sys
from typing import Optional

from pubmed_papers import get_papers, papers_to_csv

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Fetch research papers from PubMed with authors affiliated with pharma/biotech companies"
    )
    parser.add_argument(
        "query",
        type=str,
        help="PubMed search query (supports full PubMed query syntax)"
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Print debug information during execution"
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        help="Specify the filename to save the results (if not provided, output to console)"
    )
    
    return parser.parse_args()

def main() -> int:
    """Main entry point for the command-line program.
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    args = parse_arguments()
    
    try:
        # Get papers matching the query
        papers = get_papers(args.query, debug=args.debug)
        
        if not papers:
            print("No papers found matching the criteria.", file=sys.stderr)
            return 1
        
        # Convert papers to CSV
        csv_output = papers_to_csv(papers)
        
        # Output results
        if args.file:
            with open(args.file, 'w', encoding='utf-8') as f:
                f.write(csv_output)
            print(f"Results saved to {args.file}")
        else:
            print(csv_output)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())