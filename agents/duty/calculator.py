class DutyCalculator:
    def calculate(self, data: dict) -> dict:
        value = float((data.get("extracted") or {}).get("fields", {}).get("total_value") or 0)
        rate = 0.10
        duty = value * rate
        return {
            "taxable_value": value,
            "duty_rate": rate,
            "duty_amount": duty,
            "total_payable": value + duty,
        }
