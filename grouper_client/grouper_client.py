"""
Grouper Client Module

This module provides a Python client for interacting with the Grouper API. 
It includes functionality for managing groups, users, and memberships within 
a Grouper environment.

Classes:
    - GrouperClient: A client for performing operations such as retrieving groups, 
      managing group memberships, and checking user or group existence.

Environment Variables:
    - GROUPER_API_URL: The base URL for the Grouper API.
    - GROUPER_ENTITY_ID: The entity ID used for authentication.
    - GROUPER_KEY_PATH: The file path to the private key used for generating JWT tokens.
    - GROUPER_HPC_STEM: The default stem for group operations (default: 'RTGID:app:Deploy').

Dependencies:
    - jwt: Used for generating JWT tokens for authentication.
    - os: Used for accessing environment variables.
    - datetime: Used for handling timestamps.

Usage:
    Instantiate the `GrouperClient` class and use its methods to interact with the Grouper API.
"""
import os
import datetime
import jwt
from grouper_client.abstract_client import AbstractClient
from grouper_client.models import (
    FindGroupsRequest,
    WsRestFindGroupsRequest,
    WsQueryFilter,
    GetGroupMembersRequest,
    WsRestGetMembersRequest,
    AddMembersRequest,
    WsRestAddMemberRequest,
    RemoveMembersRequest,
    WsRestDeleteMemberRequest,
    GetGroupsForUserRequest,
    WsRestGetGroupsRequest,
    GetUsersRequest,
    WsRestGetSubjectsRequest,
    SaveGroupRequest,
    WsRestGroupSaveRequest,
    DeleteGroupRequest,
    WsRestGroupDeleteRequest
)


GROUPER_API_URL = os.getenv('GROUPER_API_URL', None)
GROUPER_ENTITY_ID = os.getenv('GROUPER_ENTITY_ID', None)
GROUPER_KEY_PATH = os.getenv('GROUPER_KEY_PATH', None)
GROUPER_HPC_STEM = os.getenv('GROUPER_HPC_STEM', None)


