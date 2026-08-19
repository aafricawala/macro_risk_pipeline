# Google Drive Headless Cloud Sync Setup Guide (100% Free)

This guide documents the exact setup required to enable automated GitHub Actions runners to upload production reports and CSV tables directly to a designated Google Drive folder.

---

## 1. Google Cloud Service Account Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Select your active project (`macrorisk-pipeline`).
3. Search for **Google Drive API** in the top search bar and click **Enable**.
4. Navigate to **APIs & Services -> Credentials -> Create Credentials -> Service Account**.
5. Name: `macrorisk-gdrive-bot` -> Click **Create and Continue** -> Click **Done**.
6. In the Service Accounts table, click your new bot email -> Go to the **Keys** tab.
7. Click **Add Key -> Create new key -> JSON -> Create**.
8. A `.json` private key file will download to your computer.

---

## 2. Google Drive Folder Sharing
1. Open Google Drive in your browser.
2. Navigate to your target folder: `My Drive > Colab Notebooks > macro_risk_pipeline`.
3. Click **Share** -> Paste the Service Account email (`macrorisk-gdrive-bot@...`).
4. Set role to **Editor** -> Click **Share**.
5. Copy the **Folder ID** from your browser address bar:
   `https://drive.google.com/drive/folders/{GDRIVE_FOLDER_ID}`

---

## 3. GitHub Repository Secrets
Navigate to your GitHub repository -> **Settings -> Secrets and variables -> Actions -> New repository secret**:

| Secret Name | Secret Value |
| :--- | :--- |
| `GDRIVE_SERVICE_ACCOUNT_KEY` | Entire text content of the downloaded `.json` service account key file |
| `GDRIVE_FOLDER_ID` | Alphanumeric folder ID copied from the Google Drive URL |
| `GEMINI_API_KEY` | Google AI Studio Gemini API Key |

---

## 4. Automated Tiered Storage Architecture
* **Tier 1 (Primary):** Direct Google Drive upload via `src/core/gdrive_sync.py`.
* **Tier 2 (Secondary Fallback):** GitHub Actions Artifact storage (`actions/upload-artifact@v4`).
* **Tier 3 (Local Fallback):** Local runner disk storage in `./artifacts_storage/`.
