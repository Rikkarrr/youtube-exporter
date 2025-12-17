from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from .config import ExportConfig, DEFAULT_MAX_VIDEOS, DEFAULT_SHEET_NAME
from .exporter import run_export
from .errors import FriendlyError


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Channel Exporter")
        self.geometry("720x560")

        self.var_api_key = tk.StringVar()
        self.var_channel = tk.StringVar()
        self.var_max = tk.StringVar(value=str(DEFAULT_MAX_VIDEOS))

        self.var_csv = tk.StringVar()

        self.var_use_sheets = tk.BooleanVar(value=False)
        self.var_sa_json = tk.StringVar()
        self.var_sheet_id = tk.StringVar()
        self.var_sheet_name = tk.StringVar(value=DEFAULT_SHEET_NAME)

        self.var_use_oauth = tk.BooleanVar(value=False)
        self.var_oauth_json = tk.StringVar()

        self.var_skip_existing = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Label(frm, text="YouTube Data API Key").grid(
            row=0, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_api_key, width=60).grid(
            row=0, column=1, sticky="we", **pad)

        ttk.Label(frm, text="Channel URL or Handle").grid(
            row=1, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_channel, width=60).grid(
            row=1, column=1, sticky="we", **pad)

        ttk.Label(frm, text="Max videos").grid(
            row=2, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_max, width=10).grid(
            row=2, column=1, sticky="w", **pad)

        ttk.Separator(frm).grid(row=3, column=0,
                                columnspan=2, sticky="we", pady=12)

        ttk.Label(frm, text="CSV output file").grid(
            row=4, column=0, sticky="w", **pad)
        out_row = ttk.Frame(frm)
        out_row.grid(row=4, column=1, sticky="we", **pad)
        ttk.Entry(out_row, textvariable=self.var_csv, width=45).pack(
            side="left", fill="x", expand=True)
        ttk.Button(out_row, text="Browse", command=self._pick_csv).pack(
            side="left", padx=8)

        ttk.Separator(frm).grid(row=5, column=0,
                                columnspan=2, sticky="we", pady=12)

        ttk.Checkbutton(frm, text="Write to Google Sheets", variable=self.var_use_sheets).grid(
            row=6, column=0, sticky="w", **pad
        )

        ttk.Label(frm, text="Service account JSON").grid(
            row=7, column=0, sticky="w", **pad)
        sa_row = ttk.Frame(frm)
        sa_row.grid(row=7, column=1, sticky="we", **pad)
        ttk.Entry(sa_row, textvariable=self.var_sa_json, width=45).pack(
            side="left", fill="x", expand=True)
        ttk.Button(sa_row, text="Browse", command=self._pick_sa).pack(
            side="left", padx=8)

        ttk.Label(frm, text="Spreadsheet ID").grid(
            row=8, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_sheet_id, width=60).grid(
            row=8, column=1, sticky="we", **pad)

        ttk.Label(frm, text="Worksheet name").grid(
            row=9, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_sheet_name, width=30).grid(
            row=9, column=1, sticky="w", **pad)

        ttk.Checkbutton(frm, text="Skip existing rows (by Video Link)", variable=self.var_skip_existing).grid(
            row=10, column=0, sticky="w", **pad
        )

        ttk.Separator(frm).grid(row=11, column=0,
                                columnspan=2, sticky="we", pady=12)

        ttk.Checkbutton(frm, text="Use OAuth for transcripts (official captions API)", variable=self.var_use_oauth).grid(
            row=12, column=0, sticky="w", **pad
        )

        ttk.Label(frm, text="OAuth client secrets JSON").grid(
            row=13, column=0, sticky="w", **pad)
        oa_row = ttk.Frame(frm)
        oa_row.grid(row=13, column=1, sticky="we", **pad)
        ttk.Entry(oa_row, textvariable=self.var_oauth_json, width=45).pack(
            side="left", fill="x", expand=True)
        ttk.Button(oa_row, text="Browse", command=self._pick_oauth).pack(
            side="left", padx=8)

        ttk.Separator(frm).grid(row=14, column=0,
                                columnspan=2, sticky="we", pady=12)

        btns = ttk.Frame(frm)
        btns.grid(row=15, column=0, columnspan=2, sticky="we", pady=8)
        ttk.Button(btns, text="Run export", command=self._run).pack(
            side="left", padx=6)
        ttk.Button(btns, text="Quit", command=self.destroy).pack(
            side="left", padx=6)

        frm.columnconfigure(1, weight=1)

    def _pick_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if path:
            self.var_csv.set(path)

    def _pick_sa(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            self.var_sa_json.set(path)

    def _pick_oauth(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            self.var_oauth_json.set(path)

    def _run(self):
        api_key = self.var_api_key.get().strip()
        channel = self.var_channel.get().strip()

        try:
            max_v = int(self.var_max.get().strip() or str(DEFAULT_MAX_VIDEOS))
        except ValueError:
            messagebox.showerror(
                "Invalid input", "Max videos must be a number")
            return

        if not api_key or not channel:
            messagebox.showerror(
                "Missing input", "API key and channel are required")
            return

        out_csv = self.var_csv.get().strip() or None

        use_sheets = self.var_use_sheets.get()
        sa_json = self.var_sa_json.get().strip() if use_sheets else None
        sheet_id = self.var_sheet_id.get().strip() if use_sheets else None
        sheet_name = self.var_sheet_name.get().strip() if use_sheets else None

        if use_sheets and (not sa_json or not sheet_id or not sheet_name):
            messagebox.showerror(
                "Sheets config missing",
                "Service account JSON, spreadsheet ID, and worksheet name are required"
            )
            return

        use_oauth = self.var_use_oauth.get()
        oauth_json = self.var_oauth_json.get().strip() if use_oauth else None
        if use_oauth and not oauth_json:
            messagebox.showerror(
                "OAuth config missing", "OAuth client secrets JSON is required for transcripts")
            return

        cfg = ExportConfig(
            api_key=api_key,
            channel_input=channel,
            max_videos=max_v,
            out_csv=out_csv,
            sheets_service_account_json=sa_json,
            spreadsheet_id=sheet_id,
            worksheet_name=sheet_name,
            oauth_client_secrets=oauth_json,
            skip_existing=self.var_skip_existing.get(),
        )

        try:
            rows = run_export(cfg)
            messagebox.showinfo("Done", f"Exported {len(rows)} videos")
        except FriendlyError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))
