"""One bounded, anonymous Chromium playback diagnostic; no account/profile access.

This observes ordinary playback and emits only allowlisted diagnostic fields.
It neither exports media URLs/cookies/tokens nor solves access challenges. It is
not an archive downloader: successful playback still requires a verified full
audio acquisition before collection progress can be recorded.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, parse_qs


def media_host(url):
    parsed = urlsplit(url)
    return parsed.scheme == "https" and (parsed.hostname or "").endswith(".googlevideo.com")


def probe(video_id, channel="chrome", max_media_requests=12):
    from playwright.sync_api import sync_playwright
    observed = []
    dispatched = 0
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=channel, headless=True,
            args=["--proxy-server=direct://", "--proxy-bypass-list=*"], timeout=30000)
        try:
            context = browser.new_context(locale="en-US", service_workers="block")
            page = context.new_page()
            def admit(route):
                nonlocal dispatched
                if media_host(route.request.url):
                    dispatched += 1
                    if dispatched > max_media_requests:
                        return route.abort()
                return route.continue_()
            def response(response):
                if media_host(response.url) and len(observed) < max_media_requests:
                    query = parse_qs(urlsplit(response.url).query)
                    observed.append({"status":response.status,
                        "format_id":query.get("itag", [""])[0],
                        "content_type":response.headers.get("content-type", ""),
                        "content_length":response.headers.get("content-length", "")})
            context.route("**/*", admit)
            page.on("response", response)
            page.goto("https://www.youtube.com/watch?v="+video_id,
                      wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            player = page.evaluate("""() => {
                const p=window.ytInitialPlayerResponse || {};
                const v=document.querySelector('video');
                return {status:p.playabilityStatus?.status || 'UNKNOWN',
                  video_id:p.videoDetails?.videoId || '',
                  live:!!p.videoDetails?.isLiveContent,
                  duration_s:Number(p.videoDetails?.lengthSeconds)||null,
                  video_ready_state:v?.readyState ?? null};
            }""")
            if player["status"] == "OK" and player["video_id"] == video_id:
                page.evaluate("""() => {
                    const p=document.getElementById('movie_player');
                    if(p?.playVideo) p.playVideo();
                    const v=document.querySelector('video');
                    if(v){v.muted=true;v.play().catch(()=>{});}
                }""")
                page.wait_for_timeout(5000)
                player["video_ready_state"] = page.evaluate(
                    "document.querySelector('video')?.readyState ?? null")
            return {"schema_version":1,"captured_at":datetime.datetime.now(
                datetime.timezone.utc).isoformat(), "video_id":video_id,
                "browser_version":browser.version,"channel":channel,
                "anonymous_context":True,"persistent_profile":False,
                "player":player,"media_responses":observed,
                "media_request_limit":max_media_requests,
                "archive_download_completed":False}
        finally:
            browser.close()


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video-id",required=True)
    ap.add_argument("--channel",choices=("chrome","msedge"),default="chrome")
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}",args.video_id):
        ap.error("Invalid video ID")
    # An explicit command is required. Importing the module starts no browser.
    try:
        record=probe(args.video_id,args.channel)
    except Exception as exc:
        # Playwright errors can include URLs/headers; never emit their text.
        record={"schema_version":1,"video_id":args.video_id,
                "error_type":type(exc).__name__,"archive_download_completed":False}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(record))
    return 0 if record.get("player",{}).get("status")=="OK" else 3


if __name__=="__main__":
    raise SystemExit(main())
