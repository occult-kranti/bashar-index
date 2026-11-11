import asyncio, json
from playwright.async_api import async_playwright
BASE = '/tmp/claude-0/-home-claude/61a86037-21c7-5e0d-95ce-b1bc19051ed9/scratchpad/harness'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium', args=['--no-sandbox'])
        for name, w, h in (('wide', 1100, 900), ('narrow', 400, 800)):
            pg = await b.new_page(viewport={'width': w, 'height': h})
            errs = []
            pg.on('pageerror', lambda e: errs.append('PAGEERROR ' + str(e)))
            pg.on('console', lambda m: errs.append('CONSOLE ' + m.type + ' ' + m.text) if m.type in ('error', 'warning') else None)
            await pg.goto(f'file://{BASE}/harness.html')
            await pg.wait_for_timeout(600)
            info = await pg.evaluate('''() => ({
              scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth,
              kpis: [...document.querySelectorAll('.ci-kn')].map(e => e.textContent),
              take: document.querySelector('.ci-take').textContent.replace(/\\s+/g,' ').trim(),
              observed: document.querySelector('.ci-eyebrow').textContent.trim(),
              chRows: document.querySelectorAll('#ch-table tbody tr').length,
              vdRows: document.querySelectorAll('#vd-table tbody tr').length,
              plRows: document.querySelectorAll('#pl-table tbody tr').length,
              bars: document.querySelectorAll('#entity-bars .ci-bar-row').length,
              dots: document.querySelectorAll('#audience-chart circle').length,
              segs: [...document.querySelectorAll('.ci-seg')].map(e => e.style.flexGrow),
              legendNums: [...document.querySelectorAll('.ci-n')].map(e => e.textContent),
              ch1: document.querySelector('#ch-table tbody tr')?.innerText.replace(/\\s+/g,' ').slice(0,160),
              vd1: document.querySelector('#vd-table tbody tr')?.innerText.replace(/\\s+/g,' ').slice(0,160),
              pl1: document.querySelector('#pl-table tbody tr')?.innerText.replace(/\\s+/g,' ').slice(0,160),
              count1: document.querySelector('#ch-count').textContent, count2: document.querySelector('#vd-count').textContent
            })''')
            print(name, json.dumps(info, ensure_ascii=False, indent=1))
            # interactions: sort, search, filter, tooltip
            await pg.click('#ch-table th[data-field="person_name"] .ci-sort')
            await pg.fill('#vd-q', 'ryok')
            await pg.check('#vd-chan')
            await pg.wait_for_timeout(200)
            print(name, 'after interactions:', await pg.evaluate('''() => ({ch: document.querySelector('#ch-table tbody tr td').innerText, sort: document.querySelector('#ch-table th[aria-sort]')?.dataset.field, vd: document.querySelectorAll('#vd-table tbody tr').length, vdc: document.querySelector('#vd-count').textContent})'''))
            await pg.hover('#audience-chart rect >> nth=2')
            await pg.wait_for_timeout(150)
            print(name, 'tooltip:', await pg.evaluate("() => document.querySelector('#audience-chart .ci-tip')?.innerText.replace(/\\n/g,' | ')"))
            await pg.fill('#vd-q', ''); await pg.uncheck('#vd-chan')
            await pg.screenshot(path=f'{BASE}/shot_{name}.png', full_page=True)
            print(name, 'errors:', errs)
            await pg.close()
        await b.close()
asyncio.run(main())
