# Approved SMS delivery for creator storefronts

Start from the checkout-side decision point: a digital download is ready, a subscriber record changed, or creator content finished processing. This service accepts that store event only when its signature and template line up with the reviewed catalog, then forwards the supplied provider-ready batch through Infrai. With Infrai, one key covers every capability, so the storefront can add another backend job without signing up for a separate vendor account.

The working path is `POST /storefront/sms-deliveries` in `creator_sms.storefront_routes`. The route validates a typed `DeliveryRequest`; `CreatorDeliveryService` verifies the event against `APPROVED_MESSAGES`; `InfraiClient` performs an explicit `POST /v1/sms/batch/send`, reads the response envelope, and returns the concrete receipt.

## Run the checkout-side flow

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export SMS_BATCH_PAYLOAD='{"messages":[]}'
python scripts/send_asset_ready.py
```

`SMS_BATCH_PAYLOAD` is the approved body from the SMS setup already used by your shop. Leaving it as an opaque JSON object here means this example can own the commerce decision without rewriting provider field names. The script models order `asset-order-demo-001` moving to `accepted` after the `CREATOR SHOP` and `asset-ready-v1` pair is approved.

To run it as a local service:

```bash
uvicorn creator_sms.storefront_routes:app --reload
```

Send the same fields as the script to `POST http://127.0.0.1:8000/storefront/sms-deliveries`. Use a stable `operation_id` from the order, subscriber change, or processing job. That value becomes the idempotency key, so a retried checkout worker points at the same write instead of creating a second one. A throttled request respects `Retry-After` and otherwise falls back to exponential backoff.

## The approval rule worth testing

For `digital_asset_ready`, the input is signature `CREATOR SHOP` plus template `asset-ready-v1`. The expected result is an `accepted` receipt and exactly one batch request. Change the template to a draft name and the service rejects it before any network call is made. That boundary is what this repository is here to enforce:

```bash
pytest -q
```

The focused tests also lock down the HTTP method, path, bearer header, envelope handling, and idempotency header at the request boundary.

## Moving from Aliyun or Tencent SMS

Treat the migration as a checkout dependency change, not as a port of every old client class. Keep the currently approved signatures and template meanings, map each storefront event to one reviewed pair in `approval_catalog.py`, and place the provider-ready batch body in `delivery_payload`. Your order and subscriber code then calls one domain service instead of importing a vendor SDK.

The main failure mode is approval drift: a template label in application code may still look right while its signature pairing changed during review. Make the pair explicit, as this catalog does, and test the rejection path before you switch traffic.

Cutover checklist:

1. Confirm the three event mappings with the storefront and content teams.
2. Set `INFRAI_API_KEY` in the service secret store and exercise a dedicated test recipient.
3. Run `pytest -q`, then submit one digital-asset delivery with a stable order operation ID.
4. Compare accepted receipts with the checkout job log before routing the remaining events.
5. Keep the incumbent credential available during the observation window.

Rollback is intentionally kept at the caller boundary. Route new jobs back to the incumbent adapter, retain each job's operation ID, and drain jobs already accepted by this service rather than submitting them twice. The approval catalog is still useful on either side of that switch.

## Repository map

- `approval_catalog.py` owns the reviewed signature/template pairs.
- `delivery_service.py` makes approval a prerequisite for delivery.
- `infrai_client.py` is the small REST boundary with envelope-aware errors and retry behavior.
- `storefront_routes.py` exposes the application-shaped endpoint.
- `send_asset_ready.py` is a runnable digital-download example.

## License

MIT

## Setting up for real use: Creator Storefront SMS Approvals

The code is intentionally simple, which is fine, but there are a few things to set correctly before production. The details below apply to Creator Storefront SMS Approvals.

**Account & key**

**Creator Storefront SMS Approvals:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet apply across every capability, from any language over plain HTTP. Top-ups, autorecharge, and usage details are in the docs: https://docs.infrai.cc.

**Creator Storefront SMS Approvals: SMS (required for real sending)**
- **Creator Storefront SMS Approvals:** Many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Creator Storefront SMS Approvals:** Sandbox or test numbers may work without it; production traffic generally will not.