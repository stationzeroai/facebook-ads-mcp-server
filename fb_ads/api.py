"""
Core API helpers and global state management for Facebook Graph API.

This module provides async HTTP clients, parameter builders, and
global configuration management for all Facebook Ads tools.
"""

import json
import sys
import logging
from typing import Dict, List, Optional, Any
import httpx

# Configure logging to stderr (stdout must be reserved for JSON-RPC)
logger = logging.getLogger(__name__)


# --- Constants ---
FB_API_VERSION = "v22.0"
FB_GRAPH_URL = f"https://graph.facebook.com/{FB_API_VERSION}"
DEFAULT_AD_ACCOUNT_FIELDS = [
    'name', 'business_name', 'age', 'account_status', 'balance',
    'amount_spent', 'attribution_spec', 'account_id', 'business',
    'business_city', 'brand_safety_content_filter_levels', 'currency',
    'created_time', 'id'
]


# --- Global State ---
_CONFIG = {
    'access_token': None,
    'act_id': None,
    'pixel_id': None,
    'page_id': None,
    'instagram_user_id': None,
    'catalog_id': None,
    'website_domain': None,
}


def init_config_from_args():
    """
    Initialize global configuration from command-line arguments.

    Expected arguments:
        --fb-token: Facebook access token (required)
        --facebook-ads-ad-account-id: Facebook Ad Account ID with act_ prefix (optional)
        --pixel-id: Meta Pixel ID (optional)
        --page-id: Facebook Page ID (optional)
        --instagram-user-id: Instagram User ID (optional)
        --catalog-id: Product Catalog ID (optional)
        --website-domain: Website domain for conversions (optional)
    """
    global _CONFIG

    def get_arg(flag: str, required: bool = False) -> Optional[str]:
        """Get command-line argument value."""
        if flag in sys.argv:
            idx = sys.argv.index(flag) + 1
            if idx < len(sys.argv):
                return sys.argv[idx]
            elif required:
                raise ValueError(f"{flag} provided but no value followed")
        elif required:
            raise ValueError(f"{flag} is required")
        return None

    _CONFIG['access_token'] = get_arg('--fb-token', required=True)
    _CONFIG['act_id'] = get_arg('--facebook-ads-ad-account-id')
    _CONFIG['pixel_id'] = get_arg('--pixel-id')
    _CONFIG['page_id'] = get_arg('--page-id')
    _CONFIG['instagram_user_id'] = get_arg('--instagram-user-id')
    _CONFIG['catalog_id'] = get_arg('--catalog-id')
    _CONFIG['website_domain'] = get_arg('--website-domain')

    logger.info(f"✓ Facebook API configured (v{FB_API_VERSION})")
    if _CONFIG['act_id']:
        logger.info(f"✓ Ad Account ID: {_CONFIG['act_id']}")
    if _CONFIG['pixel_id']:
        logger.info(f"✓ Pixel ID: {_CONFIG['pixel_id']}")
    if _CONFIG['page_id']:
        logger.info(f"✓ Page ID: {_CONFIG['page_id']}")


def get_access_token() -> str:
    """Get the configured Facebook access token."""
    if not _CONFIG['access_token']:
        raise ValueError("Access token not initialized. Call init_config_from_args() first.")
    return _CONFIG['access_token']


def get_act_id() -> Optional[str]:
    """Get the configured Facebook Ad Account ID."""
    return _CONFIG['act_id']


def get_pixel_id() -> Optional[str]:
    """Get the configured Meta Pixel ID."""
    return _CONFIG['pixel_id']


def get_page_id() -> Optional[str]:
    """Get the configured Facebook Page ID."""
    return _CONFIG['page_id']


def get_instagram_user_id() -> Optional[str]:
    """Get the configured Instagram User ID."""
    return _CONFIG['instagram_user_id']


def get_catalog_id() -> Optional[str]:
    """Get the configured Product Catalog ID."""
    return _CONFIG['catalog_id']


def get_website_domain() -> Optional[str]:
    """Get the configured website domain."""
    return _CONFIG['website_domain']


# --- HTTP Helpers ---

