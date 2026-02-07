from typing import Dict, List


class QualificationEngine:
    """
    Production Qualification Engine.

    Responsibilities:
    - classify technical state
    - apply business qualification rules
    - assign temperature and value
    - emit controlled reasons
    """

    # ----------------------------
    # Controlled vocabularies
    # ----------------------------

    TECHNICAL_REASONS = {
        "no_website_data",
        "signal_build_failure"
    }

    BUSINESS_REASONS = {
        "low_digital_maturity",
        "missing_booking",
        "missing_contacts"
    }

    # ----------------------------

    def __init__(
        self,
             min_digital_score=30,
             require_booking=False,
             require_contacts=False

    ):
        self.min_digital_score = min_digital_score
        self.require_booking = require_booking
        self.require_contacts = require_contacts

    # ----------------------------
    # PUBLIC API
    # ----------------------------

    def qualify(self, record: Dict) -> Dict:
        reasons: List[str] = []

        signals = record.get("signals")
        crawl_ok = record.get("crawl_ok", True)

        # ----------------------------
        # TECHNICAL GATE
        # ----------------------------

        if not crawl_ok:
            return self._technical_result(["no_website_data"])

        if not isinstance(signals, dict) or not signals:
            return self._technical_result(["signal_build_failure"])

        # ----------------------------
        # BUSINESS FACTS
        # ----------------------------

        score = int(signals.get("digital_maturity_score", 0))
        booking_status = signals.get("booking_type", "unknown")

        has_contacts = any([
            signals.get("has_email"),
            signals.get("has_phone"),
            signals.get("has_instagram"),
            signals.get("has_whatsapp"),
            signals.get("has_online_forms")
        ])

        qualified = True

        if score < self.min_digital_score:
            qualified = False
            reasons.append("low_digital_maturity")

        if self.require_booking and booking_status in {"none", "unknown"}:
            qualified = False
            reasons.append("missing_booking")

        if self.require_contacts and not has_contacts:
            qualified = False
            reasons.append("missing_contacts")

        # ----------------------------
        # LEAD CLASSIFICATION
        # ----------------------------

        temperature = self._lead_temperature(score, booking_status, has_contacts)
        value = self._lead_value(signals)

        status = "qualified" if qualified else "business_disqualified"

        return {
            "status": status,
            "qualified": qualified,
            "lead_temperature": temperature,
            "lead_value": value,
            "reasons": reasons,
            "digital_score": score,
            "booking_status": booking_status,
            "contacts_present": has_contacts
        }

    # ----------------------------
    # RESULT BUILDERS
    # ----------------------------

    @staticmethod
    def _technical_result(reasons: List[str]) -> Dict:
        return {
            "status": "technical_failure",
            "qualified": False,
            "lead_temperature": "dead",
            "lead_value": "low",
            "reasons": reasons,
            "digital_score": 0,
            "booking_status": "unknown",
            "contacts_present": False
        }

    # ----------------------------
    # LEAD MODELS
    # ----------------------------

    @staticmethod
    def _lead_temperature(score: int, booking_status: str, has_contacts: bool) -> str:
        if score >= 70 and booking_status not in {"none", "unknown"} and has_contacts:
            return "hot"
        elif score >= 40 and (booking_status not in {"none", "unknown"} or has_contacts):
            return "warm"
        elif score >= 15:
            return "cold"
        else:
            return "dead"

    @staticmethod
    def _lead_value(signals: Dict) -> str:
        score = signals.get("digital_maturity_score", 0)
        page_count = signals.get("page_count", 0)
        has_tracking = signals.get("has_google_analytics") or signals.get("has_facebook_pixel")
        booking_type = signals.get("booking_type")

        if score >= 75 and booking_type == "saas" and has_tracking and page_count >= 3:
            return "very_high"
        elif score >= 60 and booking_type in {"saas", "manual"}:
            return "high"
        elif score >= 35:
            return "medium"
        else:
            return "low"

    # ----------------------------
    # BATCH
    # ----------------------------

    def batch_qualify(self, records: List[Dict]) -> List[Dict]:
        results = []
        for rec in records:
            try:
                results.append(self.qualify(rec))
            except Exception:
                results.append(self._technical_result(["signal_build_failure"]))
        return results
