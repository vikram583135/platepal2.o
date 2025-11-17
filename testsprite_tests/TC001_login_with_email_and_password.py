import requests

def test_login_with_email_and_password():
    base_url = "http://localhost:3020"
    login_endpoint = f"{base_url}/api/auth/token/"
    headers = {
        "Content-Type": "application/json"
    }

    # Provide valid test credentials for login
    payload = {
        "email": "testuser@example.com",
        "password": "TestPassword123!"
    }

    try:
        response = requests.post(login_endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        assert False, f"HTTP request failed: {e}"

    # Validate response status code
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"

    # Validate response content for access and refresh tokens
    json_response = response.json()
    assert "access" in json_response, "Response JSON does not contain 'access' token"
    assert "refresh" in json_response, "Response JSON does not contain 'refresh' token"
    assert isinstance(json_response["access"], str) and len(json_response["access"]) > 0, "'access' token is empty or invalid"
    assert isinstance(json_response["refresh"], str) and len(json_response["refresh"]) > 0, "'refresh' token is empty or invalid"

test_login_with_email_and_password()
