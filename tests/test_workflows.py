"""Backend integration and negative-path tests against a fresh isolated SQLite database."""
import io
import os
import tempfile
from datetime import date,timedelta
os.environ['SHEFFIELD_DATA_DIR']=tempfile.mkdtemp(prefix='sheffield-test-')
from fastapi.testclient import TestClient
from app.main import app
import pytest

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
        as_user(c,9)
        r=c.post('/api/demo/reset',json={'data':{'confirm':'RESET DEMO'}})
        assert r.status_code==200,r.text

def as_user(c,id):
    r=c.post('/api/login',json={'data':{'user_id':id,'pin':'sheffield-demo'}})
    assert r.status_code==200,r.text
    return r.json()['user']

def post(c,path,**payload):return c.post('/api'+path,json={'data':payload})
def get(c,path):return c.get('/api'+path)
def future(n=14):return (date.today()+timedelta(days=n)).isoformat()

def test_health_and_capability_scope(client):
    x=get(client,'/health').json();assert x['oracle_connected'] is False
    a=get(client,'/capabilities').json();assert len(a)==47
    assert sum(e['proposal']=='Additional Cost' for e in a)==4

def test_unauthenticated_data_is_blocked(client):
    client.post('/api/logout')
    assert get(client,'/people').status_code==401
    assert get(client,'/reports').status_code==401
    assert get(client,'/vacancies').status_code==200

def test_bad_access_code(client):
    assert client.post('/api/login',json={'data':{'user_id':1,'pin':'bad'}}).status_code==401

def test_role_restrictions(client):
    as_user(client,1)
    for endpoint in ['/integrations','/audit','/reports','/applications','/cases']:
        assert get(client,endpoint).status_code==403,endpoint
    assert post(client,'/payroll/run',period='2026-10').status_code==403

def test_leave_approval_changes_employee_balance(client):
    as_user(client,1);before=get(client,'/leave').json()['balance']
    r=post(client,'/leave',start=future(21),ending=future(22),leave_type='Annual');assert r.status_code==200,r.text
    id=r.json()['id']; days=r.json()['days'];assert days>=1
    as_user(client,4)
    assert post(client,f'/leave/{id}/decision',decision='Approved').status_code==200
    as_user(client,1)
    assert get(client,'/leave').json()['balance']==before-days

def test_leave_overlap_and_double_approval(client):
    as_user(client,1)
    x=post(client,'/leave',start=future(21),ending=future(22),leave_type='Annual').json()
    assert post(client,'/leave',start=future(21),ending=future(23),leave_type='Annual').status_code==409
    as_user(client,4)
    assert post(client,f'/leave/{x["id"]}/decision',decision='Rejected').status_code==200
    assert post(client,f'/leave/{x["id"]}/decision',decision='Approved').status_code==409

def test_invalid_leave_dates_and_balance(client):
    as_user(client,1)
    assert post(client,'/leave',start=future(23),ending=future(21),leave_type='Annual').status_code==400
    assert post(client,'/leave',start=future(25),ending=future(70),leave_type='Annual').status_code==409

def test_manager_cannot_approve_unassigned_request(client):
    as_user(client,3)
    x=post(client,'/leave',start=future(20),ending=future(20),leave_type='Other').json()
    # Same manager seeded for Megan; use service director who is not request owner
    as_user(client,8)
    assert post(client,f'/leave/{x["id"]}/decision',decision='Approved').status_code==403

def test_org_rollup_and_role_visibility(client):
    as_user(client,4)
    x=get(client,'/org').json();assert x['rollups']
    assert all(a['id']==4 or a['manager_id']==4 or a['id']==8 for a in x['people'])
    as_user(client,1)
    x=get(client,'/org').json();assert not x['rollups']

def test_profile_changes_are_private(client):
    as_user(client,1)
    assert post(client,'/profile',phone='0123456789',address='Demo street',emergency_contact='Lee').status_code==200
    assert get(client,'/profile').json()['profile']['phone']=='0123456789'
    as_user(client,2)
    assert get(client,'/profile').json()['profile']['phone']==''

