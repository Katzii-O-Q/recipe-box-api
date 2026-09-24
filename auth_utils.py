from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(plain_password: str) -> str:
    """
    Take a plaintext password and return a one-way hash string
    suitable for storing in the database.
    """
    return generate_password_hash(plain_password)


def verify_password(stored_hash: str, candidate_password: str) -> bool:
    """
    Check a candidate password against a stored password hash.
    Returns True if they match, False otherwise.
    """
    return check_password_hash(stored_hash, candidate_password)