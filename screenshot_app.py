"""Take screenshots of all major MediChain pages."""
import os, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT  = r"E:\medichain_project\screenshots"
os.makedirs(OUT, exist_ok=True)

PAGES = [
    ("01_landing",            "/"),
    ("02_login",              "/accounts/login/"),
    ("03_dashboard",          "/dashboard/"),
    ("04_healthcare",         "/healthcare/"),
    ("05_patient_list",       "/healthcare/patients/"),
    ("06_patient_add",        "/healthcare/patients/add/"),
    ("07_hospital_list",      "/healthcare/hospitals/"),
    ("08_record_list",        "/healthcare/records/"),
    ("09_record_add",         "/healthcare/records/add/"),
    ("10_lab_list",           "/healthcare/labs/"),
    ("11_insurance_list",     "/healthcare/insurance/"),
    ("12_permission_list",    "/healthcare/permissions/"),
    ("13_audit_log",          "/healthcare/audit/"),
    ("14_reports_hub",        "/healthcare/reports/"),
    ("15_system_overview",    "/healthcare/reports/overview/"),
    ("16_audit_report",       "/healthcare/reports/audit/"),
    ("17_blockchain",         "/blockchain/"),
    ("18_block_list",         "/blockchain/blocks/"),
    ("19_transaction_list",   "/blockchain/transactions/"),
    ("20_transaction_add",    "/blockchain/transactions/add/"),
    ("21_rollup_list",        "/blockchain/rollups/"),
    ("22_rollup_create",      "/blockchain/rollups/create/"),
    ("23_crosschain",         "/cross-chain/"),
    ("24_crosschain_transfer","/cross-chain/transfer/"),
    ("25_zk_dashboard",       "/zk-proofs/"),
    ("26_zk_generate",        "/zk-proofs/generate/"),
    ("27_zk_verify",          "/zk-proofs/verify/"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    # ── log in ──
    page.goto(f"{BASE}/accounts/login/")
    page.fill('input[name="username"]', 'testadmin')
    page.fill('input[name="password"]', 'testpass123')
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    print(f"Logged in, now at: {page.url}")

    for name, path in PAGES:
        try:
            page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=10000)
            time.sleep(0.3)
            dest = os.path.join(OUT, f"{name}.png")
            page.screenshot(path=dest, full_page=True)
            print(f"OK  {name}")
        except Exception as e:
            print(f"FAIL  {name}  -- {e}")

    # ── detail pages (need real IDs from DB) ──
    try:
        import django, sys
        sys.path.insert(0, r"E:\medichain_project")
        os.environ["DJANGO_SETTINGS_MODULE"] = "medichain_project.settings"
        django.setup()
        from healthcare.models import Patient, Hospital, MedicalRecord, Laboratory, InsuranceProvider
        from blockchain.models import Transaction, RollupBatch, Block

        details = []
        p_ = Patient.objects.first()
        if p_: details.append(("28_patient_detail", f"/healthcare/patients/{p_.patient_id}/"))
        h = Hospital.objects.first()
        if h: details.append(("29_hospital_detail", f"/healthcare/hospitals/{h.hospital_id}/"))
        r = MedicalRecord.objects.first()
        if r:
            details.append(("30_record_detail",   f"/healthcare/records/{r.record_id}/"))
            details.append(("31_record_report",   f"/healthcare/records/{r.record_id}/report/"))
        lab = Laboratory.objects.first()
        if lab:
            details.append(("32_lab_detail",  f"/healthcare/labs/{lab.lab_id}/"))
            details.append(("33_lab_edit",    f"/healthcare/labs/{lab.lab_id}/edit/"))
        ins = InsuranceProvider.objects.first()
        if ins:
            details.append(("34_insurance_detail", f"/healthcare/insurance/{ins.provider_id}/"))
            details.append(("35_insurance_edit",   f"/healthcare/insurance/{ins.provider_id}/edit/"))
        tx = Transaction.objects.first()
        if tx: details.append(("36_transaction_detail", f"/blockchain/transactions/{tx.tx_hash}/"))
        rb = RollupBatch.objects.first()
        if rb: details.append(("37_rollup_detail", f"/blockchain/rollups/{rb.batch_id}/"))
        bl = Block.objects.first()
        if bl: details.append(("38_block_detail", f"/blockchain/blocks/{bl.block_number}/"))

        for name, path in details:
            try:
                page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=10000)
                time.sleep(0.3)
                dest = os.path.join(OUT, f"{name}.png")
                page.screenshot(path=dest, full_page=True)
                print(f"✓  {name}")
            except Exception as e:
                print(f"✗  {name}  — {e}")
    except Exception as e:
        print(f"Detail pages error: {e}")

    browser.close()
    print(f"\nAll screenshots saved to: {OUT}")
