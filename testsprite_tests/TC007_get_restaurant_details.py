import requests

BASE_URL = "http://localhost:3020"
TIMEOUT = 30

# Assuming no authentication info was provided, so this example does not authenticate.
# In real scenario, add JWT token in headers if required, e.g.:
# HEADERS = {"Authorization": f"Bearer {token}"}

def test_get_restaurant_details():
    headers = {
        "Accept": "application/json"
    }
    # Step 1: Get list of restaurants to obtain a valid restaurant id
    try:
        list_resp = requests.get(f"{BASE_URL}/api/restaurants/restaurants/", headers=headers, timeout=TIMEOUT)
        assert list_resp.status_code == 200, f"Failed to list restaurants, status code: {list_resp.status_code}"
        restaurants = list_resp.json()
        assert isinstance(restaurants, list), "Restaurants response is not a list"
        assert len(restaurants) > 0, "No restaurants found to test details endpoint"
        restaurant_id = None
        # The endpoint in PRD /api/restaurants/restaurants/ returns list. 
        # The format of each restaurant in list is unknown, we assume each has 'id' key.
        for r in restaurants:
            if isinstance(r, dict) and 'id' in r:
                restaurant_id = r['id']
                break
        assert restaurant_id is not None, "No valid restaurant id found in list response"

        # Step 2: Query the details endpoint for that restaurant id
        details_resp = requests.get(f"{BASE_URL}/api/restaurants/restaurants/{restaurant_id}/", headers=headers, timeout=TIMEOUT)
        assert details_resp.status_code == 200, f"Failed to get restaurant details, status code: {details_resp.status_code}"
        details = details_resp.json()
        assert isinstance(details, dict), "Restaurant details response is not a dictionary"
        assert details.get("id") == restaurant_id, "Returned restaurant id does not match requested id"
        # Additional possible validations:
        # eg. check for expected keys in details like name, address, cuisine, rating etc if known
        expected_keys = ["id", "name", "address", "cuisine", "rating"]
        missing_keys = [key for key in expected_keys if key not in details]
        assert not missing_keys, f"Missing expected keys in restaurant details: {missing_keys}"

    except requests.RequestException as e:
        assert False, f"HTTP request failed: {e}"

test_get_restaurant_details()
