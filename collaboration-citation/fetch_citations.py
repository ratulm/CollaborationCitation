#!/usr/bin/env python3
"""
Fetch citation counts from Semantic Scholar for papers in DBLP.

This script reads papers from dblp.xml.gz, filters by year range,
and fetches citationCount and influentialCitationCount from Semantic Scholar.
"""

import argparse
import csv
import gzip
import os
import time
import sys
from typing import Dict, List, Optional, Set
import requests
import xmltodict

# Semantic Scholar API configuration
API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
if not API_KEY:
    print("Error: SEMANTIC_SCHOLAR_API_KEY environment variable is not set.", file=sys.stderr)
    print("Please set it with: export SEMANTIC_SCHOLAR_API_KEY='your-api-key'", file=sys.stderr)
    sys.exit(1)

BATCH_API_URL = "https://api.semanticscholar.org/graph/v1/paper/batch"
RATE_LIMIT_DELAY = 1.0  # seconds between requests

# Batch size for API requests (max 500 per Semantic Scholar docs)
BATCH_SIZE = 500


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch citation counts from Semantic Scholar for DBLP papers"
    )
    parser.add_argument(
        "--from-year",
        type=int,
        default=2015,
        help="Start year for filtering papers (default: 2015)",
    )
    parser.add_argument(
        "--to-year",
        type=int,
        default=2025,
        help="End year for filtering papers (default: 2025)",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="dblp.xml.gz",
        help="Input DBLP XML file (default: dblp.xml.gz)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="dblp-citations.csv",
        help="Output CSV file (default: dblp-citations.csv)",
    )
    parser.add_argument(
        "--search-no-doi",
        action="store_true",
        default=False,
        help="Search for papers without DOI using search API (slower) (default: False)",
    )
    parser.add_argument(
        "--search-notfound-doi",
        action="store_true",
        default=False,
        help="Retry papers with DOI that weren't found via batch API using search API (slower) (default: False)",
    )
    parser.add_argument(
        "--resume-from",
        type=str,
        default=None,
        help="Resume from a previous run by reading existing results from this CSV file",
    )
    parser.add_argument(
        "--papers",
        type=str,
        default="papers.csv",
        help="CSV file with papers to fetch citations for (must have dblp_key column) (default: papers.csv)",
    )
    return parser.parse_args()


def extract_paper_info(entry: Dict, from_year: int, to_year: int) -> Optional[Dict]:
    """
    Extract relevant paper information from a DBLP entry.
    
    Returns None if the paper should be skipped (wrong year, missing data, etc.)
    """
    # Get year
    year_str = entry.get("year")
    if not year_str:
        return None
    
    try:
        year = int(year_str)
    except (ValueError, TypeError):
        return None
    
    # Filter by year range
    if year < from_year or year > to_year:
        return None
    
    # Get title
    title = entry.get("title")
    if not title:
        return None
    
    # Get DOI if available (best identifier for Semantic Scholar)
    doi = entry.get("ee")
    if doi and "doi.org" in doi:
        # Extract DOI from URL
        doi = doi.split("doi.org/")[-1]
    else:
        doi = None
    
    # Get authors
    authors = entry.get("author", [])
    if isinstance(authors, str):
        authors = [authors]
    elif isinstance(authors, dict):
        authors = [authors.get("#text", "")]
    
    return {
        "title": title,
        "year": year,
        "doi": doi,
        "authors": authors,
        "dblp_key": entry.get("@key", ""),
    }


