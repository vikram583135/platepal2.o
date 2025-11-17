import requests

def test_verify_otp():
    base_url = "http://localhost:3020"
    otp_send_url = f"{base_url}/api/auth/otp/send/"
    otp_verify_url = f"{base_url}/api/auth/otp/verify/"
    headers = {"Content-Type": "application/json"}
    timeout = 30

    # For test purposes, use a test email
    test_email = "testuser@example.com"

    try:
        # Step 1: Send OTP
        send_payload = {"email": test_email}
        send_response = requests.post(otp_send_url, json=send_payload, headers=headers, timeout=timeout)
        assert send_response.status_code == 200, f"Failed to send OTP, status code: {send_response.status_code}"
        send_data = send_response.json()
        assert "otp" in send_data or "detail" in send_data, "OTP not sent successfully."

        # Assuming OTP is returned in response for test environment or fetched via mock
        # If OTP not returned, test cannot proceed further automatically.
        otp = send_data.get("otp")
        if not otp:
            raise ValueError("No OTP received in send response; manual input needed or test environment must provide OTP.")

        # Step 2: Verify OTP
        verify_payload = {
            "email": test_email,
            "otp": otp
        }
        verify_response = requests.post(otp_verify_url, json=verify_payload, headers=headers, timeout=timeout)
        assert verify_response.status_code == 200, f"OTP verification failed with status code {verify_response.status_code}"
        verify_data = verify_response.json()
        # Assumption: Successful verification returns JSON with success message or token
        assert verify_data.get("detail") == "OTP verified successfully" or "token" in verify_data, "OTP verification response invalid"

    except requests.RequestException as e:
        assert False, f"HTTP request failed: {e}"
    except AssertionError as e:
        assert False, f"Assertion failed: {e}"


test_verify_otp()
