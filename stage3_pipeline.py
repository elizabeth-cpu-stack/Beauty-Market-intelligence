import csv
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path

from src.intelligence.crawler import WebsiteCrawler
from src.intelligence.booking_detector import BookingDetector
from src.intelligence.contact_extractor import ContactExtractor
from src.intelligence.signal_engine import SignalEngine
from src.intelligence.qualification_engine import QualificationEngine

from src.pipeline.lead_splitter import LeadSplitter
from src.pipeline.exporters import CSVExporter
from src.utils.logger import log


# =========================
# PATHS
# =========================

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "output"

INPUT_PATH = RAW_DIR / "salons_stage1.csv"
QUALIFIED_OUT = OUTPUT_DIR / "qualified_leads.csv"
UNQUALIFIED_OUT = OUTPUT_DIR / "unqualified_leads.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# CONFIG
# =========================

MAX_PAGES = 4
CRAWL_TIMEOUT = 90
BATCH_SIZE = 15   # safer for Playwright


# =========================
# LOADERS
# =========================

def load_stage1_records(path: Path) -> List[Dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# =========================
# HELPERS
# =========================

def extract_city(city_state: str) -> str:
    if not city_state:
        return "Unknown"
    return city_state.split(",")[0].strip()


# =========================
# FINAL LEAD BUILDER
# =========================
def build_final_lead(
    record: Dict,
    booking: Optional[Dict],
    contacts: Optional[Dict],
    signals: Optional[Dict],
    qualification: Dict
) -> Dict:
    """
    Converts all Stage 2 & 3 outputs into a single structured lead record.
    Ensures:
    - booking info is used
    - signals merged
    - contacts merged
    - qualification enforced
    - city normalized
    """

    socials = contacts.get("socials", {}) if contacts else {}

    return {
        "salon_name": record.get("salon_name", "unknown"),
        "website": record.get("website", "unknown"),
        "city": extract_city(record.get("city_state")),

        # ------------------------
        # Contacts
        # ------------------------
        "emails": contacts.get("emails", []) if contacts else [],
        "phones": contacts.get("phones", []) if contacts else [],
        "instagram": socials.get("instagram", []),
        "facebook": socials.get("facebook", []),

        # ------------------------
        # Booking
        # ------------------------
        "booking_status": booking.get("booking_status", "none") if booking else "none",
        "booking_provider": booking.get("booking_provider", "unknown") if booking else "unknown",
        "booking_confidence": booking.get("booking_confidence", 0.0) if booking else 0.0,

        # ------------------------
        # Signals
        # ------------------------
        "digital_score": signals.get("digital_maturity_score", 0) if signals else 0,
        "page_count": signals.get("page_count", 0) if signals else 0,
        "has_forms": signals.get("has_online_forms", False) if signals else False,
        "has_google_analytics": signals.get("has_google_analytics", False) if signals else False,
        "has_facebook_pixel": signals.get("has_facebook_pixel", False) if signals else False,

        # ------------------------
        # Qualification
        # ------------------------
        "qualified": qualification.get("qualified", False),
        "status": qualification.get("status", "technical_failure"),
        "lead_temperature": qualification.get("lead_temperature", "dead"),
        "lead_value": qualification.get("lead_value", "low"),
        "reasons": qualification.get("reasons", ["unspecified"]),

        # ------------------------
        # Pipeline metadata
        # ------------------------
        "processed_at": datetime.now(timezone.utc).isoformat()
    }

# =========================
# SALON WORKER
# =========================

# =========================
# SAAS DETECTION (ADD THIS BEFORE THE FUNCTION)
# =========================

SAAS_DOMAINS = {
    "fresha.com": "fresha",
    "booksy.com": "booksy",
    "square.site": "square",
    "glossgenius.com": "glossgenius",
    "vagaro.com": "vagaro",
    "styleseat.com": "styleseat",
    "mindbodyonline.com": "mindbody",
    "squareup.com": "square"
}


def detect_saas_hosting(website: str) -> tuple:
    """Check if website IS a SaaS platform (not just using one)"""
    if not website:
        return False, ""

    website_lower = website.lower()
    for domain, provider in SAAS_DOMAINS.items():
        if domain in website_lower:
            return True, provider
    return False, ""


# =========================
# SALON WORKER (MODIFIED)
# =========================

async def process_single_salon(
        rec: Dict,
        booking_detector: BookingDetector,
        contact_extractor: ContactExtractor,
        signal_engine: SignalEngine,
        qualification_engine: QualificationEngine
) -> Dict:
    # ----------------------------
    # CHECK: Is this a SaaS-hosted site?
    # ----------------------------
    is_saas_hosted, saas_provider = detect_saas_hosting(rec.get("website", ""))

    if is_saas_hosted:
        # Skip crawling - we already know they use SaaS
        rec["crawl_ok"] = True
        rec["website_pages"] = []

        booking = {
            "booking_status": "saas",
            "booking_provider": saas_provider,
            "booking_confidence": 1.0
        }

        contacts = {
            "emails": [],
            "phones": [],
            "socials": {},
            "has_forms": False
        }

        rec["booking"] = booking
        rec["contacts"] = contacts

        # Build minimal signals
        signals = {
            "has_website": True,
            "page_count": 0,
            "has_booking": True,
            "booking_type": "saas",
            "booking_provider": saas_provider,
            "has_email": False,
            "has_phone": False,
            "has_instagram": False,
            "has_whatsapp": False,
            "has_contact_page": False,
            "has_online_forms": False,
            "has_facebook_pixel": False,
            "has_google_analytics": False,
            "has_facebook_sitewide": False,
            "has_instagram_sitewide": False,
            "mentions_booking_language": False,
            "mentions_pricing": False,
            "mentions_services": False,
            "mentions_training": False,
            "external_domain_count": 0,
            "script_count": 0,
            "digital_maturity_score": 55  # Base score for SaaS-hosted
        }

        rec["signals"] = signals
        qualification = qualification_engine.qualify(rec)

        return build_final_lead(rec, booking, contacts, signals, qualification)

    # ----------------------------
    # NORMAL FLOW: Crawl the site
    # ----------------------------

    crawler = WebsiteCrawler(rec.get("website"), max_pages=MAX_PAGES)

    crawl_result = await crawler.crawl()

    rec["crawl_ok"] = crawl_result.get("ok", False)
    rec["website_pages"] = crawl_result.get("pages", [])

    booking = booking_detector.detect_site(rec["website_pages"]) if rec["crawl_ok"] else {}
    contacts = contact_extractor.extract_from_pages(rec["website_pages"]) if rec["crawl_ok"] else {}

    rec["booking"] = booking
    rec["contacts"] = contacts

    signals = signal_engine.build_signals(rec) if rec["crawl_ok"] else {}
    rec["signals"] = signals

    qualification = qualification_engine.qualify(rec)

    return build_final_lead(rec, booking, contacts, signals, qualification)
# =========================
# ORCHESTRATOR
# =========================

async def run_stage3():
    start_time = datetime.now(timezone.utc)
    log(f"[PIPELINE START] {start_time.isoformat()}")

    stage1_records = load_stage1_records(INPUT_PATH)
    total = len(stage1_records)

    booking_detector = BookingDetector()
    contact_extractor = ContactExtractor()
    signal_engine = SignalEngine()
    qualification_engine = QualificationEngine()

    qualified_all = []
    unqualified_all = []

    for i in range(0, total, BATCH_SIZE):

        batch = stage1_records[i:i + BATCH_SIZE]

        tasks = [
            process_single_salon(
                rec,
                booking_detector,
                contact_extractor,
                signal_engine,
                qualification_engine
            )
            for rec in batch
        ]

        results = await asyncio.gather(*tasks)

        qualified, unqualified = LeadSplitter.split(results)

        qualified_all.extend(qualified)
        unqualified_all.extend(unqualified)

        CSVExporter.export(str(QUALIFIED_OUT), qualified_all)
        CSVExporter.export(str(UNQUALIFIED_OUT), unqualified_all)

        log(f"[BATCH COMPLETE] {min(i + BATCH_SIZE, total)}/{total}")

    duration = datetime.now(timezone.utc) - start_time

    log("[PIPELINE COMPLETE]")
    log(f"[SUMMARY] Duration={duration} | Qualified={len(qualified_all)} | Unqualified={len(unqualified_all)}")


# =========================
# ENTRY
# =========================

if __name__ == "__main__":
    asyncio.run(run_stage3())