def test_timesheet_validation_approval_and_queue(client):
    as_user(client,1)
    monday=date.today()-timedelta(days=date.today().weekday())
    x=post(client,'/time',week_start=monday.isoformat(),hours=37.5);assert x.status_code==200,x.text
    id=x.json()['id']
    assert post(client,'/time',week_start=monday.isoformat(),hours=18).status_code==409
    as_user(client,4)
    assert post(client,f'/time/{id}/decision',decision='Approved').status_code==200
    as_user(client,9)
    assert any(x['event']=='time-approved' for x in get(client,'/integrations').json()['events'])

def test_vacancy_publish_edit_and_close(client):
    as_user(client,4)
    x=post(client,'/vacancies',title='Housing Officer',department='Housing',summary='Serve residents',closing=future(30));assert x.status_code==200,x.text
    id=x.json()['id']
    assert post(client,f'/vacancies/{id}/publish').status_code==403
    assert post(client,f'/vacancies/{id}/update',summary='Revised responsibilities').json()['revision']==2
    as_user(client,10)
    assert post(client,f'/vacancies/{id}/publish').status_code==200
    assert post(client,f'/vacancies/{id}/close').status_code==200
    assert post(client,f'/vacancies/{id}/publish').status_code==409

def test_candidate_requires_cover_and_duplicate_rejected(client):
    x=post(client,'/apply/1',name='Maya Evans',email='maya.demo@example.com',statement='Council experience');assert x.status_code==400
    x=post(client,'/apply/1',name='Maya Evans',email='maya.demo@example.com',statement='Council experience',cover_letter='Relevant experience');assert x.status_code==200,x.text
    token=x.json()['access_token']
    assert get(client,f'/candidate/{token}').json()['stage']=='Applied'
    assert post(client,'/apply/1',name='Maya Evans',email='maya.demo@example.com',statement='Duplicate',cover_letter='Again').status_code==409

def test_candidate_stage_and_reschedule(client):
    a=post(client,'/apply/1',name='Maya Evans',email='maya.demo@example.com',statement='Strong skills',cover_letter='Cover').json()
    id=a['id'];token=a['access_token']
    assert post(client,f'/candidate/{token}/interview',slot=future(10)+'T11:00').status_code==409
    as_user(client,10)
    assert post(client,f'/applications/{id}/stage',stage='Shortlisted').status_code==200
    assert post(client,f'/applications/{id}/stage',stage='Offered').status_code==409
    assert post(client,f'/candidate/{token}/interview',slot=future(10)+'T11:00',type='Video').status_code==200
    assert post(client,f'/candidate/{token}/interview',slot=future(11)+'T14:00',type='In-person').status_code==200
    assert get(client,f'/candidate/{token}').json()['interview_type']=='In-person'

def test_interview_feedback_required(client):
    a=post(client,'/apply/1',name='Maya Evans',email='maya.demo@example.com',statement='Strong skills',cover_letter='Cover').json()
    as_user(client,10);post(client,f'/applications/{a["id"]}/stage',stage='Shortlisted')
    post(client,f'/candidate/{a["access_token"]}/interview',slot=future(10)+'T11:00')
    assert post(client,f'/applications/{a["id"]}/stage',stage='Interview Completed').status_code==400
    assert post(client,f'/applications/{a["id"]}/stage',stage='Interview Completed',score=4,feedback='Clear examples and relevant service experience').status_code==200

def test_complete_recruit_to_worker_creates_tasks_and_events(client):
    a=post(client,'/apply/1',name='Maya Evans',email='maya.demo@example.com',statement='Strong skills',cover_letter='Cover').json()
    id=a['id'];token=a['access_token'];as_user(client,10)
    post(client,f'/applications/{id}/stage',stage='Shortlisted')
    post(client,f'/candidate/{token}/interview',slot=future(10)+'T11:00')
    post(client,f'/applications/{id}/stage',stage='Interview Completed',score=5,feedback='Excellent public service evidence')
    for stage in ['Offered','Offer Accepted','Checks Complete','Onboarded']:
        r=post(client,f'/applications/{id}/stage',stage=stage);assert r.status_code==200,(stage,r.text)
    as_user(client,9)
    assert get(client,'/dashboard').json()['headcount']==17
    assert any(t['kind']=='Onboarding' for t in get(client,'/tasks').json())
    assert any(e['event']=='new-starter' for e in get(client,'/integrations').json()['events'])
    assert post(client,f'/applications/{id}/stage',stage='Onboarded').status_code==409

