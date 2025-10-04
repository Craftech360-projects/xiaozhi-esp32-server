# User Account Management API Documentation

This document describes the user-facing APIs for password updates and account deletion that don't require authentication or admin privileges.

## Table of Contents
- [Update Password](#update-password)
- [Delete Account](#delete-account)
- [Common Request/Response Formats](#common-requestresponse-formats)

---

## Update Password

### Endpoint
```
PUT /user/update-password
```

### Description
Allows users to update their password without requiring the old password or login session. This endpoint relies on frontend verification mechanisms.

### Authentication
**Not Required** - The endpoint is publicly accessible and relies on frontend verification.

### Request Body
```json
{
  "username": "string (required)",
  "newPassword": "string (required)"
}
```

#### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | String | Yes | User's username or phone number |
| `newPassword` | String | Yes | New password to set |

#### Password Requirements
The new password must meet the following criteria:
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one number (0-9)

### Response

#### Success Response (200 OK)
```json
{
  "code": 0,
  "msg": "success"
}
```

#### Error Responses

**User Not Found (500)**
```json
{
  "code": 1001,
  "msg": "Account does not exist"
}
```

**Weak Password (500)**
```json
{
  "code": 1003,
  "msg": "Password is too weak"
}
```

**Generic Error (500)**
```json
{
  "code": 500,
  "msg": "Password update failed, please try again later"
}
```

### Example Request
```bash
curl -X PUT http://localhost:8080/user/update-password \
  -H "Content-Type: application/json" \
  -d '{
    "username": "13800138000",
    "newPassword": "NewPassword123"
  }'
```

### Logging
The endpoint logs the following events:
- **INFO**: Password update request initiation with username
- **DEBUG**: DTO validation success
- **INFO**: User found with userId
- **DEBUG**: Service method call for password update
- **INFO**: Password update success
- **ERROR**: User not found, validation failures, or exceptions

### Implementation Location
- **Controller**: `LoginController.java:177-208`
- **Service**: `SysUserServiceImpl.java:133-144` (changePasswordDirectly method)

---

## Delete Account

### Endpoint
```
DELETE /user/delete-account
```

### Description
Allows users to delete their account without requiring login session or password verification. This endpoint deletes the user account and all associated data including devices and agents. It relies on frontend verification mechanisms.

### Authentication
**Not Required** - The endpoint is publicly accessible and relies on frontend verification.

### Request Body
```json
{
  "username": "string (required)"
}
```

#### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | String | Yes | User's username or phone number |

**Note**: The `newPassword` field exists in the DTO but is not validated or used by this endpoint.

### Response

#### Success Response (200 OK)
```json
{
  "code": 0,
  "msg": "success"
}
```

#### Error Responses

**User Not Found (500)**
```json
{
  "code": 1001,
  "msg": "Account does not exist"
}
```

**Generic Error (500)**
```json
{
  "code": 500,
  "msg": "Account deletion failed, please try again later"
}
```

### Data Deletion
When an account is deleted, the following data is also removed:
- User account information
- All devices associated with the user
- All agents/智能体 associated with the user

### Example Request
```bash
curl -X DELETE http://localhost:8080/user/delete-account \
  -H "Content-Type: application/json" \
  -d '{
    "username": "13800138000"
  }'
```

### Logging
The endpoint logs the following events:
- **INFO**: Account deletion request initiation with username
- **DEBUG**: DTO validation success
- **INFO**: User found for deletion with userId
- **INFO**: Account and associated data deletion start
- **INFO**: Account deletion success
- **ERROR**: User not found or exceptions

### Implementation Location
- **Controller**: `LoginController.java:210-241`
- **Service**: `SysUserServiceImpl.java:96-105` (deleteById method)

---

## Common Request/Response Formats

### DTO Classes

#### UpdatePasswordDTO
**Location**: `UpdatePasswordDTO.java`

```java
{
  "username": String,    // User's username or phone number (required)
  "newPassword": String  // New password (required for update-password)
}
```

### Error Codes
| Code | Description |
|------|-------------|
| 0 | Success |
| 500 | Generic server error |
| 1001 | Account does not exist |
| 1003 | Password is too weak |

### Base URL
Default base URL: `http://localhost:8080`

---

## Security Considerations

⚠️ **Important Security Notes**:

1. **Frontend Verification Required**: Both endpoints are publicly accessible and do NOT require authentication. You MUST implement proper verification mechanisms in your frontend application before calling these endpoints.

2. **No Password Verification**: The delete account endpoint does not verify the user's password. Ensure your frontend properly authenticates the user before allowing account deletion.

3. **No Old Password Check**: The update password endpoint does not require the old password. Implement appropriate security measures in your frontend.

4. **Irreversible Actions**: Account deletion is permanent and cannot be undone. All associated data (devices, agents) will be permanently deleted.

5. **Rate Limiting**: Consider implementing rate limiting on these endpoints to prevent abuse.

6. **Audit Logging**: Both endpoints provide comprehensive logging. Monitor these logs for suspicious activity.

---

## Best Practices

1. **Frontend Verification**: Implement robust user verification in your frontend before calling these APIs
2. **User Confirmation**: Always ask for user confirmation before deleting accounts
3. **Password Strength**: Enforce strong password requirements in your frontend UI
4. **Error Handling**: Implement proper error handling for all possible error responses
5. **User Feedback**: Provide clear feedback to users about password requirements and deletion consequences

---

## Version Information
- **API Version**: 1.0
- **Last Updated**: 2025-10-04
- **Maintained By**: Xiaozhi Development Team
