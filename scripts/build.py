#!/usr/bin/env python3
"""Build the reviewed Disclosure Atlas edition without network access."""
from datetime import date
from html import escape
import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from search_metadata import add_search_metadata

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
INFORMATION = (("finding", "What the record establishes"), ("outcome", "What followed"), ("limits", "What remains open"))


def https(url):
    parts = urlsplit(url)
    return parts.scheme == "https" and parts.hostname and not parts.username and not parts.password


def validate(edition):
    date.fromisoformat(edition["reviewed"])
    cases = edition["cases"]
    ids = [case["slug"] for case in cases]
    if not cases or len(ids) != len(set(ids)) or any(not SLUG.fullmatch(key) or key == "sources" for key in ids):
        raise ValueError("Casefile slugs must be unique public paths")
    featured = edition["featured"]
    if featured["case"] not in ids or not featured["summary"].strip() or not featured["action"].strip():
        raise ValueError("The home page needs a featured casefile and action")
    for case in cases:
        if any(not case[key].strip() for key in ("title", "question", "region", "kind", "period", "summary")):
            raise ValueError("Each casefile needs an editorial introduction")
        sources = case["sources"]
        keys = [source["id"] for source in sources]
        if len(keys) < 2 or len(set(keys)) != len(keys) or not all(SLUG.fullmatch(key) for key in keys):
            raise ValueError("A case needs at least two distinct source references")
        for source in sources:
            if not https(source["url"]) or not all(source[key].strip() for key in ("title", "date", "publisher")):
                raise ValueError("Incomplete source citation")
        if not case["timeline"] or not all(event["date"] and event["title"] for event in case["timeline"]):
            raise ValueError("The timeline needs dated events")
        for entry in [*case["timeline"], *(case[key] for key, _ in INFORMATION)]:
            if entry["source"] not in keys or not entry["text"].strip():
                raise ValueError("Every statement needs a source from the casefile")
        if not case["related"] or any(key == case["slug"] or key not in ids for key in case["related"]):
            raise ValueError("Related casefile not found")
        link = case.get("connection")
        if link and (not https(link["url"]) or not link["title"] or not link["text"]):
            raise ValueError("Invalid related tool")


def anchor(url, title):
    return f'<a href="{escape(url)}">{escape(title)}</a>'


def citation(case, source_id):
    source = next(item for item in case["sources"] if item["id"] == source_id)
    return f'<a class="footref" href="#src-{source_id}">{escape(source["title"])}</a>'


def docs(case):
    items = []
    for source in case["sources"]:
        items.append(f'<li id="src-{source["id"]}">{anchor(source["url"], source["title"])}'
                     f'<small>{escape(source["publisher"])} · {escape(source["date"])}</small></li>')
    return '<ul class="docs">' + ''.join(items) + '</ul>'


def controls(cases):
    def options(key):
        return ''.join(f'<option>{escape(value)}</option>' for value in sorted({c[key] for c in cases}))
    return f'''<form class="controls" data-filter hidden role="search" aria-label="Find casefiles">
    <div class="field"><label for="query">Search casefiles</label><input id="query" name="query" type="search" placeholder="Try NATO or time served" autocomplete="off"></div>
    <div class="field"><label for="kind">Source type</label><select id="kind" name="kind"><option value="">All types</option>{options("kind")}</select></div>
    <div class="field"><label for="region">Region</label><select id="region" name="region"><option value="">All regions</option>{options("region")}</select></div>
    <button type="reset" hidden>Clear filters</button></form>'''


def listing(cases, prefix):
    cards = []
    for c in cases:
        text = " ".join([c["title"], c["question"], c["kind"], c["region"], c["period"], c["summary"],
                         *(s["publisher"] + " " + s["title"] for s in c["sources"]),
                         *(e["text"] for e in c["timeline"]), *(c[key]["text"] for key, _ in INFORMATION)])
        cards.append(f'''<article class="card" data-case data-search="{escape(text)}"
        data-kind="{escape(c["kind"])}" data-region="{escape(c["region"])}">
        <p class="meta">{escape(c["region"])} · {escape(c["period"])}</p>
        <h3>{anchor(prefix + c["slug"] + "/", c["title"])}</h3><p>{escape(c["question"])}</p></article>''')
    return controls(cases) + f'<p class="status" role="status" data-status>{len(cases)} casefiles</p><div class="cards">' + ''.join(cards) + '</div>'


