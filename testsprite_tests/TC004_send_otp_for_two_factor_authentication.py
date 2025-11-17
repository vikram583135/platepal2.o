import requests

def test_send_otp_for_two_factor_authentication():
    base_url = "http://localhost:3020"
    url = f"{base_url}/api/auth/otp/send/"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "email": "testuser@example.com"
    }
    timeout = 30

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
        json_response = response.json()
        assert "detail" in json_response or "message" in json_response or json_response.get("success", False) or json_response.get("otp_sent", False), \
            "Response does not indicate OTP send success"
    except requests.exceptions.RequestException as e:
        assert False, f"Request failed: {e}"

test_send_otp_for_two_factor_authentication()