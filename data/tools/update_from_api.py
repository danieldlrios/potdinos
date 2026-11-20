#!/usr/bin/env python3
"""Refresh the potdinos.com data files from the Potservers public API.

GitHub Actions runs this twice a day (see .github/workflows/refresh-data.yml).
It uses only the Python standard library, so there is nothing to install.

    python3 tools/update_from_api.py                  fetch, check, rewrite data/ if anything changed
    python3 tools/update_from_api.py --dry-run        fetch and check, write nothing
    python3 tools/update_from_api.py --fixtures DIR   read DIR/list.json and DIR/dinos/<id>.json
                                                      instead of the API (offline testing)

Safety rules: nothing is written unless the API answered for at least 90% of the
creatures, at least 30 official creatures came back, and the roster did not shrink
by more than 20% (use --allow-shrink once you have checked Potservers by hand).
A creature that fails to download keeps its previous file.

data/version.json keeps the patch name and date you type there ("patch",
"patch_date"). The script fills in "stats_changed" (the newest stat-change date
among official creatures) and "updated" (the day the data files last changed).

Exit status: 0 finished (with or without changes), 1 refused to write, 2 bad arguments.
"""
import argparse
import datetime as dt
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://potservers.net/api/v1"
USER_AGENT = "potdinos.com data refresh (+https://potdinos.com)"
MIN_GAP = 0.6           # seconds between requests; Potservers allows 120 a minute
TIMEOUT = 30            # seconds per request
RETRIES = 4             # tries per request before giving up on it
MIN_OFFICIAL = 30       # refuse to write if fewer official creatures come back
MAX_FAIL_SHARE = 0.10   # refuse to write if more than 10% of creatures fail
MAX_SHRINK = 0.20       # refuse to write if the roster shrinks by more than 20%
RETRY_CODES = {408, 425, 429, 500, 502, 503, 504}

SLOT_MAP = {
    "head": "head", "front limb": "front_limb", "front_limb": "front_limb",
    "back limb": "back_limb", "back_limb": "back_limb", "legs": "legs",
    "tail": "tail", "hide": "hide", "senses": "senses", "metabolism": "metabolism",
    "voice": "voice", "passives": "passives", "passive": "passives", "other": "other",
}
NOISE_METRICS = {"Recoveries Tick Rate", "Depletions Tick Rate", "Rule Group", "Groupe Rule"}
EXACT_KIND = {
    "damage": "damage", "bleed": "bleed", "venom": "venom", "toxin": "toxin", "fracture": "fracture",
    "bone break": "bone_break", "cooldown": "cooldown", "stamina cost": "stamina_cost",
    "stamina gain": "stamina_gain", "range": "range", "knockback": "knockback",
    "carry weight": "carry_weight", "slow": "slow", "full charge": "full_charge",
    "hit ramp": "hit_ramp", "no jumping": "no_jumping",
}
# Short tags used when a modded creature shares its name with another creature.
PACK_SHORT = {
    "Primordial Tyrants": "PT", "Divine Beasts": "Divine", "Jagged Fang Designs": "JFD",
    "Primal Wrath": "PW", "Ex Argilla": "EA", "Ancient Monster": "AM", "Cenozoic Timelines": "CT",
    "Tales From The Bayou": "Bayou", "El Reptileano": "ER", "Clayton's Mods": "Clayton",
    "Titanus Constructus": "TC", "The Crimson Isle": "Crimson", "Sappho's Garden": "SG",
    "Mesozoic Monsters": "MM", "Aurora Artifex": "AUR", "Prehistoric Expanse": "PX",
    "P&D's Menagerie": "P&D", "CRL Studios": "CRL",
}
TRAILING_TAG = re.compile(r"\s*\([^)]*\)\s*$")

warnings = []


def log(msg=""):
    print(msg, flush=True)


def warn(msg):
    warnings.append(msg)


