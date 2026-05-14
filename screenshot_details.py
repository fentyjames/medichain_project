"""Take screenshots of detail pages using pre-fetched IDs."""
import os, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT  = r"E:\medichain_project\screenshots"

DETAILS = [
    ("28_patient_detail",    "/healthcare/patients/4541b850f7086157ec6ff342365ef3f0cf5b70d28b9a70375bc639accc3ee31e/"),
    ("29_hospital_detail",   "/healthcare/hospitals/280caf0e0c30fb32a0ce96bde09a16acab259c603c38d0da6942120eb07d8647/"),
    ("30_record_detail",     "/healthcare/records/3e94f3209557a0a225d1ba5c80be43773459378847dddcdd90b9bde300ddd3fa/"),
    ("31_record_report",     "/healthcare/records/3e94f3209557a0a225d1ba5c80be43773459378847dddcdd90b9bde300ddd3fa/report/"),
    ("32_lab_detail",        "/healthcare/labs/c5c923bd903259fd6962e2d47c71c6f50b12e0f7f063b4fc8eabe5c1f566a477/"),
    ("33_lab_edit",          "/healthcare/labs/c5c923bd903259fd6962e2d47c71c6f50b12e0f7f063b4fc8eabe5c1f566a477/edit/"),
    ("34_insurance_detail",  "/healthcare/insurance/5960fa6f73732cb7be5cdbd1ebf16e96e6975e7d6b14f2ac66f35570bfbec7d2/"),
    ("35_insurance_edit",    "/healthcare/insurance/5960fa6f73732cb7be5cdbd1ebf16e96e6975e7d6b14f2ac66f35570bfbec7d2/edit/"),
    ("36_transaction_detail","/blockchain/transactions/814ec2d168dc1bc095813234f814086e9056269c21163674c227cde4d4825cdb/"),
    ("37_rollup_detail",     "/blockchain/rollups/faa11ca56b4ebcbf4a6e676ca12848fc4c33b584a98502ac7f03eb1d5c639657/"),
    ("38_block_detail",      "/blockchain/blocks/3/"),
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
    print(f"Logged in, now at: {page.url}")

    for name, path in DETAILS:
        try:
            page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=10000)
            time.sleep(0.3)
            dest = os.path.join(OUT, f"{name}.png")
            page.screenshot(path=dest, full_page=True)
            print(f"OK  {name}")
        except Exception as e:
            print(f"FAIL  {name}  -- {e}")

    browser.close()
    print(f"\nDone. Screenshots in: {OUT}")
