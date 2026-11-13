#!/usr/bin/env python3
"""Count YouTube fetches and transcripts in the session's sub-agent logs (read-only)."""
import json, glob, re, os, sys, collections as C

J = "/root/.claude/projects/-home-claude/61a86037-21c7-5e0d-95ce-b1bc19051ed9"
OUT = sys.argv[1] if len(sys.argv) > 1 else None

VID = re.compile(r"(?:[?&]v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})")


def blocks(obj):
    c = (obj.get("message") or {}).get("content")
    if isinstance(c, list):
        for b in c:
            if isinstance(b, dict):
                yield b
    elif isinstance(c, str):
        yield {"type": "text", "text": c}


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(x.get("text", "") for x in content if isinstance(x, dict) and x.get("type") == "text")
    return ""


def load(path):
    uses, results = {}, {}
    for line in open(path, encoding="utf-8"):
        try:
            o = json.loads(line)
        except Exception:
            continue
        ts = o.get("timestamp")
        for b in blocks(o):
            if b.get("type") == "tool_use":
                uses[b["id"]] = (b.get("name"), b.get("input") or {}, ts)
            elif b.get("type") == "tool_result":
                results[b.get("tool_use_id")] = (text_of(b.get("content")), bool(b.get("is_error")))
    return uses, results


FAIL = re.compile(r"client_error|Request failed|blocked|cannot be fetched|unable to fetch|ECONN|timed out|403|404|Error:|not allowed|failed", re.I)


def classify(txt, is_err):
    """ok / fail by result text."""
    if is_err:
        return "fail"
    t = txt.strip()
    if len(t) < 400 and FAIL.search(t):
        return "fail"
    if len(t) < 120:
        return "fail"
    return "ok"


rows = []
for p in sorted(glob.glob(J + "/subagents/*.jsonl")):
    aid = os.path.basename(p).replace(".jsonl", "")
    meta = {}
    try:
        meta = json.load(open(p.replace(".jsonl", ".meta.json")))
    except Exception:
        pass
    uses, results = load(p)
    for uid, (name, inp, ts) in uses.items():
        res, err = results.get(uid, ("", False))
        url = inp.get("url") or ""
        alex = inp.get("alexandria")
        rows.append(dict(agent=aid, desc=meta.get("description", ""), atype=meta.get("agentType", ""),
                         tool=name, url=url, alex=alex, ts=ts, status=classify(res, err), rlen=len(res),
                         rsnip=res[:160].replace("\n", " ")))

print("total sub-agent tool calls parsed:", len(rows))

# --- 1. youtubetotranscript.com fetches (transcripts) -------------------------
yt = [r for r in rows if "youtubetotranscript" in r["url"]]
print("\n[1] youtubetotranscript.com fetch attempts:", len(yt))
by_tool = C.Counter((r["tool"], r["status"]) for r in yt)
print("   by tool/status:", dict(by_tool))
ids_all, ids_ok = set(), set()
for r in yt:
    m = VID.search(r["url"])
    if m:
        ids_all.add(m.group(1))
        if r["status"] == "ok":
            ids_ok.add(m.group(1))
print("   distinct video ids attempted:", len(ids_all), "| with >=1 ok fetch:", len(ids_ok))
print("   attempted but never ok:", len(ids_all - ids_ok))

# per-agent breakdown
print("\n   per agent (transcript fetches):")
pa = C.defaultdict(lambda: [0, 0, set(), ""])
for r in yt:
    a = pa[r["agent"]]
    a[3] = r["desc"]
    a[0 if r["status"] == "ok" else 1] += 1
    m = VID.search(r["url"])
    if m and r["status"] == "ok":
        a[2].add(m.group(1))
for k, (ok, fail, ids, d) in sorted(pa.items(), key=lambda kv: kv[1][3]):
    print(f"   {k[:14]} ok={ok:3d} fail={fail:3d} distinct_ok_ids={len(ids):3d}  {d[:60]}")

# --- 2. other youtube.com page fetches ----------------------------------------
oth = [r for r in rows if re.search(r"youtube\.com|youtu\.be", r["url"]) and "youtubetotranscript" not in r["url"]]
print("\n[2] direct youtube.com/youtu.be fetch attempts:", len(oth))
print("   by tool/status:", dict(C.Counter((r["tool"], r["status"]) for r in oth)))
kinds = C.Counter()
for r in oth:
    u = r["url"]
    k = "watch" if "watch?v=" in u or "youtu.be" in u else "shorts" if "/shorts/" in u else "playlist" if "playlist" in u else "channel/handle" if re.search(r"/@|/channel/|/c/|/user/", u) else "other"
    kinds[(k, r["status"])] += 1
print("   kinds:", dict(kinds))

# --- 3. Alexandria youtube-com provider (channel/video crawl) ------------------
al = []
for r in rows:
    a = r["alex"]
    if not a:
        continue
    for x in (a if isinstance(a, list) else [a]):
        if isinstance(x, dict) and "youtube" in str(x.get("provider", "")).lower():
            al.append((r, x))
print("\n[3] Alexandria youtube* provider calls:", len(al))
print("   provider/capability:", dict(C.Counter((x.get("provider"), x.get("capability")) for _, x in al)))
print("   status:", dict(C.Counter(r["status"] for r, _ in al)))

# --- 4. other tool counts that touch youtube -----------------------------------
srch = [r for r in rows if r["tool"] in ("WebSearch", "mcp__Firecrawl__firecrawl_search")]
print("\n[4] search calls (all topics):", len(srch))

if OUT:
    json.dump(rows, open(OUT, "w"))
    print("\nwrote", OUT)
