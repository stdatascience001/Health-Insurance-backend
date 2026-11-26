import msal
import secrets
from itsdangerous import URLSafeTimedSerializer
from app.core.config import settings

MICROSOFT_AUTHORITY = (
    f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}"
)

MICROSOFT_SCOPES = ["User.Read"]


# creates the Microsoft authentication client using your application credentials.
def get_microsoft_client():
    """
    Create an MSAL confidential client application.
    """

    return msal.ConfidentialClientApplication(
        client_id=settings.MICROSOFT_CLIENT_ID,
        authority=MICROSOFT_AUTHORITY,
        client_credential=settings.MICROSOFT_CLIENT_SECRET,
    )


# generates the URL where the admin will sign in.
def get_microsoft_login_url(state: str):
    """
    Generate the Microsoft login URL.
    """

    microsoft_app = get_microsoft_client()

    return microsoft_app.get_authorization_request_url(
        scopes=MICROSOFT_SCOPES,
        redirect_uri=settings.MICROSOFT_REDIRECT_URI,
        state=state,
        prompt="select_account",
    )


# exchanges the authorization code received from Microsoft for an access token.
def get_microsoft_user_token(code: str):
    """
    Exchange the authorization code for Microsoft access tokens.
    """

    microsoft_app = get_microsoft_client()

    result = microsoft_app.acquire_token_by_authorization_code(
        code=code,
        scopes=MICROSOFT_SCOPES,
        redirect_uri=settings.MICROSOFT_REDIRECT_URI,
    )

    if "error" in result:
        raise ValueError(
            result.get("error_description", "Microsoft authentication failed.")
        )

    return result

# This protects the OAuth callback against CSRF attacks. The state expires after 10 minutes.
def generate_oauth_state():
    """
    Generate a signed, unpredictable OAuth state.
    """

    serializer = URLSafeTimedSerializer(
        settings.SECRET_KEY, salt="microsoft-oauth-state"
    )

    return serializer.dumps(secrets.token_urlsafe(32))


def verify_oauth_state(state: str):
    """
    Validate OAuth state and its expiration.
    """

    serializer = URLSafeTimedSerializer(
        settings.SECRET_KEY, salt="microsoft-oauth-state"
    )

    try:
        serializer.loads(state, max_age=600)
        return True
    except Exception:
        return False
