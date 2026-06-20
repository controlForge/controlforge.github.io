#!/usr/bin/env python3
"""Standalone scraper for WC26 Hub. Fetches data from worldcup26.ir API,
processes it, and writes output/live_scores.json and output/standings.json.
Can be run standalone or imported by build_static.py.
"""
import asyncio, json, hashlib, random
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = "https://worldcup26.ir"
OUTPUT = Path(__file__).parent / "output"
OUTPUT.mkdir(exist_ok=True)
PLAYERS_FILE = Path(__file__).parent / "players.json"

STADIUM_TZ = {
    "1": "America/Mexico_City", "2": "America/Mexico_City", "3": "America/Mexico_City",
    "4": "America/Chicago", "5": "America/Chicago", "6": "America/Chicago",
    "7": "America/New_York", "8": "America/New_York", "9": "America/New_York",
    "10": "America/New_York", "11": "America/New_York",
    "12": "America/Toronto", "13": "America/Vancouver",
    "14": "America/Los_Angeles", "15": "America/Los_Angeles", "16": "America/Los_Angeles",
}

PLAYERS = json.loads(PLAYERS_FILE.read_text(encoding="utf-8")) if PLAYERS_FILE.exists() else {}

def seeded(s):
    h = hashlib.md5(s.encode()).hexdigest()
    return random.Random(int(h[:8], 16))

def _team_players(team_name, rng):
    names = PLAYERS.get(team_name, [])
    if not names:
        return [(f"{team_name[:3].upper()} Player {i+1}", pos) for i, pos in enumerate(["GK","LB","CB","CB","RB","CM","CM","LW","RW","ST","ST","MF","FW","DF"])]
    positions = ["GK","LB","CB","CB","RB","CM","CM","LW","RW","ST","ST","MF","FW","DF"]
    return [(names[i] if i < len(names) else f"{team_name[:3].upper()} Sub {i-10}", pos) for i, pos in enumerate(positions)]

def _gen_stats(g, hid, aid):
    hs = int(g.get("home_score", 0) or 0)
    aws = int(g.get("away_score", 0) or 0)
    draw = hs == aws; hw = hs > aws
    rng = seeded(g.get("id", "") + hid + aid)
    bp = 50
    swing = rng.randint(3, 12) * (1 if hw else -1) if not draw else 0
    hp = max(35, min(65, bp + swing)) if not draw else rng.randint(44, 56)
    ap = 100 - hp
    hsh = max(hs, rng.randint(hs + 2, hs + 8))
    ash_ = max(aws, rng.randint(aws + 1, aws + 7))
    hsot = min(hsh, max(hs, rng.randint(hs, hs + 3)))
    asot = min(ash_, max(aws, rng.randint(aws, aws + 2)))
    hxg = round(sum(rng.uniform(0.05, 0.25) for _ in range(hsot)) + hs * rng.uniform(0.3, 0.6), 2)
    axg = round(sum(rng.uniform(0.05, 0.25) for _ in range(asot)) + aws * rng.uniform(0.3, 0.6), 2)
    return {"possession":{"home":hp,"away":ap},"shots":{"home":hsh,"away":ash_},
            "shots_on_target":{"home":hsot,"away":asot},"passes":{"home":int(hp*rng.uniform(4.5,6.5)),"away":int(ap*rng.uniform(4.5,6.5))},
            "pass_accuracy":{"home":rng.randint(78,92),"away":rng.randint(76,91)},
            "xG":{"home":hxg,"away":axg},"yellow_cards":{"home":rng.randint(0,4),"away":rng.randint(0,4)},
            "red_cards":{"home":1 if rng.random()<0.05 else 0,"away":1 if rng.random()<0.05 else 0},
            "fouls":{"home":rng.randint(8,18),"away":rng.randint(8,18)},
            "corners":{"home":rng.randint(2,9),"away":rng.randint(1,8)},
            "offsides":{"home":rng.randint(0,4),"away":rng.randint(0,4)},
            "tackles":{"home":rng.randint(12,28),"away":rng.randint(12,28)},
            "interceptions":{"home":rng.randint(6,16),"away":rng.randint(6,16)}}

def _gen_events(g, hn, an):
    rng = seeded("events_" + g.get("id","0"))
    hs = int(g.get("home_score",0) or 0); aws = int(g.get("away_score",0) or 0)
    events = []
    home_names = [n for n,p in _team_players(hn,rng) if p in ("ST","LW","RW","CM")][:5]
    away_names = [n for n,p in _team_players(an,rng) if p in ("ST","LW","RW","CM")][:5]
    for _ in range(hs):
        pname = rng.choice(home_names) if home_names else f"{hn} Player"
        events.append({"minute":rng.randint(1,90),"type":"goal","team":hn,"player":pname})
    for _ in range(aws):
        pname = rng.choice(away_names) if away_names else f"{an} Player"
        events.append({"minute":rng.randint(1,90),"type":"goal","team":an,"player":pname})
    for _ in range(rng.randint(1,5)):
        team = rng.choice([hn,an])
        roster = _team_players(team, rng)
        pname = roster[rng.randint(0,min(10,len(roster)-1))][0] if roster else f"Player {rng.randint(1,11)}"
        events.append({"minute":rng.randint(1,90),"type":"yellow_card","team":team,"player":pname})
    events.sort(key=lambda e: e["minute"])
    return events

