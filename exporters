from typing import List, Dict, Union
from pathlib import Path
import csv


class CSVExporter:

    @staticmethod
    def export(path: Union[str, Path], records: List[Dict]) -> None:
        if not records:
            return

        path = Path(path)

        fieldnames = list(records[0].keys())

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