def source_group(case):
    items = ''.join(f'<li>{anchor(s["url"], s["title"])}<small>{escape(s["publisher"])} · {escape(s["date"])}</small></li>'
                    for s in case["sources"])
    return f'<section class="section sources-group" id="{case["slug"]}"><h2>{anchor("../" + case["slug"] + "/", case["title"])}</h2><ul class="docs">{items}</ul></section>'


def case_body(c, by_id):
    events = "".join(f'<li><span class="meta">{escape(e["date"])}</span><h3>{escape(e["title"])}</h3>'
                     f'<p>{escape(e["text"])}</p>{citation(c, e["source"])}</li>' for e in c["timeline"])
    answer = "".join(f'<section class="answer"><h2>{heading}</h2><p>{escape(c[key]["text"])}</p>'
                     f'{citation(c, c[key]["source"])}</section>' for key, heading in INFORMATION)
    related = "".join(f'<li>{anchor("../" + slug + "/", by_id[slug]["title"])}</li>' for slug in c["related"])
    link = c.get("connection")
    connection = f'<p class="explainer">{escape(link["text"])} {anchor(link["url"], link["title"])}</p>' if link else ''
    return f'''<p class="crumb">{anchor("../", "← All casefiles")}</p>
    <article><div class="intro"><p class="eyebrow">{escape(c["kind"])} · {escape(c["region"])} · {escape(c["period"])}</p>
    <h1>{escape(c["title"])}</h1><p class="lede">{escape(c["summary"])}</p>
    <nav class="jumps" aria-label="In this casefile"><a href="#timeline">Timeline</a><a href="#findings">Findings and outcome</a><a href="#sources">Source documents</a></nav></div>
    <div class="bodygrid"><section id="timeline"><h2>Timeline</h2><ol class="timeline">{events}</ol></section><div class="outcomes" id="findings">{answer}</div></div>
    <section class="section" id="sources"><h2>Source documents</h2>{docs(c)}</section>
    <section class="section"><h2>Follow another record</h2><ul class="related">{related}</ul>{connection}</section></article>'''


def root_body(cases, selection):
    featured = next(c for c in cases if c["slug"] == selection["case"])
    return f'''<div class="hero"><div><h1>What happened after the disclosure?</h1>
    <p class="lede">Follow a case from the first public record to the court decision, apology or archive that came next.</p></div>
    <article class="feature"><p class="eyebrow">Featured case · {escape(featured["region"])}</p><h2>{escape(featured["title"])}</h2>
    <p>{escape(selection["summary"])}</p>
    <a class="button" href="records/{featured["slug"]}/">{escape(selection["action"])} <span aria-hidden="true">→</span></a></article></div>
    <section class="bar"><h2>Find a casefile</h2>{listing(cases, "records/")}</section>
    <nav class="links" aria-label="Browse the edition"><a href="records/">Casefile directory</a><a href="records/sources/">Browse source documents</a></nav>'''


