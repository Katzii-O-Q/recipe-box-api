## 1. Target Layout

app/
    __init__.py
    auth.py
    recipes.py
    db.py
    config.py

## 2. Responsibilities in current app.py
- User account management (register/login)
- Authorization (protected routes)
- Communicating with the database (SQLite)
- Recipe operations (CRUD)
- Configuration (JWT secret & database file)

Total responsibilities identified: 5

## 3. Acceptance list (public contract)
- GET /recipes --> 200
- GET /recipes/<id> --> 200
- POST /recipes --> 201
- PATCH /recipes/<id> --> 200
- POST /register --> 201
- POST /login --> 200
- DELETE /recipes/<id> --> 204

Total acceptance items: 7

## 4. Refactor boundary
This refactor may change the internal file/module structure of the app (for example, moving auth, recipes, DB, and config into separate modules), but it must not change the public contract. All existing endpoints, methods, required inputs, status codes, and important response fields must stay the same.