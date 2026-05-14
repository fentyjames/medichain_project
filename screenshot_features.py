"""Screenshot all new features added in v1.1."""
import os, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT  = r"E:\medichain_project\screenshots"
os.makedirs(OUT, exist_ok=True)

PAGES = [
    # --- Dashboard (Chart.js charts) ---
    ("feat_01_dashboard_charts",        "/dashboard/"),

    # --- Blockchain: fixed block detail ---
    ("feat_02_block_detail_fixed",      "/blockchain/blocks/1/"),

    # --- ZK: generate (form) ---
    ("feat_03_zk_generate",             "/zk-proofs/generate/"),

    # --- ZK: verify (form) ---
    ("feat_04_zk_verify",               "/zk-proofs/verify/"),

    # --- ZK: range proof ---
    ("feat_05_zk_range",                "/zk-proofs/range/"),

    # --- ZK: dashboard with proof history ---
    ("feat_06_zk_dashboard_history",    "/zk-proofs/"),

    # --- API: Swagger UI ---
    ("feat_07_api_swagger",             "/api/docs/"),

    # --- API: ReDoc ---
    ("feat_08_api_redoc",               "/api/redoc/"),

    # --- Healthcare list pages with CSV button ---
    ("feat_09_patients_csv",            "/healthcare/patients/"),
    ("feat_10_records_csv",             "/healthcare/records/"),
    ("feat_11_audit_csv",               "/healthcare/audit/"),

    # --- Blockchain transactions with CSV button ---
    ("feat_12_transactions_csv",        "/blockchain/transactions/"),

    # --- Block 2 and 3 detail ---
    ("feat_13_block_detail_2",          "/blockchain/blocks/2/"),
    ("feat_14_block_detail_3",          "/blockchain/blocks/3/"),
]

def shot(page, name, path, wait=0.8):
    try:
        page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=20000)
        time.sleep(wait)
        dest = os.path.join(OUT, f"{name}.png")
        page.screenshot(path=dest, full_page=True)
        print(f"OK   {name}")
    except Exception as e:
        print(f"FAIL {name} -- {e}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    # --- Login ---
    page.goto(f"{BASE}/accounts/login/")
    page.fill('input[name="username"]', 'testadmin')
    page.fill('input[name="password"]', 'testpass123')
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    print("Logged in.")

    # --- Pre-populate ZK history: generate a proof via the form ---
    try:
        page.goto(f"{BASE}/zk-proofs/generate/", wait_until="networkidle", timeout=15000)
        # Fill private inputs
        page.fill('textarea[name="inputs"]', 'tx_hash_abc123\ntx_hash_def456\ntx_hash_ghi789')
        page.fill('input[name="public_output"]', 'merkle_root_demo_0000000000000000000000000000')
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        time.sleep(0.5)
        print("ZK proof generated (history seeded).")
    except Exception as e:
        print(f"NOTE: ZK seed step skipped -- {e}")

    # --- Take all screenshots ---
    for name, path in PAGES:
        wait = 1.5 if "swagger" in name or "redoc" in name or "dashboard" in name else 0.8
        shot(page, name, path, wait=wait)

    browser.close()
    print("\nDone. Screenshots saved to:", OUT)
