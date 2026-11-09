"""
The transport's retries: a request refused for an expired token is sent again with a new one, and
one that times out is sent again, up to RETRIES more times. Either way the answer is the retry's.
"""

import json

import pytest
import requests

from grouper_client.abstract_client import RETRIES
from grouper_client.grouper_client import GrouperClient


def response(status, body):
    answer = requests.Response()
    answer.status_code = status
    answer._content = json.dumps(body).encode()
    answer.url = "https://grouper.example.edu/groups"
    return answer


@pytest.fixture
def client(monkeypatch):
    grouper = GrouperClient(base_url="https://grouper.example.edu/", entity_id="test", key_path="unused", stem="s")
    grouper.renewals = 0

    def renew_token(refresh_token="NA"):
        grouper.renewals += 1
        grouper.token = f"fresh-{grouper.renewals}"

    monkeypatch.setattr(grouper, "renew_token", renew_token)
    grouper.token = "expired"
    return grouper


@pytest.fixture
def answer_in_turn(monkeypatch):
    """Make requests give these answers in order, raising any that are exceptions; returns what was sent."""
    sent = []

    def answering(*answers):
        queue = list(answers)

        def fake_request(method, url, **kwargs):
            sent.append({"method": method, "url": url, **kwargs})
            answer = queue.pop(0)
            if isinstance(answer, Exception):
                raise answer
            return answer

        def not_this_way(*args, **kwargs):
            raise AssertionError("requests should be sent with requests.request")

        monkeypatch.setattr(requests, "request", fake_request)
        monkeypatch.setattr(requests, "get", not_this_way)
        monkeypatch.setattr(requests, "delete", not_this_way)
        return sent

    return answering


@pytest.mark.parametrize("status", [401, 403])
def test_a_request_refused_for_an_expired_token_is_resent_with_a_new_one(client, answer_in_turn, status):
    sent = answer_in_turn(response(status, {"error": "expired"}), response(200, {"ok": True}))

    assert client._send_post_request("groups", {"x": 1}) == {"ok": True}
    assert client.renewals == 1
    assert [request["headers"]["Authorization"] for request in sent] == ["Bearer expired", "Bearer fresh-1"]
    assert sent[1]["json"] == {"x": 1}


def test_a_request_still_refused_after_the_retries_raises(client, answer_in_turn):
    answer_in_turn(*[response(401, {"error": "expired"})] * (RETRIES + 1))

    with pytest.raises(requests.HTTPError):
        client._send_post_request("groups", {"x": 1})
    assert client.renewals == RETRIES


def test_other_http_errors_are_not_retried(client, answer_in_turn):
    sent = answer_in_turn(response(500, {"error": "boom"}))

    with pytest.raises(requests.HTTPError):
        client._send_post_request("groups", {"x": 1})
    assert len(sent) == 1


def test_a_request_that_times_out_is_retried(client, answer_in_turn):
    sent = answer_in_turn(requests.Timeout("read timed out"), response(200, {"ok": True}))

    assert client._send_post_request("groups", {"x": 1}) == {"ok": True}
    assert len(sent) == 2


def test_a_request_that_keeps_timing_out_raises(client, answer_in_turn):
    sent = answer_in_turn(*[requests.Timeout("read timed out")] * (RETRIES + 1))

    with pytest.raises(requests.Timeout):
        client._send_post_request("groups", {"x": 1})
    assert len(sent) == RETRIES + 1


def test_a_get_is_retried_the_same_way(client, answer_in_turn):
    sent = answer_in_turn(response(401, {"error": "expired"}), response(200, {"ok": True}))

    assert client._send_get_request("groups", {"q": "x"}) == {"ok": True}
    assert [request["method"] for request in sent] == ["GET", "GET"]
    assert sent[1]["params"] == {"q": "x"}


def test_a_delete_without_a_body_is_retried_the_same_way(client, answer_in_turn):
    sent = answer_in_turn(requests.Timeout("read timed out"), response(200, {}))

    assert client._send_delete_request("groups/x") == {"status": 200}
    assert [request["method"] for request in sent] == ["DELETE", "DELETE"]
