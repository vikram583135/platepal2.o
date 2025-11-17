import requests

BASE_URL = "http://localhost:3020"
TOKEN_URL = f"{BASE_URL}/api/auth/token/"
REFRESH_URL = f"{BASE_URL}/api/auth/token/refresh/"
TIMEOUT = 30

def test_refresh_access_token():
    # Use a valid test user to login and get a refresh token
    login_payload = {
        "email": "testuser@example.com",
        "password": "TestPassword123!"
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        login_response = requests.post(TOKEN_URL, json=login_payload, headers=headers, timeout=TIMEOUT)
        assert login_response.status_code == 200, f"Login failed with status code {login_response.status_code}"
        tokens = login_response.json()
        assert "refresh" in tokens, "Refresh token not found in login response"
        refresh_token = tokens["refresh"]

        refresh_payload = {
            "refresh": refresh_token
        }

        refresh_response = requests.post(REFRESH_URL, json=refresh_payload, headers=headers, timeout=TIMEOUT)
        assert refresh_response.status_code == 200, f"Refresh token request failed with status code {refresh_response.status_code}"
        refresh_data = refresh_response.json()
        assert "access" in refresh_data, "Access token not returned in refresh response"
        new_access_token = refresh_data["access"]
        assert isinstance(new_access_token, str) and len(new_access_token) > 0, "Invalid access token returned"

    except requests.exceptions.RequestException as e:
        assert False, f"HTTP request failed: {e}"

test_refresh_access_token()
