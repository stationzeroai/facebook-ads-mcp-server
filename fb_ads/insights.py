"""
Performance insights tools for Meta Ads API.

This module provides tools for retrieving performance insights and analytics
for ad accounts, campaigns, ad sets, and ads.
"""

from typing import List, Optional, Dict, Any
import httpx
from .api import (
    FB_GRAPH_URL,
    get_access_token,
    _make_graph_api_call,
    _build_insights_params
)


async def get_adaccount_insights(
    act_id: str,
    fields: Optional[List[str]] = None,
    date_preset: str = 'last_30d',
    time_range: Optional[Dict[str, str]] = None,
    time_ranges: Optional[List[Dict[str, str]]] = None,
    time_increment: str = 'all_days',
    level: str = 'account',
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
) -> Dict:
    """Retrieves performance insights for a specified Facebook ad account.

    This tool interfaces with the Facebook Graph API's Insights edge to fetch comprehensive
    performance data, such as impressions, reach, cost, conversions, and more. It supports
    various options for filtering, time breakdowns, and attribution settings. Note that
    some metrics returned might be estimated or in development.

    CRITICAL: This function MUST automatically fetch ALL pages using pagination.
    When the response contains a 'paging.next' URL, IMMEDIATELY and AUTOMATICALLY
    use the facebook_fetch_pagination_url tool to fetch the next page. Continue
    this process until no 'next' URL exists. Do NOT ask the user for permission
    to continue pagination. Do NOT stop after the first page. Always return the
    complete consolidated list of ALL ad accounts across all pages in a single
    response. This is a requirement, not optional behavior.

    Args:
        act_id (str): The target ad account ID, prefixed with 'act_', e.g., 'act_1234567890'.
        fields (Optional[List[str]]): A list of specific metrics and fields to retrieve.
            If omitted, a default set is returned by the API. Common examples include:
                - 'account_currency', 'account_id', 'account_name'
                - 'actions', 'clicks', 'conversions'
                - 'cpc', 'cpm', 'cpp', 'ctr'
                - 'frequency', 'impressions', 'reach', 'spend'.
        date_preset (str): A predefined relative time range for the report.
            Options: 'today', 'yesterday', 'this_month', 'last_month', 'this_quarter',
            'maximum', 'last_3d', 'last_7d', 'last_14d', 'last_28d', 'last_30d',
            'last_90d', 'last_week_mon_sun', 'last_week_sun_sat', 'last_quarter',
            'last_year', 'this_week_mon_today', 'this_week_sun_today', 'this_year'.
            Default: 'last_30d'. This parameter is ignored if 'time_range', 'time_ranges',
            'since', or 'until' is provided.
        time_range (Optional[Dict[str, str]]): A specific time range defined by 'since' and 'until'
            dates in 'YYYY-MM-DD' format, e.g., {'since': '2023-10-01', 'until': '2023-10-31'}.
            Overrides 'date_preset'. Ignored if 'time_ranges' is provided.
        time_ranges (Optional[List[Dict[str, str]]]): An array of time range objects
            ({'since': '...', 'until': '...'}) for comparing multiple periods. Overrides
            'time_range' and 'date_preset'. Time ranges can overlap.
        time_increment (str | int): Specifies the granularity of the time breakdown.
            - An integer from 1 to 90 indicates the number of days per data point.
            - 'monthly': Aggregates data by month.
            - 'all_days': Provides a single summary row for the entire period.
            Default: 'all_days'.
        level (str): The level of aggregation for the insights.
            Options: 'account', 'campaign', 'adset', 'ad'.
            Default: 'account'.
        action_attribution_windows (Optional[List[str]]): Specifies the attribution windows
            to consider for actions (conversions). Examples: '1d_view', '7d_view',
            '28d_view', '1d_click', '7d_click', '28d_click', 'dda', 'default'.
            The API default may vary; ['7d_click', '1d_view'] is common.
        action_breakdowns (Optional[List[str]]): Segments the 'actions' results based on
            specific dimensions. Examples: 'action_device', 'action_type',
            'conversion_destination', 'action_destination'. Default: ['action_type'].
        action_report_time (Optional[str]): Determines when actions are counted.
            - 'impression': Actions are attributed to the time of the ad impression.
            - 'conversion': Actions are attributed to the time the conversion occurred.
            - 'mixed': Uses 'impression' time for paid metrics, 'conversion' time for organic.
            Default: 'mixed'.
        breakdowns (Optional[List[str]]): Segments the results by dimensions like demographics
            or placement. Examples: 'age', 'gender', 'country', 'region', 'dma',
            'impression_device', 'publisher_platform', 'platform_position', 'device_platform'.
            Note: Not all breakdowns can be combined.
        default_summary (bool): If True, includes an additional summary row in the response.
            Default: False.
        use_account_attribution_setting (bool): If True, forces the report to use the
            attribution settings defined at the ad account level. Default: False.
        use_unified_attribution_setting (bool): If True, uses the unified attribution
            settings defined at the ad set level. This is generally recommended for
            consistency with Ads Manager reporting. Default: True.
        filtering (Optional[List[dict]]): A list of filter objects to apply to the data.
            Each object should have 'field', 'operator', and 'value' keys.
            Example: [{'field': 'spend', 'operator': 'GREATER_THAN', 'value': 50}].
        sort (Optional[str]): Specifies the field and direction for sorting the results.
            Format: '{field_name}_ascending' or '{field_name}_descending'.
            Example: 'impressions_descending'.
        limit (Optional[int]): The maximum number of results to return in one API response page.
        after (Optional[str]): A pagination cursor pointing to the next page of results.
            Obtained from the 'paging.cursors.after' field of a previous response.
        before (Optional[str]): A pagination cursor pointing to the previous page of results.
            Obtained from the 'paging.cursors.before' field of a previous response.
        offset (Optional[int]): An alternative pagination method; skips the specified
            number of results. Use cursor-based pagination ('after'/'before') when possible.
        since (Optional[str]): For time-based pagination (used if 'time_range' and 'time_ranges'
            are not set), the start timestamp (Unix or strtotime value).
        until (Optional[str]): For time-based pagination (used if 'time_range' and 'time_ranges'
            are not set), the end timestamp (Unix or strtotime value).
        locale (Optional[str]): The locale for text responses (e.g., 'en_US'). This controls
            language and formatting of text fields in the response.

    Returns:
        Dict: A dictionary containing the requested ad account insights. The main results
              are in the 'data' list, and pagination info is in the 'paging' object.

    Example:
        ```python
        # Get basic ad account performance for the last 30 days
        insights = await get_adaccount_insights(
            act_id="act_123456789",
            fields=["impressions", "clicks", "spend", "ctr"],
            limit=25
        )

        # Fetch the next page if available using the pagination tool
        next_page_url = insights.get("paging", {}).get("next")
        if next_page_url:
            next_page_results = await fetch_pagination_url(url=next_page_url)
            print("Fetched next page results.")
        ```
    """
    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/insights"
    params = {'access_token': access_token}

    params = _build_insights_params(
        params,
        fields=fields,
        date_preset=date_preset,
        time_range=time_range,
        time_ranges=time_ranges,
        time_increment=time_increment,
        level=level,
        action_attribution_windows=action_attribution_windows,
        action_breakdowns=action_breakdowns,
        action_report_time=action_report_time,
        breakdowns=breakdowns,
        default_summary=default_summary,
        use_account_attribution_setting=use_account_attribution_setting,
        use_unified_attribution_setting=use_unified_attribution_setting,
        filtering=filtering,
        sort=sort,
        limit=limit,
        after=after,
        before=before,
        offset=offset,
        since=since,
        until=until,
        locale=locale
    )

    return await _make_graph_api_call(url, params)