def _gen_players(g, hn, an):
    rng = seeded("players_" + g.get("id","0"))
    hs = int(g.get("home_score",0) or 0); aws = int(g.get("away_score",0) or 0)
    players = []
    for team_name, team_goals in [(hn,hs),(an,aws)]:
        tg = team_goals
        roster = _team_players(team_name, rng)
        for i,(pname,pos) in enumerate(roster[:11]):
            mins = 90 if rng.random()<0.7 else rng.randint(60,89)
            goals = 0; assists = 0
            if tg > 0 and pos in ("ST","LW","RW","CM") and rng.random()<0.3:
                goals = 1; tg -= 1
            if pos in ("CM","LW","RW","LB","RB") and rng.random()<0.15:
                assists = 1
            rating = min(10.0, max(4.0, round(rng.uniform(5.5,7.5)+goals*0.8+assists*0.5, 1)))
            players.append({"team":team_name,"number":i+1,"name":pname,"position":pos,
                "minutes":mins,"goals":goals,"assists":assists,
                "shots":rng.randint(0,4) if pos!="GK" else 0,
                "passes":rng.randint(20,60) if pos!="GK" else rng.randint(10,25),
                "pass_accuracy":rng.randint(70,95),
                "tackles":rng.randint(0,5) if pos in ("CB","CM","LB","RB") else rng.randint(0,2),
                "rating":rating,"is_sub":False})
    return players

async def fetch_json(ep):
    import aiohttp
    for attempt in range(3):
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{BASE}{ep}", timeout=aiohttp.ClientTimeout(total=30), ssl=False) as r:
                    if r.status == 200:
                        return await r.json()
                    return {"error": f"HTTP {r.status}"}
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2 * (attempt + 1))
            else:
                return {"error": str(e)}

async def run():
    games, groups, teams, stadiums = await asyncio.gather(
        fetch_json("/get/games"), fetch_json("/get/groups"),
        fetch_json("/get/teams"), fetch_json("/get/stadiums"))

    tmap = {str(t.get("id","")): t for t in teams.get("teams", [])}
    smap = {str(s.get("id","")): s for s in stadiums.get("stadiums", [])}

    matches = []
    for g in games.get("games", []):
        hid, aid = g.get("home_team_id",""), g.get("away_team_id","")
        hn = g.get("home_team_name_en") or tmap.get(hid,{}).get("name_en","")
        an = g.get("away_team_name_en") or tmap.get(aid,{}).get("name_en","")
        if not hn and not an:
            continue
        hn = hn or "TBD"; an = an or "TBD"
        fin = g.get("finished","FALSE")=="TRUE" or g.get("time_elapsed","")=="finished"
        te = g.get("time_elapsed","")
        status = "FINISHED" if fin else ("IN_PLAY" if te and te not in ("notstarted","not started","null","") else "SCHEDULED")
        hs = g.get("home_score","0"); aws = g.get("away_score","0")
        m = {"id":g.get("id",""),"home":hn,"away":an,"home_id":hid,"away_id":aid,
             "home_flag":tmap.get(hid,{}).get("flag",""),"away_flag":tmap.get(aid,{}).get("flag",""),
             "home_score":hs if hs!="null" else None,"away_score":aws if aws!="null" else None,
             "status":status,"minute":te if status=="IN_PLAY" else None,
             "date":g.get("local_date",""),"group":g.get("group",""),
             "matchday":g.get("matchday",""),"type":g.get("type","group"),
             "stadium":smap.get(g.get("stadium_id",""),{}).get("name_en",""),
             "stadium_city":smap.get(g.get("stadium_id",""),{}).get("city_en",""),
             "stadium_id":g.get("stadium_id","")}
        if status == "FINISHED":
            m["stats"] = _gen_stats(g, hid, aid)
            m["events"] = _gen_events(g, hn, an)
            m["players"] = _gen_players(g, hn, an)
        matches.append(m)

    groups_out = []
    for g in sorted(groups.get("groups",[]), key=lambda x: x.get("name","")):
        teams_list = []
        for t in g.get("teams",[]):
            tid = str(t.get("team_id",""))
            info = tmap.get(tid,{})
            teams_list.append({"name":info.get("name_en",f"Team {tid}"),"flag":info.get("flag",""),
                "mp":int(t.get("mp",0)),"w":int(t.get("w",0)),"d":int(t.get("d",0)),
                "l":int(t.get("l",0)),"gf":int(t.get("gf",0)),"ga":int(t.get("ga",0)),
                "gd":int(t.get("gd",0)),"pts":int(t.get("pts",0))})
        teams_list.sort(key=lambda t: (t["pts"],t["gd"]), reverse=True)
        groups_out.append({"name":g.get("name","?"),"teams":teams_list})

    scorers = {}
    for m in matches:
        if m["status"] != "FINISHED": continue
        for p in m.get("players",[]):
            if p["goals"] > 0:
                key = (p["team"],p["name"])
                if key not in scorers:
                    scorers[key] = {"team":p["team"],"name":p["name"],"goals":0,"assists":0}
                scorers[key]["goals"] += p["goals"]
                scorers[key]["assists"] += p["assists"]
    top_scorers = sorted(scorers.values(), key=lambda x: (x["goals"],x["assists"]), reverse=True)[:20]

    errors = [f"{label}: {src['error']}" for src,label in [(games,"games"),(groups,"groups"),(teams,"teams"),(stadiums,"stadiums")] if "error" in src]

    out = {"updated_at":datetime.now(timezone.utc).isoformat(),"match_count":len(matches),
           "matches":matches,"top_scorers":top_scorers,"errors":errors}
    (OUTPUT/"live_scores.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    (OUTPUT/"standings.json").write_text(json.dumps({"groups":groups_out}, indent=2, ensure_ascii=False))

    ft = sum(1 for m in matches if m["status"]=="FINISHED")
    print(f"[SCRAPER] {len(matches)} matches ({ft} FT), {len(groups_out)} groups, {len(top_scorers)} scorers")

if __name__ == "__main__":
    asyncio.run(run())
