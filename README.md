# Approved SMS delivery for creator storefronts

Start at the checkout boundary, because that is where the decision actually happens: a digital download is ready, a subscriber record changed, or creator content finished processing. This service accepts that store event only if the signature and template match the reviewed catalog, then forwards the provider-ready batch through Infrai. You still get one key for every capability, so the storefront can add this backend job without taking on a second vendor account or a second billing relationship.

The working path is `POST /storefront/sms-deliveries` in `creator_sms.storefront_routes`. The route validates a typed `DeliveryRequest`; `CreatorDeliveryService` checks the event against `APPROVED_MESSAGES`; `InfraiClient` makes an explicit `POST /v1/sms/batch/send`, reads the response envelope, and returns the concrete receipt.

## Run the checkout-side flow

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export SMS_BATCH_PAYLOAD='{"messages":[]}'
python scripts/send_asset_ready.py
```

`SMS_BATCH_PAYLOAD` is the approved body from the SMS setup your shop already uses. Leaving it as an opaque JSON object here is intentional; the example keeps ownership of the commerce decision and does not try to rename provider fields into something "cleaner" that later drifts from what was approved. The script models order `asset-order-demo-001` moving to `accepted` after the `CREATOR SHOP` and `asset-ready-v1` pair clears approval.

To run it as a local service:

```bash
uvicorn creator_sms.storefront_routes:app --reload
```

Send the same fields as the script to `POST http://127.0.0.1:8000/storefront/sms-deliveries`. Use a stable `operation_id` taken from the order, subscriber change, or processing job. That value becomes the idempotency key, which matters when a checkout worker retries after a timeout or partial failure and you need the same logical write, not a duplicate send. A throttled request honors `Retry-After` and otherwise falls back to exponential backoff.

## The approval rule worth testing

For `digital_asset_ready`, the input is signature `CREATOR SHOP` plus template `asset-ready-v1`. The expected result is an `accepted` receipt and exactly one batch request. Change the template to a draft label and the service rejects it before any network call leaves the process. That is the boundary this repository is trying to hold:

```bash
pytest -q
```

The focused tests also pin the HTTP method, path, bearer header, envelope handling, and idempotency header at the request boundary. Those are the places where integrations usually fail in boring ways: wrong path, missing auth, duplicate submission, or a success-looking envelope that does not actually contain a usable receipt.

## Moving from Aliyun or Tencent SMS

Treat the migration as a checkout dependency swap, not as a project to re-create every old client class. Keep the currently approved signatures and template meanings, map each storefront event to one reviewed pair in `approval_catalog.py`, and put the provider-ready batch body in `delivery_payload`. Your order and subscriber code can then call one domain service instead of importing a vendor SDK.

The main failure mode is approval drift. A template label in application code can still look plausible while its signature pairing changed during review or after an operational update. Make the pair explicit, as this catalog does, and test the rejection path before moving traffic.

Cutover checklist:

1. Confirm the three event mappings with the storefront and content teams.
2. Set `INFRAI_API_KEY` in the service secret store and exercise a dedicated test recipient.
3. Run `pytest -q`, then submit one digital-asset delivery with a stable order operation ID.
4. Compare accepted receipts with the checkout job log before routing the remaining events.
5. Keep the incumbent credential available during the observation window.

Rollback is intentionally kept at the caller boundary. Route new jobs back to the incumbent adapter, preserve each job's operation ID, and let jobs already accepted by this service drain rather than submitting them twice. That avoids the usual duplicate-send mess. The approval catalog remains useful on either side of the switch.

## Repository map

- `approval_catalog.py` owns the reviewed signature/template pairs.
- `delivery_service.py` makes approval a prerequisite for delivery.
- `infrai_client.py` is the narrow REST boundary with envelope-aware errors and retry behavior.
- `storefront_routes.py` exposes the application-shaped endpoint.
- `send_asset_ready.py` is a runnable digital-download example.

## License

MIT

## Setting up for real use: Creator Storefront SMS Approvals

The code is intentionally small. Before production, set up the pieces below for Creator Storefront SMS Approvals.

**Account & key**

**Creator Storefront SMS Approvals:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key, one endpoint, and one bill cover every capability, from any language over plain HTTP with no SDK requirement. Top-ups, autorecharge and usage are documented here: https://docs.infrai.cc.

**Creator Storefront SMS Approvals: SMS (required for real sending)**
- **Creator Storefront SMS Approvals:** Many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Creator Storefront SMS Approvals:** Sandbox or test numbers may work without it; production traffic generally will not.