from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from app.slack_security import verify_slack_request
from app.snowflake_client import onboard_user, reset_password
import requests

app = FastAPI()

AUTHORIZED_USERS = [
    "U0ACJ36FF8W",   # Add your Slack user IDs
]


# @app.post("/slack/command")
# async def slack_command(
#     request: Request,
#     user_id: str = Form(...),
#     command: str = Form(...),
#     text: str = Form(...),
#     response_url: str = Form(...)
# ):

#     body = await request.body()

#     if not verify_slack_request(request.headers, body.decode()):
#         return JSONResponse({"text": "Invalid Slack signature"}, status_code=401)

#     if user_id not in AUTHORIZED_USERS:
#         return {"text": "❌ You are not authorized to perform this action"}

#     args = text.split()

#     if len(args) < 1:
#         return {"text": "Invalid command format"}

#     action = args[0]

#     # -------- ONBOARD USER ----------
#     if action == "onboard_user":

#         if len(args) != 3:
#             return {"text": "Usage: /snowflake onboard_user <username> <role>"}

#         username = args[1]
#         role = args[2]

#         success, result = onboard_user(username, role)

#         if success:
#             message = f"""
# ✅ User Created Successfully

# Username: {username}
# Role: {role}
# Temporary Password: `{result}`
# """
#         else:
#             message = f"❌ Error: {result}"

#     # -------- RESET PASSWORD ----------
#     elif action == "reset_password":

#         if len(args) != 2:
#             return {"text": "Usage: /snowflake reset_password <username>"}

#         username = args[1]

#         success, result = reset_password(username)

#         if success:
#             message = f"""
# ✅ Password Reset Successful

# Username: {username}
# Temporary Password: `{result}`
# """
#         else:
#             message = f"❌ Error: {result}"

#     else:
#         message = "❌ Unknown command"

#     # Send async response
#     requests.post(response_url, json={"text": message})

#     return {"text": "⏳ Processing your request..."}

def process_command(text, response_url):

    args = text.split()

    if len(args) < 1:
        requests.post(response_url, json={"text": "Invalid command format"})
        return

    action = args[0]

    # -------- ONBOARD USER ----------
    if action == "onboard_user":

        if len(args) != 3:
            requests.post(response_url, json={
                "text": "Usage: /snowflake onboard_user <username> <role>"
            })
            return

        username = args[1]
        role = args[2]

        success, result = onboard_user(username, role)

        if success:
            message = f"""
✅ User Created Successfully

Username: {username}
Role: {role}
Temporary Password: `{result}`
"""
        else:
            message = f"❌ Error: {result}"

    # -------- RESET PASSWORD ----------
    elif action == "reset_password":

        if len(args) != 2:
            requests.post(response_url, json={
                "text": "Usage: /snowflake reset_password <username>"
            })
            return

        username = args[1]

        success, result = reset_password(username)

        if success:
            message = f"""
✅ Password Reset Successful

Username: {username}
Temporary Password: `{result}`
"""
        else:
            message = f"❌ Error: {result}"

    else:
        message = "❌ Unknown command"

    # ---------- Send Result Back To Slack ----------
    requests.post(response_url, json={"text": message})


@app.post("/slack/command")
async def slack_command(
    request: Request,
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    command: str = Form(...),
    text: str = Form(...),
    response_url: str = Form(...)
):

    # ---------- FIX 1: Get raw body correctly ----------
    raw_body = (await request.body()).decode("utf-8")

    # ---------- Verify Slack Signature ----------
    if not verify_slack_request(request.headers, raw_body):
        return JSONResponse({"text": "Invalid Slack signature"}, status_code=401)

    # ---------- Authorization ----------
    if user_id not in AUTHORIZED_USERS:
        return {"text": "❌ You are not authorized to perform this action"}

    # ---------- ACK Slack Immediately (IMPORTANT) ----------
    background_tasks.add_task(process_command, text, response_url)

    return {
        "response_type": "ephemeral",
        "text": "⏳ Processing your request..."
    }


