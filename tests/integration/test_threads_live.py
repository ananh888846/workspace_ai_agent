import os

import pytest

from app.providers.threads.client import ThreadsClient, ThreadsCredentialContext
from app.providers.threads.connector import ThreadsSourceConnector


@pytest.mark.integration
def test_live_threads_owned_posts_smoke():
    if os.getenv("RUN_THREADS_LIVE_SMOKE") != "1":
        pytest.skip("set RUN_THREADS_LIVE_SMOKE=1 to run live Threads smoke test")

    token = os.getenv("THREADS_SMOKE_ACCESS_TOKEN")
    if not token:
        pytest.fail("THREADS_SMOKE_ACCESS_TOKEN is required for the live smoke test")

    connector = ThreadsSourceConnector(ThreadsClient())
    page = connector.list_owned_posts(
        credential=ThreadsCredentialContext(access_token=token),
        organization_id=os.getenv("THREADS_SMOKE_ORG_ID", "smoke-org"),
        user_account_id=os.getenv("THREADS_SMOKE_ACCOUNT_ID", "smoke-account"),
    )

    assert isinstance(page.items, tuple)
    assert page.next_cursor is None or isinstance(page.next_cursor, str)
