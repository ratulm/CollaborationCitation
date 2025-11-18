#!/usr/bin/env python3
"""
Extract conference information from DBLP papers.

For each paper in DBLP, extracts:
- dblp_key
- title
- year
- conference (mapped from venue)
- author_conferences (primary research areas of faculty authors)
- known_authors (canonical names of all faculty authors)
- num_authors (total number of authors, including non-faculty)
"""

import argparse
import csv
import gzip
import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Set
from collections import defaultdict

# Import conference mapping from csrankings.py
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from util.csrankings import areadict, Conference

# Build confdict mapping conference names to areas
confdict = {}
for area, conferences in areadict.items():
    for conf in conferences:
        confdict[conf] = area


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract conference information from DBLP papers"
    )
    parser.add_argument(
        "--dblp",
        type=str,
        required=True,
        help="DBLP XML file (e.g., dblp.xml.gz)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="papers.csv",
        help="Output CSV file (default: papers.csv)",
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
        "--author-info",
        type=str,
        default="generated-author-info.csv",
        help="Author info CSV file (default: generated-author-info.csv)",
    )
    parser.add_argument(
        "--faculty",
        type=str,
        default="csrankings.csv",
        help="Faculty CSV file (default: csrankings.csv)",
    )
    parser.add_argument(
        "--aliases",
        type=str,
        default="dblp-aliases.csv",
        help="DBLP aliases CSV file (default: dblp-aliases.csv)",
    )
    parser.add_argument(
        "--no-skip-unknown-venues",
        action="store_true",
        default=False,
        help="Include papers with unknown venues (default: False, skip them)",
    )
    parser.add_argument(
        "--no-skip-unknown-authors",
        action="store_true",
        default=False,
        help="Include papers with zero known authors (default: False, skip them)",
    )
    return parser.parse_args()


