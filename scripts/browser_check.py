"""Headless browser verification; screenshots stay local in data/verification."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'data'/'verification'
OUT.mkdir(parents=True,exist_ok=True)
errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto('http://127.0.0.1:8787',wait_until='networkidle')
    page.wait_for_selector('flutter-view',timeout=30000)
    page.wait_for_timeout(1500)
    page.evaluate("document.querySelector('flt-semantics-placeholder')?.click()")
    page.wait_for_timeout(600)
    page.screenshot(path=str(OUT/'desktop-home.png'))
    print('HOME TEXT',page.locator('body').inner_text()[:3500],flush=True)
    page.get_by_text('에셋 보관함',exact=True).first.click()
    page.wait_for_timeout(900)
    page.screenshot(path=str(OUT/'desktop-assets.png'))
    page.get_by_text('나의 다이어리',exact=True).first.click()
    page.wait_for_timeout(1800)
    frame=page.frame_locator('iframe')
    frame.locator('canvas').wait_for(timeout=15000)
    assert frame.locator('#status').inner_text()=='',frame.locator('#status').inner_text()
    page.screenshot(path=str(OUT/'desktop-diary.png'))
    page.get_by_role('button',name='스티커 만들기',exact=True).first.click()
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT/'desktop-upload.png'))
    page.get_by_role('button',name='취소',exact=True).click()
    page.set_viewport_size({'width':390,'height':844})
    page.wait_for_timeout(1200)
    page.screenshot(path=str(OUT/'mobile-diary.png'))
    browser.close()
(OUT/'browser-report.json').write_text(json.dumps({'errors':errors,'checked':['home','assets','diary GLB','upload dialog','mobile diary']},ensure_ascii=False,indent=2),encoding='utf-8')
print('BROWSER ERRORS',errors)
assert not errors,errors
