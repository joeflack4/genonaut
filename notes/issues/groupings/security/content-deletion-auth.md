# Content Deletion Authentication & Authorization

## Severity: CRITICAL
**Status:** Open
**Priority:** P0 - Must fix before production
**Created:** 2025-11-16
**Related Feature:** [Delete Content Implementation](../../../active/delete-content.md)

## Overview
Content deletion endpoints lack authentication and authorization checks, allowing any user (or unauthenticated request) to delete any content by ID. This is a critical security vulnerability that must be addressed before the delete feature goes to production.

## Affected Endpoints

### 1. Regular Content Deletion
**Endpoint:** `DELETE /api/v1/content/{content_id}`
**File:** `genonaut/api/routes/content.py:257-268`
**Current Implementation:**
```python
@router.delete("/{content_id}", response_model=SuccessResponse)
async def delete_content(
    content_id: int,
    db: Session = Depends(get_database_session)
):
    """Delete content."""
    service = ContentService(db)
    try:
        service.delete_content(content_id)
        return SuccessResponse(message=f"Content {content_id} deleted successfully")
```

**Issues:**
- No user authentication check
- No ownership verification
- No role/permission check
- Anyone can delete any content

### 2. Auto-Generated Content Deletion
**Endpoint:** `DELETE /api/v1/content-auto/{content_id}`
**File:** `genonaut/api/routes/content_auto.py:98-110`
**Current Implementation:**
```python
@router.delete("/{content_id}", response_model=SuccessResponse)
async def delete_auto_content(
    content_id: int,
    db: Session = Depends(get_database_session),
):
    """Delete an automated content record."""
    service = _service(db)
    try:
        service.delete_content(content_id)
        return SuccessResponse(message=f"Auto content {content_id} deleted successfully")
```

**Issues:**
- Same as regular content - no auth checks whatsoever

## Attack Scenarios

### Scenario 1: Unauthorized Deletion
**Attacker Action:**
```bash
curl -X DELETE http://api.genonaut.com/api/v1/content/123
```

**Result:** Content ID 123 deleted permanently, regardless of who owns it

**Impact:**
- Users lose their content without consent
- Malicious actors can vandalize the platform
- No audit trail of who deleted what

### Scenario 2: Automated Mass Deletion
**Attacker Action:**
```bash
for i in {1..10000}; do
  curl -X DELETE http://api.genonaut.com/api/v1/content/$i &
done
```

**Result:** Thousands of content items deleted in parallel

**Impact:**
- Platform-wide data loss
- Service disruption
- Potential database integrity issues with FK constraints

### Scenario 3: Targeted User Attack
**Attacker Action:**
1. Enumerate user's content IDs via gallery endpoints
2. Delete all their content programmatically

**Result:** All of a specific user's content permanently removed

**Impact:**
- User loses all their work
- Potential legal liability
- Reputation damage to platform

## Required Security Controls

### 1. Authentication
**Requirement:** Verify user identity before allowing deletion

**Implementation Options:**
- JWT token validation (if using token-based auth)
- Session-based authentication
- API key authentication

**Example:**
```python
@router.delete("/{content_id}", response_model=SuccessResponse)
async def delete_content(
    content_id: int,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user)  # ADD THIS
):
    """Delete content."""
    # ... rest of implementation
```

### 2. Authorization - Ownership Check
**Requirement:** Verify user owns the content they're trying to delete

**Implementation:**
```python
# In ContentService.delete_content()
def delete_content(self, content_id: int, user_id: UUID) -> bool:
    """Delete a content record if user owns it."""
    content = self.repository.get_or_404(content_id)

    # Check ownership
    if content.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete this content"
        )

    return self.repository.delete(content_id)
```

### 3. Authorization - Admin Override
**Requirement:** Allow admins to delete any content (moderation)

**Implementation:**
```python
def delete_content(self, content_id: int, user_id: UUID, is_admin: bool = False) -> bool:
    """Delete a content record."""
    content = self.repository.get_or_404(content_id)

    # Check ownership or admin permission
    if content.user_id != user_id and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete this content"
        )

    return self.repository.delete(content_id)
```

### 4. Rate Limiting
**Requirement:** Prevent mass deletion attacks

**Implementation Options:**
- Per-user rate limits (e.g., 10 deletions per minute)
- Global rate limits
- Progressive delays after multiple deletions

**Example (using slowapi):**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.delete("/{content_id}", response_model=SuccessResponse)
@limiter.limit("10/minute")  # ADD THIS
async def delete_content(
    request: Request,
    content_id: int,
    # ...
):
    # ... implementation
```

### 5. Audit Logging
**Requirement:** Log all deletion attempts for accountability

**Implementation:**
```python
import logging
logger = logging.getLogger(__name__)

def delete_content(self, content_id: int, user_id: UUID) -> bool:
    """Delete a content record with audit logging."""
    content = self.repository.get_or_404(content_id)

    # Log deletion attempt
    logger.info(
        f"User {user_id} attempting to delete content {content_id} "
        f"(owner: {content.user_id})"
    )

    # Check ownership
    if content.user_id != user_id:
        logger.warning(
            f"Unauthorized deletion attempt: user {user_id} tried to delete "
            f"content {content_id} owned by {content.user_id}"
        )
        raise HTTPException(status_code=403, detail="Forbidden")

    result = self.repository.delete(content_id)
    logger.info(f"Content {content_id} successfully deleted by user {user_id}")

    return result
