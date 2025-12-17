## Required credentials overview

Depending on the features you want to use, different credentials are required.

### Always required

* YouTube Data API Key

### Required only for Google Sheets export

* Service Account JSON
* Spreadsheet ID

### Required only for transcripts

* OAuth Client Secrets JSON

---

## Step 1 Create a Google Cloud project

1. Open [https://console.cloud.google.com](https://console.cloud.google.com)
2. Sign in with your Google account
3. Click **Select project**
4. Click **New project**
5. Name it for example `youtube-exporter`
6. Click **Create**

---

## Step 2 Enable the YouTube Data API

1. In the project go to **APIs and Services**
2. Click **Library**
3. Search for **YouTube Data API v3**
4. Click **Enable**

---

## Step 3 Create a YouTube Data API Key

1. Go to **APIs and Services** → **Credentials**
2. Click **Create credentials**
3. Select **API key**
4. Copy the generated key

Optional but recommended:

* Restrict the key to **YouTube Data API v3** only

This key is entered into the field:

```
YouTube Data API Key
```

---

## Step 4 Enable Google Sheets API

This step is required only if you want to write data to Google Sheets.

1. Go to **APIs and Services** → **Library**
2. Search for **Google Sheets API**
3. Click **Enable**

---

## Step 5 Create a Service Account

This step is required only for Google Sheets export.

1. Go to **APIs and Services** → **Credentials**
2. Click **Create credentials** → **Service account**
3. Name it for example `sheets-writer`
4. Finish creation
5. Open the Service Account
6. Go to **Keys**
7. Click **Add key** → **Create new key**
8. Choose **JSON**
9. Download the file

This file is selected in the application as:

```
Service account JSON
```

---

## Step 6 Share the Google Sheet with the Service Account

1. Open your Google Sheet
2. Click **Share**
3. Add the service account email
   The email can be found inside the JSON file under `client_email`
4. Set permission to **Editor**
5. Save

Without this step the application cannot write to the sheet.

---

## Step 7 Get the Spreadsheet ID

Open your Google Sheet in the browser.

The URL looks like this:

```
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```

Copy only the part between `/d/` and `/edit`.

Enter this value into:

```
Spreadsheet ID
```

---

## Step 8 Set the worksheet name

The worksheet name must match exactly.

Examples:

* Sheet1
* Example
* Tabellenblatt1

This value is entered into:

```
Worksheet name
```

The name is case sensitive.

---

## Step 9 Create OAuth Client Secrets

This step is required only if you want transcripts.

1. Go to **APIs and Services** → **Credentials**
2. Click **Create credentials** → **OAuth client ID**
3. Choose **Desktop application**
4. Name it for example `transcript-provider`
5. Create and download the JSON file

This file is selected in the application as:

```
OAuth client secrets JSON
```

---

## Step 10 Configure OAuth consent screen

1. Go to **OAuth consent screen**
2. Choose **External**
3. Set an application name
4. Set a support email
5. Set a developer contact email
6. Save

### Add yourself as a test user

1. Scroll to **Test users**
2. Add your Google email address
3. Save

Without adding a test user Google will block the login.

---

## How to run the project

The project is structured as a Python package and must be started from the **project root folder**.

The root folder contains:

* `youtube_exporter/` directory
* `requirements.txt`

---

### Run using Windows Command Line or PowerShell

1. Open the project root folder
2. Open a terminal in that folder
3. Install dependencies

```
pip install -r requirements.txt
```

4. Start the graphical interface

```
python -m youtube_exporter.main
```

---

### Run using Visual Studio Code

1. Open Visual Studio Code
2. Click **File → Open Folder** and select the project root folder
3. Open the terminal via **Terminal → New Terminal**
4. Install dependencies

```
pip install -r requirements.txt
```

5. Start the application

```
python -m youtube_exporter.main
```

---

## Optional Command Line Usage (Advanced)

The tool can also be executed without the graphical interface.

Example:

```
python -m youtube_exporter.main --api-key YOUR_API_KEY --channel @channelname --max 10
```

---

## Common errors and fixes

### 403 Permission error when writing to Sheets

* The Google Sheet is not shared with the service account
* The service account does not have Editor permissions

### 400 Unable to parse range

* The worksheet name does not exist
* The worksheet name is misspelled or uses different capitalization

### quotaExceeded error

* The YouTube Data API daily quota has been reached
* Wait until the quota resets or use a new Google Cloud project

### Transcript field is empty

* The channel does not provide captions
* You do not have ownership or access via OAuth
* This is expected and compliant behavior

---

## Compliance notice

This project uses only:

* YouTube Data API v3
* Google Sheets API
* YouTube Captions API via OAuth

Transcripts are never scraped.
If transcripts are not officially accessible, the field remains empty.

---

## Summary

* Fully compliant with Google and YouTube policies
* Reusable and configurable
* Safe for client delivery
* No scraping and no policy violations

---

End of documentation.
