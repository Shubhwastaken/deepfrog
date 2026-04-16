class MetaScorer:
    def score(self, data: dict) -> dict:
        scores = [c["confidence"] for c in data.get("hs_codes", []) if "confidence" in c]
        avg = sum(scores) / len(scores) if scores else 0
        return {
            "overall_confidence": round(avg, 3),
            "recommendation": "proceed" if avg > 0.7 else "manual_review"
        }
