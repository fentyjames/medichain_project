"""Screenshot new/fixed pages."""
import os, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT  = r"E:\medichain_project\screenshots"

PAGES = [
    ("new_01_dashboard",      "/dashboard/"),
    ("new_02_block_detail",   "/blockchain/blocks/3/"),
    ("new_03_zk_dashboard",   "/zk-proofs/"),
    ("new_04_api_docs",       "/api/docs/"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    page.goto(f"{BASE}/accounts/login/")
    page.fill('input[name="username"]', 'testadmin')
    page.fill('input[name="password"]', 'testpass123')
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    for name, path in PAGES:
        try:
            page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=15000)
            time.sleep(0.5)
            dest = os.path.join(OUT, f"{name}.png")
            page.screenshot(path=dest, full_page=True)
            print(f"OK  {name}")
        except Exception as e:
            print(f"FAIL  {name}  -- {e}")

    browser.close()
    print("Done.")
