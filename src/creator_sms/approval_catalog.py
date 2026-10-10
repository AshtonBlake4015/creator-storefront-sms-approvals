from dataclasses import dataclass

from .models import DeliveryRequest, StoreEvent


class ApprovalRejected(ValueError):
    pass


@dataclass(frozen=True)
class ApprovedMessage:
    signature: str
    template_name: str


APPROVED_MESSAGES: dict[StoreEvent, ApprovedMessage] = {
    StoreEvent.DIGITAL_ASSET_READY: ApprovedMessage("CREATOR SHOP", "asset-ready-v1"),
    StoreEvent.SUBSCRIBER_UPDATED: ApprovedMessage("CREATOR SHOP", "subscriber-update-v1"),
    StoreEvent.CONTENT_PROCESSED: ApprovedMessage("CREATOR STUDIO", "content-ready-v1"),
}


def require_approved(request: DeliveryRequest) -> ApprovedMessage:
    approved = APPROVED_MESSAGES[request.event]
    if (request.signature, request.template_name) != (
        approved.signature,
        approved.template_name,
    ):
        raise ApprovalRejected(
            f"{request.event.value} must use its approved signature and template"
        )
    return approved

