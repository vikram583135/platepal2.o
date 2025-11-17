import requests

def test_login_with_biometric_authentication():
    base_url = "http://localhost:3020"
    url = f"{base_url}/api/auth/biometric-auth/login/"
    headers = {
        "Content-Type": "application/json"
    }
    # Updated payload for biometric auth
    payload = {
        "biometric_token": "example-token"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not in JSON format"
    
    # Based on JWT-based auth mentioned in PRD, expect access and refresh tokens
    assert "access" in data, "Response JSON does not contain 'access' token"
    assert "refresh" in data, "Response JSON does not contain 'refresh' token"

test_login_with_biometric_authentication()
