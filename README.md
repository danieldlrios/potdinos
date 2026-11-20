# PoT Dinos · potdinos.com

A fan-made reference for Path of Titans: stats and full ability kits for every playable
creature, official and modded, with side-by-side comparisons. It is a static site hosted on
Vercel. A GitHub Action refreshes the data from the Potservers public API twice a day.

## What's in this repo

| Path | What it is |
| --- | --- |
| `index.html` | The whole site: HTML, CSS and JavaScript in one file |
| `data/index.json` | The roster: one summary line per creature |
| `data/c/<id>.json` | The full record for each creature, loaded when its page opens |
| `data/version.json` | Patch name and date (you edit these), plus dates and counts the refresh fills in |
| `tools/update_from_api.py` | Downloads fresh data from Potservers (Python 3, standard library only) |
| `.github/workflows/refresh-data.yml` | Runs the download twice a day and commits anything that changed |
| `favicon.ico`, `favicon-32.png`, `favicon-192.png`, `apple-touch-icon.png` | Site icons, in the same style as the creature badges |
| `og-image.png` | The preview card Discord and other apps show for a shared link, drawn with the site's own styles |

## Set the patch name

Open `data/version.json` on GitHub, click the pencil, change `"patch"` and `"patch_date"`
(`YYYY-MM-DD`), then **Commit changes**. Vercel redeploys in about a minute. The refresh
keeps whatever you type there.

## Refresh the data by hand

On GitHub: **Actions → Refresh dino data → Run workflow**. On your computer:
`python3 tools/update_from_api.py` (add `--dry-run` to see what would change without writing).

The refresh writes nothing unless Potservers answered for at least 90% of creatures, returned
at least 30 official ones, and the roster did not shrink by more than 20%. A creature that
fails to download keeps its previous data.

## Preview the site on your computer

From this folder run `python3 -m http.server 8000`, then open <http://localhost:8000>.
Opening `index.html` straight from disk will not load the data files.

## Credits

Stats and abilities come from the [Potservers](https://potservers.net) public API.
Path of Titans and its creatures belong to Alderon Games; this site is unofficial.
