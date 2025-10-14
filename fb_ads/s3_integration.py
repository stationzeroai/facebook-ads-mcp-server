"""
S3 integration for Facebook ad creative media processing.

This module provides tools to create Facebook ads using media files stored in AWS S3,
including automatic download, processing, and creative generation.
"""

import json
import os
import tempfile
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
from .api import get_access_token, get_page_id, get_instagram_user_id
from .media import (
    _upload_image_to_facebook,
    _upload_video_to_facebook,
    _extract_video_thumbnail,
    _create_single_image_creative,
    _create_carousel_creative,
    _create_video_creative
)
from .ads import create_ad_with_catalog_creative

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


def _parse_s3_url(s3_url: str) -> tuple:
    """Parse S3 URL to extract bucket and key.

    Args:
        s3_url (str): S3 URL in format s3://bucket-name/path/to/folder/
                      or https://bucket-name.s3.amazonaws.com/path/to/folder/

    Returns:
        tuple: (bucket_name, prefix)

    Raises:
        ValueError: If URL format is invalid
    """
    if s3_url.startswith('s3://'):
        # Format: s3://bucket-name/path/to/folder/
        parsed = urlparse(s3_url)
        bucket = parsed.netloc
        prefix = parsed.path.lstrip('/')
        return bucket, prefix
    elif 's3.amazonaws.com' in s3_url or 's3-' in s3_url:
        # Format: https://bucket-name.s3.amazonaws.com/path/to/folder/
        # or https://s3.region.amazonaws.com/bucket-name/path/to/folder/
        parsed = urlparse(s3_url)
        if '.s3.' in parsed.netloc or '.s3-' in parsed.netloc:
            bucket = parsed.netloc.split('.')[0]
            prefix = parsed.path.lstrip('/')
        else:
            # s3.region.amazonaws.com format
            path_parts = parsed.path.lstrip('/').split('/', 1)
            bucket = path_parts[0]
            prefix = path_parts[1] if len(path_parts) > 1 else ''
        return bucket, prefix
    else:
        raise ValueError(
            "Invalid S3 URL format. Expected s3://bucket/path or "
            "https://bucket.s3.amazonaws.com/path"
        )


def _list_s3_folder_contents(
    bucket: str,
    prefix: str,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_region: Optional[str] = None
) -> List[str]:
    """List all files in an S3 folder.

    Args:
        bucket (str): S3 bucket name
        prefix (str): Folder prefix/path
        aws_access_key_id (str): AWS Access Key ID. Optional if using IAM role.
        aws_secret_access_key (str): AWS Secret Access Key. Optional if using IAM role.
        aws_region (str): AWS region. Default: us-east-1

    Returns:
        List[str]: List of S3 keys (file paths)

    Raises:
        Exception: If boto3 not installed or AWS credentials invalid
    """
    if not BOTO3_AVAILABLE:
        raise ImportError(
            "boto3 is required for S3 integration. "
            "Install it with: pip install boto3"
        )

    # Create S3 client
    session_kwargs = {}
    if aws_access_key_id and aws_secret_access_key:
        session_kwargs['aws_access_key_id'] = aws_access_key_id
        session_kwargs['aws_secret_access_key'] = aws_secret_access_key
    if aws_region:
        session_kwargs['region_name'] = aws_region

    s3_client = boto3.client('s3', **session_kwargs)

    # List objects
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)

        if 'Contents' not in response:
            return []

        # Filter out folders (keys ending with /)
        files = [
            obj['Key'] for obj in response['Contents']
            if not obj['Key'].endswith('/')
        ]

        return files

    except NoCredentialsError:
        raise ValueError(
            "AWS credentials not found. Provide aws_access_key_id and "
            "aws_secret_access_key or configure AWS credentials."
        )
    except ClientError as e:
        raise ValueError(f"Failed to list S3 folder contents: {str(e)}")


