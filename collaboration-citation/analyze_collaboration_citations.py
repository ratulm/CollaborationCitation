#!/usr/bin/env python3
"""
Analyze the correlation between collaboration score and citation count.

This script reads the output from compute_collaboration_score.py and performs
statistical analysis to determine if there's a relationship between cross-disciplinary
collaboration and citation impact.
"""

import argparse
import csv
import os
import sys
from typing import List, Dict, Tuple, Set
import statistics
import matplotlib.pyplot as plt
import numpy as np

# Conference to parent area mapping (from csrankings.ts)
PARENT_MAP = {
    'aaai': 'ai', 'ijcai': 'ai',
    'cvpr': 'vision', 'eccv': 'vision', 'iccv': 'vision',
    'icml': 'mlmining', 'iclr': 'mlmining', 'kdd': 'mlmining', 'nips': 'mlmining',
    'acl': 'nlp', 'emnlp': 'nlp', 'naacl': 'nlp',
    'sigir': 'inforet', 'www': 'inforet',
    'asplos': 'arch', 'isca': 'arch', 'micro': 'arch', 'hpca': 'arch',
    'ccs': 'sec', 'oakland': 'sec', 'usenixsec': 'sec', 'ndss': 'sec', 'pets': 'sec',
    'vldb': 'mod', 'sigmod': 'mod', 'icde': 'mod', 'pods': 'mod',
    'dac': 'da', 'iccad': 'da',
    'emsoft': 'bed', 'rtas': 'bed', 'rtss': 'bed',
    'sc': 'hpc', 'hpdc': 'hpc', 'ics': 'hpc',
    'mobicom': 'mobile', 'mobisys': 'mobile', 'sensys': 'mobile',
    'imc': 'metrics', 'sigmetrics': 'metrics',
    'osdi': 'ops', 'sosp': 'ops', 'eurosys': 'ops', 'fast': 'ops', 'usenixatc': 'ops',
    'popl': 'plan', 'pldi': 'plan', 'oopsla': 'plan', 'icfp': 'plan',
    'fse': 'soft', 'icse': 'soft', 'ase': 'soft', 'issta': 'soft',
    'nsdi': 'comm', 'sigcomm': 'comm',
    'siggraph': 'graph', 'siggraph-asia': 'graph', 'eurographics': 'graph',
    'focs': 'act', 'soda': 'act', 'stoc': 'act',
    'crypto': 'crypt', 'eurocrypt': 'crypt',
    'cav': 'log', 'lics': 'log',
    'ismb': 'bio', 'recomb': 'bio',
    'ec': 'ecom', 'wine': 'ecom',
    'chiconf': 'chi', 'ubicomp': 'chi', 'uist': 'chi',
    'icra': 'robotics', 'iros': 'robotics', 'rss': 'robotics',
    'vis': 'visualization', 'vr': 'visualization',
    'sigcse': 'csed'
}

# Parent area to meta-area mapping
META_AREA_MAP = {
    # AI areas
    'ai': 'ai', 'vision': 'ai', 'mlmining': 'ai', 'nlp': 'ai', 'inforet': 'ai',
    # Systems areas
    'arch': 'systems', 'comm': 'systems', 'sec': 'systems', 'mod': 'systems',
    'da': 'systems', 'bed': 'systems', 'hpc': 'systems', 'mobile': 'systems',
    'metrics': 'systems', 'ops': 'systems', 'plan': 'systems', 'soft': 'systems',
    # Theory areas
    'act': 'theory', 'crypt': 'theory', 'log': 'theory',
    # Interdisciplinary areas
    'bio': 'interdisciplinary', 'graph': 'interdisciplinary', 'csed': 'interdisciplinary',
    'ecom': 'interdisciplinary', 'chi': 'interdisciplinary', 'robotics': 'interdisciplinary',
    'visualization': 'interdisciplinary'
}

# Friendly names for areas (from csrankings.ts areaMap)
AREA_NAMES = {
    'ai': 'AI', 'vision': 'Vision', 'mlmining': 'ML', 'nlp': 'NLP', 'inforet': 'Web+IR',
    'arch': 'Arch', 'comm': 'Networks', 'sec': 'Security', 'mod': 'DB',
    'da': 'EDA', 'bed': 'Embedded', 'hpc': 'HPC', 'mobile': 'Mobile',
    'metrics': 'Metrics', 'ops': 'OS', 'plan': 'PL', 'soft': 'Software Engineering',
    'act': 'Theory', 'crypt': 'Crypto', 'log': 'Logic',
    'bio': 'Comp. Bio', 'graph': 'Graphics', 'csed': 'CSEd',
    'ecom': 'ECom', 'chi': 'HCI', 'robotics': 'Robotics',
    'visualization': 'Visualization',
    # Conferences
    'aaai': 'AI', 'ijcai': 'AI', 'cvpr': 'Vision', 'eccv': 'Vision', 'iccv': 'Vision',
    'icml': 'ML', 'kdd': 'ML', 'iclr': 'ML', 'nips': 'ML',
    'acl': 'NLP', 'emnlp': 'NLP', 'naacl': 'NLP',
    'sigir': 'Web+IR', 'www': 'Web+IR',
    'asplos': 'Arch', 'isca': 'Arch', 'micro': 'Arch', 'hpca': 'Arch',
    'sigcomm': 'Networks', 'nsdi': 'Networks',
    'ccs': 'Security', 'oakland': 'Security', 'usenixsec': 'Security', 'ndss': 'Security', 'pets': 'Security',
    'sigmod': 'DB', 'vldb': 'DB', 'icde': 'DB', 'pods': 'DB',
    'sc': 'HPC', 'hpdc': 'HPC', 'ics': 'HPC',
    'mobicom': 'Mobile', 'mobisys': 'Mobile', 'sensys': 'Mobile',
    'imc': 'Metrics', 'sigmetrics': 'Metrics',
    'sosp': 'OS', 'osdi': 'OS', 'fast': 'OS', 'usenixatc': 'OS', 'eurosys': 'OS',
    'pldi': 'PL', 'popl': 'PL', 'icfp': 'PL', 'oopsla': 'PL',
    'fse': 'SE', 'icse': 'SE', 'ase': 'SE', 'issta': 'SE',
    'focs': 'Theory', 'soda': 'Theory', 'stoc': 'Theory',
    'crypto': 'Crypto', 'eurocrypt': 'Crypto',
    'cav': 'Logic', 'lics': 'Logic',
    'siggraph': 'Graphics', 'siggraph-asia': 'Graphics', 'eurographics': 'Graphics',
    'chiconf': 'HCI', 'ubicomp': 'HCI', 'uist': 'HCI',
    'icra': 'Robotics', 'iros': 'Robotics', 'rss': 'Robotics',
    'ismb': 'Comp. Bio', 'recomb': 'Comp. Bio',
    'dac': 'EDA', 'iccad': 'EDA',
    'emsoft': 'Embedded', 'rtas': 'Embedded', 'rtss': 'Embedded',
    'vis': 'Visualization', 'vr': 'Visualization',
    'ec': 'ECom', 'wine': 'ECom',
    'sigcse': 'CSEd'
}


def get_valid_metaareas() -> List[str]:
    """Get list of valid metaareas."""
    return sorted(set(META_AREA_MAP.values()))


def get_valid_areas() -> List[str]:
    """Get list of valid areas (parent areas)."""
    return sorted(set(PARENT_MAP.values()))


def get_valid_conferences() -> List[str]:
    """Get list of valid conferences."""
    return sorted(PARENT_MAP.keys())