async def _make_graph_api_call(url: str, params: Dict[str, Any]) -> Dict:
    """
    Make an async GET request to the Facebook Graph API.

    Args:
        url: The API endpoint URL
        params: Query parameters (including access_token)

    Returns:
        Dict: JSON response from the API

    Raises:
        httpx.HTTPStatusError: For 4xx/5xx responses
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        # Log error with redacted sensitive params
        safe_params = {
            k: "[REDACTED]" if any(s in k.lower() for s in ['token', 'secret', 'key']) else v
            for k, v in params.items()
        }
        logger.error(f"❌ Graph API GET error: {url} | Params: {safe_params} | Error: {e}")
        raise
    except httpx.RequestError as e:
        logger.error(f"❌ Request error: {url} | Error: {e}")
        raise


async def _make_graph_api_post(url: str, data: Dict[str, Any]) -> Dict:
    """
    Make an async POST request to the Facebook Graph API.

    Args:
        url: The API endpoint URL
        data: POST data (including access_token)

    Returns:
        Dict: JSON response from the API, or error dict if API returned an error
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, data=data)

        response_json = response.json()

        # Facebook API sometimes returns errors with 200 status
        if 'error' in response_json:
            safe_data = {k: v for k, v in data.items() if 'token' not in k.lower()}
            return {
                "error": response_json['error'],
                "payload_sent": safe_data,
                "url": url,
                "status_code": response.status_code
            }

        response.raise_for_status()
        return response_json

    except httpx.HTTPStatusError as e:
        error_details = {
            "error": "HTTP error",
            "details": str(e),
            "url": url,
            "status_code": e.response.status_code if hasattr(e, 'response') else None
        }
        if hasattr(e, 'response') and e.response is not None:
            try:
                api_error = e.response.json()
                if 'error' in api_error:
                    error_details["api_error"] = api_error['error']
            except:
                error_details["response_text"] = e.response.text[:500]
        return error_details
    except httpx.RequestError as e:
        return {
            "error": "Request failed",
            "details": str(e),
            "url": url
        }


def _prepare_params(base_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Prepare API parameters by adding optional kwargs and handling special encoding.

    Args:
        base_params: Base parameters dict
        **kwargs: Additional optional parameters

    Returns:
        Dict: Combined parameters with proper encoding
    """
    params = base_params.copy()

    for key, value in kwargs.items():
        if value is None:
            continue

        # JSON encoding for complex structures
        if key in ['filtering', 'time_range', 'time_ranges', 'effective_status',
                   'special_ad_categories', 'objective', 'ab_test_control_setups',
                   'buyer_guarantee_agreement_status', 'targeting', 'frequency_control_specs',
                   'promoted_object'] and isinstance(value, (list, dict)):
            params[key] = json.dumps(value)

        # List to comma-separated string
        elif key in ['fields', 'action_attribution_windows', 'action_breakdowns', 'breakdowns'] and isinstance(value, list):
            params[key] = ','.join(str(v) for v in value)

        # Boolean to string
        elif key == 'campaign_budget_optimization' and isinstance(value, bool):
            params[key] = "true" if value else "false"

        # Numbers to strings for budget/bid fields
        elif key in ['daily_budget', 'lifetime_budget', 'bid_cap', 'spend_cap', 'bid_amount', 'roas_average_floor']:
            params[key] = str(value)

        else:
            params[key] = value

    return params


def _build_insights_params(
    base_params: Dict[str, Any],
    fields: Optional[List[str]] = None,
    date_preset: Optional[str] = None,
    time_range: Optional[Dict[str, str]] = None,
    time_ranges: Optional[List[Dict[str, str]]] = None,
    time_increment: Optional[str] = None,
    level: Optional[str] = None,
    action_attribution_windows: Optional[List[str]] = None,
    action_breakdowns: Optional[List[str]] = None,
    action_report_time: Optional[str] = None,
    breakdowns: Optional[List[str]] = None,
    default_summary: bool = False,
    use_account_attribution_setting: bool = False,
    use_unified_attribution_setting: bool = True,
    filtering: Optional[List[dict]] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    offset: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    locale: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build parameter dictionary specifically for insights API calls.

    Handles all the complex parameter combinations and encodings
    required by the Insights API.
    """
    # Start with base params and add common fields
    params = _prepare_params(
        base_params,
        fields=fields,
        level=level,
        action_attribution_windows=action_attribution_windows,
        action_breakdowns=action_breakdowns,
        action_report_time=action_report_time,
        breakdowns=breakdowns,
        filtering=filtering,
        sort=sort,
        limit=limit,
        after=after,
        before=before,
        offset=offset,
        locale=locale
    )

    # Handle time parameters (specific logic for insights)
    time_params_provided = time_range or time_ranges or since or until
    if not time_params_provided and date_preset:
        params['date_preset'] = date_preset

    if time_range:
        params['time_range'] = json.dumps(time_range)
    if time_ranges:
        params['time_ranges'] = json.dumps(time_ranges)
    if time_increment and time_increment != 'all_days':  # API default
        params['time_increment'] = time_increment

    # Time-based pagination (only if specific time range isn't set)
    if not time_range and not time_ranges:
        if since:
            params['since'] = since
        if until:
            params['until'] = until

    # Boolean flags need specific handling ('true'/'false' strings)
    if default_summary:
        params['default_summary'] = 'true'
    if use_account_attribution_setting:
        params['use_account_attribution_setting'] = 'true'
    if use_unified_attribution_setting:
        params['use_unified_attribution_setting'] = 'true'

    return params
