# Bookmark Feature Security Review

**Task**: 14.5 Security review (ensure user_id constraints work, test RLS)
**Date**: 2025-11-14
**Status**: COMPLETE

## Executive Summary

The bookmark feature implements **database-level** Row-Level Security (RLS) via composite foreign key constraints. These constraints are **working correctly** and prevent cross-user data contamination. However, there is **NO API-level authentication**, which creates a critical security vulnerability for production deployment.

### Security Posture

- [x] **Database Level (GOOD)**: Composite FK constraints prevent data corruption
- [ ] **API Level (CRITICAL ISSUE)**: No authentication - user_id accepted as query parameter

## Database-Level Security (VERIFIED WORKING)

### 1. Composite Foreign Keys for RLS

**Implementation**: The `bookmark_category_members` table enforces same-user constraints via composite FKs:

```sql
-- Composite FK to bookmarks table
FOREIGN KEY (bookmark_id, user_id)
REFERENCES bookmarks(id, user_id)

-- Composite FK to bookmark_categories table
FOREIGN KEY (category_id, user_id)
REFERENCES bookmark_categories(id, user_id)
```

**What This Prevents**:
- User A cannot add User B's bookmark to User A's category
- User A cannot add User A's bookmark to User B's category
- Cannot create membership with wrong user_id even if bookmark and category belong to same user

**Test Coverage**:
- test_composite_fk_prevents_cross_user_bookmark_to_category: PASSED
- test_composite_fk_allows_same_user_bookmark_to_category: PASSED
- test_composite_fk_prevents_wrong_user_id_in_membership: PASSED

### 2. Hierarchical Category Constraints

**Implementation**: Self-referential FK with composite constraint:

```sql
FOREIGN KEY (parent_id, user_id)
REFERENCES bookmark_categories(id, user_id)
```

**What This Prevents**:
- User B cannot create a child category with User A's category as parent
- Ensures entire category tree belongs to single user

**Test Coverage**:
- test_category_parent_must_belong_to_same_user: PASSED

### 3. Unique Constraints

**Implementation**: Prevents duplicate bookmarks per user:

```sql
UNIQUE (user_id, content_id, content_source_type)
```

**What This Prevents**:
- User cannot bookmark same content twice
- Still allows different users to bookmark same content

**Test Coverage**:
- test_unique_bookmark_per_user_content: PASSED
- test_different_users_can_bookmark_same_content: PASSED

## API-Level Security (CRITICAL ISSUE)

### Missing Authentication

**Finding**: The API endpoints accept `user_id` as a **query parameter** without any authentication or authorization layer.

**Evidence**:

1. **Endpoint Example** (genonaut/api/routes/bookmarks.py:55-67):
```python
@router.get("/", response_model=BookmarkListResponse)
async def list_bookmarks(
    user_id: UUID = Query(..., description="User ID to list bookmarks for"),
    # ... other parameters
):
```

2. **No Authentication Middleware** (genonaut/api/middleware/security_middleware.py:232-243):
```python
def _get_user_id(self, request: Request) -> Optional[str]:
    """Get user ID from request (if authenticated)."""
    # This would depend on your authentication system
    # For now, return None as we don't have auth implemented
    return None
```

**Impact**:
- Any client can access any user's bookmarks by changing `user_id` query parameter
- Any client can create/modify/delete bookmarks for any user
- Example vulnerable request:
  ```bash
  # Attacker can access any user's bookmarks by changing user_id
  curl "http://localhost:8001/api/v1/bookmarks?user_id=VICTIM_USER_ID"
  ```

### Security Gaps

1. **No JWT/Session Validation**: No token-based auth
2. **No User Identity Verification**: API doesn't verify requester matches user_id
3. **Query Parameter Trust**: Blindly trusts user_id from query string
4. **No Rate Limiting on User Endpoints**: RateLimitMiddleware exists but doesn't protect bookmark endpoints

## Service-Layer Validation (PARTIAL)

**Good**: Service layer validates same-user constraints (genonaut/api/services/bookmark_category_member_service.py:48-51):

