from typing import Dict, List
from urllib.parse import urlparse
import re


class SignalEngine:
    """
    Production signal engine.
    Emits strictly-typed, schema-stable factual signals.
    No business decisions. No technical judgments.
    """

    BOOKING_VOCAB = {"saas", "manual", "weak", "none", "unknown"}

    # ----------------------------
    # PUBLIC API
    # ----------------------------

    def build_signals(self, record: Dict) -> Dict:
        pages = record.get("website_pages") if isinstance(record.get("website_pages"), list) else []
        contacts = record.get("contacts") if isinstance(record.get("contacts"), dict) else {}
        booking = record.get("booking") if isinstance(record.get("booking"), dict) else {}

        socials = contacts.get("socials") if isinstance(contacts.get("socials"), dict) else {}

        combined_text = self._merge_text(pages)
        all_links = self._merge_links(pages)

        booking_status = booking.get("booking_status", "unknown")
        if booking_status not in self.BOOKING_VOCAB:
            booking_status = "unknown"

        signals = {
            # Infrastructure
            "has_website": len(pages) > 0,
            "page_count": len(pages),

            # Booking
            "has_booking": booking_status not in {"none", "unknown"},
            "booking_type": booking_status,
            "booking_provider": booking.get("booking_provider") or "",

            # Contacts
            "has_email": bool(contacts.get("emails")),
            "has_phone": bool(contacts.get("phones")),
            "has_instagram": bool(socials.get("instagram")),
            "has_whatsapp": bool(socials.get("whatsapp")),

            # Website structure
            "has_contact_page": self._has_contact_page(all_links),
            "has_online_forms": self._has_forms(pages),

            # Tracking / tech
            "has_facebook_pixel": self._has_facebook_pixel(pages),
            "has_google_analytics": self._has_google_analytics(pages),

            # Social presence (sitewide)
            "has_facebook_sitewide": self._has_domain_link(all_links, "facebook.com"),
            "has_instagram_sitewide": self._has_domain_link(all_links, "instagram.com"),

            # Language signals
            "mentions_booking_language": self._contains_booking_language(combined_text),
            "mentions_pricing": self._contains_pricing(combined_text),
            "mentions_services": self._contains_services(combined_text),
            "mentions_training": self._contains_training(combined_text),

            # Technical surface
            "external_domain_count": self._external_domain_count(all_links, record.get("website")),
            "script_count": self._script_count(pages),

            # Composite factual score
            "digital_maturity_score": self._digital_maturity_score(contacts, socials, booking_status, pages)
        }

        return signals

    # ----------------------------
    # CORE HELPERS
    # ----------------------------

    @staticmethod
    def _merge_text(pages: List[Dict]) -> str:
        return " ".join(p.get("text", "") for p in pages if isinstance(p, dict)).lower()

    @staticmethod
    def _merge_links(pages: List[Dict]) -> List[str]:
        links = []
        for p in pages:
            if isinstance(p, dict):
                links.extend(p.get("links", []))
        return list(set(l.lower() for l in links if isinstance(l, str)))

    @staticmethod
    def _has_contact_page(links: List[str]) -> bool:
        return any("contact" in l or "about" in l for l in links)

    @staticmethod
    def _has_forms(pages: List[Dict]) -> bool:
        return any(bool(p.get("forms")) for p in pages if isinstance(p, dict))

    @staticmethod
    def _has_facebook_pixel(pages: List[Dict]) -> bool:
        return any("facebook" in " ".join(p.get("scripts", [])).lower() for p in pages if isinstance(p, dict))

    @staticmethod
    def _has_google_analytics(pages: List[Dict]) -> bool:
        return any(
            "google-analytics" in " ".join(p.get("scripts", [])).lower()
            or "gtag" in " ".join(p.get("scripts", [])).lower()
            for p in pages if isinstance(p, dict)
        )

    @staticmethod
    def _has_domain_link(links: List[str], domain: str) -> bool:
        return any(domain in l for l in links)

    @staticmethod
    def _external_domain_count(links: List[str], base_url: str) -> int:
        if not base_url:
            return 0

        try:
            base = urlparse(base_url).netloc.replace("www.", "")
        except ValueError:
            return 0

        domains = set()
        for l in links:
            try:
                d = urlparse(l).netloc.replace("www.", "")
                if d and base not in d:
                    domains.add(d)
            except ValueError:
                continue

        return len(domains)

    @staticmethod
    def _script_count(pages: List[Dict]) -> int:
        return sum(len(p.get("scripts", [])) for p in pages if isinstance(p, dict))

    # ----------------------------
    # LANGUAGE SIGNALS
    # ----------------------------

    @staticmethod
    def _contains_booking_language(text: str) -> bool:
        return any(k in text for k in ["book now", "appointment", "schedule", "reserve"])

    @staticmethod
    def _contains_pricing(text: str) -> bool:
        return bool(re.search(r"\$|price|pricing|usd|eur|gbp", text))

    @staticmethod
    def _contains_services(text: str) -> bool:
        return any(k in text for k in ["services", "treatments", "lashes", "brows", "nails", "hair"])

    @staticmethod
    def _contains_training(text: str) -> bool:
        return any(k in text for k in ["training", "academy", "course", "certification", "class"])

    # ----------------------------
    # COMPOSITE SCORE (FACTUAL)
    # ----------------------------

    @staticmethod
    def _digital_maturity_score(contacts: Dict, socials: Dict, booking_status: str, pages: List[Dict]) -> int:
        score = 0

        if pages:
            score += 25
        if len(pages) >= 3:
            score += 15

        if booking_status == "saas":
            score += 20
        elif booking_status in {"manual", "weak"}:
            score += 15

        if contacts.get("emails"):
            score += 10
        if contacts.get("phones"):
            score += 10
        if socials.get("instagram"):
            score += 5
        if socials.get("whatsapp"):
            score += 5

        return min(score, 100)
