# Sheffield Connect — HR & Payroll opportunity demonstrator

**Opportunity:** Sheffield City Council, pre-market engagement reference **100113345**.  
**Respondent:** PayrollCloud Limited.  
**What this is:** a working, self-contained demonstration application, designed for live narration and recording, not a licensed Oracle product, production HRIS, compliance-certified payroll system or finished production deployment.

The programme is driven by Sheffield's original PME, PayrollCloud's submitted response and a separately supplied evaluation feedback appendix. It is built as a Sheffield-specific prototype; **no prior proprietary app codebase was supplied or verified as reusable**. The UI and backend were authored for this package.

## Quick start (Windows / Mac / Linux)

Requires Python 3.11+ (3.12 recommended), a current browser, and an internet connection **only** to install the Python dependencies. After installation, the application runs without an external API or subscription.

```bash
python -m venv .venv
```

Activate the virtual environment:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Mac/Linux: `source .venv/bin/activate`

```bash
python -m pip install -r requirements.txt
python run.py
```

Open **http://127.0.0.1:8000**. Use the default **demo access code** `sheffield-demo` and pick any sample persona in the sign-in dropdown. It auto-generates `data/sheffield.sqlite3` and sample records on first launch. To reset and take a clean recording, sign in as **Sofia Bennett** → Demo walkthrough → Reset all demo data (type `RESET DEMO`). Don't use real personal information.

**Alternative: Docker** (for private demo evaluation only):

```bash
docker build -t sheffield-connect-demo .
docker run --rm -p 127.0.0.1:8000:8000 -e SHEFFIELD_SECRET=change-to-a-long-random-secret -e SHEFFIELD_DEMO_PIN=choose-a-private-demo-pin sheffield-connect-demo
```

Change the code above before sharing access. A Docker container without a mounted data volume loses changes on restart. This is still NOT a public production security posture.

## Demonstration personas (all fictional)

| Name | Role | Most useful demonstration |
|---|---|---|
| Aisha Khan | Employee | Absence request, personal file, time entry, course booking |
| Helen Walker | Manager | Approve/reject team leave and timesheet, inspect organisation, create vacancy |
| Grace Turner | Recruiter | Advert, shortlist, candidate feedback, offer, onboarding |
| Priya Shah | People Services | Employee tasks, document lifecycle, restricted HR case |
| Sofia Bennett | Administrator | Reset sample, retry mock integration, simulate document retention expiry |
| Matthew Grant | Service director | Permission-controlled workforce reports |
| Oliver Reed | Payroll lead | Illustrative payroll run/finalisation/payslip |
| Amira Yusuf | Learning admin | Learning records |

Other employee records are generated as fictional workforce background data. **The 8,000-person count in the submitted response is a pricing/scale baseline, NOT 8,000 real records loaded into this demo.**

## Demonstrate the six requested user journeys

1. **Book and approve annual leave:** Aisha → Leave → New request → switch to Helen → Approve → back to Aisha. The balance and approval status change in the database. Leave types, annual/bank/purchased/carry-forward figures, overlapping request checks and audit history are represented.
2. **Organisation and establishment:** Helen or Matthew → Organisation. See manager tree, posts, grade, FTE, cost centre, visible spans and roll-ups. Converting a candidate updates the headcount and organisational data.
3. **Applicant-to-worker lifecycle:** Helen/Grace → draft/publish vacancy → Public careers → submit candidate with required cover letter → recruiter shortlists → candidate schedules or reschedules → recruiter records scored feedback → offer / acceptance / checks / onboarding → new person and onboarding tasks; application changes drive mock external events.
4. **Document lifecycle:** Aisha → Upload a `.txt` example → Priya → Archive → Sofia → Simulate expiry → Priya → Run eligible purge; audit records remain. It does not implement a certified GDPR compliance engine.
5. **People Services processes:** Priya → HR journeys & tasks → Assign a task → switch to assigned colleague to complete → Priya reviews the auditable change and integration handoffs. The optional casework module is explicitly marked **additional cost**.
6. **Management information:** Matthew or Priya → Workforce insights → filter/group by department, cost centre or grade → choose headcount/FTE → export CSV; the report is computed from transactions with role restrictions.

