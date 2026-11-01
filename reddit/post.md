## Title

[OC] The Nobel brain drain: 34% of Nobel prizes won in the US went to people born abroad, and the US gained 131 more laureates than it grew. Only 5 countries come out ahead

## Body

I drew a line from birthplace to prize for every Nobel laureate in physics, chemistry, medicine and economics, 1901 to 2026 (760 prizes), using the Nobel Prize's own API for birthplaces and affiliations at the award and Wikidata for coordinates. 31% went to someone working outside their birth country. The US hosted 402 prizes but grew only 271 laureates (+131); after it, the biggest net gain is Switzerland's +9. Germany took 31% of prizes up to 1932 and 6.5% since 1933. Japan went from 5 science laureates in the 20th century to 22 since 2000, and unlike most countries it keeps them. Caveats: affiliation at the award is not always where the winning work was done, birth country is not nationality, and Poland's big "loss" is mostly Germans born in places that are Polish today. Interactive flow map with prize, decade and sex filters: https://maps.tristanhotham.com/nobel-brain-drain/

## Source comment

Source: Nobel Prize API v2.1 (Nobel Prize Outreach), 2026: every prize to a person, with birthplace and affiliations at the award; Wikidata (CC0) via QLever for birthplace and institution coordinates, matched by Wikidata ID with prize and year checked; Natural Earth. Present-day countries. Peace and Literature have no affiliations and are left out of the flows. Map labels were placed by a script that checks each one sits on plain sea and covers no line or dot.

Tools: Python (shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/nobel-brain-drain/
Paper: https://doi.org/10.5281/zenodo.23857487
Blog post: https://blog.tristanhotham.com/2026/10/31/nobel-brain-drain/
