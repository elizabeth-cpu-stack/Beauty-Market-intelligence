

Overview

The Beauty Market Intelligence Pipeline is an automated B2B data intelligence system that identifies salons and spas with weak booking infrastructure and generates buyer-ready datasets for software companies, marketing agencies,and lead generation agencies.

What makes it different: This isn't a contact scraper—it's an infrastructure analysis engine that provides evidence-backed intelligence on digital maturity, booking systems, and commercial vulnerability.


Business Model

The Problem:
- Salons and spas using manual booking (phone/WhatsApp) lose 20-30% potential revenue
- Booking SaaS companies need pre-qualified leads
- Marketing agencies waste 40+ hours researching prospects
- Lead generation agencies scrape unqualified leads

The Solution...
Automated pipeline that:
1. Discovers salons from public platforms
2. Analyzes their digital infrastructure
3. Detects booking systems and vulnerabilities
4. Packages intelligence for buyers


System Architecture

Pipeline Stages


Stage 1: Territory Capture
   ↓
Stage 2: Intelligence Extraction
   ↓
Stage 3: Qualification & Packaging


Core Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| WebsiteCrawler | Scrapes salon websites (up to 6 pages) | Playwright (async) |
| BookingDetector | Identifies booking systems (none/manual/SaaS) | Pattern matching |
| ContactExtractor | Extracts emails, phones, social profiles | Regex patterns |
| SignalEngine | Generates digital maturity scores (0-100) | Multi-factor analysis |
| QualificationEngine | Classifies leads by value and temperature | Business rules |



Technical Stack

Languages & Frameworks
- Python 3.12
- Playwright - Async web crawling
- pandas - Data manipulation
- openpyxl - Excel file generation

Key Libraries
python
playwright==1.40.0
pandas==2.1.4
openpyxl==3.1.2


Installation

Prerequisites
- Python 3.12+
- pip package manager

Setup
bash
# Clone repository
cd PythonProject

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Mac/Linux
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install playwright pandas openpyxl

# Install Playwright browsers
playwright install chromium




## Project Structure


PythonProject/
│
├── data/
│   ├── raw/
│   │   ├── salons_discovered.csv      # Stage 1 output (all salons)
│   │   └── salons_stage1.csv          # Filtered (websites only)
│   │
│   └── output/
│       ├── qualified_leads.csv        # Stage 3 output (qualified)
│       ├── unqualified_leads.csv      # Stage 3 output (unqualified)
│       └── packages/                  # Excel deliverables
│           ├── 1_Vulnerability_Leads_FL_YYYYMMDD.xlsx
│           ├── 2_SaaS_Growth_Leads_FL_YYYYMMDD.xlsx
│           └── 3_Complete_Dataset_FL_YYYYMMDD.xlsx
│
├── src/
│   ├── intelligence/
│   │   ├── crawler.py                 # WebsiteCrawler
│   │   ├── booking_detector.py        # BookingDetector
│   │   ├── contact_extractor.py       # ContactExtractor
│   │   ├── signal_engine.py           # SignalEngine
│   │   └── qualification_engine.py    # QualificationEngine
│   │
│   ├── pipeline/
│   │   ├── stage3_orchestrator.py     # Main pipeline runner
│   │   ├── lead_splitter.py           # Splits qualified/unqualified
│   │   └── exporters.py               # CSV/Excel export
│   │
│   └── utils/
│       └── logger.py                  # Logging utilities
│
└── package_excel.py                   # Excel packaging script




Usage

Run the Full Pipeline**

bash
# Ensure Stage 1 data exists in data/raw/salons_stage1.csv

# Run Stage 3 (Intelligence + Qualification)
python -m src.pipeline.stage3_orchestrator

# Package results into Excel
python package_excel.py


# Expected Runtime
- Stage 3: 30-45 minutes for 700 salons
- Packaging: 1-2 minutes



#Data Flow

### Input (Stage 1)**
CSV with columns:
- salon_name
- maps_url
- website
- city_state
- scraped_at

#Processing (Stage 2 & 3)

For each salon:
1. Crawl website → Extract text, links, scripts, forms
2. Detect booking → Identify none/manual/SaaS + provider
3. Extract contacts → Find emails, phones, social profiles
4. Generate signals → Calculate 35+ data points
5. Qualify → Score, classify, assign value/temperature

#Output (Buyer-Ready Datasets)

3 Excel packages:

