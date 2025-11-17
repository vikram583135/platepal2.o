import requests

BASE_URL = "http://localhost:3020"
PAYMENTS_ENDPOINT = "/api/payments/payments/"
TIMEOUT = 30

# Example auth token (replace with a real valid token for actual testing)
AUTH_TOKEN = "your_valid_jwt_token_here"

HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def test_process_payment():
    payment_methods_payloads = [
        {
            "payment_method": "credit_card",
            "amount": 100.00,
            "currency": "USD",
            "details": {
                "card_number": "4111111111111111",
                "expiry_month": "12",
                "expiry_year": "2030",
                "cvv": "123",
                "cardholder_name": "John Doe"
            }
        },
        {
            "payment_method": "upi",
            "amount": 50.00,
            "currency": "INR",
            "details": {
                "upi_id": "john.doe@upi"
            }
        },
        {
            "payment_method": "wallet",
            "amount": 25.00,
            "currency": "USD",
            "details": {
                "wallet_id": "wallet_user_123"
            }
        },
        {
            "payment_method": "cash_on_delivery",
            "amount": 75.00,
            "currency": "USD",
            "details": {}
        }
    ]

    for payload in payment_methods_payloads:
        response = None
        try:
            response = requests.post(
                BASE_URL + PAYMENTS_ENDPOINT,
                json=payload,
                headers=HEADERS,
                timeout=TIMEOUT
            )
            assert response.status_code == 200 or response.status_code == 201, (
                f"Failed for payment method {payload['payment_method']}: Unexpected status code {response.status_code}"
            )
            resp_json = response.json()
            # Basic checks for expected keys in response
            assert "payment_id" in resp_json, f"'payment_id' missing in response for {payload['payment_method']}"
            assert resp_json.get("status") in ("success", "pending", "completed"), (
                f"Unexpected payment status for {payload['payment_method']} payment: {resp_json.get('status')}"
            )
        except requests.exceptions.RequestException as e:
            assert False, f"Request failed for payment method {payload['payment_method']}: {str(e)}"
        finally:
            if response is not None:
                response.close()

test_process_payment()
