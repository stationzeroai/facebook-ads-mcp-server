"""
Smart query tools for Facebook Ads with integrated insights.

This module provides name-based search functions that combine entity retrieval
with performance insights for comprehensive analysis.
"""

import json
from typing import List, Optional, Dict, Any
from .api import (
    FB_GRAPH_URL,
    get_access_token,
    get_act_id,
    _make_graph_api_call,
    _build_insights_params
)


async def fetch_campaigns_by_name(
    campaign_names: List[str],
    fields: Optional[List[str]] = None,
    include_insights: bool = True,
    date_preset: Optional[str] = "last_30d",
    insights_fields: Optional[List[str]] = None,
    limit: Optional[int] = 500
) -> Dict[str, Any]:
    """Fetch campaigns by name with exact matching and optional performance insights.

    This function retrieves campaigns using exact name matching (EQUAL operator) and can
    automatically fetch performance metrics for matched campaigns. Each campaign name is
    searched individually since Facebook's API doesn't support IN operator for names.

    Args:
        campaign_names (List[str]): List of campaign names to fetch using exact name matching
        fields (Optional[List[str]]): Campaign fields to retrieve. Default:
            ['id', 'name', 'objective', 'status', 'effective_status', 'daily_budget', 'lifetime_budget']
        include_insights (bool): If True, includes performance insights for each campaign. Default: True
        date_preset (Optional[str]): Date preset for insights. Default: "last_30d"
            Options: today, yesterday, last_7d, last_14d, last_30d, last_90d, lifetime, etc.
        insights_fields (Optional[List[str]]): Insights metrics to retrieve. Default:
            ['impressions', 'clicks', 'spend', 'reach', 'cpc', 'cpm', 'ctr', 'frequency']
        limit (Optional[int]): Maximum number of campaigns to return per name. Default: 500

    Returns:
        Dict: Dictionary containing:
            - 'data' (List[Dict]): List of matched campaigns with insights
            - 'summary' (Dict): Summary with requested_names, total_matched_campaigns,
              campaigns_with_insights, unmatched_requests, and name_mappings

    Example:
        ```python
        result = await fetch_campaigns_by_name(
            campaign_names=["Summer Sale", "Holiday Promo"],
            include_insights=True,
            date_preset="last_7d"
        )
        # Returns campaigns with exact names plus their last 7 days performance
        ```
    """
    act_id = get_act_id()
    if not act_id:
        return {
            "error": "Ad account ID not configured. Set --facebook-ads-ad-account-id at server startup.",
            "data": [],
            "summary": {"requested_names": campaign_names, "unmatched_requests": campaign_names}
        }

    if not campaign_names:
        return {
            "data": [],
            "summary": {"requested_names": [], "unmatched_requests": []}
        }

    access_token = get_access_token()

    # Set default fields if none provided
    if not fields:
        fields = [
            'id', 'name', 'objective', 'status', 'effective_status',
            'daily_budget', 'lifetime_budget', 'created_time', 'updated_time'
        ]

    if not insights_fields:
        insights_fields = [
            'impressions', 'clicks', 'spend', 'reach',
            'cpc', 'cpm', 'ctr', 'frequency'
        ]

    # Step 1: Fetch each campaign with exact match
    matched_campaigns = []

    for requested_name in campaign_names:
        name_filter = [
            {
                "field": "name",
                "operator": "EQUAL",
                "value": requested_name
            }
        ]

        campaigns_url = f"{FB_GRAPH_URL}/{act_id}/campaigns"
        campaigns_params = {
            'access_token': access_token,
            'fields': ','.join(fields),
            'filtering': json.dumps(name_filter),
            'limit': limit
        }

        try:
            campaigns_data = await _make_graph_api_call(campaigns_url, campaigns_params)

            if campaigns_data.get("data"):
                # Found exact match
                for campaign in campaigns_data.get("data", []):
                    campaign["requested_name"] = requested_name
                    campaign["matched_name"] = requested_name  # Exact match
                    matched_campaigns.append(campaign)

        except Exception as e:
            print(f"Error fetching campaign '{requested_name}': {str(e)}")

    # Step 2: Fetch insights for each matched campaign
    campaigns_with_insights = []

    for campaign in matched_campaigns:
        if include_insights:
            insights_url = f"{FB_GRAPH_URL}/{campaign['id']}/insights"

            base_params = {'access_token': access_token}
            insights_params = _build_insights_params(
                base_params,
                fields=insights_fields,
                date_preset=date_preset
            )

            try:
                insights_data = await _make_graph_api_call(insights_url, insights_params)
                campaign_with_insights = {
                    **campaign,
                    "insights": insights_data.get('data', [])
                }
                campaigns_with_insights.append(campaign_with_insights)

            except Exception as e:
                # Include campaign even if insights failed, but note the error
                campaign_with_insights = {
                    **campaign,
                    "insights": [],
                    "insights_error": str(e)
                }
                campaigns_with_insights.append(campaign_with_insights)
        else:
            campaigns_with_insights.append(campaign)

    # Create summary information
    name_mappings = {}
    matched_requested_names = []

    for campaign in matched_campaigns:
        requested = campaign.get("requested_name", "")
        matched = campaign.get("matched_name", "")
        if requested:
            name_mappings[requested] = matched
            matched_requested_names.append(requested)

    unmatched_requests = [name for name in campaign_names if name not in matched_requested_names]

    return {
        "data": campaigns_with_insights,
        "summary": {
            "requested_names": campaign_names,
            "total_matched_campaigns": len(matched_campaigns),
            "campaigns_with_insights": len([c for c in campaigns_with_insights if "insights_error" not in c]),
            "unmatched_requests": unmatched_requests,
            "name_mappings": name_mappings
        }
    }


