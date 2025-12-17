from __future__ import annotations

import csv
import logging
from typing import Any, Dict, List

from .config import ExportConfig
from .errors import FriendlyError
from .youtube_api import (
    build_youtube_api,
    build_youtube_oauth,
    parse_channel_identifier,
    resolve_channel_id,
    get_uploads_playlist_id,
    list_upload_video_ids,
    get_video_details,
    get_transcript_official,
)
from .sheets_writer import build_sheets_service, append_to_sheet, read_existing_video_urls


LOG = logging.getLogger("youtube_exporter")


def rows_to_csv(rows: List[Dict[str, Any]], out_path: str) -> None:
    headers = ["video_url", "title", "thumbnail_url",
               "view_count", "posted_date", "transcript"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in headers})


def run_export(cfg: ExportConfig) -> List[Dict[str, Any]]:
    LOG.info("Starting export")
    LOG.info("Channel input: %s", cfg.channel_input)
    LOG.info("Max videos: %s", cfg.max_videos)

    youtube = build_youtube_api(cfg.api_key)

    youtube_oauth = None
    if cfg.oauth_client_secrets:
        LOG.info("OAuth enabled for transcripts")
        youtube_oauth = build_youtube_oauth(
            cfg.oauth_client_secrets, token_path=cfg.token_path)
    else:
        LOG.info(
            "OAuth not enabled. Transcript field will remain empty unless you provide OAuth client secrets.")

    ident = parse_channel_identifier(cfg.channel_input)
    channel_id = resolve_channel_id(youtube, ident)
    LOG.info("Resolved channel id: %s", channel_id)

    uploads = get_uploads_playlist_id(youtube, channel_id)
    LOG.info("Uploads playlist id: %s", uploads)

    video_ids = list_upload_video_ids(youtube, uploads, cfg.max_videos)
    LOG.info("Fetched video ids: %s", len(video_ids))

    base_rows = get_video_details(youtube, video_ids)
    LOG.info("Fetched video details: %s", len(base_rows))

    existing_urls = set()
    sheets_service = None
    if cfg.skip_existing and cfg.sheets_service_account_json and cfg.spreadsheet_id and cfg.worksheet_name:
        sheets_service = build_sheets_service(cfg.sheets_service_account_json)
        existing_urls = read_existing_video_urls(
            sheets_service, cfg.spreadsheet_id, cfg.worksheet_name)
        LOG.info("Skip existing enabled. Existing URLs found: %s",
                 len(existing_urls))

    final_rows: List[Dict[str, Any]] = []
    for r in base_rows:
        if cfg.skip_existing and existing_urls and r.get("video_url") in existing_urls:
            continue

        video_id = r.get("video_id", "")
        r["transcript"] = get_transcript_official(
            youtube_oauth, video_id) if youtube_oauth else ""
        r.pop("video_id", None)
        final_rows.append(r)

    LOG.info("Rows after filtering: %s", len(final_rows))

    if cfg.out_csv:
        rows_to_csv(final_rows, cfg.out_csv)
        LOG.info("CSV written: %s", cfg.out_csv)

    if cfg.sheets_service_account_json and cfg.spreadsheet_id and cfg.worksheet_name:
        if sheets_service is None:
            sheets_service = build_sheets_service(
                cfg.sheets_service_account_json)

        append_to_sheet(
            sheets_service,
            cfg.spreadsheet_id,
            cfg.worksheet_name,
            final_rows,
            service_account_json=cfg.sheets_service_account_json
        )
        LOG.info("Google Sheets updated: %s", cfg.spreadsheet_id)

    LOG.info("Export finished")
    return final_rows