# ---------------------------------------------------------------- fetching
class Source:
    """Reads the Potservers API politely, or a fixtures folder for offline tests."""

    def __init__(self, fixtures=None):
        self.fixtures = fixtures
        self.last = 0.0
        self.requests = 0

    def get(self, path):
        if self.fixtures:
            if path == "/dinos":
                name = "list.json"
            else:
                name = os.path.join("dinos", urllib.parse.unquote(path.rsplit("/", 1)[1]) + ".json")
            with open(os.path.join(self.fixtures, name), encoding="utf-8") as fh:
                return json.load(fh)
        url = API + path
        delay = 2.0
        problem = ""
        for attempt in range(1, RETRIES + 1):
            wait = MIN_GAP - (time.monotonic() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()
            self.requests += 1
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code not in RETRY_CODES:
                    raise RuntimeError(f"HTTP {e.code} for {path}") from None
                problem = f"HTTP {e.code}"
                after = (e.headers.get("Retry-After") or "").strip() if e.headers else ""
                if after.isdigit():
                    delay = max(delay, min(int(after), 120))
            except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError) as e:
                problem = f"{type(e).__name__}: {e}"
            if attempt == RETRIES:
                raise RuntimeError(f"{path}: {problem} (gave up after {RETRIES} tries)")
            log(f"    retry {attempt} for {path} in {delay:.0f}s ({problem})")
            time.sleep(delay)
            delay = min(delay * 2.5, 60.0)
        raise RuntimeError(f"{path}: unreachable")


# ---------------------------------------------------------------- conversion
def norm_num(v):
    if isinstance(v, float):
        r = round(v, 4)
        return int(r) if r == int(r) else r
    return v


def norm_slot(s, who=""):
    key = str(s or "other").strip().lower()
    out = SLOT_MAP.get(key) or SLOT_MAP.get(key.replace("_", " "))
    if not out:
        warn(f"{who}: unknown slot {s!r}, shown under Other")
        out = "other"
    return out


def norm_metrics(ms):
    out = []
    for m in ms or []:
        m = list(m) + [None] * (5 - len(m))
        name, val, unit, kind, cond = m[:5]
        if name in NOISE_METRICS:
            continue
        if name == "Critter Damage" and val == 100:
            continue
        if kind is None:
            kind = EXACT_KIND.get(str(name).strip().lower())
            if kind == "cooldown" and unit not in ("s", None):
                kind = None
        if kind == "knockback" and val == 0:
            continue
        row = [name, norm_num(val), unit, kind]
        if cond:
            row.append(cond)
        while row and row[-1] is None:
            row.pop()
        out.append(row)
    return out


def norm_ability(a, who):
    aid, name, slot, cost, default, desc, metrics, subs = (list(a) + [None] * 8)[:8]
    return [aid, name, norm_slot(slot, f"{who}/{name}"), cost, 1 if default else 0, (desc or "").strip(),
            norm_metrics(metrics), [norm_ability(s, who) for s in (subs or [])]]


def pretty_curve(row):
    parts = [p for p in row.split(".")[1:] if p not in ("Core", "Multiplier")]
    text = re.sub(r"V2", "", " ".join(parts))
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def stat_val(st, key):
    v = st.get(key)
    return v[0] if isinstance(v, list) else v


def habitat(rec):
    st = rec["st"]
    if rec.get("fly"):
        return "flyer"
    if rec.get("aq"):
        return "aquatic" if (stat_val(st, "sprint_speed") or 0) < 10 else "semi"
    return "land"


def from_api(d):
    """One Potservers creature (the "data" object) -> the record shape convert() reads."""
    def ability(a):
        return [a.get("id"), a.get("name"), a.get("slot"), a.get("unlock_cost"),
                bool(a.get("unlocked_by_default")), a.get("description") or "",
                [[m.get("name"), m.get("value"), m.get("unit"), m.get("kind"), m.get("condition")]
                 for m in (a.get("metrics") or []) if isinstance(m, dict)],
                [ability(s) for s in (a.get("sub_abilities") or []) if isinstance(s, dict)]]

    stats = {}
    for key, v in (d.get("stats") or {}).items():
        if isinstance(v, dict):
            stats[key] = [v.get("value"), v.get("unit")]
        else:
            stats[key] = [v, None]
    hot = d.get("live_hotfix")
    mod = d.get("mod")
    if not mod and d.get("modded"):
        mod = {"name": d.get("name")}
    return {
        "id": d["id"],
        "name": d.get("name") or d["id"],
        "diet": str(d.get("diet") or "").strip().lower(),
        "aq": bool(d.get("aquatic")),
        "fly": bool(d.get("flying")),
        "gs": d.get("group_slots"),
        "nest": list(d.get("nest_materials") or []),
        "chg": d.get("stats_changed_at") or "",
        "apx": bool(d.get("stats_changed_at_approximate")),
        "st": stats,
        "sub": [[s.get("name"), s.get("description"), s.get("unlock_cost")]
                for s in (d.get("subspecies") or []) if isinstance(s, dict)],
        "ab": [ability(a) for a in (d.get("abilities") or []) if isinstance(a, dict)],
        "hot": {"captured_at": hot.get("captured_at"), "curve_rows": list(hot.get("curve_rows") or [])}
        if isinstance(hot, dict) else None,
        "mod": mod or None,
    }


