from app import create_app
from app.db_utils import init_db

app = create_app("testing")

# explicitly create tables in recipes-test.db
init_db(app)

print("APP_IDENTITY:", app.config["APP_IDENTITY"])
print("DATABASE:", app.config["DATABASE"])

with app.test_client() as client:
    # 1) Register a new user in the TEST database
    register_payload = {
        "username": "testuser1",
        "email": "testuser1@example.com",
        "password": "testpassword123"
    }
    reg_resp = client.post("/register",
json=register_payload)
    print("REGISTER status:", reg_resp.status_code)
    print("REGISTER json:", reg_resp.get_json())

    # 2) Login with that same user
    login_payload = {
        "username": "testuser1",
        "password": "testpassword123"
    }
    login_resp = client.post("/login", json=login_payload)
    print("LOGIN status:", login_resp.status_code)
    print("LOGIN json:", login_resp.get_json())