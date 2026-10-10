from .approval_catalog import require_approved
from .infrai_client import InfraiClient
from .models import DeliveryReceipt, DeliveryRequest


class CreatorDeliveryService:
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def deliver(self, request: DeliveryRequest) -> DeliveryReceipt:
        require_approved(request)
        result = self.client.sms_batch_send(
            request.delivery_payload,
            operation_id=request.operation_id,
        )
        return DeliveryReceipt(
            operation_id=request.operation_id,
            status="accepted",
            result=result,
        )

