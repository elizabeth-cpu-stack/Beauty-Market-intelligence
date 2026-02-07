import pandas as pd
from pathlib import Path
from datetime import datetime
import ast

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "output"
PACKAGES_DIR = OUTPUT_DIR / "packages"

PACKAGES_DIR.mkdir(exist_ok=True)


def safe_parse_list(value):
    if pd.isna(value) or value == '' or value == '[]':
        return ''
    try:
        parsed = ast.literal_eval(str(value))
        if isinstance(parsed, list):
            return ', '.join(str(item) for item in parsed if item)
        return str(value)
    except (ValueError, SyntaxError):
        return str(value)


def create_summary_sheet(data, package_name):
    """Create buyer-focused summary"""

    if package_name == "Vulnerability":
        metrics = {
            'Metric': [
                'Total Leads',
                'Manual Booking System',
                'No Booking System',
                '',
                'Quality Metrics',
                'Average Digital Score (out of 100)',
                'Hot Leads',
                'Warm Leads',
                'Cold Leads',
                '',
                'Lead Value Distribution',
                'Very High Value',
                'High Value',
                'Medium Value'
            ],
            'Count': [
                len(data),
                len(data[data['booking_status'] == 'manual']),
                len(data[data['booking_status'] == 'none']),
                '',
                '',
                f"{data['digital_score'].mean():.1f}",
                len(data[data['lead_temperature'] == 'hot']),
                len(data[data['lead_temperature'] == 'warm']),
                len(data[data['lead_temperature'] == 'cold']),
                '',
                '',
                len(data[data['lead_value'] == 'very_high']),
                len(data[data['lead_value'] == 'high']),
                len(data[data['lead_value'] == 'medium'])
            ]
        }

    elif package_name == "SaaS Growth":
        metrics = {
            'Metric': [
                'Total Leads',
                'Using SaaS Booking System',
                '',
                'Quality Metrics',
                'Average Digital Score (out of 100)',
                'Hot Leads',
                'Warm Leads',
                '',
                'Technology Adoption',
                'Has Google Analytics',
                'Has Facebook Pixel',
                'Active on Social Media',
                '',
                'Lead Value Distribution',
                'Very High Value',
                'High Value',
                'Medium Value'
            ],
            'Count': [
                len(data),
                len(data[data['booking_status'] == 'saas']),
                '',
                '',
                f"{data['digital_score'].mean():.1f}",
                len(data[data['lead_temperature'] == 'hot']),
                len(data[data['lead_temperature'] == 'warm']),
                '',
                '',
                len(data[data['has_google_analytics'] == True]) if 'has_google_analytics' in data.columns else 0,
                len(data[data['has_facebook_pixel'] == True]) if 'has_facebook_pixel' in data.columns else 0,
                len(data[(data['instagram'] != '') | (data['facebook'] != '')]),
                '',
                '',
                len(data[data['lead_value'] == 'very_high']),
                len(data[data['lead_value'] == 'high']),
                len(data[data['lead_value'] == 'medium'])
            ]
        }

    else:  # Complete
        metrics = {
            'Metric': [
                'Total Leads',
                'Vulnerability Segment (Manual + No Booking)',
                'SaaS Growth Segment',
                '',
                'Quality Metrics',
                'Average Digital Score (out of 100)',
                'Hot Leads',
                'Warm Leads',
                '',
                'Booking Status Distribution',
                'Manual Booking',
                'No Booking System',
                'SaaS Booking',
                '',
                'Lead Value Distribution',
                'Very High Value',
                'High Value',
                'Medium Value'
            ],
            'Count': [
                len(data),
                len(data[data['booking_status'].isin(['manual', 'none'])]),
                len(data[data['booking_status'] == 'saas']),
                '',
                '',
                f"{data['digital_score'].mean():.1f}",
                len(data[data['lead_temperature'] == 'hot']),
                len(data[data['lead_temperature'] == 'warm']),
                '',
                '',
                len(data[data['booking_status'] == 'manual']),
                len(data[data['booking_status'] == 'none']),
                len(data[data['booking_status'] == 'saas']),
                '',
                '',
                len(data[data['lead_value'] == 'very_high']),
                len(data[data['lead_value'] == 'high']),
                len(data[data['lead_value'] == 'medium'])
            ]
        }

    return pd.DataFrame(metrics)


