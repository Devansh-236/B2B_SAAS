"""
Offline end-to-end check for the Onboarder API.

Gemini is replaced with canned responses and the database / generated documents
go to a temporary directory, so no API key or network access is needed:

    python tests/e2e_check.py
"""
import os, sys, json, time, tempfile, threading, sqlite3
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix="onb_e2e_")
os.environ.update({
    "GEMINI_API_KEY": "dummy-key",
    "ONBOARDER_DB_PATH": os.path.join(TMP, "test.db"),
    "DOCUMENT_OUTPUT_DIR": os.path.join(TMP, "docs"),
})
os.environ.pop("ONBOARDER_API_KEY", None)
sys.path.insert(0, ROOT)

import google.generativeai as genai

SLOW = {"on": False}
CALLS = {"n": 0, "kw": set()}

class Resp:
    def __init__(self, text): self.text = text

def fake_generate_content(self, contents, **kwargs):
    CALLS["n"] += 1
    CALLS["kw"].update(kwargs.keys())
    if SLOW["on"]:
        time.sleep(2)
    p = str(contents)
    if "corporate email address" in p:
        return Resp("jane.doe@company.com")
    if '"selected_buddy"' in p:
        return Resp(json.dumps({"selected_buddy": {"name": "Mock Buddy", "role": "Staff Engineer",
                    "department": "Engineering", "experience_years": 6, "compatibility_score": 9,
                    "matching_reasons": ["role fit"]}, "matching_reasons": ["role fit"]}))
    if '"standard_systems"' in p:
        sysd = lambda n: {"system_name": n, "access_level": "Standard", "provisioning_priority": "High"}
        return Resp(json.dumps({"standard_systems": [sysd("Email System"), sysd("Slack")],
                    "role_specific_systems": [sysd("GitHub")], "department_systems": [],
                    "security_levels": ["Standard"], "access_timeline": {"days": 1}}))
    if "IMPORTANT: You must respond with valid JSON" in p:
        # Echo back the schema example embedded in the prompt
        start = p.index("{", p.index("exact structure:"))
        depth = 0
        for i, ch in enumerate(p[start:], start):
            depth += ch == "{"; depth -= ch == "}"
            if depth == 0:
                return Resp(p[start:i + 1])
    return Resp("Canned LLM text.")

genai.GenerativeModel.generate_content = fake_generate_content

from fastapi.testclient import TestClient
import main
from onboarder.database_manager import DatabaseManager

client = TestClient(main.app)
db = main.db_manager
results = []
def check(name, cond, info=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{info}]" if info else ""))

hire = {"full_name": "Jane Doe", "personal_email": "jane@example.com", "job_title": "Software Engineer",
        "manager_name": "Bob", "start_date": "2024-01-15"}

print("DB path:", db.db_path)
with sqlite3.connect(db.db_path) as c:
    check("WAL journal mode", c.execute("PRAGMA journal_mode").fetchone()[0] == "wal")

r = client.post("/onboarding", json=hire); check("create 200", r.status_code == 200, r.status_code)
emp = r.json()["data"]["employee_id"]; print("employee_id:", emp, "onboarding_id:", r.json()["data"]["onboarding_id"])
r2 = client.post("/onboarding", json=hire)
check("same name gets distinct id", r2.status_code == 200 and r2.json()["data"]["employee_id"] != emp)
r = client.post("/onboarding", json={**hire, "employee_id": "EMPX"}); check("explicit id 200", r.status_code == 200)
r = client.post("/onboarding", json={**hire, "employee_id": "EMPX"}); check("duplicate id 409", r.status_code == 409, r.status_code)

# Full run (TestClient runs background tasks before returning)
r = client.post(f"/onboarding/{emp}/start"); check("start 200", r.status_code == 200, r.text[:100])
st = client.get(f"/onboarding/{emp}/status").json()
print("final status:", st["status"], st["current_phase"], st["completed_phases"])
check("run reaches COMPLETED", st["status"] == "COMPLETED" and st["current_phase"] == "COMPLETED"
      and st["completed_phases"] == ["PRE_BOARDING", "DAY1_SETUP", "INTEGRATION"])
check("LLM calls used request_options timeout", "request_options" in CALLS["kw"], CALLS)
rec = db.get_onboarding_by_employee_id(emp)
for phase, agents in rec["results"].items():
    print(" ", phase, {a: v.get("status") for a, v in agents.items()})
check("buddy used LLM result (no SIGALRM failure)",
      rec["results"]["integration"]["BuddyAgent"]["selected_buddy"]["name"] == "Mock Buddy")
check("start again -> 409", client.post(f"/onboarding/{emp}/start").status_code == 409)

ctx = client.get(f"/onboarding/{emp}/context")
body = ctx.text
check("no temp_password in context/results", "temp_password\"" not in body and "temp_password\":" not in body
      and "temp_password_issued" in json.dumps(rec["results"]))
items = [i["item"] for i in rec["onboarding_context"]["PRE_BOARDING"]["checklist_items"]]
check("checklist items stripped", all(not i.startswith("]") for i in items), items[:2])
docs = sorted(os.listdir(os.environ["DOCUMENT_OUTPUT_DIR"]))
print("docs:", docs)
pw = rec["results"]["pre_boarding"]["PaperworkAgent"]
check("paperwork returns real .txt paths that exist", os.path.exists(pw["contract_path"]) and pw["contract_path"].endswith(".txt"))

