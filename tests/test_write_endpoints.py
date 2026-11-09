"""
Group lookups and the write endpoints ColdFront uses, against what Grouper 6.4 answered in probes
on 2026-11-09 (a throwaway group, created and deleted again).

The people, ids and group names are made up; the shapes, result codes and HTTP statuses are real.
Grouper answers a repeated write with success: adding an existing member gives
SUCCESS_ALREADY_EXISTED, removing a non-member SUCCESS_WASNT_IMMEDIATE, creating an existing group
SUCCESS_NO_CHANGES_NEEDED, deleting a missing one SUCCESS_GROUP_NOT_FOUND. A request naming a group
that doesn't exist is an HTTP 404; adding someone who doesn't exist fails the whole request with a
500, even alongside people who do.
"""

import pytest
import requests
from conftest import STEM, http_error

OK = {"resultCode": "SUCCESS", "success": "T"}
GROUP = {
    "extension": "probe_grp",
    "typeOfGroup": "group",
    "displayExtension": "probe_grp",
    "displayName": f"{STEM}:probe_grp",
    "name": f"{STEM}:probe_grp",
    "uuid": "e0d1c2b3a4958677685940a3b2c1d0e9",
    "idIndex": "1000002",
    "enabled": "T",
}
ROBIN = {
    "identifierLookup": "rtest01",
    "resultCode": "SUCCESS",
    "success": "T",
    "id": "1B3D5F7A9C2E4A6C8E0B2D4F6A8C0E2D",
    "name": "Robin Q Tester",
    "sourceId": "tuftsedutrunk_SubSourceID",
}


def member_results(results_key, result_code, subject=ROBIN, group_key="wsGroupAssigned"):
    return {
        results_key: {
            "results": [{"wsSubject": subject, "resultMetadata": {"resultCode": result_code, "success": "T"}}],
            group_key: GROUP,
            "resultMetadata": OK,
        }
    }


class TestGroupExists:
    def test_a_group_grouper_finds_exists(self, grouper_answering):
        client = grouper_answering({"WsFindGroupsResults": {"groupResults": [GROUP], "resultMetadata": OK}})

        assert client.group_exists("probe_grp") is True
        method, endpoint, payload = client.sent[0]
        assert payload == {
            "WsRestFindGroupsRequest": {
                "wsQueryFilter": {"queryFilterType": "FIND_BY_GROUP_NAME_EXACT", "groupName": f"{STEM}:probe_grp"}
            }
        }

    def test_a_missing_group_comes_back_without_group_results(self, grouper_answering):
        client = grouper_answering({"WsFindGroupsResults": {"resultMetadata": OK}})

        assert client.group_exists("no_such_group") is False


def test_listing_the_members_of_a_missing_group_raises_the_500(grouper_answering):
    """Grouper answers PROBLEM_GETTING_MEMBERS, GROUP_NOT_FOUND, as a 500."""
    client = grouper_answering(http_error(500))

    with pytest.raises(requests.HTTPError):
        client.get_group_members("no_such_group")


class TestCreateGroup:
    @pytest.mark.parametrize("result_code", ["SUCCESS_INSERTED", "SUCCESS_NO_CHANGES_NEEDED"])
    def test_creating_a_group_succeeds_whether_or_not_it_existed(self, grouper_answering, result_code):
        response = {
            "WsGroupSaveResults": {
                "results": [{"wsGroup": GROUP, "resultMetadata": {"resultCode": result_code, "success": "T"}}],
                "resultMetadata": OK,
            }
        }
        client = grouper_answering(response)

        assert client.create_group("probe_grp") is True
        method, endpoint, payload = client.sent[0]
        assert payload["WsRestGroupSaveRequest"]["wsGroupToSaves"] == [
            {
                "wsGroupLookup": {"groupName": f"{STEM}:probe_grp"},
                "wsGroup": {"extension": "probe_grp", "name": f"{STEM}:probe_grp"},
            }
        ]


