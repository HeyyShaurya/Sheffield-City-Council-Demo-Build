import json
from pathlib import Path
sets = {
 'Payroll':['Automated Payroll Processing','Payroll Management','Time & Attendance','Compliance with payroll regulations','Pensions','Payslips/P60/P45','Claims/Expenses'],
 'Employee Self Service':['View Payslips/P60/P45','Book/View Leave','Make Time and Expenses Claims','Complete Employment documentation','View/Update personal details'],
 'Manager Self Service':['Authorise requests','View Team information','Carry out key HR processes','Generate Team reports','Re-directing tasks'],
 'Learning Management':['Carry out e-learning','Book training courses/opportunities','View employee learning record','View team learning record','Access informal learning'],
 'Document Storage':['Store employee documentation','Set retention dates for employee documentation','Automated document deletion/destruction','Make document viewing available to employees'],
 'Organisational Chart':['Visualisation of organisational establishment structure'],
 'Recruitment / Onboarding':['Raise Vacancy/Request to Recruit','Job Advert Creation and Publication','Candidate Application Stage','Shortlisting','Interview Scheduling','Interview and Outcome Recording','Offer Stage','Pre-Employment checks','Onboarding','Hiring/Contract Issue','Post-Recruitment Closure'],
 'Reporting / Analytics':['Integration with Business Intelligence Tools','Real Time Data Insights','Workforce, Payroll, and HR Analytics','Advanced Reporting Capabilities'],
 'Access / Security':['Single Sign On','Multi Factor Authentication','GDPR compliance'],
 'Case Management':['HR casework (managing attendance, disciplinaries)'],
 'System Integration':['Integration with other applications'],
}
optional={('Payroll','Claims/Expenses'),('Employee Self Service','Make Time and Expenses Claims'),('Reporting / Analytics','Advanced Reporting Capabilities'),('Case Management','HR casework (managing attendance, disciplinaries)')}
implementation={
 'Payroll':'Demo: payroll run and payslips with non-statutory illustrative deduction; time/attendance is a prototype, pension and UK HMRC processing not implemented.',
 'Employee Self Service':'Demo: absence, personal directory, document upload, payslip and optional expense claim.',
 'Manager Self Service':'Demo: team approval, workforce metrics and assignments.',
 'Learning Management':'Demo: course enrolment, completion and manager view; no third-party LMS connection.',
 'Document Storage':'Demo: uploaded files, access controls, retention date, archive and purge; production policies not validated.',
 'Organisational Chart':'Demo: reporting hierarchy, FTE and cost-centre summaries.',
 'Recruitment / Onboarding':'Demo: vacancy, candidate self-service, interviews, outcomes, offers, checks and employee conversion.',
 'Reporting / Analytics':'Demo: filtered report builder, exports and dynamic aggregates; external BI integration not connected.',
 'Access / Security':'Demo: role-aware access, signed local sessions, audit; Entra SSO/MFA not connected.',
 'Case Management':'Optional demonstrator: HR case register; not included in proposed base subscription.',
 'System Integration':'Demo: durable local mock queue, retries/failure injection; no actual third-party endpoint.',
}
items=[]
for category, processes in sets.items():
 for process in processes:
  items.append({'id':len(items)+1,'area':category,'process':process,'proposal':'Additional Cost' if (category,process) in optional else 'Standard Offer','demo_note':implementation[category],
                'demo_depth':'working demo subset' if category not in ('Access / Security','Payroll') else 'partial simulator'})
assert len(items)==47
assert sum(x['proposal']=='Additional Cost' for x in items)==4
Path(__file__).with_name('capability_matrix.json').write_text(json.dumps(items,indent=2),encoding='utf-8')
