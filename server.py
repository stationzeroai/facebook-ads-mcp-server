"""
Facebook Ads MCP Server

This MCP server provides comprehensive Facebook/Meta Ads management tools,
including campaign creation, ad set management, creative management, targeting,
insights, and more.

All tools are prefixed with 'facebook_' to avoid namespace collisions when
used alongside other MCP servers (e.g., Google Ads).
"""

from mcp.server.fastmcp import FastMCP
from typing import Dict, List, Optional, Any, Union

# Import all tool modules
from fb_ads import campaigns, adsets, ads, meta_utils, queries, insights, s3_integration

# Import API initialization
from fb_ads.api import init_config_from_args

# Create MCP server
mcp = FastMCP("facebook-ads-mcp-server")

# Initialize configuration from command-line arguments
init_config_from_args()


# ==============================================================================
# CAMPAIGN TOOLS (6 tools)
# ==============================================================================

@mcp.tool()
async def facebook_create_cbo_campaign(
    name: str,
    objective: str,
    status: str = "PAUSED",
    daily_budget: Optional[float] = None,
    lifetime_budget: Optional[float] = None,
    buying_type: Optional[str] = "AUCTION",
    bid_strategy: Optional[str] = None,
    bid_amount: Optional[float] = None,
    spend_cap: Optional[float] = None
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

    Returns:
        str: JSON string containing the created campaign details or error message.
    """
    return await campaigns.create_cbo_campaign(
        name, objective, status, daily_budget, lifetime_budget,
        buying_type, bid_strategy, bid_amount, spend_cap
    )


@mcp.tool()
async def facebook_create_abo_campaign(
    name: str,
    objective: str = "OUTCOME_SALES",
    status: str = "PAUSED",
    buying_type: Optional[str] = "AUCTION"
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

    Returns:
        str: JSON string containing the created campaign details or error message.
    """
    return await campaigns.create_abo_campaign(
        name, objective, status, buying_type
    )


@mcp.tool()
async def facebook_update_campaign_budget(
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
    return await campaigns.update_campaign_budget(
        campaign_id, daily_budget, lifetime_budget
    )


@mcp.tool()
async def facebook_deactivate_or_activate_campaign(
    campaign_id: str,
    status: str,
) -> str:
    """Update campaign status (activate, pause, or archive).

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
    return await campaigns.deactivate_or_activate_campaign(campaign_id, status)


@mcp.tool()
async def facebook_get_campaign_by_id(
    campaign_id: str,
    fields: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> Dict:
    """Retrieves detailed information about a specific Facebook ad campaign by its ID.

    Args:
        campaign_id (str): The ID of the campaign to retrieve information for.
        fields (Optional[List[str]]): A list of specific fields to retrieve. If None,
            a default set of fields will be returned.
        date_format (Optional[str]): Format for date responses. Options:
            - 'U': Unix timestamp (seconds since epoch)
            - 'Y-m-d H:i:s': MySQL datetime format
            - None: ISO 8601 format (default)

    Returns:
        Dict: A dictionary containing the requested campaign information.
    """
    return await campaigns.get_campaign_by_id(campaign_id, fields, date_format)


@mcp.tool()
async def facebook_get_campaigns_by_adaccount(
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

    Args:
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
    """
    return await campaigns.get_campaigns_by_adaccount(
        fields, filtering, limit, after, before, date_preset,
        time_range, updated_since, effective_status, is_completed,
        special_ad_categories, objective, buyer_guarantee_agreement_status,
        date_format, include_drafts
    )


# ==============================================================================
# AD SET TOOLS (6 tools)
# ==============================================================================

@mcp.tool()
async def facebook_create_adset(
    campaign_id: str,
    name: str,
    optimization_goal: str,
    billing_event: str,
    custom_event_type: Optional[str] = None,
    status: str = "PAUSED",
    daily_budget: Optional[str] = None,
    lifetime_budget: Optional[str] = None,
    targeting: Union[str, Dict[str, Any], None] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    bid_strategy: Optional[str] = None,
    bid_cap: Optional[str] = None,
    roas_average_floor: Optional[str] = None,
    frequency_control_specs: Optional[List[Dict[str, Any]]] = None,
    promoted_object: Optional[Dict[str, Any]] = None
) -> str:
    """Create a new ad set with comprehensive targeting options.

    CRITICAL: Returns ONLY the JSON result. This tool is complete in itself and creates the ad set.
    Do not attempt to interpret or "try again" - the JSON contains success or error information.

    Args:
        campaign_id (str): The Campaign ID where the ad set will be created
        name (str): Ad set name
        optimization_goal (str): What to optimize for. Common values:
            OFFSITE_CONVERSIONS, VALUE, LINK_CLICKS, LANDING_PAGE_VIEWS,
            IMPRESSIONS, REACH, etc.
        billing_event (str): What you're charged for. Common values:
            IMPRESSIONS, LINK_CLICKS, POST_ENGAGEMENT
        custom_event_type (str): Required for OFFSITE_CONVERSIONS. Options:
            PURCHASE, ADD_TO_CART, LEAD, COMPLETE_REGISTRATION, etc.
        status (str): Initial status (default: PAUSED). Options: ACTIVE, PAUSED
        daily_budget (str): Daily budget in cents
        lifetime_budget (str): Lifetime budget in cents
        targeting (Union[str, Dict, None]): Targeting specification as dict or JSON string
        start_time (str): Start time in ISO 8601 format
        end_time (str): End time in ISO 8601 format
        bid_strategy (str): Bid strategy. Options:
            LOWEST_COST_WITHOUT_CAP, LOWEST_COST_WITH_BID_CAP, COST_CAP, LOWEST_COST_WITH_MIN_ROAS
        bid_cap (str): Maximum bid amount in cents
        roas_average_floor (str): Minimum ROAS target
        frequency_control_specs (List[Dict]): Frequency capping rules
        promoted_object (Dict): Object being promoted (pixel_id, custom_event_type, etc.)

    Returns:
        str: JSON string containing the created ad set details or error message.
    """
    return await adsets.create_adset(
        campaign_id, name, optimization_goal, billing_event,
        custom_event_type, status, daily_budget, lifetime_budget, targeting,
        start_time, end_time, bid_strategy, bid_cap, roas_average_floor,
        frequency_control_specs, promoted_object
    )


@mcp.tool()
async def facebook_update_adset(
    adset_id: str,
    name: Optional[str] = None,
    status: Optional[str] = None,
    daily_budget: Optional[str] = None,
    lifetime_budget: Optional[str] = None,
    targeting: Union[str, Dict[str, Any], None] = None,
    bid_strategy: Optional[str] = None,
    bid_cap: Optional[str] = None,
    roas_average_floor: Optional[str] = None,
    frequency_control_specs: Optional[List[Dict[str, Any]]] = None
) -> str:
    """Update an existing ad set's properties.

    Args:
        adset_id (str): The Ad Set ID to update
        name (str): New ad set name. Optional.
        status (str): New status. Options: ACTIVE, PAUSED, ARCHIVED, DELETED. Optional.
        daily_budget (str): New daily budget in cents. Optional.
        lifetime_budget (str): New lifetime budget in cents. Optional.
        targeting (Union[str, Dict, None]): New targeting specification. Optional.
        bid_strategy (str): New bid strategy. Optional.
        bid_cap (str): New bid cap in cents. Optional.
        roas_average_floor (str): New ROAS target. Optional.
        frequency_control_specs (List[Dict]): New frequency capping rules. Optional.

    Returns:
        str: JSON string containing update result or error message.
    """
    return await adsets.update_adset(
        adset_id, name, status, daily_budget, lifetime_budget, targeting,
        bid_strategy, bid_cap, roas_average_floor, frequency_control_specs
    )


@mcp.tool()
async def facebook_get_adset_by_id(
    adset_id: str,
    fields: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> str:
    """Retrieves detailed information about a specific Facebook ad set by its ID.

    Args:
        adset_id (str): The ID of the ad set to retrieve information for.
        fields (Optional[List[str]]): A list of specific fields to retrieve.
        date_format (Optional[str]): Format for date responses.

    Returns:
        str: JSON string containing the requested ad set information or error message.
    """
    return await adsets.get_adset_by_id(adset_id, fields, date_format)


@mcp.tool()
async def facebook_get_adsets_by_ids(
    adset_ids: List[str],
    fields: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> str:
    """Retrieves detailed information about multiple Facebook ad sets by their IDs.

    Args:
        adset_ids (List[str]): List of ad set IDs to retrieve.
        fields (Optional[List[str]]): A list of specific fields to retrieve.
        date_format (Optional[str]): Format for date responses.

    Returns:
        str: JSON string containing the requested ad sets information or error message.
    """
    return await adsets.get_adsets_by_ids(adset_ids, fields, date_format)


@mcp.tool()
async def facebook_get_adsets_by_adaccount(
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
) -> str:
    """Retrieves ad sets from a specific Facebook ad account.

    Args:
        fields (Optional[List[str]]): A list of specific fields to retrieve.
        filtering (Optional[List[dict]]): Filter objects.
        limit (Optional[int]): Maximum number of ad sets to return per page.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        date_preset (Optional[str]): Predefined relative date range.
        time_range (Optional[Dict[str, str]]): Custom time range.
        updated_since (Optional[int]): Return ad sets updated since this Unix timestamp.
        effective_status (Optional[List[str]]): Filter by effective status.
        date_format (Optional[str]): Format for date responses.

    Returns:
        str: JSON string containing the requested ad sets or error message.
    """
    return await adsets.get_adsets_by_adaccount(
        fields, filtering, limit, after, before, date_preset,
        time_range, updated_since, effective_status, date_format
    )


@mcp.tool()
async def facebook_get_adsets_by_campaign(
    campaign_id: str,
    fields: Optional[List[str]] = None,
    filtering: Optional[List[dict]] = None,
    limit: Optional[int] = 25,
    after: Optional[str] = None,
    before: Optional[str] = None,
    effective_status: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> str:
    """Retrieves ad sets from a specific Facebook campaign.

    Args:
        campaign_id (str): The ID of the campaign to retrieve ad sets from.
        fields (Optional[List[str]]): A list of specific fields to retrieve.
        filtering (Optional[List[dict]]): Filter objects.
        limit (Optional[int]): Maximum number of ad sets to return per page.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        effective_status (Optional[List[str]]): Filter by effective status.
        date_format (Optional[str]): Format for date responses.

    Returns:
        str: JSON string containing the requested ad sets or error message.
    """
    return await adsets.get_adsets_by_campaign(
        campaign_id, fields, filtering, limit, after, before,
        effective_status, date_format
    )


# ==============================================================================
# AD AND CREATIVE TOOLS (10 tools)
# ==============================================================================

@mcp.tool()
async def facebook_create_catalog_creative(
    name: str,
    object_story_spec_link_data_message: str,
    product_set_id: Optional[str] = None,
    adv_image_template: Optional[str] = None,
    adv_text_optimizations: Optional[bool] = None,
    adv_image_crop: Optional[bool] = None,
    adv_video_crop: Optional[bool] = None,
    adv_composite_media: Optional[bool] = None,
    adv_catalog_feed_spec: Optional[Dict[str, Any]] = None,
    call_to_action_type: Optional[str] = None,
    link: Optional[str] = None
) -> str:
    """Create a catalog-based ad creative for Dynamic Product Ads (DPA) with Advantage+ features.

    Args:
        name (str): Creative name for identification
        object_story_spec_link_data_message (str): The main ad text/message
        product_set_id (str): Product set ID from your catalog.
        adv_image_template (str): Advantage+ Image Template ID.
        adv_text_optimizations (bool): Enable Advantage+ Text Optimizations.
        adv_image_crop (bool): Enable Advantage+ Image Cropping.
        adv_video_crop (bool): Enable Advantage+ Video Cropping.
        adv_composite_media (bool): Enable Advantage+ Composite Media.
        adv_catalog_feed_spec (Dict): Advanced catalog feed specification.
        call_to_action_type (str): CTA button type.
        link (str): Destination URL.

    Returns:
        str: JSON string containing the created creative details or error message.
    """
    return await ads.create_catalog_creative(
        name, object_story_spec_link_data_message, product_set_id,
        adv_image_template, adv_text_optimizations,
        adv_image_crop, adv_video_crop, adv_composite_media,
        adv_catalog_feed_spec, call_to_action_type, link
    )


@mcp.tool()
async def facebook_create_ad_with_catalog_creative(
    adset_id: str,
    creative_id: str,
    name: str,
    status: str = "PAUSED"
) -> str:
    """Create a new ad using an existing catalog creative.

    Args:
        adset_id (str): The Ad Set ID where the ad will be created
        creative_id (str): The Creative ID to use for the ad
        name (str): Ad name for identification
        status (str): Initial ad status (default: PAUSED). Options: ACTIVE, PAUSED

    Returns:
        str: JSON string containing the created ad details or error message.
    """
    return await ads.create_ad_with_catalog_creative(
        adset_id, creative_id, name, status
    )


@mcp.tool()
async def facebook_fetch_product_sets(
    fields: Optional[List[str]] = None,
    limit: Optional[int] = 25
) -> str:
    """Fetch product sets from a Meta product catalog.

    Args:
        fields (List[str]): Fields to retrieve. Default: ['id', 'name', 'product_count', 'filter']
        limit (int): Maximum number of product sets to return. Default: 25.

    Returns:
        str: JSON string containing product sets or error message.
    """
    return await ads.fetch_product_sets(fields, limit)


@mcp.tool()
async def facebook_edit_ad(
    ad_id: str,
    name: Optional[str] = None,
    status: Optional[str] = None,
    creative_id: Optional[str] = None,
    adset_id: Optional[str] = None
) -> str:
    """Edit an existing ad's properties.

    Args:
        ad_id (str): The Ad ID to edit
        name (str): New ad name. Optional.
        status (str): New status. Options: ACTIVE, PAUSED, ARCHIVED, DELETED. Optional.
        creative_id (str): New creative ID to use. Optional.
        adset_id (str): Move ad to a different ad set. Optional.

    Returns:
        str: JSON string containing update result or error message.
    """
    return await ads.edit_ad(ad_id, name, status, creative_id, adset_id)


@mcp.tool()
async def facebook_bulk_update_status(
    ad_ids: List[str],
    status: str
) -> str:
    """Bulk update the status of multiple ads.

    Args:
        ad_ids (List[str]): List of Ad IDs to update
        status (str): New status to set. Options: ACTIVE, PAUSED, ARCHIVED, DELETED

    Returns:
        str: JSON string containing results for each ad.
    """
    return await ads.bulk_update_status(ad_ids, status)


@mcp.tool()
async def facebook_get_ad_by_id(
    ad_id: str,
    fields: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> str:
    """Retrieves detailed information about a specific Facebook ad by its ID.

    Args:
        ad_id (str): The ID of the ad to retrieve information for.
        fields (Optional[List[str]]): A list of specific fields to retrieve.
        date_format (Optional[str]): Format for date responses.

    Returns:
        str: JSON string containing the requested ad information or error message.
    """
    return await ads.get_ad_by_id(ad_id, fields, date_format)


@mcp.tool()
async def facebook_get_ads_by_adaccount(
    fields: Optional[List[str]] = None,
    filtering: Optional[List[dict]] = None,
    limit: Optional[int] = 25,
    after: Optional[str] = None,
    before: Optional[str] = None,
    effective_status: Optional[List[str]] = None,
    updated_since: Optional[int] = None,
    date_format: Optional[str] = None
) -> str:
    """Retrieves ads from a specific Facebook ad account.

    Args:
        fields (Optional[List[str]]): A list of specific fields to retrieve.
        filtering (Optional[List[dict]]): Filter objects.
        limit (Optional[int]): Maximum number of ads to return per page.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        effective_status (Optional[List[str]]): Filter by effective status.
        updated_since (Optional[int]): Return ads updated since this Unix timestamp.
        date_format (Optional[str]): Format for date responses.

    Returns:
        str: JSON string containing the requested ads or error message.
    """
    return await ads.get_ads_by_adaccount(
        fields, filtering, limit, after, before,
        effective_status, updated_since, date_format
    )


@mcp.tool()
async def facebook_get_ads_by_campaign(
    campaign_id: str,
    fields: Optional[List[str]] = None,
    filtering: Optional[List[dict]] = None,
    limit: Optional[int] = 25,
    after: Optional[str] = None,
    before: Optional[str] = None,
    effective_status: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> str:
    """Retrieves ads from a specific Facebook campaign.

    Args:
        campaign_id (str): The ID of the campaign to retrieve ads from.
        fields (Optional[List[str]]): A list of specific fields to retrieve.
        filtering (Optional[List[dict]]): Filter objects.
        limit (Optional[int]): Maximum number of ads to return per page.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        effective_status (Optional[List[str]]): Filter by effective status.
        date_format (Optional[str]): Format for date responses.

    Returns:
        str: JSON string containing the requested ads or error message.
    """
    return await ads.get_ads_by_campaign(
        campaign_id, fields, filtering, limit, after, before,
        effective_status, date_format
    )


@mcp.tool()
async def facebook_get_ads_by_adset(
    adset_id: str,
    fields: Optional[List[str]] = None,
    filtering: Optional[List[dict]] = None,
    limit: Optional[int] = 25,
    after: Optional[str] = None,
    before: Optional[str] = None,
    effective_status: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> str:
    """Retrieves ads from a specific Facebook ad set.

    Args:
        adset_id (str): The ID of the ad set to retrieve ads from.
        fields (Optional[List[str]]): A list of specific fields to retrieve.
        filtering (Optional[List[dict]]): Filter objects.
        limit (Optional[int]): Maximum number of ads to return per page.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        effective_status (Optional[List[str]]): Filter by effective status.
        date_format (Optional[str]): Format for date responses.

    Returns:
        str: JSON string containing the requested ads or error message.
    """
    return await ads.get_ads_by_adset(
        adset_id, fields, filtering, limit, after, before,
        effective_status, date_format
    )


@mcp.tool()
async def facebook_get_ad_creative_by_id(
    creative_id: str,
    fields: Optional[List[str]] = None,
    thumbnail_width: Optional[int] = None,
    thumbnail_height: Optional[int] = None
) -> str:
    """Retrieves detailed information about a specific Facebook ad creative by its ID.

    Args:
        creative_id (str): The ID of the creative to retrieve information for.
        fields (Optional[List[str]]): A list of specific fields to retrieve.
        thumbnail_width (Optional[int]): Width for thumbnail image.
        thumbnail_height (Optional[int]): Height for thumbnail image.

    Returns:
        str: JSON string containing the requested creative information or error message.
    """
    return await ads.get_ad_creative_by_id(
        creative_id, fields, thumbnail_width, thumbnail_height
    )


# ==============================================================================
# TARGETING AND UTILITY TOOLS (3 tools)
# ==============================================================================

@mcp.tool()
async def facebook_search_ad_interests(
    query: str,
    limit: Optional[int] = 25,
    locale: str = "pt_BR"
) -> str:
    """Search for Facebook ad interests by keyword.

    Args:
        query (str): Search term for interests (e.g., "futebol", "moda", "tecnologia")
        limit (int): Maximum number of results to return. Default: 25.
        locale (str): Locale for search results. Default: "pt_BR" (Brazilian Portuguese).

    Returns:
        str: JSON string containing matching interests with their IDs, names, and metadata.
    """
    return await meta_utils.search_ad_interests(query, limit, locale)


@mcp.tool()
async def facebook_get_region_key_for_adsets(
    region_name: str,
    country_code: str = "BR"
) -> str:
    """Get the region key for Brazilian states or other regions to use in ad set targeting.

    Args:
        region_name (str): Name of the region/state (e.g., "São Paulo", "Rio de Janeiro")
        country_code (str): ISO country code. Default: "BR" (Brazil)

    Returns:
        str: JSON string containing the region key and metadata, or error message.
    """
    return await meta_utils.get_region_key_for_adsets(region_name, country_code)


@mcp.tool()
async def facebook_list_pixels(
    fields: Optional[List[str]] = None,
    limit: Optional[int] = 25
) -> str:
    """List all Meta Pixels associated with an ad account.

    Args:
        fields (Optional[List[str]]): Fields to retrieve.
        limit (Optional[int]): Maximum number of pixels to return. Default: 25.

    Returns:
        str: JSON string containing pixel information or error message.
    """
    return await meta_utils.list_pixels(fields, limit)


# ==============================================================================
# SMART QUERY TOOLS (1 tool)
# ==============================================================================

@mcp.tool()
async def facebook_fetch_objects_by_name(
    object_names: List[str],
    include_insights: bool = True,
    date_preset: Optional[str] = "last_30d",
    insights_fields: Optional[List[str]] = None
) -> str:
    """Unified search for campaigns and ad sets by name with automatic cascading fallback.

    This tool automatically tries to find objects by name using exact matching:
    1. First searches for campaigns with the given names
    2. For names not found as campaigns, searches for ad sets
    3. Returns combined results with 'object_type' field identifying each object

    Each returned object includes:
    - 'object_type': Either "campaign" or "adset"
    - 'requested_name': The name you searched for
    - 'matched_name': The actual name found (same as requested for exact matches)
    - All standard fields (id, name, status, budget, etc.)
    - Performance insights (if include_insights=True)

    Args:
        object_names (List[str]): List of object names to search for using exact name matching.
            Example: ["Summer Sale Campaign", "Holiday Promo", "Q4 Ads"]
        include_insights (bool): If True, includes performance insights for each object. Default: True
        date_preset (Optional[str]): Date preset for insights. Default: "last_30d"
            Options: today, yesterday, last_7d, last_14d, last_30d, last_90d, lifetime
        insights_fields (Optional[List[str]]): Specific metrics to retrieve. Default:
            ['impressions', 'clicks', 'spend', 'reach', 'cpc', 'cpm', 'ctr', 'frequency']

    Returns:
        str: JSON string with structure:
            - 'data': List of found objects, each with 'object_type' field
            - 'summary': Contains found_as_campaigns, found_as_adsets, not_found lists,
              plus counts and statistics

    Example:
        Input: ["Summer Campaign", "Fall Targeting"]
        Output includes:
        - "Summer Campaign" with object_type="campaign" (if found as campaign)
        - "Fall Targeting" with object_type="adset" (if not found as campaign but exists as ad set)
    """
    return await queries.fetch_objects_by_name(
        object_names, include_insights, date_preset, insights_fields
    )


# ==============================================================================
# INSIGHTS TOOLS (5 tools)
# ==============================================================================

@mcp.tool()
async def facebook_get_adaccount_insights(
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

    Args:
        fields (Optional[List[str]]): List of specific metrics to retrieve.
        date_preset (str): Predefined relative time range. Default: 'last_30d'.
        time_range (Optional[Dict[str, str]]): Specific time range.
        time_ranges (Optional[List[Dict[str, str]]]): Array of time ranges.
        time_increment (str): Time breakdown granularity. Default: 'all_days'.
        level (str): Aggregation level. Default: 'account'.
        action_attribution_windows (Optional[List[str]]): Attribution windows.
        action_breakdowns (Optional[List[str]]): Action segments.
        action_report_time (Optional[str]): Action counting time.
        breakdowns (Optional[List[str]]): Result segments.
        default_summary (bool): Include summary row. Default: False.
        use_account_attribution_setting (bool): Use account attribution. Default: False.
        use_unified_attribution_setting (bool): Use unified attribution. Default: True.
        filtering (Optional[List[dict]]): Filter objects.
        sort (Optional[str]): Sort specification.
        limit (Optional[int]): Maximum results per page.
        after (Optional[str]): Pagination cursor for next page.
        before (Optional[str]): Pagination cursor for previous page.
        offset (Optional[int]): Result offset.
        since (Optional[str]): Start timestamp.
        until (Optional[str]): End timestamp.
        locale (Optional[str]): Locale for text responses.

    Returns:
        Dict: Dictionary containing requested ad account insights.
    """
    return await insights.get_adaccount_insights(
        fields, date_preset, time_range, time_ranges,
        time_increment, level, action_attribution_windows,
        action_breakdowns, action_report_time, breakdowns,
        default_summary, use_account_attribution_setting,
        use_unified_attribution_setting, filtering, sort,
        limit, after, before, offset, since, until, locale
    )


@mcp.tool()
async def facebook_get_campaign_insights(
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

    Args:
        campaign_id (str): The ID of the target campaign.
        fields (Optional[List[str]]): List of specific metrics to retrieve.
        date_preset (str): Predefined relative time range. Default: 'last_30d'.
        time_range (Optional[Dict[str, str]]): Specific time range.
        time_ranges (Optional[List[Dict[str, str]]]): Array of time ranges.
        time_increment (str): Time breakdown granularity. Default: 'all_days'.
        action_attribution_windows (Optional[List[str]]): Attribution windows.
        action_breakdowns (Optional[List[str]]): Action segments.
        action_report_time (Optional[str]): Action counting time.
        breakdowns (Optional[List[str]]): Result segments.
        default_summary (bool): Include summary row. Default: False.
        use_account_attribution_setting (bool): Use account attribution. Default: False.
        use_unified_attribution_setting (bool): Use unified attribution. Default: True.
        level (Optional[str]): Aggregation level. Default: 'campaign'.
        filtering (Optional[List[dict]]): Filter objects.
        sort (Optional[str]): Sort specification.
        limit (Optional[int]): Maximum results per page.
        after (Optional[str]): Pagination cursor for next page.
        before (Optional[str]): Pagination cursor for previous page.
        offset (Optional[int]): Result offset.
        since (Optional[str]): Start timestamp.
        until (Optional[str]): End timestamp.
        locale (Optional[str]): Locale for text responses.

    Returns:
        Dict: Dictionary containing requested campaign insights.
    """
    return await insights.get_campaign_insights(
        campaign_id, fields, date_preset, time_range, time_ranges,
        time_increment, action_attribution_windows, action_breakdowns,
        action_report_time, breakdowns, default_summary,
        use_account_attribution_setting, use_unified_attribution_setting,
        level, filtering, sort, limit, after, before, offset,
        since, until, locale
    )


@mcp.tool()
async def facebook_get_adset_insights(
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

    Args:
        adset_id (str): The ID of the target ad set.
        fields (Optional[List[str]]): List of specific metrics to retrieve.
        date_preset (str): Predefined relative time range. Default: 'last_30d'.
        time_range (Optional[Dict[str, str]]): Specific time range.
        time_ranges (Optional[List[Dict[str, str]]]): Array of time ranges.
        time_increment (str): Time breakdown granularity. Default: 'all_days'.
        action_attribution_windows (Optional[List[str]]): Attribution windows.
        action_breakdowns (Optional[List[str]]): Action segments.
        action_report_time (Optional[str]): Action counting time.
        breakdowns (Optional[List[str]]): Result segments.
        default_summary (bool): Include summary row. Default: False.
        use_account_attribution_setting (bool): Use account attribution. Default: False.
        use_unified_attribution_setting (bool): Use unified attribution. Default: True.
        level (Optional[str]): Aggregation level. Default: 'adset'.
        filtering (Optional[List[dict]]): Filter objects.
        sort (Optional[str]): Sort specification.
        limit (Optional[int]): Maximum results per page.
        after (Optional[str]): Pagination cursor for next page.
        before (Optional[str]): Pagination cursor for previous page.
        offset (Optional[int]): Result offset.
        since (Optional[str]): Start timestamp.
        until (Optional[str]): End timestamp.
        locale (Optional[str]): Locale for text responses.

    Returns:
        Dict: Dictionary containing requested ad set insights.
    """
    return await insights.get_adset_insights(
        adset_id, fields, date_preset, time_range, time_ranges,
        time_increment, action_attribution_windows, action_breakdowns,
        action_report_time, breakdowns, default_summary,
        use_account_attribution_setting, use_unified_attribution_setting,
        level, filtering, sort, limit, after, before, offset,
        since, until, locale
    )


@mcp.tool()
async def facebook_get_ad_insights(
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

    Args:
        ad_id (str): The ID of the target ad.
        fields (Optional[List[str]]): List of specific metrics to retrieve.
        date_preset (str): Predefined relative time range. Default: 'last_30d'.
        time_range (Optional[Dict[str, str]]): Specific time range.
        time_ranges (Optional[List[Dict[str, str]]]): Array of time ranges.
        time_increment (str): Time breakdown granularity. Default: 'all_days'.
        action_attribution_windows (Optional[List[str]]): Attribution windows.
        action_breakdowns (Optional[List[str]]): Action segments.
        action_report_time (Optional[str]): Action counting time.
        breakdowns (Optional[List[str]]): Result segments.
        default_summary (bool): Include summary row. Default: False.
        use_account_attribution_setting (bool): Use account attribution. Default: False.
        use_unified_attribution_setting (bool): Use unified attribution. Default: True.
        level (Optional[str]): Aggregation level. Default: 'ad'.
        filtering (Optional[List[dict]]): Filter objects.
        sort (Optional[str]): Sort specification.
        limit (Optional[int]): Maximum results per page.
        after (Optional[str]): Pagination cursor for next page.
        before (Optional[str]): Pagination cursor for previous page.
        offset (Optional[int]): Result offset.
        since (Optional[str]): Start timestamp.
        until (Optional[str]): End timestamp.
        locale (Optional[str]): Locale for text responses.

    Returns:
        Dict: Dictionary containing requested ad insights.
    """
    return await insights.get_ad_insights(
        ad_id, fields, date_preset, time_range, time_ranges,
        time_increment, action_attribution_windows, action_breakdowns,
        action_report_time, breakdowns, default_summary,
        use_account_attribution_setting, use_unified_attribution_setting,
        level, filtering, sort, limit, after, before, offset,
        since, until, locale
    )


@mcp.tool()
async def facebook_fetch_pagination_url(url: str) -> Dict:
    """Fetch data from a Facebook Graph API pagination URL.

    Args:
        url: The complete pagination URL from response['paging']['next'] or response['paging']['previous'].

    Returns:
        The dictionary containing the next/previous page of results.
    """
    return await insights.fetch_pagination_url(url)


# ==============================================================================
# S3 INTEGRATION TOOL (1 tool)
# ==============================================================================

@mcp.tool()
async def facebook_create_ad_with_media_creative_from_s3_folder_link(
    s3_folder_url: str,
    adset_id: str,
    ad_name: str,
    creative_name: str,
    message: str,
    link: str,
    call_to_action_type: str = "LEARN_MORE",
    creative_type: str = "auto",
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_region: Optional[str] = None,
    status: str = "PAUSED"
) -> str:
    """Create a Facebook ad with media creative from an S3 folder.

    This function:
    1. Lists all media files in the S3 folder
    2. Downloads them to temporary storage
    3. Uploads them to Facebook
    4. Creates an appropriate creative (single image, video, or carousel)
    5. Creates an ad with the creative

    Args:
        s3_folder_url (str): S3 folder URL containing media files
        adset_id (str): Ad Set ID where the ad will be created
        ad_name (str): Name for the ad
        creative_name (str): Name for the creative
        message (str): Ad text/message
        link (str): Destination URL
        call_to_action_type (str): CTA button type. Default: "LEARN_MORE"
        creative_type (str): Type of creative. Options: "auto", "single_image", "carousel", "video". Default: "auto"
        aws_access_key_id (str): AWS Access Key ID.
        aws_secret_access_key (str): AWS Secret Access Key.
        aws_region (str): AWS region.
        status (str): Initial ad status. Default: "PAUSED"

    Returns:
        str: JSON string containing the created ad and creative details or error message.
    """
    return await s3_integration.create_ad_with_media_creative_from_s3_folder_link(
        s3_folder_url, adset_id, ad_name, creative_name, message, link,
        call_to_action_type, creative_type,
        aws_access_key_id, aws_secret_access_key,
        aws_region, status
    )


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main():
    """Main entry point for the Facebook Ads MCP Server.

    This function is called when the server is started via the installed
    command-line script (facebook-ads-mcp-server).
    """
    import logging

    # Configure logging to stderr (stdout must be reserved for JSON-RPC)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting Facebook Ads MCP Server...")
        # Configuration is already initialized at module import time
        # via init_config_from_args() call at the top of this module
        mcp.run()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