class GrouperClient(AbstractClient):
    """
    GrouperClient Class

    This class provides a client for interacting with the Grouper API. It allows for 
    managing groups, users, and memberships within a Grouper environment. The client 
    supports operations such as retrieving groups, checking group or user existence, 
    managing group memberships, and creating or deleting groups.

    Attributes:
        - url (str): The base URL for the Grouper API.
        - entity_id (str): The entity ID used for authentication.
        - key_path (str): The file path to the private key used for generating JWT tokens.
        - stem (str): The default stem for group operations.
        - refresh_token (str): A placeholder for refresh tokens (not used in this implementation).

    Methods:
        - renew_token: Renews the JWT token used for authentication.
        - get_groups: Retrieves a list of groups under a specific stem.
        - get_group_members: Retrieves the members of a specific group.
        - is_user_in_group: Checks if a specific user is a member of a given group.
        - get_group: Retrieves the group object for a given group name.
        - get_group_id: Retrieves the unique ID of a specific group.
        - group_exists: Checks if a specific group exists.
        - add_members_to_group: Adds members to a specific group.
        - get_groups_for_member: Retrieves the groups a specific member belongs to.
        - remove_members_from_group: Removes members from a specific group.
        - extract_username: Parses subject attributes to extract a username.
        - get_users_by_id: Retrieves detailed information about specific users by ID.
        - get_users_by_username: Retrieves detailed information about specific users by username.
        - user_exists: Checks if a specific user exists in Grouper.
        - create_group: Creates a new group.
        - delete_group: Deletes a specific group.

    Usage:
        Instantiate the `GrouperClient` class with the required parameters and use its 
        methods to interact with the Grouper API.
    """
    def __init__(self, base_url=GROUPER_API_URL, entity_id=GROUPER_ENTITY_ID,
                 key_path=GROUPER_KEY_PATH, stem=GROUPER_HPC_STEM):
        """
        Initializes the GrouperClient with the provided parameters or environment variables.
        :param base_url: The base URL for the Grouper API. 
        :param entity_id: The entity ID used for authentication. Get this from Grouper.
        :param key_path: The file path to the private key used for generating JWT tokens. 
        :param stem: The default stem for group operations. e.g. 'RTGID:app:Deploy'
        :return: None
        :raises ValueError: If any of the required parameters are missing."""
        if base_url is None or entity_id is None or key_path is None or stem is None:
            raise ValueError("base_url, entity_id, key_path, and stem arguments are required. "
                             "Alternatively, the "
                             "GROUPER_API_URL, GROUPER_ENTITY_ID, GROUPER_KEY_PATH, and GROUPER_HPC_STEM "
                             "environment variables may be set.")
        self.url = base_url if base_url.endswith('/') else base_url + '/'
        self.entity_id = entity_id
        self.key_path = key_path
        self.stem = stem
        self.refresh_token = 'NA'

    def renew_token(self, refresh_token='NA'):
        """
        Renews the JWT token used for authentication.

        :param refresh_token: this service does not use refresh tokens, so this argument is ignored.
        :return: None
        """
        with open(self.key_path, encoding='utf-8') as f:
            key = f.read()
            encoded_jwt = jwt.encode({
                "iat": datetime.datetime.now(datetime.timezone.utc).timestamp()
            }, key, algorithm="RS256")

            self.token = f"jwtUser_{self.entity_id}_{encoded_jwt}"

    def get_groups(self, page_number=1, page_size=10000, stem=None, details=False):
        """
        Returns a list of groups with the given stem.
        :param page_number: The page number to return.
        :param page_size: The number of groups to return per page.
        :param stem: The stem to return groups from. If None, the default stem is used.
        :param details: If True, returns the full group details. 
            If False, returns only the group names.
        :return: A list of groups with the given stem.
        """
        if stem is None:
            stem = self.stem
        payload = FindGroupsRequest(WsRestFindGroupsRequest=WsRestFindGroupsRequest(
            wsQueryFilter=WsQueryFilter(
                typeOfGroups='group',
                pageSize=page_size,
                pageNumber=page_number,
                sortString='extension',
                ascending=True,
                queryFilterType='FIND_BY_STEM_NAME',
                stemName=stem,
                stemNameScope='ALL_IN_SUBTREE',
                enabled=True
            ),
            includeGroupDetail=True
        ))
        r = self._send_post_request("groups", payload.model_dump(exclude_unset=True))
        r = r['WsFindGroupsResults']['groupResults']
        if not details:
            return [i['extension'] for i in r]
        else:
            return r

    def get_group_members(self, group_name) -> dict:
        """
        Returns a list of members in the given group.
        :param group_name: The name of the group to return members from.
        :return: A dict of members in the group. keys are member ids, values are usernames.
        """
        payload = GetGroupMembersRequest(
            WsRestGetMembersRequest=WsRestGetMembersRequest(
                includeSubjectDetail=True,
                wsGroupLookups=[{"groupName": self.get_qualified_groupname(group_name)}]
        ))
        resp = self._send_post_request("groups", payload.model_dump(exclude_unset=True))
        return self.__handle_get_group_members_response(resp)
 
    def __handle_get_group_members_response(self, response):
        """
        Handles the response from the Grouper API for group members.
        :param response: The response from the Grouper API.
        :return: A dictionary of members in the group. keys are member ids, values are usernames.
        """
        results = response['WsGetMembersResults']['results']
        if len(results) == 0 or 'wsSubjects' not in results[0]:
            return {}
        resp = results[0]['wsSubjects']

        return {i['id']: GrouperClient.extract_username(i['attributeValues'])
                for i in resp if i['resultCode'] == 'SUCCESS'}

    def is_user_in_group(self, group_name, user_uid):
        """
        Checks if a specific user is a member of a given group.

        :param group_name: The name of the group to check.
        :param user_uid: The unique identifier of the user.
        :return: True if the user is in the group, False otherwise.
        """
        return user_uid in self.get_group_members(group_name).values()

    def get_group(self, group_name):
        """
        Returns the group object for the given group name.
        :param group_name: The name of the group to return.
        :return: The group object for the given group name.
        """
        payload = FindGroupsRequest(WsRestFindGroupsRequest=WsRestFindGroupsRequest(
            wsQueryFilter=WsQueryFilter(
                groupName=self.get_qualified_groupname(group_name),
                queryFilterType='FIND_BY_GROUP_NAME_EXACT'
            )
        ))

        return self._send_post_request("groups", payload.model_dump(exclude_unset=True))['WsFindGroupsResults']

    def get_group_id(self, group_name):
        """
        Returns the group id for the given group name.
        :param group_name: The name of the group to return the id for.
        :return: The group id for the given group name.
        """
        return self.get_group(group_name)['groupResults'][0]['uuid']

    def group_exists(self, group_name):
        """
        Checks if a specific group exists.

        :param group_name: The name of the group to check.
        :return: True if the group exists, False otherwise.
        """
        try:
            response = self.get_group(group_name)
            return len(response['groupResults']) > 0
        except KeyError:
            return False

    def add_members_to_group(self, group_name, member_uids: list):
        """
        Adds members to a specific group.

        :param group_name: The name of the group.
        :param member_uids: A list of member unique identifiers to add.
        :return: A list of dictionaries indicating the success status for each member.
        """
        payload = AddMembersRequest(
            WsRestAddMemberRequest=WsRestAddMemberRequest(
                wsGroupLookup={"groupName": self.get_qualified_groupname(group_name)},
                subjectLookups=[{"subjectIdentifier": m} for m in member_uids],
                replaceAllExisting=False
        ))

        resp = self._send_post_request("groups", payload.model_dump(exclude_unset=True))
        return self.__handle_add_members_response(resp)
    
    def __handle_add_members_response(self, response):
        """
        Handles the response from the Grouper API for adding members to a group.
        :param response: The response from the Grouper API.
        :return: A dictionary of members added to the group. keys are member ids, values are usernames.
        """
        if 'WsAddMemberResults' not in response or 'results' not in response['WsAddMemberResults']:
            raise ValueError(f"Unexpected response from Grouper when adding members to group: {response}")
        resp = response['WsAddMemberResults']['results']
        return {i['wsSubject']['identifierLookup']: i['wsSubject']['resultCode'] == 'SUCCESS'
                for i in resp}

    def get_groups_for_member(self, member_id):
        """
        Retrieves the groups a specific member belongs to.

        :param member_id: The unique identifier of the member.
        :return: The response from the Grouper API containing group details.
        """
        payload = GetGroupsForUserRequest(
            WsRestGetGroupsRequest=WsRestGetGroupsRequest(
                subjectLookups=[{"subjectId": member_id}],
                subjectAttributeNames=["description"]
        ))

        resp = self._send_post_request("subjects", payload.model_dump(exclude_unset=True))['WsGetGroupsResults']
        return resp

    def remove_members_from_group(self, group_name, member_uids: list):
        """
        Removes members from a specific group.

        :param group_name: The name of the group.
        :param member_uids: A list of member unique identifiers to remove.
        :return: A list of dictionaries indicating the success status for each member.
        """
        payload = RemoveMembersRequest(
            WsRestDeleteMemberRequest=WsRestDeleteMemberRequest(
                wsGroupLookup={"groupName": self.get_qualified_groupname(group_name)},
                subjectLookups=[{"subjectIdentifier": m} for m in member_uids]
        ))

        resp = self._send_delete_request("groups", payload.model_dump(exclude_unset=True))
        return self.__handle_remove_members_response(resp)
    
    def __handle_remove_members_response(self, response):
        """
        Handles the response from the Grouper API for removing members from a group.
        :param response: The response from the Grouper API.
        :return: A dictionary of members removed from the group. keys are member ids, values are usernames.
        """
        resp = response['WsDeleteMemberResults']['results']
        try:
            return {i['wsSubject']['identifierLookup']: i['wsSubject']['resultCode'] == 'SUCCESS'
                    for i in resp}
        except KeyError:
            return resp

    @staticmethod
    def extract_username(subject_attributes):
        """
        Parses the subject attributes to extract the username from the description.

        :param subject_attributes: The subject attributes list.
        :return: The extracted username or None if not found.
        """
        if subject_attributes is None:
            return None
        for s in subject_attributes:
            if "(" in s and ")" in s:
                # Extract the username from the string
                # Example: "Eileen Dover (edover02)"
                # We want to extract "edover02"
                result = s[s.find("(")+1:s.find(")")]
                if len(result) > 2:
                    return result
        return None

    def get_users_by_id(self, member_ids):
        """
        Retrieves detailed information about specific users.

        :param member_ids: A list of member unique identifiers.
        :return: A list of usernames for the provided member IDs.
        :raises ValueError: If not all members are found in Grouper.
        """
        payload = GetUsersRequest(
            WsRestGetSubjectsRequest=WsRestGetSubjectsRequest(
                includeSubjectDetail=True,
                wsSubjectLookups=[{"subjectId": m} for m in member_ids]
        ))

        r = self._send_post_request("subjects", payload.model_dump(exclude_unset=True))
        subject_list = self.__handle_get_users_response(r)
        return self.__extract_and_validate_users_found(subject_list, member_ids)
    
    def __handle_get_users_response(self, response):
        """
        Handles the response from the Grouper API for user details.
        :param response: The response from the Grouper API.
        :return: A dictionary of users. keys are user ids, values are usernames.
        """
        resp = response['WsGetSubjectsResults']['wsSubjects']
        return {i['id']: GrouperClient.extract_username(i['attributeValues'])
                for i in resp if i['resultCode'] == 'SUCCESS'}
    
    def __extract_and_validate_users_found(self, subject_list, member_ids):
        if len(subject_list.items()) != len(member_ids):
            raise ValueError(f"Not all members were found in grouper: {subject_list}")
        return subject_list.values()

    def get_users_by_username(self, member_uids):
        """
        Retrieves detailed information about specific users.

        :param member_ids: A list of member unique identifiers.
        :return: A list of usernames for the provided member IDs.
        :raises ValueError: If not all members are found in Grouper.
        """
        payload = GetUsersRequest(
            WsRestGetSubjectsRequest=WsRestGetSubjectsRequest(
                includeSubjectDetail=True,
                wsSubjectLookups=[{"subjectIdentifier": m} for m in member_uids]
        ))

        r = self._send_post_request("subjects", payload.model_dump(exclude_unset=True))
        subject_list = self.__handle_get_users_response(r)
        if len(subject_list.items()) != len(member_ids):
            raise ValueError(f"Not all members were found in grouper: {subject_list}")
        return subject_list.keys()

    def user_exists(self, user_id):
        """
        Checks if a specific user exists in Grouper.

        :param user_id: The unique identifier of the user.
        :return: True if the user exists, False otherwise.
        """
        r = self.get_users_by_username([user_id])
        if len(r) == 0:
            return False
        if len(r) > 1:
            raise ValueError(
                f"Multiple users found with the same ID: {user_id}")
        return True

    def create_group(self, group_name):
        """
        Creates a new group.

        :param group_name: The name of the group to create.
        :return: True if the group was successfully created, False otherwise.
        """
        payload = SaveGroupRequest(
            WsRestGroupSaveRequest=WsRestGroupSaveRequest(
                wsGroupToSaves=[
                    {
                        "wsGroupLookup": {
                            "groupName": self.get_qualified_groupname(group_name)
                        },
                        "wsGroup": {
                            "extension": group_name,
                            "name": self.get_qualified_groupname(group_name)
                        }
                    }
                ]
        ))
        
        r = self._send_post_request("groups", payload.model_dump(exclude_unset=True))
        return self.__result_metadata_success(r['WsGroupSaveResults']['results'])

    def delete_group(self, group_name):
        """
        Deletes a specific group.

        :param group_name: The name of the group to delete.
        :return: True if the group was successfully deleted, False otherwise.
        """
        payload = DeleteGroupRequest(
            WsRestGroupDeleteRequest=WsRestGroupDeleteRequest(
                wsGroupLookups=[{"groupName": self.get_qualified_groupname(group_name)}]
        ))
        r = self._send_post_request("groups", payload.model_dump(exclude_unset=True))
        return self.__result_metadata_success(r['WsGroupDeleteResults']['results'])
    
    def __result_metadata_success(self, results):
        """
        Checks if the result metadata indicates success.

        :param results: The results object from the Grouper API.
        :return: True if the operation was successful, False otherwise.
        """
        return len(results) > 0 and results[0]['resultMetadata']['success'] == 'T'
    
    def get_qualified_groupname(self, group_name):
        """
        Returns the qualified group name for a given group name.

        :param group_name: The name of the group.
        :return: The qualified group name.
        """
        return f"{self.stem}:{group_name}"