def validate_filters(metaareas: List[str] = None, areas: List[str] = None, conferences: List[str] = None):
    """Validate filter arguments and print helpful error messages.
    
    Args:
        metaareas: List of metaarea filter values
        areas: List of area filter values
        conferences: List of conference filter values
    
    Raises:
        SystemExit if any filter is invalid
    """
    if metaareas:
        valid_metaareas = get_valid_metaareas()
        invalid = [m for m in metaareas if m not in valid_metaareas]
        if invalid:
            print(f"Error: Invalid metaarea(s): {', '.join(invalid)}")
            print(f"\nValid metaareas: {', '.join(valid_metaareas)}")
            sys.exit(1)
    
    if areas:
        valid_areas = get_valid_areas()
        invalid = [a for a in areas if a not in valid_areas]
        if invalid:
            print(f"Error: Invalid area(s): {', '.join(invalid)}")
            print(f"\nValid areas: {', '.join(valid_areas)}")
            sys.exit(1)
    
    if conferences:
        valid_conferences = get_valid_conferences()
        invalid = [c for c in conferences if c not in valid_conferences]
        if invalid:
            print(f"Error: Invalid conference(s): {', '.join(invalid)}")
            print(f"\nValid conferences: {', '.join(valid_conferences)}")
            sys.exit(1)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze correlation between collaboration score and citations"
    )
    parser.add_argument(
        "--citations",
        type=str,
        required=True,
        help="Input CSV file with citation data (citations.csv)",
    )
    parser.add_argument(
        "--papers",
        type=str,
        required=True,
        dest='papers_file',
        help="Input CSV file with paper information (papers.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output file for detailed analysis (default: print to stdout)",
    )
    parser.add_argument(
        "--min-citations",
        type=int,
        default=0,
        help="Minimum citation count for papers to include in analysis (default: 0)",
    )
    parser.add_argument(
        "--collaboration-level",
        type=str,
        choices=["conference", "area", "metaarea"],
        default="conference",
        help="Level at which to compute collaboration scores: conference (default), area (parent), or metaarea (AI/Systems/Theory/Interdisciplinary)",
    )
    parser.add_argument(
        "--only-metaareas",
        type=str,
        nargs='+',
        choices=["ai", "systems", "theory", "interdisciplinary"],
        default=None,
        dest='metaareas',
        help="Filter papers to only those published in conferences belonging to the specified metaarea(s) (default: None, analyze all papers). Can specify multiple values.",
    )
    parser.add_argument(
        "--only-areas",
        type=str,
        nargs='+',
        default=None,
        dest='areas',
        help="Filter papers to only those published in the specified area(s) (e.g., 'vision', 'nlp', 'sec') (default: None, analyze all papers). Can specify multiple values.",
    )
    parser.add_argument(
        "--only-conferences",
        type=str,
        nargs='+',
        default=None,
        dest='conference_filters',
        help="Filter papers to only those published in the specified conference(s) (e.g., 'cvpr', 'sigcomm', 'icml') (default: None, analyze all papers). Can specify multiple values.",
    )
    parser.add_argument(
        "--only-authors",
        type=str,
        nargs='+',
        default=None,
        dest='author_filters',
        help="Filter papers to only those authored by the specified faculty member(s) (canonical names from csrankings.csv) (default: None, analyze all papers). Can specify multiple values. This filter can be combined with venue filters (--only-metaareas, --only-areas, --only-conferences).",
    )
    parser.add_argument(
        "--max-collaboration-score",
        type=int,
        default=3,
        help="Maximum collaboration score to display separately; scores at or above this value are grouped into a single bin (default: 3)",
    )
    parser.add_argument(
        "--graph",
        type=str,
        default=None,
        help="Output file for bar chart visualization (default: None, no graph generated)",
    )
    parser.add_argument(
        "--max-y1-val",
        type=float,
        default=None,
        help="Maximum primary y-axis value for the first plot (default: auto-scale)",
    )
    parser.add_argument(
        "--max-y2-val",
        type=float,
        default=None,
        help="Maximum secondary y-axis value for the first plot (default: auto-scale)",
    )
    parser.add_argument(
        "--y1-tick-freq",
        type=float,
        default=None,
        help="Tick frequency for primary y-axis in first plot (citation count) (default: None, automatic)",
    )
    parser.add_argument(
        "--y2-tick-freq",
        type=float,
        default=None,
        help="Tick frequency for secondary y-axis in first plot (probability) (default: None, automatic)",
    )
    parser.add_argument(
        "--min-y3-val",
        type=float,
        default=None,
        help="Minimum primary y-axis value for the second plot (default: auto-scale)",
    )
    parser.add_argument(
        "--max-y3-val",
        type=float,
        default=None,
        help="Maximum primary y-axis value for the second plot (default: auto-scale)",
    )
    parser.add_argument(
        "--min-y4-val",
        type=float,
        default=None,
        help="Minimum secondary y-axis value for the second plot (default: auto-scale)",
    )
    parser.add_argument(
        "--max-y4-val",
        type=float,
        default=None,
        help="Maximum secondary y-axis value for the second plot (default: auto-scale)",
    )
    parser.add_argument(
        "--y3-tick-freq",
        type=float,
        default=None,
        help="Tick frequency for primary y-axis in second plot (normalized citation count) (default: None, automatic)",
    )
    parser.add_argument(
        "--y4-tick-freq",
        type=float,
        default=None,
        help="Tick frequency for secondary y-axis in second plot (normalized probability) (default: None, automatic)",
    )
    parser.add_argument(
        "--heavy-hitter",
        type=float,
        default=10.0,
        help="Percentage threshold for heavy hitters (top X%% of papers by citation count) (default: 10.0)",
    )
    parser.add_argument(
        "--from-year",
        type=int,
        default=None,
        help="Filter papers to only those published from this year onwards (inclusive) (default: None, no lower bound)",
    )
    parser.add_argument(
        "--to-year",
        type=int,
        default=None,
        help="Filter papers to only those published up to this year (inclusive) (default: None, no upper bound)",
    )
    parser.add_argument(
        "--author-normalization",
        type=str,
        choices=["known", "all"],
        default="all",
        help="Author count to use for normalization baseline: 'known' (faculty authors only) or 'all' (all authors) (default: all)",
    )
    parser.add_argument(
        "--max-authors",
        type=int,
        default=7,
        help="Maximum author count for normalization bins; papers with >= this many authors are grouped together (default: 7)",
    )
    parser.add_argument(
        "--num-reference-bundles",
        type=int,
        default=100,
        help="Number of random reference bundles to create for computing expected statistics (default: 100)",
    )
    return parser.parse_args()


def map_to_level(conferences: List[str], level: str) -> Set[str]:
    """Map conference-level areas to the specified hierarchy level.
    
    Args:
        conferences: List of conference-level area codes
        level: 'conference', 'area', or 'metaarea'
    
    Returns:
        Set of unique areas at the specified level
    """
    if level == "conference":
        return set(conferences)

    mapped = set()
    for conf in conferences:
        if level == "area":
            # Map to parent area
            parent = PARENT_MAP.get(conf, conf)
            mapped.add(parent)
        elif level == "metaarea":
            # Map to meta-area (AI/Systems/Theory/Interdisciplinary)
            parent = PARENT_MAP.get(conf, conf)
            meta = META_AREA_MAP.get(parent, parent)
            mapped.add(meta)

    return mapped


