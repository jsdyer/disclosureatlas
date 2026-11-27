import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "scripts"))
from build import build, validate


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.canonical = []
        self.description = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        if tag == "a":
            self.links.append(a["href"])
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical.append(a["href"])
        if tag == "meta" and a.get("name") == "description":
            self.description.append(a["content"])


class EditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        for directory in ("web", "data"):
            shutil.copytree(ROOT / directory, cls.root / directory)
        shutil.copyfile(ROOT / "tool.json", cls.root / "tool.json")
        cls.edition = json.loads((cls.root / "data/edition.json").read_text())
        build(cls.root)
        cls.site = cls.root / "dist"

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_canonicals_descriptions_source_links_and_sitemap(self):
        base = "https://coolcode.ca/disclosureatlas/"
        sitemap = ET.parse(self.site / "sitemap.xml")
        locs = {element.text for element in sitemap.findall(".//{*}loc")}
        pages = {}
        for file in self.site.rglob("index.html"):
            path = str(file.relative_to(self.site)).removesuffix("index.html")
            page = Page()
            page.feed(file.read_text())
            url = base + path
            self.assertEqual(page.canonical, [url])
            self.assertEqual(len(page.description), 1)
            self.assertGreater(len(page.description[0]), 35)
            pages[url] = page
        self.assertEqual(locs, set(pages) - {base})
        self.assertIn(base+"records/", locs)
        self.assertEqual(len(locs), len(self.edition['cases']) + 2)
        for url, page in pages.items():
            for href in page.links:
                full = urljoin(url, href)
                parts = urlsplit(full)
                if not full.startswith(base):
                    continue
                address = full.split('#')[0]
                if address.endswith('/'):
                    self.assertIn(address, pages)
                    if parts.fragment:
                        self.assertIn(unquote(parts.fragment), pages[address].ids)
                else:
                    self.assertTrue((self.site / address.removeprefix(base)).is_file())
        for case in self.edition["cases"]:
            source_urls = {s["url"] for s in case["sources"]}
            url = base + "records/" + case["slug"] + "/"
            self.assertTrue(source_urls <= set(pages[url].links))
            self.assertTrue(source_urls <= set(pages[base+"records/sources/"].links))
        self.assertEqual(self.edition, json.loads((self.site / "data/edition.json").read_text()))

    def test_invalid_references_and_slug_are_rejected(self):
        for key, value in [("slug","../escape"), ("related",["missing"])]:
            data = copy.deepcopy(self.edition)
            data["cases"][0][key] = value
            with self.assertRaises(ValueError):
                validate(data)
        data = copy.deepcopy(self.edition)
        data["cases"][0]["outcome"]["source"] = "missing"
        with self.assertRaises(ValueError):
            validate(data)

    def test_expansion_is_discovered_without_new_routes_in_code(self):
        data = copy.deepcopy(self.edition)
        extra = copy.deepcopy(data['cases'][0])
        extra.update(slug="added-on-review", title="A newly reviewed record", region="Added region")
        data["cases"].append(extra)
        validate(data)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(self.root / "web", root / "web")
            (root / "data").mkdir()
            (root / "data/edition.json").write_text(json.dumps(data))
            shutil.copyfile(self.root / "tool.json", root / "tool.json")
            build(root)
            self.assertTrue((root / "dist/records/added-on-review/index.html").exists())
            self.assertIn("<option>Added region</option>", (root / "dist/index.html").read_text())