```

## Implementation Tasks

### Phase 1: Authentication Infrastructure
- [ ] Review current auth system (JWT, session, API key?)
- [ ] Identify `get_current_user` dependency or equivalent
- [ ] Ensure auth middleware is working on all routes
- [ ] Document auth strategy in `docs/authentication.md`

### Phase 2: Content Deletion Authorization
- [ ] Update `ContentService.delete_content()` signature to accept `user_id`
- [ ] Add ownership check in service layer
- [ ] Update DELETE endpoint to inject `current_user`
- [ ] Pass user_id to service method
- [ ] Return 403 for unauthorized attempts
- [ ] Add same changes to auto content deletion

### Phase 3: Admin Override
- [ ] Define admin role/permission model
- [ ] Add `is_admin` check in service layer
- [ ] Allow admins to delete any content
- [ ] Document admin permissions in `docs/authorization.md`

### Phase 4: Rate Limiting
- [ ] Add rate limiting library (slowapi or similar)
- [ ] Configure deletion rate limits
- [ ] Apply to both deletion endpoints
- [ ] Test rate limit enforcement
- [ ] Document rate limits in API docs

### Phase 5: Audit Logging
- [ ] Set up structured logging for deletions
- [ ] Log all deletion attempts (success and failure)
- [ ] Include user_id, content_id, timestamp, result
- [ ] Configure log retention/aggregation
- [ ] Document logging format and location

### Phase 6: Testing
- [ ] Unit test: Authenticated user deletes own content (success)
- [ ] Unit test: Authenticated user tries to delete other's content (403)
- [ ] Unit test: Unauthenticated request (401)
- [ ] Unit test: Admin deletes any content (success)
- [ ] Integration test: Rate limit enforcement
- [ ] E2E test: Full delete flow with auth

### Phase 7: Documentation
- [ ] Update API docs with auth requirements
- [ ] Document error codes (401, 403, 429)
- [ ] Add auth examples to API reference
- [ ] Update frontend integration guide

## Related Security Issues

### Other Endpoints Needing Auth Review
Based on this analysis, the following endpoints may also lack proper auth:

1. **Content Creation**
   - `POST /api/v1/content`
   - `POST /api/v1/content-auto`
   - Should verify authenticated user
   - Should set user_id to current user (not trust client)

2. **Content Update**
   - `PUT /api/v1/content/{content_id}`
   - `PATCH /api/v1/content/{content_id}`
   - Should verify ownership before allowing updates

3. **User Data Modification**
   - Any endpoint that modifies user data
   - Should verify user is modifying their own data

**Action:** Conduct comprehensive auth audit of all endpoints

## Migration Strategy

### For Existing Installations
If delete functionality is already deployed without auth:

1. **Immediate:** Disable delete endpoints in production
2. **Deploy auth fix** with proper testing
3. **Re-enable** delete endpoints with auth enforced
4. **Monitor** audit logs for suspicious activity

### For New Deployments
- Do not deploy delete functionality until auth is implemented
- Block this feature implementation until security controls are in place

## Testing the Fix

### Manual Security Testing
```bash
# Test 1: Unauthenticated deletion (should fail with 401)
curl -X DELETE http://localhost:8001/api/v1/content/123
# Expected: {"detail": "Not authenticated"}

# Test 2: Delete someone else's content (should fail with 403)
curl -X DELETE http://localhost:8001/api/v1/content/123 \
  -H "Authorization: Bearer <user2_token>"
# Expected: {"detail": "You do not have permission to delete this content"}

# Test 3: Delete own content (should succeed)
curl -X DELETE http://localhost:8001/api/v1/content/123 \
  -H "Authorization: Bearer <owner_token>"
# Expected: {"message": "Content 123 deleted successfully"}

# Test 4: Admin deletes any content (should succeed)
curl -X DELETE http://localhost:8001/api/v1/content/123 \
  -H "Authorization: Bearer <admin_token>"
# Expected: {"message": "Content 123 deleted successfully"}

# Test 5: Rate limit (should fail after N requests)
for i in {1..20}; do
  curl -X DELETE http://localhost:8001/api/v1/content/$i \
    -H "Authorization: Bearer <user_token>"
done
# Expected: 429 Too Many Requests after limit reached
```

### Automated Security Tests
Create security test suite in `test/security/test_content_deletion_auth.py`:
- Test unauthorized access
- Test ownership enforcement
- Test admin override
- Test rate limiting
- Test audit logging

## Compliance Considerations

### GDPR Implications
- Users have right to delete their own data
- Platform needs ability to delete user data on request
- Audit logs must record who deleted what

### Data Retention Policies
- Soft delete may be preferable for compliance (already noted in delete-content.md)
- Audit logs should be retained longer than content

## References
- Main feature doc: `notes/active/delete-content.md`
- API routes: `genonaut/api/routes/content.py`, `genonaut/api/routes/content_auto.py`
- Service layer: `genonaut/api/services/content_service.py`
- Repository: `genonaut/api/repositories/base.py`

## Decision Log

### 2025-11-16: Issue Identified
- Discovered during delete feature implementation planning
- Documented as critical blocker for production deployment
- Decision: Implement delete feature for development/testing but do NOT deploy to production without auth

## Next Steps
1. Review existing auth infrastructure in codebase
2. Create separate task for auth implementation
3. Block production deployment of delete feature until auth is complete
4. Consider broader auth audit of all API endpoints
