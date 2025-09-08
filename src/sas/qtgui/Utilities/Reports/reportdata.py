from dataclasses import dataclass


@dataclass
class ReportData:
    html: str = "<html><body>No Data</body></html>"
    text: str = "No data"