# Validation
check("phase bad status 422", client.post(f"/onboarding/{emp}/phase", json={"phase": "PRE_BOARDING", "status": "BOGUS"}).status_code == 422)
check("phase IN_PROGRESS 422", client.post(f"/onboarding/{emp}/phase", json={"phase": "PRE_BOARDING", "status": "IN_PROGRESS"}).status_code == 422)
check("phase bad phase 422", client.post(f"/onboarding/{emp}/phase", json={"phase": "X", "status": "COMPLETED"}).status_code == 422)
check("execute via GET -> 405", client.get(f"/onboarding/{emp}/phase/DAY1_SETUP/execute").status_code == 405)
check("execute bad phase 400", client.post(f"/onboarding/{emp}/phase/NOPE/execute").status_code == 400)

# Manual phase update on second hire leaves PENDING (not IN_PROGRESS)
emp2 = r2.json()["data"]["employee_id"]
r = client.post(f"/onboarding/{emp2}/phase", json={"phase": "PRE_BOARDING", "status": "COMPLETED"})
check("manual phase -> PENDING", r.status_code == 200 and r.json()["data"]["status"] == "PENDING"
      and r.json()["data"]["current_phase"] == "DAY1_SETUP", r.json())
r = client.post(f"/onboarding/{emp2}/phase/DAY1_SETUP/execute")
s2 = client.get(f"/onboarding/{emp2}/status").json()
check("single-phase execute -> PENDING at INTEGRATION", r.status_code == 200 and s2["status"] == "PENDING"
      and s2["current_phase"] == "INTEGRATION", (s2["status"], s2["current_phase"]))

# Stuck IN_PROGRESS recovery
r = client.post("/onboarding", json={**hire, "full_name": "Stuck Person"}); emp3 = r.json()["data"]["employee_id"]
oid3 = r.json()["data"]["onboarding_id"]
old_run = db.claim_onboarding(oid3)  # simulate a run that died
check("second claim refused (atomic)", db.claim_onboarding(oid3) is None)
check("start on stuck -> 409", client.post(f"/onboarding/{emp3}/start").status_code == 409)
r = client.post(f"/onboarding/{emp3}/reset"); check("reset 200 -> PENDING", r.status_code == 200 and r.json()["data"]["status"] == "PENDING")
# old run's late write must be ignored
main.agent_orchestrator.execute_phase(emp3, oid3, "PRE_BOARDING", old_run)
s3 = db.get_onboarding_record(oid3)
check("late write from reset run ignored", s3["status"] == "PENDING" and s3["completed_phases"] == [], (s3["status"], s3["completed_phases"]))
client.post(f"/onboarding/{emp3}/start")
check("restart after reset completes", client.get(f"/onboarding/{emp3}/status").json()["status"] == "COMPLETED")

# Timeout: thread finishing late must not clobber FAILED
r = client.post("/onboarding", json={**hire, "full_name": "Slow Person"}); emp4 = r.json()["data"]["employee_id"]
main.agent_orchestrator.phase_timeout = 1
SLOW["on"] = True
before = threading.active_count()
client.post(f"/onboarding/{emp4}/start")
s4 = client.get(f"/onboarding/{emp4}/status").json()
check("timed-out phase -> FAILED", s4["status"] == "FAILED", s4["status"])
time.sleep(12)  # let the worker thread finish its slow LLM calls
SLOW["on"] = False
main.agent_orchestrator.phase_timeout = 120
s4 = db.get_onboarding_by_employee_id(emp4)
check("late thread did not clobber FAILED", s4["status"] == "FAILED" and s4["completed_phases"] == [], (s4["status"], s4["completed_phases"], s4["errors"]))

# Filename sanitization
from onboarder.tools.document_generator import DocumentGenerator
dg = DocumentGenerator(os.path.join(TMP, "docs2"))
p = dg.generate_employment_contract({"full_name": "../../etc/Evil Name", "employee_id": "../x"})
check("sanitized path stays in output dir", os.path.dirname(p) == os.path.realpath(os.path.join(TMP, "docs2")) and os.path.exists(p), os.path.basename(p))

# Whitelist
try:
    db.update_onboarding_record("x", {"status = 'X' --": 1}); ok = False
except ValueError:
    ok = True
check("update column whitelist", ok)

# Migration
jf = os.path.join(TMP, "legacy.json")
json.dump({"onboard_legacy_1": {"new_hire_data": {"full_name": "Legacy"}, "status": "COMPLETED",
           "current_phase": "COMPLETED", "completed_phases": ["PRE_BOARDING"]}}, open(jf, "w"))
check("migrate_from_json works", db.migrate_from_json(jf) and db.get_onboarding_record("onboard_legacy_1")["employee_id"] == "emp_onboard_legacy_1")

# API key
os.environ["ONBOARDER_API_KEY"] = "s3cret"
check("api key: missing -> 401", client.get("/onboardings").status_code == 401)
check("api key: wrong -> 401", client.get("/onboardings", headers={"X-API-Key": "nope"}).status_code == 401)
check("api key: right -> 200", client.get("/onboardings", headers={"X-API-Key": "s3cret"}).status_code == 200)
check("health open without key", client.get("/health").status_code == 200)
os.environ.pop("ONBOARDER_API_KEY")

# CORS
r = client.options("/onboardings", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"})
check("CORS rejects unknown origin", "access-control-allow-origin" not in r.headers)
r = client.options("/onboardings", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"})
check("CORS allows localhost:3000 w/o credentials", r.headers.get("access-control-allow-origin") == "http://localhost:3000"
      and "access-control-allow-credentials" not in r.headers)
print("stats:", client.get("/stats").json())
print(f"\n{sum(ok for _, ok in results)}/{len(results)} checks passed; temp dir {TMP}")
sys.exit(0 if all(ok for _, ok in results) else 1)
