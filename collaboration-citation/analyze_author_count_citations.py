#!/usr/bin/env python3
"""
Analyze the correlation between number of authors and citation count.

This script examines whether papers with more authors tend to receive more
citations, using non-parametric statistical methods that don't assume linearity.
"""

import argparse
import csv
import sys
from typing import List, Dict, Tuple, Set
import statistics
import matplotlib.pyplot as plt
import numpy as np

# Conference to parent area mapping (from csrankings.ts)
PARENT_MAP = {
    "aaai": "ai",
    "ijcai": "ai",
    "cvpr": "vision",
    "eccv": "vision",
    "iccv": "vision",
    "icml": "mlmining",
    "iclr": "mlmining",
    "kdd": "mlmining",
    "nips": "mlmining",
    "acl": "nlp",
    "emnlp": "nlp",
    "naacl": "nlp",
    "sigir": "inforet",
    "www": "inforet",
    "asplos": "arch",
    "isca": "arch",
    "micro": "arch",
    "hpca": "arch",
    "ccs": "sec",
    "oakland": "sec",
    "usenixsec": "sec",
    "ndss": "sec",
    "pets": "sec",
    "vldb": "mod",
    "sigmod": "mod",
    "icde": "mod",
    "pods": "mod",
    "dac": "da",
    "iccad": "da",
    "emsoft": "bed",
    "rtas": "bed",
    "rtss": "bed",
    "sc": "hpc",
    "hpdc": "hpc",
    "ics": "hpc",
    "mobicom": "mobile",
    "mobisys": "mobile",
    "sensys": "mobile",
    "imc": "metrics",
    "sigmetrics": "metrics",
    "osdi": "ops",
    "sosp": "ops",
    "eurosys": "ops",
    "fast": "ops",
    "usenixatc": "ops",
    "popl": "plan",
    "pldi": "plan",
    "oopsla": "plan",
    "icfp": "plan",
    "pacmpl": "plan",
    "fse": "soft",
    "icse": "soft",
    "ase": "soft",
    "issta": "soft",
    "nsdi": "comm",
    "sigcomm": "comm",
    "siggraph": "graph",
    "siggraph-asia": "graph",
    "eurographics": "graph",
    "focs": "act",
    "soda": "act",
    "stoc": "act",
    "crypto": "crypt",
    "eurocrypt": "crypt",
    "cav": "log",
    "lics": "log",
    "ismb": "bio",
    "recomb": "bio",
    "ec": "ecom",
    "wine": "ecom",
    "chiconf": "chi",
    "ubicomp": "chi",
    "uist": "chi",
    "icra": "robotics",
    "iros": "robotics",
    "rss": "robotics",
    "vis": "visualization",
    "vr": "visualization",
    "sigcse": "csed",
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
        description="Analyze correlation between author count and citations"
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
        help="Input CSV file with paper information (papers.csv)",
    )
    parser.add_argument(
        "--min-citations",
        type=int,
        default=0,
        help="Minimum citation count for papers to include (default: 0)",
    )
    parser.add_argument(
        "--max-authors",
        type=int,
        default=20,
        help="Maximum author count to display separately; higher counts are binned together (default: 20)",
    )
    parser.add_argument(
        "--graph",
        type=str,
        default=None,
        help="Output file for visualization (default: None, no graph generated)",
    )
    parser.add_argument(
        "--from-year",
        type=int,
        default=None,
        help="Filter papers from this year onwards (inclusive) (default: None)",
    )
    parser.add_argument(
        "--to-year",
        type=int,
        default=None,
        help="Filter papers up to this year (inclusive) (default: None)",
    )
    parser.add_argument(
        "--author-normalization",
        type=str,
        choices=["known", "all"],
        default="all",
        help="Count 'known' (faculty authors only) or 'all' authors (default: all)",
    )
    parser.add_argument(
        "--home-run",
        dest="home_run_pct",
        type=float,
        default=10.0,
        help="Percentage threshold for home runs (top X%% of papers by citation count) (default: 10.0)",
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
        "--max-y1-val",
        type=float,
        default=75,
        help="Maximum value for primary y-axis (median citations) (default: 75)",
    )
    parser.add_argument(
        "--max-y2-val",
        type=float,
        default=20,
        help="Maximum value for secondary y-axis (home run probability) (default: 20)",
    )
    parser.add_argument(
        "--y1-tick-freq",
        type=float,
        default=None,
        help="Tick frequency for primary y-axis (median citations) (default: None, automatic)",
    )
    parser.add_argument(
        "--y2-tick-freq",
        type=float,
        default=None,
        help="Tick frequency for secondary y-axis (home run probability) (default: None, automatic)",
    )
    return parser.parse_args()


