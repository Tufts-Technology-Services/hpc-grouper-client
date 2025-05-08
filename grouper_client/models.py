from typing import Optional, Literal
from typing_extensions import TypedDict, Self
from pydantic import (BaseModel, ConfigDict, PositiveInt,
                      field_serializer, model_validator)


class WsQueryFilter(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    typeOfGroups: Literal['group'] = 'group'
    pageSize: Optional[PositiveInt] = None
    pageNumber: Optional[PositiveInt] = None
    sortString: Optional[str] = None
    ascending: Optional[bool] = None
    queryFilterType: Literal['FIND_BY_STEM_NAME', 'FIND_BY_GROUP_NAME_EXACT']
    stemName: Optional[str] = None
    stemNameScope: Optional[Literal['ALL_IN_SUBTREE']] = None
    enabled: Optional[bool] = None
    groupName: Optional[str] = None

    @field_serializer('enabled')
    def serialize_enabled(self, value: bool) -> str:
        return 'T' if value else 'F'
    
    @field_serializer('ascending')
    def serialize_ascending(self, value: bool) -> str:
        return 'T' if value else 'F'


class WsRestFindGroupsRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    wsQueryFilter: WsQueryFilter
    includeGroupDetail: Optional[bool] = None

    @field_serializer('includeGroupDetail')
    def serialize_include_group_detail(self, value: bool) -> str:
        return 'T' if value else 'F'

class FindGroupsRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    WsRestFindGroupsRequest: WsRestFindGroupsRequest
    

class SubjectLookup(BaseModel):
    subjectIdentifier: Optional[str] = None
    subjectId: Optional[str] = None

    @model_validator(mode='after')
    def check_fields(self) -> Self:
        if not (self.subjectIdentifier or self.subjectId):
            raise ValueError('Either subjectIdentifier or subjectId must be provided')
        return self


class WsRestGetGroupsRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    subjectLookups: list[SubjectLookup]
    subjectAttributeNames: list[str]


class GetGroupsForUserRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    WsRestGetGroupsRequest: WsRestGetGroupsRequest


class WsGroupLookup(TypedDict):
    groupName: str


class WsRestGetMembersRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    includeSubjectDetail: bool
    wsGroupLookups: list[WsGroupLookup]

    @field_serializer('includeSubjectDetail')
    def serialize_include_subject_detail(self, value) -> str:
        return 'T' if value else 'F'


class GetGroupMembersRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    WsRestGetMembersRequest: WsRestGetMembersRequest


class WsRestAddMemberRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    wsGroupLookup: WsGroupLookup
    subjectLookups: list[SubjectLookup]
    replaceAllExisting: bool

    @field_serializer('replaceAllExisting')
    def serialize_replace_all_existing(self, value) -> str:
        return 'T' if value else 'F'


class AddMembersRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    WsRestAddMemberRequest: WsRestAddMemberRequest


class WsRestDeleteMemberRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    wsGroupLookup: WsGroupLookup
    subjectLookups: list[SubjectLookup]


class RemoveMembersRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    WsRestDeleteMemberRequest: WsRestDeleteMemberRequest


class WsRestGetSubjectsRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    includeSubjectDetail: bool
    wsSubjectLookups: list[SubjectLookup]

    @field_serializer('includeSubjectDetail')
    def serialize_include_subject_detail(self, value) -> str:
        return 'T' if value else 'F'


class GetUsersRequest(BaseModel):
    WsRestGetSubjectsRequest: WsRestGetSubjectsRequest
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)


class WsGroup(TypedDict):
    extension: str
    name: str

class WsGroupToSave(TypedDict):
    wsGroupLookup: WsGroupLookup
    wsGroup: WsGroup


class WsRestGroupSaveRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    wsGroupToSaves: list[WsGroupToSave]


class SaveGroupRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    WsRestGroupSaveRequest: WsRestGroupSaveRequest


class WsRestGroupDeleteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    wsGroupLookups: list[WsGroupLookup]


class DeleteGroupRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, frozen=True)
    WsRestGroupDeleteRequest: WsRestGroupDeleteRequest