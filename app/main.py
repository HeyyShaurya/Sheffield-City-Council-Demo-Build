"""Sheffield Connect: auditable opportunity-specific demonstration application.

Demo-only: no Oracle connection, real e-mail, certified UK payroll, or Entra federation.
"""
from __future__ import annotations
import csv
import io
import json
import os
import re
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from hmac import compare_digest, new as hmac_new
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('SHEFFIELD_DATA_DIR', str(ROOT / 'data')))
DATA.mkdir(parents=True, exist_ok=True)
UPLOADS = DATA / 'uploads'; UPLOADS.mkdir(parents=True, exist_ok=True)
DB = DATA / 'sheffield.sqlite3'
SECRET = os.environ.get('SHEFFIELD_SECRET', 'local-demonstration-only-please-set-for-network')
DEMO_PIN = os.environ.get('SHEFFIELD_DEMO_PIN', 'sheffield-demo')
APP = FastAPI(title='Sheffield Connect | Opportunity Demonstrator', version='1.0.0')
APP.mount('/static', StaticFiles(directory=str(ROOT/'app'/'static')), name='static')

class Payload(BaseModel):
    model_config = {'extra': 'forbid'}
    data: dict[str, Any] = Field(default_factory=dict)

def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def today() -> str:
    return date.today().isoformat()

def isodays(n: int) -> str:
    return (date.today() + timedelta(days=n)).isoformat()

@contextmanager
def conn():
    c = sqlite3.connect(str(DB), timeout=15, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA journal_mode=WAL')
    try:
        c.execute('BEGIN IMMEDIATE')
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()

def row(r):
    return dict(r) if r is not None else None

def rows(rs):
    return [dict(r) for r in rs]

def fail(message, status=400):
    raise HTTPException(status_code=status, detail=message)

def require_fields(p, *names):
    for n in names:
        if n not in p or str(p[n]).strip() == '':
            fail('Required field: ' + n)

def limit(s: Any, n: int=255) -> str:
    value = str(s).strip()
    if len(value)>n: fail('Field exceeds '+str(n)+' characters')
    return value

def dateval(s: Any) -> date:
    try: return date.fromisoformat(str(s))
    except (TypeError,ValueError): fail('Invalid ISO date')

def numeric(value: Any, lo=0, hi=1000000) -> float:
    try: x=float(value)
    except (ValueError, TypeError): fail('Expected a number')
    if x<lo or x>hi: fail('Number is out of allowed range')
    return x

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, role TEXT NOT NULL,
 department TEXT, job TEXT, grade TEXT, manager_id INTEGER REFERENCES users(id), fte REAL DEFAULT 1, salary REAL DEFAULT 30000,
 cost_center TEXT, leave_total REAL DEFAULT 25, leave_carry REAL DEFAULT 0, leave_purchased REAL DEFAULT 0,
 leave_bank REAL DEFAULT 8, active INTEGER DEFAULT 1, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS profiles(employee_id INTEGER PRIMARY KEY REFERENCES users(id),phone TEXT DEFAULT '',address TEXT DEFAULT '',emergency_contact TEXT DEFAULT '',updated TEXT);
CREATE TABLE IF NOT EXISTS leave_requests(id INTEGER PRIMARY KEY, employee_id INTEGER REFERENCES users(id), manager_id INTEGER REFERENCES users(id),
 leave_type TEXT NOT NULL,start TEXT NOT NULL,ending TEXT NOT NULL,days REAL NOT NULL,note TEXT DEFAULT '',status TEXT NOT NULL,
 decided_at TEXT,created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS vacancies(id INTEGER PRIMARY KEY,title TEXT,department TEXT,location TEXT,grade TEXT,salary TEXT,
 summary TEXT,cover_required INTEGER DEFAULT 0,status TEXT DEFAULT 'Draft',owner_id INTEGER REFERENCES users(id),
 revision INTEGER DEFAULT 1,created TEXT,closing TEXT);
CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY,vacancy_id INTEGER REFERENCES vacancies(id),name TEXT,email TEXT,
 statement TEXT,cover_letter TEXT,source TEXT DEFAULT 'Council careers',access_token TEXT UNIQUE,stage TEXT DEFAULT 'Applied',
 interview_slot TEXT,interview_type TEXT DEFAULT 'Video',interview_feedback TEXT,interview_score INTEGER,
 offer_status TEXT DEFAULT '',worker_id INTEGER REFERENCES users(id),created TEXT,updated TEXT);
CREATE TABLE IF NOT EXISTS candidate_events(id INTEGER PRIMARY KEY,application_id INTEGER REFERENCES applications(id),title TEXT,body TEXT,event_kind TEXT,created TEXT);
CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY,employee_id INTEGER REFERENCES users(id),name TEXT,doc_type TEXT,
 classification TEXT,stored_name TEXT,retention_until TEXT,archived INTEGER DEFAULT 0,deleted INTEGER DEFAULT 0,
 uploaded_by INTEGER REFERENCES users(id),created TEXT);
CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY,title TEXT,kind TEXT,assigned_to INTEGER REFERENCES users(id),
 employee_id INTEGER REFERENCES users(id),status TEXT DEFAULT 'Open',due TEXT,notes TEXT,created TEXT,completed TEXT);
CREATE TABLE IF NOT EXISTS courses(id INTEGER PRIMARY KEY,title TEXT,category TEXT,hours REAL,seats INTEGER,description TEXT);
CREATE TABLE IF NOT EXISTS enrolments(id INTEGER PRIMARY KEY,course_id INTEGER REFERENCES courses(id),employee_id INTEGER REFERENCES users(id),
 status TEXT DEFAULT 'Enrolled',created TEXT,completed TEXT,UNIQUE(course_id,employee_id));
CREATE TABLE IF NOT EXISTS payroll_runs(id INTEGER PRIMARY KEY,period TEXT UNIQUE,status TEXT,headcount INTEGER,gross REAL,net REAL,
 deduction REAL,created TEXT,completed TEXT);
CREATE TABLE IF NOT EXISTS payroll_items(id INTEGER PRIMARY KEY,run_id INTEGER REFERENCES payroll_runs(id),employee_id INTEGER REFERENCES users(id),
 gross REAL,deduction REAL,net REAL,UNIQUE(run_id,employee_id));
CREATE TABLE IF NOT EXISTS time_entries(id INTEGER PRIMARY KEY,employee_id INTEGER REFERENCES users(id),week_start TEXT,
 hours REAL,status TEXT DEFAULT 'Submitted',manager_id INTEGER REFERENCES users(id),UNIQUE(employee_id,week_start));
CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY,employee_id INTEGER REFERENCES users(id),category TEXT,amount REAL,
 detail TEXT,status TEXT DEFAULT 'Submitted',manager_id INTEGER REFERENCES users(id),created TEXT);
CREATE TABLE IF NOT EXISTS hr_cases(id INTEGER PRIMARY KEY,employee_id INTEGER REFERENCES users(id),category TEXT,title TEXT,
 details TEXT,status TEXT DEFAULT 'Open',owner_id INTEGER REFERENCES users(id),created TEXT);
CREATE TABLE IF NOT EXISTS integrations(id INTEGER PRIMARY KEY,name TEXT UNIQUE,method TEXT,description TEXT,status TEXT DEFAULT 'Ready');
CREATE TABLE IF NOT EXISTS integration_events(id INTEGER PRIMARY KEY,system TEXT,event TEXT,entity_id INTEGER,payload TEXT,
 status TEXT DEFAULT 'Queued',attempts INTEGER DEFAULT 0,error TEXT,created TEXT,updated TEXT,UNIQUE(system,event,entity_id));
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY,subject TEXT,body TEXT,sender_id INTEGER REFERENCES users(id),
 force_notify INTEGER,created TEXT);
