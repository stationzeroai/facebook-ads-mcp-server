"""
Campaign-related tools for Meta Ads API.

This module provides tools for creating and managing Facebook/Meta ad campaigns,
including both Campaign Budget Optimization (CBO) and Ad Set Budget Optimization (ABO) campaigns.
"""

import json
from typing import List, Optional, Dict, Any
from .api import (
    FB_GRAPH_URL,
    get_access_token,
    _make_graph_api_call,
    _make_graph_api_post,
    _prepare_params
)


async def create_cbo_campaign(
    name: str,
    objective: str,
    status: str = "PAUSED",
    daily_budget: Optional[float] = None,
    lifetime_budget: Optional[float] = None,
    buying_type: Optional[str] = "AUCTION",
    bid_strategy: Optional[str] = None,
    bid_amount: Optional[float] = None,
    spend_cap: Optional[float] = None,
    act_id: Optional[str] = None
) -> str:
    """Create a new CBO (Campaign Budget Optimization) campaign in a Meta Ads account.

    This function creates a new CBO campaign where budget and bidding strategy are managed at the campaign level.
    CBO campaigns automatically distribute budget across ad sets to get the best results.

    Args:
        name (str): Campaign name
        objective (str): Campaign objective. Valid values:
            OUTCOME_APP_PROMOTION, OUTCOME_AWARENESS, OUTCOME_ENGAGEMENT,
            OUTCOME_LEADS, OUTCOME_SALES, OUTCOME_TRAFFIC
        status (str): Initial campaign status (default: PAUSED). Options: ACTIVE, PAUSED
        daily_budget (float): Daily budget in account currency (in cents). Either daily_budget or lifetime_budget is required for CBO campaigns.
        lifetime_budget (float): Lifetime budget in account currency (in cents). Either daily_budget or lifetime_budget is required for CBO campaigns.
        buying_type (str): Buying type (default: AUCTION)
        bid_strategy (str): Bid strategy. Options: LOWEST_COST_WITHOUT_CAP (default), LOWEST_COST_WITH_BID_CAP, COST_CAP
        bid_amount (float): Bid amount in account currency (in cents). Required if bid_strategy is LOWEST_COST_WITH_BID_CAP or COST_CAP
        spend_cap (float): Spending limit for the campaign in account currency (in cents). Optional.
        act_id (str): Ad account ID (with act_ prefix). Required.

    Returns:
        str: JSON string containing the created campaign details or error message.
    """
    if not name:
        return json.dumps({"error": "No campaign name provided"}, indent=2)

    if not objective:
        return json.dumps({"error": "No campaign objective provided"}, indent=2)

    if not act_id:
        return json.dumps({"error": "No ad account ID (act_id) provided"}, indent=2)

    # For CBO campaigns, either daily_budget or lifetime_budget is required
    if not daily_budget and not lifetime_budget:
        return json.dumps({"error": "CBO campaigns require either daily_budget or lifetime_budget"}, indent=2)

    # Default bid strategy for CBO campaigns
    if not bid_strategy:
        bid_strategy = "LOWEST_COST_WITHOUT_CAP"

    # Validate bid_amount requirement
    if bid_strategy in ["LOWEST_COST_WITH_BID_CAP", "COST_CAP"] and not bid_amount:
        return json.dumps({"error": f"bid_amount is required when bid_strategy is {bid_strategy}"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/campaigns"

    base_params = {
        "access_token": access_token,
        "name": name,
        "objective": objective,
        "status": status,
        "campaign_budget_optimization": True  # Always true for CBO campaigns
    }

    params = _prepare_params(
        base_params,
        daily_budget=daily_budget,
        lifetime_budget=lifetime_budget,
        buying_type=buying_type,
        bid_strategy=bid_strategy,
        bid_amount=bid_amount,
        spend_cap=spend_cap,
        special_ad_categories=[],  # Required by API, empty by default
        ab_test_control_setups=[]  # Required by API, empty by default
    )

    try:
        data = await _make_graph_api_post(url, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        return json.dumps({
            "error": "Failed to create CBO campaign",
            "details": error_msg,
            "params_sent": {k: v for k, v in params.items() if 'token' not in k.lower()}
        }, indent=2)


async def create_abo_campaign(
    name: str,
    objective: str = "OUTCOME_SALES",
    status: str = "PAUSED",
    buying_type: Optional[str] = "AUCTION",
    act_id: Optional[str] = None
) -> str:
    """Create a new ABO (Ad Set Budget Optimization) campaign in a Meta Ads account.

    This function creates a new ABO campaign where budget and bidding strategy are managed at the ad set level.
    ABO campaigns allow you to control budget allocation for each ad set individually.

    Note: Budget and bid strategy parameters are NOT allowed for ABO campaigns at the campaign level.
    These must be set when creating ad sets for this campaign.

    Args:
        name (str): Campaign name
        objective (str): Campaign objective. Valid values:
            OUTCOME_APP_PROMOTION, OUTCOME_AWARENESS, OUTCOME_ENGAGEMENT,
            OUTCOME_LEADS, OUTCOME_SALES, OUTCOME_TRAFFIC
            Default: OUTCOME_SALES
        status (str): Initial campaign status (default: PAUSED). Options: ACTIVE, PAUSED
        buying_type (str): Buying type (default: AUCTION)
        act_id (str): Ad account ID (with act_ prefix). Required.

    Returns:
        str: JSON string containing the created campaign details or error message.
    """
    if not name:
        return json.dumps({"error": "No campaign name provided"}, indent=2)

    if not objective:
        return json.dumps({"error": "No campaign objective provided"}, indent=2)

    if not act_id:
        return json.dumps({"error": "No ad account ID (act_id) provided"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/campaigns"

    base_params = {
        "access_token": access_token,
        "name": name,
        "objective": objective,
        "status": status,
        "campaign_budget_optimization": False  # Always false for ABO campaigns
    }

    # For ABO campaigns, we only include non-budget related parameters
    params = _prepare_params(
        base_params,
        special_ad_categories=[],
        buying_type=buying_type,
        ab_test_control_setups=[]
    )

    try:
        data = await _make_graph_api_post(url, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        return json.dumps({
            "error": "Failed to create ABO campaign",
            "details": error_msg,
            "params_sent": {k: v for k, v in params.items() if 'token' not in k.lower()}
        }, indent=2)


async def update_campaign_budget(
    campaign_id: str,
    daily_budget: Optional[float] = None,
    lifetime_budget: Optional[float] = None,
) -> str:
    """Update the budget of a campaign.

    Args:
        campaign_id (str): The Campaign ID to be updated.
        daily_budget (float): The daily budget in account currency (in cents). Optional: should be passed if lifetime_budget is not passed.
        lifetime_budget (float): The lifetime budget in account currency (in cents). Optional: should be passed if daily_budget is not passed.

    Returns:
        str: Pretty-printed JSON with update result or error payload.
    """
    if not campaign_id:
        return json.dumps({"error": "No campaign ID provided"}, indent=2)

    if not daily_budget and not lifetime_budget:
        return json.dumps({"error": "Either daily_budget or lifetime_budget must be provided"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{campaign_id}"

    params = {"access_token": access_token}
    if daily_budget:
        params["daily_budget"] = str(daily_budget)
    if lifetime_budget:
        params["lifetime_budget"] = str(lifetime_budget)

    try:
        data = await _make_graph_api_post(url, params)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": "Failed to update campaign budget",
            "details": str(e),
            "campaign_id": campaign_id
        }, indent=2, ensure_ascii=False)


async def deactivate_or_activate_campaign(
    campaign_id: str,
    status: str,
) -> str:
    """Update campaign status (activate, pause, or archive).

    Sends a POST /<CAMPAIGN_ID> request with a new status.

    Args:
        campaign_id (str): The Campaign ID to be updated.
        status (str): The status to be set for the campaign. Options:
            - ACTIVE: Campaign is running
            - PAUSED: Campaign is paused
            - ARCHIVED: Campaign is archived
            - DELETED: Campaign is deleted

    Returns:
        str: Pretty-printed JSON with update result or error payload.
    """
    if not campaign_id:
        return json.dumps({"error": "No campaign ID provided"}, indent=2)

    if not status:
        return json.dumps({"error": "No status provided"}, indent=2)

    valid_statuses = ["ACTIVE", "PAUSED", "ARCHIVED", "DELETED"]
    if status not in valid_statuses:
        return json.dumps({
            "error": f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
        }, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{campaign_id}"
    params = {"access_token": access_token, "status": status}

    try:
        data = await _make_graph_api_post(url, params)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": "Failed to update campaign status",
            "details": str(e),
            "campaign_id": campaign_id
        }, indent=2, ensure_ascii=False)


async def get_campaign_by_id(
    campaign_id: str,
    fields: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> Dict:
    """Retrieves detailed information about a specific Facebook ad campaign by its ID.

    This function accesses the Facebook Graph API to retrieve information about a
    single campaign, including details about its objective, status, budget settings,
    and other campaign-level configurations.

    Args:
        campaign_id (str): The ID of the campaign to retrieve information for.
        fields (Optional[List[str]]): A list of specific fields to retrieve. If None,
            a default set of fields will be returned. Available fields include:
            - 'id', 'name', 'account_id', 'objective', 'status', 'configured_status', 'effective_status'
            - 'created_time', 'updated_time', 'start_time', 'stop_time'
            - 'daily_budget', 'lifetime_budget', 'budget_remaining', 'spend_cap'
            - 'bid_strategy', 'buying_type', 'special_ad_categories'
            - And many more (see Facebook Graph API documentation for complete list)
        date_format (Optional[str]): Format for date responses. Options:
            - 'U': Unix timestamp (seconds since epoch)
            - 'Y-m-d H:i:s': MySQL datetime format
            - None: ISO 8601 format (default)

    Returns:
        Dict: A dictionary containing the requested campaign information.

    Example:
        ```python
        # Get basic campaign information
        campaign = await get_campaign_by_id(
            campaign_id="23843211234567",
            fields=["name", "objective", "effective_status", "budget_remaining"]
        )
        ```
    """
    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{campaign_id}"
    params = {'access_token': access_token}

    if fields:
        params['fields'] = ','.join(fields)

    if date_format:
        params['date_format'] = date_format

    return await _make_graph_api_call(url, params)


async def get_campaigns_by_adaccount(
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
    is_completed: Optional[bool] = None,
    special_ad_categories: Optional[List[str]] = None,
    objective: Optional[List[str]] = None,
    buyer_guarantee_agreement_status: Optional[List[str]] = None,
    date_format: Optional[str] = None,
    include_drafts: Optional[bool] = None
) -> Dict:
    """Retrieves campaigns from a specific Facebook ad account.

    This function allows querying all campaigns belonging to a specific ad account with
    various filtering options, pagination, and field selection.

    Args:
        act_id (str): The ID of the ad account to retrieve campaigns from, prefixed with 'act_',
                      e.g., 'act_1234567890'.
        fields (Optional[List[str]]): A list of specific fields to retrieve for each campaign.
        filtering (Optional[List[dict]]): Filter objects with 'field', 'operator', and 'value' keys.
        limit (Optional[int]): Maximum number of campaigns to return per page. Default is 25, max is 100.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        date_preset (Optional[str]): Predefined relative date range.
        time_range (Optional[Dict[str, str]]): Custom time range with 'since' and 'until' dates.
        updated_since (Optional[int]): Return campaigns updated since this Unix timestamp.
        effective_status (Optional[List[str]]): Filter by effective status.
        is_completed (Optional[bool]): If True, returns only completed campaigns.
        special_ad_categories (Optional[List[str]]): Filter by special ad categories.
        objective (Optional[List[str]]): Filter by advertising objective.
        buyer_guarantee_agreement_status (Optional[List[str]]): Filter by buyer guarantee status.
        date_format (Optional[str]): Format for date responses ('U', 'Y-m-d H:i:s', or None).
        include_drafts (Optional[bool]): If True, includes draft campaigns.

    Returns:
        Dict: A dictionary containing the requested campaigns in 'data' list with pagination info.

    Example:
        ```python
        # Get active campaigns from an ad account
        campaigns = await get_campaigns_by_adaccount(
            act_id="act_123456789",
            fields=["name", "objective", "effective_status"],
            effective_status=["ACTIVE"],
            limit=50
        )
        ```
    """
    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/campaigns"
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

    if is_completed is not None:
        params['is_completed'] = is_completed

    if special_ad_categories:
        params['special_ad_categories'] = json.dumps(special_ad_categories)

    if objective:
        params['objective'] = json.dumps(objective)

    if buyer_guarantee_agreement_status:
        params['buyer_guarantee_agreement_status'] = json.dumps(buyer_guarantee_agreement_status)

    if date_format:
        params['date_format'] = date_format

    if include_drafts is not None:
        params['include_drafts'] = include_drafts

    return await _make_graph_api_call(url, params)