class TestDeleteGroup:
    def test_deleting_a_group_succeeds(self, grouper_answering):
        response = {
            "WsGroupDeleteResults": {
                "results": [{"wsGroup": GROUP, "resultMetadata": {"resultCode": "SUCCESS", "success": "T"}}],
                "resultMetadata": OK,
            }
        }

        assert grouper_answering(response).delete_group("probe_grp") is True

    def test_deleting_a_missing_group_succeeds_too(self, grouper_answering):
        response = {
            "WsGroupDeleteResults": {
                "results": [
                    {
                        "wsGroup": {"extension": "probe_grp", "name": f"{STEM}:probe_grp"},
                        "resultMetadata": {"resultCode": "SUCCESS_GROUP_NOT_FOUND", "success": "T"},
                    }
                ],
                "resultMetadata": OK,
            }
        }

        assert grouper_answering(response).delete_group("probe_grp") is True


class TestAddMembersToGroup:
    @pytest.mark.parametrize("result_code", ["SUCCESS", "SUCCESS_ALREADY_EXISTED"])
    def test_adding_a_member_succeeds_whether_or_not_they_were_one(self, grouper_answering, result_code):
        client = grouper_answering(member_results("WsAddMemberResults", result_code))

        assert client.add_members_to_group("probe_grp", ["rtest01"]) == {"rtest01": True}
        method, endpoint, payload = client.sent[0]
        assert (method, endpoint) == ("POST", "groups")
        assert payload == {
            "WsRestAddMemberRequest": {
                "wsGroupLookup": {"groupName": f"{STEM}:probe_grp"},
                "subjectLookups": [{"subjectIdentifier": "rtest01"}],
                "replaceAllExisting": "F",
            }
        }

    def test_adding_someone_who_does_not_exist_raises_the_500(self, grouper_answering):
        client = grouper_answering(http_error(500))

        with pytest.raises(requests.HTTPError):
            client.add_members_to_group("probe_grp", ["rtest01", "zzprobe99"])

    def test_adding_to_a_missing_group_raises_the_404(self, grouper_answering):
        client = grouper_answering(http_error(404))

        with pytest.raises(requests.HTTPError):
            client.add_members_to_group("no_such_group", ["rtest01"])


class TestRemoveMembersFromGroup:
    @pytest.mark.parametrize("result_code", ["SUCCESS", "SUCCESS_WASNT_IMMEDIATE"])
    def test_removing_a_member_succeeds_whether_or_not_they_were_one(self, grouper_answering, result_code):
        client = grouper_answering(member_results("WsDeleteMemberResults", result_code, group_key="wsGroup"))

        assert client.remove_members_from_group("probe_grp", ["rtest01"]) == {"rtest01": True}
        method, endpoint, payload = client.sent[0]
        assert (method, endpoint) == ("DELETE", "groups")
        assert payload == {
            "WsRestDeleteMemberRequest": {
                "wsGroupLookup": {"groupName": f"{STEM}:probe_grp"},
                "subjectLookups": [{"subjectIdentifier": "rtest01"}],
            }
        }

    def test_removing_someone_who_does_not_exist_answers_by_username(self, grouper_answering):
        """Grouper doesn't fail this one: SUCCESS_WASNT_IMMEDIATE, with the subject's id as the lookup."""
        client = grouper_answering(
            member_results("WsDeleteMemberResults", "SUCCESS_WASNT_IMMEDIATE", subject={"id": "zzprobe99"}, group_key="wsGroup")
        )

        assert client.remove_members_from_group("probe_grp", ["zzprobe99"]) == {"zzprobe99": True}

    def test_removing_from_a_missing_group_raises_the_404(self, grouper_answering):
        client = grouper_answering(http_error(404))

        with pytest.raises(requests.HTTPError):
            client.remove_members_from_group("no_such_group", ["rtest01"])
