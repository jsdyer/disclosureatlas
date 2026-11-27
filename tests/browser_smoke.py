"""Walk the published static edition at its project prefix, including phone and no-JS."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / 'dist', Path(temporary) / 'disclosureatlas')
        server = ThreadingHTTPServer(('127.0.0.1',0), partial(QuietHandler,directory=temporary))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        url = f'http://127.0.0.1:{server.server_port}/disclosureatlas/'
        try:
            with sync_playwright() as pw:
                options = {"executable_path": os.environ["CHROMIUM_PATH"]} if os.getenv("CHROMIUM_PATH") else {}
                browser = pw.chromium.launch(**options)
                page = browser.new_page(viewport={"width":1280,"height":900})
                errors = []
                page.on("pageerror",lambda err: errors.append(str(err)))
                page.goto(url)
                assert page.get_by_role("heading", level=1).is_visible()
                assert page.get_by_role("link", name="Follow the Arar inquiry").is_visible()
                page.get_by_role("searchbox").fill("time served")
                assert page.locator("[data-case]:visible").count() == 1
                page.get_by_role("link", name="WikiLeaks and the Assange plea").click()
                assert "62 months" in page.inner_text("main")
                page.get_by_role("link", name="The Pentagon Papers", exact=True).click()
                assert "2,384" in page.inner_text("main")
                page.goto(url+"records/#q=NATO&place=Canada")
                assert page.locator("[data-case]:visible").count() == 1
                page.get_by_label("Region",exact=True).select_option("United States")
                assert "No matching" in page.locator("[data-status]").inner_text()
                page.get_by_role("button",name="Clear filters").click()
                total = page.locator("[data-case]").count()
                assert page.locator("[data-case]:visible").count() == total
                page.goto(url)
                page.screenshot(path=str(screenshots/'desktop.png'))
                page.set_viewport_size({"width":390,"height":844})
                cta = page.get_by_role("link",name="Follow the Arar inquiry")
                bounds = cta.bounding_box()
                assert bounds["y"] + bounds["height"] < 844
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.screenshot(path=str(screenshots/'mobile.png'))
                cta.click()
                assert "/records/arar-inquiry/" in page.url
                page.get_by_role("link",name="Findings and outcome").click()
                assert "CAD $10.5 million" in page.locator("#findings").inner_text()
                page.set_viewport_size({"width":320,"height":740})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                assert not errors, errors
                nojs = browser.new_context(java_script_enabled=False)
                native = nojs.new_page()
                native.goto(url)
                native.get_by_role("link",name="The Panama Papers",exact=True).click()
                assert native.get_by_role("link",name="Explore the Offshore Records Atlas").get_attribute("href") == "https://coolcode.ca/offshorerecords/"
                native.get_by_role("link",name="Source documents",exact=True).click()
                assert native.locator("#src-recommendation a").get_attribute("href").startswith("https://eur-lex.europa.eu/")
                native.get_by_role("link",name="Sources",exact=True).click()
                assert native.get_by_role("link",name="Download the casefiles and citations as JSON").is_visible()
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
    print("Browser checks passed for search, filters, source links, no-JS pages and mobile first use")


if __name__ == "__main__":
    main()