def build(root=ROOT):
    edition = json.loads((root / "data/edition.json").read_text())
    tool = json.loads((root / "tool.json").read_text())
    validate(edition)
    cases = edition["cases"]
    by_id = {c["slug"]: c for c in cases}
    reviewed = edition["reviewed"]
    canonical = "https://coolcode.ca" + tool["url"]
    template = (root / "web/index.html").read_text()
    routes = []
    with tempfile.TemporaryDirectory(dir=root) as temporary:
        stage = Path(temporary) / "site"
        stage.mkdir()
        def page(path, title, description, body, schema="CollectionPage", citations=None):
            target = stage / path
            target.mkdir(exist_ok=True, parents=True)
            seo_title = title + " · Disclosure Atlas" if path else "Disclosure Atlas · Trace public disclosures and their outcomes"
            url = canonical + path
            metadata = ""
            if path:
                graph = {"@context":"https://schema.org","@type":schema,"url":url,"name":title,
                         "description":description,"dateModified":reviewed,"inLanguage":"en"}
                if citations:
                    graph.update(headline=title, citation=citations, author={"@type":"Organization","name":"CoolCode","url":"https://coolcode.ca/"})
                encoded = json.dumps(graph, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")
                metadata = f'<link rel="canonical" href="{escape(url)}"><meta property="og:url" content="{escape(url)}"><meta property="og:title" content="{escape(seo_title)}"><meta property="og:description" content="{escape(description)}"><meta property="og:type" content="{"article" if schema == "Article" else "website"}"><script type="application/ld+json">{encoded}</script>'
                routes.append(url)
            substitutions = {"TITLE":escape(seo_title), "DESCRIPTION":escape(description), "PREFIX":("../" * path.count("/") or "./"),
                             "REVIEWED":reviewed, "DISPLAY_DATE":date.fromisoformat(reviewed).strftime("%d %B %Y").lstrip("0"),
                             "META":metadata, "SOURCE":escape(tool["source"]), "CONTENT":body}
            markup = re.sub(r"\{\{([A-Z_]+)\}\}", lambda hit: substitutions[hit[1]], template)
            if not path:
                markup = add_search_metadata(markup, tool, category="ReferenceApplication")
            (target / "index.html").write_text(markup, encoding="utf-8")
        page("", tool["title"], tool["description"], root_body(cases, edition["featured"]))
        page("records/", "Public disclosure casefiles", "Browse sourced timelines of public disclosures, judicial decisions, official inquiries and archive releases.",
             '<div class="intro"><h1>Casefile directory</h1><p class="lede">Choose a question to read the timeline, findings and original documents.</p></div>' +
             listing(cases, "./") + '<div class="links"><a href="sources/">Browse the source index</a></div>')
        source_count = len({s["url"] for c in cases for s in c["sources"]})
        source_intro = f'<p class="crumb">{anchor("../", "← All casefiles")}</p><div class="intro"><h1>Source documents</h1><p class="lede">Open the {source_count} records cited in this edition, grouped by casefile. Dates identify the document, event or edition where available.</p><nav class="jumps" aria-label="Jump to a casefile">'
        source_menu = "".join(anchor("#" + c["slug"], c["title"]) for c in cases)
        page("records/sources/", "Source documents for disclosure casefiles", "Find the reports, primary documents, court records and original releases cited in the Disclosure Atlas.",
             source_intro + source_menu + '</nav></div>' + "".join(source_group(c) for c in cases) +
             '<p class="section" id="dataset"><a href="../../data/edition.json" download>Download the casefiles and citations as JSON</a></p>')
        for c in cases:
            page(f'records/{c["slug"]}/', c["title"], c["summary"], case_body(c, by_id), "Article", [s["url"] for s in c["sources"]])
        for name in ("style.css","app.mjs","model.mjs"):
            shutil.copyfile(root / "web" / name, stage / name)
        (stage / "data").mkdir()
        shutil.copyfile(root / "data/edition.json", stage / "data/edition.json")
        sitemap = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        for url in sorted(routes):
            row = ET.SubElement(sitemap, "url")
            ET.SubElement(row, "loc").text = url
            ET.SubElement(row, "lastmod").text = reviewed
        ET.ElementTree(sitemap).write(stage / "sitemap.xml", encoding="utf-8", xml_declaration=True)
        (stage / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {canonical}sitemap.xml\n")
        (stage / ".nojekyll").touch()
        output = root / "dist"
        if output.is_symlink():
            raise ValueError("dist must not be a symlink")
        if output.exists():
            shutil.rmtree(output)
        stage.rename(output)
    return len(routes)


if __name__ == "__main__":
    print(f"Built Disclosure Atlas with {build()} indexed result URLs")
