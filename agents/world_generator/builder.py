class WorldBuilder:
    def generate(self, data: dict) -> list:
        return [
            {"world_id": "W1", "route": "direct", "estimated_duty_rate": 0.05},
            {"world_id": "W2", "route": "via_fta", "estimated_duty_rate": 0.0},
            {"world_id": "W3", "route": "bonded_warehouse", "estimated_duty_rate": 0.03},
        ]
