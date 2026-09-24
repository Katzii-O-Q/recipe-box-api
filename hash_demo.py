from werkzeug.security import generate_password_hash, check_password_hash

SAMPLE_PASSWORD = "CorrectHorseBatteryStaple!123"  # fake sample

def main():
    password_hash = generate_password_hash(SAMPLE_PASSWORD)

    print("Generated hash:")
    print(password_hash)
    print()

    # Check correct password
    is_correct = check_password_hash(password_hash, SAMPLE_PASSWORD)
    print("Check correct password ->", is_correct)

    # Check wrong password
    is_wrong = check_password_hash(password_hash, "WrongPassword!999")
    print("Check wrong password   ->", is_wrong)

if __name__ == "__main__":
    main()