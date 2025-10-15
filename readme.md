# Facebook Ads MCP Server

[![Trust Score](https://archestra.ai/mcp-catalog/api/badge/quality/gomarble-ai/facebook-ads-mcp-server)](https://archestra.ai/mcp-catalog/gomarble-ai__facebook-ads-mcp-server)
[![smithery badge](https://smithery.ai/badge/@gomarble-ai/facebook-ads-mcp-server)](https://smithery.ai/server/@gomarble-ai/facebook-ads-mcp-server)
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/gomarble-ai/facebook-ads-mcp-server)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A comprehensive Model Context Protocol (MCP) server providing **full CRUD operations** for Facebook/Meta Ads management through the Graph API v22.0.

<video controls width="1920" height="512" src="https://github.com/user-attachments/assets/c4a76dcf-cf5d-4a1d-b976-08165e880fe4">Your browser does not support the video tag.</video>

## 🚀 What's New in v2.0.0

- **32 Tools** (up from 21) with `facebook_` prefix for namespace safety
- **Full CRUD Operations**: Create, Read, Update, Delete campaigns, ad sets, and ads
- **Campaign Budget Optimization (CBO)** and **Ad Set Budget Optimization (ABO)**
- **Dynamic Product Ads (DPA)** with Advantage+ Creative features
- **Advanced Targeting**: Geo-locations, interests, demographics, Advantage+ Audience
- **S3 Integration**: Auto-download media from S3 and create ads
- **Smart Queries**: Search by name with integrated performance insights
- **Async Architecture**: Built with httpx for efficient API calls
- **Modular Design**: Clean separation across 11 modules

## Easy One-Click Setup

For a simpler setup experience, we offer ready-to-use installers:

👉 **Download installer -** [https://gomarble.ai/mcp](https://gomarble.ai/mcp)

## Join our community for help and updates

👉 **Slack Community -** [AI in Ads](https://join.slack.com/t/ai-in-ads/shared_invite/zt-36hntbyf8-FSFixmwLb9mtEzVZhsToJQ)

## Try Google ads mcp server also

👉 **Google Ads MCP -** [Google Ads MCP](https://github.com/gomarble-ai/google-ads-mcp-server)

---

## 📋 Table of Contents

- [Setup](#setup)
- [32 Available Tools](#32-available-tools)
  - [Campaign Tools (6)](#campaign-tools-6)
  - [Ad Set Tools (6)](#ad-set-tools-6)
  - [Ad & Creative Tools (10)](#ad--creative-tools-10)
  - [Targeting & Utility Tools (3)](#targeting--utility-tools-3)
  - [Smart Query Tools (1)](#smart-query-tools-1)
  - [Insights Tools (5)](#insights-tools-5)
  - [S3 Integration (1)](#s3-integration-1)
- [Usage Examples](#usage-examples)
- [Targeting Guide](#targeting-guide)
- [Architecture](#architecture)

---

## Setup

### Prerequisites

- Python 3.10+
- Facebook/Meta Ads account
- Facebook User Access Token with appropriate permissions

### Installation

1. **(Optional but Recommended) Create and Activate a Virtual Environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

2. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

3. **Obtain Meta Access Token:**
Secure a Meta User Access Token with the necessary permissions:
- `ads_read` (for reading ad data)
- `ads_management` (for creating/updating ads)
- `business_management` (for accessing Business Manager)

Follow [this guide](https://elfsight.com/blog/how-to-get-facebook-access-token/) or the [Meta Developer portal](https://developers.facebook.com/).

### Usage with MCP Clients (Claude Desktop, Cursor)

Add this configuration to your MCP client settings:

```json
{
  "mcpServers": {
    "fb-ads-mcp-server": {
      "command": "python",
      "args": [
        "/path/to/your/fb-ads-mcp-server/server.py",
        "--fb-token",
        "YOUR_META_ACCESS_TOKEN",
        "--pixel-id",
        "YOUR_PIXEL_ID",
        "--page-id",
        "YOUR_PAGE_ID",
        "--instagram-user-id",
        "YOUR_INSTAGRAM_ID",
        "--catalog-id",
        "YOUR_CATALOG_ID",
        "--website-domain",
        "yourdomain.com"
      ]
    }
  }
}
```

**Note:** Only `--fb-token` is required. Other parameters are optional and can be set per ad set/creative.

Restart the MCP Client app after updating the configuration.

### Debugging the Server

Execute `server.py` directly:

```bash
python server.py --fb-token YOUR_META_ACCESS_TOKEN
```

---

## 32 Available Tools

All tools are prefixed with `facebook_` to prevent namespace collisions when used alongside other MCP servers (e.g., Google Ads).

### Campaign Tools (6)

| Tool | Description |
|------|-------------|
| `facebook_create_cbo_campaign` | Create a Campaign Budget Optimization campaign with budget managed at campaign level |
| `facebook_create_abo_campaign` | Create an Ad Set Budget Optimization campaign with budget managed at ad set level |
| `facebook_update_campaign_budget` | Update the daily or lifetime budget of an existing campaign |
| `facebook_deactivate_or_activate_campaign` | Change campaign status (ACTIVE, PAUSED, ARCHIVED, DELETED) |
| `facebook_get_campaign_by_id` | Retrieve detailed information about a specific campaign |
| `facebook_get_campaigns_by_adaccount` | List all campaigns in an ad account with filtering and pagination |

### Ad Set Tools (6)

| Tool | Description |
|------|-------------|
| `facebook_create_adset` | Create a new ad set with comprehensive targeting (geo, interests, Advantage+ Audience) |
| `facebook_update_adset` | Update an existing ad set's properties including targeting, budget, and bid strategy |
| `facebook_get_adset_by_id` | Retrieve detailed information about a specific ad set |
| `facebook_get_adsets_by_ids` | Retrieve information about multiple ad sets in batch |
| `facebook_get_adsets_by_adaccount` | List all ad sets in an ad account with filtering and pagination |
| `facebook_get_adsets_by_campaign` | List all ad sets within a specific campaign |

### Ad & Creative Tools (10)

| Tool | Description |
|------|-------------|
| `facebook_create_catalog_creative` | Create a catalog-based creative for Dynamic Product Ads with Advantage+ features |
| `facebook_create_ad_with_catalog_creative` | Create a new ad using an existing catalog creative |
| `facebook_fetch_product_sets` | Retrieve product sets from a Meta product catalog for DPA campaigns |
| `facebook_edit_ad` | Update an existing ad's properties (name, status, creative, ad set) |
| `facebook_bulk_update_status` | Update the status of multiple ads at once |
| `facebook_get_ad_by_id` | Retrieve detailed information about a specific ad |
| `facebook_get_ads_by_adaccount` | List all ads in an ad account with filtering and pagination |
| `facebook_get_ads_by_campaign` | List all ads within a specific campaign |
| `facebook_get_ads_by_adset` | List all ads within a specific ad set |
| `facebook_get_ad_creative_by_id` | Retrieve detailed information about a specific ad creative |

### Targeting & Utility Tools (3)

| Tool | Description |
|------|-------------|
| `facebook_search_ad_interests` | Search for Facebook ad targeting interests by keyword with pt_BR locale support |
| `facebook_get_region_key_for_adsets` | Get region keys for geo-targeting (especially Brazilian states) |
| `facebook_list_pixels` | List all Meta Pixels associated with an ad account |

### Smart Query Tools (1)

| Tool | Description |
|------|-------------|
| `facebook_fetch_objects_by_name` | Universal search for campaigns, ad sets, and ads by name with insights |

### Insights Tools (5)

| Tool | Description |
|------|-------------|
| `facebook_get_adaccount_insights` | Retrieve performance insights and analytics for an ad account |
| `facebook_get_campaign_insights` | Retrieve performance insights and analytics for a campaign |
| `facebook_get_adset_insights` | Retrieve performance insights and analytics for an ad set |
| `facebook_get_ad_insights` | Retrieve performance insights and analytics for an ad |
| `facebook_fetch_pagination_url` | Fetch the next or previous page of insights data |

### S3 Integration (1)

| Tool | Description |
|------|-------------|
| `facebook_create_ad_with_media_creative_from_s3_folder_link` | Create an ad with media from S3 (auto-detects image/video/carousel) |

---

## Usage Examples

### Example 1: Create a Complete Campaign Flow

```python
# 1. Create an ABO campaign
campaign = await facebook_create_abo_campaign(
    name="Summer Sale 2024",
    objective="OUTCOME_SALES",
    status="PAUSED",
    act_id="act_123456789"
)

# 2. Create an ad set with targeting
adset = await facebook_create_adset(
    campaign_id="campaign_id_from_step_1",
    name="Brazil - 25-34 - Fashion Interests",
    optimization_goal="OFFSITE_CONVERSIONS",
    billing_event="IMPRESSIONS",
    custom_event_type="PURCHASE",
    act_id="act_123456789",
    daily_budget="5000",  # $50.00 in cents
    targeting={
        "geo_locations": {
            "countries": ["BR"],
            "regions": [{"key": "3462"}]  # São Paulo
        },
        "age_min": 25,
        "age_max": 34,
        "interests": [{"id": "6003139266461"}],  # Fashion
        "targeting_automation": {
            "advantage_audience": 1
        }
    },
    promoted_object={
        "pixel_id": "your_pixel_id",
        "custom_event_type": "PURCHASE"
    }
)

# 3. Create a catalog creative
creative = await facebook_create_catalog_creative(
    name="DPA Creative - Summer",
    object_story_spec_link_data_message="Check out our summer collection!",
    product_set_id="product_set_id",
    act_id="act_123456789",
    adv_text_optimizations=True,
    adv_image_crop=True,
    call_to_action_type="SHOP_NOW"
)

# 4. Create the ad
ad = await facebook_create_ad_with_catalog_creative(
    adset_id="adset_id_from_step_2",
    creative_id="creative_id_from_step_3",
    name="Summer Sale Ad",
    status="PAUSED",
    act_id="act_123456789"
)
```

### Example 2: Search Interests for Targeting

```python
# Search for Brazilian Portuguese interests
interests = await facebook_search_ad_interests(
    query="futebol",
    limit=10,
    locale="pt_BR"
)
# Returns interest IDs with audience sizes for targeting
```

### Example 3: Smart Query with Insights

```python
# Universal search for objects by name with last 7 days performance
results = await facebook_fetch_objects_by_name(
    name_query="summer",
    object_types=["campaigns", "adsets"],  # Optional, defaults to all types
    include_insights=True,
    date_preset="last_7d"
)
```

### Example 4: S3 Media Integration

```python
# Create ad from S3 folder (auto-detects carousel from multiple images)
result = await facebook_create_ad_with_media_creative_from_s3_folder_link(
    s3_folder_url="s3://my-bucket/campaigns/summer-2024/",
    adset_id="adset_123",
    ad_name="Summer Collection Ad",
    creative_name="Summer Carousel",
    message="Check out our latest summer styles!",
    link="https://example.com/summer",
    act_id="act_123456789",
    call_to_action_type="SHOP_NOW"
)
```

---

## Targeting Guide

### Basic Targeting Structure

```python
targeting = {
    # Geographic
    "geo_locations": {
        "countries": ["BR"],
        "regions": [{"key": "3462"}],  # São Paulo
        "cities": [{"key": "123", "radius": 10, "distance_unit": "kilometer"}]
    },

    # Demographics
    "age_min": 25,
    "age_max": 45,
    "genders": [1],  # 1=Male, 2=Female

    # Interests
    "interests": [
        {"id": "6003139266461"}  # Use facebook_search_ad_interests
    ],

    # Advantage+ Audience (AI-powered expansion)
    "targeting_automation": {
        "advantage_audience": 1  # 0=off, 1=on
    }
}
```

### Common Brazilian State Keys

| State | Key |
|-------|-----|
| São Paulo | 3462 |
| Rio de Janeiro | 3444 |
| Minas Gerais | 3445 |
| Rio Grande do Sul | 3463 |
| Paraná | 3450 |
| Bahia | 3471 |

Use `facebook_get_region_key_for_adsets` to find others.

### Objective → Optimization Goal Mapping

| Objective | Common Optimization Goals |
|-----------|---------------------------|
| OUTCOME_SALES | OFFSITE_CONVERSIONS, VALUE |
| OUTCOME_TRAFFIC | LINK_CLICKS, LANDING_PAGE_VIEWS |
| OUTCOME_LEADS | OFFSITE_CONVERSIONS, LEAD_GENERATION |
| OUTCOME_ENGAGEMENT | POST_ENGAGEMENT, PAGE_LIKES |
| OUTCOME_AWARENESS | REACH, IMPRESSIONS |

---

## Architecture

### Modular Structure

```
facebook-ads-mcp-server/
├── fb_ads/
│   ├── __init__.py           # Package initialization
│   ├── api.py                # Core API helpers
│   ├── campaigns.py          # 6 campaign tools
│   ├── adsets.py             # 6 ad set tools
│   ├── ads.py                # 10 ad/creative tools
│   ├── meta_utils.py         # 3 targeting utilities
│   ├── media.py              # Creative helpers
│   ├── s3_integration.py     # S3 media processing
│   ├── queries.py            # 3 smart query tools
│   └── insights.py           # 5 insights tools
├── server.py                 # MCP server (32 tools)
├── requirements.txt
├── manifest.json
└── README.md
```

### Key Features

- **Async/Await**: All API calls use `httpx` for non-blocking I/O
- **Global Configuration**: Command-line args parsed once at startup
- **Tool Prefixing**: All tools prefixed with `facebook_` for namespace safety
- **Error Handling**: Comprehensive error responses with details
- **Type Safety**: Type hints throughout

---

## Installing via Smithery

To install Facebook Ads Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@gomarble-ai/facebook-ads-mcp-server):

```bash
npx -y @smithery/cli install @gomarble-ai/facebook-ads-mcp-server --client claude
```

---

## Dependencies

- [mcp](https://pypi.org/project/mcp/) (>=1.6.0)
- [httpx](https://pypi.org/project/httpx/) (>=0.26.0)
- [requests](https://pypi.org/project/requests/) (>=2.32.3)
- [facebook_business](https://pypi.org/project/facebook-business/) (>=20.0.0)
- [Pillow](https://pypi.org/project/Pillow/) (>=10.0.0)
- [opencv-python](https://pypi.org/project/opencv-python/) (>=4.0.0)
- [boto3](https://pypi.org/project/boto3/) (>=1.34.0)

---

## Changelog

### Version 2.0.0 (Current)
- ✨ Complete rewrite with 32 tools (up from 21)
- ✨ Full CRUD operations for campaigns, ad sets, and ads
- ✨ Async architecture with httpx
- ✨ Modular structure (11 modules)
- ✨ All tools prefixed with `facebook_`
- ✨ DPA and Advantage+ Creative support
- ✨ S3 integration for media
- ✨ Smart queries with insights
- ✨ Brazilian market focus (pt_BR locale, state targeting)

### Version 0.1.0 (Legacy)
- Basic read-only operations
- 21 tools without prefix
- Synchronous architecture

---

## License

This project is licensed under the MIT License.

---

## Support

For issues, questions, or contributions:
- **GitHub Issues**: [Create an issue](https://github.com/gomarble-ai/facebook-ads-mcp-server/issues)
- **Email**: support@gomarble.ai
- **Slack**: [AI in Ads Community](https://join.slack.com/t/ai-in-ads/shared_invite/zt-36hntbyf8-FSFixmwLb9mtEzVZhsToJQ)

---

**Built with ❤️ by [GoMarble AI](https://github.com/gomarble-ai)**
