class HSClassifier:
    def classify(self, description: str) -> list:
        # Integrate WCO HS database + LLM in production
        return [
            {"code": "8471.30", "confidence": 0.92, "description": "Portable digital ADP machines"},
            {"code": "8471.41", "confidence": 0.75, "description": "Other ADP machines"},
        ]
