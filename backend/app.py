from flask import Flask, request, jsonify
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from flask_cors import CORS
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Allow OAuth to work on http://localhost
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

flow = Flow.from_client_config(
    {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uris": [REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    },
    scopes=["https://www.googleapis.com/auth/calendar"]
)

flow.redirect_uri = REDIRECT_URI

# Store Google credentials in memory
credentials = None


@app.route("/auth-url")
def auth_url():
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        include_granted_scopes="true"
    )
    return jsonify({"url": auth_url})


@app.route("/oauth2callback")
def oauth2callback():
    global credentials
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    return "Authentication successful. You can close this tab."


@app.route("/is-authenticated")
def is_authenticated():
    global credentials
    return {"authenticated": credentials is not None}


@app.route("/create-events", methods=["POST"])
def create_events():
    global credentials
    if not credentials:
        return jsonify({"error": "Not authenticated with Google"}), 401

    data = request.json
    events = data.get("events", [])

    service = build("calendar", "v3", credentials=credentials)

    created = []
    for event in events:
        response = service.events().insert(
            calendarId="primary",
            body={
                "summary": event["summary"],
                "start": {"dateTime": event["start"], "timeZone": "America/New_York"},
                "end": {"dateTime": event["end"], "timeZone": "America/New_York"},
            },
        ).execute()
        created.append(response)

    return jsonify({"created": created})


@app.route("/disconnect")
def disconnect():
    global credentials
    credentials = None
    return "Disconnected"


if __name__ == "__main__":
    app.run(port=5000, debug=True)