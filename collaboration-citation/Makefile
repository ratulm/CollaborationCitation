# Makefile for collaboration-citation analysis

# Input file
DBLP_FILE = ../dblp.xml.gz

# Output files
CITATIONS_CSV = citations.csv
PAPERS_CSV = papers.csv
GRAPH_DIR = graphs
OVERALL_GRAPH = $(GRAPH_DIR)/overall.png
SYSTEMS_GRAPH = $(GRAPH_DIR)/systems.png
AI_GRAPH = $(GRAPH_DIR)/ai.png
THEORY_GRAPH = $(GRAPH_DIR)/theory.png
INTERDISCIPLINARY_GRAPH = $(GRAPH_DIR)/interdisciplinary.png
NETWORKS_GRAPH = $(GRAPH_DIR)/networks.png
SE_GRAPH = $(GRAPH_DIR)/se.png

# Python scripts
FETCH_CITATIONS = fetch_citations.py
FILTER_ANNOTATE_PAPERS = filter_annotate_papers.py
ANALYZE_COLLABORATION = analyze_collaboration_citations.py

# Default target
all: $(CITATIONS_CSV) $(PAPERS_CSV)

# Generate all graphs
all-graphs: $(OVERALL_GRAPH) $(SYSTEMS_GRAPH) $(AI_GRAPH) $(THEORY_GRAPH) $(INTERDISCIPLINARY_GRAPH) $(NETWORKS_GRAPH) $(SE_GRAPH)

# Generate citations.csv using fetch_citations.py, papers.csv, and dblp.xml.gz
# Run from parent directory so csrankings.py can find sigcse-research-articles.csv
# If citations.csv exists, resume from it and write to citations2.csv, then move
$(CITATIONS_CSV): $(FETCH_CITATIONS) $(PAPERS_CSV) $(DBLP_FILE)
	@if [ -f $(CITATIONS_CSV) ]; then \
		echo "Resuming from existing $(CITATIONS_CSV)..."; \
		cd .. && python collaboration-citation/$(FETCH_CITATIONS) --input dblp.xml.gz --papers collaboration-citation/$(PAPERS_CSV) --output collaboration-citation/citations2.csv --search-no-doi --search-notfound-doi --resume-from collaboration-citation/$(CITATIONS_CSV); \
		mv collaboration-citation/citations2.csv collaboration-citation/$(CITATIONS_CSV); \
	else \
		echo "Creating new $(CITATIONS_CSV)..."; \
		cd .. && python collaboration-citation/$(FETCH_CITATIONS) --input dblp.xml.gz --papers collaboration-citation/$(PAPERS_CSV) --output collaboration-citation/$(CITATIONS_CSV) --search-no-doi --search-notfound-doi; \
	fi

# Generate papers.csv using filter_annotate_papers.py and dblp.xml.gz
# Run from parent directory so csrankings.py can find sigcse-research-articles.csv
$(PAPERS_CSV): $(FILTER_ANNOTATE_PAPERS) $(DBLP_FILE)
	cd .. && python collaboration-citation/$(FILTER_ANNOTATE_PAPERS) --dblp dblp.xml.gz --output collaboration-citation/$(PAPERS_CSV)

# Generate overall.png using analyze_collaboration_citations.py
$(OVERALL_GRAPH): $(ANALYZE_COLLABORATION) $(CITATIONS_CSV) $(PAPERS_CSV) | $(GRAPH_DIR)
	python $(ANALYZE_COLLABORATION) --citations $(CITATIONS_CSV) --papers $(PAPERS_CSV) --graph $(OVERALL_GRAPH) --max-y-val 100

# Generate systems.png for systems metaarea
$(SYSTEMS_GRAPH): $(ANALYZE_COLLABORATION) $(CITATIONS_CSV) $(PAPERS_CSV) | $(GRAPH_DIR)
	python $(ANALYZE_COLLABORATION) --citations $(CITATIONS_CSV) --papers $(PAPERS_CSV) --graph $(SYSTEMS_GRAPH) --only-metaareas systems --max-y-val 100

# Generate ai.png for ai metaarea
$(AI_GRAPH): $(ANALYZE_COLLABORATION) $(CITATIONS_CSV) $(PAPERS_CSV) | $(GRAPH_DIR)
	python $(ANALYZE_COLLABORATION) --citations $(CITATIONS_CSV) --papers $(PAPERS_CSV) --graph $(AI_GRAPH) --only-metaareas ai --max-y-val 100

# Generate theory.png for theory metaarea
$(THEORY_GRAPH): $(ANALYZE_COLLABORATION) $(CITATIONS_CSV) $(PAPERS_CSV) | $(GRAPH_DIR)
	python $(ANALYZE_COLLABORATION) --citations $(CITATIONS_CSV) --papers $(PAPERS_CSV) --graph $(THEORY_GRAPH) --only-metaareas theory --max-y-val 100

# Generate interdisciplinary.png for interdisciplinary metaarea
$(INTERDISCIPLINARY_GRAPH): $(ANALYZE_COLLABORATION) $(CITATIONS_CSV) $(PAPERS_CSV) | $(GRAPH_DIR)
	python $(ANALYZE_COLLABORATION) --citations $(CITATIONS_CSV) --papers $(PAPERS_CSV) --graph $(INTERDISCIPLINARY_GRAPH) --only-metaareas interdisciplinary --max-y-val 100

# Generate networks.png for comm area
$(NETWORKS_GRAPH): $(ANALYZE_COLLABORATION) $(CITATIONS_CSV) $(PAPERS_CSV) | $(GRAPH_DIR)
	python $(ANALYZE_COLLABORATION) --citations $(CITATIONS_CSV) --papers $(PAPERS_CSV) --graph $(NETWORKS_GRAPH) --only-areas comm --max-y-val 100

# Generate se.png for soft (software engineering) area
$(SE_GRAPH): $(ANALYZE_COLLABORATION) $(CITATIONS_CSV) $(PAPERS_CSV) | $(GRAPH_DIR)
	python $(ANALYZE_COLLABORATION) --citations $(CITATIONS_CSV) --papers $(PAPERS_CSV) --graph $(SE_GRAPH) --only-areas soft --max-y-val 100 --collaboration-level area

# Create graphs directory
$(GRAPH_DIR):
	mkdir -p $(GRAPH_DIR)

# Clean generated files
clean:
	rm -f $(CITATIONS_CSV) $(PAPERS_CSV)
	rm -rf $(GRAPH_DIR)

# Phony targets
.PHONY: all clean all-graphs

# Prevent Make from deleting these files on interrupt or error
.PRECIOUS: $(CITATIONS_CSV) $(PAPERS_CSV)
