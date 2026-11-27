# Disclosure Atlas

Follow public disclosures through original documents, dated findings and official outcomes. The first edition covers the Arar inquiry, Canadian NATO oral histories, the Brown & Williamson tobacco documents, the Panama Papers, the Pentagon Papers and the Assange plea.

[Open Disclosure Atlas](https://coolcode.ca/disclosureatlas/) · [Browse the casefiles](https://coolcode.ca/disclosureatlas/records/) · [Browse the original sources](https://coolcode.ca/disclosureatlas/records/sources/)

<!-- coolcode:guide -->
Start with the Arar inquiry to trace the commission’s findings to Canada’s apology. Each casefile links the timeline and its conclusions to specific public records. Search by topic or filter by source type and region.
<!-- /coolcode:guide -->

## Coverage and updates

The six starting cases illustrate how official inquiries, archival releases, investigative reporting, industry records and court proceedings enter the public record. Each timeline distinguishes event dates from publication and editorial review dates. Individual sources identify their authors or custodians. The Atlas links to source documents at their original hosts. Those hosts set their own access and reuse terms.

Editors revise the collection when they verify a new source, correction or outcome. The review date in the footer and edition records that editorial work. A new deployment alone does not move that date. The app does not monitor proceedings or check for new outcomes automatically.

## Using the Atlas

Choose a case on the home page or search the directory. Keywords match names, document titles, publishers, events and conclusions. The filters work together. Clear filters to restore the full list. A link copied after filtering restores the selection on another visit. Search terms stay in the browser's URL fragment. Following an external document opens its publisher's website.

Casefiles and the source index are static HTML and can be read without JavaScript. The selected casefile links to other cases with a related evidentiary question. The Panama Papers case leads to the Offshore Records Atlas. The NATO case links to the Canadian federal access-request explorer.

## Expand or customize

Edit `data/edition.json` to add a case, update an outcome or fix a citation. Give the case a stable lowercase slug, a question, region, source type, covered period and summary. Assign each source a short unique ID, original HTTPS URL, publisher and document date or an explicit date-availability note. Reference these IDs from every timeline event, finding, outcome and limit. Add related case slugs. Optional related-tool entries need a title, URL and reason to follow the link. Choose the home page example with the `featured` case slug, summary and action text. Update `reviewed` only after reviewing the evidence. Preserve stable casefile paths when revising titles or descriptions.

Build and test from the repository root using Python 3.12 and Node 24.

```sh
node --test tests/*.test.mjs
python -m unittest discover -s tests -v
python scripts/build.py
python -m pip install -r tests/browser-requirements.txt
python -m playwright install chromium
python tests/browser_smoke.py
python -m http.server 8010 --directory dist
```

An existing system Chromium can be supplied through `CHROMIUM_PATH`. The default build reads only the retained edition and emits the root, casefile directory, source index, individual canonical HTML pages, native sitemap and JSON download in `dist/`. No build dependencies are needed. The source repository uses the name disclosureatlas-. The CoolCode hub serves its reviewed build at the clean disclosureatlas path. Native CI checks pull requests and main pushes and keeps the resulting site artifact. The Pages deployment job also supports a future matching repository name and skips publication at the suffixed GitHub Pages path.

[Download the curated edition](https://coolcode.ca/disclosureatlas/data/edition.json) · [Native sitemap](https://coolcode.ca/disclosureatlas/sitemap.xml)
