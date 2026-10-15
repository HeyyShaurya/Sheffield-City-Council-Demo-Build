# Sheffield Connect — QA and verified coverage

**Executed:** 15 October 2026, local sandbox.  
**Application:** Sheffield Council opportunity demonstrator, reference 100113345.  
**Implementation state:** working demonstration prototype; not a production release or Oracle-connected implementation.

## Automated verification record

| Check | Result | Method |
|---|---|---|
| Backend import/compilation | PASS | `python -m py_compile app/main.py` |
| Frontend JavaScript syntax | PASS | `node --check app/static/app.js` |
| Python API/workflow regression suite | **32 passed** | `python -m pytest -q tests/test_workflows.py` |
| Browser navigation and all work-area screens | PASS | Chromium rendered HTML/CSS/JS plus local FastAPI bridge; no JS page errors |
| Browser annual leave request and manager approval | PASS | UI clicks across employee/manager personas |
| Browser candidate apply, recruiter shortlist, candidate correspondence and self-select interview | PASS | UI clicks, dynamic database state |
| Browser interview feedback, offer and onboarding | PASS | UI clicks through all stage transitions |
| Browser document upload, archive, demo expiry and eligible purge | PASS | UI clicks across employee, HR and admin roles |
| Candidate mobile public view | PASS | 390px viewport, `scrollWidth == viewport width` |
| Candidate token privacy/invalid token | PASS | API tests |
| Duplicate candidate email/vacancy | PASS | API tests, blocked 409 |
| Overlapping/insufficient leave and double decision | PASS | API tests |
| Unauthorised role access | PASS | API tests for sensitive work areas and records |
| Duplicate timesheet, invalid date, manager approval | PASS | API tests |
| Private payslip access and duplicate payroll run | PASS | API tests, local non-statutory maths only |
| Report group filters/export and salary visibility | PASS | API tests |
| BCC-style messaging and 255/4000 limits | PASS | API tests |
| Integration failure, retry and deduplication | PASS | API tests against **mock adapter** |
| Reset with confirmation | PASS | API tests |

Test execution and UI evidence files: `docs/qa-login.png`, `docs/qa-overview.png`, `docs/qa-careers.png`, `docs/qa-mobile-careers.png`, `docs/qa-recruit-flow.png`. Browser runner uses an offline Python HTTP bridge because this sandbox Chromium's enterprise URL blocklist prevents navigation to localhost. The rendered DOM ran the actual application JavaScript and sent real API requests to a FastAPI test instance. It does not prove cross-browser/public-domain performance.

## Remaining unverified / out of scope

- No Oracle Fusion Cloud HCM, Oracle Payroll, Entra SSO/MFA, HMRC, Microsoft Outlook calendar or external finance/payment production endpoint was available or integrated.
- Payroll is a simple fixed 18% **illustrative deduction**, not any type of valid UK payroll result.
- Full workforce performance at 8,000 employee records, production concurrency, penetration-testing, verified full WCAG accessibility, screen-reader tests, backup/restore and disaster-recovery testing have not been completed.
- Browser UI was tested in Chromium, with functional mobile candidate overflow checks; no independent Safari, Firefox, iPhone or Android real-device test was performed.
- Employee/candidate records are fictional, and email notifications are not sent. Production security, encrypted persistent storage and lawful records retention need a separate implementation.
- Real video interviews are represented by scheduled interview preferences; live meeting video is not built.
- This app is not a reuse of an authenticated proprietary Oracle or PCL codebase; original module source was not provided or retrievable in the accessible sources.

## Repeat tests after changes

```bash
python -m pip install pytest httpx
python scripts/verify_demo.py
# Optional UI testing after `python -m pip install playwright` and Chromium installed:
python tests/browser_navigation.py
python tests/browser_journeys.py
```

**Gate:** Never present this as a live payroll platform or publicly publish without further security/production engineering. Suitable use: controlled, synthetic-data opportunity-specific demo, rehearsal and recording.