async def get_campaign_insights(
    campaign_id: str,
    fields: Optional[List[str]] = None,
    date_preset: str = 'last_30d',
    time_range: Optional[Dict[str, str]] = None,
    time_ranges: Optional[List[Dict[str, str]]] = None,
    time_increment: str = 'all_days',
    action_attribution_windows: Optional[List[str]] = None,
    action_breakdowns: Optional[List[str]] = None,
    action_report_time: Optional[str] = None,
    breakdowns: Optional[List[str]] = None,
    default_summary: bool = False,
    use_account_attribution_setting: bool = False,
    use_unified_attribution_setting: bool = True,
    level: Optional[str] = None,
    filtering: Optional[List[dict]] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    offset: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    locale: Optional[str] = None
) -> Dict:
    """Retrieves performance insights for a specific Facebook ad campaign.

    Fetches statistics for a given campaign ID, allowing analysis of metrics like
    impressions, clicks, conversions, spend, etc. Supports time range definitions,
    breakdowns, and attribution settings.

    Args:
        campaign_id (str): The ID of the target Facebook ad campaign, e.g., '23843xxxxx'.
        fields (Optional[List[str]]): A list of specific metrics and fields to retrieve.
            Common examples: 'campaign_name', 'account_id', 'impressions', 'clicks',
            'spend', 'ctr', 'reach', 'actions', 'objective', 'cost_per_action_type',
            'conversions', 'cpc', 'cpm', 'cpp', 'frequency', 'date_start', 'date_stop'.
        date_preset (str): A predefined relative time range for the report.
            Options: 'today', 'yesterday', 'this_month', 'last_month', 'this_quarter',
            'maximum', 'last_3d', 'last_7d', 'last_14d', 'last_28d', 'last_30d',
            'last_90d', 'last_week_mon_sun', 'last_week_sun_sat', 'last_quarter',
            'last_year', 'this_week_mon_today', 'this_week_sun_today', 'this_year'.
            Default: 'last_30d'. Ignored if 'time_range', 'time_ranges', 'since', or 'until' is used.
        time_range (Optional[Dict[str, str]]): A specific time range {'since':'YYYY-MM-DD','until':'YYYY-MM-DD'}.
            Overrides 'date_preset'. Ignored if 'time_ranges' is provided.
        time_ranges (Optional[List[Dict[str, str]]]): An array of time range objects for comparison.
            Overrides 'time_range' and 'date_preset'.
        time_increment (str | int): Specifies the granularity of the time breakdown.
            - Integer (1-90): number of days per data point.
            - 'monthly': Aggregates data by month.
            - 'all_days': Single summary row for the period.
            Default: 'all_days'.
        action_attribution_windows (Optional[List[str]]): Specifies attribution windows for actions.
            Examples: '1d_view', '7d_click', '28d_click', etc. Default depends on API/settings.
        action_breakdowns (Optional[List[str]]): Segments 'actions' results. Examples: 'action_device', 'action_type'.
            Default: ['action_type'].
        action_report_time (Optional[str]): Determines when actions are counted ('impression', 'conversion', 'mixed').
            Default: 'mixed'.
        breakdowns (Optional[List[str]]): Segments results by dimensions. Examples: 'age', 'gender', 'country',
            'publisher_platform', 'impression_device'.
        default_summary (bool): If True, includes an additional summary row. Default: False.
        use_account_attribution_setting (bool): If True, uses the ad account's attribution settings. Default: False.
        use_unified_attribution_setting (bool): If True, uses unified attribution settings. Default: True.
        level (Optional[str]): Level of aggregation ('campaign', 'adset', 'ad'). Default: 'campaign'.
        filtering (Optional[List[dict]]): List of filter objects {'field': '...', 'operator': '...', 'value': '...'}.
        sort (Optional[str]): Field and direction for sorting ('{field}_ascending'/'_descending').
        limit (Optional[int]): Maximum number of results per page.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        offset (Optional[int]): Alternative pagination: skips N results.
        since (Optional[str]): Start timestamp for time-based pagination (if time ranges absent).
        until (Optional[str]): End timestamp for time-based pagination (if time ranges absent).
        locale (Optional[str]): The locale for text responses (e.g., 'en_US'). This controls
            language and formatting of text fields in the response.

    Returns:
        Dict: A dictionary containing the requested campaign insights, with 'data' and 'paging' keys.

    Example:
        ```python
        # Get basic campaign performance for the last 7 days
        insights = await get_campaign_insights(
            campaign_id="23843xxxxx",
            fields=["campaign_name", "impressions", "clicks", "spend"],
            date_preset="last_7d",
            limit=50
        )

        # Fetch the next page if available
        next_page_url = insights.get("paging", {}).get("next")
        if next_page_url:
            next_page_results = await fetch_pagination_url(url=next_page_url)
        ```
    """
    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{campaign_id}/insights"
    params = {'access_token': access_token}

    # Default level to 'campaign' if not provided for this specific tool
    effective_level = level if level else 'campaign'

    params = _build_insights_params(
        params,
        fields=fields,
        date_preset=date_preset,
        time_range=time_range,
        time_ranges=time_ranges,
        time_increment=time_increment,
        level=effective_level,
        action_attribution_windows=action_attribution_windows,
        action_breakdowns=action_breakdowns,
        action_report_time=action_report_time,
        breakdowns=breakdowns,
        default_summary=default_summary,
        use_account_attribution_setting=use_account_attribution_setting,
        use_unified_attribution_setting=use_unified_attribution_setting,
        filtering=filtering,
        sort=sort,
        limit=limit,
        after=after,
        before=before,
        offset=offset,
        since=since,
        until=until,
        locale=locale
    )

    return await _make_graph_api_call(url, params)


