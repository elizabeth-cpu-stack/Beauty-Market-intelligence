import asyncio
import time
from typing import List, Set, Dict
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError


class WebsiteCrawler:
    """
    Production-hardened async website crawler.

    Guarantees:
    - never crashes caller
    - deterministic output
    - strict technical failure isolation
    """

    def __init__(
        self,
        start_url: str,
        max_pages: int = 6,
        nav_timeout: int = 30000,
        max_retries: int = 2
    ):
        self.start_url = self._normalize_url(start_url)
        self.domain = urlparse(self.start_url).netloc

        self.max_pages = max_pages
        self.nav_timeout = nav_timeout
        self.max_retries = max_retries

        self.visited: Set[str] = set()
        self.to_visit: asyncio.Queue[str] = asyncio.Queue()

        self.pages: List[Dict] = []
        self.failed_urls: List[str] = []
        self.errors: List[str] = []

        self._t0 = time.time()

    # ----------------------------
    # Public API
    # ----------------------------

    async def crawl(self) -> dict:
        await self.to_visit.put(self.start_url)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled"
                    ]
                )

                context = await browser.new_context(
                    ignore_https_errors=True,
                    java_script_enabled=True
                )

                await context.route("**/*", self._route_filter)

                while not self.to_visit.empty() and len(self.visited) < self.max_pages:
                    url = await self.to_visit.get()

                    if url in self.visited:
                        continue

                    await self._crawl_page(context, url)

                await context.close()
                await browser.close()

        except Exception as e:
            self.errors.append(f"browser_level_failure: {type(e).__name__}: {e}")

        finally:
            return self._build_result()

    # ----------------------------
    # Core crawl logic
    # ----------------------------

    async def _crawl_page(self, context, url: str) -> None:
        self.visited.add(url)

        for attempt in range(1, self.max_retries + 1):
            page = None
            try:
                page = await context.new_page()
                await page.goto(url, timeout=self.nav_timeout, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle", timeout=8000)

                data = await self._extract_page(page, url)
                self.pages.append(data)

                await self._discover_links(page, url)
                return

            except PlaywrightTimeoutError:
                if attempt == self.max_retries:
                    self.failed_urls.append(url)
                    self.errors.append(f"timeout: {url}")

            except PlaywrightError as e:
                if attempt == self.max_retries:
                    self.failed_urls.append(url)
                    self.errors.append(f"playwright_error: {url} | {type(e).__name__}")

            except Exception as e:
                if attempt == self.max_retries:
                    self.failed_urls.append(url)
                    self.errors.append(f"unknown_error: {url} | {type(e).__name__}: {e}")

            finally:
                if page:
                    try:
                        await page.close()
                    except Exception:
                        pass

    # ----------------------------
    # Extraction
    # ----------------------------

    async def _extract_page(self, page, url: str) -> Dict:
        text = await page.inner_text("body")

        links = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        scripts = await page.eval_on_selector_all("script[src]", "els => els.map(e => e.src)")
        buttons = await page.eval_on_selector_all("button", "els => els.map(e => e.innerText)")
        forms = await page.eval_on_selector_all("form", "els => els.map(e => e.outerHTML)")
        iframes = await page.eval_on_selector_all("iframe[src]", "els => els.map(e => e.src)")

        return {
            "url": url,
            "text": text or "",
            "links": links or [],
            "scripts": scripts or [],
            "buttons": buttons or [],
            "forms": forms or [],
            "iframes": iframes or []

        }

    async def _discover_links(self, page, base_url: str) -> None:
        hrefs = await page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => e.getAttribute('href'))"
        )

        for href in hrefs:
            if not href:
                continue

            full = urljoin(base_url, href)
            parsed = urlparse(full)

            if parsed.netloc == self.domain:
                normalized = self._normalize_url(full)
                if normalized not in self.visited:
                    await self.to_visit.put(normalized)

    # ----------------------------
    # Network hardening
    # ----------------------------

    async def _route_filter(self, route, request):
        try:
            if request.resource_type in {"image", "font", "media"}:
                await route.abort()
            else:
                await route.continue_()
        except Exception:
            await route.abort()

    # ----------------------------
    # Output
    # ----------------------------

    def _build_result(self) -> dict:
        return {
            "ok": len(self.pages) > 0,
            "base_url": self.start_url,
            "pages": self.pages,
            "pages_crawled": len(self.pages),
            "failed_urls": self.failed_urls,
            "errors": self.errors,
            "timings": {
                "seconds": round(time.time() - self._t0, 2)
            }
        }

    # ----------------------------
    # Utilities
    # ----------------------------

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
