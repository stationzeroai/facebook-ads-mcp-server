"""
Ad Set-related tools for Meta Ads API.

This module provides tools for creating and managing Facebook/Meta ad sets,
including advanced targeting, budget optimization, and frequency capping.
"""

import json
from typing import List, Optional, Dict, Any, Union
from .api import (
    FB_GRAPH_URL,
    get_access_token,
    get_pixel_id,
    get_website_domain,
    _make_graph_api_call,
    _make_graph_api_post,
    _prepare_params
)


def _requires_conversion_details(optimization_goal: str) -> bool:
    """Check if an optimization goal requires conversion-specific details (pixel_id, custom_event_type)."""
    conversion_goals = {
        "OFFSITE_CONVERSIONS",
        "VALUE",
        "APP_INSTALLS",
        "APP_INSTALLS_AND_OFFSITE_CONVERSIONS",
        "IN_APP_VALUE",
        "ADVERTISER_SILOED_VALUE",
        "MESSAGING_PURCHASE_CONVERSION",
        "MESSAGING_APPOINTMENT_CONVERSION",
    }
    return optimization_goal in conversion_goals


async def create_adset(
    campaign_id: str,
    name: str,
    optimization_goal: str,
    billing_event: str,
    act_id: str,
    custom_event_type: Optional[str] = None,
    status: str = "PAUSED",
    daily_budget: Optional[str] = None,
    lifetime_budget: Optional[str] = None,
    targeting: Union[str, Dict[str, Any], None] = None,
    bid_amount: Optional[str] = None,
    bid_strategy: Optional[str] = None,
    roas_average_floor: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    destination_type: Optional[str] = "WEBSITE"
) -> str:
    """
    Create a new ad set in a Meta Ads account.

    IMPORTANT NOTES:
    - If the campaign is CBO (campaign_budget_optimization=true), DO NOT provide:
      daily_budget, lifetime_budget, bid_strategy, bid_amount, roas_average_floor
    - If the campaign is ABO (campaign_budget_optimization=false), REQUIRED:
      - Exactly one of: daily_budget OR lifetime_budget
      - bid_strategy (required)
      - bid_amount (required for LOWEST_COST_WITH_BID_CAP or COST_CAP strategies)
      - roas_average_floor (required for LOWEST_COST_WITH_MIN_ROAS strategy)
      - start_time and end_time (required for lifetime budgets)
    - Always provide: optimization_goal, billing_event, targeting, status, name, campaign_id
    - For conversion goals (OFFSITE_CONVERSIONS, VALUE, APP_INSTALLS, etc.), provide:
      custom_event_type, destination_type, and ensure pixel_id is configured

    Objective → Optimization Goal Mapping:
    - OUTCOME_AWARENESS → IMPRESSIONS, REACH, AD_RECALL_LIFT, THRUPLAY
    - OUTCOME_TRAFFIC → LINK_CLICKS, LANDING_PAGE_VIEWS, IMPRESSIONS, VISIT_INSTAGRAM_PROFILE
    - OUTCOME_ENGAGEMENT → POST_ENGAGEMENT, PAGE_LIKES, EVENT_RESPONSES, PROFILE_VISIT
    - OUTCOME_LEADS → LEAD_GENERATION, QUALITY_LEAD, CONVERSATIONS, SUBSCRIBERS
    - OUTCOME_APP_PROMOTION → APP_INSTALLS, APP_INSTALLS_AND_OFFSITE_CONVERSIONS, IN_APP_VALUE, VALUE
    - OUTCOME_SALES → OFFSITE_CONVERSIONS, VALUE, ADVERTISER_SILOED_VALUE

    Optimization Goal → Billing Event Mapping:
    - IMPRESSIONS, REACH, AD_RECALL_LIFT, THRUPLAY → IMPRESSIONS
    - LINK_CLICKS, LANDING_PAGE_VIEWS → LINK_CLICKS or IMPRESSIONS
    - POST_ENGAGEMENT, PAGE_LIKES, EVENT_RESPONSES → Same as goal or IMPRESSIONS
    - All conversion goals → IMPRESSIONS

    Bid Strategies (required for ABO campaigns):
    - LOWEST_COST_WITHOUT_CAP (default) – fully automatic bidding
    - LOWEST_COST_WITH_BID_CAP – auto-bid capped at bid_amount
    - COST_CAP – aims to average results at bid_amount
    - LOWEST_COST_WITH_MIN_ROAS – bids to maintain ROAS above roas_average_floor

    Args:
        campaign_id (str): ID of the parent campaign
        name (str): Human-readable ad set name
        optimization_goal (str): Optimization goal (must match campaign objective)
        billing_event (str): What you pay for (must match optimization_goal)
        act_id (str): Ad account ID (with act_ prefix)
        custom_event_type (str): Required for conversion goals. Options: PURCHASE, VIEW_CONTENT, ADD_TO_CART, ADD_TO_WISHLIST, INITIATE_CHECKOUT, SUBSCRIBE, START_TRIAL
        status (str): Initial delivery status (default: PAUSED). Options: ACTIVE, PAUSED
        daily_budget (str): Daily budget in cents (for ABO campaigns only)
        lifetime_budget (str): Lifetime budget in cents (for ABO campaigns only)
        targeting (dict): Targeting specification. Examples:
            Broad country targeting:
            ```python
            {
                "geo_locations": {"countries": ["BR"]},
                "age_min": 18,
                "age_max": 65,
                "genders": [1, 2]  # 1 = men, 2 = women
            }
            ```
            Regional + interest targeting:
            ```python
            {
                "geo_locations": {
                    "regions": [{"key": "3448"}],  # São Paulo
                },
                "age_min": 25,
                "age_max": 45,
                "genders": [2],
                "interests": [{"id": "6003139266461"}],  # Futebol
                "targeting_automation": {"advantage_audience": 1}
            }
            ```
            Advantage+ Audience (note: age_max must be 65):
            ```python
            {
                "targeting_automation": {"advantage_audience": 1},
                "age_min": 18,
                "age_max": 65,
                "genders": [1, 2]
            }
            ```
        bid_amount (str): Bid amount in cents (required for BID_CAP or COST_CAP strategies)
        bid_strategy (str): Bid strategy (required for ABO campaigns)
        roas_average_floor (str): ROAS floor in cents (required for MIN_ROAS strategy)
        start_time (str): ISO-8601 timestamp (required for lifetime budgets)
        end_time (str): ISO-8601 timestamp (required for lifetime budgets)
        destination_type (str): Destination type (default: WEBSITE). Options: WEBSITE, APP, INSTAGRAM_DIRECT, INSTAGRAM_PROFILE

    Returns:
        str: JSON string containing the created ad set details or error message

    Example:
        ```python
        # Create conversion ad set for ABO campaign
        adset = await create_adset(
            campaign_id="120123456",
            name="Women 25-34 • BR • Futebol",
            act_id="act_123456789",
            daily_budget="5000",
            optimization_goal="OFFSITE_CONVERSIONS",
            billing_event="IMPRESSIONS",
            bid_strategy="LOWEST_COST_WITHOUT_CAP",
            custom_event_type="PURCHASE",
            targeting={
                "geo_locations": {"countries": ["BR"]},
                "age_min": 25,
                "age_max": 34,
                "interests": [{"id": "6003139266461"}],
                "targeting_automation": {"advantage_audience": 1}
            },
            status="PAUSED"
        )
        ```
    """
    # Validate required parameters
    if not all([act_id, campaign_id, name]):
        return json.dumps({"error": "act_id, campaign_id, and name are required"}, indent=2)

    if not optimization_goal or not billing_event:
        return json.dumps({"error": "optimization_goal and billing_event are required"}, indent=2)

    # Check conversion goal requirements
    if _requires_conversion_details(optimization_goal):
        pixel_id = get_pixel_id()
        website_domain = get_website_domain()

        if not pixel_id:
            return json.dumps({"error": "pixel_id is required for conversion goals. Configure with --pixel-id"}, indent=2)

        if not custom_event_type:
            return json.dumps({"error": "custom_event_type is required for conversion goals (e.g., PURCHASE, VIEW_CONTENT)"}, indent=2)

        if not website_domain:
            return json.dumps({"error": "website_domain is required for conversion goals. Configure with --website-domain"}, indent=2)

    # Validate bid strategy requirements
    if bid_strategy == "LOWEST_COST_WITH_MIN_ROAS" and not roas_average_floor:
        return json.dumps({"error": "roas_average_floor is required for LOWEST_COST_WITH_MIN_ROAS strategy"}, indent=2)

    # Basic targeting is required if not provided
    if not targeting:
        targeting = {
            "age_min": 18,
            "age_max": 65,
            "geo_locations": {"countries": ["BR"]},
            "targeting_automation": {"advantage_audience": 1}
        }

    # Parse targeting if provided as string
    if isinstance(targeting, str):
        try:
            targeting = json.loads(targeting)
        except json.JSONDecodeError as exc:
            return json.dumps({
                "error": "targeting was sent as string but is not valid JSON",
                "details": str(exc),
                "received": targeting,
            }, indent=2)

    # Build base parameters
    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/adsets"

    base_params = {
        "access_token": access_token,
        "name": name,
        "campaign_id": campaign_id,
        "status": status,
        "optimization_goal": optimization_goal,
        "billing_event": billing_event
    }

    # Add conversion-specific parameters
    if _requires_conversion_details(optimization_goal):
        promoted_object = {"pixel_id": get_pixel_id()}
        promoted_object["custom_event_type"] = custom_event_type.upper()
        base_params["promoted_object"] = json.dumps(promoted_object)
        base_params["destination_type"] = destination_type
        base_params["conversion_domain"] = get_website_domain()

    # Prepare final parameters
    params = _prepare_params(
        base_params,
        targeting=targeting,
        daily_budget=daily_budget,
        lifetime_budget=lifetime_budget,
        bid_amount=bid_amount,
        bid_strategy=bid_strategy,
        start_time=start_time,
        end_time=end_time,
        roas_average_floor=roas_average_floor
    )

    try:
        data = await _make_graph_api_post(url, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to create ad set",
            "details": str(e),
            "params_sent": {k: v for k, v in params.items() if 'token' not in k.lower()}
        }, indent=2)


