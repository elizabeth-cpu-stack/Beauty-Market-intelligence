# Save as check_crawl_failures.py
import csv

with open("data/raw/salons_stage1.csv", encoding="utf-8") as f:
    stage1 = list(csv.DictReader(f))

with open("data/output/unqualified_leads.csv", encoding="utf-8") as f:
    unqualified = list(csv.DictReader(f))

# Get the salons marked as 'no_website_data'
failed_crawls = [u for u in unqualified if "no_website_data" in u.get("reasons", "")]

# Match them back to stage1 to see their websites
failed_websites = []
for fail in failed_crawls:
    salon_name = fail.get("salon_name")
    match = next((s for s in stage1 if s.get("salon_name") == salon_name), None)
    if match:
        failed_websites.append(match.get("website"))

print("\n" + "="*60)
print(f"CRAWL FAILURES ANALYSIS (n={len(failed_crawls)})")
print("="*60)
print("\nFirst 20 failed websites:")
for i, site in enumerate(failed_websites[:20], 1):
    print(f"{i:2}. {site}")

# Look for patterns
fresha_redirects = sum(1 for w in failed_websites if "fresha.com" in w)
booksy_redirects = sum(1 for w in failed_websites if "booksy.com" in w)
square_redirects = sum(1 for w in failed_websites if "square.site" in w)
glossgenius = sum(1 for w in failed_websites if "glossgenius.com" in w)

print(f"\nREDIRECT PATTERNS:")
print(f"  Fresha redirects: {fresha_redirects}")
print(f"  Booksy redirects: {booksy_redirects}")
print(f"  Square redirects: {square_redirects}")
print(f"  GlossGenius: {glossgenius}")
print(f"  Total SaaS-hosted: {fresha_redirects + booksy_redirects + square_redirects + glossgenius}")
print("="*60 + "\n")


