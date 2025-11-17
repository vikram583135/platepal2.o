import requests

BASE_URL = "http://localhost:3020"
TIMEOUT = 30

# Dummy credentials for authentication - replace with valid test user credentials
AUTH_EMAIL = "testuser@example.com"
AUTH_PASSWORD = "TestPassword123!"

def test_create_new_order():
    try:
        # Step 1: Authenticate user to obtain JWT access token
        auth_url = f"{BASE_URL}/api/auth/token/"
        auth_payload = {
            "email": AUTH_EMAIL,
            "password": AUTH_PASSWORD
        }
        auth_headers = {
            "Content-Type": "application/json"
        }
        auth_response = requests.post(auth_url, json=auth_payload, headers=auth_headers, timeout=TIMEOUT)
        assert auth_response.status_code == 200, f"Authentication failed: {auth_response.text}"
        tokens = auth_response.json()
        access_token = tokens.get("access")
        assert access_token, "Access token not found in authentication response"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Step 2: Get list of restaurants to obtain a valid restaurant_id
        restaurants_url = f"{BASE_URL}/api/restaurants/restaurants/"
        restaurants_response = requests.get(restaurants_url, headers=headers, timeout=TIMEOUT)
        assert restaurants_response.status_code == 200, f"Failed to list restaurants: {restaurants_response.text}"
        restaurants = restaurants_response.json()
        assert isinstance(restaurants, list) and len(restaurants) > 0, "No restaurants found for order creation"
        restaurant_id = restaurants[0].get("id")
        assert restaurant_id, "Restaurant ID missing in restaurants list"

        # Step 3: Get menu items for the chosen restaurant to prepare order items
        menu_url = f"{BASE_URL}/api/restaurants/restaurants/{restaurant_id}/menu/"
        menu_response = requests.get(menu_url, headers=headers, timeout=TIMEOUT)
        assert menu_response.status_code == 200, f"Failed to get menu: {menu_response.text}"
        menu_items = menu_response.json()
        assert isinstance(menu_items, list) and len(menu_items) > 0, "No menu items found for the selected restaurant"

        # Prepare items list with at least one item and quantity (assuming quantity 1)
        item_id = menu_items[0].get("id")
        assert item_id, "Menu item ID missing"
        items = [{"item_id": item_id, "quantity": 1}]

        # Step 4: Get delivery addresses
        profile_url = f"{BASE_URL}/api/accounts/profile/"
        profile_response = requests.get(profile_url, headers=headers, timeout=TIMEOUT)
        if profile_response.status_code != 200 or not profile_response.json().get("delivery_addresses"):
            orders_url = f"{BASE_URL}/api/orders/orders/"
            orders_response = requests.get(orders_url, headers=headers, timeout=TIMEOUT)
            assert orders_response.status_code == 200, f"Failed to list orders: {orders_response.text}"
            orders = orders_response.json()
            delivery_address_id = None
            for order in orders:
                if order.get("delivery_address_id"):
                    delivery_address_id = order["delivery_address_id"]
                    break
            assert delivery_address_id, "No delivery address id found from previous orders"
        else:
            delivery_addresses = profile_response.json().get("delivery_addresses")
            assert isinstance(delivery_addresses, list) and len(delivery_addresses) > 0, "No delivery addresses found"
            delivery_address_id = delivery_addresses[0].get("id")
            assert delivery_address_id, "Delivery address ID missing"

        # Step 5: Create new order
        create_order_url = f"{BASE_URL}/api/orders/orders/"
        order_payload = {
            "restaurant_id": restaurant_id,
            "items": items,
            "delivery_address_id": delivery_address_id
        }
        order_response = requests.post(create_order_url, json=order_payload, headers=headers, timeout=TIMEOUT)
        assert order_response.status_code == 201, f"Order creation failed: {order_response.status_code} - {order_response.text}"
        order_data = order_response.json()
        assert order_data.get("id"), "Order ID missing in response"
        assert order_data.get("restaurant_id") == restaurant_id, "Restaurant ID mismatch in order response"
        assert order_data.get("delivery_address_id") == delivery_address_id, "Delivery address ID mismatch in order response"
        assert isinstance(order_data.get("items"), list) and len(order_data["items"]) > 0, "Order items missing in response"

    except (requests.RequestException, AssertionError) as e:
        assert False, f"Test failed due to error: {str(e)}"


test_create_new_order()
