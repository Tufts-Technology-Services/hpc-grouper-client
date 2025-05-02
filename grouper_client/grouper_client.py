import os
import datetime
import jwt
from grouper_client.abstract_client import AbstractClient

GROUPER_API_URL = os.getenv('GROUPER_API_URL', None)
GROUPER_ENTITY_ID = os.getenv('GROUPER_ENTITY_ID', None)
GROUPER_KEY_PATH = os.getenv('GROUPER_KEY_PATH', None)
GROUPER_HPC_STEM = os.getenv('GROUPER_HPC_STEM', 'RTGID:app:Deploy')


class GrouperClient(AbstractClient):
    def __init__(self, base_url=GROUPER_API_URL, entity_id=GROUPER_ENTITY_ID,
                 key_path=GROUPER_KEY_PATH, stem=GROUPER_HPC_STEM):
        self.url = base_url if base_url.endswith('/') else base_url + '/'
        self.entity_id = entity_id
        self.key_path = key_path
        self.stem = stem
        self.refresh_token = 'NA'
        
    def renew_token(self, refresh_token='NA'):
        """
        Renews the JWT token used for authentication.

        :param refresh_token: this service does not use refresh tokens, so this is ignored.
        :return: None
        """
        with open(self.key_path) as f:
            key = f.read()
            encoded_jwt = jwt.encode({"iat": datetime.datetime.now(datetime.UTC).timestamp()}, key, algorithm="RS256")
            self.token = f"jwtUser_{self.entity_id}_{encoded_jwt}"

    def get_groups(self, page_number=1, page_size=100, stem=None, details=False):
        """
        Returns a list of groups with the given stem.
        :param page_number: The page number to return.
        :param page_size: The number of groups to return per page.
        :param stem: The stem to return groups from. If None, the default stem is used.
        :param details: If True, returns the full group details. If False, returns only the group names.
        :return: A list of groups with the given stem.
        """
        if stem is None:
            stem = self.stem
        payload = {
                    "WsRestFindGroupsRequest": {
                        "wsQueryFilter": {
                            "typeOfGroups": "group",
                            "pageSize": str(page_size),
                            "pageNumber": str(page_number),
                            "sortString": "extension",
                            "ascending": "T",
                            "queryFilterType": "FIND_BY_STEM_NAME",
                            "stemName": stem,
                            "stemNameScope": "ALL_IN_SUBTREE",
                            "enabled": "T"
                        },
                        "includeGroupDetail": "T"
                        }
                    }
        
        r = self._send_post_request("groups", payload)
        # todo: handle multiple pages
        r = r['WsFindGroupsResults']['groupResults']
        if not details:
            return [i['extension'] for i in r]
        else:
            return r

    def get_group_members(self, group_name) -> dict:
        """
        Returns a list of members in the given group.
        :param group_name: The name of the group to return members from.
        :return: A dict of members in the given group. keys are the member ids, values are the usernames.
        """
        payload = {
                    "WsRestGetMembersRequest": {
                        "includeSubjectDetail": "T",
                        "wsGroupLookups": [{
                            "groupName": f"{self.stem}:{group_name}"
                        }]
                    }
                    }
        resp = self._send_post_request("groups", payload)
        resp = resp['WsGetMembersResults']['results'][0]['wsSubjects']
        return {i['id']: GrouperClient.extract_username(i['attributeValues']) for i in resp if i['resultCode'] == 'SUCCESS'}
    
    def is_user_in_group(self, group_name, user_id):
        """
        Checks if a specific user is a member of a given group.

        :param group_name: The name of the group to check.
        :param user_id: The unique identifier of the user.
        :return: True if the user is in the group, False otherwise.
        """
        return user_id in self.get_group_members(group_name).values()

    def get_group(self, group_name):
        """
        Returns the group object for the given group name.
        :param group_name: The name of the group to return.
        :return: The group object for the given group name.
        """
        payload = {
                    "WsRestFindGroupsRequest":{
                        "wsQueryFilter": {
                        "groupName": f"{self.stem}:{group_name}",
                        "queryFilterType": "FIND_BY_GROUP_NAME_EXACT",
                        }
                    }
                }
        return self._send_post_request("groups", payload)['WsFindGroupsResults']
   
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
        payload = {
                    "WsRestAddMemberRequest":{
                        "subjectLookups": [{"subjectIdentifier": m} for m in member_uids],
                        "wsGroupLookup":{
                            "groupName": f"{self.stem}:{group_name}"
                            }
                        },
                        "replaceAllExisting": False
                    }
        resp = self._send_post_request("groups", payload)
        resp = resp['WsAddMemberResults']['results']
        print(resp)
        return [{i['wsSubject']['identifierLookup']: i['wsSubject']['resultCode'] == 'SUCCESS'} for i in resp]

    def get_groups_for_member(self, member_id):
        """
        Retrieves the groups a specific member belongs to.

        :param member_id: The unique identifier of the member.
        :return: The response from the Grouper API containing group details.
        """
        payload = {
                    "WsRestGetGroupsRequest":{
                        "subjectLookups":[{
                            "subjectId": member_id
                        }],
                        "subjectAttributeNames":[
                            "description"
                        ]
                    }
                }
        return self._send_post_request("subjects", payload)
    
    def remove_members_from_group(self, group_name, member_uids: list):
        """
        Removes members from a specific group.

        :param group_name: The name of the group.
        :param member_uids: A list of member unique identifiers to remove.
        :return: A list of dictionaries indicating the success status for each member.
        """
        members = [{"subjectIdentifier": m} for m in member_uids]
        payload = {
            "WsRestDeleteMemberRequest": {
                "wsGroupLookup": {
                    "groupName": f"{self.stem}:{group_name}"
                },
                "subjectLookups": members
            }}
        resp = self._send_delete_request("groups", payload)
        resp = resp['WsDeleteMemberResults']['results']
        return [{i['wsSubject']['identifierLookup']: i['wsSubject']['resultCode'] == 'SUCCESS'} for i in resp]

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
        payload = {
            "WsRestGetSubjectsRequest": {
                "includeSubjectDetail": "T",
                "wsSubjectLookups": [{"subjectId": m } for m in member_ids]
            }
        }
        r =  self._send_post_request("subjects", payload)
        subject_list = r['WsGetSubjectsResults']['wsSubjects']
        subject_list = [i for i in subject_list if i['resultCode'] == 'SUCCESS']
        subject_list = {i['id']: GrouperClient.extract_username(i['attributeValues']) for i in subject_list}
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
        payload = {
            "WsRestGetSubjectsRequest": {
                "includeSubjectDetail": "T",
                "wsSubjectLookups": [{"subjectIdentifier": m } for m in member_uids]
            }
        }
        r =  self._send_post_request("subjects", payload)
        subject_list = r['WsGetSubjectsResults']['wsSubjects']
        subject_list = [i for i in subject_list if i['resultCode'] == 'SUCCESS']
        subject_list = {i['id']: GrouperClient.extract_username(i['attributeValues']) for i in subject_list}
        if len(subject_list.items()) != len(member_uids):
            raise ValueError(f"Not all members were found in grouper: {subject_list}")
        return subject_list.values()
 
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
            raise ValueError(f"Multiple users found with the same ID: {user_id}")
        return True
        
    def create_group(self, group_name):
        """
        Creates a new group.

        :param group_name: The name of the group to create.
        :return: True if the group was successfully created, False otherwise.
        """
        payload = {
            "WsRestGroupSaveRequest":{
                "wsGroupToSaves":[
                    {
                    "wsGroupLookup":{
                        "groupName": f"{self.stem}:{group_name}"
                    },
                    "wsGroup":{
                        "extension": group_name,
                        "name": f"{self.stem}:{group_name}"
                    }
                    }
                ]
            }
            }
        return self._send_post_request("groups", payload)['WsGroupSaveResults']['results'][0]['resultMetadata']['success'] == 'T'
    
    def delete_group(self, group_name):
        """
        Deletes a specific group.

        :param group_name: The name of the group to delete.
        :return: True if the group was successfully deleted, False otherwise.
        """
        payload = {
            "WsRestGroupDeleteRequest": {
                "wsGroupLookups": [{
                    "groupName": f"{self.stem}:{group_name}"
                }]
            }
        }
        return self._send_post_request("groups", payload)['WsGroupDeleteResults']['results'][0]['resultMetadata']['success'] == 'T'
