# Save as analyze_qualified.py in project root
import csv
from collections import Counter

with open("data/output/qualified_leads.csv", encoding="utf-8") as f:
    qualified = list(csv.DictReader(f))

print("\n" + "="*60)
print(f"QUALIFIED LEADS ANALYSIS (n={len(qualified)})")
print("="*60)

# Booking status breakdown
booking_statuses = [lead.get("booking_status", "unknown") for lead in qualified]
print("\nBOOKING STATUS:")
for status, count in Counter(booking_statuses).most_common():
    pct = count/len(qualified)*100
    print(f"  {status:15} {count:4} ({pct:5.1f}%)")

# Score distribution
scores = [int(lead.get("digital_score", 0)) for lead in qualified]
print(f"\nDIGITAL SCORES:")
print(f"  Average: {sum(scores)/len(scores):.1f}")
print(f"  Range: {min(scores)} - {max(scores)}")
print(f"  30-49: {sum(1 for s in scores if 30 <= s < 50)} ({sum(1 for s in scores if 30 <= s < 50)/len(scores)*100:.1f}%)")
print(f"  50-69: {sum(1 for s in scores if 50 <= s < 70)} ({sum(1 for s in scores if 50 <= s < 70)/len(scores)*100:.1f}%)")
print(f"  70+:   {sum(1 for s in scores if s >= 70)} ({sum(1 for s in scores if s >= 70)/len(scores)*100:.1f}%)")

# Temperature
temps = [lead.get("lead_temperature", "unknown") for lead in qualified]
print(f"\nLEAD TEMPERATURE:")
for temp, count in Counter(temps).most_common():
    pct = count/len(qualified)*100
    print(f"  {temp:10} {count:4} ({pct:5.1f}%)")

# Value
values = [lead.get("lead_value", "unknown") for lead in qualified]
print(f"\nLEAD VALUE:")
for val, count in Counter(values).most_common():
    pct = count/len(qualified)*100
    print(f"  {val:15} {count:4} ({pct:5.1f}%)")

# High-value targets (no booking but good infrastructure)
high_value_no_booking = [
    lead for lead in qualified
    if lead.get("booking_status") == "none"
    and int(lead.get("digital_score", 0)) >= 40
]
print(f"\nHIGH-VALUE TARGETS (no booking, score ≥40): {len(high_value_no_booking)} ({len(high_value_no_booking)/len(qualified)*100:.1f}%)")

print("="*60 + "\n")
