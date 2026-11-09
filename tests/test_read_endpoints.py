"""
The read endpoints ColdFront uses, against the responses Grouper 6.4 gave in probes on 2026-11-09.

The people, ids and group names are made up; the shapes, result codes and HTTP statuses are real.
"""

import pytest
import requests
from conftest import STEM, http_error

GROUP = {
    "extension": "lab_grp",
    "typeOfGroup": "group",
    "displayExtension": "lab_grp",
    "displayName": f"{STEM}:lab_grp",
    "name": f"{STEM}:lab_grp",
    "uuid": "0f1e2d3c4b5a69788796a5b4c3d2e1f0",
    "idIndex": "1000001",
    "enabled": "T",
}


def has_member_response(username, subject, result_metadata):
    return {
        "WsHasMemberResults": {
            "results": [{"wsSubject": subject, "resultMetadata": result_metadata}],
            "wsGroup": GROUP,
            "resultMetadata": {"resultCode": "SUCCESS", "success": "T"},
            "responseMetadata": {"millis": "5", "serverVersion": "6.4.1"},
        }
    }


def person(username, subject_id, name):
    return {
        "identifierLookup": username,
        "resultCode": "SUCCESS",
        "success": "T",
        "id": subject_id,
        "name": name,
        "sourceId": "tuftsedutrunk_SubSourceID",
    }


MEMBER = has_member_response(
    "kpark12",
    person("kpark12", "9A1F0C3E5B7D4E2A8C6B0D1E3F5A7C9B", "Kim(Jiwoo) Park"),
    {"resultCode": "IS_MEMBER", "success": "T"},
)
NOT_A_MEMBER = has_member_response(
    "rtest01",
    person("rtest01", "1B3D5F7A9C2E4A6C8E0B2D4F6A8C0E2D", "Robin Q Tester"),
    {"resultCode": "IS_NOT_MEMBER", "success": "T"},
)
NO_SUCH_PERSON = has_member_response(
    "zzprobe99",
    {"id": "zzprobe99"},
    {
        "resultCode": "IS_NOT_MEMBER",
        "resultCode2": "SUBJECT_NOT_FOUND",
        "resultMessage": "Subject: WsSubjectLookup[subjectFindResult=SUBJECT_NOT_FOUND,subjectIdentifier=zzprobe99] had problems: SUBJECT_NOT_FOUND",
        "success": "T",
    },
)


class TestIsUserInGroup:
    @pytest.mark.parametrize(
        "response, expected",
        [(MEMBER, True), (NOT_A_MEMBER, False), (NO_SUCH_PERSON, False)],
        ids=["member", "not a member", "no such person"],
    )
    def test_reads_the_member_result(self, grouper_answering, response, expected):
        client = grouper_answering(response)

        assert client.is_user_in_group("lab_grp", "kpark12") is expected

    def test_asks_the_groups_members_endpoint_by_username(self, grouper_answering):
        client = grouper_answering(MEMBER)

        client.is_user_in_group("lab_grp", "kpark12")

        method, endpoint, payload = client.sent[0]
        assert endpoint == "groups/test%3Astem%3Alab_grp/members"
        assert payload == {"WsRestHasMemberRequest": {"subjectLookups": [{"subjectIdentifier": "kpark12"}]}}

    def test_an_unknown_group_raises_the_404(self, grouper_answering):
        """Callers turn this into False: user-management catches IOError, account_signup everything."""
        client = grouper_answering(http_error(404))

        with pytest.raises(requests.HTTPError):
            client.is_user_in_group("no_such_group", "kpark12")


class TestGetUsersByUsername:
    def test_an_unknown_username_raises(self, grouper_answering):
        response = {
            "WsGetSubjectsResults": {
                "subjectAttributeNames": ["uid"],
                "wsSubjects": [{"identifierLookup": "zzprobe99", "resultCode": "SUBJECT_NOT_FOUND", "success": "F"}],
                "resultMetadata": {"resultCode": "SUCCESS", "resultMessage": "Queried 1 subjects", "success": "T"},
            }
        }
        client = grouper_answering(response)

        with pytest.raises(ValueError, match="Not all members were found"):
            client.get_users_by_username(["zzprobe99"])


class TestGetGroupsForMember:
    def test_returns_grouper_s_results_for_the_member(self, grouper_answering):
        other_group = dict(GROUP, extension="other_grp", name=f"{STEM}:other_grp", displayName=f"{STEM}:other_grp")
        response = {
            "WsGetGroupsResults": {
                "results": [{"wsGroups": [GROUP, other_group], "resultMetadata": {"resultCode": "SUCCESS", "success": "T"}}],
                "resultMetadata": {"resultCode": "SUCCESS", "success": "T"},
            }
        }
        client = grouper_answering(response)

        results = client.get_groups_for_member("kpark12")

        assert [group["extension"] for group in results["results"][0]["wsGroups"]] == ["lab_grp", "other_grp"]
        method, endpoint, payload = client.sent[0]
        assert endpoint == "subjects"
        assert payload["WsRestGetGroupsRequest"]["subjectLookups"] == [{"subjectIdentifier": "kpark12"}]

    def test_an_unknown_username_raises_the_500(self, grouper_answering):
        client = grouper_answering(http_error(500))

        with pytest.raises(requests.HTTPError):
            client.get_groups_for_member("zzprobe99")
