from fastapi import Depends, FastAPI, HTTPException

from .approval_catalog import ApprovalRejected
from .delivery_service import CreatorDeliveryService
from .infrai_client import InfraiClient, InfraiError
from .models import DeliveryReceipt, DeliveryRequest

app = FastAPI(title="Creator storefront SMS approvals")


def get_delivery_service() -> CreatorDeliveryService:
    return CreatorDeliveryService(InfraiClient())


@app.post("/storefront/sms-deliveries", response_model=DeliveryReceipt)
def create_delivery(
    request: DeliveryRequest,
    service: CreatorDeliveryService = Depends(get_delivery_service),
) -> DeliveryReceipt:
    try:
        return service.deliver(request)
    except ApprovalRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc

