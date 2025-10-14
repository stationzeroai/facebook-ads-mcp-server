"""
Media handling utilities for Facebook ad creatives.

This module provides helper functions for uploading images and videos to Facebook,
extracting video thumbnails, and creating various types of ad creatives.
"""

import json
import os
import tempfile
from typing import Optional, Dict, Any, List
import httpx
from .api import (
    FB_GRAPH_URL,
    get_access_token,
    get_page_id,
    get_instagram_user_id,
    _make_graph_api_post
)

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


async def _upload_image_to_facebook(
    image_path: str,
    act_id: str,
    name: Optional[str] = None
) -> Dict[str, Any]:
    """Upload an image to Facebook Ad Account.

    Args:
        image_path (str): Local path to the image file
        act_id (str): Ad account ID (with act_ prefix)
        name (str): Optional name for the image

    Returns:
        Dict: Response containing image hash and other metadata

    Raises:
        Exception: If upload fails or image doesn't exist
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/adimages"

    # Prepare the file upload
    with open(image_path, 'rb') as image_file:
        files = {'file': (os.path.basename(image_path), image_file, 'image/jpeg')}
        data = {'access_token': access_token}

        if name:
            data['name'] = name

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, data=data, files=files)

        response.raise_for_status()
        result = response.json()

        # Extract the hash from the nested response structure
        if 'images' in result:
            # Response format: {"images": {"filename.jpg": {"hash": "...", "url": "..."}}}
            first_image = next(iter(result['images'].values()))
            return first_image
        else:
            return result


async def _upload_video_to_facebook(
    video_path: str,
    act_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Upload a video to Facebook Ad Account.

    Facebook video upload uses a resumable upload process for large files.
    This function handles the complete upload flow.

    Args:
        video_path (str): Local path to the video file
        act_id (str): Ad account ID (with act_ prefix)
        name (str): Optional name for the video
        description (str): Optional description

    Returns:
        Dict: Response containing video ID and other metadata

    Raises:
        Exception: If upload fails or video doesn't exist
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/advideos"

    file_size = os.path.getsize(video_path)

    # Prepare the file upload
    with open(video_path, 'rb') as video_file:
        files = {'file': (os.path.basename(video_path), video_file, 'video/mp4')}
        data = {
            'access_token': access_token,
            'file_size': str(file_size)
        }

        if name:
            data['name'] = name
        if description:
            data['description'] = description

        # Upload with extended timeout for large videos
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, data=data, files=files)

        response.raise_for_status()
        return response.json()


def _extract_video_thumbnail(
    video_path: str,
    output_path: Optional[str] = None,
    frame_time: float = 1.0
) -> str:
    """Extract a thumbnail image from a video file.

    Args:
        video_path (str): Path to the video file
        output_path (str): Path where to save the thumbnail. If None, creates a temp file.
        frame_time (float): Time in seconds from which to extract the frame. Default: 1.0

    Returns:
        str: Path to the saved thumbnail image

    Raises:
        Exception: If opencv-python is not installed or extraction fails
    """
    if not CV2_AVAILABLE:
        raise ImportError(
            "opencv-python is required for video thumbnail extraction. "
            "Install it with: pip install opencv-python"
        )

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Open the video
    video = cv2.VideoCapture(video_path)

    if not video.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    try:
        # Get FPS to calculate frame number
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_number = int(fps * frame_time)

        # Set the frame position
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        # Read the frame
        success, frame = video.read()

        if not success:
            # Fallback to first frame
            video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            success, frame = video.read()

            if not success:
                raise ValueError("Could not read frame from video")

        # Generate output path if not provided
        if not output_path:
            temp_dir = tempfile.gettempdir()
            video_basename = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(temp_dir, f"{video_basename}_thumbnail.jpg")

        # Save the frame as an image
        cv2.imwrite(output_path, frame)

        return output_path

    finally:
        video.release()


async def _create_single_image_creative(
    act_id: str,
    name: str,
    image_hash: str,
    message: str,
    link: str,
    call_to_action_type: str = "LEARN_MORE"
) -> Dict[str, Any]:
    """Create a single image ad creative.

    Args:
        act_id (str): Ad account ID (with act_ prefix)
        name (str): Creative name
        image_hash (str): Hash of uploaded image from _upload_image_to_facebook
        message (str): Ad text/message
        link (str): Destination URL
        call_to_action_type (str): CTA button type. Default: "LEARN_MORE"

    Returns:
        Dict: Created creative details
    """
    page_id = get_page_id()
    instagram_user_id = get_instagram_user_id()

    if not page_id:
        raise ValueError("No page_id provided or configured")

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/adcreatives"

    object_story_spec = {
        "page_id": page_id,
        "link_data": {
            "message": message,
            "link": link,
            "image_hash": image_hash,
            "call_to_action": {
                "type": call_to_action_type
            }
        }
    }

    if instagram_user_id:
        object_story_spec["instagram_actor_id"] = instagram_user_id

    params = {
        "access_token": access_token,
        "name": name,
        "object_story_spec": json.dumps(object_story_spec)
    }

    return await _make_graph_api_post(url, params)


async def _create_carousel_creative(
    act_id: str,
    name: str,
    cards: List[Dict[str, Any]],
    message: str,
    link: str
) -> Dict[str, Any]:
    """Create a carousel ad creative with multiple cards.

    Args:
        act_id (str): Ad account ID (with act_ prefix)
        name (str): Creative name
        cards (List[Dict]): List of carousel cards. Each card should have:
            - 'picture' or 'image_hash': Image URL or hash
            - 'name': Card headline
            - 'description': Card description
            - 'link': Card destination URL
            - 'call_to_action' (optional): Dict with 'type' key
        message (str): Main ad text/message
        link (str): Default destination URL

    Returns:
        Dict: Created creative details

    Example:
        ```python
        cards = [
            {
                "image_hash": "abc123",
                "name": "Product 1",
                "description": "Description 1",
                "link": "https://example.com/product1"
            },
            {
                "image_hash": "def456",
                "name": "Product 2",
                "description": "Description 2",
                "link": "https://example.com/product2"
            }
        ]
        creative = await _create_carousel_creative(
            act_id="act_123",
            name="Carousel Ad",
            cards=cards,
            message="Check out our products!",
            link="https://example.com"
        )
        ```
    """
    page_id = get_page_id()
    instagram_user_id = get_instagram_user_id()

    if not page_id:
        raise ValueError("No page_id provided or configured")

    if not cards or len(cards) < 2:
        raise ValueError("Carousel creative requires at least 2 cards")

    if len(cards) > 10:
        raise ValueError("Carousel creative supports maximum 10 cards")

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/adcreatives"

    # Process cards
    child_attachments = []
    for card in cards:
        attachment = {}

        # Image
        if 'image_hash' in card:
            attachment['image_hash'] = card['image_hash']
        elif 'picture' in card:
            attachment['picture'] = card['picture']
        else:
            raise ValueError("Each card must have either 'image_hash' or 'picture'")

        # Text content
        if 'name' in card:
            attachment['name'] = card['name']
        if 'description' in card:
            attachment['description'] = card['description']

        # Link
        attachment['link'] = card.get('link', link)

        # Call to action
        if 'call_to_action' in card:
            attachment['call_to_action'] = card['call_to_action']

        child_attachments.append(attachment)

    object_story_spec = {
        "page_id": page_id,
        "link_data": {
            "message": message,
            "link": link,
            "child_attachments": child_attachments
        }
    }

    if instagram_user_id:
        object_story_spec["instagram_actor_id"] = instagram_user_id

    params = {
        "access_token": access_token,
        "name": name,
        "object_story_spec": json.dumps(object_story_spec)
    }

    return await _make_graph_api_post(url, params)


async def _create_video_creative(
    act_id: str,
    name: str,
    video_id: str,
    message: str,
    link: Optional[str] = None,
    call_to_action_type: str = "LEARN_MORE",
    thumbnail_url: Optional[str] = None
) -> Dict[str, Any]:
    """Create a video ad creative.

    Args:
        act_id (str): Ad account ID (with act_ prefix)
        name (str): Creative name
        video_id (str): Video ID from _upload_video_to_facebook
        message (str): Ad text/message
        link (str): Destination URL. Optional for video ads.
        call_to_action_type (str): CTA button type. Default: "LEARN_MORE"
        thumbnail_url (str): Custom thumbnail URL. Optional.

    Returns:
        Dict: Created creative details
    """
    page_id = get_page_id()
    instagram_user_id = get_instagram_user_id()

    if not page_id:
        raise ValueError("No page_id provided or configured")

    access_token = get_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/adcreatives"

    video_data = {
        "message": message,
        "video_id": video_id
    }

    if link:
        video_data["link"] = link
        video_data["call_to_action"] = {
            "type": call_to_action_type
        }

    if thumbnail_url:
        video_data["image_url"] = thumbnail_url

    object_story_spec = {
        "page_id": page_id,
        "video_data": video_data
    }

    if instagram_user_id:
        object_story_spec["instagram_actor_id"] = instagram_user_id

    params = {
        "access_token": access_token,
        "name": name,
        "object_story_spec": json.dumps(object_story_spec)
    }

    return await _make_graph_api_post(url, params)
