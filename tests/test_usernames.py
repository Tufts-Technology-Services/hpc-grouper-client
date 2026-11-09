"""
Usernames come from the subject's uid attribute, which Grouper returns when asked for it.

They used to be parsed from the description, "Display Name (username)", but Grouper sends the
display name first by default, and a display name can have parentheses of its own: for
"Kim(Jiwoo) Park", whose description is "Kim(Jiwoo) Park (kpark12)", that gave "Jiwoo".

The responses below follow the shape Grouper 6.4 returned in probes on 2026-11-09, with made-up
people, ids and group names.
"""

import pytest

from grouper_client.grouper_client import GrouperClient

JIWOO = ["Kim(Jiwoo) Park", "Kim(Jiwoo) Park (kpark12)"]


def subject(subject_id, attribute_values, name):
    return {
        "resultCode": "SUCCESS",
        "success": "T",
        "memberId": f"member-{subject_id}",
        "id": subject_id,
        "name": name,
        "sourceId": "tuftsedutrunk_SubSourceID",
        "attributeValues": attribute_values,
    }


class RecordingClient(GrouperClient):
    """A client that records the request it would send and answers with a canned response."""

    def __init__(self, response):
        super().__init__(base_url="https://grouper.example.edu/", entity_id="test", key_path="unused", stem="test:stem")
        self.response = response
        self.sent = None

    def _send_post_request(self, endpoint, payload):
        self.sent = payload
        return self.response


def test_group_members_are_read_from_their_uid():
    response = {
        "WsGetMembersResults": {
            "subjectAttributeNames": ["uid"],
            "resultMetadata": {"resultCode": "SUCCESS", "success": "T"},
            "results": [
                {
                    "wsSubjects": [
                        subject("9A1F0C3E5B7D4E2A8C6B0D1E3F5A7C9B", ["kpark12"], "Kim(Jiwoo) Park"),
                        subject("1B3D5F7A9C2E4A6C8E0B2D4F6A8C0E2D", ["edover02"], "Eileen Dover"),
                    ]
                }
            ],
        }
    }
    client = RecordingClient(response)

    members = client.get_group_members("lab_grp")

    request = client.sent["WsRestGetMembersRequest"]
    assert request["subjectAttributeNames"] == ["uid"]
    # without subject detail, Grouper sends only the attributes asked for
    assert request["includeSubjectDetail"] == "F"
    assert members == {"9A1F0C3E5B7D4E2A8C6B0D1E3F5A7C9B": "kpark12", "1B3D5F7A9C2E4A6C8E0B2D4F6A8C0E2D": "edover02"}


def test_a_member_without_a_uid_has_no_username():
    response = {
        "WsGetMembersResults": {
            "subjectAttributeNames": ["uid"],
            "results": [{"wsSubjects": [subject("5C7E9A1B3D5F7A9C2E4A6C8E0B2D4F6A", [""], "Service Account")]}],
        }
    }

    members = RecordingClient(response).get_group_members("lab_grp")

    assert members == {"5C7E9A1B3D5F7A9C2E4A6C8E0B2D4F6A": None}


def test_the_uid_is_found_among_other_attributes():
    response = {
        "WsGetMembersResults": {
            "subjectAttributeNames": ["name", "uid", "description"],
            "results": [{"wsSubjects": [subject("1", ["Kim(Jiwoo) Park", "kpark12", JIWOO[1]], "Kim(Jiwoo) Park")]}],
        }
    }

    assert RecordingClient(response).get_group_members("lab_grp") == {"1": "kpark12"}


@pytest.mark.parametrize("lookup", ["get_users_by_id", "get_users_by_username"])
def test_user_lookups_are_read_from_the_uid(lookup):
    response = {
        "WsGetSubjectsResults": {
            "subjectAttributeNames": ["uid"],
            "wsSubjects": [subject("9A1F0C3E5B7D4E2A8C6B0D1E3F5A7C9B", ["kpark12"], "Kim(Jiwoo) Park")],
        }
    }
    client = RecordingClient(response)

    users = getattr(client, lookup)(["kpark12"])

    request = client.sent["WsRestGetSubjectsRequest"]
    assert request["subjectAttributeNames"] == ["uid"]
    assert request["includeSubjectDetail"] == "F"
    assert list(users) == ["kpark12"]


# extract_username is no longer how the client reads usernames, but stays for callers that parse
# descriptions themselves


@pytest.mark.parametrize(
    "attributes, expected",
    [
        (["Eileen Dover (edover02)"], "edover02"),
        (["Kim(Jiwoo) Park (kpark12)"], "kpark12"),
        # the display name first, as Grouper sends it by default
        (JIWOO, "kpark12"),
        (["Eileen Dover"], None),
        ([], None),
        (None, None),
    ],
)
def test_extract_username_reads_the_username_at_the_end_of_a_value(attributes, expected):
    assert GrouperClient.extract_username(attributes) == expected


def test_extract_username_reads_only_the_description_when_the_attribute_names_are_known():
    # a display name ending in parentheses would otherwise be read as a username
    attributes = ["Jack Smith (Jack)", "Jack Smith (jsmith01)"]

    assert GrouperClient.extract_username(attributes, attribute_names=["name", "description"]) == "jsmith01"