def load_data(
    citations_file: str,
    papers_file: str,
    min_citations: int = 0,
    max_authors: int = 20,
    from_year: int = None,
    to_year: int = None,
    author_normalization: str = "all",
    metaarea_filters: List[str] = None,
    area_filters: List[str] = None,
    conference_filters: List[str] = None,
    author_filters: List[str] = None,
) -> Tuple[List[Dict], int]:
    """Load papers with author counts and citation data.
    
    Args:
        citations_file: Path to citations CSV file
        papers_file: Path to papers CSV file
        min_citations: Minimum citation count threshold
        max_authors: Maximum author count to display separately
        from_year: If specified, only include papers from this year onwards
        to_year: If specified, only include papers up to this year
        author_normalization: Count 'known' or 'all' authors
        metaarea_filters: If specified, only include papers published in these metaareas
        area_filters: If specified, only include papers published in these areas
        conference_filters: If specified, only include papers published in these conferences
        author_filters: If specified, only include papers authored by these faculty members
    
    Returns:
        Tuple of (filtered papers, total papers loaded)
    """
    all_papers = []
    
    print(f"Loading citation data from {citations_file}...")
    print(f"Loading paper data from {papers_file}...")
    print(f"Author count mode: {author_normalization} authors")
    
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
                # Determine author count based on normalization mode
                if author_normalization == "known":
                    # Count only known (faculty) authors
                    known_authors = row.get("known_authors", row.get("authors", ""))
                    author_count = len(known_authors.split(";")) if known_authors else 0
                else:  # "all"
                    # Use total author count if available, otherwise fall back to known authors
                    if "num_authors" in row and row["num_authors"]:
                        author_count = int(row["num_authors"])
                    else:
                        # Fallback for older papers.csv format
                        known_authors = row.get("known_authors", row.get("authors", ""))
                        author_count = len(known_authors.split(";")) if known_authors else 0
                
                paper_info[row["dblp_key"]] = {
                    "author_count": author_count,
                    "conference": row.get("conference", ""),
                    "known_authors": row.get("known_authors", ""),
                }
        
        print(f"Loaded paper information for {len(paper_info)} papers")
        
        # Load citation data and join with author count
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
                        paper_year = int(row["year"])
                        
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
                        
                        # Apply year filters
                        if from_year is not None and paper_year < from_year:
                            continue
                        if to_year is not None and paper_year > to_year:
                            continue
                        
                        # Get author count
                        author_count = paper_data["author_count"]
                        
                        # Bin author counts: max_authors+ -> max_authors
                        binned_author_count = min(author_count, max_authors)
                        
                        all_papers.append({
                            "dblp_key": dblp_key,
                            "title": row["title"],
                            "year": paper_year,
                            "citationCount": citation_count,
                            "influentialCitationCount": int(row["influentialCitationCount"]) if row["influentialCitationCount"] else 0,
                            "author_count": binned_author_count,
                        })
                    except (ValueError, KeyError):
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


