import csv
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "output"

UNQUALIFIED = OUTPUT_DIR / "unqualified_leads.csv"

with open(UNQUALIFIED, encoding="utf-8") as f:
    unqualified = list(csv.DictReader(f))

# Count failure reasons
reasons = []
for lead in unqualified:
    r = lead.get("reasons", "")
    reasons.append(r)

print("\n" + "="*60)
print("FAILURE REASON BREAKDOWN")
print("="*60)
for reason, count in Counter(reasons).most_common():
    pct = count/len(unqualified)*100
    print(f"{reason:30} {count:4} ({pct:5.1f}%)")

# Check scores
scores = [int(lead.get("digital_score", 0)) for lead in unqualified]
print(f"\nAverage score of unqualified: {sum(scores)/len(scores):.1f}")
print(f"Scores >=30: {sum(1 for s in scores if s >= 30)} ({sum(1 for s in scores if s >= 30)/len(scores)*100:.1f}%)")
print(f"Total unqualified: {len(unqualified)}")
print("="*60 + "\n")
