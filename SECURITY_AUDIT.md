# Security Audit - Recipes API

## Safe password storage
- Inspection: users table
- Observed: password field is hashed and unreadable
- Conclusion: ✅ Passwords are not stored in plaintext

## Authentication (401)
- Request: DELETE /recipes/2 (no authorization header)
- Observed: 401 UNAUTHORIZED, "missing or invalid authroization header"
- Conclusion: ✅ Protected actions require authentication

## Authorization - ownership / roles (403)
- Request: DELETE /recipes/2 as non-owner, non-admin
- Observed: 403 FORBIDDEN, "access denied. You cannot delete this recipe"
- Conclusion: ✅ Authenticated but unauthorized users are blocked

- Request: DELETE /recipes/2 as owner
- Observed: 204 NO CONTENT
- Conclusion: ✅ Owner can delete their own recipe

## Privacy / lising behavior
- Intended: Anonymous GET /recipes should only return recipes where `is_public = true`.
- Request: GET /recipes as anonymous
- Observed: All recipes are returned, including `is_public = false`.
- Conclusion: ❌ Bug - list endpoint ignores `is_public` flag and leaks private recipes.

## Regression agains old exploits
- Old exploit: anonymous user could perform actions on recipes.
- Current: destructive actions (e.g. DELETE /recipes/:id) now require auth and enforce ownership/role checks.
- Status: ✅ Exploit closed for protected actions; ❌ privacy still broken on list-all endpoint.