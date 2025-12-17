from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

YOUTUBE_SCOPES_CAPTIONS = ["https://www.googleapis.com/auth/youtube.force-ssl"]
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

DEFAULT_MAX_VIDEOS = 25
DEFAULT_SHEET_NAME = "Example"
DEFAULT_TOKEN_PATH = "token.json"


@dataclass(frozen=True)
class ExportConfig:
    api_key: str
    channel_input: str
    max_videos: int = DEFAULT_MAX_VIDEOS

    out_csv: Optional[str] = None

    sheets_service_account_json: Optional[str] = None
    spreadsheet_id: Optional[str] = None
    worksheet_name: Optional[str] = None

    oauth_client_secrets: Optional[str] = None
    token_path: str = DEFAULT_TOKEN_PATH

    skip_existing: bool = False
    verbose: bool = False