`docs/VIDEO_DEMO_SCRIPT.md` contains a full **45–50-minute** narrated script, presenter persona switches, exact screen actions and recovery notes. The in-app **Demo walkthrough** contains a shorter scene checklist.

## Additional working prototype features

- Employee personal record edits; time and attendance hours with manager decisions.
- Four learning catalogue records, employee enrolment and completion.
- Illustrative payroll runs, controlled finalisation and private example payslips.
- Explicitly optional employee expense claims and HR case management.
- Candidate self-service tracker, correspondence inbox, interview selection and rescheduling, withdrawal, detailed selection notes.
- Private internal messaging with **BCC-equivalent recipient privacy**, **255-character subject** and **4,000-character message** limits; optional force-notify is **recorded as a mock event, no email goes out**.
- Role-scoped activity/audit evidence and mock integrations with forced failure/retry.
- `docs/capability_matrix.json` contains a traceability index of all **47 Sheffield functional processes**, their submitted classification and honest **demo depth** (full, subset, partial simulator, external dependency).

## Automated verification

```bash
python -m pip install pytest httpx
python scripts/verify_demo.py
```

`verify_demo.py` runs syntax checks and the isolated backend integration tests (currently 32). Browser DOM and click-path QA scripts are in `tests/browser_navigation.py` and `tests/browser_journeys.py`; these additionally require `playwright` and a Chromium executable. The tests run against an isolated temporary dataset rather than your working application data. Screenshots of the rendered screens from our QA are included in `docs/qa-*.png`.

## Deployment boundaries and security

**Publishing directly to an external website is NOT recommended for this prototype.** It uses a single shared demo code, simple signed cookies, synthetic personas, local SQLite and local file storage. Although some role checks are enforced, it has NOT had an independent security assessment, penetration test, accessibility audit, production observability, consent/legal retention validation, load test at 8,000 records, or data-protection impact assessment. Build real Entra SSO/MFA, proper access management, CSRF/security controls, secrets management, encrypted backups and monitoring before real use. Keep it **localhost or access-controlled private sandbox only**, with fictional data.

This package does **NOT** connect to Oracle Fusion HCM, Oracle Learning, Outlook, Microsoft Entra ID, Sheffield finance/CRM/payments, YORtender, a real mail system, HMRC, LGPS/TPS, or real video meetings. Demonstrated integrations are controlled **local mocks**; configuring production interfaces, UK hosting, statutory payroll and legal retention requires separate implementation. Payslip deductions are a fixed **illustrative 18%**, not PAYE/NI/pension calculations; no BACS/payment file is transmitted. None of the screenshots or functions establishes that the specific product is Oracle-certified.

## Project contents

| Path | Contents |
|---|---|
| `app/main.py` | Python FastAPI API, transactions, validations, SQLite database, audit |
| `app/static/` | Responsive standalone app UI (HTML/CSS/JavaScript) |
| `data/` | Generated local database/storage after startup (not shipped with demo state) |
| `docs/capability_matrix.json` | All 47 proposed scope items, differentiating response vs prototype coverage |
| `docs/VIDEO_DEMO_SCRIPT.md` | Full recorded-demo narration and click paths |
| `docs/REQUIREMENTS_AND_LIMITATIONS.md` | Requirement-to-implementation traceability and explicit constraints |
| `docs/TEST_REPORT.md` | Test record and known limitations |
| `docs/qa-*.png` | Actual Chromium rendering QA screenshots, including mobile candidate view |
| `tests/` | Automated workflow & browser checks |
| `scripts/verify_demo.py` | One-command automated verification |
| `Dockerfile` | Private container build |

## Licensing and privacy

Synthetic names and employee/payroll figures are generated for product demonstration; they are NOT Sheffield employee records, PCL client data or instructions to process real payroll. Original opportunity/response files are **not bundled** into the ZIP to avoid redistribution; the `docs` directory records their titles and the requirements they informed.
