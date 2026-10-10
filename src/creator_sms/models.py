from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StoreEvent(str, Enum):
    DIGITAL_ASSET_READY = "digital_asset_ready"
    SUBSCRIBER_UPDATED = "subscriber_updated"
    CONTENT_PROCESSED = "content_processed"


class DeliveryRequest(BaseModel):
    storefront_id: str = Field(min_length=1)
    event: StoreEvent
    signature: str = Field(min_length=1)
    template_name: str = Field(min_length=1)
    delivery_payload: dict[str, Any] = Field(
        description="Provider-ready body for the SMS batch endpoint"
    )
    operation_id: str = Field(min_length=1)


class DeliveryReceipt(BaseModel):
    operation_id: str
    status: str
    result: dict[str, Any]