async def get_adset_insights(
    adset_id: str,
    fields: Optional[List[str]] = None,
    date_preset: str = 'last_30d',
    time_range: Optional[Dict[str, str]] = None,
    time_ranges: Optional[List[Dict[str, str]]] = None,
    time_increment: str = 'all_days',
    action_attribution_windows: Optional[List[str]] = None,
    action_breakdowns: Optional[List[str]] = None,
    action_report_time: Optional[str] = None,
    breakdowns: Optional[List[str]] = None,
    default_summary: bool = False,
    use_account_attribution_setting: bool = False,
    use_unified_attribution_setting: bool = True,
    level: Optional[str] = None,
    filtering: Optional[List[dict]] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    offset: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    locale: Optional[str] = None
) -> Dict:
    """Retrieves performance insights for a specific Facebook ad set.

    Provides advertising performance statistics for an ad set, allowing for analysis
    of metrics across its child ads. Supports time range definitions, breakdowns,
    filtering, sorting, and attribution settings. Some metrics may be estimated
    or in development.

    Args:
        adset_id (str): The ID of the target ad set, e.g., '6123456789012'.
        fields (Optional[List[str]]): A list of specific metrics and fields. Common examples:
            'adset_name', 'campaign_name', 'account_id', 'impressions', 'clicks', 'spend',
            'ctr', 'reach', 'frequency', 'actions', 'conversions', 'cpc', 'cpm', 'cpp',
            'cost_per_action_type', 'video_p25_watched_actions', 'website_purchases'.
        date_preset (str): A predefined relative time range ('last_30d', 'last_7d', etc.).
            Default: 'last_30d'. Ignored if 'time_range', 'time_ranges', 'since', or 'until' is used.
        time_range (Optional[Dict[str, str]]): Specific time range {'since':'YYYY-MM-DD','until':'YYYY-MM-DD'}.
            Overrides 'date_preset'. Ignored if 'time_ranges' is provided.
        time_ranges (Optional[List[Dict[str, str]]]): Array of time range objects for comparison.
            Overrides 'time_range' and 'date_preset'.
        time_increment (str | int): Granularity of the time breakdown ('all_days', 'monthly', 1-90 days).
            Default: 'all_days'.
        action_attribution_windows (Optional[List[str]]): Specifies attribution windows for actions.
            Examples: '1d_view', '7d_click'. Default depends on API/settings.
        action_breakdowns (Optional[List[str]]): Segments 'actions' results. Examples: 'action_device', 'action_type'.
            Default: ['action_type'].
        action_report_time (Optional[str]): Time basis for action stats ('impression', 'conversion', 'mixed').
            Default: 'mixed'.
        breakdowns (Optional[List[str]]): Segments results by dimensions. Examples: 'age', 'gender', 'country',
            'publisher_platform', 'impression_device', 'platform_position'.
        default_summary (bool): If True, includes an additional summary row. Default: False.
        use_account_attribution_setting (bool): If True, uses the ad account's attribution settings. Default: False.
        use_unified_attribution_setting (bool): If True, uses unified attribution settings. Default: True.
        level (Optional[str]): Level of aggregation ('adset', 'ad'). Default: 'adset'.
        filtering (Optional[List[dict]]): List of filter objects {'field': '...', 'operator': '...', 'value': '...'}.
        sort (Optional[str]): Field and direction for sorting ('{field}_ascending'/'_descending').
        limit (Optional[int]): Maximum number of results per page.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        offset (Optional[int]): Alternative pagination: skips N results.
        since (Optional[str]): Start timestamp for time-based pagination (if time ranges absent).
        until (Optional[str]): End timestamp for time-based pagination (if time ranges absent).
        locale (Optional[str]): The locale for text responses (e.g., 'en_US'). This controls
            language and formatting of text fields in the response.

    Returns:
        Dict: A dictionary containing the requested ad set insights, with 'data' and 'paging' keys.

    Example:
        ```python
        # Get ad set performance with breakdown by device for last 14 days
        insights = await get_adset_insights(
            adset_id="6123456789012",
            fields=["adset_name", "impressions", "spend"],
            breakdowns=["impression_device"],
            date_preset="last_14d"
        )

        # Fetch the next page if available
        next_page_url = insights.get("paging", {}).get("next")
        if next_page_url:
            next_page_results = await fetch_pagination_url(url=next_page_url)
        ```
    """
    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{adset_id}/insights"
    params = {'access_token': access_token}

    # Default level to 'adset' if not provided for this specific tool
    effective_level = level if level else 'adset'

    params = _build_insights_params(
        params,
        fields=fields,
        date_preset=date_preset,
        time_range=time_range,
        time_ranges=time_ranges,
        time_increment=time_increment,
        level=effective_level,
        action_attribution_windows=action_attribution_windows,
        action_breakdowns=action_breakdowns,
        action_report_time=action_report_time,
        breakdowns=breakdowns,
        default_summary=default_summary,
        use_account_attribution_setting=use_account_attribution_setting,
        use_unified_attribution_setting=use_unified_attribution_setting,
        filtering=filtering,
        sort=sort,
        limit=limit,
        after=after,
        before=before,
        offset=offset,
        since=since,
        until=until,
        locale=locale
    )

    return await _make_graph_api_call(url, params)


