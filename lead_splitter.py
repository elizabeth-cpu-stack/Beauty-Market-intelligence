from typing import Dict, List, Tuple


class LeadSplitter:
    """
    Business splitter.
    Separates qualified vs unqualified leads.
    """

    @staticmethod
    def split(leads: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        qualified = []
        unqualified = []

        for lead in leads:
            if lead.get("qualified"):
                qualified.append(lead)
            else:
                unqualified.append(lead)

        return qualified, unqualified