def load_faculty(faculty_file: str) -> Set[str]:
    """Load the set of faculty members from csrankings.csv."""
    faculty = set()
    
    try:
        with open(faculty_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                faculty.add(row["name"])
        
        print(f"Loaded {len(faculty)} faculty members from {faculty_file}")
    except Exception as e:
        print(f"Error loading faculty file: {e}")
        sys.exit(1)
    
    return faculty


def load_aliases(aliases_file: str) -> Dict[str, str]:
    """Load author aliases.
    
    Returns:
        aliasdict: alias -> canonical name
    """
    aliasdict = {}
    
    try:
        with open(aliases_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                aliasdict[row["alias"]] = row["name"]
        
        print(f"Loaded {len(aliasdict)} aliases from {aliases_file}")
    except FileNotFoundError:
        print(f"Warning: Aliases file {aliases_file} not found, continuing without aliases")
    except Exception as e:
        print(f"Error loading aliases file: {e}")
    
    return aliasdict


def compute_author_primary_areas(author_info_file: str, faculty: Set[str], 
                                  aliasdict: Dict[str, str]) -> Dict[str, str]:
    """Compute the primary research area for each author.
    
    The primary area is the one where the author has published the highest
    fraction of their papers.
    
    Uses 'count' (not 'adjustedcount') to match CSRankings website behavior
    for determining author areas (pie charts).
    
    Returns:
        Dictionary mapping author name to primary area
    """
    # Count papers per author per area
    author_area_counts: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    
    try:
        with open(author_info_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                author = row["name"]
                
                # Check if this author is in faculty (or their canonical name is)
                canonical_name = aliasdict.get(author, author)
                if canonical_name not in faculty and author not in faculty:
                    continue
                
                area = row["area"]
                count = float(row["count"])  # Changed from adjustedcount to count
                
                author_area_counts[canonical_name][area] += count
        
        print(f"Processed publication data for {len(author_area_counts)} faculty members")
    except Exception as e:
        print(f"Error loading author info file: {e}")
        sys.exit(1)
    
    # Determine primary area for each author (area with highest fraction)
    author_primary_area = {}
    for author, area_counts in author_area_counts.items():
        if not area_counts:
            continue
        
        # Find area with maximum count
        primary_area = max(area_counts.items(), key=lambda x: x[1])[0]
        author_primary_area[author] = primary_area
    
    print(f"Computed primary areas for {len(author_primary_area)} authors")
    return author_primary_area


def extract_paper_info(dblp_file: str, from_year: int, to_year: int,
                       author_primary_area: Dict[str, str], faculty: Set[str],
                       aliasdict: Dict[str, str], skip_unknown_venues: bool = True,
                       skip_unknown_authors: bool = True) -> tuple[List[Dict], int, int]:
    """Extract paper information from DBLP.
    
    Returns:
        Tuple of (papers list, skipped_venue_count, skipped_author_count)
    """
    papers = []
    skipped_venue_count = 0
    skipped_author_count = 0

    print(f"Extracting papers from {dblp_file} (years {from_year}-{to_year})...")

    try:
        with gzip.open(dblp_file, "rt", encoding="utf-8") as f:
            content = f.read()
            root = ET.fromstring(content)

        processed = 0
        for child in root:
            if child.tag not in ["inproceedings", "article"]:
                continue

            # Extract year
            year_elem = child.find("year")
            if year_elem is None or year_elem.text is None:
                continue

            try:
                year = int(year_elem.text)
            except (ValueError, TypeError):
                continue

            # Filter by year range
            if year < from_year or year > to_year:
                continue

            # Extract dblp_key
            dblp_key = child.get("key", "")
            if not dblp_key:
                continue

            # Extract title
            title_elem = child.find("title")
            if title_elem is None or title_elem.text is None:
                continue
            title = title_elem.text.strip()

            # Extract authors
            authors = []
            for author_elem in child.findall("author"):
                if author_elem.text is not None:
                    authors.append(author_elem.text.strip())

            # Extract venue (booktitle for conferences, journal for articles)
            venue_elem = child.find("booktitle")
            if venue_elem is None:
                venue_elem = child.find("journal")
            venue = venue_elem.text.strip() if venue_elem is not None and venue_elem.text else ""

            # Map venue to conference area using confdict
            conference = ""
            if venue:
                conf = Conference(venue)
                if conf in confdict:
                    conference = str(confdict[conf])

            # Fallback: Extract venue from DBLP key if not found
            # DBLP keys for conferences have format: conf/{venue}/{paperid}
            if not conference and dblp_key.startswith("conf/"):
                parts = dblp_key.split("/")
                if len(parts) >= 2:
                    venue_from_key = parts[1].upper()
                    conf = Conference(venue_from_key)
                    if conf in confdict:
                        conference = str(confdict[conf])

            # Find primary areas of faculty authors and collect faculty names
            faculty_author_areas = set()
            faculty_authors = []

            for author in authors:
                # Try to resolve author name
                canonical_name = aliasdict.get(author, author)

                # Check if this is a faculty member
                if canonical_name in faculty or author in faculty:
                    # Add canonical name to faculty authors list
                    faculty_authors.append(canonical_name)

                    # Get their primary area
                    primary_area = author_primary_area.get(canonical_name) or author_primary_area.get(author)
                    if primary_area:
                        faculty_author_areas.add(primary_area)

            # Create a sorted list of areas for readability
            areas_list = sorted(list(faculty_author_areas))
            author_conferences = ";".join(areas_list) if areas_list else ""

            # Create a sorted list of faculty authors
            known_authors_list = (
                ";".join(sorted(faculty_authors)) if faculty_authors else ""
            )

            # Count total number of authors (including non-faculty)
            num_authors = len(authors)

            # Apply filters
            if skip_unknown_venues and not conference:
                skipped_venue_count += 1
                continue  # Skip papers with unknown venues

            if skip_unknown_authors and not author_conferences:
                skipped_author_count += 1
                continue  # Skip papers with zero known authors

            papers.append(
                {
                    "dblp_key": dblp_key,
                    "title": title,
                    "year": year,
                    "conference": conference,
                    "author_conferences": author_conferences,
                    "known_authors": known_authors_list,
                    "num_authors": num_authors,
                }
            )

            processed += 1
            if processed % 10000 == 0:
                print(f"  Processed {processed} papers...")

        print(f"Extracted {len(papers)} papers")
    except Exception as e:
        print(f"Error loading DBLP file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    return papers, skipped_venue_count, skipped_author_count


def write_output(papers: List[Dict], output_file: str, skipped_venue_count: int, 
                 skipped_author_count: int, total_candidates: int):
    """Write papers to CSV, deduplicating by dblp_key."""
    if not papers:
        print("No papers to write")
        return

    print(f"Deduplicating papers by dblp_key...")

    # Deduplicate papers by dblp_key, keeping the first occurrence
    seen_keys = set()
    unique_papers = []
    duplicate_count = 0

    for paper in papers:
        key = paper["dblp_key"]
        if key in seen_keys:
            duplicate_count += 1
            print(f"  Warning: Duplicate dblp_key found: {key}")
        else:
            seen_keys.add(key)
            unique_papers.append(paper)

    if duplicate_count > 0:
        print(f"  Found {duplicate_count} duplicate papers (removed)")

    print(f"Writing {len(unique_papers)} unique papers to {output_file}...")

    fieldnames = [
        "dblp_key",
        "title",
        "year",
        "conference",
        "author_conferences",
        "known_authors",
        "num_authors",
    ]

    try:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_papers)

        print(f"Successfully wrote {len(unique_papers)} papers to {output_file}")

        # Print filter statistics
        if skipped_venue_count > 0 or skipped_author_count > 0:
            print(f"\nFilter Statistics:")
            if skipped_venue_count > 0:
                print(f"  Papers skipped (unknown venue): {skipped_venue_count} ({100*skipped_venue_count/total_candidates:.1f}%)")
            if skipped_author_count > 0:
                print(f"  Papers skipped (no known authors): {skipped_author_count} ({100*skipped_author_count/total_candidates:.1f}%)")
            total_skipped = skipped_venue_count + skipped_author_count
            print(f"  Total papers skipped: {total_skipped} ({100*total_skipped/total_candidates:.1f}%)")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


def main():
    """Main function."""
    args = parse_arguments()
    
    print("Extracting conference information from DBLP")
    print(f"DBLP file: {args.dblp}")
    print(f"Output file: {args.output}")
    print(f"Year range: {args.from_year}-{args.to_year}")
    print()
    
    # Load faculty list
    faculty = load_faculty(args.faculty)
    
    # Load aliases
    aliasdict = load_aliases(args.aliases)
    
    # Compute primary areas for each author
    print()
    author_primary_area = compute_author_primary_areas(args.author_info, faculty, aliasdict)
    
    # Extract paper info from DBLP
    print()
    skip_unknown_venues = not args.no_skip_unknown_venues
    skip_unknown_authors = not args.no_skip_unknown_authors
    
    if skip_unknown_venues:
        print("Filtering: Skipping papers with unknown venues")
    if skip_unknown_authors:
        print("Filtering: Skipping papers with zero known authors")
    
    papers, skipped_venue_count, skipped_author_count = extract_paper_info(
        args.dblp, args.from_year, args.to_year,
        author_primary_area, faculty, aliasdict,
        skip_unknown_venues, skip_unknown_authors)
    
    # Calculate total candidates (papers + skipped)
    total_candidates = len(papers) + skipped_venue_count + skipped_author_count
    
    # Write output
    print()
    write_output(papers, args.output, skipped_venue_count, skipped_author_count, total_candidates)
    
    print(f"\nDone!")


if __name__ == "__main__":
    main()
