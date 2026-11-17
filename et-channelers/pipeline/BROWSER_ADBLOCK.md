# Isolated Chromium with both project extensions

`chromium_extensions.py` validates two already-installed local MV3 extensions.
It does not install packages or grant source, receiver, GPU or download admission.
The official adblocker package must be verified separately and remain unchanged.

## Official package installation

The pinned package is [uBlock Origin Lite 2026.1116.1650](https://github.com/uBlockOrigin/uBOL-home/releases/tag/2026.1116.1650), the maintainer's Manifest V3 Chromium release. Its official ZIP is 9,099,013 bytes with GitHub-published SHA-256 `67e084b34470c51c08fa9314b118b8cb73df3a72e90c6a3b536d041c92e61bbc`. The manifest requires Chrome 122 or newer; the tested project Chromium is 151.0.7922.34. [Playwright recommends its Chromium build for sideloaded extensions](https://playwright.dev/python/docs/chrome-extensions), since branded Chrome/Edge removed the required command-line flags.

Run from the repository root, using the actual owned browser's major version:

```powershell
$EtTools = Join-Path $env:USERPROFILE 'et-channelers-tools'
& "$EtTools\venv\Scripts\python.exe" -I et-channelers/pipeline/install_adblock.py `
    --tools-root $EtTools --browser-major 151 --download
```

The installer fetches only the pinned official asset if it is absent, checks size/SHA-256 before extraction, rejects escaping/duplicate/device/symlink entries and bounds expansion. It keeps the original package and bundled license unchanged, under the tools root rather than Git. The adjacent receipt records every installed file hash and actual enabled rulesets. The current package expands to 32,948,819 bytes; archive plus package fit the 64 MB reservation.

This release's default is **Optimal** mode. Its default-enabled static rulesets are `ublock-filters`, `easylist`, `easyprivacy`, `pgl`, `ublock-badware` and `urlhaus-full`. Read the installed manifest/actual runtime rather than older single-ruleset or Basic-default examples. Permissions and host access belong to the isolated project profile. No package patch or extra debug permission is required for the recorded local test.

## Project browser factory

```python
from playwright.async_api import async_playwright
from pipeline.chromium_extensions import launch_project_chromium

async with async_playwright() as playwright:
    async with launch_project_chromium(
        playwright,
        owned_profile_path=new_empty_profile,
        executable_path=owned_chromium_executable,
        downloader_dir=verified_downloader_package,
        adblocker_dir=verified_adblocker_package,
        headless=False,
        launch_args=("--mute-audio", "--disable-background-networking"),
    ) as session:
        # No source navigation is performed by the factory.
        # Install the separately approved job's network controls before navigating.
        context = session.context
        downloader = session.downloader_worker
        blocker_id = session.adblocker.extension_id
```

The profile must be absent or empty, with an existing parent. Existing personal
profiles, profile/extension overrides and startup URL arguments are refused.
Both extension flags are generated together. Downloader selection requires its
fixed public ID and exact declared worker path; adblocker selection checks the
actual runtime version and manifest path and reports the loaded ID separately.
A single leading slash in an official worker path is extension-root-relative.

The context closes in `finally` while the outer Playwright transport is alive,
including validation failures. Profile deletion remains the caller's duty.
An uncertain close is reported; if the job already failed, its original exception
is preserved. Worker discovery is bounded (20 seconds by default, at most 60 for
each lookup). Website service workers default to `block`; this does not replace
request isolation or a network proxy for local-only tests.

The caller must account for package/profile growth and the Playwright browser
cache even when that cache is outside the usual managed roots. Existing source
cooldowns, receiver leases and native protocol checks remain authoritative.
Successful ad blocking or extension startup is not proof of native audio access,
SPS1 acceptance, full-file completion, or Drive publication.

The [dated browser evidence](../research/chromium-adblock-2026-11-17.md) separates the successful local A/B test, public publisher metadata observations and remaining source restrictions. The public snapshot uses an allowlisted, hash-checked local audit receipt; it never upgrades local compatibility into full-file source acceptance.
