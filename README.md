# grouper-client
This class provides a client for interacting with the Grouper API. It allows for 
managing groups, users, and memberships within a Grouper environment. The client 
supports operations such as retrieving groups, checking group or user existence, 
managing group memberships, and creating or deleting groups.

The client uses JWT tokens for authentication and requires configuration
parameters such as the Grouper API URL, entity ID, and private key path.

## Prerequisites
You will need to have the following information to use the GrouperClient:
- Grouper API URL
- Entity ID
- private key for JWT token generation
- Default stem for group operations

Much of this will be provided by your Grouper administrator.
See https://spaces.at.internet2.edu/spaces/Grouper/pages/207650892/Grouper+web+services+-+authentication+-+self-service+JWT 
for more details on setting up JWT authentication to Grouper. Note that this client will handle the JWT token generation for you.

## Installation

You can install the package using pip:
```bash
pip install grouper-client@git+https://github.com/Tufts-Technology-Services/hpc-grouper-client.git
```

## Usage
To use the GrouperClient, you can set the following environment variables, or provide these values 
directly when instantiating the client:
- `GROUPER_API_URL`: The base URL of the Grouper API.
- `GROUPER_ENTITY_ID`: The entity ID for JWT authentication.
- `GROUPER_KEY_PATH`: The file path to the private key used for signing JWT tokens.
- `GROUPER_HPC_STEM`: The default stem for group operations.

Example with environment variables set:
```python
from grouper_client.grouper_client import GrouperClient
client = GrouperClient()
```

Example with parameters provided directly:
```python
from grouper_client.grouper_client import GrouperClient
client = GrouperClient(
    api_url='https://grouper.example.com/grouper-ws/servicesRest/json/2.4.000/',
    entity_id='your-entity-id',
    key_path='/path/to/your/private/key.pem',
    default_stem='YOUR_BASE:app:APPNAME'
)
```

### Methods:
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
