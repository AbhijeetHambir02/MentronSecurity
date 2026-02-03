import snowflake.connector
import os
from dotenv import load_dotenv
import secrets
import string

load_dotenv()

def get_connection():
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        role=os.getenv("SNOWFLAKE_ROLE"),
    )
    return conn


def onboard_user(username, role):
    conn = get_connection()
    cursor = conn.cursor()

    temp_password = "Temp@" + username + "123"

    try:
        cursor.execute(
            f"CREATE USER {username} PASSWORD='{temp_password}' MUST_CHANGE_PASSWORD=TRUE"
        )

        cursor.execute(
            f"GRANT ROLE {role} TO USER {username}"
        )

        return True, temp_password

    except Exception as e:
        return False, str(e)

    finally:
        cursor.close()
        conn.close()


def generate_password(length=12):
    """
    Generates a strong password containing:
    - Uppercase letters
    - Lowercase letters
    - Numbers
    - Special characters
    """

    if length < 8:
        raise ValueError("Password length must be at least 8 characters")

    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*()-_=+[]{}|;:,.<>?/"

    # Ensure minimum one character from each category
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]

    # Fill remaining characters
    all_chars = uppercase + lowercase + digits + special

    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))

    # Shuffle to avoid predictable pattern
    secrets.SystemRandom().shuffle(password)

    return "".join(password)


def reset_password(username):
    conn = get_connection()
    cursor = conn.cursor()

    password = generate_password()
    try:
        cursor.execute(
            f"ALTER USER {username} SET PASSWORD='{password}' MUST_CHANGE_PASSWORD=TRUE"
        )

        return True, password

    except Exception as e:
        return False, str(e)

    finally:
        cursor.close()
        conn.close()
