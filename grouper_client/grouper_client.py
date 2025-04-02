import os
import datetime
import jwt
from grouper_client.abstract_client import AbstractClient

GROUPER_API_URL = os.getenv('GROUPER_API_URL', None)
GROUPER_ENTITY_ID = os.getenv('GROUPER_ENTITY_ID', None)
GROUPER_KEY_PATH = os.getenv('GROUPER_KEY_PATH', None)


class GrouperClient(AbstractClient):
    def __init__(self, base_url=GROUPER_API_URL, entity_id=GROUPER_ENTITY_ID, key_path=GROUPER_KEY_PATH):
        self.base_url = base_url if base_url.endswith('/') else base_url + '/'
        self.entity_id = entity_id
        self.key_path = key_path
        
    def generate_token(self):
        with open(self.key_path) as f:
            key = f.read()
            encoded_jwt = jwt.encode({"iat": datetime.datetime.now(datetime.UTC).timestamp()}, key, algorithm="RS256")
            self.token = f"jwtUser_{self.entity_id}_{encoded_jwt}"

    def get_groups(self):
        pass

    def get_group_members(self, group_id):
        return self._send_get_request(f"groups/{group_id}/members")

    def add_members_to_group(self, group_name, member_uids: list):
        """
                RTGID:app:Deploy:aldridgelab
        """
        payload = {
                    "WsRestAddMemberRequest":{
                        "subjectLookups": [{"subjectSourceId": "uid", "subjectIdentifier": m} for m in member_uids],
                        "wsGroupLookup":{
                            "groupName": group_name
                            }
                        }
                    }
        return self._send_put_request("groups", payload)

    def get_groups_for_member(self, member_id):
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
    
    def remove_member_from_group(self, group_id, member_id):
        pass