def _download_s3_file(
    bucket: str,
    key: str,
    local_path: str,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_region: Optional[str] = None
) -> str:
    """Download a file from S3 to local storage.

    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key
        local_path (str): Local path where to save the file
        aws_access_key_id (str): AWS Access Key ID. Optional if using IAM role.
        aws_secret_access_key (str): AWS Secret Access Key. Optional if using IAM role.
        aws_region (str): AWS region. Default: us-east-1

    Returns:
        str: Path to downloaded file

    Raises:
        Exception: If download fails
    """
    if not BOTO3_AVAILABLE:
        raise ImportError(
            "boto3 is required for S3 integration. "
            "Install it with: pip install boto3"
        )

    # Create S3 client
    session_kwargs = {}
    if aws_access_key_id and aws_secret_access_key:
        session_kwargs['aws_access_key_id'] = aws_access_key_id
        session_kwargs['aws_secret_access_key'] = aws_secret_access_key
    if aws_region:
        session_kwargs['region_name'] = aws_region

    s3_client = boto3.client('s3', **session_kwargs)

    try:
        s3_client.download_file(bucket, key, local_path)
        return local_path
    except ClientError as e:
        raise ValueError(f"Failed to download S3 file {key}: {str(e)}")


async def create_ad_with_media_creative_from_s3_folder_link(
    s3_folder_url: str,
    adset_id: str,
    ad_name: str,
    creative_name: str,
    message: str,
    link: str,
    act_id: str,
    call_to_action_type: str = "LEARN_MORE",
    creative_type: str = "auto",
    page_id: Optional[str] = None,
    instagram_user_id: Optional[str] = None,
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
            Format: s3://bucket-name/path/to/folder/ or https://bucket.s3.amazonaws.com/path/
        adset_id (str): Ad Set ID where the ad will be created
        ad_name (str): Name for the ad
        creative_name (str): Name for the creative
        message (str): Ad text/message
        link (str): Destination URL
        act_id (str): Ad account ID (with act_ prefix)
        call_to_action_type (str): CTA button type. Default: "LEARN_MORE"
        creative_type (str): Type of creative to create. Options:
            - "auto": Automatically detect based on files (default)
            - "single_image": Force single image creative (uses first image)
            - "carousel": Force carousel creative (multiple images)
            - "video": Force video creative (uses first video)
        page_id (str): Facebook Page ID. If not provided, uses global config.
        instagram_user_id (str): Instagram User ID. If not provided, uses global config.
        aws_access_key_id (str): AWS Access Key ID. Optional if using IAM role.
        aws_secret_access_key (str): AWS Secret Access Key. Optional if using IAM role.
        aws_region (str): AWS region. Default: us-east-1
        status (str): Initial ad status. Default: "PAUSED"

    Returns:
        str: JSON string containing the created ad and creative details or error message.

    Example:
        ```python
        result = await create_ad_with_media_creative_from_s3_folder_link(
            s3_folder_url="s3://my-bucket/campaigns/summer-2024/",
            adset_id="123456789",
            ad_name="Summer Sale Ad",
            creative_name="Summer Sale Creative",
            message="Check out our summer collection!",
            link="https://example.com/summer-sale",
            act_id="act_123456789",
            call_to_action_type="SHOP_NOW"
        )
        ```
    """
    if not BOTO3_AVAILABLE:
        return json.dumps({
            "error": "boto3 is not installed. Install it with: pip install boto3"
        }, indent=2)

    try:
        # Parse S3 URL
        bucket, prefix = _parse_s3_url(s3_folder_url)

        # List folder contents
        files = _list_s3_folder_contents(
            bucket, prefix,
            aws_access_key_id, aws_secret_access_key, aws_region
        )

        if not files:
            return json.dumps({
                "error": "No files found in S3 folder",
                "s3_folder_url": s3_folder_url
            }, indent=2)

        # Categorize files by type
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv'}

        images = [f for f in files if os.path.splitext(f.lower())[1] in image_extensions]
        videos = [f for f in files if os.path.splitext(f.lower())[1] in video_extensions]

        if not images and not videos:
            return json.dumps({
                "error": "No supported media files found (images: jpg/png/gif, videos: mp4/mov)",
                "files_found": files
            }, indent=2)

        # Create temp directory for downloads
        temp_dir = tempfile.mkdtemp()

        try:
            # Determine creative type
            if creative_type == "auto":
                if videos:
                    creative_type = "video"
                elif len(images) > 1:
                    creative_type = "carousel"
                else:
                    creative_type = "single_image"

            creative_result = None

            if creative_type == "video":
                # Download and upload first video
                if not videos:
                    return json.dumps({
                        "error": "No video files found for video creative"
                    }, indent=2)

                video_key = videos[0]
                local_video_path = os.path.join(temp_dir, os.path.basename(video_key))

                _download_s3_file(
                    bucket, video_key, local_video_path,
                    aws_access_key_id, aws_secret_access_key, aws_region
                )

                # Upload to Facebook
                video_result = await _upload_video_to_facebook(
                    local_video_path, act_id, name=creative_name
                )

                # Create video creative
                creative_result = await _create_video_creative(
                    act_id=act_id,
                    name=creative_name,
                    video_id=video_result['id'],
                    message=message,
                    link=link,
                    call_to_action_type=call_to_action_type,
                    page_id=page_id,
                    instagram_user_id=instagram_user_id
                )

            elif creative_type == "carousel":
                # Download and upload multiple images (up to 10)
                if len(images) < 2:
                    return json.dumps({
                        "error": "Carousel requires at least 2 images",
                        "images_found": len(images)
                    }, indent=2)

                carousel_images = images[:10]  # Max 10 cards
                cards = []

                for idx, image_key in enumerate(carousel_images):
                    local_image_path = os.path.join(temp_dir, os.path.basename(image_key))

                    _download_s3_file(
                        bucket, image_key, local_image_path,
                        aws_access_key_id, aws_secret_access_key, aws_region
                    )

                    # Upload to Facebook
                    image_result = await _upload_image_to_facebook(
                        local_image_path, act_id
                    )

                    cards.append({
                        "image_hash": image_result['hash'],
                        "name": f"Card {idx + 1}",
                        "link": link
                    })

                # Create carousel creative
                creative_result = await _create_carousel_creative(
                    act_id=act_id,
                    name=creative_name,
                    cards=cards,
                    message=message,
                    link=link,
                    page_id=page_id,
                    instagram_user_id=instagram_user_id
                )

            else:  # single_image
                # Download and upload first image
                if not images:
                    return json.dumps({
                        "error": "No image files found for single image creative"
                    }, indent=2)

                image_key = images[0]
                local_image_path = os.path.join(temp_dir, os.path.basename(image_key))

                _download_s3_file(
                    bucket, image_key, local_image_path,
                    aws_access_key_id, aws_secret_access_key, aws_region
                )

                # Upload to Facebook
                image_result = await _upload_image_to_facebook(
                    local_image_path, act_id, name=creative_name
                )

                # Create single image creative
                creative_result = await _create_single_image_creative(
                    act_id=act_id,
                    name=creative_name,
                    image_hash=image_result['hash'],
                    message=message,
                    link=link,
                    call_to_action_type=call_to_action_type,
                    page_id=page_id,
                    instagram_user_id=instagram_user_id
                )

            # Create the ad
            ad_result = await create_ad_with_catalog_creative(
                adset_id=adset_id,
                creative_id=creative_result['id'],
                name=ad_name,
                status=status,
                act_id=act_id
            )

            return json.dumps({
                "success": True,
                "ad": json.loads(ad_result),
                "creative": creative_result,
                "creative_type": creative_type,
                "media_processed": {
                    "images": len(images),
                    "videos": len(videos)
                }
            }, indent=2)

        finally:
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        return json.dumps({
            "error": "Failed to create ad from S3 folder",
            "details": str(e),
            "s3_folder_url": s3_folder_url
        }, indent=2)