async def update_adset(
    adset_id: str,
    frequency_control_specs: Optional[List[Dict[str, Any]]] = None,
    bid_strategy: Optional[str] = None,
    bid_amount: Optional[int] = None,
    status: Optional[str] = None,
    targeting: Optional[Dict[str, Any]] = None,
    optimization_goal: Optional[str] = None
) -> str:
    """
    Update an ad set with new settings including frequency caps.

    Args:
        adset_id (str): Meta Ads ad set ID
        frequency_control_specs (List[Dict]): Frequency control specifications.
            Example: [{"event": "IMPRESSIONS", "interval_days": 7, "max_frequency": 3}]
        bid_strategy (str): Bid strategy. Options: LOWEST_COST_WITH_BID_CAP, LOWEST_COST_WITHOUT_CAP, COST_CAP, LOWEST_COST_WITH_MIN_ROAS
        bid_amount (int): Bid amount in account currency (in cents)
        status (str): Update ad set status. Options: ACTIVE, PAUSED, ARCHIVED, DELETED
        targeting (Dict): Targeting specifications. Can provide:
            - Full targeting spec (replaces existing)
            - Partial spec with targeting_automation only (preserves rest)
            Examples:
            ```python
            # Update only Advantage+ setting:
            {"targeting_automation": {"advantage_audience": 1}}

            # Full targeting update:
            {
                "geo_locations": {"countries": ["BR"]},
                "age_min": 18,
                "age_max": 45,
                "genders": [1, 2],
                "interests": [{"id": "6003139266461"}],
                "targeting_automation": {"advantage_audience": 1}
            }
            ```
        optimization_goal (str): Conversion optimization goal. Options: LINK_CLICKS, OFFSITE_CONVERSIONS, APP_INSTALLS, etc.

    Returns:
        str: JSON string with update result or error details
    """
    if not adset_id:
        return json.dumps({"error": "No ad set ID provided"}, indent=2)

    changes = {}

    if frequency_control_specs is not None:
        changes['frequency_control_specs'] = json.dumps(frequency_control_specs)

    if bid_strategy is not None:
        changes['bid_strategy'] = bid_strategy

    if bid_amount is not None:
        changes['bid_amount'] = bid_amount

    if status is not None:
        changes['status'] = status

    if optimization_goal is not None:
        changes['optimization_goal'] = optimization_goal

    if targeting is not None:
        # Get current ad set details to preserve existing targeting settings
        access_token = get_access_token()
        details_url = f"{FB_GRAPH_URL}/{adset_id}"
        details_params = {
            "access_token": access_token,
            "fields": "targeting"
        }
        try:
            current_details = await _make_graph_api_call(details_url, details_params)
            current_targeting = current_details.get('targeting', {})

            if 'targeting_automation' in targeting and len(targeting) == 1:
                # Only update targeting_automation while preserving other targeting settings
                if current_targeting:
                    merged_targeting = current_targeting.copy()
                    merged_targeting['targeting_automation'] = targeting['targeting_automation']
                    changes['targeting'] = json.dumps(merged_targeting)
                else:
                    # If there's no existing targeting, create a basic one
                    basic_targeting = {
                        'targeting_automation': targeting['targeting_automation'],
                        'geo_locations': {'countries': ['BR']}
                    }
                    changes['targeting'] = json.dumps(basic_targeting)
            else:
                # Full targeting replacement
                changes['targeting'] = json.dumps(targeting)
        except Exception as e:
            return json.dumps({
                "error": "Failed to fetch current targeting",
                "details": str(e)
            }, indent=2)

    if not changes:
        return json.dumps({"error": "No update parameters provided"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{adset_id}"

    params = {
        "access_token": access_token,
        **changes
    }

    try:
        data = await _make_graph_api_post(url, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to update ad set",
            "details": str(e),
            "adset_id": adset_id
        }, indent=2)


async def get_adset_by_id(
    adset_id: str,
    fields: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> Dict:
    """Retrieves detailed information about a specific Facebook ad set by its ID.

    Args:
        adset_id (str): The ID of the ad set to retrieve information for
        fields (Optional[List[str]]): Specific fields to retrieve. Available fields include:
            - id, name, campaign_id, account_id
            - status, configured_status, effective_status
            - created_time, updated_time, start_time, end_time
            - daily_budget, lifetime_budget, budget_remaining
            - optimization_goal, billing_event, bid_strategy, bid_amount
            - targeting, promoted_object, destination_type
            - And many more
        date_format (Optional[str]): Format for date responses ('U', 'Y-m-d H:i:s', or None)

    Returns:
        Dict: Dictionary containing the requested ad set information

    Example:
        ```python
        adset = await get_adset_by_id(
            adset_id="23843211234567",
            fields=["name", "campaign_id", "effective_status", "targeting"]
        )
        ```
    """
    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{adset_id}"
    params = {'access_token': access_token}

    if fields:
        params['fields'] = ','.join(fields)

    if date_format:
        params['date_format'] = date_format

    return await _make_graph_api_call(url, params)


async def get_adsets_by_ids(
    adset_ids: List[str],
    fields: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> Dict:
    """Retrieves detailed information about multiple Facebook ad sets by their IDs.

    This function allows batch retrieval of multiple ad sets in a single API call,
    improving efficiency when you need data for several ad sets.

    Args:
        adset_ids (List[str]): A list of ad set IDs to retrieve information for
        fields (Optional[List[str]]): Specific fields to retrieve for each ad set
        date_format (Optional[str]): Format for date responses ('U', 'Y-m-d H:i:s', or None)

    Returns:
        Dict: Dictionary where keys are ad set IDs and values are ad set details

    Example:
        ```python
        adsets = await get_adsets_by_ids(
            adset_ids=["23843211234567", "23843211234568", "23843211234569"],
            fields=["name", "campaign_id", "effective_status", "budget_remaining"]
        )

        # Access specific ad set
        if "23843211234567" in adsets:
            print(adsets["23843211234567"]["name"])
        ```
    """
    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/"
    params = {
        'access_token': access_token,
        'ids': ','.join(adset_ids)
    }

    if fields:
        params['fields'] = ','.join(fields)

    if date_format:
        params['date_format'] = date_format

    return await _make_graph_api_call(url, params)


async def get_adsets_by_adaccount(
    act_id: str,
    fields: Optional[List[str]] = None,
    filtering: Optional[List[dict]] = None,
    limit: Optional[int] = 25,
    after: Optional[str] = None,
    before: Optional[str] = None,
    date_preset: Optional[str] = None,
    time_range: Optional[Dict[str, str]] = None,
    updated_since: Optional[int] = None,
    effective_status: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> Dict:
    """Retrieves ad sets from a specific Facebook ad account.

    Args:
        act_id (str): Ad account ID (with act_ prefix)
        fields (Optional[List[str]]): Specific fields to retrieve
        filtering (Optional[List[dict]]): Filter objects with 'field', 'operator', 'value'
        limit (Optional[int]): Maximum ad sets per page (default: 25, max: 100)
        after (Optional[str]): Pagination cursor for next page
        before (Optional[str]): Pagination cursor for previous page
        date_preset (Optional[str]): Predefined date range
        time_range (Optional[Dict[str, str]]): Custom date range {'since': 'YYYY-MM-DD', 'until': 'YYYY-MM-DD'}
        updated_since (Optional[int]): Unix timestamp
        effective_status (Optional[List[str]]): Filter by status
        date_format (Optional[str]): Date format ('U', 'Y-m-d H:i:s', or None)

    Returns:
        Dict: Dictionary with 'data' list and 'paging' info

    Example:
        ```python
        adsets = await get_adsets_by_adaccount(
            act_id="act_123456789",
            fields=["name", "campaign_id", "effective_status", "daily_budget"],
            effective_status=["ACTIVE"],
            limit=50
        )
        ```
    """
    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/adsets"
    params = {'access_token': access_token}

    if fields:
        params['fields'] = ','.join(fields)

    if filtering:
        params['filtering'] = json.dumps(filtering)

    if limit is not None:
        params['limit'] = limit

    if after:
        params['after'] = after

    if before:
        params['before'] = before

    if date_preset:
        params['date_preset'] = date_preset

    if time_range:
        params['time_range'] = json.dumps(time_range)

    if updated_since:
        params['updated_since'] = updated_since

    if effective_status:
        params['effective_status'] = json.dumps(effective_status)

    if date_format:
        params['date_format'] = date_format

    return await _make_graph_api_call(url, params)


async def get_adsets_by_campaign(
    campaign_id: str,
    fields: Optional[List[str]] = None,
    filtering: Optional[List[dict]] = None,
    limit: Optional[int] = 25,
    after: Optional[str] = None,
    before: Optional[str] = None,
    date_preset: Optional[str] = None,
    time_range: Optional[Dict[str, str]] = None,
    updated_since: Optional[int] = None,
    effective_status: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> Dict:
    """Retrieves ad sets from a specific campaign.

    Args:
        campaign_id (str): Campaign ID
        fields (Optional[List[str]]): Specific fields to retrieve
        filtering (Optional[List[dict]]): Filter objects
        limit (Optional[int]): Maximum ad sets per page
        after (Optional[str]): Pagination cursor
        before (Optional[str]): Pagination cursor
        date_preset (Optional[str]): Predefined date range
        time_range (Optional[Dict[str, str]]): Custom date range
        updated_since (Optional[int]): Unix timestamp
        effective_status (Optional[List[str]]): Filter by status
        date_format (Optional[str]): Date format

    Returns:
        Dict: Dictionary with 'data' list and 'paging' info

    Example:
        ```python
        adsets = await get_adsets_by_campaign(
            campaign_id="23843211234567",
            fields=["name", "effective_status", "daily_budget", "targeting"],
            effective_status=["ACTIVE"]
        )
        ```
    """
    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{campaign_id}/adsets"
    params = {'access_token': access_token}

    if fields:
        params['fields'] = ','.join(fields)

    if filtering:
        params['filtering'] = json.dumps(filtering)

    if limit is not None:
        params['limit'] = limit

    if after:
        params['after'] = after

    if before:
        params['before'] = before

    if date_preset:
        params['date_preset'] = date_preset

    if time_range:
        params['time_range'] = json.dumps(time_range)

    if updated_since:
        params['updated_since'] = updated_since

    if effective_status:
        params['effective_status'] = json.dumps(effective_status)

    if date_format:
        params['date_format'] = date_format

    return await _make_graph_api_call(url, params)
