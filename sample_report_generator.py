import pandas as pd
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "output"
PACKAGES_DIR = OUTPUT_DIR / "packages"
SAMPLES_DIR = OUTPUT_DIR / "samples"

SAMPLES_DIR.mkdir(exist_ok=True)


def create_sample_report():
    """Create a professional sample report for buyer outreach"""

    qualified = pd.read_csv(OUTPUT_DIR / "qualified_leads.csv")

    # Get 5 best leads from each segment
    vulnerability = qualified[qualified['booking_status'].isin(['manual', 'none'])].head(5)
    saas_growth = qualified[qualified['booking_status'] == 'saas'].head(5)

    timestamp = datetime.now().strftime("%Y%m%d")

    # Create sample report
    sample_path = SAMPLES_DIR / f"Sample_Report_FL_Salons_{timestamp}.xlsx"

    with pd.ExcelWriter(sample_path, engine='openpyxl') as writer:
        # Cover sheet
        cover = pd.DataFrame({
            '': [
                'FLORIDA SALON INTELLIGENCE REPORT',
                'Sample Dataset - January 2026',
                '',
                'WHAT THIS REPORT CONTAINS',
                '',
                '• 10 sample salon leads (5 vulnerability, 5 SaaS-equipped)',
                '• Full intelligence: booking status, digital scores, contacts',
                '• Real, verified Florida salons crawled January 2026',
                '',
                'FULL DATASET AVAILABLE',
                '',
                '• Package 1: 230+ Vulnerability Leads (manual/no booking)',
                '• Package 2: 155+ SaaS Growth Leads',
                '• Package 3: 385+ Complete Dataset',
                '',
                'DATA FIELDS INCLUDED',
                '',
                '• Salon name, location, website',
                '• Booking system status (none/manual/SaaS)',
                '• Contact methods (email, phone, social)',
                '• Digital maturity score (0-100)',
                '• Lead temperature (hot/warm/cold)',
                '• Lead value rating',
                '',
                'CONTACT FOR FULL DATASET',
                '',
                'Email: [jolaosoelizabethaduragbemi@gmail.com]',
                'Available immediately in Excel format'
            ]
        })
        cover.to_excel(writer, sheet_name='Cover', index=False, header=False)

        # Vulnerability sample
        vuln_display = vulnerability[[
            'salon_name', 'city', 'website', 'booking_status',
            'digital_score', 'lead_temperature', 'lead_value',
            'emails', 'phones', 'instagram'
        ]].copy()

        vuln_display.to_excel(writer, sheet_name='Vulnerability Sample', index=False)

        # SaaS Growth sample
        saas_display = saas_growth[[
            'salon_name', 'city', 'website', 'booking_status', 'booking_provider',
            'digital_score', 'lead_temperature', 'lead_value',
            'emails', 'phones', 'instagram'
        ]].copy()

        saas_display.to_excel(writer, sheet_name='SaaS Growth Sample', index=False)

        # Data dictionary
        dictionary = pd.DataFrame({
            'Field Name': [
                'salon_name',
                'city',
                'website',
                'booking_status',
                'booking_provider',
                'digital_score',
                'lead_temperature',
                'lead_value',
                'emails',
                'phones',
                'instagram',
                'best_contact_method'
            ],
            'Description': [
                'Business name',
                'City, State location',
                'Primary website URL',
                'none = no system | manual = phone/WhatsApp | saas = using software',
                'Specific SaaS provider detected (e.g., Fresha, Booksy)',
                '0-100 score based on digital infrastructure maturity',
                'hot = ready to buy | warm = interested | cold = needs nurturing',
                'very_high/high/medium/low based on business signals',
                'Email addresses extracted from website',
                'Phone numbers extracted from website',
                'Instagram profile link',
                'Recommended first contact channel'
            ]
        })

        dictionary.to_excel(writer, sheet_name='Data Dictionary', index=False)

    print(f"\n✅ Sample report created: {sample_path.name}")
    print(f"   Location: {sample_path}")
    print(f"\n📧 Attach this to your outreach emails as proof of data quality.\n")


if __name__ == "__main__":
    create_sample_report()
