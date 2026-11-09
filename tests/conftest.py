import pytest
import requests

from grouper_client.grouper_client import GrouperClient

STEM = "test:stem"


class RecordingClient(GrouperClient):
    """
    A client whose transport records each request and answers from a list, in order.

    An answer that is an exception is raised instead of returned, as the real transport raises
    requests' HTTPError for a 4xx or 5xx status.
    """

    def __init__(self, *answers):
        super().__init__(base_url="https://grouper.example.edu/", entity_id="test", key_path="unused", stem=STEM)
        self.answers = list(answers)
        self.sent = []

    def _answer(self, method, endpoint, payload):
        self.sent.append((method, endpoint, payload))
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    def _send_post_request(self, endpoint, payload, headers=None, skip_auth=False):
        return self._answer("POST", endpoint, payload)

    def _send_delete_request(self, endpoint, body=None, retries=0):
        return self._answer("DELETE", endpoint, body)


def http_error(status):
    """The HTTPError the transport raises for a response with this status."""
    response = requests.Response()
    response.status_code = status
    return requests.HTTPError(f"{status} Client Error", response=response)


@pytest.fixture
def grouper_answering():
    """Make a RecordingClient that answers with these responses or errors, in order."""
    return RecordingClient
