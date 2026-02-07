import re
from typing import List, Dict, Set
from urllib.parse import urlparse

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"\+?\d[\d\s()\-]{7,}\d")

SOCIAL_DOMAINS = {
    "instagram": "instagram.com",
    "facebook": "facebook.com",
    "tiktok": "tiktok.com",
    "twitter": "twitter.com",
    "linkedin": "linkedin.com",
    "youtube": "youtube.com",
    "whatsapp": "wa.me"
}

CONTACT_KEYWORDS = [
    "contact", "about", "support", "appointment", "booking", "connect"
]


class ContactExtractor:
    """
    Production-grade contact intelligence extractor.
    """

    # ----------------------------
    # PRODUCTION ENTRYPOINT
    # ----------------------------

    def extract_from_pages(self, pages: List[Dict]) -> Dict:
        """
        Pipeline-safe wrapper.
        """

        if not pages or not isinstance(pages, list):
            return {
                "emails": [],
                "phones": [],
                "socials": {},
                "contact_pages": [],
                "has_forms": False,
                "contact_score": 0.0
            }

        return self.extract(pages)

    # ----------------------------
    # CORE ENGINE
    # ----------------------------

    def extract(self, pages: List[Dict]) -> Dict:
        emails: Set[str] = set()
        phones: Set[str] = set()
        socials: Dict[str, Set[str]] = {k: set() for k in SOCIAL_DOMAINS}
        contact_pages: Set[str] = set()
        has_forms = False

        for page in pages:
            if not isinstance(page, dict):
                continue

            text = page.get("text", "")
            links = page.get("links", [])
            forms = page.get("forms", [])

            if forms:
                has_forms = True

            for email in EMAIL_REGEX.findall(text):
                emails.add(email.lower())

            for phone in PHONE_REGEX.findall(text):
                phones.add(self._clean_phone(phone))

            for link in links:
                if not isinstance(link, str):
                    continue

                l = link.lower()

                for platform, domain in SOCIAL_DOMAINS.items():
                    if domain in l:
                        socials[platform].add(self._normalize_url(link))

                if any(k in l for k in CONTACT_KEYWORDS):
                    contact_pages.add(self._normalize_url(link))

        return {
            "emails": sorted(emails),
            "phones": sorted(phones),
            "socials": {k: sorted(v) for k, v in socials.items() if v},
            "contact_pages": sorted(contact_pages),
            "has_forms": has_forms,
            "contact_score": self._contact_score(emails, phones, socials, has_forms)
        }

    # ----------------------------
    # UTILITIES
    # ----------------------------

    @staticmethod
    def _clean_phone(phone: str) -> str:
        return re.sub(r"[^\d+]", "", phone)

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

    @staticmethod
    def _contact_score(emails, phones, socials, has_forms) -> float:
        score = 0.0
        if emails: score += 0.4
        if phones: score += 0.3
        if any(socials.values()): score += 0.2
        if has_forms: score += 0.1
        return round(min(score, 1.0), 2)