def load_data(
    citations_file: str,
    papers_file: str,
    min_citations: int = 0,
    collaboration_level: str = "conference",
    metaarea_filters: List[str] = None,
    area_filters: List[str] = None,
    conference_filters: List[str] = None,
    author_filters: List[str] = None,
    max_collab_score: int = 3,
    from_year: int = None,
    to_year: int = None,
    author_normalization: str = "known",
    max_authors: int = 7,
) -> Tuple[List[Dict], int]:
    """Load papers with collaboration scores and citation counts.

    Args:
        citations_file: Path to citations CSV file
        papers_file: Path to papers CSV file
        min_citations: Minimum citation count threshold
        collaboration_level: Level at which to compute collaboration scores
        metaarea_filters: If specified, only include papers published in these metaareas
        area_filters: If specified, only include papers published in these areas
        conference_filters: If specified, only include papers published in these conferences
        author_filters: If specified, only include papers authored by these faculty members
        max_collab_score: Maximum collaboration score to display separately; scores >= this are binned together
        from_year: If specified, only include papers from this year onwards (inclusive)
        to_year: If specified, only include papers up to this year (inclusive)
        author_normalization: Use 'known' or 'all' authors for normalization baseline
        max_authors: Maximum author count for normalization bins

    Returns:
        Tuple of (filtered papers, total papers loaded)
    """
    all_papers = []

    print(f"Loading citation data from {citations_file}...")
    print(f"Loading paper data from {papers_file}...")
    if conference_filters:
        print(f"Filtering to papers published in conference(s): {', '.join(conference_filters)}")
    elif area_filters:
        print(f"Filtering to papers published in area(s): {', '.join(area_filters)}")
    elif metaarea_filters:
        print(f"Filtering to papers published in metaarea(s): {', '.join(metaarea_filters)}")

    if author_filters:
        print(f"Filtering to papers authored by: {', '.join(author_filters)}")

    if from_year is not None or to_year is not None:
        year_range = []
        if from_year is not None:
            year_range.append(f"from {from_year}")
        if to_year is not None:
            year_range.append(f"to {to_year}")
        print(f"Filtering to papers published {' '.join(year_range)}")

    try:
        # Load paper information indexed by dblp_key
        paper_info = {}
        with open(papers_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Get author counts
                known_authors = row.get("known_authors", "")
                known_author_count = (
                    len(known_authors.split(";")) if known_authors else 0
                )

                # Use num_authors if available, otherwise fall back to known_author_count
                if "num_authors" in row and row["num_authors"]:
                    total_author_count = int(row["num_authors"])
                else:
                    total_author_count = known_author_count

                paper_info[row["dblp_key"]] = {
                    "conference": row.get("conference", ""),
                    "author_conferences": row.get("author_conferences", ""),
                    "known_authors": known_authors,
                    "known_author_count": known_author_count,
                    "total_author_count": total_author_count,
                }

        print(f"Loaded paper information for {len(paper_info)} papers")

        # Load citation data and join with conference information
        with open(citations_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dblp_key = row["dblp_key"]

                # Skip papers without paper information
                if dblp_key not in paper_info:
                    continue

                # Only include papers with citation data
                if row["citationCount"] and row["citationCount"] != "":
                    try:
                        citation_count = int(row["citationCount"])

                        # Get paper information
                        paper_data = paper_info[dblp_key]
                        paper_conference = paper_data["conference"]

                        # Apply author filter first (if specified)
                        if author_filters:
                            paper_authors = (
                                paper_data["known_authors"].split(";")
                                if paper_data["known_authors"]
                                else []
                            )
                            # Check if any of the specified authors are in the paper's author list
                            if not any(author in paper_authors for author in author_filters):
                                continue  # Skip papers not authored by the specified authors

                        # Apply venue filters based on paper_conference
                        # Conference filter (most specific)
                        if conference_filters:
                            if paper_conference not in conference_filters:
                                continue  # Skip papers not in the specified conferences

                        # Area filter (parent area)
                        elif area_filters:
                            paper_area = PARENT_MAP.get(paper_conference, paper_conference)
                            if paper_area not in area_filters:
                                continue  # Skip papers not in the specified areas

                        # Metaarea filter (top-level category)
                        elif metaarea_filters:
                            if paper_conference:
                                # Map paper's conference to metaarea
                                paper_area = PARENT_MAP.get(paper_conference, paper_conference)
                                paper_metaarea = META_AREA_MAP.get(paper_area, "")
                                if paper_metaarea not in metaarea_filters:
                                    continue  # Skip papers not in the specified metaareas
                            else:
                                continue  # Skip papers without venue information

                        # Parse conference-level areas from author conferences
                        author_conferences = paper_data["author_conferences"]
                        conference_areas = author_conferences.split(";") if author_conferences else []

                        # Map to the requested level and recompute score
                        mapped_areas = map_to_level(conference_areas, collaboration_level)
                        collaboration_score = len(mapped_areas)

                        # Bin scores: 0 -> 1, 1 -> 1, 2 -> 2, ..., max_collab_score+ -> max_collab_score
                        if collaboration_score == 0:
                            binned_score = 1
                        else:
                            binned_score = min(collaboration_score, max_collab_score)

                        areas_string = ";".join(sorted(mapped_areas))

                        # Get paper year
                        paper_year = int(row["year"])

                        # Apply year filters
                        if from_year is not None and paper_year < from_year:
                            continue  # Skip papers before from_year
                        if to_year is not None and paper_year > to_year:
                            continue  # Skip papers after to_year

                        # Get author counts
                        known_author_count = paper_data["known_author_count"]
                        total_author_count = paper_data["total_author_count"]

                        # Determine which author count to use for normalization baseline
                        if author_normalization == "known":
                            author_count_for_norm = known_author_count
                        else:  # "all"
                            author_count_for_norm = total_author_count

                        # Bin author count for normalization (e.g., 7+ authors)
                        binned_author_count = min(author_count_for_norm, max_authors)

                        influential_count = (
                            int(row["influentialCitationCount"])
                            if row["influentialCitationCount"]
                            else 0
                        )

                        all_papers.append(
                            {
                                "dblp_key": dblp_key,
                                "title": row["title"],
                                "year": paper_year,
                                "citationCount": citation_count,
                                "influentialCitationCount": influential_count,
                                "known_author_count": known_author_count,
                                "total_author_count": total_author_count,
                                "author_count_for_norm": author_count_for_norm,
                                "binned_author_count": binned_author_count,
                                "collaboration_score": binned_score,
                                "collaboration_areas": areas_string,
                            }
                        )
                    except (ValueError, KeyError) as e:
                        continue

        total_loaded = len(all_papers)
        print(f"Loaded {total_loaded} papers with citation data")

        # Filter by minimum citations
        if min_citations > 0:
            filtered_papers = [p for p in all_papers if p["citationCount"] >= min_citations]
            print(f"Filtered to {len(filtered_papers)} papers with >= {min_citations} citations")
            return filtered_papers, total_loaded

        return all_papers, total_loaded

    except Exception as e:
        print(f"Error loading data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def compute_correlation(x: List[float], y: List[float]) -> float:
    """Compute Spearman rank correlation coefficient."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0

    # Create ranks for x and y
    def rank_data(data):
        """Assign ranks to data, handling ties with average ranks."""
        sorted_indices = sorted(range(len(data)), key=lambda i: data[i])
        ranks = [0] * len(data)

        i = 0
        while i < len(sorted_indices):
            j = i
            # Find all tied values
            while j < len(sorted_indices) - 1 and data[sorted_indices[j]] == data[sorted_indices[j + 1]]:
                j += 1

            # Assign average rank to all tied values
            avg_rank = (i + j) / 2 + 1  # +1 because ranks start at 1
            for k in range(i, j + 1):
                ranks[sorted_indices[k]] = avg_rank

            i = j + 1

        return ranks

    ranks_x = rank_data(x)
    ranks_y = rank_data(y)

    # Compute Pearson correlation on ranks
    n = len(ranks_x)
    mean_x = statistics.mean(ranks_x)
    mean_y = statistics.mean(ranks_y)

    numerator = sum((ranks_x[i] - mean_x) * (ranks_y[i] - mean_y) for i in range(n))
    denominator_x = sum((ranks_x[i] - mean_x) ** 2 for i in range(n))
    denominator_y = sum((ranks_y[i] - mean_y) ** 2 for i in range(n))

    if denominator_x == 0 or denominator_y == 0:
        return 0.0

    return numerator / (denominator_x * denominator_y) ** 0.5


def compute_baseline_by_author_count(
    papers: List[Dict], max_authors: int
) -> Dict[int, Dict]:
    """Compute baseline citation statistics by author count.

    Args:
        papers: List of all papers in the filtered set P
        max_authors: Maximum author count bin (papers with >= this many authors are grouped)

    Returns:
        Dictionary mapping binned author counts to citation statistics
    """
    by_author_count = {}

    for paper in papers:
        author_bin = paper["binned_author_count"]
        if author_bin not in by_author_count:
            by_author_count[author_bin] = {
                "citations": [],
                "influential_citations": [],
            }

        by_author_count[author_bin]["citations"].append(paper["citationCount"])
        by_author_count[author_bin]["influential_citations"].append(
            paper["influentialCitationCount"]
        )

    return by_author_count


def compute_expected_statistics(
    papers_in_group: List[Dict],
    baseline_data: Dict[int, Dict],
    heavy_hitter_threshold: int,
    num_bundles: int = 100,
    actual_median_citations: float = None,
    actual_mean_citations: float = None,
    actual_median_influential: float = None,
    actual_mean_influential: float = None,
    actual_hh_probability: float = None,
) -> Dict:
    """Compute expected statistics using reference bundle sampling.

    Args:
        papers_in_group: Papers in the collaboration score group
        baseline_data: Citation values by author count from compute_baseline_by_author_count
        heavy_hitter_threshold: Citation threshold for heavy hitters
        num_bundles: Number of reference bundles to create
        actual_median_citations: Actual median citations for the group
        actual_mean_citations: Actual mean citations for the group
        actual_median_influential: Actual median influential citations for the group
        actual_mean_influential: Actual mean influential citations for the group
        actual_hh_probability: Actual heavy hitter probability for the group

    Returns:
        Dictionary with expected values and variances for normalized statistics
    """
    import random

    # Count papers by author bin in this group
    author_count_distribution = {}
    for paper in papers_in_group:
        author_bin = paper["binned_author_count"]
        author_count_distribution[author_bin] = (
            author_count_distribution.get(author_bin, 0) + 1
        )

    # Pre-convert baseline data to numpy arrays for faster operations
    baseline_arrays = {}
    for author_bin in author_count_distribution.keys():
        if author_bin in baseline_data:
            baseline_arrays[author_bin] = {
                "citations": np.array(baseline_data[author_bin]["citations"]),
                "influential": np.array(
                    baseline_data[author_bin]["influential_citations"]
                ),
            }

    total_papers = len(papers_in_group)

    # Generate ALL random samples at once for maximum speed
    # This creates a 2D array where each row is a complete bundle
    all_bundles_citations = []
    all_bundles_influential = []

    for author_bin, count in author_count_distribution.items():
        if author_bin in baseline_arrays:
            citations_arr = baseline_arrays[author_bin]["citations"]
            influential_arr = baseline_arrays[author_bin]["influential"]

            # Generate all random indices at once: shape (num_bundles, count)
            all_indices = np.random.randint(
                0, len(citations_arr), size=(num_bundles, count)
            )

            # Sample all bundles at once: shape (num_bundles, count)
            sampled_citations = citations_arr[all_indices]
            sampled_influential = influential_arr[all_indices]

            all_bundles_citations.append(sampled_citations)
            all_bundles_influential.append(sampled_influential)

    # Concatenate all author bins for each bundle: shape (num_bundles, total_papers)
    if all_bundles_citations:
        all_bundles_citations = np.concatenate(all_bundles_citations, axis=1)
        all_bundles_influential = np.concatenate(all_bundles_influential, axis=1)

        # Compute statistics for all bundles at once using vectorized operations
        bundle_medians_citations = np.median(all_bundles_citations, axis=1)
        bundle_means_citations = np.mean(all_bundles_citations, axis=1)
        bundle_medians_influential = np.median(all_bundles_influential, axis=1)
        bundle_means_influential = np.mean(all_bundles_influential, axis=1)

        # Heavy hitter probability for all bundles at once
        hh_counts = np.sum(all_bundles_citations >= heavy_hitter_threshold, axis=1)
        bundle_hh_probabilities = (hh_counts / total_papers) * 100
    else:
        # No data available
        bundle_medians_citations = np.zeros(num_bundles)
        bundle_means_citations = np.zeros(num_bundles)
        bundle_medians_influential = np.zeros(num_bundles)
        bundle_means_influential = np.zeros(num_bundles)
        bundle_hh_probabilities = np.zeros(num_bundles)

    # Compute expected values (mean across bundles)
    expected_median_citations = float(np.mean(bundle_medians_citations))
    expected_mean_citations = float(np.mean(bundle_means_citations))
    expected_median_influential = float(np.mean(bundle_medians_influential))
    expected_mean_influential = float(np.mean(bundle_means_influential))
    expected_hh_probability = float(np.mean(bundle_hh_probabilities))

    # Compute normalized values for each bundle
    normalized_median_citations_per_bundle = (
        actual_median_citations - bundle_medians_citations
        if actual_median_citations is not None
        else np.zeros(num_bundles)
    )
    normalized_mean_citations_per_bundle = (
        actual_mean_citations - bundle_means_citations
        if actual_mean_citations is not None
        else np.zeros(num_bundles)
    )
    normalized_median_influential_per_bundle = (
        actual_median_influential - bundle_medians_influential
        if actual_median_influential is not None
        else np.zeros(num_bundles)
    )
    normalized_mean_influential_per_bundle = (
        actual_mean_influential - bundle_means_influential
        if actual_mean_influential is not None
        else np.zeros(num_bundles)
    )
    normalized_hh_probability_per_bundle = (
        actual_hh_probability - bundle_hh_probabilities
        if actual_hh_probability is not None
        else np.zeros(num_bundles)
    )

    # Compute variance of normalized values across bundles
    return {
        "expected_median_citations": expected_median_citations,
        "expected_mean_citations": expected_mean_citations,
        "expected_median_influential": expected_median_influential,
        "expected_mean_influential": expected_mean_influential,
        "expected_heavy_hitter_probability": expected_hh_probability,
        "variance_median_citations": float(
            np.var(normalized_median_citations_per_bundle, ddof=1)
        ),
        "variance_mean_citations": float(
            np.var(normalized_mean_citations_per_bundle, ddof=1)
        ),
        "variance_median_influential": float(
            np.var(normalized_median_influential_per_bundle, ddof=1)
        ),
        "variance_mean_influential": float(
            np.var(normalized_mean_influential_per_bundle, ddof=1)
        ),
        "variance_heavy_hitter_probability": float(
            np.var(normalized_hh_probability_per_bundle, ddof=1)
        ),
    }


def analyze_by_score(
    papers: List[Dict],
    heavy_hitter_pct: float = 10.0,
    max_authors: int = 7,
    num_bundles: int = 100,
) -> Dict[int, Dict]:
    """Group papers by collaboration score and compute statistics.

    Args:
        papers: List of paper dictionaries
        heavy_hitter_pct: Percentage threshold for heavy hitters (default: 10.0)
        max_authors: Maximum author count for normalization bins
        num_bundles: Number of reference bundles for expected statistics

    Returns:
        Dictionary mapping collaboration scores to statistics
    """
    # First, collect baseline citation data by author count across all papers
    baseline_data = compute_baseline_by_author_count(papers, max_authors)

    by_score = {}

    for paper in papers:
        score = paper["collaboration_score"]
        if score not in by_score:
            by_score[score] = {
                "papers": [],
                "citations": [],
                "influential_citations": [],
            }

        by_score[score]["papers"].append(paper)
        by_score[score]["citations"].append(paper["citationCount"])
        by_score[score]["influential_citations"].append(
            paper["influentialCitationCount"]
        )

    # Determine heavy hitter threshold (top X% by citation count)
    all_citations = [p["citationCount"] for p in papers]
    all_citations_sorted = sorted(all_citations, reverse=True)
    heavy_hitter_count = max(1, int(len(all_citations) * heavy_hitter_pct / 100))
    heavy_hitter_threshold = all_citations_sorted[heavy_hitter_count - 1]

    # Compute statistics for each score
    stats_by_score = {}
    for score, data in by_score.items():
        citations = data["citations"]
        influential = data["influential_citations"]
        papers_in_group = data["papers"]

        # Compute actual statistics
        actual_median_citations = statistics.median(citations)
        actual_mean_citations = statistics.mean(citations)
        actual_median_influential = statistics.median(influential)
        actual_mean_influential = statistics.mean(influential)

        # Count heavy hitters in this score group (raw citations)
        heavy_hitters_in_group = sum(
            1 for c in citations if c >= heavy_hitter_threshold
        )
        actual_hh_probability = (
            (heavy_hitters_in_group / len(citations)) * 100 if len(citations) > 0 else 0
        )

        # Compute expected statistics using reference bundle sampling
        # Pass actual values so we can compute normalized values per bundle
        expected_stats = compute_expected_statistics(
            papers_in_group,
            baseline_data,
            heavy_hitter_threshold,
            num_bundles,
            actual_median_citations,
            actual_mean_citations,
            actual_median_influential,
            actual_mean_influential,
            actual_hh_probability,
        )

        # Compute normalized values (actual - expected)
        normalized_median_citations = (
            actual_median_citations - expected_stats["expected_median_citations"]
        )
        normalized_mean_citations = (
            actual_mean_citations - expected_stats["expected_mean_citations"]
        )
        normalized_median_influential = (
            actual_median_influential - expected_stats["expected_median_influential"]
        )
        normalized_mean_influential = (
            actual_mean_influential - expected_stats["expected_mean_influential"]
        )

        # Normalized heavy hitter probability
        normalized_heavy_hitter_probability = (
            actual_hh_probability - expected_stats["expected_heavy_hitter_probability"]
        )

        stats_by_score[score] = {
            "count": len(citations),
            "mean_citations": actual_mean_citations,
            "median_citations": actual_median_citations,
            "stdev_citations": statistics.stdev(citations) if len(citations) > 1 else 0,
            "mean_influential": actual_mean_influential,
            "median_influential": actual_median_influential,
            "expected_median_citations": expected_stats["expected_median_citations"],
            "expected_mean_citations": expected_stats["expected_mean_citations"],
            "expected_median_influential": expected_stats[
                "expected_median_influential"
            ],
            "expected_mean_influential": expected_stats["expected_mean_influential"],
            "normalized_median_citations": normalized_median_citations,
            "normalized_mean_citations": normalized_mean_citations,
            "normalized_median_influential": normalized_median_influential,
            "normalized_mean_influential": normalized_mean_influential,
            "variance_median_citations": expected_stats["variance_median_citations"],
            "variance_mean_citations": expected_stats["variance_mean_citations"],
            "variance_median_influential": expected_stats[
                "variance_median_influential"
            ],
            "variance_mean_influential": expected_stats["variance_mean_influential"],
            "total_citations": sum(citations),
            "heavy_hitters": heavy_hitters_in_group,
            "heavy_hitter_probability": actual_hh_probability,
            "expected_heavy_hitter_probability": expected_stats[
                "expected_heavy_hitter_probability"
            ],
            "normalized_heavy_hitter_probability": normalized_heavy_hitter_probability,
            "variance_heavy_hitter_probability": expected_stats[
                "variance_heavy_hitter_probability"
            ],
        }

    return stats_by_score


def analyze_by_year(papers: List[Dict]) -> Dict[int, Dict]:
    """Analyze correlation separately by year."""
    by_year = {}

    for paper in papers:
        year = paper["year"]
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(paper)

    year_stats = {}
    for year, year_papers in by_year.items():
        if len(year_papers) < 10:  # Skip years with too few papers
            continue

        scores = [p["collaboration_score"] for p in year_papers]
        citations = [p["citationCount"] for p in year_papers]

        correlation = compute_correlation(scores, citations)

        year_stats[year] = {
            "count": len(year_papers),
            "correlation": correlation,
            "mean_score": statistics.mean(scores),
            "mean_citations": statistics.mean(citations),
        }

    return year_stats


def print_analysis(
    papers: List[Dict],
    stats_by_score: Dict,
    year_stats: Dict,
    min_citations: int = 0,
    total_papers: int = None,
    max_collab_score: int = 3,
    heavy_hitter_pct: float = 10.0,
    author_normalization: str = "known",
    max_authors: int = 7,
):
    """Print comprehensive analysis results.

    Args:
        papers: List of paper dictionaries
        stats_by_score: Statistics grouped by collaboration score
        year_stats: Statistics grouped by year
        min_citations: Minimum citation threshold used
        total_papers: Total number of papers loaded
        max_collab_score: Maximum collaboration score for binning
        heavy_hitter_pct: Percentage threshold for heavy hitters
        author_normalization: Type of author normalization used ('known' or 'all')
        max_authors: Maximum author count for normalization bins
    """

    print("\n" + "="*80)
    print("COLLABORATION SCORE vs CITATION COUNT ANALYSIS")
    print("="*80)

    # Overall statistics
    if min_citations > 0:
        print(f"\nMinimum citation threshold: {min_citations}")
        if total_papers:
            print(f"Total papers with citation data: {total_papers}")
            print(f"Papers meeting threshold: {len(papers)} ({100*len(papers)/total_papers:.1f}%)")
    else:
        print(f"\nTotal papers analyzed: {len(papers)}")

    print(f"Years covered: {min(p['year'] for p in papers)} - {max(p['year'] for p in papers)}")

    # Overall correlation
    all_scores = [p["collaboration_score"] for p in papers]
    all_citations = [p["citationCount"] for p in papers]
    all_influential = [p["influentialCitationCount"] for p in papers]

    overall_correlation = compute_correlation(all_scores, all_citations)
    influential_correlation = compute_correlation(all_scores, all_influential)

    # For normalized correlation, we need to compute normalized values for each paper
    # based on the stats_by_score which contains the expected values
    normalized_citations_list = []
    normalized_influential_list = []

    # Create a mapping from collaboration score to expected medians
    expected_by_score = {
        score: {
            "citations": stats["expected_median_citations"],
            "influential": stats["expected_median_influential"],
        }
        for score, stats in stats_by_score.items()
    }

    # For correlation, compute per-paper normalized citations
    # Use median of author bin as the expected value for each paper
    baseline_data = compute_baseline_by_author_count(papers, max_authors)

    # Pre-compute medians for each author bin (do this ONCE, not per paper!)
    baseline_medians = {}
    for author_bin, data in baseline_data.items():
        baseline_medians[author_bin] = {
            "citations": np.median(data["citations"]),
            "influential": np.median(data["influential_citations"]),
        }

    # Now compute normalized values for each paper
    for paper in papers:
        author_bin = paper["binned_author_count"]
        if author_bin in baseline_medians:
            expected_citations = baseline_medians[author_bin]["citations"]
            expected_influential = baseline_medians[author_bin]["influential"]
        else:
            expected_citations = 0
            expected_influential = 0

        normalized_citations_list.append(paper["citationCount"] - expected_citations)
        normalized_influential_list.append(
            paper["influentialCitationCount"] - expected_influential
        )

    normalized_correlation = compute_correlation(all_scores, normalized_citations_list)
    normalized_influential_correlation = compute_correlation(
        all_scores, normalized_influential_list
    )

    print(f"\n{'OVERALL CORRELATION':-^80}")
    print(f"Author normalization: {author_normalization} authors")
    print(f"\nCitation Count:")
    print(f"  Spearman rank correlation coefficient: {overall_correlation:.4f}")

    if abs(overall_correlation) < 0.1:
        interpretation = "negligible"
    elif abs(overall_correlation) < 0.3:
        interpretation = "weak"
    elif abs(overall_correlation) < 0.5:
        interpretation = "moderate"
    elif abs(overall_correlation) < 0.7:
        interpretation = "strong"
    else:
        interpretation = "very strong"

    direction = "positive" if overall_correlation > 0 else "negative"
    print(f"  Interpretation: {interpretation} {direction} correlation")

    print(f"\nInfluential Citation Count:")
    print(f"  Spearman rank correlation coefficient: {influential_correlation:.4f}")

    if abs(influential_correlation) < 0.1:
        interpretation_inf = "negligible"
    elif abs(influential_correlation) < 0.3:
        interpretation_inf = "weak"
    elif abs(influential_correlation) < 0.5:
        interpretation_inf = "moderate"
    elif abs(influential_correlation) < 0.7:
        interpretation_inf = "strong"
    else:
        interpretation_inf = "very strong"

    direction_inf = "positive" if influential_correlation > 0 else "negative"
    print(f"  Interpretation: {interpretation_inf} {direction_inf} correlation")

    print(
        f"\nNormalized Citation Count (controlling for {author_normalization} author count):"
    )
    print(f"  Spearman rank correlation coefficient: {normalized_correlation:.4f}")

    if abs(normalized_correlation) < 0.1:
        interpretation_norm = "negligible"
    elif abs(normalized_correlation) < 0.3:
        interpretation_norm = "weak"
    elif abs(normalized_correlation) < 0.5:
        interpretation_norm = "moderate"
    elif abs(normalized_correlation) < 0.7:
        interpretation_norm = "strong"
    else:
        interpretation_norm = "very strong"

    direction_norm = "positive" if normalized_correlation > 0 else "negative"
    print(f"  Interpretation: {interpretation_norm} {direction_norm} correlation")

    print(
        f"\nNormalized Influential Citation Count (controlling for {author_normalization} author count):"
    )
    print(
        f"  Spearman rank correlation coefficient: {normalized_influential_correlation:.4f}"
    )

    if abs(normalized_influential_correlation) < 0.1:
        interpretation_norm_inf = "negligible"
    elif abs(normalized_influential_correlation) < 0.3:
        interpretation_norm_inf = "weak"
    elif abs(normalized_influential_correlation) < 0.5:
        interpretation_norm_inf = "moderate"
    elif abs(normalized_influential_correlation) < 0.7:
        interpretation_norm_inf = "strong"
    else:
        interpretation_norm_inf = "very strong"

    direction_norm_inf = (
        "positive" if normalized_influential_correlation > 0 else "negative"
    )
    print(
        f"  Interpretation: {interpretation_norm_inf} {direction_norm_inf} correlation"
    )

    # Calculate heavy hitter threshold for display
    all_citations = [p["citationCount"] for p in papers]
    all_citations_sorted = sorted(all_citations, reverse=True)
    heavy_hitter_count = max(1, int(len(all_citations) * heavy_hitter_pct / 100))
    heavy_hitter_threshold = all_citations_sorted[heavy_hitter_count - 1]

    # Combined statistics table
    print(f"\n{'STATISTICS BY COLLABORATION SCORE':-^80}")
    print(f"Heavy hitter threshold: Top {heavy_hitter_pct:.1f}% of papers ({heavy_hitter_threshold}+ citations, {heavy_hitter_count} papers)")
    print()
    print(f"{'Score':<8} {'Papers':<10} {'Mean':<10} {'Median':<10} {'Mean':<10} {'Median':<10} {'HH':<8} {'HH Prob':<10}")
    print(f"{'':8} {'':10} {'Cites':<10} {'Cites':<10} {'Infl':<10} {'Infl':<10} {'Count':<8} {'(%)':<10}")
    print("-" * 80)

    for score in sorted(stats_by_score.keys()):
        stats = stats_by_score[score]
        # Display score with "+" if it's the max bin
        score_label = f"{score}+" if score == max_collab_score else str(score)
        print(f"{score_label:<8} {stats['count']:<10} {stats['mean_citations']:<10.2f} "
              f"{stats['median_citations']:<10.1f} {stats['mean_influential']:<10.2f} "
              f"{stats['median_influential']:<10.1f} {stats['heavy_hitters']:<8} "
              f"{stats['heavy_hitter_probability']:<10.2f}")

    print("DEBUG: About to print normalized statistics")
    # Normalized statistics table
    # Normalized statistics table
    print(f"\n{'NORMALIZED STATISTICS BY COLLABORATION SCORE':-^80}")
    print(f"Normalization: controlling for {author_normalization} author count")
    print(f"(Normalized value = Actual - Expected based on author count distribution)")
    print(f"(±std shows standard deviation across reference bundles)")
    print()

    # Median citations table
    print("MEDIAN CITATIONS:")
    print(
        f"{'Score':<8} {'Papers':<10} {'Actual':<12} {'Expected':<15} {'Normalized':<18} {'95% CI':<20}"
    )
    print("-" * 95)
    for score in sorted(stats_by_score.keys()):
        stats = stats_by_score[score]
        score_label = f"{score}+" if score == max_collab_score else str(score)
        std_median = stats["variance_median_citations"] ** 0.5
        std_norm = stats["variance_median_citations"] ** 0.5
        normalized = stats["normalized_median_citations"]
        ci_lower = normalized - 1.96 * std_norm
        ci_upper = normalized + 1.96 * std_norm
        print(
            f"{score_label:<8} {stats['count']:<10} "
            f"{stats['median_citations']:>8.1f}    "
            f"{stats['expected_median_citations']:>8.2f} (±{std_median:>4.2f})  "
            f"{normalized:>+7.2f} (±{std_norm:>4.2f})   "
            f"[{ci_lower:>+7.2f}, {ci_upper:>+7.2f}]"
        )

    # Mean citations table
    print(f"\nMEAN CITATIONS:")
    print(
        f"{'Score':<8} {'Papers':<10} {'Actual':<12} {'Expected':<15} {'Normalized':<18} {'95% CI':<20}"
    )
    print("-" * 95)
    for score in sorted(stats_by_score.keys()):
        stats = stats_by_score[score]
        score_label = f"{score}+" if score == max_collab_score else str(score)
        std_mean = stats["variance_mean_citations"] ** 0.5
        std_norm = stats["variance_mean_citations"] ** 0.5
        normalized = stats["normalized_mean_citations"]
        ci_lower = normalized - 1.96 * std_norm
        ci_upper = normalized + 1.96 * std_norm
        print(
            f"{score_label:<8} {stats['count']:<10} "
            f"{stats['mean_citations']:>8.2f}    "
            f"{stats['expected_mean_citations']:>8.2f} (±{std_mean:>4.2f})  "
            f"{normalized:>+7.2f} (±{std_norm:>4.2f})   "
            f"[{ci_lower:>+7.2f}, {ci_upper:>+7.2f}]"
        )

    # Heavy hitter probability table
    print(f"\nHEAVY HITTER PROBABILITY (%):")
    print(
        f"{'Score':<8} {'Papers':<10} {'Actual':<12} {'Expected':<15} {'Normalized':<18} {'95% CI':<20}"
    )
    print("-" * 95)
    for score in sorted(stats_by_score.keys()):
        stats = stats_by_score[score]
        score_label = f"{score}+" if score == max_collab_score else str(score)
        std_hh = stats["variance_heavy_hitter_probability"] ** 0.5
        std_norm = stats["variance_heavy_hitter_probability"] ** 0.5
        normalized = stats["normalized_heavy_hitter_probability"]
        ci_lower = normalized - 1.96 * std_norm
        ci_upper = normalized + 1.96 * std_norm
        print(
            f"{score_label:<8} {stats['count']:<10} "
            f"{stats['heavy_hitter_probability']:>8.2f}    "
            f"{stats['expected_heavy_hitter_probability']:>8.2f} (±{std_hh:>4.2f})  "
            f"{normalized:>+7.2f} (±{std_norm:>4.2f})   "
            f"[{ci_lower:>+7.2f}, {ci_upper:>+7.2f}]"
        )

    # Comparison: single-area vs multi-area
    print(f"\n{'SINGLE-AREA vs MULTI-AREA COMPARISON':-^80}")

    single_area = [p for p in papers if p["collaboration_score"] == 1]
    multi_area = [p for p in papers if p["collaboration_score"] >= 2]

    if single_area and multi_area:
        single_citations = [p["citationCount"] for p in single_area]
        multi_citations = [p["citationCount"] for p in multi_area]
        single_influential = [p["influentialCitationCount"] for p in single_area]
        multi_influential = [p["influentialCitationCount"] for p in multi_area]

        print(f"\nSingle-area papers (score = 1):")
        print(f"  Count: {len(single_area)}")
        print(f"  Mean citations: {statistics.mean(single_citations):.2f}")
        print(f"  Median citations: {statistics.median(single_citations):.1f}")
        print(f"  Mean influential citations: {statistics.mean(single_influential):.2f}")
        print(f"  Median influential citations: {statistics.median(single_influential):.1f}")

        print(f"\nMulti-area papers (score >= 2):")
        print(f"  Count: {len(multi_area)}")
        print(f"  Mean citations: {statistics.mean(multi_citations):.2f}")
        print(f"  Median citations: {statistics.median(multi_citations):.1f}")
        print(f"  Mean influential citations: {statistics.mean(multi_influential):.2f}")
        print(f"  Median influential citations: {statistics.median(multi_influential):.1f}")

        diff_mean = statistics.mean(multi_citations) - statistics.mean(single_citations)
        diff_pct = (diff_mean / statistics.mean(single_citations)) * 100
        diff_influential = statistics.mean(multi_influential) - statistics.mean(single_influential)
        diff_influential_pct = (diff_influential / statistics.mean(single_influential)) * 100 if statistics.mean(single_influential) > 0 else 0

        print(f"\nCitation Count Difference: {diff_mean:+.2f} citations ({diff_pct:+.1f}%)")
        print(f"Influential Citation Difference: {diff_influential:+.2f} citations ({diff_influential_pct:+.1f}%)")

    # Correlation by year
    if year_stats:
        print(f"\n{'CORRELATION BY YEAR':-^80}")
        print(f"{'Year':<8} {'Papers':<10} {'Correlation':<14} {'Mean Score':<12} {'Mean Cites':<12}")
        print("-" * 80)

        for year in sorted(year_stats.keys()):
            stats = year_stats[year]
            print(f"{year:<8} {stats['count']:<10} {stats['correlation']:<14.4f} "
                  f"{stats['mean_score']:<12.2f} {stats['mean_citations']:<12.2f}")

    print("\n" + "="*80)


def create_bar_chart(
    stats_by_score: Dict,
    graph_file: str,
    max_collab_score: int = 3,
    metaarea_filters: List[str] = None,
    area_filters: List[str] = None,
    conference_filters: List[str] = None,
    author_filters: List[str] = None,
    max_y1_val: float = None,
    max_y2_val: float = None,
    min_y3_val: float = None,
    max_y3_val: float = None,
    min_y4_val: float = None,
    max_y4_val: float = None,
    heavy_hitter_pct: float = 10.0,
    y1_tick_freq: float = None,
    y2_tick_freq: float = None,
    y3_tick_freq: float = None,
    y4_tick_freq: float = None,
):
    """Create a bar chart visualization of the analysis with two subplots.

    Args:
        stats_by_score: Statistics grouped by collaboration score
        graph_file: Output file path for the graph
        max_collab_score: Maximum collaboration score (for labeling)
        metaarea_filters: Metaarea filters applied
        area_filters: Area filters applied
        conference_filters: Conference filters applied
        author_filters: Author filters applied
        max_y1_val: Maximum primary y-axis value for first plot (None for auto-scale)
        max_y2_val: Maximum secondary y-axis value for first plot (None for auto-scale)
        min_y3_val: Minimum primary y-axis value for second plot (None for auto-scale)
        max_y3_val: Maximum primary y-axis value for second plot (None for auto-scale)
        min_y4_val: Minimum secondary y-axis value for second plot (None for auto-scale)
        max_y4_val: Maximum secondary y-axis value for second plot (None for auto-scale)
        heavy_hitter_pct: Percentage threshold for heavy hitters
        y1_tick_freq: Tick frequency for primary y-axis in first plot (None for automatic)
        y2_tick_freq: Tick frequency for secondary y-axis in first plot (None for automatic)
        y3_tick_freq: Tick frequency for primary y-axis in second plot (None for automatic)
        y4_tick_freq: Tick frequency for secondary y-axis in second plot (None for automatic)
    """
    print(f"\nCreating bar chart visualization...")

    # Prepare data
    scores = sorted(stats_by_score.keys())

    # Extract metrics
    median_citations = [stats_by_score[s]["median_citations"] for s in scores]
    mean_citations = [stats_by_score[s]["mean_citations"] for s in scores]
    normalized_median_citations = [
        stats_by_score[s]["normalized_median_citations"] for s in scores
    ]
    normalized_mean_citations = [
        stats_by_score[s]["normalized_mean_citations"] for s in scores
    ]
    hh_probability = [stats_by_score[s]["heavy_hitter_probability"] for s in scores]
    normalized_hh_probability = [
        stats_by_score[s]["normalized_heavy_hitter_probability"] for s in scores
    ]

    # Extract 95% confidence intervals for error bars (only for normalized metrics)
    # 95% CI = ±1.96 × standard deviation
    ci_normalized_median = [
        1.96 * (stats_by_score[s]["variance_median_citations"] ** 0.5) for s in scores
    ]
    ci_normalized_mean = [
        1.96 * (stats_by_score[s]["variance_mean_citations"] ** 0.5) for s in scores
    ]
    ci_normalized_hh = [
        1.96 * (stats_by_score[s]["variance_heavy_hitter_probability"] ** 0.5)
        for s in scores
    ]

    # Paper counts for legend
    paper_counts = {s: stats_by_score[s]["count"] for s in scores}
    total_papers = sum(paper_counts.values())

    # Colors for each score
    n_scores = len(scores)
    colors = plt.cm.viridis(np.linspace(0.2, 0.9, n_scores))

    # Set up the figure with two subplots side by side
    # Increase wspace to add more space between subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.subplots_adjust(wspace=0.5)  # Horizontal space between subplots

    # Bar width and positions - group by metric, not by score
    bar_width = 0.15
    group_spacing = 0.15  # Reduced from 0.3 to bring bar groups closer together
    n_metrics = 3  # median citations, mean citations, and heavy hitter probability

    # Create score labels with percentages
    score_labels = []
    for score in scores:
        score_label = f"{score}+" if score == max_collab_score else str(score)
        percentage = (paper_counts[score] / total_papers) * 100
        score_labels.append(f"{score_label} ({percentage:.0f}%)")

    # === LEFT SUBPLOT: Raw metrics ===
    # Create secondary y-axis for left subplot
    ax1_secondary = ax1.twinx()

    # X positions: group by metric (mean citations, median citations, then heavy hitter probability)
    metric_positions = np.arange(n_metrics) * (n_scores * bar_width + group_spacing)

    # Plot mean citations (first group)
    x_mean = metric_positions[0] + np.arange(n_scores) * bar_width
    bars1 = ax1.bar(x_mean, mean_citations, bar_width, color=colors, alpha=0.8)

    # Plot median citations (second group)
    x_median = metric_positions[1] + np.arange(n_scores) * bar_width
    bars2 = ax1.bar(x_median, median_citations, bar_width, color=colors, alpha=0.8)

    # Plot heavy hitter probability (third group)
    x_hh = metric_positions[2] + np.arange(n_scores) * bar_width
    bars3 = ax1_secondary.bar(x_hh, hh_probability, bar_width, color=colors, alpha=0.8)

    # Data labels will be added after y-axis limits are set

    # Customize left subplot
    ax1.set_ylabel("Citation count", fontsize=22, fontweight="bold")
    ax1_secondary.set_ylabel("Probability (%)", fontsize=22, fontweight="bold")
    ax1.tick_params(axis="y", labelsize=22)
    ax1_secondary.tick_params(axis="y", labelsize=22)
    ax1.tick_params(axis="x", labelsize=22)

    # Set x-axis labels at metric group centers
    metric_labels = [
        "Mean\ncitations",
        "Median\ncitations",
        "Heavy hitter\nprobability",
    ]
    ax1.set_xticks(metric_positions + (n_scores - 1) * bar_width / 2)
    ax1.set_xticklabels(metric_labels)

    # Apply y-axis limits and tick frequencies for first plot
    if max_y1_val is not None:
        ax1.set_ylim(0, max_y1_val)
    if max_y2_val is not None:
        ax1_secondary.set_ylim(0, max_y2_val)
    if y1_tick_freq is not None:
        ax1.yaxis.set_major_locator(plt.MultipleLocator(y1_tick_freq))
    if y2_tick_freq is not None:
        ax1_secondary.yaxis.set_major_locator(plt.MultipleLocator(y2_tick_freq))

    # Add grid with minor gridlines
    ax1.grid(axis="y", which="major", alpha=0.5, linestyle="--")
    ax1.grid(axis="y", which="minor", alpha=0.35, linestyle=":")
    ax1.minorticks_on()
    ax1.set_axisbelow(True)

    # Add data labels for left subplot - only for bars that exceed y-axis limits
    y1_lim = ax1.get_ylim()[1]
    y2_lim = ax1_secondary.get_ylim()[1]

    # Track which bars have labels to stagger them
    prev_label_y1 = None
    for i, (bar, val) in enumerate(zip(bars1, mean_citations)):
        if val > y1_lim:
            # Stagger vertically if previous bar also had a label
            if prev_label_y1 is not None:
                y_pos = y1_lim * 0.90  # Lower position for alternating
                prev_label_y1 = None
            else:
                y_pos = y1_lim * 0.95  # Higher position
                prev_label_y1 = i

            ax1.text(
                bar.get_x() + bar.get_width() / 2.0,
                y_pos,
                f"{int(val)}",
                ha="center",
                va="top",
                fontsize=18,
            )
        else:
            prev_label_y1 = None

    prev_label_y1 = None
    for i, (bar, val) in enumerate(zip(bars2, median_citations)):
        if val > y1_lim:
            # Stagger vertically if previous bar also had a label
            if prev_label_y1 is not None:
                y_pos = y1_lim * 0.90
                prev_label_y1 = None
            else:
                y_pos = y1_lim * 0.95
                prev_label_y1 = i

            ax1.text(
                bar.get_x() + bar.get_width() / 2.0,
                y_pos,
                f"{int(val)}",
                ha="center",
                va="top",
                fontsize=18,
            )
        else:
            prev_label_y1 = None

    prev_label_y2 = None
    for i, (bar, val) in enumerate(zip(bars3, hh_probability)):
        if val > y2_lim:
            # Stagger vertically if previous bar also had a label
            if prev_label_y2 is not None:
                y_pos = y2_lim * 0.90
                prev_label_y2 = None
            else:
                y_pos = y2_lim * 0.95
                prev_label_y2 = i

            ax1_secondary.text(
                bar.get_x() + bar.get_width() / 2.0,
                y_pos,
                f"{val:.1f}",
                ha="center",
                va="top",
                fontsize=18,
            )
        else:
            prev_label_y2 = None

    # === RIGHT SUBPLOT: Normalized metrics ===
    # Create secondary y-axis for right subplot
    ax2_secondary = ax2.twinx()

    # Plot normalized mean citations (first group) with error bars
    bars4 = ax2.bar(
        x_mean, normalized_mean_citations, bar_width, color=colors, alpha=0.8
    )
    ax2.errorbar(
        x_mean,
        normalized_mean_citations,
        yerr=ci_normalized_mean,
        fmt="none",
        ecolor="black",
        capsize=4,
        capthick=1.5,
        linewidth=1.5,
        alpha=0.7,
    )

    # Plot normalized median citations (second group) with error bars
    bars5 = ax2.bar(
        x_median, normalized_median_citations, bar_width, color=colors, alpha=0.8
    )
    ax2.errorbar(
        x_median,
        normalized_median_citations,
        yerr=ci_normalized_median,
        fmt="none",
        ecolor="black",
        capsize=4,
        capthick=1.5,
        linewidth=1.5,
        alpha=0.7,
    )

    # Plot normalized heavy hitter probability (third group) with error bars
    bars6 = ax2_secondary.bar(
        x_hh, normalized_hh_probability, bar_width, color=colors, alpha=0.8
    )
    ax2_secondary.errorbar(
        x_hh,
        normalized_hh_probability,
        yerr=ci_normalized_hh,
        fmt="none",
        ecolor="black",
        capsize=4,
        capthick=1.5,
        linewidth=1.5,
        alpha=0.7,
    )

    # Data labels will be added after y-axis limits are set

    # Customize right subplot
    ax2.set_ylabel("Excess citation count", fontsize=22, fontweight="bold")
    ax2_secondary.set_ylabel("Excess probability (%)", fontsize=22, fontweight="bold")
    ax2.tick_params(axis="y", labelsize=22)
    ax2_secondary.tick_params(axis="y", labelsize=22)
    ax2.tick_params(axis="x", labelsize=22)

    ax2.set_xticks(metric_positions + (n_scores - 1) * bar_width / 2)
    ax2.set_xticklabels(metric_labels)

    # Add horizontal line at zero for normalized plot
    ax2.axhline(y=0, color="black", linestyle="-", linewidth=0.8, alpha=0.5)
    ax2_secondary.axhline(y=0, color="black", linestyle="-", linewidth=0.8, alpha=0.5)

    # Apply y-axis limits and tick frequencies for second plot
    if min_y3_val is not None and max_y3_val is not None:
        # Use specified limits for primary axis
        ax2.set_ylim(min_y3_val, max_y3_val)
    elif max_y3_val is not None:
        # Only max specified, use symmetric limits
        ax2.set_ylim(-max_y3_val, max_y3_val)
    else:
        # Auto-scale: center zero on the y-axis for normalized plot
        # Get the max absolute value for symmetric axes (consider both median and mean)
        max_abs_citations = max(
            abs(min(normalized_median_citations)),
            abs(max(normalized_median_citations)),
            abs(min(normalized_mean_citations)),
            abs(max(normalized_mean_citations)),
        )

        # Add some padding (20%)
        max_abs_citations *= 1.2

        ax2.set_ylim(-max_abs_citations, max_abs_citations)

    if min_y4_val is not None and max_y4_val is not None:
        # Use specified limits for secondary axis
        ax2_secondary.set_ylim(min_y4_val, max_y4_val)
    elif max_y4_val is not None:
        # Only max specified, use symmetric limits
        ax2_secondary.set_ylim(-max_y4_val, max_y4_val)
    else:
        # Auto-scale
        max_abs_hh = max(
            abs(min(normalized_hh_probability)), abs(max(normalized_hh_probability))
        )

        # Add some padding (20%)
        max_abs_hh *= 1.2

        ax2_secondary.set_ylim(-max_abs_hh, max_abs_hh)

    if y3_tick_freq is not None:
        ax2.yaxis.set_major_locator(plt.MultipleLocator(y3_tick_freq))
    if y4_tick_freq is not None:
        ax2_secondary.yaxis.set_major_locator(plt.MultipleLocator(y4_tick_freq))

    # Add grid with minor gridlines
    ax2.grid(axis="y", which="major", alpha=0.5, linestyle="--")
    ax2.grid(axis="y", which="minor", alpha=0.35, linestyle=":")
    ax2.minorticks_on()
    ax2.set_axisbelow(True)

    # Add data labels for right subplot - only for bars that exceed y-axis limits
    y3_lim_upper = ax2.get_ylim()[1]
    y3_lim_lower = ax2.get_ylim()[0]
    y4_lim_upper = ax2_secondary.get_ylim()[1]
    y4_lim_lower = ax2_secondary.get_ylim()[0]

    prev_label_y3_upper = None
    prev_label_y3_lower = None
    for i, (bar, val) in enumerate(zip(bars4, normalized_mean_citations)):
        if val > y3_lim_upper:
            # Stagger vertically if previous bar also had a label
            if prev_label_y3_upper is not None:
                y_pos = y3_lim_upper * 0.90
                prev_label_y3_upper = None
            else:
                y_pos = y3_lim_upper * 0.95
                prev_label_y3_upper = i

            ax2.text(
                bar.get_x() + bar.get_width() / 2.0,
                y_pos,
                f"{val:+.1f}",
                ha="center",
                va="top",
                fontsize=18,
            )
        elif val < y3_lim_lower:
            # Stagger vertically if previous bar also had a label
            if prev_label_y3_lower is not None:
                y_pos = y3_lim_lower * 0.90
                prev_label_y3_lower = None
            else:
                y_pos = y3_lim_lower * 0.95
                prev_label_y3_lower = i

            ax2.text(
                bar.get_x() + bar.get_width() / 2.0,
                y_pos,
                f"{val:+.1f}",
                ha="center",
                va="bottom",
                fontsize=18,
            )
        else:
            prev_label_y3_upper = None
            prev_label_y3_lower = None

    prev_label_y3_upper = None
    prev_label_y3_lower = None
    for i, (bar, val) in enumerate(zip(bars5, normalized_median_citations)):
        if val > y3_lim_upper:
            # Stagger vertically if previous bar also had a label
            if prev_label_y3_upper is not None:
                y_pos = y3_lim_upper * 0.90
                prev_label_y3_upper = None
            else:
                y_pos = y3_lim_upper * 0.95
                prev_label_y3_upper = i

            ax2.text(
                bar.get_x() + bar.get_width() / 2.0,
                y_pos,
                f"{val:+.1f}",
                ha="center",
                va="top",
                fontsize=18,
            )
        elif val < y3_lim_lower:
            # Stagger vertically if previous bar also had a label
            if prev_label_y3_lower is not None:
                y_pos = y3_lim_lower * 0.90
                prev_label_y3_lower = None
            else:
                y_pos = y3_lim_lower * 0.95
                prev_label_y3_lower = i

            ax2.text(
                bar.get_x() + bar.get_width() / 2.0,
                y_pos,
                f"{val:+.1f}",
                ha="center",
                va="bottom",
                fontsize=18,
            )
        else:
            prev_label_y3_upper = None
            prev_label_y3_lower = None

    prev_label_y4_upper = None
    prev_label_y4_lower = None
    for i, (bar, val) in enumerate(zip(bars6, normalized_hh_probability)):
        if val > y4_lim_upper:
            # Stagger vertically if previous bar also had a label
            if prev_label_y4_upper is not None:
                y_pos = y4_lim_upper * 0.90
                prev_label_y4_upper = None
            else:
                y_pos = y4_lim_upper * 0.95
                prev_label_y4_upper = i

            ax2_secondary.text(
                bar.get_x() + bar.get_width() / 2.0,
                y_pos,
                f"{val:+.1f}",
                ha="center",
                va="top",
                fontsize=18,
            )
        elif val < y4_lim_lower:
            # Stagger vertically if previous bar also had a label
            if prev_label_y4_lower is not None:
                y_pos = y4_lim_lower * 0.90
                prev_label_y4_lower = None
            else:
                y_pos = y4_lim_lower * 0.95
                prev_label_y4_lower = i

            ax2_secondary.text(
                bar.get_x() + bar.get_width() / 2.0,
                y_pos,
                f"{val:+.1f}",
                ha="center",
                va="bottom",
                fontsize=18,
            )
        else:
            prev_label_y4_upper = None
            prev_label_y4_lower = None

    # Create custom legend with labels below color boxes
    # Create custom legend with labels below color boxes
    # Convert bar_width from data coordinates to axis coordinates
    # Get the x-axis range to calculate the relative width
    x_range = ax2.get_xlim()[1] - ax2.get_xlim()[0]
    box_width_axis = bar_width / x_range  # Convert bar width to axis coordinates

    # Position in axis coordinates (0-1 range)
    legend_x_start = 0.20  # Start position (moved left)
    legend_y = 0.85  # Positioned at top of plot
    box_height = 0.04  # Height of color box
    spacing = box_width_axis * 3.5  # Spacing to prevent overlap

    # Calculate center position for the legend
    total_width = (n_scores - 1) * spacing
    legend_x_center = legend_x_start + total_width / 2

    # Add title centered above the boxes
    ax2.text(
        legend_x_center,
        legend_y + 0.06,
        "Num areas",
        transform=ax2.transAxes,
        fontsize=22,
        ha="center",
        va="bottom",
    )

    # Add color boxes and labels
    for i, (color, label) in enumerate(zip(colors, score_labels)):
        x_pos = legend_x_start + i * spacing

        # Add color box with same width as bars
        box = plt.Rectangle(
            (x_pos - box_width_axis / 2, legend_y),
            box_width_axis,
            box_height,
            facecolor=color,
            alpha=0.8,
            transform=ax2.transAxes,
            clip_on=False,
        )
        ax2.add_patch(box)

        # Add label below box
        ax2.text(
            x_pos,
            legend_y - 0.02,
            label,
            transform=ax2.transAxes,
            fontsize=22,
            ha="center",
            va="top",
        )

    # Metaarea friendly names
    METAAREA_NAMES = {
        'ai': 'AI',
        'systems': 'Systems',
        'theory': 'Theory',
        'interdisciplinary': 'Interdisciplinary'
    }

    # Determine title based on filters with friendly names
    venue_desc = None
    if conference_filters:
        friendly_names = [AREA_NAMES.get(c, c) for c in conference_filters]
        venue_desc = ", ".join(friendly_names) + " papers"
    elif area_filters:
        friendly_names = [AREA_NAMES.get(a, a) for a in area_filters]
        venue_desc = ", ".join(friendly_names) + " papers"
    elif metaarea_filters:
        friendly_names = [METAAREA_NAMES.get(m, m) for m in metaarea_filters]
        venue_desc = ", ".join(friendly_names) + " papers"
    else:
        venue_desc = "All papers"

    # Add author filter to title if specified
    if author_filters:
        author_desc = ", ".join(author_filters)
        filter_desc = f"{venue_desc} by {author_desc} (n={total_papers:,})"
    else:
        filter_desc = f"{venue_desc} (n={total_papers:,})"

    # Add overall title
    fig.suptitle(filter_desc, fontsize=22, fontweight="bold", y=0.98)

    # Adjust layout to prevent label cutoff, but preserve wspace
    plt.tight_layout(rect=[0, 0, 1, 0.96], w_pad=4.0)

    # Create directory if it doesn't exist
    graph_dir = os.path.dirname(graph_file)
    if graph_dir and not os.path.exists(graph_dir):
        os.makedirs(graph_dir)

    # Save the figure
    plt.savefig(graph_file, dpi=300, bbox_inches='tight')
    print(f"Bar chart saved to {graph_file}")
    plt.close()


def write_detailed_output(papers: List[Dict], output_file: str):
    """Write detailed analysis to a file."""
    print(f"\nWriting detailed analysis to {output_file}...")
    
    # Sort papers by citation count
    papers_sorted = sorted(papers, key=lambda p: p["citationCount"], reverse=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Collaboration Score vs Citation Count - Detailed Analysis\n")
        f.write("="*80 + "\n\n")
        
        # Write top 100 most cited papers
        f.write("TOP 100 MOST CITED PAPERS\n")
        f.write("-"*80 + "\n")
        f.write(f"{'Rank':<6} {'Cites':<8} {'Score':<8} {'Title':<50} {'Areas'}\n")
        f.write("-"*80 + "\n")
        
        for i, paper in enumerate(papers_sorted[:100], 1):
            title = paper["title"][:47] + "..." if len(paper["title"]) > 50 else paper["title"]
            areas = paper["collaboration_areas"][:30] if paper["collaboration_areas"] else "N/A"
            f.write(f"{i:<6} {paper['citationCount']:<8} {paper['collaboration_score']:<8} "
                   f"{title:<50} {areas}\n")
    
    print(f"Detailed analysis written to {output_file}")


def main():
    """Main function."""
    args = parse_arguments()

    # Check that only one venue filter type is specified
    venue_filter_count = sum([
        args.metaareas is not None,
        args.areas is not None,
        args.conference_filters is not None
    ])

    if venue_filter_count > 1:
        print("Error: Only one of --only-metaareas, --only-areas, or --only-conferences can be specified at a time.")
        sys.exit(1)

    # Validate filter arguments
    validate_filters(args.metaareas, args.areas, args.conference_filters)

    print(f"Collaboration level: {args.collaboration_level}")
    if args.conference_filters:
        print(f"Conference filter(s): {', '.join(args.conference_filters)}")
    elif args.areas:
        print(f"Area filter(s): {', '.join(args.areas)}")
    elif args.metaareas:
        print(f"Metaarea filter(s): {', '.join(args.metaareas)}")

    if args.author_filters:
        print(f"Author filter(s): {', '.join(args.author_filters)}")

    print(f"Max collaboration score (binning threshold): {args.max_collaboration_score}")

    # Load data (will recompute collaboration scores at the specified level)
    papers, total_papers = load_data(
        args.citations,
        args.papers_file,
        args.min_citations,
        args.collaboration_level,
        args.metaareas,
        args.areas,
        args.conference_filters,
        args.author_filters,
        args.max_collaboration_score,
        args.from_year,
        args.to_year,
        args.author_normalization,
        args.max_authors,
    )

    if not papers:
        print("No papers with citation data found.")
        sys.exit(1)

    # Analyze
    stats_by_score = analyze_by_score(
        papers, args.heavy_hitter, args.max_authors, args.num_reference_bundles
    )
    year_stats = analyze_by_year(papers)

    # Print analysis
    print_analysis(
        papers,
        stats_by_score,
        year_stats,
        args.min_citations,
        total_papers,
        args.max_collaboration_score,
        args.heavy_hitter,
        args.author_normalization,
        args.max_authors,
    )

    # Create bar chart visualization only if --graph is specified
    if args.graph:
        create_bar_chart(
            stats_by_score,
            args.graph,
            args.max_collaboration_score,
            args.metaareas,
            args.areas,
            args.conference_filters,
            args.author_filters,
            args.max_y1_val,
            args.max_y2_val,
            args.min_y3_val,
            args.max_y3_val,
            args.min_y4_val,
            args.max_y4_val,
            args.heavy_hitter,
            args.y1_tick_freq,
            args.y2_tick_freq,
            args.y3_tick_freq,
            args.y4_tick_freq,
        )

    # Write detailed output if requested
    if args.output:
        write_detailed_output(papers, args.output)

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