def test_candidate_withdrawal_blocks_next_stage(client):
    a=post(client,'/apply/1',name='Maya Evans',email='maya.demo@example.com',statement='Relevant',cover_letter='Cover').json()
    assert post(client,f'/candidate/{a["access_token"]}/withdraw').status_code==200
    as_user(client,10)
    assert post(client,f'/applications/{a["id"]}/stage',stage='Shortlisted').status_code==409

def test_document_upload_read_permissions_archive_and_purge(client):
    as_user(client,1)
    files={'file':('signed-declaration.txt',b'Employee signed declaration','text/plain')}
    r=client.post('/api/documents?retention_until=2033-12-31&doc_type=Declaration',files=files);assert r.status_code==200,r.text
    id=r.json()['id']
    assert get(client,f'/documents/{id}/download').status_code==200
    as_user(client,2)
    assert get(client,f'/documents/{id}/download').status_code==403
    assert post(client,f'/documents/{id}/archive').status_code==403
    as_user(client,5)
    assert post(client,f'/documents/{id}/archive').status_code==200
    assert post(client,'/documents/purge').json()['purged']==0

def test_upload_invalid_extension_and_size(client):
    as_user(client,1)
    assert client.post('/api/documents',files={'file':('bad.exe',b'BAD','application/octet-stream')}).status_code==400
    assert client.post('/api/documents',files={'file':('big.txt',b'x'*(5*1024*1024+1),'text/plain')}).status_code==400

def test_task_reassign_and_complete(client):
    as_user(client,5)
    x=post(client,'/tasks',title='Starter record check',assigned_to=5,employee_id=1);assert x.status_code==200,x.text
    id=x.json()['id']
    assert post(client,f'/tasks/{id}/reassign',assigned_to=4).status_code==200
    as_user(client,4)
    assert post(client,f'/tasks/{id}/complete').status_code==200
    assert post(client,f'/tasks/{id}/complete').status_code==409

def test_learning_booking_and_completion(client):
    as_user(client,1)
    assert post(client,'/learning/1/enrol').status_code==200
    assert post(client,'/learning/1/enrol').status_code==409
    eid=get(client,'/learning').json()['enrolments'][0]['id']
    assert post(client,f'/learning/{eid}/complete').status_code==200
    assert post(client,f'/learning/{eid}/complete').status_code==409

def test_payroll_finalise_and_private_payslip(client):
    as_user(client,6)
    x=post(client,'/payroll/run',period='2026-10');assert x.status_code==200,x.text
    id=x.json()['id']
    assert post(client,'/payroll/run',period='2026-10').status_code==409
    assert post(client,f'/payroll/{id}/finalise').status_code==200
    assert post(client,f'/payroll/{id}/finalise').status_code==409
    as_user(client,1)
    mine=get(client,'/payroll').json()
    assert len(mine['payslips'])==1 and mine['runs']==[]

@pytest.mark.parametrize('group,metric',[('department','headcount'),('cost_center','fte'),('grade','headcount')])
def test_reports_and_export(client,group,metric):
    as_user(client,5)
    r=get(client,f'/reports?group={group}&metric={metric}');assert r.status_code==200
    assert r.json()['total']>0
    csv=get(client,f'/reports/export?group={group}&metric={metric}');assert csv.status_code==200
    assert 'text/csv' in csv.headers['content-type']

def test_restricted_pay_analytics(client):
    as_user(client,4)
    assert get(client,'/reports?metric=salary').status_code==403
    as_user(client,5)
    assert get(client,'/reports?metric=salary').status_code==200
    assert get(client,'/reports?group=id').status_code==400

