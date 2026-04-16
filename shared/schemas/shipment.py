from pydantic import BaseModel
from typing import Optional

class ShipmentSchema(BaseModel):
    shipper_name: Optional[str] = None
    consignee_name: Optional[str] = None
    origin_country: Optional[str] = None
    destination_country: Optional[str] = None
    invoice_number: Optional[str] = None
    total_value: Optional[float] = None
    currency: Optional[str] = "USD"
    goods_description: Optional[str] = None
    quantity: Optional[float] = None
    weight: Optional[float] = None
