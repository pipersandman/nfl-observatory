# 🏈 NFL Officiating Observatory

A data-driven investigation into NFL officiating patterns, crew chief behavior, and what 16,000+ penalty flags reveal about human decision-making.

---

## 📋 Table of Contents

1. [Quick Start (Local Preview)](#-quick-start-local-preview)
2. [Full Setup Instructions](#-full-setup-instructions)
3. [Populating Real Data](#-populating-real-data)
4. [GitHub Setup](#-github-setup)
5. [HostGator Deployment](#-hostgator-deployment)
6. [How It Works](#-how-it-works)
7. [File Structure](#-file-structure)
8. [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start (Local Preview)

To preview the site locally right now:

### Windows (PowerShell)

```powershell
# Navigate to your project
cd C:\Users\tfost\nfl-observatory

# Start a local server
python -m http.server 8000 --directory frontend

# Open in browser: http://localhost:8000
```

### Mac/Linux

```bash
cd ~/nfl-observatory
python3 -m http.server 8000 --directory frontend
# Open: http://localhost:8000
```

> **Note:** The site will show "0" values until you run the data script.

---

## 🔧 Full Setup Instructions

### Step 1: Install Python Dependencies

Open PowerShell and run:

```powershell
# Navigate to project
cd C:\Users\tfost\nfl-observatory

# Create virtual environment (recommended)
python -m venv venv

# Activate it
.\venv\Scripts\Activate

# Install dependencies
pip install -r scripts/requirements.txt
```

You should see output like:
```
Successfully installed nfl_data_py-0.3.x pandas-2.x.x numpy-1.x.x
```

### Step 2: Verify Installation

```powershell
python -c "import nfl_data_py; print('✓ nfl_data_py installed')"
python -c "import pandas; print('✓ pandas installed')"
```

---

## 📊 Populating Real Data

### Run the Data Script (First Time - Full Build)

This downloads ALL data from 2020-2024. Takes 2-5 minutes.

```powershell
# Make sure you're in the project directory
cd C:\Users\tfost\nfl-observatory

# Activate virtual environment if not already
.\venv\Scripts\Activate

# Run FULL rebuild (first time)
python scripts/update_data.py --full
```

You'll see output like:
```
============================================================
🏈 NFL OFFICIATING OBSERVATORY - DATA UPDATE
============================================================
   Mode: Full Rebuild
   Seasons: [2020, 2021, 2022, 2023, 2024]

📥 Loading data for seasons: [2020, 2021, 2022, 2023, 2024]
============================================================
   Loading officials...
   ✓ 8547 official assignments
   Loading schedules...
   ✓ 1408 games
   Loading play-by-play (this takes a minute)...
   ✓ 16244 penalties

📊 Calculating referee statistics...
   ✓ Calculated stats for 17 crew chiefs

📈 Calculating league trends...
   ✓ Generated trend data

💾 Saving JSON files...
   💾 stats.json
   💾 trends.json
   💾 insights.json
   💾 referees.json

📝 Generating referee profiles...
   ✓ Generated 17 profiles

============================================================
✅ DATA UPDATE COMPLETE
============================================================
```

### Verify Data Was Created

```powershell
# Check the data files exist
Get-ChildItem frontend\data\

# Should show:
#   stats.json
#   referees.json
#   trends.json
#   insights.json
#   referee\ (folder with individual profiles)
```

### Preview Updated Site

```powershell
python -m http.server 8000 --directory frontend
# Open http://localhost:8000
```

You should now see real numbers!

---

## 🐙 GitHub Setup

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `nfl-observatory` (or whatever you want)
3. Select **Private**
4. Do NOT initialize with README (we have one)
5. Click **Create repository**

### Step 2: Initialize Git Locally

```powershell
cd C:\Users\tfost\nfl-observatory

# Initialize git
git init

# Add all files
git add .

# First commit
git commit -m "Initial commit - NFL Officiating Observatory"
```

### Step 3: Connect to GitHub

GitHub will show you commands after creating the repo. Run:

```powershell
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/nfl-observatory.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 4: Add GitHub Secrets

Go to your repo on GitHub, then:

1. Click **Settings** (top menu)
2. Click **Secrets and variables** → **Actions** (left sidebar)
3. Click **New repository secret**

Add these 4 secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `FTP_SERVER` | Your HostGator FTP server | `ftp.yourdomain.com` |
| `FTP_USERNAME` | Your FTP username | `user@yourdomain.com` |
| `FTP_PASSWORD` | Your FTP password | `yourpassword` |
| `FTP_SERVER_DIR` | Path on server | `/public_html/nfl/` |

### Step 5: Test GitHub Actions

1. Go to **Actions** tab in your repo
2. Click **Update NFL Data** workflow (left sidebar)
3. Click **Run workflow** button (right side)
4. Check **Full historical rebuild** checkbox
5. Click green **Run workflow** button

Watch the workflow run. It should:
- Pull data from NFL sources
- Generate JSON files
- Commit to repo
- Deploy to HostGator

---

## 🌐 HostGator Deployment

### Before GitHub Actions (Manual First Deploy)

If you want to deploy before setting up Actions:

#### Option A: FTP Client (FileZilla)

1. Download FileZilla: https://filezilla-project.org/
2. Connect to HostGator:
   - Host: `ftp.yourdomain.com`
   - Username: (from cPanel)
   - Password: (from cPanel)
   - Port: `21`
3. Navigate to `/public_html/` (or subdomain folder)
4. Upload entire `frontend/` folder contents

#### Option B: cPanel File Manager

1. Log into HostGator cPanel
2. Open **File Manager**
3. Navigate to `public_html` (or your target folder)
4. Upload files from your local `frontend/` folder

### After GitHub Actions

Once Actions is working, deployments are automatic every Tuesday. You can also trigger manually from the Actions tab.

### Verify Deployment

Visit your domain:
- `https://yourdomain.com/` (if deployed to root)
- `https://yourdomain.com/nfl/` (if deployed to subdirectory)

---

## ⚙️ How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    GITHUB ACTIONS                            │
│  Runs every Tuesday 6am UTC (after Monday Night Football)   │
│                                                              │
│  1. Pulls latest data from nfl_data_py                      │
│  2. Runs Python scripts to calculate stats                  │
│  3. Generates JSON files                                    │
│  4. Commits changes to repo                                 │
│  5. Deploys to HostGator via FTP                            │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    HOSTGATOR                                 │
│  Static files only - no server-side code needed             │
│                                                              │
│  /index.html          - Main page                           │
│  /css/styles.css      - Styles                              │
│  /js/app.js           - JavaScript                          │
│  /data/               - JSON data (auto-updated)            │
│     ├── stats.json                                          │
│     ├── referees.json                                       │
│     ├── trends.json                                         │
│     ├── insights.json                                       │
│     └── referee/*.json  - Individual profiles               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
nfl-observatory/
├── .github/
│   └── workflows/
│       └── update-data.yml      ← GitHub Actions (auto-runs Tuesdays)
│
├── scripts/
│   ├── requirements.txt         ← Python dependencies
│   └── update_data.py           ← Main data pipeline script
│
├── frontend/                     ← DEPLOYED TO HOSTGATOR
│   ├── index.html               ← Main page
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   └── app.js
│   └── data/                    ← JSON data (generated by script)
│       ├── stats.json
│       ├── referees.json
│       ├── trends.json
│       ├── insights.json
│       └── referee/
│           ├── brad-allen.json
│           ├── shawn-hochuli.json
│           └── ... (one per crew chief)
│
├── .gitignore
└── README.md                    ← This file
```

---

## 🔧 Troubleshooting

### "No module named nfl_data_py"

```powershell
pip install nfl_data_py
```

### Data script shows 0 penalties

The NFL data source may be temporarily unavailable. Wait and try again, or check:
```python
import nfl_data_py as nfl
print(nfl.import_officials([2024]).head())
```

### GitHub Actions failing

1. Check the Actions tab for error logs
2. Verify all 4 secrets are set correctly
3. Make sure `FTP_SERVER_DIR` ends with `/`

### FTP deployment not working

1. Verify FTP credentials in cPanel
2. Try connecting manually with FileZilla
3. Check HostGator firewall settings

### Site shows but data is empty

The JSON files may not have been created. Run:
```powershell
python scripts/update_data.py --full
```

### Charts not rendering

- Open browser console (F12) for errors
- Verify Chart.js CDN is accessible
- Check JSON files are valid

---

## 🔄 Regular Maintenance

### Weekly (Automatic)
- GitHub Actions runs every Tuesday
- Data is updated and deployed automatically

### Manual Update (If Needed)
```powershell
cd C:\Users\tfost\nfl-observatory
.\venv\Scripts\Activate
python scripts/update_data.py
git add frontend/data/
git commit -m "Manual data update"
git push
```

---

## 📝 Important Notes

### About the Data

- **Crew Chiefs only**: We track head referees, not individual flag-throwers
- **Accepted penalties**: Only penalties that were accepted (not declined/offsetting)
- **Regular season + playoffs**: All games included
- **Data source**: Official NFL GSIS via nflverse

### Privacy

This repo should be **private** if you plan to monetize or keep exclusive.

---

## 🚀 Next Steps

After basic setup, consider:

1. **Game Previews**: Add `/preview/` pages for upcoming matchups
2. **Historical Analysis**: Expand to 1999-present
3. **Email Alerts**: Weekly reports on referee assignments
4. **Custom Domain**: Point your domain to the HostGator folder

---

*Last updated: December 2024*