def package_for_delivery():
    """Create 3 professional Excel packages"""

    qualified = pd.read_csv(OUTPUT_DIR / "qualified_leads.csv")

    # Deduplicate
    qualified = qualified.drop_duplicates(subset=['salon_name', 'website'])

    # City is already clean - no need to process
    # Just fill any missing with 'Florida'
    qualified['city'] = qualified['city'].fillna('Florida')

    # Parse list columns
    list_columns = ['emails', 'phones', 'instagram', 'facebook']
    for col in list_columns:
        if col in qualified.columns:
            qualified[col] = qualified[col].apply(safe_parse_list)

    # Priority scoring (for sorting only)
    temp_map = {'hot': 100, 'warm': 70, 'cold': 40, 'dead': 0}
    value_map = {'very_high': 100, 'high': 75, 'medium': 50, 'low': 25}

    qualified['priority_score'] = (
            qualified['digital_score'] * 0.4 +
            qualified['lead_temperature'].map(temp_map).fillna(0) * 0.3 +
            qualified['lead_value'].map(value_map).fillna(0) * 0.3
    ).round(1)

    # Best contact method
    def best_contact(row):
        if row.get('emails', ''):
            return 'Email'
        elif row.get('phones', ''):
            return 'Phone'
        elif row.get('instagram', ''):
            return 'Instagram DM'
        elif row.get('has_forms', False):
            return 'Website Form'
        else:
            return 'Website Only'

    qualified['best_contact_method'] = qualified.apply(best_contact, axis=1)

    # Sort by priority
    qualified = qualified.sort_values('priority_score', ascending=False)

    # Remove internal columns
    columns_to_remove = ['priority_score', 'reasons', 'processed_at']
    qualified = qualified.drop(columns=[col for col in columns_to_remove if col in qualified.columns])

    # Reorder columns - salon_name first, then city
    important_cols = ['salon_name', 'city', 'website', 'booking_status', 'booking_provider',
                      'digital_score', 'lead_temperature', 'lead_value', 'best_contact_method',
                      'emails', 'phones', 'instagram', 'facebook']

    other_cols = [col for col in qualified.columns if col not in important_cols]
    new_order = [col for col in important_cols if col in qualified.columns] + other_cols
    qualified = qualified[new_order]

    # Create segments
    vulnerability_leads = qualified[qualified['booking_status'].isin(['manual', 'none'])].copy()
    saas_growth_leads = qualified[qualified['booking_status'] == 'saas'].copy()
    complete_dataset = qualified.copy()

    timestamp = datetime.now().strftime("%Y%m%d")

    # Package 1: Vulnerability
    vuln_path = PACKAGES_DIR / f"1_Vulnerability_Leads_FL_{timestamp}.xlsx"
    with pd.ExcelWriter(vuln_path, engine='openpyxl') as writer:
        create_summary_sheet(vulnerability_leads, "Vulnerability").to_excel(writer, sheet_name='Summary', index=False)
        vulnerability_leads.to_excel(writer, sheet_name='All Leads', index=False)
        manual = vulnerability_leads[vulnerability_leads['booking_status'] == 'manual']
        none = vulnerability_leads[vulnerability_leads['booking_status'] == 'none']
        if len(manual) > 0:
            manual.to_excel(writer, sheet_name='Manual Booking', index=False)
        if len(none) > 0:
            none.to_excel(writer, sheet_name='No Booking', index=False)

    # Package 2: SaaS Growth
    saas_path = PACKAGES_DIR / f"2_SaaS_Growth_Leads_FL_{timestamp}.xlsx"
    with pd.ExcelWriter(saas_path, engine='openpyxl') as writer:
        create_summary_sheet(saas_growth_leads, "SaaS Growth").to_excel(writer, sheet_name='Summary', index=False)
        saas_growth_leads.to_excel(writer, sheet_name='All Leads', index=False)

    # Package 3: Complete
    complete_path = PACKAGES_DIR / f"3_Complete_Dataset_FL_{timestamp}.xlsx"
    with pd.ExcelWriter(complete_path, engine='openpyxl') as writer:
        create_summary_sheet(complete_dataset, "Complete").to_excel(writer, sheet_name='Summary', index=False)
        complete_dataset.to_excel(writer, sheet_name='All Leads', index=False)
        vulnerability_leads.to_excel(writer, sheet_name='Vulnerability Segment', index=False)
        saas_growth_leads.to_excel(writer, sheet_name='SaaS Segment', index=False)

    print(f"\n✅ 3 packages created: {PACKAGES_DIR}\n")


if __name__ == "__main__":
    package_for_delivery()