```python
# Verify bookmark and category belong to same user
if bookmark.user_id != category.user_id:
    raise ValidationError("Bookmark and category must belong to the same user")
```

**Limitation**: This only prevents cross-user bookmark-to-category assignments when both entities already exist. It doesn't prevent unauthorized access to either entity in the first place.

## Test Coverage Summary

### Created Test File
- `test/db/unit/test_bookmark_security.py` (345 lines)
- 6 tests, all passing
- Comprehensive coverage of composite FK constraints

### Tests Created

**RLS Tests (4)**:
1. test_composite_fk_prevents_cross_user_bookmark_to_category
2. test_composite_fk_allows_same_user_bookmark_to_category
3. test_composite_fk_prevents_wrong_user_id_in_membership
4. test_category_parent_must_belong_to_same_user

**Unique Constraint Tests (2)**:
5. test_unique_bookmark_per_user_content
6. test_different_users_can_bookmark_same_content

### Missing Tests

**API Security Tests**: NO tests verify that:
- Users cannot access other users' data via API
- Invalid user_id values are rejected
- Authentication tokens are required/validated

## Recommendations

### Before Production

1. **CRITICAL: Implement Authentication**
   - Add JWT or session-based authentication
   - Create auth middleware to validate tokens
   - Extract user_id from authenticated session, not query params
   - Update all endpoints to use authenticated user context

2. **HIGH: Update Endpoints**
   ```python
   # CURRENT (INSECURE)
   @router.get("/")
   async def list_bookmarks(
       user_id: UUID = Query(...),
       # ...
   )

   # RECOMMENDED (SECURE)
   from fastapi import Depends
   from genonaut.api.auth import get_current_user

   @router.get("/")
   async def list_bookmarks(
       current_user: User = Depends(get_current_user),
       # ...
   ):
       user_id = current_user.id  # Use authenticated user's ID
   ```

3. **MEDIUM: Add API Security Tests**
   - Test unauthorized access attempts fail
   - Test users cannot access other users' data
   - Test authentication token validation

4. **LOW: Add Rate Limiting**
   - Extend RateLimitMiddleware to cover bookmark endpoints
   - Implement per-user rate limits

### Development/Testing

Current state is acceptable for:
- Local development
- Testing environments
- Demos with trusted users

**NOT acceptable for**:
- Production deployment
- Any environment accessible to untrusted users
- Cloud-hosted instances

## Architecture Decisions

### Why Composite FK RLS?

The team chose composite foreign keys instead of application-level checks because:

1. **Database Enforcement**: Cannot be bypassed by application bugs
2. **Performance**: No need for additional WHERE clauses on every query
3. **Data Integrity**: Guarantees consistency even if application code has bugs
4. **Partitioned Table Support**: Required for content_items_all partitioning by source_type

### Tradeoffs

**Pros**:
- Bulletproof data integrity at database level
- Cannot be bypassed even with SQL injection
- Clear error messages when constraint violated

**Cons**:
- More complex schema (composite keys, additional user_id columns)
- Slightly larger index sizes
- Requires careful FK setup during schema design

## Files Modified/Created

### Created
- `test/db/unit/test_bookmark_security.py` - Security test suite (345 lines)
- `notes/bookmark-security-review.md` - This report

### Reviewed
- `genonaut/db/schema.py` - Verified composite FK constraints (lines 1432-1629)
- `genonaut/api/routes/bookmarks.py` - Identified missing auth (lines 1-264)
- `genonaut/api/routes/bookmark_categories.py` - Identified missing auth (lines 1-290)
- `genonaut/api/middleware/security_middleware.py` - Confirmed no auth (line 242-243)
- `genonaut/api/services/bookmark_category_member_service.py` - Verified validation logic (line 50)

## Conclusion

**Database security is solid**. The composite foreign key constraints correctly prevent cross-user data contamination and all tests pass.

**API security is missing**. There is no authentication layer, which is a **blocker for production deployment**.

For production, implement:
1. JWT/session authentication
2. Auth middleware
3. Update endpoints to use authenticated user context
4. Add API security tests

The current implementation is a good foundation - the hard part (database constraints) is done correctly. Adding API auth is the remaining critical task before production deployment.
