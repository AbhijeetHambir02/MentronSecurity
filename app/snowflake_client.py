import snowflake.connector
import os
from dotenv import load_dotenv

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


def reset_password(username, password):
    conn = get_connection()
    cursor = conn.cursor()

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
