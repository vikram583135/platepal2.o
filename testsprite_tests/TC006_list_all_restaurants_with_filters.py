import requests

BASE_URL = "http://localhost:3020"
TIMEOUT = 30

# Placeholder token, adjust as appropriate
AUTH_TOKEN = "Bearer your_valid_jwt_token_here"

def test_list_all_restaurants_with_filters():
    url = f"{BASE_URL}/api/restaurants/restaurants/"
    headers = {
        "Accept": "application/json",
        "Authorization": AUTH_TOKEN
    }

    # Define filter parameters to test
    params_list = [
        {"search": "pizza", "cuisine": None, "rating": None},
        {"search": None, "cuisine": "Italian", "rating": None},
        {"search": None, "cuisine": None, "rating": 4},
        {"search": "sushi", "cuisine": "Japanese", "rating": 5},
        {"search": "", "cuisine": "", "rating": None}  # empty filters, should return all
    ]

    for params in params_list:
        # Clean params to exclude None values
        query_params = {k: v for k, v in params.items() if v is not None and v != ""}
        try:
            response = requests.get(url, headers=headers, params=query_params, timeout=TIMEOUT)
            assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
            data = response.json()
            assert isinstance(data, list), "Response should be a list of restaurants"

            # Verify filtering if filters applied
            for restaurant in data:
                if "search" in query_params:
                    search_lower = query_params["search"].lower()
                    name = restaurant.get("name", "").lower()
                    description = restaurant.get("description", "").lower() if restaurant.get("description") else ""
                    assert search_lower in name or search_lower in description, \
                        f"Restaurant does not match search filter: {restaurant}"
                if "cuisine" in query_params:
                    cuisine_filter = query_params["cuisine"].lower()
                    cuisines = [c.lower() for c in restaurant.get("cuisines", [])] if isinstance(restaurant.get("cuisines"), list) else []
                    assert cuisine_filter in cuisines, f"Restaurant does not match cuisine filter: {restaurant}"
                if "rating" in query_params:
                    rating_filter = float(query_params["rating"])
                    rating = float(restaurant.get("rating", 0))
                    assert rating >= rating_filter, f"Restaurant rating lower than filter: {restaurant}"

        except requests.RequestException as e:
            assert False, f"Request failed: {e}"

test_list_all_restaurants_with_filters()