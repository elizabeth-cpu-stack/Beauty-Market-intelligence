import re
from typing import Dict, Tuple, Optional, List


# =========================
# CONFIG: Known SaaS Providers
# =========================

SAAS_PROVIDERS = {
    "fresha": ["fresha.com"],
    "mindbody": ["mindbodyonline.com", "mindbody.io"],
    "square": ["squareup.com", "square.site"],
    "vagaro": ["vagaro.com"],
    "booksy": ["booksy.com"],
    "setmore": ["setmore.com"],
    "acuity": ["acuityscheduling.com"],
    "simplybook": ["simplybook.me"],
    "mangomint": ["mangomint.com"],
    "glossgenius": ["glossgenius.com"],
    "zenoti": ["zenoti.com"],
    "boulevard": ["joinblvd.com"],
    "phorest": ["phorest.com"],
    "daysmart": ["daysmartsalon.com"],
    "squire": ["getsquire.com", "squire.com"],
    "timely": ["timely.com"],
    "schedulicity": ["schedulicity.com"],
    "booker": ["booker.com"],
    "saloncloud": ["saloncloud.com"],
    "nearcut": ["nearcut.com"],
    "appointy": ["appointy.com"],
    "salonized": ["salonized.com"],
    "styleseat": ["styleseat.com"],
    "supersaas": ["supersaas.com"],
    "picktime": ["picktime.com"]
}

# =========================
# Manual / Weak Signals
# =========================

MANUAL_ACTION_PATTERNS = [
    r"book\s+now",
    r"schedule\s+appointment",
    r"make\s+an?\s+appointment",
    r"reserve\s+now",
    r"online\s+booking",
    r"book\s+online"
]

MANUAL_LINK_PATTERNS = [
    r"tel:",
    r"mailto:",
    r"wa\.me",
    r"whatsapp\.com",
    r"calendly\.com"
]


# =========================
# Utilities
# =========================

def normalize(s: str) -> str:
    return s.lower().strip() if isinstance(s, str) else ""


def flatten_assets(page_data: Dict) -> List[str]:
    assets = []
    for key in ("links", "scripts", "forms", "iframes", "buttons"):
        items = page_data.get(key) or []
        assets.extend(items)
    assets.append(page_data.get("text") or "")
    return [normalize(a) for a in assets if a]


# =========================
# Core Detection
# =========================

def detect_saas(assets: List[str]) -> Tuple[Optional[str], float]:
    for provider, domains in SAAS_PROVIDERS.items():
        for asset in assets:
            if any(domain in asset for domain in domains):
                return provider, 1.0
    return None, 0.0


def detect_manual(page_data: Dict, assets: List[str]) -> Tuple[Optional[str], float]:

    # Strong DOM-based signals
    if page_data.get("forms"):
        return "manual_form", 0.85

    for asset in assets:
        for p in MANUAL_LINK_PATTERNS:
            if re.search(p, asset):
                return "manual_contact", 0.75

    text = normalize(page_data.get("text", ""))
    for p in MANUAL_ACTION_PATTERNS:
        if re.search(p, text):
            return "manual_text", 0.65

    return None, 0.0


# =========================
# Production Booking Engine
# =========================

class BookingDetector:
    """
    Production-grade booking detection engine.

    Purpose:
    - Detect SaaS booking platforms
    - Detect manual / weak booking setups
    - Aggregate signals across crawled site
    """

    # ----------------------------
    # Page-level detection
    # ----------------------------

    def detect_page(self, page_data: Dict) -> Dict:

        if not isinstance(page_data, dict):
            return self._empty()

        assets = flatten_assets(page_data)

        # SaaS detection (hard signal)
        saas_provider, saas_conf = detect_saas(assets)
        if saas_provider:
            return {
                "booking_status": "saas",
                "booking_provider": saas_provider,
                "booking_confidence": saas_conf
            }

        # Manual detection (soft signal)
        manual_method, manual_conf = detect_manual(page_data, assets)
        if manual_method:
            return {
                "booking_status": "manual",
                "booking_provider": manual_method,
                "booking_confidence": manual_conf
            }

        return self._empty()

    # ----------------------------
    # Site-level aggregation
    # ----------------------------

    def detect_site(self, pages: List[Dict]) -> Dict:

        if not pages or not isinstance(pages, list):
            return self._empty()

        best = self._empty()
        manual_hits = 0

        for page in pages:
            result = self.detect_page(page)

            # SaaS overrides everything
            if result["booking_status"] == "saas":
                return result

            if result["booking_status"] == "manual":
                manual_hits += 1
                if result["booking_confidence"] > best["booking_confidence"]:
                    best = result

        # Escalate repeated manual signals
        if manual_hits >= 2 and best["booking_confidence"] > 0:
            best["booking_confidence"] = min(best["booking_confidence"] + 0.1, 0.9)

        return best

    # ----------------------------
    # Internal
    # ----------------------------

    @staticmethod
    def _empty() -> Dict:
        return {
            "booking_status": "none",
            "booking_provider": "unknown",
            "booking_confidence": 0.0
        }
