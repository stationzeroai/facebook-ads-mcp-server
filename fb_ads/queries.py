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
    _make_graph_api_call,
    _build_insights_params
)


async def fetch_campaigns_by_name(
    act_id: str,
    name_query: str,
    fields: Optional[List[str]] = None,
    include_insights: bool = True,
    date_preset: Optional[str] = "last_30d",
    insights_fields: Optional[List[str]] = None,
    limit: Optional[int] = 25
) -> str:
    """Search for campaigns by name and optionally include performance insights.

    This function searches for campaigns whose names contain the query string
    and can automatically fetch performance metrics for matched campaigns.

    Args:
        act_id (str): Ad account ID (with act_ prefix)
        name_query (str): Search term to match in campaign names (case-insensitive)
        fields (Optional[List[str]]): Campaign fields to retrieve. Default:
            ['id', 'name', 'objective', 'status', 'effective_status', 'daily_budget', 'lifetime_budget']
        include_insights (bool): If True, includes performance insights for each campaign. Default: True
        date_preset (Optional[str]): Date preset for insights. Default: "last_30d"
            Options: today, yesterday, last_7d, last_14d, last_30d, last_90d, lifetime, etc.
        insights_fields (Optional[List[str]]): Insights metrics to retrieve. Default:
            ['impressions', 'clicks', 'spend', 'reach', 'cpc', 'cpm', 'ctr']
        limit (Optional[int]): Maximum number of campaigns to return. Default: 25

    Returns:
        str: JSON string containing matched campaigns with optional insights.

    Example:
        ```python
        result = await fetch_campaigns_by_name(
            act_id="act_123456789",
            name_query="summer",
            include_insights=True,
            date_preset="last_7d"
        )
        # Returns campaigns with "summer" in the name plus their last 7 days performance
        ```
    """
    if not act_id:
        return json.dumps({"error": "No ad account ID (act_id) provided"}, indent=2)

    if not name_query:
        return json.dumps({"error": "No name query provided"}, indent=2)

    access_token = get_access_token()

    # Set default fields if none provided
    if not fields:
        fields = [
            'id', 'name', 'objective', 'status', 'effective_status',
            'daily_budget', 'lifetime_budget', 'created_time', 'updated_time'
        ]

    # Fetch all campaigns with name filtering
    campaigns_url = f"{FB_GRAPH_URL}/{act_id}/campaigns"
    campaigns_params = {
        'access_token': access_token,
        'fields': ','.join(fields),
        'filtering': json.dumps([
            {
                "field": "name",
                "operator": "CONTAIN",
                "value": name_query
            }
        ]),
        'limit': limit
    }

    try:
        campaigns_data = await _make_graph_api_call(campaigns_url, campaigns_params)

        if 'data' not in campaigns_data or not campaigns_data['data']:
            return json.dumps({
                "message": f"No campaigns found matching '{name_query}'",
                "query": name_query,
                "results": []
            }, indent=2)

        campaigns = campaigns_data['data']

        # Fetch insights if requested
        if include_insights:
            if not insights_fields:
                insights_fields = [
                    'impressions', 'clicks', 'spend', 'reach',
                    'cpc', 'cpm', 'ctr', 'frequency'
                ]

            for campaign in campaigns:
                insights_url = f"{FB_GRAPH_URL}/{campaign['id']}/insights"

                base_params = {'access_token': access_token}
                insights_params = _build_insights_params(
                    base_params,
                    fields=insights_fields,
                    date_preset=date_preset
                )

                try:
                    insights_data = await _make_graph_api_call(insights_url, insights_params)
                    campaign['insights'] = insights_data.get('data', [])
                except Exception as e:
                    campaign['insights_error'] = str(e)

        result = {
            "query": name_query,
            "total_found": len(campaigns),
            "campaigns": campaigns
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "error": "Failed to fetch campaigns by name",
            "details": str(e),
            "query": name_query
        }, indent=2)


