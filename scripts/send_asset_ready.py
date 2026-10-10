import json
import os

from creator_sms.delivery_service import CreatorDeliveryService
from creator_sms.infrai_client import InfraiClient
from creator_sms.models import DeliveryRequest, StoreEvent


def main() -> None:
    raw_payload = os.environ.get("SMS_BATCH_PAYLOAD")
    if not raw_payload:
        raise RuntimeError("SMS_BATCH_PAYLOAD is required")

    request = DeliveryRequest(
        storefront_id="shop-demo",
        event=StoreEvent.DIGITAL_ASSET_READY,
        signature="CREATOR SHOP",
        template_name="asset-ready-v1",
        delivery_payload=json.loads(raw_payload),
        operation_id="asset-order-demo-001",
    )
    client = InfraiClient()
    try:
        receipt = CreatorDeliveryService(client).deliver(request)
        print(receipt.model_dump_json(indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()

