# Path of Titans Dinodex · potdinos.com

A fan-made, one-stop guide to Path of Titans: stats and full ability kits for every playable
creature (official and modded), interactive maps of Gondwa, Panjura and Riparia, and
plain-English guides to growth, combat, nesting, quests, servers and more. It is a static site
hosted on Vercel.

## What's in this repo

| Path | What it is |
| --- | --- |
| `index.html` | The whole site: HTML, CSS and JavaScript in one file, including the guides |
| `data/index.json` | The creature roster: one summary line per creature |
| `data/c/<id>.json` | The full record for each creature, loaded when its page opens |
| `data/version.json` | Patch name and date, plus the date the data was last refreshed |
| `api/potservers.js` | A small Vercel function that relays read-only Potservers requests if a browser blocks direct calls |
| `favicon.ico`, `favicon-32.png`, `favicon-192.png`, `apple-touch-icon.png` | Site icons |
| `og-image.png` | The preview card Discord and other apps show for a shared link |

## Live data

Ability icons, growth-stage curves, maps and quests load straight from the
[Potservers](https://potservers.net) public API when a page needs them. Creature pictures are
freely licensed lead images from each creature's Wikipedia article (hosted on Wikimedia Commons),
credited with author and license on the site's Credits & legal page (`#credits`). Creature stats
and abilities come from the `data/` files, which are refreshed by hand after each game patch.

## Set the patch name

Open `data/version.json` on GitHub, click the pencil, change `"patch"` and `"patch_date"`
(`YYYY-MM-DD`), then **Commit changes**. Vercel redeploys in about a minute.

## Preview the site on your computer

From this folder run `python3 -m http.server 8000`, then open <http://localhost:8000>.
Opening `index.html` straight from disk will not load the data files.

## Credits

Creature data, ability icons and map data come from the [Potservers](https://potservers.net) public API.
Creature pictures come from [Wikimedia Commons](https://commons.wikimedia.org) under their stated free licenses.
Guides are written for this site with credit to the [Path of Titans Wiki](https://pathoftitans.wiki/pot).
This is an unofficial fan site, not affiliated with or endorsed by Alderon Games Pty Ltd. Path of Titans and its creatures belong to Alderon Games.
Suggestions: Discord **uzzislayerz** (in game: Uzzi).