def test_expenses_and_hr_case(client):
    as_user(client,1)
    id=post(client,'/expenses',category='Training',detail='Safeguarding event',amount=45).json()['id']
    assert post(client,'/cases',title='test').status_code==403
    as_user(client,4)
    assert post(client,f'/expenses/{id}/decision',decision='Approved').status_code==200
    as_user(client,5)
    case=post(client,'/cases',title='Return-to-work support',employee_id=1,details='Schedule a meeting').json()['id']
    assert post(client,f'/cases/{case}/close').status_code==200

def test_bcc_privacy_and_character_limits(client):
    as_user(client,5)
    x=post(client,'/messages',subject='Return to work',body='Private note',recipients=[1,2],force_notify=True)
    assert x.status_code==200,x.text
    assert x.json()['email_status'].startswith('Demo queue')
    assert post(client,'/messages',subject='x'*256,body='hi',recipients=[1]).status_code==400
    assert post(client,'/messages',subject='hello',body='x'*4001,recipients=[1]).status_code==400
    as_user(client,1)
    m=get(client,'/messages').json();assert len(m)==1 and 'recipient' not in str(m[0])
    assert post(client,f'/messages/{m[0]["id"]}/read').status_code==200
    as_user(client,3);assert get(client,'/messages').json()==[]

def test_mock_failure_recovery_and_idempotence(client):
    as_user(client,6)
    pid=post(client,'/payroll/run',period='2026-10').json()['id']
    post(client,f'/payroll/{pid}/finalise')
    as_user(client,9)
    events=get(client,'/integrations').json()['events'];id=next(e['id'] for e in events if e['event']=='payment-export')
    assert post(client,f'/integrations/{id}/process',fail=True).json()['status']=='Failed'
    assert post(client,f'/integrations/{id}/process',fail=False).json()['attempts']==2
    assert post(client,f'/integrations/{id}/process',fail=False).status_code==409

def test_demo_reset_confirmation(client):
    as_user(client,9)
    assert post(client,'/demo/reset',confirm='not really').status_code==400
    assert post(client,'/demo/reset',confirm='RESET DEMO').status_code==200
    assert get(client,'/dashboard').json()['headcount']==16

def test_candidate_correspondence_and_private_inbox(client):
    a=post(client,'/apply/1',name='Leena Shah',email='leena.demo@example.com',statement='Public service experience',cover_letter='Relevant experience').json()
    token=a['access_token']
    initial=get(client,f'/candidate/{token}/messages');assert initial.status_code==200
    assert initial.json()[0]['title']=='Application received'
    assert get(client,'/candidate/not-a-valid-token/messages').status_code==404
    as_user(client,10)
    msg=post(client,f'/applications/{a["id"]}/message',subject='Interview next steps',body='Please select a convenient interview slot from your candidate portal.')
    assert msg.status_code==200,msg.text
    assert 'no real' in msg.json()['delivery'].lower() or msg.json()['delivery'].startswith('Candidate portal')
    assert post(client,f'/applications/{a["id"]}/message',subject='x'*256,body='hi').status_code==400
    as_user(client,1)
    assert post(client,f'/applications/{a["id"]}/message',subject='Private',body='Not authorised').status_code==403
    assert any(e['title']=='Interview next steps' for e in get(client,f'/candidate/{token}/messages').json())


def test_archival_expiry_purge_and_access_denied(client):
    as_user(client,1)
    r=client.post('/api/documents?retention_until=2035-12-31&doc_type=Signed%20declaration',
                  files={'file':('signed-declaration.txt',b'Synthetic declaration', 'text/plain')})
    assert r.status_code==200,r.text
    id=r.json()['id']
    as_user(client,5)
    assert post(client,f'/documents/{id}/archive').status_code==200
    assert post(client,'/documents/purge').json()['purged']==0
    assert post(client,f'/documents/{id}/simulate-expiry').status_code==403
    as_user(client,9)
    assert post(client,f'/documents/{id}/simulate-expiry').status_code==200
    as_user(client,5)
    assert post(client,'/documents/purge').json()['purged']>=1
    as_user(client,1)
    assert get(client,f'/documents/{id}/download').status_code in (403,404,410)
