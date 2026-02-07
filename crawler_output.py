from urllib.parse import urlparse, urljoin
import re


class CrawlerOutputEngine:
    """
    Converts raw crawled pages into a unified intelligence object
    that downstream engines (booking, contacts, signals) can trust.
    """

    def __init__(self, pages: list[dict]):
        self.pages = pages

    def build(self) -> dict:
        return {
            "base_url": self._get_base_url(),
            "pages_crawled": len(self.pages),
            "all_text": self._merge_text(),
            "all_links": self._merge_links(),
            "internal_links": self._extract_internal_links(),
            "external_links": self._extract_external_links(),
            "all_scripts": self._merge_scripts(),
            "all_buttons": self._merge_buttons(),
            "all_forms": self._merge_forms(),
            "page_map": self._build_page_map(),
            "all_iframes": self._merge_iframes()

        }

    # ---------------- CORE MERGERS ---------------- #

    def _merge_text(self) -> str:
        return "\n".join(p.get("text", "") for p in self.pages if p.get("text"))

    def _merge_links(self) -> set:
        links = set()
        for p in self.pages:
            links.update(p.get("links", []))
        return self._clean_urls(links)

    def _merge_scripts(self) -> list:
        scripts = []
        for p in self.pages:
            scripts.extend(p.get("scripts", []))
        return scripts

    def _merge_buttons(self) -> list:
        buttons = []
        for p in self.pages:
            buttons.extend(p.get("buttons", []))
        return buttons

    def _merge_forms(self) -> list:
        forms = []
        for p in self.pages:
            forms.extend(p.get("forms", []))
        return forms

    def _merge_iframes(self) -> list:
        frames = []
        for p in self.pages:
            frames.extend(p.get("iframes", []))
        return frames

    # ---------------- STRUCTURE ---------------- #

    def _build_page_map(self) -> dict:
        page_map = {}
        for p in self.pages:
            page_map[p.get("url")] = {
                "text": p.get("text"),
                "links": p.get("links"),
                "scripts": p.get("scripts"),
                "buttons": p.get("buttons"),
                "forms": p.get("forms")
            }
        return page_map

    # ---------------- URL PROCESSING ---------------- #

    def _get_base_url(self) -> str | None:
        if not self.pages:
            return None
        parsed = urlparse(self.pages[0]["url"])
        return f"{parsed.scheme}://{parsed.netloc}"

    def _extract_internal_links(self) -> set:
        base = self._get_base_url()
        if not base:
            return set()

        return {
            link for link in self._merge_links()
            if link.startswith(base)
        }

    def _extract_external_links(self) -> set:
        base = self._get_base_url()
        if not base:
            return set()

        return {
            link for link in self._merge_links()
            if link.startswith("http") and not link.startswith(base)
        }

    # ---------------- CLEANERS ---------------- #

    def _clean_urls(self, urls: set) -> set:
        cleaned = set()
        for u in urls:
            u = u.strip()
            if not u.startswith("http"):
                continue
            u = re.sub(r"#.*$", "", u)
            cleaned.add(u.rstrip("/"))
        return cleaned