Package 1: Vulnerability Leads
- Salons with manual/no booking systems
- Prime conversion targets for booking SaaS

Package 2: SaaS Growth Leads
- Salons already using booking software
- Competitive intelligence + upsell opportunities

Package 3: Complete Dataset
- All qualified leads
- For agencies and multi-product vendors



Key Algorithms

#Digital Maturity Scoring

python
score = 0
if has_website: score += 25
if page_count >= 3: score += 15
if booking_status == "saas": score += 20
elif booking_status == "manual": score += 15
if has_email: score += 10
if has_phone: score += 10
if has_instagram: score += 5
if has_whatsapp: score += 5



#Lead Temperature

python
if score >= 70 and has_booking and has_contacts:
    temperature = "hot"
elif score >= 40 and (has_booking or has_contacts):
    temperature = "warm"
elif score >= 15:
    temperature = "cold"
else:
    temperature = "dead"


#Booking Detection

SaaS Detection:
python
SAAS_PROVIDERS = {
    "fresha": ["fresha.com"],
    "vagaro": ["vagaro.com"],
    "square": ["squareup.com", "square.site"],
    # ... 20+ providers
}
 Searches all links, scripts, iframes for provider domains


Manual Detection:
python
MANUAL_PATTERNS = [
    r"tel:",           # Phone links
    r"mailto:",        # Email links
    r"wa\.me",         # WhatsApp links
    r"book\s+now",     # Booking language
]


Known Limitations

#Data Quality
Contact accuracy: ~85% (industry standard for automated collection)
- Some fields incomplete:** Emails/phones(requires manual research) missing for ~20-30% of salons
- Social URLs: ~20% error rate
- Tracking detection:GA/FB Pixel ~80% accuracy

Technical Constraints
- Playwright errors: Harmless race conditions during async crawling (visual noise, doesn't affect results)
- Timeout failures: ~40-45% of salons fail to crawl (slow sites, blocking, no website)
- JavaScript-rendered content:** May miss contact info rendered client-side

Scope
- Current coverage: Florida only (Orlando, Tallahassee, Sarasota)
- Salon count:385 qualified (from 1,566 discovered)
- Stage 1: Currently manual (Google Maps scraper separate)



Performance Metrics

Current Results (Florida Dataset)

Total discovered: 1,566 salons
Successfully crawled: 717 salons (45.8%)
Qualified: 385 salons (53.7% of crawled)

Qualification breakdown:
- Vulnerability (manual/no booking): 230(manually verified down to 211) salons and spas (58.4%)
- SaaS Growth (using software): 165(manually verified to 150) salons and spas (41.6%)




Future Enhancements

Short-term (1-3 months)
-  Expand to 5-10 additional US cities
-  Add monthly update capability (re-crawl + delta detection)
-  Improve contact extraction (OCR for images, form parsing)
-  Add phone number validation API

Medium-term (3-6 months)
-  Real-time monitoring (detect when salons switch systems)
-  API access for enterprise buyers
-  Automated sample generation
-  Geographic expansion (all 50 states)

Long-term (6-12 months)**
-  AI agent layer (alerts, insights, recommendations)
-  Vertical SaaS products (tools for buyers to act on intelligence)
-  Partnership integrations (CRM, marketing automation)
-  Predictive scoring (likelihood to convert)



Contributing

This is a solo project currently in active development. Feedback and suggestions welcome.



License

Proprietary - All rights reserved.

This system and its outputs are commercial products. Unauthorized use, reproduction, or distribution is prohibited.



Contact

Developer: Elizabeth  
Business: B2B Beauty Market Intelligence  
Stage: Pilot/early revenue  

For inquiries about purchasing datasets or partnership opportunities, contact via email.



Changelog

v1.0 (January 2026)
- Initial production release
- Florida market coverage (3 cities, 385 qualified leads)
- 3-package Excel deliverable system
- Core engines: Crawler, BookingDetector, ContactExtractor, SignalEngine, QualificationEngine

v0.9 (January 2026)
- Beta testing and data cleaning
- Removed social media URLs misclassified as websites (26 salons)
- Optimized qualification thresholds
- Added SaaS-hosted detection (skip crawling for Fresha/Booksy direct URLs)



#Acknowledgments

Built with:
- Playwright for robust web crawling
- pandas for data manipulation
- Python async for performance

Inspired by the gap between generic lead lists and actionable business intelligence.



Last Updated: January 2026  
Version:1.0  
Status: Production-ready
