from __future__ import annotations

import argparse
import sys

from .config import ExportConfig, DEFAULT_MAX_VIDEOS, DEFAULT_SHEET_NAME
from .exporter import run_export
from .logutil import setup_logging
from .ui_tk import App


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Export YouTube channel video data to CSV and or Google Sheets")
    p.add_argument("--api-key", required=False, help="YouTube Data API key")
    p.add_argument("--channel", required=False,
                   help="Channel URL, channel id, username, or handle")
    p.add_argument("--max", type=int, default=DEFAULT_MAX_VIDEOS,
                   help="Max videos to export")
    p.add_argument("--out", default="", help="CSV output path")

    p.add_argument("--sheets-sa", default="",
                   help="Google service account json path for Sheets write")
    p.add_argument("--spreadsheet-id", default="",
                   help="Target spreadsheet id")
    p.add_argument("--worksheet", default=DEFAULT_SHEET_NAME,
                   help="Worksheet name")

    p.add_argument("--oauth-client", default="",
                   help="OAuth client secrets json for official captions download")
    p.add_argument("--skip-existing", action="store_true",
                   help="Skip rows already present in sheet (by Video Link)")

    p.add_argument("--gui", action="store_true", help="Launch GUI")
    p.add_argument("--verbose", action="store_true", help="Verbose logging")
    return p


def main() -> None:
    p = build_parser()
    args = p.parse_args()

    setup_logging(args.verbose)

    if args.gui or (len(sys.argv) == 1):
        app = App()
        app.mainloop()
        return

    if not args.api_key or not args.channel:
        print("Missing --api-key and --channel", file=sys.stderr)
        raise SystemExit(2)

    cfg = ExportConfig(
        api_key=args.api_key,
        channel_input=args.channel,
        max_videos=args.max,
        out_csv=args.out.strip() or None,
        sheets_service_account_json=args.sheets_sa.strip() or None,
        spreadsheet_id=args.spreadsheet_id.strip() or None,
        worksheet_name=args.worksheet.strip() or None,
        oauth_client_secrets=args.oauth_client.strip() or None,
        skip_existing=bool(args.skip_existing),
        verbose=bool(args.verbose),
    )

    run_export(cfg)
    print("Done")


if __name__ == "__main__":
    main()