async def fetch_adsets_by_name(
    adset_names: List[str],
    fields: Optional[List[str]] = None,
    include_insights: bool = True,
    date_preset: Optional[str] = "last_30d",
    insights_fields: Optional[List[str]] = None,
    limit: Optional[int] = 500
) -> Dict[str, Any]:
    """Fetch ad sets by name with exact matching and optional performance insights.

    This function retrieves ad sets using exact name matching (EQUAL operator) and can
    automatically fetch performance metrics for matched ad sets. Each ad set name is
    searched individually since Facebook's API doesn't support IN operator for names.

    Args:
        adset_names (List[str]): List of ad set names to fetch using exact name matching
        fields (Optional[List[str]]): Ad set fields to retrieve. Default:
            ['id', 'name', 'campaign_id', 'status', 'effective_status', 'daily_budget', 'lifetime_budget', 'optimization_goal']
        include_insights (bool): If True, includes performance insights for each ad set. Default: True
        date_preset (Optional[str]): Date preset for insights. Default: "last_30d"
        insights_fields (Optional[List[str]]): Insights metrics to retrieve. Default:
            ['impressions', 'clicks', 'spend', 'reach', 'cpc', 'cpm', 'ctr', 'frequency']
        limit (Optional[int]): Maximum number of ad sets to return per name. Default: 500

    Returns:
        Dict: Dictionary containing:
            - 'data' (List[Dict]): List of matched ad sets with insights
            - 'summary' (Dict): Summary with requested_names, total_matched_adsets,
              adsets_with_insights, unmatched_requests, and name_mappings

    Example:
        ```python
        result = await fetch_adsets_by_name(
            adset_names=["Premium Targeting", "Retargeting Audience"],
            include_insights=True,
            date_preset="last_7d"
        )
        # Returns ad sets with exact names plus their last 7 days performance
        ```
    """
    act_id = get_act_id()
    if not act_id:
        return {
            "error": "Ad account ID not configured. Set --facebook-ads-ad-account-id at server startup.",
            "data": [],
            "summary": {"requested_names": adset_names, "unmatched_requests": adset_names}
        }

    if not adset_names:
        return {
            "data": [],
            "summary": {"requested_names": [], "unmatched_requests": []}
        }

    access_token = get_access_token()

    # Set default fields if none provided
    if not fields:
        fields = [
            'id', 'name', 'campaign_id', 'status', 'effective_status',
            'daily_budget', 'lifetime_budget', 'optimization_goal',
            'billing_event', 'bid_amount', 'created_time', 'updated_time'
        ]

    if not insights_fields:
        insights_fields = [
            'impressions', 'clicks', 'spend', 'reach',
            'cpc', 'cpm', 'ctr', 'frequency'
        ]

    # Step 1: Fetch each ad set with exact match
    matched_adsets = []

    for requested_name in adset_names:
        name_filter = [
            {
                "field": "name",
                "operator": "EQUAL",
                "value": requested_name
            }
        ]

        adsets_url = f"{FB_GRAPH_URL}/{act_id}/adsets"
        adsets_params = {
            'access_token': access_token,
            'fields': ','.join(fields),
            'filtering': json.dumps(name_filter),
            'limit': limit
        }

        try:
            adsets_data = await _make_graph_api_call(adsets_url, adsets_params)

            if adsets_data.get("data"):
                # Found exact match
                for adset in adsets_data.get("data", []):
                    adset["requested_name"] = requested_name
                    adset["matched_name"] = requested_name  # Exact match
                    matched_adsets.append(adset)

        except Exception as e:
            print(f"Error fetching ad set '{requested_name}': {str(e)}")

    # Step 2: Fetch insights for each matched ad set
    adsets_with_insights = []

    for adset in matched_adsets:
        if include_insights:
            insights_url = f"{FB_GRAPH_URL}/{adset['id']}/insights"

            base_params = {'access_token': access_token}
            insights_params = _build_insights_params(
                base_params,
                fields=insights_fields,
                date_preset=date_preset
            )

            try:
                insights_data = await _make_graph_api_call(insights_url, insights_params)
                adset_with_insights = {
                    **adset,
                    "insights": insights_data.get('data', [])
                }
                adsets_with_insights.append(adset_with_insights)

            except Exception as e:
                # Include ad set even if insights failed, but note the error
                print(f"Error fetching insights for ad set {adset['id']} ({adset['name']}): {str(e)}")
                adset_with_insights = {
                    **adset,
                    "insights": [],
                    "insights_error": str(e)
                }
                adsets_with_insights.append(adset_with_insights)
        else:
            adsets_with_insights.append(adset)

    # Create summary information
    name_mappings = {}
    matched_requested_names = []

    for adset in matched_adsets:
        requested = adset.get("requested_name", "")
        matched = adset.get("matched_name", "")
        if requested:
            name_mappings[requested] = matched
            matched_requested_names.append(requested)

    unmatched_requests = [name for name in adset_names if name not in matched_requested_names]

    return {
        "data": adsets_with_insights,
        "summary": {
            "requested_names": adset_names,
            "total_matched_adsets": len(matched_adsets),
            "adsets_with_insights": len([a for a in adsets_with_insights if "insights_error" not in a]),
            "unmatched_requests": unmatched_requests,
            "name_mappings": name_mappings
        }
    }


