# Collaboration and citations in computer science

*Ratul Mahajan*
<p style="text-align: center;">November, 2025</p>

In research circles, collaboration is assumed to be an unadulterated good, the more the better. Processes and [entire buildings](https://www.scientificamerican.com/blog/observations/a-revolution-in-the-creation-of-scientific-workplaces/) are designed with the explicit purpose of encouraging collaboration, especially interdisciplinary and inter-area collaboration. As much as I love to work with other smart people, given the coordination overhead and communication frustrations that accompany collaboration, I do wonder sometimes if it is worth it: Can its value be objectively shown? So, over the last weekend, I decided to crunch some numbers for fun. I've wanted to do this for a long time, and since modern coding agents make it so easy to do these things, I ran out of excuses.

## Methodology

I wanted to study the relationship between collaboration, especially across different areas of study within computer science, and the quality of the resulting research. But good research is notoriously difficult to define, especially at scale. While a researcher may be able to classify a paper as good (or bad) after careful consideration, it is hard for them to do so for thousands of papers that are published each year and it is even harder for any large group of researchers to agree on the classification. Thus, despite its limitations, I use citation count as a proxy measure of quality, with the expectation that good research tends to be cited more. 

<!-- To differentiate between raw citations, which include passing references to prior work,  and meaningful citations, I will also consider [influential citations](https://www.semanticscholar.org/faq/influential-citations) from [Semantic Scholar](https://www.semanticscholar.org/faq/influential-citations), which "identifies citations where the cited publication has a significant impact on the citing publication." -->

I crunched the numbers as follows. I started with 239,877 papers in [DBLP](https://dblp.org/), a CS-focused bibliography, that were published in the 20 year period from 2000-2020. I skipped papers published in the last 5 years to account for the [delayed citation effect](https://arxiv.org/pdf/2207.04244) for interdisciplinary research. To allow me to map a paper to its area and map its authors to their areas, I kept the papers that were published in a venue recognized by [CSRankings](https://csrankings.org/) *and* had an author recognized by CSRankings; see [CSRankings FAQ](https://csrankings.org/faq.html) for its criteria. This filtering kept 140,166 (58%) of the papers. I then pulled citation counts from [Semantic Scholar](https://www.semanticscholar.org/faq/influential-citations), using papers' DOI (digital object identifier) or title+year. I found citation information for 138,141 papers (98%); I ignore the other papers. 

<!-- I also got counts of [influential citations](https://www.semanticscholar.org/faq/influential-citations) from Semantic Scholar, which "identifies citations where the cited publication has a significant impact on the citing publication." -->

## Results

The graph below plots the median number of citations and "heavy hitter" probability as a function of the number of authors. I used median because citation counts are [heavily skewed](https://arxiv.org/pdf/1607.04125). Heavy hitter probability is the fraction papers in the top 10% that have a given number of authors. It helps answers the question: Are collaborative papers (with more authors) more likely to be heavily cited? (Because not all citations are equivalent, I tried to using Semantic Scholar's [influential citations](https://www.semanticscholar.org/faq/influential-citations) which is intended to "identify citations where the cited publication has a significant impact on the citing publication," but I found this measure to be too noisy, as [previously reported](https://www.mdpi.com/2304-6775/11/1/5?utm_source=chatgpt.com).)

![Citations as a function of the number of authors](graphs/all-authors.png)

The graph shows a clear relationship between the number of authors and citations. Starting from a base of 25 citations, each additional collaborator adds about 4 more citations. 

I did not expect the slope to be too low.

I binned papers into 3 groups based on the primary areas of its authors. Areas are fields of study like computer vision, computer networks, and algorithms; CSRankings identifies 27 distinct areas. The primary area of an author is based on the venue in which they've published the most papers. In the first group, all authors belong to the same area. The second group has authors from two areas, and the third group has 3 or more areas. This binning ignores the areas of authors not in the CSRankings database, which implies ignoring non-faculty authors and non-CS faculty.

If collaboration leads to better research and consequently more citations, then 1-area papers must get fewer citations than 2-area papers, and 3+-area papers must get the most citations. I analyzed this relationship using four measures: mean citation counts, median citation counts, mean influential citation counts, and "heavy hitter" probability. 


## Results

Lets begin by studying all papers in the pool. See the graph below.

![All areas collaboration and citation analysis](graphs/all.png)

Surprisingly, there appears to be negligible correlation between cross-area collaboration and citation metrics. There is some improvement with 3+ areas, but that is a small fraction of papers and the improvement is XXX.


## Analysis by Meta-Area

<div class="grid-container" markdown="1">

![AI area collaboration and citation analysis](graphs/ai.png)

![Systems area collaboration and citation analysis](graphs/systems.png)

![Theory area collaboration and citation analysis](graphs/theory.png)

![Interdisciplinary area collaboration and citation analysis](graphs/interdisciplinary.png)

</div>

## Analysis by Specific Area

### Networks and Communications

![Networks area collaboration and citation analysis](graphs/networks.png)

> **[Commentary]**: Discuss networking research specifically. What collaboration patterns emerge in this area?

### Software Engineering

![Software Engineering area collaboration and citation analysis](graphs/se.png)

> **[Commentary]**: Examine software engineering research. How does the applied nature of SE affect collaboration and citation patterns?

## Conclusions

> **[Conclusions]**: Summarize key findings across all areas. What are the main takeaways about collaboration's impact on citations? Are there actionable insights for researchers?

## Acknowledgements

This analysis would not have been possible without the great work of folks behind CSRankings and Semantic Scholar. 

## Appendix

All the scripts that generated the plots above are on [GitHub](https://github.com/ratulm/CollaborationCitation). If you want to play with the data, start with the README file there.

*A word to the wise:* In addition to curiosity, I did this analysis so I could play (more) with coding agents. I used Amazon Kiro wtih Claude Sonnet 4.5. I set out two constraints for myself at the start: (1) Do not directly edit the code, no matter how small a change I wanted to make—instead use the chat interface to specify what I want, and (2) Do not even read the code—instead judge correctness and infer behavior by inspecting the code's output (data, graphs) and asking questons via the chat interface. I succeeded with the first goal completely, but only partially with the second. There were a few times when data inspection and chat interface were not sufficient or felt too onerous. 

Why am I telling you this? So you don't judge me by the quality of the code.

