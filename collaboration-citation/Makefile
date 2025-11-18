# Makefile for collaboration-citation analysis

# Year range for filtering papers and citations
FROM_YEAR ?= 2000
TO_YEAR ?= 2025

# Input file
DBLP_FILE = ../dblp.xml.gz

# Output files
CITATIONS_CSV = citations.csv
PAPERS_CSV = papers.csv
GRAPH_DIR = graphs

# Optional suffix for graph filenames (can be set from command line)
GRAPH_SUFFIX ?=

ALL_GRAPH = $(GRAPH_DIR)/all$(GRAPH_SUFFIX).png
SYSTEMS_GRAPH = $(GRAPH_DIR)/systems$(GRAPH_SUFFIX).png
AI_GRAPH = $(GRAPH_DIR)/ai$(GRAPH_SUFFIX).png
THEORY_GRAPH = $(GRAPH_DIR)/theory$(GRAPH_SUFFIX).png
INTERDISCIPLINARY_GRAPH = $(GRAPH_DIR)/interdisciplinary$(GRAPH_SUFFIX).png
NETWORKS_GRAPH = $(GRAPH_DIR)/networks$(GRAPH_SUFFIX).png
SE_GRAPH = $(GRAPH_DIR)/se$(GRAPH_SUFFIX).png
ALL_AUTHORS_GRAPH = $(GRAPH_DIR)/all-authors$(GRAPH_SUFFIX).png
ANALYSIS_HTML = analysis.html
ANALYSIS_MD = analysis.md

# Python scripts
FETCH_CITATIONS = fetch_citations.py
FILTER_ANNOTATE_PAPERS = filter_annotate_papers.py
ANALYZE_COLLABORATION = analyze_collaboration_citations.py
ANALYZE_AUTHOR_COUNT = analyze_author_count_citations.py
MD_TO_HTML = md_to_html.py

# Default target
all: $(CITATIONS_CSV) $(PAPERS_CSV)

# Generate all graphs
all-graphs: $(ALL_GRAPH) $(SYSTEMS_GRAPH) $(AI_GRAPH) $(THEORY_GRAPH) $(INTERDISCIPLINARY_GRAPH) $(NETWORKS_GRAPH) $(SE_GRAPH)

# Generate citations.csv using fetch_citations.py, papers.csv, and dblp.xml.gz
# Run from parent directory so csrankings.py can find sigcse-research-articles.csv
# If citations.csv exists, resume from it and write to citations2.csv, then move
$(CITATIONS_CSV): $(FETCH_CITATIONS) $(PAPERS_CSV) $(DBLP_FILE)
	@if [ -f $(CITATIONS_CSV) ]; then \
		echo "Resuming from existing $(CITATIONS_CSV)..."; \
		cd .. && python collaboration-citation/$(FETCH_CITATIONS) \
			--input dblp.xml.gz \
			--papers collaboration-citation/$(PAPERS_CSV) \
			--output collaboration-citation/citations2.csv \
			--search-no-doi \
			--search-notfound-doi \
			--resume-from collaboration-citation/$(CITATIONS_CSV) \
			--from-year $(FROM_YEAR) \
			--to-year $(TO_YEAR); \
		mv collaboration-citation/citations2.csv collaboration-citation/$(CITATIONS_CSV); \
	else \
		echo "Creating new $(CITATIONS_CSV)..."; \
		cd .. && python collaboration-citation/$(FETCH_CITATIONS) \
			--input dblp.xml.gz \
			--papers collaboration-citation/$(PAPERS_CSV) \
			--output collaboration-citation/$(CITATIONS_CSV) \
			--search-no-doi \
			--search-notfound-doi \
			--from-year $(FROM_YEAR) \
			--to-year $(TO_YEAR); \
	fi

# Generate papers.csv using filter_annotate_papers.py and dblp.xml.gz
# Run from parent directory so csrankings.py can find sigcse-research-articles.csv
$(PAPERS_CSV): $(FILTER_ANNOTATE_PAPERS) $(DBLP_FILE)
	cd .. && python collaboration-citation/$(FILTER_ANNOTATE_PAPERS) \
		--dblp dblp.xml.gz \
		--output collaboration-citation/$(PAPERS_CSV) \
		--from-year $(FROM_YEAR) \
		--to-year $(TO_YEAR)