CREATE TABLE IF NOT EXISTS message_recipients(message_id INTEGER REFERENCES messages(id),recipient_id INTEGER REFERENCES users(id),
 read_at TEXT,PRIMARY KEY(message_id,recipient_id));
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor_id INTEGER,action TEXT,entity TEXT,entity_id INTEGER,detail TEXT,created TEXT);
'''

def audit(c, uid, action, entity, entity_id, detail=''):
    c.execute('INSERT INTO audit(actor_id,action,entity,entity_id,detail,created) VALUES(?,?,?,?,?,?)',
              (uid,action,entity,entity_id,limit(detail,900),now()))

def seed(c):
    if c.execute('SELECT COUNT(*) FROM users').fetchone()[0]: return
    fixtures = [
       (1,'Aisha Khan','aisha@demo.sheffield.local','employee','Adult Social Care','Social Worker','G7',4,1.0,35800,'ASC-110'),
       (2,'Daniel Price','daniel@demo.sheffield.local','employee','Adult Social Care','Support Officer','G5',4,1.0,29500,'ASC-110'),
       (3,'Megan Lewis','megan@demo.sheffield.local','employee','Public Health','Analyst','G6',4,0.8,31000,'PH-200'),
       (4,'Helen Walker','helen@demo.sheffield.local','manager','Adult Social Care','Service Manager','G10',8,1,51500,'ASC-110'),
       (5,'Priya Shah','priya@demo.sheffield.local','hr','People Services','HR Business Partner','G10',8,1,51000,'HR-100'),
       (6,'Oliver Reed','oliver@demo.sheffield.local','payroll','Payroll','Payroll Lead','G9',8,1,47000,'PAY-100'),
       (7,'Amira Yusuf','amira@demo.sheffield.local','learning','Learning & Development','Learning Lead','G8',8,1,42000,'LD-100'),
       (8,'Matthew Grant','matthew@demo.sheffield.local','service','Corporate Services','Service Director','G13',9,1,77000,'CS-001'),
       (9,'Sofia Bennett','sofia@demo.sheffield.local','admin','Digital Services','System Administrator','G10',None,1,55000,'IT-100'),
       (10,'Grace Turner','grace@demo.sheffield.local','recruiter','People Services','Recruitment Lead','G8',5,1,42000,'HR-100'),
       (11,'Thomas White','thomas@demo.sheffield.local','employee','Adult Social Care','Care Coordinator','G6',4,1,32200,'ASC-110'),
       (12,'Nadia Patel','nadia@demo.sheffield.local','employee','Public Health','Public Health Officer','G7',4,1,36000,'PH-200'),
       (13,'Connor Mills','connor@demo.sheffield.local','employee','Communities','Community Officer','G6',8,1,32600,'COM-300'),
       (14,'Eva Clarke','eva@demo.sheffield.local','employee','Adult Social Care','Support Officer','G5',4,0.5,18000,'ASC-110'),
       (15,'Noah Hughes','noah@demo.sheffield.local','employee','Digital Services','Developer','G8',9,1,44400,'IT-100'),
       (16,'Jade Robinson','jade@demo.sheffield.local','employee','Learning & Development','Learning Officer','G6',7,1,34500,'LD-100'),
    ]
    for id,n,email,role,dept,job,grade,mgr,fte,salary,cc in sorted(fixtures, key=lambda x: {9:0,8:1,4:2,5:2,7:2}.get(x[0],3)):
        c.execute('''INSERT INTO users(id,name,email,role,department,job,grade,manager_id,fte,salary,cost_center,
                  leave_total,leave_carry,leave_purchased,leave_bank,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                  (id,n,email,role,dept,job,grade,mgr,fte,salary,cc,25,3 if id==1 else 0,2 if id==1 else 0,8,now()))
    c.execute('''INSERT INTO vacancies(title,department,location,grade,salary,summary,cover_required,status,owner_id,revision,created,closing)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',('Community Support Officer','Adult Social Care','Sheffield / hybrid','G6',
                'GBP 30,000 - 34,000','Support adults and neighbourhood teams with high-quality public services.',1,'Published',4,1,now(),isodays(30)))
    for title,cat,hours,seats,description in [
      ('Safeguarding Essentials','Compliance',3,100,'Council safeguarding policies and practical scenarios.'),
      ('Leading Inclusive Teams','Leadership',2,40,'Practical inclusive leadership behaviours.'),
      ('Data Protection & GDPR','Compliance',2,100,'Handling employee and public information responsibly.'),
      ('Digital Service Foundations','Digital',4,25,'Modern service delivery and digital collaboration.'),
    ]: c.execute('INSERT INTO courses(title,category,hours,seats,description) VALUES(?,?,?,?,?)',(title,cat,hours,seats,description))
    for name,method,description in [
        ('Microsoft Entra ID','SAML','Federation/MFA planned; not connected in this demonstrator'),
        ('Corporate Finance','REST/SFTP','Cost allocation and approved employee events'),
        ('Outlook Calendar','REST','Interview event delivery'),
        ('Corporate CRM','REST','Controlled contact and organisation exchange'),
        ('Payment Services','SFTP','Payroll payment instruction export'),
    ]: c.execute('INSERT INTO integrations(name,method,description) VALUES(?,?,?)',(name,method,description))
    c.execute('INSERT INTO tasks(title,kind,assigned_to,employee_id,status,due,notes,created) VALUES(?,?,?,?,?,?,?,?)',
              ('Review onboarding checklist','HR Check',5,1,'Open',isodays(6),'Confirm checklist and signed declarations',now()))
    audit(c,9,'seed','system',0,'Synthetic demo dataset, not Sheffield workforce data')

with conn() as c:
    c.executescript(SCHEMA)
    seed(c)


def signed(id: int):
    payload=str(id)
    mac=hmac_new(SECRET.encode(),payload.encode(),'sha256').hexdigest()
    return payload+'.'+mac

def identity(req: Request):
    value=req.cookies.get('sc_session','')
    if '.' not in value: fail('Sign in to continue',401)
    number,mac=value.split('.',1)
    good=hmac_new(SECRET.encode(),number.encode(),'sha256').hexdigest()
    if not compare_digest(mac,good) or not number.isdecimal(): fail('Session invalid',401)
    with conn() as c: u=row(c.execute('SELECT * FROM users WHERE id=? AND active=1',(int(number),)).fetchone())
    if not u: fail('User unavailable',401)
    return u

def roles(u,*allowed):
    if u['role'] not in allowed and u['role']!='admin': fail('Access denied for this role',403)

def user_view(u):
    return {k:u[k] for k in ('id','name','email','role','department','job','grade','manager_id','fte','cost_center','active')}

def is_manager_of(c,u, target):
    if u['role'] in ('admin','hr'): return True
    if u['id']==target: return True
    return bool(c.execute('SELECT 1 FROM users WHERE id=? AND manager_id=?',(target,u['id'])).fetchone())

def see_employee(c,u,target):
    if u['role'] in ('admin','hr','payroll'): return True
    if u['id']==target: return True
    if u['role'] in ('manager','service') and is_manager_of(c,u,target): return True
    return False

def get_object(c,table,item):
    if table not in ('leave_requests','vacancies','applications','documents','tasks','courses','enrolments','payroll_runs','integration_events','expenses','time_entries','hr_cases'):
        fail('Invalid resource')
    r=row(c.execute(f'SELECT * FROM {table} WHERE id=?',(item,)).fetchone())
    if not r: fail('Not found',404)
    return r

def stage_event(c,system,event,entity,payload,actor):
    c.execute('''INSERT OR IGNORE INTO integration_events(system,event,entity_id,payload,status,created,updated)
                 VALUES(?,?,?,?,?,?,?)''',(system,event,entity,json.dumps(payload,sort_keys=True),'Queued',now(),now()))
    audit(c,actor,'queue-integration','integration',entity,system+' / '+event)

@APP.get('/')
def index(): return FileResponse(str(ROOT/'app'/'static'/'index.html'))

@APP.get('/api/health')
def health():
    with conn() as c: c.execute('SELECT 1').fetchone()
    return {'status':'ok','database':'connected','mode':'demonstration','oracle_connected':False,'email_connected':False}

@APP.get('/api/personas')
def personas():
    with conn() as c:
        return rows(c.execute('SELECT id,name,role,department,job FROM users WHERE id BETWEEN 1 AND 10 ORDER BY id').fetchall())

@APP.post('/api/login')
def login(payload: Payload):
    p=payload.data
    if str(p.get('pin',''))!=DEMO_PIN: fail('Incorrect demo access code',401)
    try: uid=int(p.get('user_id',0))
    except (ValueError,TypeError): fail('Invalid user',400)
    with conn() as c:
        u=row(c.execute('SELECT * FROM users WHERE id=? AND active=1',(uid,)).fetchone())
        if not u: fail('Unknown user',401)
        audit(c,uid,'demo-login','user',uid,'Demo persona selected')
    r=JSONResponse({'user':user_view(u),'demo':True})
    r.set_cookie('sc_session',signed(uid),httponly=True,samesite='lax',secure=os.environ.get('SHEFFIELD_COOKIE_SECURE')=='1',max_age=86400)
    return r

@APP.post('/api/logout')
def logout():
    r=JSONResponse({'ok':True}); r.delete_cookie('sc_session'); return r

@APP.get('/api/me')
def me(request:Request):return {'user':user_view(identity(request)),'demo':True}

@APP.get('/api/dashboard')
def dashboard(request:Request):
    u=identity(request)
    with conn() as c:
        own=u['id']; role=u['role']; scoped= role in ('employee','manager')
        people=c.execute('SELECT COUNT(*) FROM users WHERE active=1').fetchone()[0]
        leave=(c.execute('SELECT COUNT(*) FROM leave_requests WHERE status="Pending"').fetchone()[0] if role in ('admin','hr') else c.execute('SELECT COUNT(*) FROM leave_requests WHERE manager_id=? AND status="Pending"',(own,)).fetchone()[0] if role=='manager' else c.execute('SELECT COUNT(*) FROM leave_requests WHERE employee_id=? AND status="Pending"',(own,)).fetchone()[0])
        tasks=c.execute('SELECT COUNT(*) FROM tasks WHERE status="Open" AND (assigned_to=? OR ?=1)',(own,int(role=='admin'))).fetchone()[0]
        apps=c.execute('SELECT COUNT(*) FROM applications').fetchone()[0]
        courses=c.execute('SELECT COUNT(*) FROM courses').fetchone()[0]
        hires=c.execute('SELECT COUNT(*) FROM applications WHERE worker_id IS NOT NULL').fetchone()[0]
        pending_int=c.execute('SELECT COUNT(*) FROM integration_events WHERE status!="Delivered"').fetchone()[0]
        feed=rows(c.execute('''SELECT a.*,COALESCE(u.name,'System') actor FROM audit a
                           LEFT JOIN users u ON a.actor_id=u.id ORDER BY a.id DESC LIMIT 9''').fetchall()) if role in ('admin','hr','payroll','recruiter','service') else rows(c.execute('''SELECT a.*,COALESCE(u.name,'System') actor FROM audit a
                            LEFT JOIN users u ON a.actor_id=u.id WHERE a.actor_id=? ORDER BY a.id DESC LIMIT 9''',(own,)).fetchall())
        return {'headcount':people,'target_population':8000,'pending_leave':leave,'open_tasks':tasks,'applications':apps,
                'courses':courses,'new_hires':hires,'pending_integrations':pending_int,'activity':feed,
                'messages':c.execute('SELECT COUNT(*) FROM message_recipients WHERE recipient_id=? AND read_at IS NULL',(own,)).fetchone()[0],
                'note':'Illustrative people records; 8,000 is opportunity pricing baseline, not loaded demo records.'}

@APP.get('/api/people')
def people(request:Request):
    u=identity(request)
    with conn() as c:
        if u['role'] in ('admin','hr','payroll','service','learning','recruiter'):
            q=c.execute('SELECT id,name,job,department,grade,manager_id,fte,cost_center,active FROM users WHERE active=1 ORDER BY name')
        elif u['role']=='manager':
            q=c.execute('SELECT id,name,job,department,grade,manager_id,fte,cost_center,active FROM users WHERE id=? OR manager_id=? ORDER BY name',(u['id'],u['id']))
        else:
            q=c.execute('SELECT id,name,job,department,grade,manager_id,fte,cost_center,active FROM users WHERE id=?',(u['id'],))
        return rows(q.fetchall())

@APP.get('/api/org')
def organisation(request:Request):
    u=identity(request)
    with conn() as c:
        people=rows(c.execute('SELECT id,name,job,department,grade,manager_id,fte,cost_center,active FROM users WHERE active=1 ORDER BY manager_id,name').fetchall())
        if u['role']=='employee': people=[p for p in people if p['id']==u['id'] or p['id']==u['manager_id']]
        if u['role']=='manager': people=[p for p in people if p['id']==u['id'] or p['manager_id']==u['id'] or p['id']==u['manager_id']]
        group=rows(c.execute('''SELECT department,cost_center,COUNT(*) headcount,ROUND(SUM(fte),2) fte
                FROM users WHERE active=1 GROUP BY department,cost_center ORDER BY department''').fetchall())
        return {'people':people,'rollups':group if u['role'] in ('admin','hr','service','manager') else []}

@APP.get('/api/leave')
def leave_list(request:Request):
    u=identity(request)
    with conn() as c:
        if u['role'] in ('admin','hr'):
            q=c.execute('''SELECT l.*,x.name employee FROM leave_requests l JOIN users x ON x.id=l.employee_id ORDER BY l.id DESC''')
        elif u['role']=='manager':
            q=c.execute('''SELECT l.*,x.name employee FROM leave_requests l JOIN users x ON x.id=l.employee_id
                          WHERE l.employee_id=? OR l.manager_id=? ORDER BY l.id DESC''',(u['id'],u['id']))
        else:
            q=c.execute('''SELECT l.*,x.name employee FROM leave_requests l JOIN users x ON x.id=l.employee_id WHERE l.employee_id=? ORDER BY l.id DESC''',(u['id'],))
        used=c.execute('SELECT COALESCE(SUM(days),0) FROM leave_requests WHERE employee_id=? AND status="Approved" AND leave_type="Annual"',(u['id'],)).fetchone()[0]
        return {'items':rows(q.fetchall()), 'balance':round(u['leave_total']+u['leave_carry']+u['leave_purchased']-used,1),
                'entitlement':{'annual':u['leave_total'],'carry_forward':u['leave_carry'],'purchased':u['leave_purchased'],'bank_holidays':u['leave_bank']}}

@APP.post('/api/leave')
def create_leave(request:Request,payload:Payload):
    u=identity(request); p=payload.data
    require_fields(p,'start','ending','leave_type')
    start=dateval(p['start']); ending=dateval(p['ending'])
    if ending<start: fail('End date must be after start date')
    if start<date.today()-timedelta(days=15):fail('Please choose a current or future absence date')
    days=sum(1 for i in range((ending-start).days+1) if (start+timedelta(days=i)).weekday()<5)
    if days<1 or days>80:fail('Absence must cover between 1 and 80 weekdays')
    kind=limit(p['leave_type'],45)
    if kind not in ('Annual','Carer','Discretionary','Trade union','Sickness','Other'):fail('Invalid absence type')
    with conn() as c:
        overlap=c.execute('''SELECT 1 FROM leave_requests WHERE employee_id=? AND status IN ('Pending','Approved') AND start<=? AND ending>=?''',
                          (u['id'],str(ending),str(start))).fetchone()
        if overlap: fail('This absence overlaps an existing request',409)
        used=c.execute('SELECT COALESCE(SUM(days),0) FROM leave_requests WHERE employee_id=? AND status IN ("Pending","Approved") AND leave_type="Annual"',(u['id'],)).fetchone()[0]
        if kind=='Annual' and days>u['leave_total']+u['leave_carry']+u['leave_purchased']-used: fail('Insufficient annual leave balance',409)
        manager=u['manager_id'] or 9
        q=c.execute('INSERT INTO leave_requests(employee_id,manager_id,leave_type,start,ending,days,note,status,created) VALUES(?,?,?,?,?,?,?,?,?)',
                    (u['id'],manager,kind,str(start),str(ending),days,limit(p.get('note',''),500),'Pending',now()))
        audit(c,u['id'],'request','leave',q.lastrowid,f'{kind}: {start} to {ending}')
        return {'id':q.lastrowid,'status':'Pending','days':days}

@APP.post('/api/leave/{id}/decision')
def decide_leave(id:int,request:Request,payload:Payload):
    u=identity(request); roles(u,'manager','hr'); action=payload.data.get('decision')
    if action not in ('Approved','Rejected'):fail('Choose Approved or Rejected')
    with conn() as c:
        l=get_object(c,'leave_requests',id)
        if l['status']!='Pending':fail('Request has already been decided',409)
        if u['role']=='manager' and l['manager_id']!=u['id']:fail('Not a request for your team',403)
        c.execute('UPDATE leave_requests SET status=?,decided_at=? WHERE id=?',(action,now(),id))
        audit(c,u['id'],action.lower(),'leave',id,f"{l['employee_id']}: {l['days']} days")
        return {'ok':True,'status':action}

@APP.get('/api/vacancies')
def vacancy_list(request:Request):
    # Published careers are public; internal records appear only after sign-in.
    try: u=identity(request)
    except HTTPException: u=None
    with conn() as c:
        if u and u['role'] in ('manager','hr','recruiter','admin'):
            v=rows(c.execute('SELECT * FROM vacancies ORDER BY id DESC').fetchall())
        else: v=rows(c.execute('SELECT * FROM vacancies WHERE status="Published" ORDER BY id DESC').fetchall())
        return v

@APP.post('/api/vacancies')
def create_vacancy(request:Request,payload:Payload):
    u=identity(request); roles(u,'manager','hr','recruiter')
    p=payload.data; require_fields(p,'title','department','summary','closing')
    if dateval(p['closing'])<date.today():fail('Closing date cannot be in the past')
    with conn() as c:
        v=c.execute('''INSERT INTO vacancies(title,department,location,grade,salary,summary,cover_required,status,owner_id,created,closing)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)''',(limit(p['title'],120),limit(p['department'],90),limit(p.get('location','Sheffield'),90),
              limit(p.get('grade','G6'),20),limit(p.get('salary','Grade dependent'),70),limit(p['summary'],1200),
              int(bool(p.get('cover_required',False))),'Draft',u['id'],now(),str(dateval(p['closing']))))
        audit(c,u['id'],'create','vacancy',v.lastrowid,p['title']);return {'id':v.lastrowid,'status':'Draft'}

@APP.post('/api/vacancies/{id}/update')
def update_vacancy(id:int,request:Request,payload:Payload):
    u=identity(request);roles(u,'manager','hr','recruiter')
    p=payload.data
    with conn() as c:
        v=get_object(c,'vacancies',id)
        if u['role']=='manager' and v['owner_id']!=u['id']:fail('You can update only your vacancies',403)
        fields=[]; vals=[]
        for f,n in [('title',120),('summary',1200),('closing',15),('grade',20),('salary',70)]:
            if f in p:
                if f=='closing' and dateval(p[f])<date.today():fail('Closing date cannot be in the past')
                fields.append(f+'=?');vals.append(limit(p[f],n))
        if 'cover_required' in p: fields.append('cover_required=?');vals.append(int(bool(p['cover_required'])))
        if not fields:fail('No changes supplied')
        c.execute('UPDATE vacancies SET '+','.join(fields)+',revision=revision+1 WHERE id=?',(*vals,id))
        audit(c,u['id'],'revise','vacancy',id,'Post-publication edits versioned')
        return {'id':id,'revision':v['revision']+1}

@APP.post('/api/vacancies/{id}/publish')
def publish_vacancy(id:int,request:Request):
    u=identity(request);roles(u,'hr','recruiter')
    with conn() as c:
        v=get_object(c,'vacancies',id)
        if v['status']=='Closed':fail('Cannot publish a closed vacancy',409)
        c.execute('UPDATE vacancies SET status="Published" WHERE id=?',(id,))
        audit(c,u['id'],'publish','vacancy',id,v['title']);return {'ok':True}

@APP.post('/api/vacancies/{id}/close')
def close_vacancy(id:int,request:Request):
    u=identity(request);roles(u,'hr','recruiter')
    with conn() as c:
        get_object(c,'vacancies',id)
        c.execute('UPDATE vacancies SET status="Closed" WHERE id=?',(id,));audit(c,u['id'],'close','vacancy',id)
    return {'ok':True}

@APP.post('/api/apply/{vacancy_id}')
def apply(vacancy_id:int,payload:Payload):
    p=payload.data; require_fields(p,'name','email','statement')
    email=limit(p['email'],180).lower()
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email):fail('Enter a valid email')
    with conn() as c:
        v=get_object(c,'vacancies',vacancy_id)
        if v['status']!='Published' or dateval(v['closing'])<date.today():fail('Vacancy not accepting applications',409)
        if v['cover_required'] and not str(p.get('cover_letter','')).strip():fail('Cover letter required for this vacancy')
        if c.execute('SELECT 1 FROM applications WHERE vacancy_id=? AND lower(email)=?',(vacancy_id,email)).fetchone():fail('An application for this vacancy already exists for this email',409)
        token=secrets.token_urlsafe(27)
        a=c.execute('''INSERT INTO applications(vacancy_id,name,email,statement,cover_letter,source,access_token,stage,created,updated)
               VALUES(?,?,?,?,?,?,?,?,?,?)''',(vacancy_id,limit(p['name'],90),email,limit(p['statement'],2000),limit(p.get('cover_letter',''),2000),
              limit(p.get('source','Council careers'),60),token,'Applied',now(),now()))
        c.execute('INSERT INTO candidate_events(application_id,title,body,event_kind,created) VALUES(?,?,?,?,?)',(a.lastrowid,'Application received','Your application has been saved and is awaiting review.','Status',now()))
        audit(c,None,'candidate-apply','application',a.lastrowid,'New applicant via career site')
        return {'id':a.lastrowid,'access_token':token,'stage':'Applied'}

@APP.get('/api/applications')
def applications(request:Request):
    u=identity(request); roles(u,'hr','recruiter','manager')
    with conn() as c:
        sql='''SELECT a.id,a.vacancy_id,a.name,a.email,a.source,a.stage,a.interview_slot,a.interview_type,
                    a.interview_feedback,a.interview_score,a.offer_status,a.worker_id,a.created,v.title vacancy
             FROM applications a JOIN vacancies v ON v.id=a.vacancy_id'''
        if u['role']=='manager':
            return rows(c.execute(sql+' WHERE v.owner_id=? ORDER BY a.id DESC',(u['id'],)).fetchall())
        return rows(c.execute(sql+' ORDER BY a.id DESC').fetchall())

@APP.get('/api/candidate/{token}')
def candidate(token:str):
    with conn() as c:
        r=row(c.execute('''SELECT a.id,a.name,a.email,a.stage,a.interview_slot,a.interview_type,a.offer_status,
                     a.created,v.title vacancy,v.location FROM applications a JOIN vacancies v ON v.id=a.vacancy_id
                     WHERE a.access_token=?''',(token,)).fetchone())
        if not r:fail('Application access code not found',404)
        return r

@APP.post('/api/candidate/{token}/interview')
def candidate_interview(token:str,payload:Payload):
    p=payload.data;require_fields(p,'slot')
    slot=limit(p['slot'],40)
    try: dt=datetime.fromisoformat(slot.replace('Z','+00:00'))
    except ValueError:fail('Invalid interview slot')
    if dt.replace(tzinfo=None)<datetime.now()+timedelta(minutes=30):fail('Interview slot must be in the future')
    with conn() as c:
        a=row(c.execute('SELECT * FROM applications WHERE access_token=?',(token,)).fetchone())
        if not a:fail('Application access code not found',404)
        if a['stage'] not in ('Shortlisted','Interview Scheduled'):fail('Interview scheduling is not available at this stage',409)
        typ=p.get('type','Video')
        if typ not in ('Video','In-person'):fail('Invalid interview type')
        c.execute('UPDATE applications SET stage="Interview Scheduled",interview_slot=?,interview_type=?,updated=? WHERE id=?',
                  (slot,typ,now(),a['id']))
        stage_event(c,'Outlook Calendar','interview-scheduled',a['id'],{'slot':slot,'type':typ},None)
        c.execute('INSERT INTO candidate_events(application_id,title,body,event_kind,created) VALUES(?,?,?,?,?)',(a['id'],'Interview preference saved','Your '+typ.lower()+' interview is scheduled for '+slot+'. You can reschedule until selection is completed.','Status',now()))
        audit(c,None,'candidate-schedule','application',a['id'],slot)
        return {'ok':True,'stage':'Interview Scheduled','slot':slot}

@APP.post('/api/candidate/{token}/withdraw')
def candidate_withdraw(token:str):
    with conn() as c:
        a=row(c.execute('SELECT * FROM applications WHERE access_token=?',(token,)).fetchone())
        if not a:fail('Application access code not found',404)
        if a['worker_id'] or a['stage']=='Withdrawn':fail('Cannot withdraw this application',409)
        c.execute('UPDATE applications SET stage="Withdrawn",updated=? WHERE id=?',(now(),a['id']))
        stage_event(c,'Corporate Finance','candidate-withdrawal',a['id'],{'candidate':a['name']},None)
        c.execute('INSERT INTO candidate_events(application_id,title,body,event_kind,created) VALUES(?,?,?,?,?)',(a['id'],'Application withdrawn','Your withdrawal has been recorded.','Status',now()))
        audit(c,None,'withdraw','application',a['id']);return {'ok':True}

@APP.post('/api/applications/{id}/stage')
def application_stage(id:int,request:Request,payload:Payload):
    u=identity(request);roles(u,'recruiter','hr','manager')
    p=payload.data; action=p.get('stage')
    if action not in ('Shortlisted','Rejected','Interview Completed','Offered','Offer Accepted','Checks Complete','Onboarded'):
        fail('Invalid application stage')
    with conn() as c:
        a=get_object(c,'applications',id); v=get_object(c,'vacancies',a['vacancy_id'])
        if u['role']=='manager' and v['owner_id']!=u['id']:fail('Not your vacancy',403)
        if a['stage'] in ('Rejected','Withdrawn','Onboarded'):fail('Application is no longer active',409)
        allowed={
          'Applied':('Shortlisted','Rejected'),
          'Shortlisted':('Rejected',),
          'Interview Scheduled':('Interview Completed','Rejected'),
          'Interview Completed':('Offered','Rejected'),
          'Offered':('Offer Accepted','Rejected'),
          'Offer Accepted':('Checks Complete',),
          'Checks Complete':('Onboarded',)
        }
        if action not in allowed.get(a['stage'],()):fail(f"Cannot move from {a['stage']} to {action}",409)
        feedback=limit(p.get('feedback',''),900)
        score=p.get('score',None)
        if action=='Interview Completed' and (not feedback or score is None):fail('Interview score and detailed feedback are required')
        if score is not None:score=int(numeric(score,0,5))
        c.execute('''UPDATE applications SET stage=?,interview_feedback=CASE WHEN ?!='' THEN ? ELSE interview_feedback END,
                      interview_score=COALESCE(?,interview_score),updated=? WHERE id=?''',(action,feedback,feedback,score,now(),id))
        if action=='Onboarded':
            if c.execute('SELECT 1 FROM users WHERE lower(email)=?',(a['email'].lower(),)).fetchone():fail('This employee already exists. Review duplicate before onboarding.',409)
            new=c.execute('''INSERT INTO users(name,email,role,department,job,grade,manager_id,fte,salary,cost_center,created)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?)''',(a['name'],a['email'],'employee',v['department'],v['title'],v['grade'],v['owner_id'],1,32500,'NEW-STARTER',now())).lastrowid
            c.execute('UPDATE applications SET worker_id=? WHERE id=?',(new,id))
            for title,kind,owner in [('Submit right-to-work evidence','Onboarding',new),('Verify starter records','HR Check',5),('Assign safeguarding learning','Learning',7)]:
                c.execute('INSERT INTO tasks(title,kind,assigned_to,employee_id,status,due,created) VALUES(?,?,?,?,?,?,?)',(title,kind,owner,new,'Open',isodays(7),now()))
            stage_event(c,'Corporate Finance','new-starter',new,{'name':a['name'],'dept':v['department']},u['id'])
            stage_event(c,'Microsoft Entra ID','identity-provision',new,{'email':a['email']},u['id'])
        c.execute('INSERT INTO candidate_events(application_id,title,body,event_kind,created) VALUES(?,?,?,?,?)',(id,'Application status: '+action,'Your application has moved to '+action.lower()+'.','Status',now()))
        audit(c,u['id'],action.lower(),'application',id,feedback or a['name'])
        return {'id':id,'stage':action,'worker_id':c.execute('SELECT worker_id FROM applications WHERE id=?',(id,)).fetchone()[0]}

@APP.get('/api/tasks')
def tasks(request:Request):
    u=identity(request)
    with conn() as c:
        if u['role'] in ('hr','admin'):
            q=c.execute('SELECT t.*,u.name owner FROM tasks t LEFT JOIN users u ON u.id=t.assigned_to ORDER BY t.id DESC')
        else:q=c.execute('SELECT t.*,u.name owner FROM tasks t LEFT JOIN users u ON u.id=t.assigned_to WHERE t.assigned_to=? ORDER BY t.id DESC',(u['id'],))
        return rows(q.fetchall())

@APP.post('/api/tasks')
def add_task(request:Request,payload:Payload):
    u=identity(request);roles(u,'hr','manager','learning')
    p=payload.data; require_fields(p,'title','assigned_to')
    with conn() as c:
        try: assigned=int(p['assigned_to'])
        except (TypeError,ValueError):fail('Invalid assignee')
        if not c.execute('SELECT 1 FROM users WHERE id=? AND active=1',(assigned,)).fetchone():fail('Assignee not found')
        if u['role']=='manager' and assigned!=u['id'] and not is_manager_of(c,u,assigned):fail('Not your team',403)
        q=c.execute('INSERT INTO tasks(title,kind,assigned_to,employee_id,status,due,notes,created) VALUES(?,?,?,?,?,?,?,?)',
                 (limit(p['title'],180),limit(p.get('kind','HR Process'),60),assigned,int(p.get('employee_id',assigned)),
                  'Open',str(dateval(p.get('due',isodays(7)))),limit(p.get('notes',''),700),now()))
        audit(c,u['id'],'create','task',q.lastrowid,p['title']);return {'id':q.lastrowid}

@APP.post('/api/tasks/{id}/complete')
def complete_task(id:int,request:Request):
    u=identity(request)
    with conn() as c:
        t=get_object(c,'tasks',id)
        if t['assigned_to']!=u['id'] and u['role'] not in ('hr','admin'):fail('Task not assigned to you',403)
        if t['status']!='Open':fail('Task already completed',409)
        c.execute('UPDATE tasks SET status="Completed",completed=? WHERE id=?',(now(),id))
        audit(c,u['id'],'complete','task',id,t['title']);return {'ok':True}

@APP.get('/api/documents')
def documents(request:Request):
    u=identity(request)
    with conn() as c:
        if u['role'] in ('hr','admin'):
            q=c.execute('SELECT d.*,u.name employee FROM documents d JOIN users u ON u.id=d.employee_id WHERE d.deleted=0 ORDER BY d.id DESC')
        else:
            q=c.execute('SELECT d.*,u.name employee FROM documents d JOIN users u ON u.id=d.employee_id WHERE d.deleted=0 AND d.employee_id=? ORDER BY d.id DESC',(u['id'],))
        return rows(q.fetchall())

@APP.post('/api/documents')
async def upload_document(request:Request,file:UploadFile=File(...),employee_id:int|None=None,doc_type:str='Employment',retention_until:str='2033-12-31'):
    u=identity(request)
    employee_id=employee_id or u['id']
    with conn() as c:
        if not see_employee(c,u,employee_id) or (u['role'] not in ('admin','hr') and employee_id!=u['id']):fail('Upload forbidden',403)
        if not c.execute('SELECT 1 FROM users WHERE id=?',(employee_id,)).fetchone():fail('Employee not found',404)
        dateval(retention_until)
        if dateval(retention_until)<date.today():fail('Retention date must be in the future')
        filename=Path(file.filename or '').name
        if not filename or Path(filename).suffix.lower() not in ('.pdf','.txt','.png','.jpg','.jpeg','.docx'):
            fail('Allowed formats: PDF, TXT, PNG, JPEG, DOCX')
        content=await file.read(5*1024*1024+1)
        if not content or len(content)>5*1024*1024:fail('Document must be between 1 byte and 5 MB')
        safe=uuid.uuid4().hex+Path(filename).suffix.lower()
        (UPLOADS/safe).write_bytes(content)
        q=c.execute('''INSERT INTO documents(employee_id,name,doc_type,classification,stored_name,retention_until,uploaded_by,created)
                     VALUES(?,?,?,?,?,?,?,?)''',(employee_id,limit(filename,200),limit(doc_type,65),'Employee confidential',safe,retention_until,u['id'],now()))
        audit(c,u['id'],'upload','document',q.lastrowid,filename)
        return {'id':q.lastrowid,'filename':filename}

@APP.get('/api/documents/{id}/download')
def download_document(id:int,request:Request):
    u=identity(request)
    with conn() as c:
        d=get_object(c,'documents',id)
        if d['deleted'] or not see_employee(c,u,d['employee_id']):fail('Access denied',403)
        path=UPLOADS/d['stored_name']
        if not path.exists():fail('Document content missing',404)
        audit(c,u['id'],'view','document',id,d['name'])
        return FileResponse(path,filename=d['name'])

@APP.post('/api/documents/{id}/archive')
def archive_document(id:int,request:Request):
    u=identity(request);roles(u,'hr')
    with conn() as c:
        d=get_object(c,'documents',id)
        if d['deleted']:fail('Document already purged',409)
        c.execute('UPDATE documents SET archived=1 WHERE id=?',(id,));audit(c,u['id'],'archive','document',id)
    return {'ok':True}

@APP.post('/api/documents/purge')
def purge_documents(request:Request):
    u=identity(request);roles(u,'hr')
    with conn() as c:
        docs=rows(c.execute('SELECT * FROM documents WHERE deleted=0 AND archived=1 AND retention_until<?',(today(),)).fetchall())
        for d in docs:
            path=UPLOADS/d['stored_name']
            if path.exists():path.unlink()
            c.execute('UPDATE documents SET deleted=1 WHERE id=?',(d['id'],))
            audit(c,u['id'],'purge','document',d['id'],'Expired retention and previously archived')
    return {'purged':len(docs)}

@APP.get('/api/learning')
def learning(request:Request):
    u=identity(request)
    with conn() as c:
        courses=rows(c.execute('''SELECT c.*, (SELECT COUNT(*) FROM enrolments e WHERE e.course_id=c.id AND e.status!="Cancelled") booked
                    FROM courses c ORDER BY c.title''').fetchall())
        if u['role'] in ('learning','admin','hr'):
            q=c.execute('''SELECT e.*,c.title course,u.name employee FROM enrolments e JOIN courses c ON c.id=e.course_id
                       JOIN users u ON u.id=e.employee_id ORDER BY e.id DESC''')
        elif u['role']=='manager':
            q=c.execute('''SELECT e.*,c.title course,u.name employee FROM enrolments e JOIN courses c ON c.id=e.course_id JOIN users u ON u.id=e.employee_id
                         WHERE e.employee_id=? OR u.manager_id=? ORDER BY e.id DESC''',(u['id'],u['id']))
        else:q=c.execute('''SELECT e.*,c.title course,u.name employee FROM enrolments e JOIN courses c ON c.id=e.course_id
                      JOIN users u ON u.id=e.employee_id WHERE e.employee_id=? ORDER BY e.id DESC''',(u['id'],))
        return {'courses':courses,'enrolments':rows(q.fetchall())}

@APP.post('/api/learning/{id}/enrol')
def enrol_course(id:int,request:Request):
    u=identity(request)
    with conn() as c:
        course=get_object(c,'courses',id)
        count=c.execute('SELECT COUNT(*) FROM enrolments WHERE course_id=? AND status!="Cancelled"',(id,)).fetchone()[0]
        if count>=course['seats']:fail('Course is fully booked',409)
        if c.execute('SELECT 1 FROM enrolments WHERE course_id=? AND employee_id=?',(id,u['id'])).fetchone():fail('You are already enrolled',409)
        q=c.execute('INSERT INTO enrolments(course_id,employee_id,status,created) VALUES(?,?,?,?)',(id,u['id'],'Enrolled',now()))
        audit(c,u['id'],'enrol','learning',q.lastrowid,course['title']);return {'id':q.lastrowid}

@APP.post('/api/learning/{id}/complete')
def finish_course(id:int,request:Request):
    u=identity(request)
    with conn() as c:
        e=get_object(c,'enrolments',id)
        if e['employee_id']!=u['id'] and u['role'] not in ('learning','admin','hr'):fail('Cannot change this record',403)
        if e['status']!='Enrolled':fail('Learning already completed',409)
        c.execute('UPDATE enrolments SET status="Completed",completed=? WHERE id=?',(now(),id))
        audit(c,u['id'],'complete','learning',id);return {'ok':True}

@APP.get('/api/payroll')
def payroll(request:Request):
    u=identity(request)
    with conn() as c:
        if u['role'] in ('payroll','hr','admin'):
            runs=rows(c.execute('SELECT * FROM payroll_runs ORDER BY id DESC').fetchall())
        else:runs=[]
        own=rows(c.execute('''SELECT i.*,r.period,r.status FROM payroll_items i JOIN payroll_runs r ON r.id=i.run_id
                     WHERE i.employee_id=? AND r.status="Finalised" ORDER BY r.id DESC''',(u['id'],)).fetchall())
        return {'runs':runs,'payslips':own,'disclaimer':'Illustrative gross and example deductions only. Not certified HMRC, NI or LGPS/TPS calculations.'}

@APP.post('/api/payroll/run')
def payroll_run(request:Request,payload:Payload):
    u=identity(request);roles(u,'payroll')
    p=payload.data;period=limit(p.get('period',date.today().strftime('%Y-%m')),7)
    if not re.fullmatch(r'20\d{2}-(0[1-9]|1[0-2])',period):fail('Period must be YYYY-MM')
    with conn() as c:
        if c.execute('SELECT 1 FROM payroll_runs WHERE period=?',(period,)).fetchone():fail('Period has already been processed',409)
        active=rows(c.execute('SELECT * FROM users WHERE active=1').fetchall())
        run=c.execute('INSERT INTO payroll_runs(period,status,headcount,gross,net,deduction,created) VALUES(?,?,?,?,?,?,?)',(period,'Draft',len(active),0,0,0,now()))
        gross_sum=net_sum=deduct_sum=0
        for e in active:
            gross=round(e['salary']/12,2)
            # Purely illustrative fixed demo rate; expressly not statutory UK payroll tax/pension logic.
            deduction=round(gross*0.18,2)
            net=round(gross-deduction,2)
            c.execute('INSERT INTO payroll_items(run_id,employee_id,gross,deduction,net) VALUES(?,?,?,?,?)',(run.lastrowid,e['id'],gross,deduction,net))
            gross_sum+=gross;net_sum+=net;deduct_sum+=deduction
        c.execute('UPDATE payroll_runs SET gross=?,net=?,deduction=? WHERE id=?',(round(gross_sum,2),round(net_sum,2),round(deduct_sum,2),run.lastrowid))
        audit(c,u['id'],'calculate','payroll',run.lastrowid,period+' - illustrative only')
        return {'id':run.lastrowid,'headcount':len(active),'gross':round(gross_sum,2),'status':'Draft'}

@APP.post('/api/payroll/{id}/finalise')
def payroll_finalise(id:int,request:Request):
    u=identity(request);roles(u,'payroll')
    with conn() as c:
        r=get_object(c,'payroll_runs',id)
        if r['status']!='Draft':fail('Payroll already finalised',409)
        c.execute('UPDATE payroll_runs SET status="Finalised",completed=? WHERE id=?',(now(),id))
        stage_event(c,'Payment Services','payment-export',id,{'period':r['period'],'net':r['net']},u['id'])
        audit(c,u['id'],'finalise','payroll',id,r['period'])
        return {'status':'Finalised'}

@APP.get('/api/expenses')
def expenses(request:Request):
    u=identity(request)
    with conn() as c:
        if u['role'] in ('hr','admin'):q=c.execute('SELECT x.*,u.name employee FROM expenses x JOIN users u ON u.id=x.employee_id ORDER BY x.id DESC')
        elif u['role']=='manager':q=c.execute('SELECT x.*,u.name employee FROM expenses x JOIN users u ON u.id=x.employee_id WHERE x.employee_id=? OR x.manager_id=? ORDER BY x.id DESC',(u['id'],u['id']))
        else:q=c.execute('SELECT x.*,u.name employee FROM expenses x JOIN users u ON u.id=x.employee_id WHERE x.employee_id=? ORDER BY x.id DESC',(u['id'],))
        return rows(q.fetchall())

@APP.post('/api/expenses')
def expense_create(request:Request,payload:Payload):
    u=identity(request);p=payload.data;require_fields(p,'category','amount','detail')
    with conn() as c:
        q=c.execute('INSERT INTO expenses(employee_id,category,amount,detail,manager_id,created) VALUES(?,?,?,?,?,?)',
                    (u['id'],limit(p['category'],60),numeric(p['amount'],0.01,5000),limit(p['detail'],500),u['manager_id'] or 9,now()))
        audit(c,u['id'],'submit','expense',q.lastrowid,p['category']);return {'id':q.lastrowid}

@APP.post('/api/expenses/{id}/decision')
def expense_decide(id:int,request:Request,payload:Payload):
    u=identity(request);roles(u,'manager','hr')
    decision=payload.data.get('decision')
    if decision not in ('Approved','Rejected'):fail('Invalid decision')
    with conn() as c:
        x=get_object(c,'expenses',id)
        if x['status']!='Submitted':fail('Already reviewed',409)
        if u['role']=='manager' and x['manager_id']!=u['id']:fail('Not your team',403)
        c.execute('UPDATE expenses SET status=? WHERE id=?',(decision,id))
        audit(c,u['id'],decision.lower(),'expense',id);return {'ok':True}

@APP.get('/api/cases')
def cases(request:Request):
    u=identity(request);roles(u,'hr')
    with conn() as c:return rows(c.execute('SELECT h.*,u.name employee FROM hr_cases h LEFT JOIN users u ON u.id=h.employee_id ORDER BY h.id DESC').fetchall())

@APP.post('/api/cases')
def case_create(request:Request,payload:Payload):
    u=identity(request);roles(u,'hr');p=payload.data;require_fields(p,'title','employee_id','details')
    with conn() as c:
        emp=int(p['employee_id'])
        if not c.execute('SELECT 1 FROM users WHERE id=?',(emp,)).fetchone():fail('Employee not found',404)
        h=c.execute('INSERT INTO hr_cases(employee_id,category,title,details,owner_id,created) VALUES(?,?,?,?,?,?)',
                    (emp,limit(p.get('category','People Services'),60),limit(p['title'],150),limit(p['details'],1800),u['id'],now()))
        audit(c,u['id'],'create','case',h.lastrowid,'Optional HR casework demonstrator')
        return {'id':h.lastrowid}

@APP.post('/api/cases/{id}/close')
def case_close(id:int,request:Request):
    u=identity(request);roles(u,'hr')
    with conn() as c:
        h=get_object(c,'hr_cases',id)
        if h['status']=='Closed':fail('Already closed',409)
        c.execute('UPDATE hr_cases SET status="Closed" WHERE id=?',(id,))
        audit(c,u['id'],'close','case',id);return {'ok':True}

@APP.get('/api/integrations')
def integrations(request:Request):
    u=identity(request);roles(u,'admin','hr')
    with conn() as c:
        return {'systems':rows(c.execute('SELECT * FROM integrations').fetchall()),
                'events':rows(c.execute('SELECT * FROM integration_events ORDER BY id DESC LIMIT 100').fetchall())}

@APP.post('/api/integrations/{id}/process')
def process_integration(id:int,request:Request,payload:Payload):
    u=identity(request);roles(u,'admin')
    with conn() as c:
        e=get_object(c,'integration_events',id)
        if e['status']=='Delivered':fail('Already delivered',409)
        simulate_failure=bool(payload.data.get('fail',False))
        state='Failed' if simulate_failure else 'Delivered'
        # Delivery is to a local mock adapter, not a third-party endpoint.
        c.execute('UPDATE integration_events SET attempts=attempts+1,status=?,error=?,updated=? WHERE id=?',
                  (state,'Simulated remote timeout' if simulate_failure else None,now(),id))
        audit(c,u['id'],'mock-send' if not simulate_failure else 'mock-failure','integration',id,state)
        return {'status':state,'attempts':e['attempts']+1,'adapter':'Local mock only'}

@APP.get('/api/reports')
def report(request:Request,group:str='department',metric:str='headcount',filter:str=''):
    u=identity(request);roles(u,'manager','service','hr','payroll','recruiter','learning')
    if group not in ('department','cost_center','grade'):fail('Invalid grouping')
    if metric not in ('headcount','fte','salary'):fail('Invalid metric')
    if metric=='salary' and u['role'] not in ('admin','hr','payroll','service'):fail('Pay figures restricted',403)
    with conn() as c:
        where=' WHERE active=1'; args=[]
        if u['role']=='manager':where+=' AND (id=? OR manager_id=?)';args.extend([u['id'],u['id']])
        if filter:
            where+=' AND (department LIKE ? OR cost_center LIKE ? OR grade LIKE ?)';args.extend(['%'+filter[:80]+'%']*3)
        expression={'headcount':'COUNT(*)','fte':'ROUND(SUM(fte),2)','salary':'ROUND(SUM(salary),2)'}[metric]
        values=rows(c.execute(f'SELECT {group} label,{expression} value FROM users {where} GROUP BY {group} ORDER BY value DESC',args).fetchall())
        audit(c,u['id'],'run','report',0,f'{group}/{metric}')
        return {'group':group,'metric':metric,'items':values,'total':round(sum(v['value'] or 0 for v in values),2)}

@APP.get('/api/reports/export')
def report_export(request:Request,group:str='department',metric:str='headcount',filter:str=''):
    data=report(request,group,metric,filter)
    f=io.StringIO();w=csv.writer(f);w.writerow([group,metric]);w.writerows([(a['label'],a['value']) for a in data['items']])
    return StreamingResponse(iter([f.getvalue()]),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="sheffield-report.csv"'})

@APP.get('/api/messages')
def messages(request:Request):
    u=identity(request)
    with conn() as c:
        return rows(c.execute('''SELECT m.id,m.subject,m.body,m.force_notify,m.created,u.name sender,mr.read_at
            FROM message_recipients mr JOIN messages m ON m.id=mr.message_id JOIN users u ON u.id=m.sender_id
            WHERE mr.recipient_id=? ORDER BY m.id DESC''',(u['id'],)).fetchall())

@APP.post('/api/messages')
def message_send(request:Request,payload:Payload):
    u=identity(request);roles(u,'hr','manager','service','recruiter','learning')
    p=payload.data;require_fields(p,'subject','body','recipients')
    sub=limit(p['subject'],255);body=limit(p['body'],4000)
    recipient_ids=p['recipients']
    if not isinstance(recipient_ids,list) or len(recipient_ids)==0 or len(recipient_ids)>100:fail('Choose 1-100 recipients')
    try: recipient_ids=sorted(set(int(id) for id in recipient_ids))
    except (TypeError,ValueError):fail('Invalid recipient selection')
    with conn() as c:
        valid=[x[0] for x in c.execute('SELECT id FROM users WHERE active=1').fetchall()]
        if any(id not in valid for id in recipient_ids):fail('Unknown recipient')
        m=c.execute('INSERT INTO messages(subject,body,sender_id,force_notify,created) VALUES(?,?,?,?,?)',
                    (sub,body,u['id'],int(bool(p.get('force_notify',False))),now()))
        for id in recipient_ids:c.execute('INSERT INTO message_recipients(message_id,recipient_id) VALUES(?,?)',(m.lastrowid,id))
        audit(c,u['id'],'send','message',m.lastrowid,'BCC-style private recipients; notifications are locally queued only')
        return {'id':m.lastrowid,'recipient_count':len(recipient_ids),'email_status':'Demo queue only - no live email dispatched'}

@APP.post('/api/messages/{id}/read')
def message_read(id:int,request:Request):
    u=identity(request)
    with conn() as c:
        result=c.execute('UPDATE message_recipients SET read_at=? WHERE message_id=? AND recipient_id=?',(now(),id,u['id']))
        if result.rowcount==0:fail('Not your message',403)
        return {'ok':True}

@APP.get('/api/audit')
def audit_list(request:Request):
    u=identity(request);roles(u,'hr','payroll','service')
    with conn() as c:return rows(c.execute('''SELECT a.*,COALESCE(u.name,'External / System') actor FROM audit a
           LEFT JOIN users u ON a.actor_id=u.id ORDER BY a.id DESC LIMIT 250''').fetchall())

@APP.get('/api/capabilities')
def capabilities():
    return json.loads((ROOT/'docs'/'capability_matrix.json').read_text(encoding='utf-8'))

@APP.exception_handler(HTTPException)
async def http_exception(request,exc):
    return JSONResponse({'error':str(exc.detail)},status_code=exc.status_code)

app=APP

@APP.post('/api/demo/reset')
def reset_demo(request:Request,payload:Payload):
    u=identity(request);roles(u,'admin')
    if payload.data.get('confirm')!='RESET DEMO':fail('Type RESET DEMO to confirm')
    with conn() as c:
        for table in ('message_recipients','messages','candidate_events','integration_events','hr_cases','expenses','time_entries',
          'payroll_items','payroll_runs','enrolments','profiles','tasks','documents','applications','vacancies','courses',
          'leave_requests','integrations','audit','users'):
            c.execute('DELETE FROM '+table)
        seed(c)
        audit(c,u['id'],'reset','system',0,'Demonstration dataset restored')
    for path in UPLOADS.iterdir():
        if path.is_file():path.unlink()
    return {'ok':True,'message':'Demo records reset to clean initial state'}

@APP.get('/api/profile')
def profile(request:Request):
    u=identity(request)
    with conn() as c:
        p=row(c.execute('SELECT * FROM profiles WHERE employee_id=?',(u['id'],)).fetchone()) or {'phone':'','address':'','emergency_contact':''}
        return {'user':user_view(u),'profile':p}

@APP.post('/api/profile')
def profile_update(request:Request,payload:Payload):
    u=identity(request);p=payload.data
    with conn() as c:
        values=(limit(p.get('phone',''),50),limit(p.get('address',''),280),limit(p.get('emergency_contact',''),140),now(),u['id'])
        c.execute('''INSERT INTO profiles(phone,address,emergency_contact,updated,employee_id) VALUES(?,?,?,?,?)
        ON CONFLICT(employee_id) DO UPDATE SET phone=excluded.phone,address=excluded.address,
        emergency_contact=excluded.emergency_contact,updated=excluded.updated''',values)
        audit(c,u['id'],'update','profile',u['id'],'Employee updated contact details')
        return {'ok':True}

@APP.get('/api/time')
def timesheets(request:Request):
    u=identity(request)
    with conn() as c:
        sql='''SELECT t.*,u.name employee FROM time_entries t JOIN users u ON u.id=t.employee_id'''
        if u['role'] in ('admin','hr','payroll'):
            q=c.execute(sql+' ORDER BY t.id DESC')
        elif u['role']=='manager':q=c.execute(sql+' WHERE t.employee_id=? OR t.manager_id=? ORDER BY t.id DESC',(u['id'],u['id']))
        else:q=c.execute(sql+' WHERE t.employee_id=? ORDER BY t.id DESC',(u['id'],))
        return rows(q.fetchall())

@APP.post('/api/time')
def time_add(request:Request,payload:Payload):
    u=identity(request);p=payload.data;require_fields(p,'week_start','hours')
    week=dateval(p['week_start'])
    if week.weekday()!=0:fail('Timesheet week must start on a Monday')
    if week>date.today()+timedelta(days=14):fail('Cannot submit a timesheet more than two weeks in advance')
    with conn() as c:
        if c.execute('SELECT 1 FROM time_entries WHERE week_start=? AND employee_id=?',(str(week),u['id'])).fetchone():fail('Timesheet already exists for this week',409)
        q=c.execute('INSERT INTO time_entries(employee_id,week_start,hours,manager_id) VALUES(?,?,?,?)',
                    (u['id'],str(week),numeric(p['hours'],0.25,65),u['manager_id'] or 9))
        audit(c,u['id'],'submit','timesheet',q.lastrowid,str(week));return {'id':q.lastrowid}

@APP.post('/api/time/{id}/decision')
def time_decide(id:int,request:Request,payload:Payload):
    u=identity(request);roles(u,'manager','hr')
    decision=payload.data.get('decision')
    if decision not in ('Approved','Rejected'):fail('Invalid decision')
    with conn() as c:
        x=get_object(c,'time_entries',id)
        if x['status']!='Submitted':fail('Timesheet already decided',409)
        if u['role']=='manager' and x['manager_id']!=u['id']:fail('Not your team',403)
        c.execute('UPDATE time_entries SET status=? WHERE id=?',(decision,id))
        if decision=='Approved':stage_event(c,'Corporate Finance','time-approved',id,{'hours':x['hours'],'employee_id':x['employee_id']},u['id'])
        audit(c,u['id'],decision.lower(),'timesheet',id);return {'ok':True}

@APP.post('/api/tasks/{id}/reassign')
def task_reassign(id:int,request:Request,payload:Payload):
    u=identity(request);roles(u,'manager','hr')
    with conn() as c:
        t=get_object(c,'tasks',id)
        try:target=int(payload.data.get('assigned_to',0))
        except (TypeError,ValueError):fail('Invalid assignee')
        if not c.execute('SELECT 1 FROM users WHERE id=? AND active=1',(target,)).fetchone():fail('Assignee not found',404)
        if t['status']!='Open':fail('Completed task cannot be reassigned',409)
        if u['role']=='manager' and (t['assigned_to']!=u['id'] or not is_manager_of(c,u,target)):fail('Cannot reassign this task',403)
        c.execute('UPDATE tasks SET assigned_to=? WHERE id=?',(target,id))
        audit(c,u['id'],'reassign','task',id,str(target));return {'ok':True}

@APP.get('/api/candidate/{token}/messages')
def candidate_messages(token:str):
    with conn() as c:
        a=row(c.execute('SELECT id FROM applications WHERE access_token=?',(token,)).fetchone())
        if not a:fail('Application access code not found',404)
        return rows(c.execute('''SELECT id,title,body,event_kind,created FROM candidate_events
             WHERE application_id=? AND event_kind!='Internal' ORDER BY id DESC''',(a['id'],)).fetchall())

@APP.post('/api/applications/{id}/message')
def recruiter_message(id:int,request:Request,payload:Payload):
    u=identity(request);roles(u,'recruiter','hr','manager')
    p=payload.data;require_fields(p,'subject','body')
    with conn() as c:
        a=get_object(c,'applications',id);v=get_object(c,'vacancies',a['vacancy_id'])
        if u['role']=='manager' and v['owner_id']!=u['id']:fail('Not your vacancy',403)
        item=c.execute('INSERT INTO candidate_events(application_id,title,body,event_kind,created) VALUES(?,?,?,?,?)',
                      (id,limit(p['subject'],255),limit(p['body'],4000),'Recruiter message',now()))
        audit(c,u['id'],'candidate-correspondence','application',id,'Portal inbox message; no real e-mail')
        return {'id':item.lastrowid,'delivery':'Candidate portal inbox (demo only)'}

@APP.post('/api/documents/{id}/simulate-expiry')
def simulate_document_expiry(id:int,request:Request):
    u=identity(request);roles(u,'admin')
    with conn() as c:
        d=get_object(c,'documents',id)
        if d['deleted'] or not d['archived']:fail('Archive the document before simulating retention expiry',409)
        c.execute('UPDATE documents SET retention_until=? WHERE id=?',(isodays(-1),id))
        audit(c,u['id'],'demo-expiry','document',id,'Artificially expired for purge walkthrough; demo only')
        return {'ok':True,'retention_until':isodays(-1)}
