# Security baseline

2026-09-24

- GET /recipes → 200 OK, returns all recipes to anonymous requester
- POST /recipes → 201 CREATED, anonymous requester can create recipes
- PATCH /recipes/1 → 200 OK, anonymous requester can change existing recipe
- DELETE /recipes/1 → 204 NO CONTENT, anonymous requester can delete an existing recipe