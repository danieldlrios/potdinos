# Path of Titans Dinodex · potdinos.com

A fan-made, one-stop guide to Path of Titans: stats and full ability kits for every playable
dinosaur (official and modded), interactive maps of Gondwa, Panjura and Riparia, and
plain-English guides to growth, combat, nesting, quests, servers and more. It is a static site
hosted on Vercel.

## What's in this repo

| Path | What it is |
| --- | --- |
| `index.html` | The whole site: HTML, CSS and JavaScript in one file, including the guides |
| `data/index.json` | The dinosaur roster: one summary line per dinosaur |
| `data/c/<id>.json` | The full record for each dinosaur, loaded when its page opens |
| `data/version.json` | Patch name and date, plus the date the data was last refreshed |
| `api/potservers.js` | A small Vercel function that relays read-only Potservers requests if a browser blocks direct calls |
| `vercel.json` | Sends every page address to `index.html` (except files, `data/` and `api/`) |
| `sitemap.xml`, `robots.txt` | The page list for search engines, and the pointer to it |
| `favicon.ico`, `favicon-32.png`, `favicon-192.png`, `apple-touch-icon.png` | Site icons |
| `og-image.png` | The preview card Discord and other apps show for a shared link |

## Live data and pictures

Dinosaur pictures are the in-game character icons, and ability icons are the in-game ability
icons; both come from the game files through the [Potservers](https://potservers.net) public API,
along with growth-stage curves, maps and quests. The site uses no outside photos: if an icon can't
load, the square shows a lettered badge instead. Dinosaur stats and abilities come from the `data/`
files, which are refreshed by hand after each game patch. Squares and cards are tinted red for
carnivores and green for herbivores.

## Set the patch name

Open `data/version.json` on GitHub, click the pencil, change `"patch"` and `"patch_date"`
(`YYYY-MM-DD`), then **Commit changes**. Vercel redeploys in about a minute.

## Page addresses and search engines

Every page has its own address: `/dinosaurs/<name>`, `/compare/<a>/<b>`, `/maps/<map>`,
`/guides/<guide>` and `/credits`. `vercel.json` sends those addresses to `index.html`, which shows
the right page. Older links still work and move to the new address: `#` links (like
`/#tyrannosaurus`) and the earlier `/creatures/<name>` addresses.
`sitemap.xml` lists every dinosaur, guide and map for Google and Bing, and `robots.txt` points to it.
Regenerate `sitemap.xml` whenever dinosaurs are added or removed.

## Preview the site on your computer

From this folder run `npx serve -s .`, then open the address it prints. The `-s` option makes deep
links such as `/guides/stats` work the way they do on Vercel. Opening `index.html` straight from disk
will not load the data files.

## Credits

Dinosaur data, in-game icons and map data come from the [Potservers](https://potservers.net) public API.
Guides are written for this site and checked against Alderon's dev blogs, the
[Path of Titans Wiki](https://pathoftitans.wiki/pot), the community wiki and current game data.
This is an unofficial fan site, not affiliated with or endorsed by Alderon Games Pty Ltd. Path of Titans,
its dinosaurs and its artwork belong to Alderon Games; modded dinosaurs belong to their mod creators.
Suggestions: Discord **uzzislayerz** (in game: Uzzi).
