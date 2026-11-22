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
| `data/version.json` | The latest game update shown on the home page (patch and hotfix), and the dates the data is from |
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
files, which are refreshed by hand after each game patch and hotfix. Squares and cards are tinted red for
carnivores and green for herbivores.

## Fight matchup

On the Dinosaurs tab, **Fight matchup** (in the filter bar) lets you tap 2 to 4 dinosaurs and
compare them for a fight. The page shows every stat with your dinosaur's column highlighted, and a
head-to-head card for each opponent: damage per hit after combat weight and armor, hits to kill, and
who wins a straight trade of each side's chosen attack. Damage follows the formula the community wiki
documents: base damage × attacker weight ÷ defender weight ÷ defender armor (armor-piercing damage
skips armor). Bleed, abilities and other effects are not counted, and the page says so.

## The "Latest update" notice

The home page shows the newest game update, linked to its notes, and the date the site's numbers are
from. Both come from `data/version.json`: open it on GitHub, click the pencil, edit, then
**Commit changes**. Vercel redeploys in about a minute.

- `"patch"`, `"patch_date"` (`YYYY-MM-DD`) and `"patch_url"`: the last full game patch and Alderon's
  blog post about it, for example `"patch_url": "https://pathoftitans.com/blog/microraptor-released"`.
- `"hotfix"`, `"hotfix_date"` and `"hotfix_url"`: a hotfix that came out after that patch, for example
  `"hotfix": "Patch 53835 Hotfix 16"`. Alderon posts hotfix notes only in its Discord, so without a
  `"hotfix_url"` the notice opens the official Path of Titans Discord (https://discord.gg/P6t8FGn).

The notice shows whichever of the two is newer. When the next full patch comes out, update the three
patch lines and delete the three hotfix lines.

**Stats as of** shows the later of `"source_updated"` (when Potservers last changed the data these files
were made from) and `"stats_as_of"` (optional, `YYYY-MM-DD`: the day the numbers were last confirmed to
match the game).

## Maps

A first visit to each map shows only the region names. Visitors switch on Landmarks, Flights and item
types themselves, and those choices are saved on their device for each map until they switch them off.
Links into a map (such as "Find them on the map" on a dinosaur page) show what they point to without
changing those saved choices.

## Page addresses and search engines

Every page has its own address: `/dinosaurs/<name>`, `/compare/<a>/<b>`,
`/matchup/<you>/<b>/<c>/<d>` (a fight matchup of 2 to 4 dinosaurs, the one you play first),
`/maps/<map>`, `/guides/<guide>` and `/credits`. Compare and matchup pages are marked `noindex`,
because there are thousands of combinations. `vercel.json` sends those addresses to `index.html`, which shows
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