def read_dblp_papers(input_file: str, from_year: int, to_year: int) -> List[Dict]:
    """
    Read papers from DBLP XML file and filter by year range.
    """
    print(f"Reading papers from {input_file}...")
    papers = []
    
    try:
        import xml.etree.ElementTree as ET
        
        with gzip.open(input_file, "rt", encoding="utf-8") as f:
            print("Parsing XML (this may take a while)...")
            content = f.read()
            root = ET.fromstring(content)
        
        print(f"Processing {len(root)} entries...")
        for child in root:
            if child.tag in ["inproceedings", "article"]:
                paper_info = extract_paper_info_from_element(child, from_year, to_year)
                if paper_info:
                    papers.append(paper_info)
                    if len(papers) % 10000 == 0:
                        print(f"  Processed {len(papers)} papers...")
    
    except Exception as e:
        print(f"Error reading DBLP file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print(f"Found {len(papers)} papers in year range {from_year}-{to_year}")
    return papers


def extract_paper_info_from_element(elem, from_year: int, to_year: int) -> Optional[Dict]:
    """
    Extract relevant paper information from an XML element.
    
    Returns None if the paper should be skipped (wrong year, missing data, etc.)
    """
    # Get year
    year_elem = elem.find("year")
    if year_elem is None or year_elem.text is None:
        return None
    
    try:
        year = int(year_elem.text)
    except (ValueError, TypeError):
        return None
    
    # Filter by year range
    if year < from_year or year > to_year:
        return None
    
    # Get title
    title_elem = elem.find("title")
    if title_elem is None or title_elem.text is None:
        return None
    title = title_elem.text
    
    # Get DOI if available (best identifier for Semantic Scholar)
    doi = None
    for ee_elem in elem.findall("ee"):
        ee_text = ee_elem.text
        if ee_text and "doi.org" in ee_text:
            # Extract DOI from URL
            doi = ee_text.split("doi.org/")[-1]
            break
    
    # Get authors
    authors = [author.text for author in elem.findall("author") if author.text]
    
    # Get DBLP key
    dblp_key = elem.get("key", "")
    
    return {
        "title": title,
        "year": year,
        "doi": doi,
        "authors": authors,
        "dblp_key": dblp_key,
    }


def fetch_citations_batch(papers: List[Dict], search_no_doi: bool = False) -> tuple[List[Dict], List[Dict]]:
    """
    Fetch citation data from Semantic Scholar using batch API.
    
    For papers with DOI: uses batch API
    For papers without DOI: returns them separately for later processing
    
    Returns:
        tuple: (results_with_doi, papers_without_doi)
    """
    headers = {"x-api-key": API_KEY}
    results = []
    
    # Separate papers with and without DOI
    papers_with_doi = [p for p in papers if p["doi"]]
    papers_without_doi = [p for p in papers if not p["doi"]]
    
    print(f"Papers with DOI: {len(papers_with_doi)}")
    print(f"Papers without DOI: {len(papers_without_doi)}")
    if not search_no_doi and papers_without_doi:
        print(f"  (Papers without DOI will be skipped. Use --search-no-doi to process them)")
    print()
    
    # Process papers with DOI using batch API
    if papers_with_doi:
        print("Processing papers with DOI using batch API...")
        results.extend(fetch_citations_batch_with_doi(papers_with_doi, headers))
    
    return results, papers_without_doi


def fetch_citations_batch_with_doi(papers: List[Dict], headers: Dict, existing_results: Dict[str, Dict], output_file: str, write_header: bool) -> tuple[int, List[Dict]]:
    """
    Fetch citation data for papers with DOI using batch API.
    Writes results incrementally to output file.
    
    Returns:
        Tuple of (number of papers written, list of not-found papers with DOI)
    """
    notfound_papers = []
    papers_written = 0
    
    # Only fetch papers not in cache (cached papers already written in main)
    papers_to_fetch = [p for p in papers if p["dblp_key"] not in existing_results]
    
    print(f"Papers to fetch: {len(papers_to_fetch)}")
    if len(papers_to_fetch) < len(papers):
        print(f"Papers from cache: {len(papers) - len(papers_to_fetch)} (already written)")
    
    # Fetch new papers in batches
    total_batches = (len(papers_to_fetch) + BATCH_SIZE - 1) // BATCH_SIZE if papers_to_fetch else 0
    
    for i in range(0, len(papers_to_fetch), BATCH_SIZE):
        batch = papers_to_fetch[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        
        print(f"  Batch {batch_num}/{total_batches} ({len(batch)} papers)...")
        
        batch_results = []
        
        # Prepare DOI identifiers for batch request
        paper_ids = [f"DOI:{paper['doi']}" for paper in batch]
        
        # Make batch request with retry logic for rate limiting
        max_retries = 3
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                response = requests.post(
                    BATCH_API_URL,
                    headers=headers,
                    params={"fields": "title,year,citationCount,influentialCitationCount,externalIds"},
                    json={"ids": paper_ids},
                )
                
                if response.status_code == 200:
                    api_results = response.json()
                    
                    # Match results back to original papers
                    for j, result in enumerate(api_results):
                        original_paper = batch[j]
                        
                        if result:  # API found the paper
                            batch_results.append({
                                "dblp_key": original_paper["dblp_key"],
                                "title": original_paper["title"],
                                "year": original_paper["year"],
                                "doi": original_paper["doi"],
                                "citationCount": result.get("citationCount", 0),
                                "influentialCitationCount": result.get("influentialCitationCount", 0),
                                "semanticScholarId": result.get("paperId", ""),
                            })
                        else:  # Paper not found in Semantic Scholar
                            notfound_papers.append(original_paper)
                    
                    print(f"    Successfully fetched {len([r for r in api_results if r])} papers")
                    success = True
                elif response.status_code == 429:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 3 * retry_count  # Exponential backoff: 3s, 6s, 12s
                        print(f"    Rate limited (429). Retry {retry_count}/{max_retries} after {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"    Rate limited (429). Max retries reached. Skipping batch.")
                elif response.status_code == 400:
                    # 400 means none of the DOIs were found - add all papers to not-found list
                    print(f"    Error: HTTP 400 - None of the DOIs in this batch were found")
                    notfound_papers.extend(batch)
                    success = True  # Don't retry, we got a definitive answer
                else:
                    print(f"    Error: HTTP {response.status_code} - {response.text}")
                    break  # Don't retry on other errors
            
            except Exception as e:
                print(f"    Error fetching batch: {e}")
                break  # Don't retry on exceptions
        
        # Write batch results incrementally
        if batch_results:
            write_results(batch_results, output_file, mode="w" if write_header else "a")
            papers_written += len(batch_results)
            write_header = False
        
        # Rate limiting: wait before next request
        if i + BATCH_SIZE < len(papers_to_fetch):
            print(f"    Waiting {RATE_LIMIT_DELAY}s (rate limit)...")
            time.sleep(RATE_LIMIT_DELAY)
    
    print(f"\nTotal papers not found via batch API: {len(notfound_papers)}")
    return papers_written, notfound_papers


def fetch_citations_by_search(papers: List[Dict], headers: Dict, existing_results: Dict[str, Dict], output_file: str, write_header: bool) -> int:
    """
    Fetch citation data for papers without DOI using search API.
    This is slower but more reliable for papers without DOI.
    Writes results incrementally to output file.
    
    Returns:
        Number of papers written
    """
    search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    papers_written = 0
    
    # Only fetch papers not in cache (cached papers already written in main)
    papers_to_fetch = [p for p in papers if p["dblp_key"] not in existing_results]
    
    print(f"Papers to fetch: {len(papers_to_fetch)}")
    if len(papers_to_fetch) < len(papers):
        print(f"Papers from cache: {len(papers) - len(papers_to_fetch)} (already written)")
    
    # Fetch new papers one by one
    for i, paper in enumerate(papers_to_fetch):
        print(f"  Paper {i+1}/{len(papers_to_fetch)}: {paper['title'][:60]}...")
        
        result_row = None
        
        try:
            # Search by title and year for better accuracy with retry logic
            max_retries = 3
            retry_count = 0
            response = None
            
            while retry_count < max_retries:
                response = requests.get(
                    search_url,
                    headers=headers,
                    params={
                        "query": paper["title"],
                        "year": f"{paper['year']}-{paper['year']}",
                        "fields": "title,year,citationCount,influentialCitationCount,paperId",
                        "limit": 1,
                    },
                )
                
                if response.status_code == 429:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 3 * retry_count  # Exponential backoff: 3s, 6s, 12s
                        print(f"    Rate limited (429). Retry {retry_count}/{max_retries} after {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"    Rate limited (429). Max retries reached.")
                        break
                else:
                    break  # Success or other error, exit retry loop
            
            if response and response.status_code == 200:
                search_results = response.json()
                
                if search_results.get("data") and len(search_results["data"]) > 0:
                    result = search_results["data"][0]
                    
                    # Verify it's a reasonable match (same year)
                    if result.get("year") == paper["year"]:
                        result_row = {
                            "dblp_key": paper["dblp_key"],
                            "title": paper["title"],
                            "year": paper["year"],
                            "doi": paper["doi"],
                            "citationCount": result.get("citationCount", 0),
                            "influentialCitationCount": result.get("influentialCitationCount", 0),
                            "semanticScholarId": result.get("paperId", ""),
                        }
                        print(f"    Found: {result.get('citationCount', 0)} citations")
                    else:
                        # Year mismatch - likely wrong paper
                        result_row = {
                            "dblp_key": paper["dblp_key"],
                            "title": paper["title"],
                            "year": paper["year"],
                            "doi": paper["doi"],
                            "citationCount": None,
                            "influentialCitationCount": None,
                            "semanticScholarId": "",
                        }
                        print(f"    Year mismatch (expected {paper['year']}, got {result.get('year')})")
                else:
                    # No results found
                    result_row = {
                        "dblp_key": paper["dblp_key"],
                        "title": paper["title"],
                        "year": paper["year"],
                        "doi": paper["doi"],
                        "citationCount": None,
                        "influentialCitationCount": None,
                        "semanticScholarId": "",
                    }
                    print(f"    Not found")
            else:
                print(f"    Error: HTTP {response.status_code}")
                result_row = None
        
        except Exception as e:
            print(f"    Error: {e}")
            result_row = None
        
        # Write result incrementally if we got one
        if result_row:
            write_results([result_row], output_file, mode="w" if write_header else "a")
            papers_written += 1
            write_header = False
        
        # Rate limiting: wait before next request
        if i + 1 < len(papers_to_fetch):
            time.sleep(RATE_LIMIT_DELAY)
    
    return papers_written


def write_results(results: List[Dict], output_file: str, mode: str = "w"):
    """Write results to CSV file.
    
    Args:
        results: List of result dictionaries
        output_file: Path to output CSV file
        mode: File mode - 'w' to write/overwrite, 'a' to append
    """
    fieldnames = [
        "dblp_key",
        "title",
        "year",
        "doi",
        "citationCount",
        "influentialCitationCount",
        "semanticScholarId",
    ]
    
    if mode == "w":
        print(f"\nWriting results to {output_file}...")
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    else:  # append mode
        print(f"\nAppending results to {output_file}...")
        with open(output_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerows(results)


def load_existing_results(resume_file: str) -> Dict[str, Dict]:
    """Load existing results from a previous run.
    
    Returns:
        Dictionary mapping dblp_key to result dictionary
    """
    existing = {}
    
    try:
        with open(resume_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert citation counts back to int/None
                if row["citationCount"]:
                    row["citationCount"] = int(row["citationCount"])
                else:
                    row["citationCount"] = None
                
                if row["influentialCitationCount"]:
                    row["influentialCitationCount"] = int(row["influentialCitationCount"])
                else:
                    row["influentialCitationCount"] = None
                
                existing[row["dblp_key"]] = row
        
        print(f"Loaded {len(existing)} existing results from {resume_file}")
    except FileNotFoundError:
        print(f"Resume file {resume_file} not found, starting fresh")
    except Exception as e:
        print(f"Error loading resume file: {e}")
        print("Starting fresh")
    
    return existing


def print_statistics(results: List[Dict], label: str = ""):
    """Print statistics about the results."""
    total = len(results)
    if total == 0:
        return
    
    found = len([r for r in results if r["citationCount"] is not None])
    not_found = total - found
    
    prefix = f"{label} - " if label else ""
    print(f"\n{prefix}Statistics:")
    print(f"  Total papers: {total}")
    print(f"  Found in Semantic Scholar: {found} ({100*found/total:.1f}%)")
    print(f"  Not found: {not_found} ({100*not_found/total:.1f}%)")
    
    if found > 0:
        total_citations = sum(r["citationCount"] for r in results if r["citationCount"])
        total_influential = sum(
            r["influentialCitationCount"]
            for r in results
            if r["influentialCitationCount"]
        )
        print(f"  Total citations: {total_citations}")
        print(f"  Total influential citations: {total_influential}")


def load_paper_keys(papers_file: str) -> Set[str]:
    """Load DBLP keys from papers CSV file.
    
    Returns:
        Set of dblp_key values to fetch citations for
    """
    paper_keys = set()
    
    try:
        with open(papers_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "dblp_key" in row:
                    paper_keys.add(row["dblp_key"])
        
        print(f"Loaded {len(paper_keys)} paper keys from {papers_file}")
    except FileNotFoundError:
        print(f"Warning: Papers file {papers_file} not found, will process all papers from DBLP")
    except Exception as e:
        print(f"Error loading papers file: {e}")
        print("Will process all papers from DBLP")
    
    return paper_keys


def main():
    """Main function."""
    args = parse_arguments()
    
    print(f"Fetching citations for papers from {args.from_year} to {args.to_year}")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    if args.papers:
        print(f"Papers filter: {args.papers}")
    print(f"Search papers without DOI: {args.search_no_doi}")
    if args.resume_from:
        print(f"Resume from: {args.resume_from}")
    print()
    
    # Load paper keys to filter by if specified
    paper_keys_filter = None
    if args.papers:
        paper_keys_filter = load_paper_keys(args.papers)
        print()
    
    # Validate that resume-from and output are different files
    import os
    if args.resume_from and os.path.abspath(args.resume_from) == os.path.abspath(args.output):
        print("Error: --resume-from and --output cannot be the same file")
        print("The output file will be created from scratch.")
        sys.exit(1)
    
    # Load existing results if resuming
    existing_results = {}
    if args.resume_from:
        existing_results = load_existing_results(args.resume_from)
        print()
    
    # Read papers from DBLP
    papers = read_dblp_papers(args.input, args.from_year, args.to_year)
    
    # Filter by paper keys if specified
    if paper_keys_filter:
        papers_before = len(papers)
        papers = [p for p in papers if p["dblp_key"] in paper_keys_filter]
        print(f"Filtered to {len(papers)} papers from papers file (was {papers_before})")
        print()
    
    if not papers:
        print("No papers found in the specified year range.")
        sys.exit(0)
    
    # Separate papers with and without DOI
    papers_with_doi = [p for p in papers if p["doi"]]
    papers_without_doi = [p for p in papers if not p["doi"]]
    
    # Further separate papers without DOI into cached and non-cached
    papers_without_doi_cached = [p for p in papers_without_doi if p["dblp_key"] in existing_results]
    papers_without_doi_to_fetch = [p for p in papers_without_doi if p["dblp_key"] not in existing_results]
    
    print(f"\nPapers with DOI: {len(papers_with_doi)}")
    print(f"Papers without DOI: {len(papers_without_doi)}")
    print(f"  - Cached: {len(papers_without_doi_cached)}")
    print(f"  - To fetch: {len(papers_without_doi_to_fetch)}")
    if not args.search_no_doi and papers_without_doi_to_fetch:
        print(f"  (New papers without DOI will be skipped. Use --search-no-doi to fetch them)")
    print()
    
    # Fetch citation data
    print(f"Fetching citation data from Semantic Scholar...")
    print(f"Using batch API with {BATCH_SIZE} papers per request")
    print(f"Rate limit: {RATE_LIMIT_DELAY}s between requests")
    print(f"Writing results incrementally to {args.output}")
    print()
    
    total_written = 0
    notfound_doi_papers = []
    write_header = True
    
    # First, write ALL cached papers (with or without DOI)
    # Use a dict to avoid duplicates in case a paper appears multiple times
    all_cached_papers_dict = {}
    for paper in papers_with_doi + papers_without_doi:
        if paper["dblp_key"] in existing_results:
            all_cached_papers_dict[paper["dblp_key"]] = existing_results[paper["dblp_key"]]
    
    all_cached_papers = list(all_cached_papers_dict.values())
    
    if all_cached_papers:
        print(f"Writing {len(all_cached_papers)} cached papers...")
        write_results(all_cached_papers, args.output, mode="w")
        total_written += len(all_cached_papers)
        write_header = False
        print()
    
    # Process papers with DOI (only non-cached ones will be fetched)
    if papers_with_doi:
        print("Processing papers with DOI using batch API...")
        headers = {"x-api-key": API_KEY}
        written_doi, notfound_doi_papers = fetch_citations_batch_with_doi(
            papers_with_doi, 
            headers, 
            existing_results,
            args.output,
            write_header
        )
        total_written += written_doi
        write_header = False
        print(f"\nWrote {written_doi} papers with DOI")
    
    # Fetch new papers without DOI if requested
    if args.search_no_doi and papers_without_doi_to_fetch:
        print("\n" + "="*60)
        print("Now fetching new papers without DOI using search API...")
        print("This will be slower (1 request per second)")
        print("="*60 + "\n")
        
        headers = {"x-api-key": API_KEY}
        written_no_doi = fetch_citations_by_search(
            papers_without_doi_to_fetch, 
            headers, 
            existing_results,
            args.output,
            write_header
        )
        total_written += written_no_doi
        write_header = False
        print(f"\nWrote {written_no_doi} new papers without DOI")
    
    # Retry not-found DOI papers with search API if requested
    if args.search_notfound_doi and notfound_doi_papers:
        print("\n" + "="*60)
        print(f"Now retrying {len(notfound_doi_papers)} not-found DOI papers using search API...")
        print("This will be slower (1 request per second)")
        print("="*60 + "\n")
        
        headers = {"x-api-key": API_KEY}
        written_notfound = fetch_citations_by_search(
            notfound_doi_papers, 
            headers, 
            existing_results,
            args.output,
            write_header
        )
        total_written += written_notfound
        print(f"\nWrote {written_notfound} not-found DOI papers")
    
    print(f"\nDone! Total of {total_written} results written to {args.output}")
    print(f"\nTo resume this run later, use: --resume-from {args.output}")


if __name__ == "__main__":
    main()
