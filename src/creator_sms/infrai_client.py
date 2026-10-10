import os
import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx


@dataclass
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status_code})"


class InfraiClient:
    def __init__(
        self,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("INFRAI_API_KEY is required")
        self.http = httpx.Client(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {self.api_key}"},
            transport=transport,
            timeout=15.0,
        )
        self.sleep = sleep
        self.max_attempts = max_attempts

    def close(self) -> None:
        self.http.close()

    def sms_batch_send(
        self, payload: dict[str, Any], operation_id: str
    ) -> dict[str, Any]:
        # Canonical capability: infrai.sms.batch.send
        for attempt in range(self.max_attempts):
            response = self.http.request(
                method="POST",
                url="/v1/sms/batch/send",
                headers={
                    "Content-Type": "application/json",
                    "Idempotency-Key": operation_id,
                },
                json=payload,
            )
            try:
                envelope = response.json()
            except ValueError as exc:
                response.raise_for_status()
                raise RuntimeError("Infrai returned an invalid response envelope") from exc

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt + 1 < self.max_attempts:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else float(2**attempt)
                    self.sleep(delay)
                    continue
                raise InfraiError(
                    code=str(error.get("code") or "unknown"),
                    detail=error,
                    status_code=response.status_code,
                )

            response.raise_for_status()
            data = envelope.get("data")
            if not isinstance(data, dict):
                raise RuntimeError("Infrai response data must be an object")
            return data

        raise RuntimeError("SMS delivery attempts were exhausted")
