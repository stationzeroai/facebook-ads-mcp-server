"""
Ad and Creative-related tools for Meta Ads API.

This module provides tools for creating and managing Facebook/Meta ads and creatives,
including catalog-based Dynamic Product Ads (DPA), media creatives, and Advantage+ features.
"""

import json
from typing import List, Optional, Dict, Any, Union
from .api import (
    FB_GRAPH_URL,
    get_access_token,
    get_page_id,
    get_instagram_user_id,
    get_catalog_id,
    _make_graph_api_call,
    _make_graph_api_post,
    _prepare_params
)


async def create_catalog_creative(
    name: str,
    object_story_spec_link_data_message: str,
    product_set_id: Optional[str] = None,
    act_id: Optional[str] = None,
    page_id: Optional[str] = None,
    instagram_user_id: Optional[str] = None,
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

    This function creates a creative that can automatically pull product information from your
    Meta product catalog. It supports various Advantage+ features for AI-powered optimization.

    Args:
        name (str): Creative name for identification
        object_story_spec_link_data_message (str): The main ad text/message
        product_set_id (str): Product set ID from your catalog. Optional if using adv_catalog_feed_spec.
        act_id (str): Ad account ID (with act_ prefix). Required.
        page_id (str): Facebook Page ID. If not provided, uses global config.
        instagram_user_id (str): Instagram User ID for placements. If not provided, uses global config.
        adv_image_template (str): Advantage+ Image Template ID for AI-generated backgrounds.
            Example: "advantage_plus_creative_catalog_immersive_template"
        adv_text_optimizations (bool): Enable Advantage+ Text Optimizations (AI-generated variations)
        adv_image_crop (bool): Enable Advantage+ Image Cropping for optimal placement fit
        adv_video_crop (bool): Enable Advantage+ Video Cropping
        adv_composite_media (bool): Enable Advantage+ Composite Media (combine images/videos)
        adv_catalog_feed_spec (Dict): Advanced catalog feed specification. Structure:
            {
                "product_set_id": "string",
                "filter": {...},
                "automatic_product_tagging": true
            }
        call_to_action_type (str): CTA button type. Options:
            SHOP_NOW, LEARN_MORE, GET_OFFER, BOOK_TRAVEL, SIGN_UP, etc.
        link (str): Destination URL. Optional - can use catalog product URLs.

    Returns:
        str: JSON string containing the created creative details or error message.

    Example:
        ```python
        creative = await create_catalog_creative(
            name="DPA Campaign - Summer Collection",
            object_story_spec_link_data_message="Check out our summer collection!",
            product_set_id="1234567890",
            act_id="act_123456789",
            adv_text_optimizations=True,
            adv_image_crop=True,
            call_to_action_type="SHOP_NOW"
        )
        ```
    """
    if not name:
        return json.dumps({"error": "No creative name provided"}, indent=2)

    if not object_story_spec_link_data_message:
        return json.dumps({"error": "No message provided for the ad creative"}, indent=2)

    if not act_id:
        return json.dumps({"error": "No ad account ID (act_id) provided"}, indent=2)

    # Use provided IDs or fall back to global config
    page_id = page_id or get_page_id()
    instagram_user_id = instagram_user_id or get_instagram_user_id()

    if not page_id:
        return json.dumps({"error": "No page_id provided or configured"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/adcreatives"

    # Build object_story_spec
    object_story_spec = {
        "page_id": page_id
    }

    if instagram_user_id:
        object_story_spec["instagram_actor_id"] = instagram_user_id

    # Build link_data
    link_data = {
        "message": object_story_spec_link_data_message
    }

    if call_to_action_type:
        link_data["call_to_action"] = {
            "type": call_to_action_type
        }
        if link:
            link_data["call_to_action"]["value"] = {"link": link}
    elif link:
        link_data["link"] = link

    object_story_spec["link_data"] = link_data

    base_params = {
        "access_token": access_token,
        "name": name,
        "object_story_spec": json.dumps(object_story_spec)
    }

    # Add product set ID if provided (classic DPA approach)
    if product_set_id:
        base_params["product_set_id"] = product_set_id

    # Build degrees_of_freedom_spec for Advantage+ features
    degrees_of_freedom_spec = {}

    if adv_text_optimizations is not None:
        degrees_of_freedom_spec["creative_features_spec"] = {
            "standard_enhancements": {
                "enroll_status": "OPT_IN" if adv_text_optimizations else "OPT_OUT"
            }
        }

    if adv_image_crop is not None:
        if "creative_features_spec" not in degrees_of_freedom_spec:
            degrees_of_freedom_spec["creative_features_spec"] = {}
        degrees_of_freedom_spec["creative_features_spec"]["image_enhancements"] = {
            "image_crop": {
                "enroll_status": "OPT_IN" if adv_image_crop else "OPT_OUT"
            }
        }

    if adv_video_crop is not None:
        if "creative_features_spec" not in degrees_of_freedom_spec:
            degrees_of_freedom_spec["creative_features_spec"] = {}
        degrees_of_freedom_spec["creative_features_spec"]["video_enhancements"] = {
            "video_crop": {
                "enroll_status": "OPT_IN" if adv_video_crop else "OPT_OUT"
            }
        }

    if adv_composite_media is not None:
        if "creative_features_spec" not in degrees_of_freedom_spec:
            degrees_of_freedom_spec["creative_features_spec"] = {}
        degrees_of_freedom_spec["creative_features_spec"]["composite_media"] = {
            "enroll_status": "OPT_IN" if adv_composite_media else "OPT_OUT"
        }

    if degrees_of_freedom_spec:
        base_params["degrees_of_freedom_spec"] = json.dumps(degrees_of_freedom_spec)

    # Add image template if provided
    if adv_image_template:
        base_params["image_template"] = adv_image_template

    # Add advanced catalog feed spec if provided
    if adv_catalog_feed_spec:
        base_params["catalog_feed_spec"] = json.dumps(adv_catalog_feed_spec)

    try:
        data = await _make_graph_api_post(url, base_params)
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        return json.dumps({
            "error": "Failed to create catalog creative",
            "details": error_msg,
            "params_sent": {k: v for k, v in base_params.items() if 'token' not in k.lower()}
        }, indent=2)


async def create_ad_with_catalog_creative(
    adset_id: str,
    creative_id: str,
    name: str,
    status: str = "PAUSED",
    act_id: Optional[str] = None
) -> str:
    """Create a new ad using an existing catalog creative.

    Args:
        adset_id (str): The Ad Set ID where the ad will be created
        creative_id (str): The Creative ID to use for the ad
        name (str): Ad name for identification
        status (str): Initial ad status (default: PAUSED). Options: ACTIVE, PAUSED
        act_id (str): Ad account ID (with act_ prefix). Required.

    Returns:
        str: JSON string containing the created ad details or error message.
    """
    if not adset_id:
        return json.dumps({"error": "No adset_id provided"}, indent=2)

    if not creative_id:
        return json.dumps({"error": "No creative_id provided"}, indent=2)

    if not name:
        return json.dumps({"error": "No ad name provided"}, indent=2)

    if not act_id:
        return json.dumps({"error": "No ad account ID (act_id) provided"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/ads"

    params = {
        "access_token": access_token,
        "name": name,
        "adset_id": adset_id,
        "creative": json.dumps({"creative_id": creative_id}),
        "status": status
    }

    try:
        data = await _make_graph_api_post(url, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        return json.dumps({
            "error": "Failed to create ad",
            "details": error_msg,
            "params_sent": {k: v for k, v in params.items() if 'token' not in k.lower()}
        }, indent=2)


async def fetch_product_sets(
    catalog_id: Optional[str] = None,
    fields: Optional[List[str]] = None,
    limit: Optional[int] = 25
) -> str:
    """Fetch product sets from a Meta product catalog.

    Args:
        catalog_id (str): Product Catalog ID. If not provided, uses global config.
        fields (List[str]): Fields to retrieve. Default: ['id', 'name', 'product_count', 'filter']
        limit (int): Maximum number of product sets to return. Default: 25.

    Returns:
        str: JSON string containing product sets or error message.
    """
    catalog_id = catalog_id or get_catalog_id()

    if not catalog_id:
        return json.dumps({"error": "No catalog_id provided or configured"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{catalog_id}/product_sets"

    # Default fields if none provided
    if not fields:
        fields = ['id', 'name', 'product_count', 'filter']

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
            "error": "Failed to fetch product sets",
            "details": str(e),
            "catalog_id": catalog_id
        }, indent=2)


async def edit_ad(
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
    if not ad_id:
        return json.dumps({"error": "No ad_id provided"}, indent=2)

    if not any([name, status, creative_id, adset_id]):
        return json.dumps({"error": "No fields to update provided"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{ad_id}"

    params = {"access_token": access_token}

    if name:
        params["name"] = name
    if status:
        valid_statuses = ["ACTIVE", "PAUSED", "ARCHIVED", "DELETED"]
        if status not in valid_statuses:
            return json.dumps({
                "error": f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
            }, indent=2)
        params["status"] = status
    if creative_id:
        params["creative"] = json.dumps({"creative_id": creative_id})
    if adset_id:
        params["adset_id"] = adset_id

    try:
        data = await _make_graph_api_post(url, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to edit ad",
            "details": str(e),
            "ad_id": ad_id
        }, indent=2)


async def bulk_update_status(
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
    if not ad_ids:
        return json.dumps({"error": "No ad_ids provided"}, indent=2)

    if not status:
        return json.dumps({"error": "No status provided"}, indent=2)

    valid_statuses = ["ACTIVE", "PAUSED", "ARCHIVED", "DELETED"]
    if status not in valid_statuses:
        return json.dumps({
            "error": f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
        }, indent=2)

    access_token = get_access_token()
    results = []

    for ad_id in ad_ids:
        url = f"{FB_GRAPH_URL}/{ad_id}"
        params = {
            "access_token": access_token,
            "status": status
        }

        try:
            data = await _make_graph_api_post(url, params)
            results.append({
                "ad_id": ad_id,
                "success": True,
                "result": data
            })
        except Exception as e:
            results.append({
                "ad_id": ad_id,
                "success": False,
                "error": str(e)
            })

    return json.dumps({
        "total": len(ad_ids),
        "results": results
    }, indent=2)


async def get_ad_by_id(
    ad_id: str,
    fields: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> str:
    """Retrieves detailed information about a specific Facebook ad by its ID.

    Args:
        ad_id (str): The ID of the ad to retrieve information for.
        fields (Optional[List[str]]): A list of specific fields to retrieve. If None,
            a default set of fields will be returned. Available fields include:
            - 'id', 'name', 'account_id', 'adset_id', 'campaign_id'
            - 'status', 'configured_status', 'effective_status'
            - 'created_time', 'updated_time'
            - 'creative', 'tracking_specs', 'conversion_specs'
            - And many more (see Facebook Graph API documentation for complete list)
        date_format (Optional[str]): Format for date responses. Options:
            - 'U': Unix timestamp (seconds since epoch)
            - 'Y-m-d H:i:s': MySQL datetime format
            - None: ISO 8601 format (default)

    Returns:
        str: JSON string containing the requested ad information or error message.
    """
    if not ad_id:
        return json.dumps({"error": "No ad_id provided"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{ad_id}"
    params = {'access_token': access_token}

    if fields:
        params['fields'] = ','.join(fields)

    if date_format:
        params['date_format'] = date_format

    try:
        data = await _make_graph_api_call(url, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to get ad",
            "details": str(e),
            "ad_id": ad_id
        }, indent=2)


async def get_ads_by_adaccount(
    act_id: str,
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
        act_id (str): The ID of the ad account to retrieve ads from, prefixed with 'act_'.
        fields (Optional[List[str]]): A list of specific fields to retrieve for each ad.
        filtering (Optional[List[dict]]): Filter objects with 'field', 'operator', and 'value' keys.
        limit (Optional[int]): Maximum number of ads to return per page. Default is 25, max is 100.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        effective_status (Optional[List[str]]): Filter by effective status.
        updated_since (Optional[int]): Return ads updated since this Unix timestamp.
        date_format (Optional[str]): Format for date responses ('U', 'Y-m-d H:i:s', or None).

    Returns:
        str: JSON string containing the requested ads or error message.
    """
    if not act_id:
        return json.dumps({"error": "No ad account ID (act_id) provided"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/ads"
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

    if effective_status:
        params['effective_status'] = json.dumps(effective_status)

    if updated_since:
        params['updated_since'] = updated_since

    if date_format:
        params['date_format'] = date_format

    try:
        data = await _make_graph_api_call(url, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to get ads by ad account",
            "details": str(e),
            "act_id": act_id
        }, indent=2)


async def get_ads_by_campaign(
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
        fields (Optional[List[str]]): A list of specific fields to retrieve for each ad.
        filtering (Optional[List[dict]]): Filter objects with 'field', 'operator', and 'value' keys.
        limit (Optional[int]): Maximum number of ads to return per page. Default is 25, max is 100.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        effective_status (Optional[List[str]]): Filter by effective status.
        date_format (Optional[str]): Format for date responses ('U', 'Y-m-d H:i:s', or None).

    Returns:
        str: JSON string containing the requested ads or error message.
    """
    if not campaign_id:
        return json.dumps({"error": "No campaign_id provided"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{campaign_id}/ads"
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

    if effective_status:
        params['effective_status'] = json.dumps(effective_status)

    if date_format:
        params['date_format'] = date_format

    try:
        data = await _make_graph_api_call(url, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to get ads by campaign",
            "details": str(e),
            "campaign_id": campaign_id
        }, indent=2)


async def get_ads_by_adset(
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
        fields (Optional[List[str]]): A list of specific fields to retrieve for each ad.
        filtering (Optional[List[dict]]): Filter objects with 'field', 'operator', and 'value' keys.
        limit (Optional[int]): Maximum number of ads to return per page. Default is 25, max is 100.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        effective_status (Optional[List[str]]): Filter by effective status.
        date_format (Optional[str]): Format for date responses ('U', 'Y-m-d H:i:s', or None).

    Returns:
        str: JSON string containing the requested ads or error message.
    """
    if not adset_id:
        return json.dumps({"error": "No adset_id provided"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{adset_id}/ads"
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

    if effective_status:
        params['effective_status'] = json.dumps(effective_status)

    if date_format:
        params['date_format'] = date_format

    try:
        data = await _make_graph_api_call(url, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to get ads by ad set",
            "details": str(e),
            "adset_id": adset_id
        }, indent=2)


async def get_ad_creative_by_id(
    creative_id: str,
    fields: Optional[List[str]] = None,
    thumbnail_width: Optional[int] = None,
    thumbnail_height: Optional[int] = None
) -> str:
    """Retrieves detailed information about a specific Facebook ad creative by its ID.

    Args:
        creative_id (str): The ID of the creative to retrieve information for.
        fields (Optional[List[str]]): A list of specific fields to retrieve. Available fields include:
            - 'id', 'name', 'account_id'
            - 'object_story_spec', 'object_type'
            - 'thumbnail_url', 'image_url', 'video_id'
            - 'body', 'title', 'link_url', 'call_to_action_type'
            - 'asset_feed_spec', 'template_url'
            - And many more (see Facebook Graph API documentation for complete list)
        thumbnail_width (Optional[int]): Width for thumbnail image.
        thumbnail_height (Optional[int]): Height for thumbnail image.

    Returns:
        str: JSON string containing the requested creative information or error message.
    """
    if not creative_id:
        return json.dumps({"error": "No creative_id provided"}, indent=2)

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{creative_id}"
    params = {'access_token': access_token}

    if fields:
        params['fields'] = ','.join(fields)

    if thumbnail_width:
        params['thumbnail_width'] = thumbnail_width

    if thumbnail_height:
        params['thumbnail_height'] = thumbnail_height

    try:
        data = await _make_graph_api_call(url, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({
            "error": "Failed to get ad creative",
            "details": str(e),
            "creative_id": creative_id
        }, indent=2)
