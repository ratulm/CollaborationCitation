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
        "--max-y-val",
        type=float,
        default=None,
        help="Maximum y-axis value for the graph (default: auto-scale)",
    )
    parser.add_argument(
        "--heavy-hitter",
        type=float,
        default=10.0,
        help="Percentage threshold for heavy hitters (top X%% of papers by citation count) (default: 10.0)",
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


def load_data(citations_file: str, papers_file: str, min_citations: int = 0, collaboration_level: str = "conference", metaarea_filters: List[str] = None, area_filters: List[str] = None, conference_filters: List[str] = None, author_filters: List[str] = None, max_collab_score: int = 3) -> Tuple[List[Dict], int]:
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
    
    try:
        # Load paper information indexed by dblp_key
        paper_info = {}
        with open(papers_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                paper_info[row["dblp_key"]] = {
                    "conference": row.get("conference", ""),
                    "author_conferences": row.get("author_conferences", ""),
                    "authors": row.get("authors", "")
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
                            paper_authors = paper_data["authors"].split(";") if paper_data["authors"] else []
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
                        
                        all_papers.append({
                            "dblp_key": dblp_key,
                            "title": row["title"],
                            "year": int(row["year"]),
                            "citationCount": citation_count,
                            "influentialCitationCount": int(row["influentialCitationCount"]) if row["influentialCitationCount"] else 0,
                            "collaboration_score": binned_score,
                            "collaboration_areas": areas_string,
                        })
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


def analyze_by_score(papers: List[Dict], heavy_hitter_pct: float = 10.0) -> Dict[int, Dict]:
    """Group papers by collaboration score and compute statistics.
    
    Args:
        papers: List of paper dictionaries
        heavy_hitter_pct: Percentage threshold for heavy hitters (default: 10.0)
    
    Returns:
        Dictionary mapping collaboration scores to statistics
    """
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
        by_score[score]["influential_citations"].append(paper["influentialCitationCount"])
    
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
        
        # Count heavy hitters in this score group
        heavy_hitters_in_group = sum(1 for c in citations if c >= heavy_hitter_threshold)
        heavy_hitter_probability = (heavy_hitters_in_group / len(citations)) * 100 if len(citations) > 0 else 0
        
        stats_by_score[score] = {
            "count": len(citations),
            "mean_citations": statistics.mean(citations),
            "median_citations": statistics.median(citations),
            "stdev_citations": statistics.stdev(citations) if len(citations) > 1 else 0,
            "mean_influential": statistics.mean(influential),
            "median_influential": statistics.median(influential),
            "total_citations": sum(citations),
            "heavy_hitters": heavy_hitters_in_group,
            "heavy_hitter_probability": heavy_hitter_probability,
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


def print_analysis(papers: List[Dict], stats_by_score: Dict, year_stats: Dict, min_citations: int = 0, total_papers: int = None, max_collab_score: int = 3, heavy_hitter_pct: float = 10.0):
    """Print comprehensive analysis results.
    
    Args:
        papers: List of paper dictionaries
        stats_by_score: Statistics grouped by collaboration score
        year_stats: Statistics grouped by year
        min_citations: Minimum citation threshold used
        total_papers: Total number of papers loaded
        max_collab_score: Maximum collaboration score for binning
        heavy_hitter_pct: Percentage threshold for heavy hitters
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


def create_bar_chart(stats_by_score: Dict, graph_file: str, max_collab_score: int = 3, 
                     metaarea_filters: List[str] = None, area_filters: List[str] = None, 
                     conference_filters: List[str] = None, author_filters: List[str] = None, 
                     max_y_val: float = None, heavy_hitter_pct: float = 10.0):
    """Create a bar chart visualization of the analysis.
    
    Args:
        stats_by_score: Statistics grouped by collaboration score
        graph_file: Output file path for the graph
        max_collab_score: Maximum collaboration score (for labeling)
        metaarea_filters: Metaarea filters applied
        area_filters: Area filters applied
        conference_filters: Conference filters applied
        author_filters: Author filters applied
        max_y_val: Maximum y-axis value (None for auto-scale)
        heavy_hitter_pct: Percentage threshold for heavy hitters
    """
    print(f"\nCreating bar chart visualization...")

    # Prepare data
    scores = sorted(stats_by_score.keys())

    # Separate citation metrics from heavy hitter probability
    citation_metrics = {
        'Mean\ncitations': [stats_by_score[s]['mean_citations'] for s in scores],
        'Median\ncitations': [stats_by_score[s]['median_citations'] for s in scores],
        'Mean\ninfluential\ncitations': [stats_by_score[s]['mean_influential'] for s in scores],
    }

    hh_metric = {
        f'Heavy hitter\n(top {heavy_hitter_pct:.0f}%)\nprobability': [stats_by_score[s]['heavy_hitter_probability'] for s in scores],
    }

    # Combine all metrics for x-axis positioning
    all_metrics = list(citation_metrics.keys()) + list(hh_metric.keys())
    n_citation_metrics = len(citation_metrics)

    # Paper counts for legend
    paper_counts = {s: stats_by_score[s]['count'] for s in scores}

    # Set up the plot with narrower width
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Create secondary y-axis
    ax2 = ax1.twinx()

    # Number of metrics and scores
    n_metrics = len(all_metrics)
    n_scores = len(scores)

    # Width of each bar and spacing (wider bars, reduced separator)
    bar_width = 0.22
    group_spacing = 0.08
    separator_spacing = 0.15  # Reduced space before heavy hitter group
    group_width = n_scores * bar_width + group_spacing

    # X positions for each metric group (with extra space before heavy hitter)
    x_positions = np.zeros(n_metrics)
    for i in range(n_metrics):
        if i < n_citation_metrics:
            x_positions[i] = i * group_width
        else:
            # Add extra spacing before heavy hitter group
            x_positions[i] = i * group_width + separator_spacing

    # Colors for each score
    colors = plt.cm.viridis(np.linspace(0.2, 0.9, n_scores))

    # Calculate total papers for percentage
    total_papers = sum(paper_counts.values())

    # Plot bars for citation metrics (on primary y-axis)
    for i, score in enumerate(scores):
        # Get citation values for this score
        citation_values = [citation_metrics[metric][i] for metric in citation_metrics.keys()]

        # X positions for citation bars
        x_citation = x_positions[:n_citation_metrics] + i * bar_width

        # Label with score, paper count, and percentage
        score_label = f"{score}+" if score == max_collab_score else str(score)
        percentage = (paper_counts[score] / total_papers) * 100
        label = f"{score_label} (n={paper_counts[score]}, {percentage:.0f}%)"

        bars = ax1.bar(x_citation, citation_values, bar_width, label=label, color=colors[i])

        # Determine if this bar color is light (for text color selection)
        # Calculate luminance of the bar color
        bar_color = colors[i]
        r, g, b = bar_color[0], bar_color[1], bar_color[2]
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        is_light_color = luminance > 0.6  # Threshold for light colors

        # Add data labels on citation bars
        for bar_idx, bar in enumerate(bars):
            height = bar.get_height()
            # If max_y_val is set, check if label would be too close to top
            if max_y_val is not None:
                # Calculate approximate label height (as fraction of y-axis range)
                # Assuming fontsize 20 is roughly 3% of the plot height
                label_height_estimate = max_y_val * 0.04

                # If bar height + label would exceed or be very close to max_y_val
                if height + label_height_estimate >= max_y_val * 0.98:
                    # Place label inside the bar, with more distance from top (8% margin)
                    label_y = height - (max_y_val * 0.08)
                    va = 'top'
                    # Use black text for light bars, white for dark bars
                    color = 'black' if is_light_color else 'white'
                else:
                    # Normal case: place label above bar
                    label_y = height
                    va = 'bottom'
                    color = 'black'
            else:
                # No max_y_val set: normal placement
                label_y = height
                va = 'bottom'
                color = 'black'

            # Use integer format for median citations (index 1), decimal for others
            if bar_idx == 1:  # Median citations
                label_text = f'{int(height)}'
            else:
                label_text = f'{height:.1f}'

            ax1.text(bar.get_x() + bar.get_width()/2., label_y,
                   label_text,
                   ha='center', va=va, fontsize=16, color=color, 
                   fontfamily='sans-serif', stretch='condensed')

    # Plot bars for heavy hitter probability (on secondary y-axis)
    for i, score in enumerate(scores):
        # Get heavy hitter probability for this score
        hh_values = [hh_metric[metric][i] for metric in hh_metric.keys()]

        # X positions for heavy hitter bars
        x_hh = x_positions[n_citation_metrics:] + i * bar_width

        bars_hh = ax2.bar(x_hh, hh_values, bar_width, color=colors[i])

        # Add data labels on heavy hitter bars
        for bar in bars_hh:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom', fontsize=16, color='black',
                   fontfamily='sans-serif', stretch='condensed')

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
        # Use friendly names for metaareas
        friendly_names = [METAAREA_NAMES.get(m, m) for m in metaarea_filters]
        venue_desc = ", ".join(friendly_names) + " papers"
    else:
        venue_desc = "All papers"

    # Add author filter to title if specified
    if author_filters:
        author_desc = ", ".join(author_filters)
        filter_desc = f"{venue_desc} by {author_desc}"
    else:
        filter_desc = venue_desc

    # Add vertical separator line between citation metrics and heavy hitter
    # Position it exactly in the middle between the rightmost citation bar and leftmost heavy hitter bar
    # NOTE: matplotlib bar() positions bars with x as the CENTER, not left edge

    # The rightmost citation bar: last metric group, last score
    # Its center is at: x_positions[n_citation_metrics - 1] + (n_scores - 1) * bar_width
    # Its right edge is at: center + bar_width / 2
    last_citation_bar_center = x_positions[n_citation_metrics - 1] + (n_scores - 1) * bar_width
    last_citation_bar_right = last_citation_bar_center + bar_width / 2

    # The leftmost heavy hitter bar: first heavy hitter metric, first score (i=0)
    # Its center is at: x_positions[n_citation_metrics] + 0 * bar_width
    # Its left edge is at: center - bar_width / 2
    first_hh_bar_center = x_positions[n_citation_metrics]
    first_hh_bar_left = first_hh_bar_center - bar_width / 2

    # Place line exactly in the middle of the gap
    separator_x = (last_citation_bar_right + first_hh_bar_left) / 2

    # Customize the plot with adjusted font sizes
    ax1.set_ylabel('Citation count', fontsize=18, fontweight='bold')
    ax2.set_ylabel('Probability (%)', fontsize=18, fontweight='bold')
    ax1.set_title(filter_desc, fontsize=20, fontweight='bold')
    ax1.set_xticks(x_positions + (n_scores - 1) * bar_width / 2)
    ax1.set_xticklabels(all_metrics, rotation=0, ha='center', fontsize=16)
    ax1.tick_params(axis='y', labelsize=18)
    ax2.tick_params(axis='y', labelsize=18)

    # Draw the separator line AFTER setting xticks to avoid coordinate system changes
    ax1.axvline(x=separator_x, color='lightgray', linestyle='--', linewidth=1.5, alpha=0.6)
    # Position legend to the left of the separator line
    # Convert separator_x from data coordinates to axes coordinates
    xlim = ax1.get_xlim()
    legend_x = (separator_x - xlim[0]) / (xlim[1] - xlim[0]) - 0.01  # Very close to the left
    ax1.legend(title='Num areas', loc='upper right', bbox_to_anchor=(legend_x, 1.0), 
               frameon=False, fontsize=16, title_fontsize=16)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')

    # Set y-axis maximum if specified
    if max_y_val is not None:
        ax1.set_ylim(top=max_y_val)

    # Set secondary y-axis maximum to 25
    ax2.set_ylim(top=25)

    # Reduce margins on left and right
    ax1.margins(x=0.02)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

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
    papers, total_papers = load_data(args.citations, args.papers_file, args.min_citations, args.collaboration_level, args.metaareas, args.areas, args.conference_filters, args.author_filters, args.max_collaboration_score)
    
    if not papers:
        print("No papers with citation data found.")
        sys.exit(1)
    
    # Analyze
    stats_by_score = analyze_by_score(papers, args.heavy_hitter)
    year_stats = analyze_by_year(papers)
    
    # Print analysis
    print_analysis(papers, stats_by_score, year_stats, args.min_citations, total_papers, args.max_collaboration_score, args.heavy_hitter)
    
    # Create bar chart visualization only if --graph is specified
    if args.graph:
        create_bar_chart(stats_by_score, args.graph, args.max_collaboration_score, 
                         args.metaareas, args.areas, args.conference_filters, args.author_filters, args.max_y_val, args.heavy_hitter)
    
    # Write detailed output if requested
    if args.output:
        write_detailed_output(papers, args.output)
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
