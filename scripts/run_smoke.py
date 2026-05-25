import argparse
import mimetypes
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}


def build_route_handler(root: Path):
    root = root.resolve()

    def handle_route(route):
        parsed = urlparse(route.request.url)
        rel = unquote(parsed.path.lstrip("/")) or "index.html"
        path = (root / rel).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            route.fulfill(status=403, body="Forbidden")
            return

        if not path.exists() or not path.is_file():
            route.fulfill(status=404, body="Not found")
            return

        content_type = CONTENT_TYPES.get(
            path.suffix.lower(),
            mimetypes.guess_type(str(path))[0] or "application/octet-stream",
        )
        route.fulfill(status=200, body=path.read_bytes(), content_type=content_type)

    return handle_route


def run_smoke(root: Path, base_url: str, timeout_ms: int, headed: bool) -> int:
    smoke_url = base_url.rstrip("/") + "/smoke-test.html?autorun=1"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        context.route("**/*", build_route_handler(root))
        page = context.new_page()

        page.goto(smoke_url, wait_until="load")
        page.wait_for_function(
            "() => ['pass','fail'].includes(document.querySelector('#summary').className)",
            timeout=timeout_ms,
        )
        summary_class = page.locator("#summary").evaluate("el => el.className")
        summary = page.locator("#summary").inner_text()
        log_text = page.locator("#log").inner_text()

        print("summary_class=" + summary_class)
        print("summary=" + summary)
        print("log=")
        print(log_text)

        browser.close()
        return 0 if summary_class == "pass" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run LifeCash page-level smoke test.")
    parser.add_argument(
        "--root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Repository root containing smoke-test.html.",
    )
    parser.add_argument(
        "--base-url",
        default="http://lifecash.local",
        help="Synthetic same-origin URL used by Playwright route interception.",
    )
    parser.add_argument(
        "--timeout-ms",
        default=45000,
        type=int,
        help="Maximum time to wait for smoke-test.html to finish.",
    )
    parser.add_argument("--headed", action="store_true", help="Show Chromium window.")
    args = parser.parse_args()

    try:
        return run_smoke(args.root, args.base_url, args.timeout_ms, args.headed)
    except PlaywrightTimeoutError as exc:
        print("Playwright timeout:", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
