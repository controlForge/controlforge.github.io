# ⚽ WC26 Hub — World Cup 2026 Match Tracker

Live match tracker for FIFA World Cup 2026 (USA · Canada · Mexico). Features real-time scores, standings, player stats, top scorers, match timeline, and a retro arcade aesthetic with an animated soccer field hero.

**🌐 Live site:** `https://controlForge.github.io/wc26-hub/`

## Features

- **Live Match Center** — All group stage matches with filter by LIVE/FINISHED/UPCOMING
- **Animated Hero** — Canvas-based soccer field showing real players from the latest match
- **Match Detail Pages** — Full stats (possession, shots, xG, passes), timeline events, player ratings
- **Standings** — Group tables with qualification indicators
- **Top Scorers** — Aggregated from match player data
- **Auto Timezone** — All kickoff times convert to the visitor's local timezone via JS
- **AdSense Ready** — 11 ad slots across all pages
- **Affiliate Rail** — Product showcase on homepage and match detail pages
- **Mobile First** — Responsive with hamburger menu
- **Static Site** — Hosted on GitHub Pages, auto-refreshed via GitHub Actions

## Project Structure

```
wc26-hub/
├── .github/workflows/refresh.yml  # Auto-scraper (every 10 min)
├── docs/                          # Generated static site (served by GitHub Pages)
│   ├── index.html                 # Homepage
│   ├── live.html                  # Match center
│   ├── standings.html             # Group standings
│   ├── stats.html                 # Tournament stats
│   ├── 404.html                   # Custom 404
│   └── match/                     # Match detail pages
│       ├── 1.html
│       ├── 2.html
│       └── ...
├── output/                        # Scraper data cache
│   ├── live_scores.json           # Match data
│   └── standings.json             # Group standings
├── scraper.py                     # Fetches data from worldcup26.ir API
├── build_static.py                # Generates static HTML from data
├── players.json                   # 48 teams, 670+ real players
└── server.py                      # Original FastAPI server (optional, for local dev)
```

## How It Works

1. **scraper.py** fetches live data from worldcup26.ir API → writes `output/live_scores.json` + `output/standings.json`
2. **build_static.py** reads the JSON data → generates static HTML files in `docs/`
3. **GitHub Actions** runs scraper + builder every 10 minutes → auto-updates the site
4. **GitHub Pages** serves the `docs/` folder as a static website

## Quick Start (Local Dev)

```bash
git clone https://github.com/controlForge/wc26-hub.git
cd wc26-hub
pip install aiohttp
python3 scraper.py          # Fetch latest data
python3 build_static.py     # Generate static HTML
# Open docs/index.html in browser
```

## Deploy to GitHub Pages (Free)

This repo is already configured for GitHub Pages. Here's how to deploy your own copy:

### Step 1 — Fork or Clone

```bash
git clone https://github.com/controlForge/wc26-hub.git
cd wc26-hub
```

### Step 2 — Enable GitHub Pages

1. Go to your repo on GitHub → **Settings** → **Pages**
2. Under **Source**, select **Deploy from a branch**
3. Select branch: **master**, folder: **/docs**
4. Click **Save**

Your site will be live at `https://YOUR_USERNAME.github.io/wc26-hub/` in ~1 minute.

### Step 3 — Enable Auto-Refresh

The GitHub Actions workflow (`.github/workflows/refresh.yml`) runs every 10 minutes by default.

1. Go to your repo → **Settings** → **Actions** → **General**
2. Ensure **Read and write permissions** is enabled (required for the workflow to push updates)
3. The workflow will auto-commit updated data to `docs/` and `output/`

### Step 4 — Initial Data

Push the first data manually:

```bash
pip install aiohttp
python3 scraper.py
python3 build_static.py
git add docs/ output/
git commit -m "Initial data"
git push
```

## 🔗 Connecting a Custom Domain

### Option A: GitHub Pages Custom Domain (Recommended)