async def fetch_adsets_by_name(
    act_id: str,
    name_query: str,
    fields: Optional[List[str]] = None,
    include_insights: bool = True,
    date_preset: Optional[str] = "last_30d",
    insights_fields: Optional[List[str]] = None,
    limit: Optional[int] = 25
) -> str:
    """Search for ad sets by name and optionally include performance insights.

    This function searches for ad sets whose names contain the query string
    and can automatically fetch performance metrics for matched ad sets.

    Args:
        act_id (str): Ad account ID (with act_ prefix)
        name_query (str): Search term to match in ad set names (case-insensitive)
        fields (Optional[List[str]]): Ad set fields to retrieve. Default:
            ['id', 'name', 'campaign_id', 'status', 'effective_status', 'daily_budget', 'lifetime_budget', 'optimization_goal']
        include_insights (bool): If True, includes performance insights for each ad set. Default: True
        date_preset (Optional[str]): Date preset for insights. Default: "last_30d"
        insights_fields (Optional[List[str]]): Insights metrics to retrieve. Default:
            ['impressions', 'clicks', 'spend', 'reach', 'cpc', 'cpm', 'ctr']
        limit (Optional[int]): Maximum number of ad sets to return. Default: 25

    Returns:
        str: JSON string containing matched ad sets with optional insights.

    Example:
        ```python
        result = await fetch_adsets_by_name(
            act_id="act_123456789",
            name_query="premium",
            include_insights=True,
            date_preset="last_7d"
        )
        # Returns ad sets with "premium" in the name plus their last 7 days performance
        ```
    """
    if not act_id:
        return json.dumps({"error": "No ad account ID (act_id) provided"}, indent=2)

    if not name_query:
        return json.dumps({"error": "No name query provided"}, indent=2)

    access_token = get_access_token()

    # Set default fields if none provided
    if not fields:
        fields = [
            'id', 'name', 'campaign_id', 'status', 'effective_status',
            'daily_budget', 'lifetime_budget', 'optimization_goal',
            'billing_event', 'bid_amount', 'created_time', 'updated_time'
        ]

    # Fetch all ad sets with name filtering
    adsets_url = f"{FB_GRAPH_URL}/{act_id}/adsets"
    adsets_params = {
        'access_token': access_token,
        'fields': ','.join(fields),
        'filtering': json.dumps([
            {
                "field": "name",
                "operator": "CONTAIN",
                "value": name_query
            }
        ]),
        'limit': limit
    }

    try:
        adsets_data = await _make_graph_api_call(adsets_url, adsets_params)

        if 'data' not in adsets_data or not adsets_data['data']:
            return json.dumps({
                "message": f"No ad sets found matching '{name_query}'",
                "query": name_query,
                "results": []
            }, indent=2)

        adsets = adsets_data['data']

        # Fetch insights if requested
        if include_insights:
            if not insights_fields:
                insights_fields = [
                    'impressions', 'clicks', 'spend', 'reach',
                    'cpc', 'cpm', 'ctr', 'frequency'
                ]

            for adset in adsets:
                insights_url = f"{FB_GRAPH_URL}/{adset['id']}/insights"

                base_params = {'access_token': access_token}
                insights_params = _build_insights_params(
                    base_params,
                    fields=insights_fields,
                    date_preset=date_preset
                )

                try:
                    insights_data = await _make_graph_api_call(insights_url, insights_params)
                    adset['insights'] = insights_data.get('data', [])
                except Exception as e:
                    adset['insights_error'] = str(e)

        result = {
            "query": name_query,
            "total_found": len(adsets),
            "adsets": adsets
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "error": "Failed to fetch ad sets by name",
            "details": str(e),
            "query": name_query
        }, indent=2)


