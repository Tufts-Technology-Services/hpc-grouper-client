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
        with open(self.key_path) as f:
            key = f.read()
            encoded_jwt = jwt.encode({"iat": datetime.datetime.now(datetime.UTC).timestamp()}, key, algorithm="RS256")
            self.token = f"jwtUser_{self.entity_id}_{encoded_jwt}"

    def get_groups(self, page_number=1, page_size=100, stem=None, details=False):
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
        r = r['WsFindGroupsResults']['groupResults']
        if not details:
            return [i['extension'] for i in r]
        else:
            return r

    def get_group_members(self, group_name,):
        """
        {'WsGetMembersResults': {'subjectAttributeNames': ['name', 'description'], 'resultMetadata': {'resultCode': 'SUCCESS', 'resultMessage': 'Success for: clientVersion: 5.14.0, wsGroupLookups: Array size: 1: [0]: WsGroupLookup[pitGroups=[],groupName=RTGID:app:Deploy:chris_api_test]\n\n, memberFilter: All, includeSubjectDetail: true, actAsSubject: null, fieldName: null, subjectAttributeNames: null\n, paramNames: \n, params: null\n, sourceIds: null\n, pointInTimeFrom: null, pointInTimeTo: null, pageSize: null, pageNumber: null, sortString: null, ascending: null', 'success': 'T'}, 'responseMetadata': {'millis': '129', 'serverVersion': '5.14.0'}, 'results': [{'wsGroup': {'extension': 'chris_api_test', 'typeOfGroup': 'group', 'displayExtension': 'chris_api_test', 'displayName': 'RTGID:app:Deploy:chris_api_test', 'name': 'RTGID:app:Deploy:chris_api_test', 'uuid': '24d52dbbdaca44deb92b591bd5b09be5', 'idIndex': '1002143', 'enabled': 'T'}, 'wsSubjects': [{'resultCode': 'SUCCESS', 'success': 'T', 'memberId': 'a9106adb7c164c74b1b1c4e3219fadc7', 'id': '52689D2E3035295B3D59D73E7C52FF00', 'name': 'Christopher S Barnett', 'sourceId': 'tuftsedutrunk_SubSourceID', 'attributeValues': ['Christopher S Barnett', 'Christopher S Barnett (cbarne02)']}, {'resultCode': 'SUCCESS', 'success': 'T', 'memberId': '3c25285699b342e18035e13a31a4cdd7', 'id': 'CA5561E5D361F25F279EAE09030AD145', 'name': 'Tom K. Phimmasen', 'sourceId': 'tuftsedutrunk_SubSourceID', 'attributeValues': ['Tom K. Phimmasen', 'Tom K. Phimmasen (tphimm01)']}], 'resultMetadata': {'resultCode': 'SUCCESS', 'success': 'T'}}]}}
        """
        payload = {
                    "WsRestGetMembersRequest": {
                        "includeSubjectDetail": "T",
                        "wsGroupLookups": [{
                            "groupName": f"{self.stem}:{group_name}"
                        }]
                    }
                    }
        return self._send_post_request("groups", payload)
    
    def get_group_id(self, group_name):
        payload = {
                    "WsRestFindGroupsRequest":{
                        "wsQueryFilter": {
                        "groupName": f"{self.stem}:{group_name}",
                        "queryFilterType": "FIND_BY_GROUP_NAME_EXACT",
                        }
                    }
                }
        return self._send_post_request("groups", payload)['WsFindGroupsResults']['groupResults'][0]['uuid']

    def add_members_to_group(self, group_name, member_uids: list):
        """
        {'WsAddMemberResults': {'results': [{'wsSubject': {'identifierLookup': 'cbarne02', 'resultCode': 'SUCCESS', 'success': 'T', 'id': '52689D2E3035295B3D59D73E7C52FF00', 'name': 'Christopher S Barnett', 'sourceId': 'tuftsedutrunk_SubSourceID'}, 'resultMetadata': {'resultCode': 'SUCCESS', 'success': 'T'}}, {'wsSubject': {'identifierLookup': 'tphimm01', 'resultCode': 'SUCCESS', 'success': 'T', 'id': 'CA5561E5D361F25F279EAE09030AD145', 'name': 'Tom K. Phimmasen', 'sourceId': 'tuftsedutrunk_SubSourceID'}, 'resultMetadata': {'resultCode': 'SUCCESS', 'success': 'T'}}], 'wsGroupAssigned': {'extension': 'chris_api_test', 'typeOfGroup': 'group', 'displayExtension': 'chris_api_test', 'displayName': 'RTGID:app:Deploy:chris_api_test', 'name': 'RTGID:app:Deploy:chris_api_test', 'uuid': '24d52dbbdaca44deb92b591bd5b09be5', 'idIndex': '1002143', 'enabled': 'T'}, 'resultMetadata': {'resultCode': 'SUCCESS', 'resultMessage': 'Success for: clientVersion: 5.14.0, wsGroupLookup: WsGroupLookup[pitGroups=[],groupName=RTGID:app:Deploy:chris_api_test], subjectLookups: Array size: 2: [0]: WsSubjectLookup[subjectIdentifier=cbarne02]\n[1]: WsSubjectLookup[subjectIdent...\n, replaceAllExisting: false, actAsSubject: null, fieldName: null, txType: NONE, includeGroupDetail: false, includeSubjectDetail: false, subjectAttributeNames: null\n, params: null\n, disabledDate: null, enabledDate: null', 'success': 'T'}, 'responseMetadata': {'millis': '7731', 'serverVersion': '5.14.0'}}}
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
        return self._send_post_request("groups", payload)

    def get_groups_for_member(self, member_id):
        """
        {'WsGetGroupsResults': {'results': [{'wsGroups': [{'extension': 'c-admin', 'typeOfGroup': 'group', 'displayExtension': 'c-admin', 'displayName': 'RTGID:app:Deploy:c-admin', 'name': 'RTGID:app:Deploy:c-admin', 'uuid': '796387e220644200976ee323094ae1f7', 'idIndex': '1002042', 'enabled': 'T'}, {'extension': 'ccgpu', 'typeOfGroup': 'group', 'displayExtension': 'ccgpu', 'displayName': 'RTGID:app:Deploy:ccgpu', 'name': 'RTGID:app:Deploy:ccgpu', 'uuid': '82bd7831d6d14772940d688d7c626e2e', 'idIndex': '1002057', 'enabled': 'T'}, {'extension': 'chris_api_test', 'typeOfGroup': 'group', 'displayExtension': 'chris_api_test', 'displayName': 'RTGID:app:Deploy:chris_api_test', 'name': 'RTGID:app:Deploy:chris_api_test', 'uuid': '24d52dbbdaca44deb92b591bd5b09be5', 'idIndex': '1002143', 'enabled': 'T'}, {'extension': 'rtadmin', 'typeOfGroup': 'group', 'displayExtension': 'rtadmin', 'displayName': 'RTGID:app:Deploy:rtadmin', 'name': 'RTGID:app:Deploy:rtadmin', 'uuid': 'ee326aae65c6478b99def7f5cf565e5b', 'idIndex': '1002055', 'enabled': 'T'}, {'extension': 'TTS_RSCH_HPC_CLUSTER_LOGIN', 'typeOfGroup': 'group', 'displayExtension': 'TTS_RSCH_HPC_CLUSTER_LOGIN', 'displayName': 'RTGID:app:Deploy:TTS_RSCH_HPC_CLUSTER_LOGIN', 'name': 'RTGID:app:Deploy:TTS_RSCH_HPC_CLUSTER_LOGIN', 'uuid': '6fad8845f2af409084c5a16296b5ea8b', 'idIndex': '1001890', 'enabled': 'T'}], 'resultMetadata': {'resultCode': 'SUCCESS', 'success': 'T'}, 'wsSubject': {'resultCode': 'SUCCESS', 'success': 'T', 'id': 'CA5561E5D361F25F279EAE09030AD145', 'name': 'Tom K. Phimmasen', 'sourceId': 'tuftsedutrunk_SubSourceID', 'attributeValues': ['Tom K. Phimmasen (tphimm01)']}}], 'resultMetadata': {'resultCode': 'SUCCESS', 'resultMessage': 'Success for: clientVersion: 5.14.0, subjectLookups: Array size: 1: [0]: WsSubjectLookup[subjectId=CA5561E5D361F25F279EAE09030AD145]\n\nmemberFilter: All, includeGroupDetail: false, actAsSubject: null\n, params: null\n fieldName1: null\n, scope: null, wsStemLookup: null\n, stemScope: null, enabled: null, pageSize: null, pageNumber: null, sortString: null, ascending: null\n, pointInTimeFrom: null, pointInTimeTo: null', 'success': 'T'}, 'subjectAttributeNames': ['description'], 'responseMetadata': {'millis': '59', 'serverVersion': '5.14.0'}}}
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
        {'WsDeleteMemberResults': {'results': [{'wsSubject': {'identifierLookup': 'cbarne02', 'resultCode': 'SUCCESS', 'success': 'T', 'id': '52689D2E3035295B3D59D73E7C52FF00', 'name': 'Christopher S Barnett', 'sourceId': 'tuftsedutrunk_SubSourceID'}, 'resultMetadata': {'resultCode': 'SUCCESS', 'success': 'T'}}], 'wsGroup': {'extension': 'chris_api_test', 'typeOfGroup': 'group', 'displayExtension': 'chris_api_test', 'displayName': 'RTGID:app:Deploy:chris_api_test', 'name': 'RTGID:app:Deploy:chris_api_test', 'uuid': '24d52dbbdaca44deb92b591bd5b09be5', 'idIndex': '1002143', 'enabled': 'T'}, 'resultMetadata': {'resultCode': 'SUCCESS', 'resultMessage': 'Success for: clientVersion: 5.14.0, wsGroupLookup: WsGroupLookup[pitGroups=[],groupName=RTGID:app:Deploy:chris_api_test], subjectLookups: Array size: 1: [0]: WsSubjectLookup[subjectIdentifier=cbarne02]\n\n, actAsSubject: null, fieldName: null, txType: NONE\n, params: null', 'success': 'T'}, 'responseMetadata': {'millis': '348', 'serverVersion': '5.14.0'}}}
        """
        members = [{"subjectIdentifier": m} for m in member_uids]
        payload = {
            "WsRestDeleteMemberRequest": {
                "wsGroupLookup": {
                    "groupName": f"{self.stem}:{group_name}"
                },
                "subjectLookups": members
            }}
        return self._send_delete_request("groups", payload)

    def get_user_info(self, member_id):
        # todo: useful?
        payload = {
            "WsRestGetSubjectsRequest": {
                "includeSubjectDetail": "T",
                "wsSubjectLookups": [{
                    "subjectId": member_id
                }]
            }
        }
        return self._send_post_request("subjects", payload)

    def create_group(self, group_name):
            """
{'WsGroupSaveResults': {'results': [{'wsGroup': {'extension': 'chris_api_test', 'typeOfGroup': 'group', 'displayExtension': 'chris_api_test', 'displayName': 'RTGID:app:Deploy:chris_api_test', 'name': 'RTGID:app:Deploy:chris_api_test', 'uuid': '382876a44eb546d7bdf62714450400dd', 'idIndex': '1002142', 'enabled': 'T'}, 'resultMetadata': {'resultCode': 'SUCCESS_INSERTED', 'success': 'T'}}], 'resultMetadata': {'resultCode': 'SUCCESS', 'resultMessage': 'Success for: clientVersion: 5.14.0, wsGroupToSaves: Array size: 1: [0]: WsGroupToSave[\n  wsGroupLookup=WsGroupLookup[pitGroups=[],groupName=RTGID:app:Deploy:chris_api_test],\n  wsGroup=WsGroup[extension=chris_api_test,name=RTGID:app:Deploy:chris_api_...\n, actAsSubject: null, txType: NONE, paramNames: \n, params: null', 'success': 'T'}, 'responseMetadata': {'millis': '381', 'serverVersion': '5.14.0'}}}
            """
            payload = {
                "WsRestGroupSaveRequest":{
                    "wsGroupToSaves":[
                        {
                        "wsGroupLookup":{
                            "groupName": f"{self.stem}:{group_name}",
                        },
                        "wsGroup":{
                            "extension": group_name,
                            "name": f"{self.stem}:{group_name}"
                        }
                        }
                    ]
                }
                }
            return self._send_post_request("groups", payload)
    
    def delete_group(self, group_name):
        """
        {'WsGroupDeleteResults': {'results': [{'wsGroup': {'extension': 'chris_api_test', 'typeOfGroup': 'group', 'displayExtension': 'chris_api_test', 'displayName': 'RTGID:app:Deploy:chris_api_test', 'name': 'RTGID:app:Deploy:chris_api_test', 'uuid': '382876a44eb546d7bdf62714450400dd', 'idIndex': '1002142', 'enabled': 'T'}, 'resultMetadata': {'resultCode': 'SUCCESS', 'resultMessage': "Group 'RTGID:app:Deploy:chris_api_test' was deleted.", 'success': 'T'}}], 'resultMetadata': {'resultCode': 'SUCCESS', 'resultMessage': 'Success for: clientVersion: 5.14.0, wsGroupLookups: Array size: 1: [0]: WsGroupLookup[pitGroups=[],groupName=RTGID:app:Deploy:chris_api_test]\n\n, actAsSubject: null, txType: NONE, includeGroupDetail: false, paramNames: \n, params: null', 'success': 'T'}, 'responseMetadata': {'millis': '349', 'serverVersion': '5.14.0'}}}
        """
        payload = {
            "WsRestGroupDeleteRequest": {
                "wsGroupLookups": [{
                    "groupName": f"{self.stem}:{group_name}"
                }]
            }
        }
        return self._send_post_request("groups", payload)