1. In your repo → **Settings** → **Pages** → **Custom domain**
2. Enter your domain (e.g. `wc26hub.com`)
3. Click **Save** — GitHub creates a `CNAME` file in `docs/`

4. In your domain registrar's DNS settings, create:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | 185.199.108.153 | 300 |
| A | @ | 185.199.109.153 | 300 |
| A | @ | 185.199.110.153 | 300 |
| A | @ | 185.199.111.153 | 300 |
| CNAME | www | YOUR_USERNAME.github.io | 300 |

5. Wait for DNS propagation (5-30 min), then GitHub auto-provisions a free SSL certificate.

### Option B: Cloudflare (Free SSL + CDN)

1. Sign up at [cloudflare.com](https://cloudflare.com)
2. Add your domain
3. Change nameservers at your registrar to Cloudflare's
4. In Cloudflare DNS, create the same A records pointing to GitHub Pages IPs
5. Enable **SSL/TLS → Full (Strict)** and **Always Use HTTPS**

## 💰 Setting Up Google AdSense

The site has **11 ad slots** across 5 pages. Each slot has a unique `id`:

| Page | Ad Slot ID | Location |
|------|-----------|----------|
| Home | `ad-home-hero` | Below hero |
| Home | `ad-home-nav` | Below quick nav |
| Home | `ad-home-matches` | Below match grid |
| Home | `ad-home-bottom` | Below standings/scorers |
| Live | `ad-live-filter` | Below filter tabs |
| Live | `ad-live-bottom` | Below match grid |
| Match Detail | `ad-match-top` | Below tabs |
| Match Detail | `ad-match-bottom` | Below content |
| Standings | `ad-standings-top` | Below header |
| Standings | `ad-standings` | Below group tables |
| Stats | `ad-stats-top` | Below header |
| Stats | `ad-stats-bottom` | Below content |

### Replace Placeholders with Real Ad Code

In `build_static.py`, find the `adsense()` function and update:

```python
def adsense(slot_id, css_class=""):
    return f'''<div class="ad-slot {css_class}" id="{slot_id}">
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="ca-pub-YOUR_PUBLISHER_ID"
       data-ad-slot="YOUR_SLOT_ID"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
  <script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script>
</div>'''
```

Also add the AdSense `<script>` to the `<head>` in the `page()` function in `build_static.py`.

## 🛒 Setting Up Affiliate Links

The affiliate rail appears on the homepage and match detail pages with 6 products.

In `build_static.py`, find `AFFILIATE_PRODUCTS` and update:

```python
AFFILIATE_PRODUCTS = [
    ("⚽","FIFA 24 PS5","$59.99","Best Seller"),
    ("👟","Mercurial Vapor 15","$129.99","Top Rated"),
    ...
]
```

Replace the `#` hrefs in `affiliate_rail()` with your actual affiliate links. Always use `rel="sponsored nofollow"` (already in the code).

### Affiliate Programs to Join

- **Amazon Associates** — [affiliate-program.amazon.com](https://affiliate-program.amazon.com) (easiest for physical products)
- **Fanatics** — jerseys, merch
- **Pro:Direct Soccer** — boots, balls, gloves
- **Nike** — via Impact or Rakuten

## 🔧 Updating the Site

### Manual Update

```bash
python3 scraper.py          # Fetch latest data
python3 build_static.py     # Regenerate HTML
git add docs/ output/
git commit -m "Update data"
git push
```

### Automatic Update

GitHub Actions handles this every 10 minutes. To adjust the schedule, edit `.github/workflows/refresh.yml`:

```yaml
- cron: '*/10 * * * *'  # Every 10 minutes
# Change to '*/30 * * * *' for every 30 minutes
# Change to '0 */2 * * *' for every 2 hours
```

## 📝 License

MIT — use it, modify it, monetize it.

---

**Built with ⚽ and ☕ by [controlForge](https://github.com/controlForge)**
