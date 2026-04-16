import os, json

class PDFGenerator:
    def generate(self, data: dict) -> str:
        os.makedirs("reports", exist_ok=True)
        path = f"reports/report_{data.get('job_id', 'unknown')}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path  # Replace with reportlab PDF generation in production