def pack_for(m, name):
    group = m.get("group")
    if group:
        return group
    mname = m.get("name") or ""
    if mname.startswith("PT "):
        return "Primordial Tyrants"
    return {"DivineBeastsMods": "Divine Beasts", "SergiKTO": "KTO"}.get(m.get("author") or "")


def convert(rec):
    modded = bool(rec.get("mod"))
    st = {k: norm_num(stat_val(rec["st"], k)) for k in rec["st"]}
    name = re.sub(r"(\S)\(", r"\1 (", rec["name"]).strip()
    out = {
        "id": rec["id"], "h": rec["id"].replace("_", "-").lower(), "n": name, "d": rec["diet"],
        "hab": habitat(rec), "aq": bool(rec.get("aq")), "fly": bool(rec.get("fly")), "gs": rec.get("gs"),
        "nest": rec.get("nest") or [], "chg": (rec.get("chg") or "")[:10], "hot": None, "mod": None,
        "para": 0, "st": st,
        "sub": [[s[0], s[1], s[2]] for s in rec.get("sub", [])],
        "ab": [norm_ability(a, rec["id"]) for a in rec.get("ab", [])],
    }
    hot = rec.get("hot")
    if hot and hot.get("curve_rows"):
        rows = []
        for r in hot["curve_rows"]:
            p = pretty_curve(r)
            if p and p not in rows:
                rows.append(p)
        out["hot"] = {"at": (hot.get("captured_at") or "")[:10], "rows": rows}
    if modded:
        m = rec["mod"]
        out["mod"] = {"name": m.get("name"), "author": m.get("author"), "pack": m.get("group") or pack_for(m, name),
                      "v": m.get("version"), "sku": m.get("sku")}
    if out["fly"] and not st.get("fly_speed"):
        warn(f"{rec['id']}: flying flag but no fly_speed")
    for k in ("health", "combat_weight", "sprint_speed"):
        if st.get(k) is None:
            warn(f"{rec['id']}: missing stat {k}")
    if not out["ab"]:
        warn(f"{rec['id']}: no abilities")
    return out


def tag_for(c, original):
    m = c["mod"]
    if m.get("pack") and m["pack"] in PACK_SHORT:
        return PACK_SHORT[m["pack"]]
    paren = re.search(r"\(([^)]+)\)\s*$", original)
    if paren:
        return paren.group(1).strip()
    if m.get("pack"):
        return m["pack"]
    first = (m.get("name") or "").split(" ")[0]
    if len(first) >= 2 and first.isupper():
        return first
    return m.get("author") or "Mod"


def disambiguate(recs):
    """Tag modded creatures whose name matches another creature, e.g. "Acrocanthosaurus (Absentia)"."""
    groups = {}
    for c in recs:
        groups.setdefault(TRAILING_TAG.sub("", c["n"]).strip().lower(), []).append(c)
    for members in groups.values():
        if len(members) < 2:
            continue
        for c in members:
            if c["mod"]:
                original = c["n"]
                base = TRAILING_TAG.sub("", original).strip()
                c["n"] = "{} ({})".format(base, tag_for(c, original))
    seen = {}
    for c in recs:
        seen.setdefault(c["n"].lower(), []).append(c["id"])
    for n, ids in seen.items():
        if len(ids) > 1:
            warn(f"two creatures are both called {n!r}: {ids}")


def ability_names(c):
    names = []
    for a in c["ab"]:
        names.append(a[1])
        names.extend(s[1] for s in a[7])
    return list(dict.fromkeys(names))


