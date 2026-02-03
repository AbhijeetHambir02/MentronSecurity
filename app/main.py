from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from app.slack_security import verify_slack_request
from app.snowflake_client import onboard_user, reset_password
import requests
from urllib.parse import parse_qs
import os
from dotenv import load_dotenv

load_dotenv()

auth_user = os.getenv("AUTH_USER")

app = FastAPI()


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
            User Created Successfully!

            Username: {username}
            Role: {role}
            Temporary Password: `{result}`
            """
        else:
            message = f"Error: {result}"

    # -------- RESET PASSWORD ----------
    elif action == "reset_password":

        if len(args) != 2:
            requests.post(response_url, json={
                "text": "Usage: /snowflake reset_password <username> <password>"
            })
            return

        username = args[1]

        success, result = reset_password(username)

        if success:
            message = f"""
            Password Reset Successful!

            Username: {username}
            New Password: `{result}`
            """
        else:
            message = f"Error: {result}"

    else:
        message = "Unknown command"

    # Send Result Back To Slack
    requests.post(response_url, json={"text": message})


@app.post("/slack/command")
async def slack_command(request: Request, background_tasks: BackgroundTasks):

    # Read RAW Body FIRST 
    raw_body = (await request.body()).decode("utf-8")

    # Verify Slack Signature
    if not verify_slack_request(request.headers, raw_body):
        return JSONResponse({"text": "Invalid Slack signature"}, status_code=401)

    # Parse Slack Form Data
    form_data = parse_qs(raw_body)

    user_id = form_data.get("user_id", [""])[0]
    text = form_data.get("text", [""])[0]
    response_url = form_data.get("response_url", [""])[0]

    # Authorization
    if user_id not in auth_user:
        return {
            "response_type": "ephemeral",
            "text": "You are not authorized"
        }

    # Process in Background
    background_tasks.add_task(process_command, text, response_url)

    return {
        "response_type": "ephemeral",
        "text": "⏳ Processing your request..."
    }