async def fetch_objects_by_name(
    object_names: List[str],
    include_insights: bool = True,
    date_preset: Optional[str] = "last_30d",
    insights_fields: Optional[List[str]] = None
) -> str:
    """Unified search for campaigns and ad sets by name with automatic cascading fallback.

    This function automatically tries to find objects by name, first searching for campaigns,
    then searching for ad sets for any names not found as campaigns. Each returned object
    includes an 'object_type' field to identify whether it's a campaign or ad set.

    This implements the Adam-React pattern with cascading fallback:
    1. Try all names as campaigns first (exact match)
    2. For unmatched names, try them as ad sets (exact match)
    3. Return combined results with clear object type identification

    Args:
        object_names (List[str]): List of object names to fetch. Uses exact name matching only.
            The function will automatically try each name as a campaign first, then as an ad set
            if not found. Empty list returns no results.
        include_insights (bool): If True, includes performance insights for each object. Default: True
        date_preset (Optional[str]): Date preset for insights. Default: "last_30d"
            Options: today, yesterday, last_7d, last_14d, last_30d, last_90d, lifetime, etc.
        insights_fields (Optional[List[str]]): Insights metrics to retrieve. Default:
            ['impressions', 'clicks', 'spend', 'reach', 'cpc', 'cpm', 'ctr', 'frequency']

    Returns:
        str: JSON string containing all matched objects with the following structure:
            - 'data' (List[Dict]): Combined list of found objects (campaigns and ad sets), each containing:
                - All standard campaign/ad set fields (id, name, effective_status)
                - 'object_type' (str): Either "campaign" or "adset"
                - 'requested_name' (str): Originally requested name
                - 'matched_name' (str): Actual name that was matched
                - 'insights' (List[Dict]): Performance insights data
                - 'insights_error' (str, optional): Error message if insights failed
            - 'summary' (Dict): Summary information containing:
                - 'requested_names' (List[str]): All originally requested names
                - 'found_as_campaigns' (List[str]): Names found as campaigns
                - 'found_as_adsets' (List[str]): Names found as ad sets
                - 'not_found' (List[str]): Names not found as either campaigns or ad sets
                - 'total_objects_found' (int): Total number of objects found
                - 'campaigns_count' (int): Number of campaigns found
                - 'adsets_count' (int): Number of ad sets found
                - 'objects_with_insights' (int): Number with successful insights

    Example:
        ```python
        result = await fetch_objects_by_name(
            object_names=["Summer Sale Campaign", "Holiday Ad Set", "Black Friday"],
            include_insights=True,
            date_preset="last_7d"
        )
        # Returns campaigns and ad sets found, each with object_type field
        # Automatically tries as campaigns first, then ad sets for unmatched names
        ```

    Note:
        This function implements intelligent cascading fallback:
        1. Tries all names as campaigns first
        2. For unmatched names, tries them as ad sets
        3. Returns combined results with clear object type identification
        Each object in the result includes an 'object_type' field for easy identification.
    """
    act_id = get_act_id()
    if not act_id:
        return json.dumps({
            "error": "Ad account ID not configured. Set --facebook-ads-ad-account-id at server startup.",
            "data": [],
            "summary": {
                "requested_names": object_names,
                "found_as_campaigns": [],
                "found_as_adsets": [],
                "not_found": object_names,
                "total_objects_found": 0,
                "campaigns_count": 0,
                "adsets_count": 0,
                "objects_with_insights": 0
            }
        }, indent=2)

    if not object_names:
        return json.dumps({
            "data": [],
            "summary": {
                "requested_names": [],
                "found_as_campaigns": [],
                "found_as_adsets": [],
                "not_found": [],
                "total_objects_found": 0,
                "campaigns_count": 0,
                "adsets_count": 0,
                "objects_with_insights": 0
            }
        }, indent=2)

    if not insights_fields:
        insights_fields = [
            'impressions', 'clicks', 'spend', 'reach',
            'cpc', 'cpm', 'ctr', 'frequency'
        ]

    # Step 1: Try fetching all names as campaigns first
    campaigns_result = await fetch_campaigns_by_name(
        campaign_names=object_names,
        include_insights=include_insights,
        date_preset=date_preset,
        insights_fields=insights_fields
    )

    # Step 2: Identify which names weren't found as campaigns
    unmatched_campaign_names = campaigns_result.get("summary", {}).get("unmatched_requests", [])

    # Step 3: Try fetching unmatched names as ad sets
    adsets_result = None
    if unmatched_campaign_names:
        adsets_result = await fetch_adsets_by_name(
            adset_names=unmatched_campaign_names,
            include_insights=include_insights,
            date_preset=date_preset,
            insights_fields=insights_fields
        )

    # Step 4: Combine results
    all_objects = []

    # Add campaigns with object_type field
    for campaign in campaigns_result.get("data", []):
        campaign["object_type"] = "campaign"
        all_objects.append(campaign)

    # Add ad sets with object_type field
    if adsets_result:
        for adset in adsets_result.get("data", []):
            adset["object_type"] = "adset"
            all_objects.append(adset)

    # Step 5: Calculate summary statistics
    found_as_campaigns = [obj["requested_name"] for obj in campaigns_result.get("data", [])]
    found_as_adsets = []
    if adsets_result:
        found_as_adsets = [obj["requested_name"] for obj in adsets_result.get("data", [])]

    all_found_names = found_as_campaigns + found_as_adsets
    not_found = [name for name in object_names if name not in all_found_names]

    # Step 6: Return combined results
    result = {
        "data": all_objects,
        "summary": {
            "requested_names": object_names,
            "found_as_campaigns": found_as_campaigns,
            "found_as_adsets": found_as_adsets,
            "not_found": not_found,
            "total_objects_found": len(all_objects),
            "campaigns_count": len(campaigns_result.get("data", [])),
            "adsets_count": len(adsets_result.get("data", [])) if adsets_result else 0,
            "objects_with_insights": len([obj for obj in all_objects if "insights_error" not in obj])
        }
    }

    return json.dumps(result, indent=2)