# Generate all.png using analyze_collaboration_citations.py
$(ALL_GRAPH): $(ANALYZE_COLLABORATION) $(CITATIONS_CSV) $(PAPERS_CSV) | $(GRAPH_DIR)
	python $(ANALYZE_COLLABORATION) \
		--citations $(CITATIONS_CSV) \
		--papers $(PAPERS_CSV) \
		--graph $(ALL_GRAPH) \
		--max-y-val 100 \
		--from-year $(FROM_YEAR) \
		--to-year $(TO_YEAR)

# Generate metaarea graphs (systems, ai, theory, interdisciplinary)
$(GRAPH_DIR)/%$(GRAPH_SUFFIX).png: $(ANALYZE_COLLABORATION) $(CITATIONS_CSV) $(PAPERS_CSV) | $(GRAPH_DIR)
	@metaarea=$$(echo $* | sed 's/$(GRAPH_SUFFIX)$$//'); \
	if echo "systems ai theory interdisciplinary" | grep -qw "$$metaarea"; then \
		python $(ANALYZE_COLLABORATION) \
			--citations $(CITATIONS_CSV) \
			--papers $(PAPERS_CSV) \
			--graph $@ \
			--only-metaareas $$metaarea \
			--max-y-val 100 \
			--from-year $(FROM_YEAR) \
			--to-year $(TO_YEAR); \
	fi

# Generate area-specific graphs (networks for comm, se for soft)
$(NETWORKS_GRAPH) $(SE_GRAPH): $(ANALYZE_COLLABORATION) $(CITATIONS_CSV) $(PAPERS_CSV) | $(GRAPH_DIR)
	@if [ "$@" = "$(NETWORKS_GRAPH)" ]; then \
		area=comm; \
		extra_args=""; \
	elif [ "$@" = "$(SE_GRAPH)" ]; then \
		area=soft; \
		extra_args="--collaboration-level area"; \
	fi; \
	python $(ANALYZE_COLLABORATION) \
		--citations $(CITATIONS_CSV) \
		--papers $(PAPERS_CSV) \
		--graph $@ \
		--only-areas $$area \
		--max-y-val 100 \
		$$extra_args \
		--from-year $(FROM_YEAR) \
		--to-year $(TO_YEAR)

# Generate all-authors.png using analyze_author_count_citations.py
$(ALL_AUTHORS_GRAPH): $(ANALYZE_AUTHOR_COUNT) $(CITATIONS_CSV) $(PAPERS_CSV) | $(GRAPH_DIR)
	python $(ANALYZE_AUTHOR_COUNT) \
		--citations $(CITATIONS_CSV) \
		--papers $(PAPERS_CSV) \
		--from-year 2000 \
		--to-year 2020 \
		--max-authors 7 \
		--graph $(ALL_AUTHORS_GRAPH) \
		--max-y2-val 15 \
		--max-y1-val 75 \
		--y1-tick-freq 25 \
		--y2-tick-freq 5

# Create graphs directory
$(GRAPH_DIR):
	mkdir -p $(GRAPH_DIR)

# Clean generated files
clean:
	rm -f $(CITATIONS_CSV) $(PAPERS_CSV)
	rm -rf $(GRAPH_DIR)

# Generate analysis.html from analysis.md
$(ANALYSIS_HTML): $(ANALYSIS_MD) $(MD_TO_HTML)
	python $(MD_TO_HTML) $(ANALYSIS_MD) $(ANALYSIS_HTML)

# Convenience target for generating the analysis HTML
analysis: all-graphs $(ANALYSIS_HTML)

# Phony targets
.PHONY: all clean all-graphs analysis

# Prevent Make from deleting these files on interrupt or error
.PRECIOUS: $(CITATIONS_CSV) $(PAPERS_CSV)