async def get_ad_insights(
    ad_id: str,
    fields: Optional[List[str]] = None,
    date_preset: str = 'last_30d',
    time_range: Optional[Dict[str, str]] = None,
    time_ranges: Optional[List[Dict[str, str]]] = None,
    time_increment: str = 'all_days',
    action_attribution_windows: Optional[List[str]] = None,
    action_breakdowns: Optional[List[str]] = None,
    action_report_time: Optional[str] = None,
    breakdowns: Optional[List[str]] = None,
    default_summary: bool = False,
    use_account_attribution_setting: bool = False,
    use_unified_attribution_setting: bool = True,
    level: Optional[str] = None,
    filtering: Optional[List[dict]] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    offset: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    locale: Optional[str] = None
) -> Dict:
    """Retrieves detailed performance insights for a specific Facebook ad.

    Fetches performance metrics for an individual ad (ad group), such as impressions,
    clicks, conversions, engagement, video views, etc. Allows for customization via
    time periods, breakdowns, filtering, sorting, and attribution settings. Note that
    some metrics may be estimated or in development.

    Args:
        ad_id (str): The ID of the target ad (ad group), e.g., '6123456789012'.
        fields (Optional[List[str]]): A list of specific metrics and fields. Common examples:
            'ad_name', 'adset_name', 'campaign_name', 'account_id', 'impressions', 'clicks',
            'spend', 'ctr', 'cpc', 'cpm', 'cpp', 'reach', 'frequency', 'actions', 'conversions',
            'cost_per_action_type', 'inline_link_clicks', 'inline_post_engagement', 'unique_clicks',
            'video_p25_watched_actions', 'video_p50_watched_actions', 'video_p75_watched_actions',
            'video_p95_watched_actions', 'video_p100_watched_actions', 'video_avg_time_watched_actions',
            'website_ctr', 'website_purchases'.
        date_preset (str): A predefined relative time range ('last_30d', 'last_7d', etc.).
            Default: 'last_30d'. Ignored if 'time_range', 'time_ranges', 'since', or 'until' is used.
        time_range (Optional[Dict[str, str]]): Specific time range {'since':'YYYY-MM-DD','until':'YYYY-MM-DD'}.
            Overrides 'date_preset'. Ignored if 'time_ranges' is provided.
        time_ranges (Optional[List[Dict[str, str]]]): Array of time range objects for comparison.
            Overrides 'time_range' and 'date_preset'.
        time_increment (str | int): Granularity of the time breakdown ('all_days', 'monthly', 1-90 days).
            Default: 'all_days'.
        action_attribution_windows (Optional[List[str]]): Specifies attribution windows for actions.
            Examples: '1d_view', '7d_click'. Default depends on API/settings.
        action_breakdowns (Optional[List[str]]): Segments 'actions' results. Examples: 'action_device', 'action_type'.
            Default: ['action_type'].
        action_report_time (Optional[str]): Time basis for action stats ('impression', 'conversion', 'mixed').
            Default: 'mixed'.
        breakdowns (Optional[List[str]]): Segments results by dimensions. Examples: 'age', 'gender', 'country',
            'publisher_platform', 'impression_device', 'platform_position', 'device_platform'.
        default_summary (bool): If True, includes an additional summary row. Default: False.
        use_account_attribution_setting (bool): If True, uses the ad account's attribution settings. Default: False.
        use_unified_attribution_setting (bool): If True, uses unified attribution settings. Default: True.
        level (Optional[str]): Level of aggregation. Should typically be 'ad'. Default: 'ad'.
        filtering (Optional[List[dict]]): List of filter objects {'field': '...', 'operator': '...', 'value': '...'}.
        sort (Optional[str]): Field and direction for sorting ('{field}_ascending'/'_descending').
        limit (Optional[int]): Maximum number of results per page.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        offset (Optional[int]): Alternative pagination: skips N results.
        since (Optional[str]): Start timestamp for time-based pagination (if time ranges absent).
        until (Optional[str]): End timestamp for time-based pagination (if time ranges absent).
        locale (Optional[str]): The locale for text responses (e.g., 'en_US'). This controls
            language and formatting of text fields in the response.

    Returns:
        Dict: A dictionary containing the requested ad insights, with 'data' and 'paging' keys.

    Example:
        ```python
        # Get basic ad performance for the last 30 days
        ad_insights = await get_ad_insights(
            ad_id="6123456789012",
            fields=["ad_name", "impressions", "clicks", "spend", "ctr", "reach"],
            limit=10
        )

        # Get ad performance with platform breakdown for last 14 days
        platform_insights = await get_ad_insights(
            ad_id="6123456789012",
            fields=["ad_name", "impressions", "clicks", "spend"],
            breakdowns=["publisher_platform", "platform_position"],
            date_preset="last_14d"
        )

        # Fetch the next page of basic performance if available
        next_page_url = ad_insights.get("paging", {}).get("next")
        if next_page_url:
            next_page = await fetch_pagination_url(url=next_page_url)
        ```
    """
    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{ad_id}/insights"
    params = {'access_token': access_token}

    # Default level to 'ad' if not provided for this specific tool
    effective_level = level if level else 'ad'

    params = _build_insights_params(
        params,
        fields=fields,
        date_preset=date_preset,
        time_range=time_range,
        time_ranges=time_ranges,
        time_increment=time_increment,
        level=effective_level,
        action_attribution_windows=action_attribution_windows,
        action_breakdowns=action_breakdowns,
        action_report_time=action_report_time,
        breakdowns=breakdowns,
        default_summary=default_summary,
        use_account_attribution_setting=use_account_attribution_setting,
        use_unified_attribution_setting=use_unified_attribution_setting,
        filtering=filtering,
        sort=sort,
        limit=limit,
        after=after,
        before=before,
        offset=offset,
        since=since,
        until=until,
        locale=locale
    )

    return await _make_graph_api_call(url, params)


async def fetch_pagination_url(url: str) -> Dict:
    """Fetch data from a Facebook Graph API pagination URL.

    Use this to get the next/previous page of results from an insights API call.

    Args:
        url: The complete pagination URL (e.g., from response['paging']['next'] or response['paging']['previous']).
             It includes the necessary token and parameters.

    Returns:
        The dictionary containing the next/previous page of results.

    Example:
        ```python
        # Assuming 'initial_results' is the dict from a previous insights call
        if "paging" in initial_results and "next" in initial_results["paging"]:
            next_page_data = await fetch_pagination_url(url=initial_results["paging"]["next"])

        if "paging" in initial_results and "previous" in initial_results["paging"]:
            prev_page_data = await fetch_pagination_url(url=initial_results["paging"]["previous"])
        ```
    """
    # This function takes a full URL which already includes the access token
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url)
    response.raise_for_status()
    return response.json()