async def fetch_objects_by_name(
    act_id: str,
    name_query: str,
    object_types: Optional[List[str]] = None,
    include_insights: bool = True,
    date_preset: Optional[str] = "last_30d",
    insights_fields: Optional[List[str]] = None,
    limit: Optional[int] = 10
) -> str:
    """Universal search for campaigns, ad sets, and ads by name with insights.

    This function searches across multiple object types simultaneously and returns
    all matching results with optional performance insights.

    Args:
        act_id (str): Ad account ID (with act_ prefix)
        name_query (str): Search term to match in object names (case-insensitive)
        object_types (Optional[List[str]]): Types of objects to search. Default: ['campaigns', 'adsets', 'ads']
            Options: 'campaigns', 'adsets', 'ads'
        include_insights (bool): If True, includes performance insights for each object. Default: True
        date_preset (Optional[str]): Date preset for insights. Default: "last_30d"
        insights_fields (Optional[List[str]]): Insights metrics to retrieve. Default:
            ['impressions', 'clicks', 'spend', 'reach', 'cpc', 'cpm', 'ctr']
        limit (Optional[int]): Maximum number of each object type to return. Default: 10

    Returns:
        str: JSON string containing all matched objects organized by type with optional insights.

    Example:
        ```python
        result = await fetch_objects_by_name(
            act_id="act_123456789",
            name_query="black friday",
            object_types=["campaigns", "adsets"],
            include_insights=True,
            date_preset="last_7d"
        )
        # Returns all campaigns and ad sets with "black friday" in the name plus their performance
        ```
    """
    if not act_id:
        return json.dumps({"error": "No ad account ID (act_id) provided"}, indent=2)

    if not name_query:
        return json.dumps({"error": "No name query provided"}, indent=2)

    if not object_types:
        object_types = ['campaigns', 'adsets', 'ads']

    access_token = get_access_token()

    if not insights_fields:
        insights_fields = [
            'impressions', 'clicks', 'spend', 'reach',
            'cpc', 'cpm', 'ctr', 'frequency'
        ]

    results = {
        "query": name_query,
        "date_preset": date_preset if include_insights else None,
        "results": {}
    }

    # Search campaigns
    if 'campaigns' in object_types:
        try:
            campaigns_url = f"{FB_GRAPH_URL}/{act_id}/campaigns"
            campaigns_params = {
                'access_token': access_token,
                'fields': 'id,name,objective,status,effective_status,daily_budget,lifetime_budget',
                'filtering': json.dumps([{"field": "name", "operator": "CONTAIN", "value": name_query}]),
                'limit': limit
            }

            campaigns_data = await _make_graph_api_call(campaigns_url, campaigns_params)
            campaigns = campaigns_data.get('data', [])

            if include_insights:
                for campaign in campaigns:
                    insights_url = f"{FB_GRAPH_URL}/{campaign['id']}/insights"
                    base_params = {'access_token': access_token}
                    insights_params = _build_insights_params(
                        base_params, fields=insights_fields, date_preset=date_preset
                    )
                    try:
                        insights_data = await _make_graph_api_call(insights_url, insights_params)
                        campaign['insights'] = insights_data.get('data', [])
                    except:
                        campaign['insights'] = []

            results['results']['campaigns'] = campaigns

        except Exception as e:
            results['results']['campaigns_error'] = str(e)

    # Search ad sets
    if 'adsets' in object_types:
        try:
            adsets_url = f"{FB_GRAPH_URL}/{act_id}/adsets"
            adsets_params = {
                'access_token': access_token,
                'fields': 'id,name,campaign_id,status,effective_status,optimization_goal,daily_budget,lifetime_budget',
                'filtering': json.dumps([{"field": "name", "operator": "CONTAIN", "value": name_query}]),
                'limit': limit
            }

            adsets_data = await _make_graph_api_call(adsets_url, adsets_params)
            adsets = adsets_data.get('data', [])

            if include_insights:
                for adset in adsets:
                    insights_url = f"{FB_GRAPH_URL}/{adset['id']}/insights"
                    base_params = {'access_token': access_token}
                    insights_params = _build_insights_params(
                        base_params, fields=insights_fields, date_preset=date_preset
                    )
                    try:
                        insights_data = await _make_graph_api_call(insights_url, insights_params)
                        adset['insights'] = insights_data.get('data', [])
                    except:
                        adset['insights'] = []

            results['results']['adsets'] = adsets

        except Exception as e:
            results['results']['adsets_error'] = str(e)

    # Search ads
    if 'ads' in object_types:
        try:
            ads_url = f"{FB_GRAPH_URL}/{act_id}/ads"
            ads_params = {
                'access_token': access_token,
                'fields': 'id,name,campaign_id,adset_id,status,effective_status',
                'filtering': json.dumps([{"field": "name", "operator": "CONTAIN", "value": name_query}]),
                'limit': limit
            }

            ads_data = await _make_graph_api_call(ads_url, ads_params)
            ads = ads_data.get('data', [])

            if include_insights:
                for ad in ads:
                    insights_url = f"{FB_GRAPH_URL}/{ad['id']}/insights"
                    base_params = {'access_token': access_token}
                    insights_params = _build_insights_params(
                        base_params, fields=insights_fields, date_preset=date_preset
                    )
                    try:
                        insights_data = await _make_graph_api_call(insights_url, insights_params)
                        ad['insights'] = insights_data.get('data', [])
                    except:
                        ad['insights'] = []

            results['results']['ads'] = ads

        except Exception as e:
            results['results']['ads_error'] = str(e)

    # Add summary counts
    results['summary'] = {
        'total_campaigns': len(results['results'].get('campaigns', [])),
        'total_adsets': len(results['results'].get('adsets', [])),
        'total_ads': len(results['results'].get('ads', []))
    }

    return json.dumps(results, indent=2)
