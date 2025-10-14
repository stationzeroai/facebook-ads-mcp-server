"""
Meta Ads targeting and utility tools.

This module provides helper functions for ad targeting, including interest search,
region resolution, and pixel management.
"""

import json
from typing import List, Optional
from .api import (
    FB_GRAPH_URL,
    get_access_token,
    get_act_id,
    _make_graph_api_call
)


async def search_ad_interests(
    query: str,
    limit: Optional[int] = 25,
    locale: str = "pt_BR"
) -> str:
    """Search for Facebook ad interests by keyword.

    This function searches the Facebook ad targeting database for interests that match
    the provided query. Results include interest IDs that can be used in ad set targeting.

    Args:
        query (str): Search term for interests (e.g., "futebol", "moda", "tecnologia")
        limit (int): Maximum number of results to return. Default: 25.
        locale (str): Locale for search results. Default: "pt_BR" (Brazilian Portuguese).
            Other options: "en_US", "es_ES", etc.

    Returns:
        str: JSON string containing matching interests with their IDs, names, and metadata.

    Example:
        ```python
        interests = await search_ad_interests(
            query="futebol",
            limit=10,
            locale="pt_BR"
        )
        # Returns interests like:
        # [
        #   {
        #     "id": "6003139266461",
        #     "name": "Futebol",
        #     "audience_size_lower_bound": 1000000,
        #     "audience_size_upper_bound": 5000000,
        #     "path": ["Esportes e atividades ao ar livre", "Futebol"]
        #   }
        # ]
        ```
    """
    if not query:
        return json.dumps({"error": "No search query provided"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/search"

    params = {
        'access_token': access_token,
        'type': 'adinterest',
        'q': query,
        'limit': limit,
        'locale': locale
    }

    try:
        data = await _make_graph_api_call(url, params)

        # Process results to ensure proper unicode handling
        if 'data' in data:
            processed_data = []
            for interest in data['data']:
                # Ensure all string fields are properly decoded
                processed_interest = {}
                for key, value in interest.items():
                    if isinstance(value, str):
                        # Properly handle unicode characters
                        processed_interest[key] = value.encode('utf-8').decode('utf-8')
                    elif isinstance(value, list):
                        # Handle path array with unicode
                        processed_interest[key] = [
                            item.encode('utf-8').decode('utf-8') if isinstance(item, str) else item
                            for item in value
                        ]
                    else:
                        processed_interest[key] = value
                processed_data.append(processed_interest)

            data['data'] = processed_data

        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": "Failed to search ad interests",
            "details": str(e),
            "query": query
        }, indent=2, ensure_ascii=False)


async def get_region_key_for_adsets(
    region_name: str,
    country_code: str = "BR"
) -> str:
    """Get the region key for Brazilian states or other regions to use in ad set targeting.

    This function resolves region names (like state names) to their Facebook targeting keys.
    Particularly useful for targeting specific Brazilian states.

    Args:
        region_name (str): Name of the region/state (e.g., "São Paulo", "Rio de Janeiro", "Minas Gerais")
        country_code (str): ISO country code. Default: "BR" (Brazil)

    Returns:
        str: JSON string containing the region key and metadata, or error message.

    Example:
        ```python
        region = await get_region_key_for_adsets(
            region_name="São Paulo",
            country_code="BR"
        )
        # Returns:
        # {
        #   "key": "3462",
        #   "name": "São Paulo",
        #   "type": "region",
        #   "country_code": "BR",
        #   "supports_region": true
        # }

        # Use in targeting:
        targeting = {
            "geo_locations": {
                "countries": ["BR"],
                "regions": [{"key": "3462"}]  # São Paulo
            }
        }
        ```

    Note:
        Common Brazilian state keys:
        - São Paulo: "3462"
        - Rio de Janeiro: "3444"
        - Minas Gerais: "3445"
        - Rio Grande do Sul: "3463"
        - Paraná: "3450"
        - Bahia: "3471"
    """
    if not region_name:
        return json.dumps({"error": "No region name provided"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/search"

    params = {
        'access_token': access_token,
        'type': 'adgeolocation',
        'location_types': json.dumps(['region']),
        'q': region_name,
        'country_code': country_code
    }

    try:
        data = await _make_graph_api_call(url, params)

        # Process results to handle unicode properly
        if 'data' in data and len(data['data']) > 0:
            # Return the first (best) match with additional context
            best_match = data['data'][0]

            result = {
                "key": best_match.get('key'),
                "name": best_match.get('name'),
                "type": best_match.get('type'),
                "country_code": best_match.get('country_code'),
                "country_name": best_match.get('country_name'),
                "supports_region": best_match.get('supports_region', True),
                "supports_city": best_match.get('supports_city', False),
                "all_matches": data['data']  # Include all matches for reference
            }

            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return json.dumps({
                "error": "No matching region found",
                "region_name": region_name,
                "country_code": country_code,
                "suggestion": "Try using the full state name or check spelling"
            }, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "error": "Failed to get region key",
            "details": str(e),
            "region_name": region_name,
            "country_code": country_code
        }, indent=2, ensure_ascii=False)


async def list_pixels(
    fields: Optional[List[str]] = None,
    limit: Optional[int] = 25
) -> str:
    """List all Meta Pixels associated with an ad account.

    This function retrieves all pixels that are available for use with the specified ad account.
    Pixels are used for conversion tracking and audience building.

    Args:
        fields (Optional[List[str]]): Fields to retrieve. Default: ['id', 'name', 'code', 'is_created_by_business']
            Available fields include:
            - 'id': Pixel ID
            - 'name': Pixel name
            - 'code': Pixel tracking code
            - 'creation_time': When the pixel was created
            - 'last_fired_time': Last time the pixel received an event
            - 'is_created_by_business': Whether created by a Business Manager
            - 'owner_ad_account': Owning ad account
            - 'owner_business': Owning business
        limit (Optional[int]): Maximum number of pixels to return. Default: 25.

    Returns:
        str: JSON string containing pixel information or error message.

    Example:
        ```python
        pixels = await list_pixels(
            fields=["id", "name", "last_fired_time"],
            limit=10
        )
        # Returns:
        # {
        #   "data": [
        #     {
        #       "id": "1234567890",
        #       "name": "My Website Pixel",
        #       "last_fired_time": "2024-01-15T10:30:00+0000"
        #     }
        #   ]
        # }
        ```
    """
    act_id = get_act_id()
    if not act_id:
        return json.dumps({
            "error": "Ad account ID not configured. Set --facebook-ads-ad-account-id at server startup."
        }, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/adspixels"

    # Default fields if none provided
    if not fields:
        fields = ['id', 'name', 'code', 'is_created_by_business', 'creation_time', 'last_fired_time']

    params = {
        'access_token': access_token,
        'fields': ','.join(fields),
        'limit': limit
    }

    try:
        data = await _make_graph_api_call(url, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to list pixels",
            "details": str(e),
            "act_id": act_id
        }, indent=2)