def compute_spearman_correlation(x: List[float], y: List[float]) -> float:
    """Compute Spearman rank correlation coefficient."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0

    def rank_data(data):
        """Assign ranks to data, handling ties with average ranks."""
        sorted_indices = sorted(range(len(data)), key=lambda i: data[i])
        ranks = [0] * len(data)

        i = 0
        while i < len(sorted_indices):
            j = i
            while j < len(sorted_indices) - 1 and data[sorted_indices[j]] == data[sorted_indices[j + 1]]:
                j += 1

            avg_rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[sorted_indices[k]] = avg_rank

            i = j + 1

        return ranks

    ranks_x = rank_data(x)
    ranks_y = rank_data(y)

    n = len(ranks_x)
    mean_x = statistics.mean(ranks_x)
    mean_y = statistics.mean(ranks_y)

    numerator = sum((ranks_x[i] - mean_x) * (ranks_y[i] - mean_y) for i in range(n))
    denominator_x = sum((ranks_x[i] - mean_x) ** 2 for i in range(n))
    denominator_y = sum((ranks_y[i] - mean_y) ** 2 for i in range(n))

    if denominator_x == 0 or denominator_y == 0:
        return 0.0

    return numerator / (denominator_x * denominator_y) ** 0.5


def analyze_by_author_count(
    papers: List[Dict], home_run_pct: float = 10.0
) -> Dict[int, Dict]:
    """Group papers by author count and compute statistics.

    Args:
        papers: List of paper dictionaries
        home_run_pct: Percentage threshold for home runs (default: 10.0)

    Returns:
        Dictionary mapping author counts to statistics
    """
    by_count = {}

    for paper in papers:
        count = paper["author_count"]
        if count not in by_count:
            by_count[count] = {
                "papers": [],
                "citations": [],
                "influential_citations": [],
            }

        by_count[count]["papers"].append(paper)
        by_count[count]["citations"].append(paper["citationCount"])
        by_count[count]["influential_citations"].append(paper["influentialCitationCount"])

    # Determine home run threshold (top X% by citation count)
    all_citations = [p["citationCount"] for p in papers]
    all_citations_sorted = sorted(all_citations, reverse=True)
    home_run_count = max(1, int(len(all_citations) * home_run_pct / 100))
    home_run_threshold = all_citations_sorted[home_run_count - 1]

    # Compute statistics for each author count
    stats_by_count = {}
    for count, data in by_count.items():
        citations = data["citations"]
        influential = data["influential_citations"]

        # Count home runs in this author count group
        home_runs_in_group = sum(1 for c in citations if c >= home_run_threshold)
        home_run_probability = (
            (home_runs_in_group / len(citations)) * 100 if len(citations) > 0 else 0
        )

        stats_by_count[count] = {
            "count": len(citations),
            "mean_citations": statistics.mean(citations),
            "median_citations": statistics.median(citations),
            "stdev_citations": statistics.stdev(citations) if len(citations) > 1 else 0,
            "mean_influential": statistics.mean(influential),
            "median_influential": statistics.median(influential),
            "home_runs": home_runs_in_group,
            "home_run_probability": home_run_probability,
        }

    return stats_by_count


def print_analysis(
    papers: List[Dict],
    stats_by_count: Dict,
    min_citations: int = 0,
    total_papers: int = None,
    max_authors: int = 20,
    author_normalization: str = "all",
    home_run_pct: float = 10.0,
):
    """Print comprehensive analysis results."""

    print("\n" + "="*80)
    print("AUTHOR COUNT vs CITATION COUNT ANALYSIS")
    print("="*80)
    print(f"Author count mode: {author_normalization} authors")

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
    all_counts = [p["author_count"] for p in papers]
    all_citations = [p["citationCount"] for p in papers]
    all_influential = [p["influentialCitationCount"] for p in papers]

    overall_correlation = compute_spearman_correlation(all_counts, all_citations)
    influential_correlation = compute_spearman_correlation(all_counts, all_influential)

    print(f"\n{'OVERALL CORRELATION':-^80}")
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

    # Calculate home run threshold for display
    all_citations = [p["citationCount"] for p in papers]
    all_citations_sorted = sorted(all_citations, reverse=True)
    home_run_count = max(1, int(len(all_citations) * home_run_pct / 100))
    home_run_threshold = all_citations_sorted[home_run_count - 1]

    # Statistics table
    print(f"\n{'STATISTICS BY AUTHOR COUNT':-^80}")
    print(
        f"Home run threshold: Top {home_run_pct:.1f}% of papers ({home_run_threshold}+ citations, {home_run_count} papers)"
    )
    print()
    print(
        f"{'Authors':<10} {'Papers':<10} {'Mean':<12} {'Median':<12} {'Mean':<12} {'Median':<12} {'HR':<8} {'HR Prob':<10}"
    )
    print(f"{'':10} {'':10} {'Cites':<12} {'Cites':<12} {'Infl':<12} {'Infl':<12} {'Count':<8} {'(%)':<10}")
    print("-" * 80)

    for count in sorted(stats_by_count.keys()):
        stats = stats_by_count[count]
        count_label = f"{count}+" if count == max_authors else str(count)
        print(
            f"{count_label:<10} {stats['count']:<10} {stats['mean_citations']:<12.2f} "
            f"{stats['median_citations']:<12.1f} {stats['mean_influential']:<12.2f} "
            f"{stats['median_influential']:<12.1f} {stats['home_runs']:<8} "
            f"{stats['home_run_probability']:<10.2f}"
        )

    print("\n" + "="*80)


def create_visualization(
    stats_by_count: Dict,
    graph_file: str,
    max_authors: int = 20,
    total_papers: int = None,
    home_run_pct: float = 10.0,
    max_y1_val: float = 75,
    max_y2_val: float = 20,
    y1_tick_freq: float = None,
    y2_tick_freq: float = None,
):
    """Create visualization of author count vs citations."""
    print(f"\nCreating visualization...")

    counts = sorted(stats_by_count.keys())
    median_citations = [stats_by_count[c]['median_citations'] for c in counts]
    mean_citations = [stats_by_count[c]["mean_citations"] for c in counts]
    home_run_probs = [stats_by_count[c]["home_run_probability"] for c in counts]
    paper_counts = [stats_by_count[c]['count'] for c in counts]

    # Calculate total papers for percentages
    if total_papers is None:
        total_papers = sum(paper_counts)

    # Create figure with primary and secondary y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()

    x_pos = np.arange(len(counts))

    # Calculate linear regression for median citations
    coefficients_median = np.polyfit(x_pos, median_citations, 1)
    regression_line_median = np.poly1d(coefficients_median)
    y_regression_median = regression_line_median(x_pos)

    # Calculate linear regression for mean citations
    coefficients_mean = np.polyfit(x_pos, mean_citations, 1)
    regression_line_mean = np.poly1d(coefficients_mean)
    y_regression_mean = regression_line_mean(x_pos)

    # Calculate linear regression for home run probability
    coefficients_hr = np.polyfit(x_pos, home_run_probs, 1)
    regression_line_hr = np.poly1d(coefficients_hr)
    y_regression_hr = regression_line_hr(x_pos)

    # Primary y-axis: Median citations (line with markers)
    line1 = ax1.plot(x_pos, median_citations, marker='o', markersize=8, linewidth=2,
                     label='Median citations', color='steelblue', alpha=0.8)

    # Primary y-axis: Mean citations (line with markers)
    line3 = ax1.plot(
        x_pos,
        mean_citations,
        marker="^",
        markersize=8,
        linewidth=2,
        label="Mean citations",
        color="darkgreen",
        alpha=0.8,
    )

    # Add linear regression line for median citations
    line_regression_median = ax1.plot(
        x_pos,
        y_regression_median,
        linestyle="--",
        linewidth=2,
        color="darkblue",
        alpha=0.6,
    )

    # Add linear regression line for mean citations
    line_regression_mean = ax1.plot(
        x_pos,
        y_regression_mean,
        linestyle="--",
        linewidth=2,
        color="green",
        alpha=0.6,
    )

    # Add regression formula for median as text annotation
    slope_median = coefficients_median[0]
    intercept_median = coefficients_median[1]
    formula_text_median = f"y = {slope_median:.1f}x + {intercept_median:.1f}"

    # Position the text slightly below the median regression line at x=3
    x_pos_label = 3
    y_pos_label_median = y_regression_median[x_pos_label] - 3
    ax1.text(
        x_pos_label,
        y_pos_label_median,
        formula_text_median,
        fontsize=18,
        color="darkblue",
        verticalalignment="top",
    )

    # Add regression formula for mean as text annotation
    slope_mean = coefficients_mean[0]
    intercept_mean = coefficients_mean[1]
    formula_text_mean = f"y = {slope_mean:.1f}x + {intercept_mean:.1f}"

    # Position the text slightly above the mean data point at x=4 (index 3)
    x_pos_label_mean = 3
    y_pos_label_mean = mean_citations[x_pos_label_mean] + 3
    ax1.text(
        x_pos_label_mean,
        y_pos_label_mean,
        formula_text_mean,
        fontsize=18,
        color="green",
        verticalalignment="bottom",
    )

    # Secondary y-axis: Home run probability (line with markers)
    line2 = ax2.plot(
        x_pos,
        home_run_probs,
        marker="s",
        markersize=8,
        linewidth=2,
        label="Home run probability",
        color="coral",
        alpha=0.8,
    )

    # Add linear regression line for home run probability
    line_regression_hr = ax2.plot(
        x_pos,
        y_regression_hr,
        linestyle="--",
        linewidth=2,
        color="red",
        alpha=0.6,
    )

    # Add regression formula for home run as text annotation
    slope_hr = coefficients_hr[0]
    intercept_hr = coefficients_hr[1]
    formula_text_hr = f"y = {slope_hr:.1f}x + {intercept_hr:.1f}"

    # Position the text slightly below the home run regression line at x=4 (index 3)
    x_pos_label_hr = 3
    y_pos_label_hr = y_regression_hr[x_pos_label_hr] - 0.5
    ax2.text(
        x_pos_label_hr,
        y_pos_label_hr,
        formula_text_hr,
        fontsize=18,
        color="red",
        verticalalignment="top",
    )

    # Set labels and title with increased label padding
    ax1.set_xlabel('Number of authors (% of papers)', fontsize=22, fontweight='bold', labelpad=15)
    ax1.set_ylabel('Citation count', fontsize=22, fontweight='bold', color='black', labelpad=15)
    ax2.set_ylabel('Probability (%)', fontsize=22, fontweight='bold', color='black', labelpad=15)

    # Set title with total paper count
    ax1.set_title(f'All papers (n={total_papers:,})', fontsize=22, fontweight='bold')

    # Customize x-axis labels to include author count and fraction
    x_labels = []
    for i, count in enumerate(counts):
        count_label = f"{count}+" if count == max_authors else str(count)
        percentage = (paper_counts[i] / total_papers) * 100
        x_labels.append(f"{count_label}\n({percentage:.1f}%)")

    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(x_labels, fontsize=22)

    # Set tick labels to black
    ax1.tick_params(axis='y', labelcolor='black', labelsize=22)
    ax1.tick_params(axis='x', labelcolor='black', labelsize=22)
    ax2.tick_params(axis='y', labelcolor='black', labelsize=22)

    # Set both y-axes to start at zero and set maximum values
    ax1.set_ylim(bottom=0, top=max_y1_val)
    ax2.set_ylim(bottom=0, top=max_y2_val)

    # Set tick frequencies if specified
    if y1_tick_freq is not None:
        ax1.set_yticks(np.arange(0, max_y1_val + y1_tick_freq, y1_tick_freq))
        # Set minor ticks at half the major tick frequency
        ax1.set_yticks(np.arange(0, max_y1_val + y1_tick_freq / 2, y1_tick_freq / 2), minor=True)
    if y2_tick_freq is not None:
        ax2.set_yticks(np.arange(0, max_y2_val + y2_tick_freq, y2_tick_freq))
        # Set minor ticks at half the major tick frequency
        ax2.set_yticks(np.arange(0, max_y2_val + y2_tick_freq / 2, y2_tick_freq / 2), minor=True)

    # Add grid for readability - major and minor grids
    ax1.grid(axis='y', which='major', alpha=0.5, linestyle='--')
    ax1.grid(axis='y', which='minor', alpha=0.3, linestyle=':')

    # Add text labels at specific positions instead of legends
    # Median label at x=0 (author count 1), y=15
    ax1.text(
        0,
        15,
        "Median citations",
        fontsize=22,
        color="steelblue",
        verticalalignment="center",
        fontweight="normal",
    )

    # Mean label at x=0 (author count 1), y=115
    ax1.text(
        0,
        115,
        "Mean citations",
        fontsize=22,
        color="darkgreen",
        verticalalignment="center",
        fontweight="normal",
    )

    # Home run label at x=0 (author count 1), y=60
    ax1.text(
        0,
        60,
        "Home run probability",
        fontsize=22,
        color="coral",
        verticalalignment="center",
        fontweight="normal",
    )

    plt.tight_layout()
    plt.savefig(graph_file, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {graph_file}")
    plt.close()


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

    # Load data
    papers, total_papers = load_data(
        args.citations,
        args.papers,
        args.min_citations,
        args.max_authors,
        args.from_year,
        args.to_year,
        args.author_normalization,
        args.metaareas,
        args.areas,
        args.conference_filters,
        args.author_filters,
    )

    if not papers:
        print("No papers with citation data found.")
        sys.exit(1)

    # Analyze
    stats_by_count = analyze_by_author_count(papers, args.home_run_pct)

    # Print analysis
    print_analysis(
        papers,
        stats_by_count,
        args.min_citations,
        total_papers,
        args.max_authors,
        args.author_normalization,
        args.home_run_pct,
    )

    # Create visualization if requested
    if args.graph:
        create_visualization(
            stats_by_count,
            args.graph,
            args.max_authors,
            total_papers,
            args.home_run_pct,
            args.max_y1_val,
            args.max_y2_val,
            args.y1_tick_freq,
            args.y2_tick_freq,
        )

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
