from app.providers.threads.client import ThreadsCredentialContext, ThreadsClient
from app.providers.threads.connector import ThreadsSourceConnector
from app.providers.threads.normalizer import ThreadsNormalizer


def test_normalizes_thread_to_canonical_source_item():
    raw = {
        "id": "t1",
        "text": "Hello Threads",
        "timestamp": "2026-09-24T08:00:00+0000",
        "permalink": "https://www.threads.net/@demo/post/t1",
        "username": "demo",
        "media_type": "TEXT_POST",
        "has_replies": True,
        "is_reply": False,
    }

    item = ThreadsNormalizer().normalize(
        raw,
        organization_id="org-1",
        user_account_id="account-1",
    )

    assert item.provider == "threads"
    assert item.resource_type == "post"
    assert item.external_id == "t1"
    assert item.content == "Hello Threads"
    assert item.author == "demo"
    assert item.source_url.endswith("/t1")
    assert item.source_checksum


def test_normalizes_reply_parent_relationship():
    raw = {
        "id": "r1",
        "text": "Reply",
        "timestamp": "2026-09-24T08:01:00+0000",
        "permalink": "https://www.threads.net/@demo/post/r1",
        "username": "demo",
        "root_post": {"id": "t1"},
        "replied_to": {"id": "t1"},
        "is_reply": True,
    }

    item = ThreadsNormalizer().normalize(
        raw,
        organization_id="org-1",
        user_account_id="account-1",
        resource_type="reply",
    )

    assert item.resource_type == "reply"
    assert item.external_id == "r1"
    assert item.parent_external_id == "t1"


def test_connector_normalizes_owned_post_page_and_preserves_cursor():
    payload = {
        "data": [
            {
                "id": "t1",
                "text": "Hello",
                "timestamp": "2026-09-24T08:00:00+0000",
                "permalink": "https://www.threads.net/@demo/post/t1",
                "username": "demo",
            }
        ],
        "paging": {"cursors": {"after": "opaque-next"}},
    }

    def transport(**kwargs):
        assert kwargs["url"].endswith("graph.threads.net/me/threads")
        assert kwargs["params"]["access_token"] == "secret-token"
        return payload

    connector = ThreadsSourceConnector(
        ThreadsClient(transport=transport)
    )
    page = connector.list_owned_posts(
        credential=ThreadsCredentialContext(access_token="secret-token"),
        organization_id="org-1",
        user_account_id="account-1",
    )

    assert len(page.items) == 1
    assert page.items[0].external_id == "t1"
    assert page.next_cursor == "opaque-next"


def test_connector_normalizes_reply_page():
    payload = {
        "data": [
            {
                "id": "r1",
                "text": "Reply",
                "timestamp": "2026-09-24T08:01:00+0000",
                "permalink": "https://www.threads.net/@demo/post/r1",
                "username": "demo",
                "root_post": {"id": "t1"},
                "replied_to": {"id": "t1"},
                "is_reply": True,
            }
        ],
        "paging": {"cursors": {"after": "next-reply"}},
    }

    connector = ThreadsSourceConnector(ThreadsClient(transport=lambda **_: payload))
    page = connector.fetch_replies(
        credential=ThreadsCredentialContext(access_token="token"),
        organization_id="org-1",
        user_account_id="account-1",
        thread_id="t1",
    )

    assert page.items[0].parent_external_id == "t1"
    assert page.next_cursor == "next-reply"
