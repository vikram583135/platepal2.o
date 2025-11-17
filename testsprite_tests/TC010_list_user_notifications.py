import requests

def test_list_user_notifications():
    base_url = "http://localhost:3020"
    login_url = f"{base_url}/api/auth/token/"
    notifications_url = f"{base_url}/api/notifications/"
    email = "testuser@example.com"
    password = "TestPassword123!"
    timeout = 30

    # Step 1: Authenticate user to get JWT tokens
    login_payload = {
        "email": email,
        "password": password
    }
    try:
        login_response = requests.post(login_url, json=login_payload, timeout=timeout)
        assert login_response.status_code == 200, f"Login failed with status code {login_response.status_code}"
        tokens = login_response.json()
        assert "access" in tokens, "Access token not found in login response"
        access_token = tokens["access"]
    except requests.RequestException as e:
        assert False, f"Login request failed: {e}"

    # Step 2: Use access token to get user notifications
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    try:
        notif_response = requests.get(notifications_url, headers=headers, timeout=timeout)
        assert notif_response.status_code == 200, f"Notification request failed with status code {notif_response.status_code}"
        notifications = notif_response.json()
        assert isinstance(notifications, list), "Notifications response is not a list"
        # Additional validation can be done here based on notifications structure if known
    except requests.RequestException as e:
        assert False, f"Notification request failed: {e}"

test_list_user_notifications()
