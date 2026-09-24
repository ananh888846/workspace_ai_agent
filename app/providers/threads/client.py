from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.providers.meta.credentials import MetaCredentialContext


class ThreadsProviderError(RuntimeError):
    """Normalized provider error raised by the Threads client."""

    def __init__(self, code: str, message: str | None = None) -> None:
        super().__init__(message or code)
        self.code = code


# Backward-compatible provider name; the actual credential boundary is MetaCredentialContext.
ThreadsCredentialContext = MetaCredentialContext


class ThreadsClient:
    """Small provider HTTP boundary for read-oriented Threads operations."""

    def __init__(
        self,
        *,
        base_url: str = "https://graph.threads.net",
        timeout: float = 30.0,
        transport: Callable[..., Any] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._transport = transport

    def _get(self, *, path: str, credential: ThreadsCredentialContext, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._transport is None:
            from urllib.error import HTTPError, URLError
            from urllib.parse import urlencode
            from urllib.request import Request, urlopen

            query = dict(params or {})
            query["access_token"] = credential.access_token
            url = f"{self.base_url}{path}?{urlencode(query)}"
            request = Request(url, method="GET", headers={"Accept": "application/json"})
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    import json
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                if exc.code in (401, 403):
                    raise ThreadsProviderError("authorization_denied") from exc
                if exc.code == 404:
                    raise ThreadsProviderError("resource_not_found") from exc
                if exc.code == 429:
                    raise ThreadsProviderError("rate_limited") from exc
                raise ThreadsProviderError("provider_unavailable") from exc
            except (URLError, TimeoutError, OSError) as exc:
                raise ThreadsProviderError("provider_unavailable") from exc
            except (ValueError, UnicodeDecodeError) as exc:
                raise ThreadsProviderError("internal_error") from exc

        try:
            payload = self._transport(
                method="GET",
                url=f"{self.base_url}{path}",
                params={**(params or {}), "access_token": credential.access_token},
                timeout=self.timeout,
            )
        except ThreadsProviderError:
            raise
        except TimeoutError as exc:
            raise ThreadsProviderError("provider_unavailable") from exc
        except Exception as exc:
            raise ThreadsProviderError("provider_unavailable") from exc

        if not isinstance(payload, dict):
            raise ThreadsProviderError("internal_error")
        return payload

    def get_thread(self, *, thread_id: str, credential: ThreadsCredentialContext, fields: str) -> dict[str, Any]:
        return self._get(path=f"/{thread_id}", credential=credential, params={"fields": fields})

    def get_replies(
        self,
        *,
        thread_id: str,
        credential: ThreadsCredentialContext,
        fields: str,
        after: str | None = None,
        reverse: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"fields": fields, "reverse": str(reverse).lower()}
        if after:
            params["after"] = after
        return self._get(path=f"/{thread_id}/replies", credential=credential, params=params)

    def list_owned_threads(
        self,
        *,
        credential: ThreadsCredentialContext,
        fields: str,
        after: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"fields": fields}
        if after:
            params["after"] = after
        return self._get(path="/me/threads", credential=credential, params=params)
