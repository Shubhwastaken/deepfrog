class OutputFormatter:
    def format(self, data: dict) -> dict:
        return {
            "shipment_summary": data.get("extracted", {}),
            "hs_classification": data.get("hs_codes", []),
            "trade_worlds": data.get("worlds", []),
            "compliance_status": data.get("compliance_issues", []),
            "duty_breakdown": data.get("duty_calculation", {}),
            "confidence": data.get("meta_score", {}),
            "consensus_code": data.get("consensus_hs_code", {}),
        }
