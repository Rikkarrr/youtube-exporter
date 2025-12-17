from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

from .config import SHEETS_SCOPES
from .errors import PermissionDeniedError, SheetNotFoundError


LOG = logging.getLogger("youtube_exporter")


def try_read_service_account_email(service_account_json_path: str) -> str:
    try:
        data = json.loads(
            Path(service_account_json_path).read_text(encoding="utf-8"))
        return str(data.get("client_email") or "")
    except Exception:
        return ""


def build_sheets_service(service_account_json_path: str):
    creds = service_account.Credentials.from_service_account_file(
        service_account_json_path,
        scopes=SHEETS_SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def list_sheet_titles(sheets_service, spreadsheet_id: str) -> List[str]:
    meta = sheets_service.spreadsheets().get(
        spreadsheetId=spreadsheet_id).execute()
    sheets = meta.get("sheets", [])
    titles: List[str] = []
    for s in sheets:
        props = s.get("properties", {})
        title = props.get("title")
        if title:
            titles.append(str(title))
    return titles


def read_existing_video_urls(
    sheets_service,
    spreadsheet_id: str,
    sheet_name: str,
) -> Set[str]:
    try:
        rng = f"{sheet_name}!A:A"
        resp = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=rng
        ).execute()
        values = resp.get("values", [])
        urls: Set[str] = set()
        for row in values:
            if row and isinstance(row, list):
                v = str(row[0]).strip()
                if v.startswith("http"):
                    urls.add(v)
        return urls
    except HttpError:
        return set()


def ensure_sheet_exists(
    sheets_service,
    spreadsheet_id: str,
    sheet_name: str,
    service_account_json: Optional[str]
) -> None:
    try:
        titles = list_sheet_titles(sheets_service, spreadsheet_id)
        if sheet_name not in titles:
            raise SheetNotFoundError(
                f'Worksheet "{sheet_name}" not found. Available worksheets: {", ".join(titles) if titles else "(none)"}'
            )
    except HttpError as e:
        client_email = try_read_service_account_email(
            service_account_json) if service_account_json else ""
        hint = f" Share the Google Sheet with this service account as Editor: {client_email}" if client_email else ""
        raise PermissionDeniedError(
            f"Cannot access spreadsheet metadata.{hint}") from e


def append_to_sheet(
    sheets_service,
    spreadsheet_id: str,
    sheet_name: str,
    rows: List[Dict[str, Any]],
    service_account_json: Optional[str] = None
) -> None:
    headers = [
        "YouTube Video Link",
        "Thumbnail",
        "Title",
        "Posted Date",
        "Views Count",
        "Transcript"
    ]

    values: List[List[Any]] = [headers]

    for r in rows:
        thumb_url = r.get("thumbnail_url", "")
        thumbnail_formula = f'=IMAGE("{thumb_url}")' if thumb_url else ""
        values.append([
            r.get("video_url", ""),
            thumbnail_formula,
            r.get("title", ""),
            r.get("posted_date", ""),
            r.get("view_count", ""),
            r.get("transcript", ""),
        ])

    ensure_sheet_exists(sheets_service, spreadsheet_id,
                        sheet_name, service_account_json)

    target_range = f"{sheet_name}!A1"
    try:
        sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=target_range,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": values}
        ).execute()
    except HttpError as e:
        client_email = try_read_service_account_email(
            service_account_json) if service_account_json else ""
        hint = f" Share the Google Sheet with this service account as Editor: {client_email}" if client_email else ""
        raise PermissionDeniedError(
            f"Permission denied while writing to Google Sheets.{hint}") from e