def index_entry(c):
    return {
        "id": c["id"], "h": c["h"], "n": c["n"], "d": c["d"], "hab": c["hab"], "gs": c["gs"], "chg": c["chg"],
        "hot": c["hot"]["at"] if c["hot"] else None,
        "mod": {"name": c["mod"]["name"], "pack": c["mod"]["pack"], "v": c["mod"]["v"]} if c["mod"] else None,
        "na": sum(1 + len(a[7]) for a in c["ab"]), "an": ability_names(c), "st": c["st"],
    }


# ---------------------------------------------------------------- files
def read_text(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return None


def read_json(path, default):
    text = read_text(path)
    if text is None:
        return default
    try:
        return json.loads(text)
    except ValueError:
        warn(f"{path} is not valid JSON; ignoring it")
        return default


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


def github_output(**values):
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        for k, v in values.items():
            fh.write(f"{k}={str(v).replace(chr(10), ' ')}\n")


def step_summary(lines):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def refuse(reason):
    log(f"REFUSED: {reason}")
    log("Nothing was written; the site keeps its current data.")
    github_output(changed=0, message="")
    step_summary(["### Data refresh refused", "", reason, "", "The site keeps its current data."])
    return 1


def name_list(names, limit=12):
    names = sorted(names, key=str.lower)
    if len(names) <= limit:
        return ", ".join(names)
    return ", ".join(names[:limit]) + f" and {len(names) - limit} more"


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="Refresh potdinos.com data from the Potservers API.")
    ap.add_argument("--data", help="data folder (default: data/ next to tools/)")
    ap.add_argument("--fixtures", help="read list.json and dinos/<id>.json from this folder instead of the API")
    ap.add_argument("--dry-run", action="store_true", help="fetch and check, but write nothing")
    ap.add_argument("--allow-shrink", action="store_true", help="accept a roster more than 20%% smaller")
    ap.add_argument("--today", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.abspath(args.data or os.path.join(root, "data"))
    today = args.today or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    src = Source(args.fixtures)

    log("Downloading the creature list from Potservers...")
    try:
        listing = src.get("/dinos")
    except Exception as e:  # noqa: BLE001 - any failure here means no update
        return refuse(f"could not download the creature list ({e}).")
    entries = [e for e in (listing.get("data") or []) if isinstance(e, dict) and e.get("id")]
    meta = listing.get("meta") or {}
    ids = list(dict.fromkeys(e["id"] for e in entries))
    n_official_listed = sum(1 for e in entries if not e.get("modded"))
    log(f"  {len(ids)} creatures listed ({n_official_listed} official).")

    old_index = read_json(os.path.join(data_dir, "index.json"), [])
    old_by_id = {c.get("id"): c for c in old_index if isinstance(c, dict)}
    old_version = read_json(os.path.join(data_dir, "version.json"), {})

    if n_official_listed < MIN_OFFICIAL:
        return refuse(f"only {n_official_listed} official creatures listed (expected at least {MIN_OFFICIAL}).")
    if old_index and len(ids) < (1 - MAX_SHRINK) * len(old_index) and not args.allow_shrink:
        return refuse(f"the roster shrank from {len(old_index)} to {len(ids)} creatures. "
                      "If Potservers really dropped them, run once with --allow-shrink.")

    recs, failed, reused, official_dates = [], [], [], []
    for i, cid in enumerate(ids, 1):
        try:
            payload = src.get("/dinos/" + urllib.parse.quote(cid, safe=""))
            d = payload.get("data", payload) if isinstance(payload, dict) else None
            if not isinstance(d, dict) or d.get("id") != cid:
                raise ValueError("unexpected response shape")
            raw = from_api(d)
            if not raw["st"]:
                raise ValueError("no stats in response")
            c = convert(raw)
            recs.append(c)
            if not c["mod"] and raw["chg"]:
                official_dates.append((raw["chg"][:10], raw["apx"]))
        except Exception as e:  # noqa: BLE001 - keep going, judged below
            failed.append(cid)
            log(f"  ! {cid}: {e}")
            old = old_by_id.get(cid)
            prev = read_json(os.path.join(data_dir, "c", old["h"] + ".json"), None) if old and old.get("h") else None
            if prev:
                recs.append(prev)
                reused.append(cid)
        if i % 25 == 0:
            log(f"  {i}/{len(ids)} downloaded")
    if src.requests:
        log(f"  {src.requests} requests made.")

    if len(failed) > MAX_FAIL_SHARE * len(ids):
        return refuse(f"{len(failed)} of {len(ids)} creatures failed to download (limit {int(MAX_FAIL_SHARE * 100)}%).")
    n_official = sum(1 for c in recs if not c["mod"])
    if n_official < MIN_OFFICIAL:
        return refuse(f"only {n_official} official creatures came back (expected at least {MIN_OFFICIAL}).")

    disambiguate(recs)
    recs.sort(key=lambda c: (1 if c["mod"] else 0, c["n"].lower(), c["id"]))
    hashes = [c["h"] for c in recs]
    if len(hashes) != len(set(hashes)):
        return refuse("two creatures map to the same file name.")

    files = {}
    index = [index_entry(c) for c in recs]
    files["index.json"] = "[\n" + ",\n".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in index) + "\n]\n"
    for c in recs:
        files["c/" + c["h"] + ".json"] = json.dumps(c, ensure_ascii=False, separators=(",", ":"))

    changed = [rel for rel, text in files.items() if read_text(os.path.join(data_dir, rel)) != text]
    c_dir = os.path.join(data_dir, "c")
    existing = sorted(f for f in os.listdir(c_dir) if f.endswith(".json")) if os.path.isdir(c_dir) else []
    orphans = [f for f in existing if "c/" + f not in files]

    new_by_id = {c["id"]: c for c in recs}
    added = [new_by_id[i]["n"] for i in new_by_id if i not in old_by_id]
    removed = [old_by_id[i].get("n", i) for i in old_by_id if i not in new_by_id]
    updated = [c["n"] for c in recs if c["id"] in old_by_id and ("c/" + c["h"] + ".json") in changed]

    # Newest stat-change date among official creatures (dates Potservers marks as approximate are skipped).
    exact = [d for d, approx in official_dates if not approx] or [d for d, _ in official_dates]
    stats_changed = max(exact, default=None) or old_version.get("stats_changed")
    new_stats_date = bool(stats_changed and stats_changed != old_version.get("stats_changed"))

    if not changed and not orphans and not new_stats_date:
        log(f"No changes: all {len(recs)} creatures match the published data.")
        summary = ["### Data refresh: no changes", "", f"{len(recs)} creatures checked against Potservers."]
        if reused:
            summary.append(f"Could not download {len(reused)} this time (kept their previous data): {name_list(reused)}")
        github_output(changed=0, message="")
        step_summary(summary)
        return 0

    n_mod = len(recs) - n_official
    version = {
        "patch": old_version.get("patch"),
        "patch_date": old_version.get("patch_date"),
        "stats_changed": stats_changed,
        "updated": today,
        "source_updated": meta.get("updated_at"),
        "official": n_official,
        "modded": n_mod,
        "packs": len({(c["mod"].get("pack") or c["mod"].get("name")) for c in recs if c["mod"]}),
    }
    for k, v in old_version.items():
        if k not in version and k != "checked":
            version[k] = v
    version_text = json.dumps(version, ensure_ascii=False, indent=1) + "\n"

    parts = []
    if updated:
        parts.append(f"{len(updated)} updated")
    if added:
        parts.append(f"{len(added)} added")
    if removed:
        parts.append(f"{len(removed)} removed")
    message = f"Data refresh {today}: " + (", ".join(parts) or "dates only")

    report = [f"### {message}", ""]
    if new_stats_date:
        report.append(f"- Official stats last changed on {stats_changed}. If a new patch came out, put its name in data/version.json.")
    if updated:
        report.append(f"- Updated: {name_list(updated)}")
    if added:
        report.append(f"- Added: {name_list(added)}")
    if removed:
        report.append(f"- Removed: {name_list(removed)}")
    if reused:
        report.append(f"- Kept previous data for {len(reused)} that failed to download: {name_list(reused)}")
    for line in report[2:]:
        log(line)

    if args.dry_run:
        log(f"Dry run: would write {len(changed)} files and delete {len(orphans)}.")
        github_output(changed=0, message="")
        return 0

    for rel in changed:
        write_text(os.path.join(data_dir, rel), files[rel])
    for f in orphans:
        os.remove(os.path.join(c_dir, f))
    write_text(os.path.join(data_dir, "version.json"), version_text)
    log(f"Wrote {len(changed)} files, deleted {len(orphans)}, updated version.json.")
    for w in warnings:
        log(f"  note: {w}")
    github_output(changed=len(changed) + len(orphans) + 1, message=message)
    step_summary(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
