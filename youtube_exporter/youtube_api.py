from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from dateutil import parser as date_parser
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from .config import YOUTUBE_SCOPES_CAPTIONS
from .errors import FriendlyError, QuotaExceededError


LOG = logging.getLogger("youtube_exporter")


def _http_error_reason(err: HttpError) -> str:
    try:
        data = json.loads(err.content.decode("utf-8", errors="ignore"))
        errors = data.get("error", {}).get("errors", [])
        if errors and isinstance(errors, list):
            return str(errors[0].get("reason") or "")
    except Exception:
        return ""
    return ""


def _raise_friendly_http_error(err: HttpError, context: str) -> None:
    reason = _http_error_reason(err)
    status = getattr(err.resp, "status", None)

    if reason == "quotaExceeded":
        raise QuotaExceededError(
            "YouTube API quota exceeded. Reduce max videos, wait for quota reset, or use a new Google Cloud project and API key."
        ) from err

    raise FriendlyError(
        f"API error while {context}. Status {status}. Reason {reason or 'unknown'}") from err


def parse_channel_identifier(channel_input: str) -> Dict[str, str]:
    s = channel_input.strip()

    if s.startswith("@"):
        return {"forHandle": s}

    if re.match(r"^UC[a-zA-Z0-9_-]{20,}$", s):
        return {"id": s}

    m = re.search(r"(?:youtube\.com|youtu\.be)/(@[A-Za-z0-9_.-]+)", s)
    if m:
        return {"forHandle": m.group(1)}

    m = re.search(r"youtube\.com/channel/(UC[a-zA-Z0-9_-]{20,})", s)
    if m:
        return {"id": m.group(1)}

    m = re.search(r"youtube\.com/user/([A-Za-z0-9_.-]+)", s)
    if m:
        return {"forUsername": m.group(1)}

    m = re.search(r"youtube\.com/c/([A-Za-z0-9_.-]+)", s)
    if m:
        return {"customUrl": m.group(1)}

    return {"forUsername": s}


def build_youtube_api(api_key: str):
    return build("youtube", "v3", developerKey=api_key)


def build_youtube_oauth(client_secrets_path: str, token_path: str = "token.json"):
    creds = None
    token_file = Path(token_path)

    if token_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(
                str(token_file), YOUTUBE_SCOPES_CAPTIONS)
        except Exception:
            creds = None

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_path, YOUTUBE_SCOPES_CAPTIONS)
        creds = flow.run_local_server(port=0)
        token_file.write_text(creds.to_json(), encoding="utf-8")

    return build("youtube", "v3", credentials=creds)


def iso_to_date(iso_str: str) -> str:
    try:
        dt = date_parser.parse(iso_str)
        if isinstance(dt, datetime):
            return dt.date().isoformat()
        return str(iso_str)
    except Exception:
        return str(iso_str)


def chunked(lst: List[str], n: int) -> Iterable[List[str]]:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def pick_thumbnail(snippet: Dict[str, Any]) -> str:
    thumbs = (snippet.get("thumbnails") or {})
    for key in ["maxres", "standard", "high", "medium", "default"]:
        if key in thumbs and "url" in thumbs[key]:
            return thumbs[key]["url"]
    return ""


def resolve_channel_id(youtube, ident: Dict[str, str]) -> str:
    try:
        if "id" in ident:
            return ident["id"]

        if "forHandle" in ident:
            resp = youtube.channels().list(
                part="id", forHandle=ident["forHandle"]).execute()
            items = resp.get("items", [])
            if not items:
                raise FriendlyError("Channel not found for handle")
            return items[0]["id"]

        if "forUsername" in ident:
            resp = youtube.channels().list(
                part="id", forUsername=ident["forUsername"]).execute()
            items = resp.get("items", [])
            if items:
                return items[0]["id"]

            q = ident["forUsername"]
            sresp = youtube.search().list(part="snippet", q=q,
                                          type="channel", maxResults=1).execute()
            sitems = sresp.get("items", [])
            if not sitems:
                raise FriendlyError("Channel not found")
            return sitems[0]["snippet"]["channelId"]

        if "customUrl" in ident:
            q = ident["customUrl"]
            sresp = youtube.search().list(part="snippet", q=q,
                                          type="channel", maxResults=1).execute()
            sitems = sresp.get("items", [])
            if not sitems:
                raise FriendlyError("Channel not found for custom url")
            return sitems[0]["snippet"]["channelId"]

        raise FriendlyError("Unsupported channel identifier")

    except HttpError as e:
        _raise_friendly_http_error(e, "resolving channel id")


def get_uploads_playlist_id(youtube, channel_id: str) -> str:
    try:
        resp = youtube.channels().list(part="contentDetails", id=channel_id).execute()
        items = resp.get("items", [])
        if not items:
            raise FriendlyError("Channel contentDetails not found")
        return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except HttpError as e:
        _raise_friendly_http_error(e, "fetching uploads playlist id")


def list_upload_video_ids(youtube, uploads_playlist_id: str, max_videos: int) -> List[str]:
    video_ids: List[str] = []
    page_token = None

    try:
        while True:
            remaining = max_videos - len(video_ids)
            if remaining <= 0:
                break

            resp = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=min(50, remaining),
                pageToken=page_token
            ).execute()

            for it in resp.get("items", []):
                vid = it["contentDetails"]["videoId"]
                video_ids.append(vid)
                if len(video_ids) >= max_videos:
                    return video_ids

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        return video_ids

    except HttpError as e:
        _raise_friendly_http_error(e, "listing channel uploads")


def get_video_details(youtube, video_ids: List[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        for batch in chunked(video_ids, 50):
            resp = youtube.videos().list(
                part="snippet,statistics",
                id=",".join(batch)
            ).execute()

            for it in resp.get("items", []):
                vid = it["id"]
                snippet = it.get("snippet", {})
                stats = it.get("statistics", {})

                rows.append({
                    "video_url": f"https://www.youtube.com/watch?v={vid}",
                    "title": snippet.get("title", ""),
                    "thumbnail_url": pick_thumbnail(snippet),
                    "view_count": stats.get("viewCount", ""),
                    "posted_date": iso_to_date(snippet.get("publishedAt", "")),
                    "video_id": vid,
                })
        return rows

    except HttpError as e:
        _raise_friendly_http_error(e, "fetching video details")


def download_caption_track(youtube_oauth, caption_id: str) -> str:
    try:
        data = youtube_oauth.captions().download(id=caption_id, tfmt="srt").execute()
        if isinstance(data, (bytes, bytearray)):
            return data.decode("utf-8", errors="replace")
        return str(data)
    except HttpError:
        return ""


def get_transcript_official(
    youtube_oauth,
    video_id: str,
    prefer_langs: Optional[List[str]] = None
) -> str:
    if youtube_oauth is None:
        return ""

    prefer_langs = prefer_langs or ["en", "de"]

    try:
        resp = youtube_oauth.captions().list(part="snippet", videoId=video_id).execute()
        items = resp.get("items", [])
        if not items:
            return ""

        def score(item: Dict[str, Any]) -> int:
            lang = item.get("snippet", {}).get("language", "")
            return 0 if lang in prefer_langs else 1

        items_sorted = sorted(items, key=score)
        caption_id = items_sorted[0]["id"]
        srt = download_caption_track(youtube_oauth, caption_id)
        return srt.strip()

    except HttpError:
        return ""
