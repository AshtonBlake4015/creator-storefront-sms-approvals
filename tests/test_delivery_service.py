import httpx
import pytest

from creator_sms.approval_catalog import ApprovalRejected
from creator_sms.delivery_service import CreatorDeliveryService
from creator_sms.infrai_client import InfraiClient
from creator_sms.models import DeliveryRequest, StoreEvent


def request_for(template_name: str = "asset-ready-v1") -> DeliveryRequest:
    return DeliveryRequest(
        storefront_id="shop-42",
        event=StoreEvent.DIGITAL_ASSET_READY,
        signature="CREATOR SHOP",
        template_name=template_name,
        delivery_payload={},
        operation_id="asset-order-42",
    )


def test_unapproved_template_never_reaches_delivery_client() -> None:
    class RecordingClient:
        called = False

        def sms_batch_send(self, payload: dict, operation_id: str) -> dict:
            self.called = True
            return {}

    client = RecordingClient()
    service = CreatorDeliveryService(client)  # type: ignore[arg-type]

    with pytest.raises(ApprovalRejected):
        service.deliver(request_for("draft-asset-template"))

    assert client.called is False


def test_approved_delivery_uses_post_envelope_and_idempotency_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/sms/batch/send"
        assert request.headers["Idempotency-Key"] == "asset-order-42"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(200, json={"ok": True, "data": {"accepted": 1}})

    client = InfraiClient(api_key="test-key", transport=httpx.MockTransport(handler))
    try:
        receipt = CreatorDeliveryService(client).deliver(request_for())
    finally:
        client.close()

    assert receipt.status == "accepted"
    assert receipt.result == {"accepted": 1}
