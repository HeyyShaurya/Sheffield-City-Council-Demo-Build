import os,tempfile,json,sys
from pathlib import Path
from datetime import date,timedelta
os.environ['SHEFFIELD_DATA_DIR']=tempfile.mkdtemp(prefix='sheffield-browser-e2e-')
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from fastapi.testclient import TestClient
from app.main import app
from playwright.sync_api import sync_playwright
# project root derived from test file
html=(root/'app/static/index.html').read_text().replace('<script src="/static/app.js" defer></script>','').replace('<link rel="stylesheet" href="/static/styles.css">','')
client=TestClient(app)
def bridge(url,method,body,headers):
 if body and isinstance(body,str) and body.startswith('{"__multipart_demo__":'):
  d=json.loads(body)['__multipart_demo__'];items={v['key']:(v['filename'],bytes(v['bytes']),v['type']) for v in d if 'filename' in v}
  r=client.request(method,url,files=items)
 else:
  r=client.request(method,url,content=body if body else None,headers=headers or {})
 return {'status':r.status_code,'body':r.text}
def go(pg,key):
 pg.locator(f'nav [data-page="{key}"]').first.click()
 pg.wait_for_timeout(170)
def switch(pg,id):
 pg.locator('#switchPerson').click();pg.wait_for_timeout(140)
 pg.locator('#personaSelect').select_option(str(id))
 pg.locator('#loginForm button').click();pg.wait_for_timeout(220)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 pg=b.new_page(viewport={'width':1365,'height':900});errors=[]
 pg.on('pageerror',lambda e:errors.append(str(e)))
 pg.on('dialog',lambda d:d.accept())
 pg.expose_function('__bridge',bridge)
 pg.set_content(html)
 pg.add_style_tag(content=(root/'app/static/styles.css').read_text())
 pg.evaluate('''() => {const store={};Object.defineProperty(window,'localStorage',{value:{getItem:k=>store[k]||null,setItem:(k,v)=>store[k]=String(v),removeItem:k=>delete store[k]}});window.fetch=async(path,o={})=>{let b=o.body||null;if(b instanceof FormData){const parts=[];for(const [key,value] of b.entries()){if(value instanceof File){parts.push({key,filename:value.name,type:value.type,bytes:Array.from(new Uint8Array(await value.arrayBuffer()))})}else{parts.push({key,value:String(value)})}}b=JSON.stringify({__multipart_demo__:parts})}const r=await window.__bridge(path,o.method||'GET',b,o.headers||{});return new Response(r.body,{status:r.status,headers:{'content-type':'application/json'}})}}''')
 pg.add_script_tag(content=(root/'app/static/app.js').read_text())
 pg.wait_for_timeout(230)
 pg.locator('#loginForm button').click();pg.wait_for_timeout(230)
 go(pg,'leave')
 pg.locator('[data-act="new-leave"]').click()
 pg.locator('input[name="start"]').fill((date.today()+timedelta(days=21)).isoformat())
 pg.locator('input[name="ending"]').fill((date.today()+timedelta(days=22)).isoformat())
 pg.locator('form[data-form="leave"] button[type=submit]').click();pg.wait_for_timeout(250)
 print('leave submitted',pg.locator('#content').inner_text().count('Pending'))
 switch(pg,4)
 go(pg,'leave')
 print('approve buttons',pg.locator('[data-act="leave-decision"][data-choice="Approved"]').count())
 pg.locator('[data-act="leave-decision"][data-choice="Approved"]').first.click();pg.wait_for_timeout(200)
 print('approved displayed',pg.locator('#content').inner_text().count('Approved'))
 switch(pg,10)
 go(pg,'recruit')
 pg.locator('[data-act="public-careers"]').click();pg.wait_for_timeout(160)
 pg.locator('[data-act="apply"]').first.click()
 pg.locator('form[data-form="apply"] [name="name"]').fill('Maya Evans')
 pg.locator('form[data-form="apply"] [name="email"]').fill('maya.browser@example.com')
 pg.locator('form[data-form="apply"] [name="statement"]').fill('Experienced in public services')
 pg.locator('form[data-form="apply"] [name="cover_letter"]').fill('A good fit for this role')
 pg.locator('form[data-form="apply"] button[type=submit]').click();pg.wait_for_timeout(230)
 print('applied',pg.locator('#content').inner_text().count('YOUR APPLICATION TRACKER'))
 pg.locator('[data-act="public-exit"]').click();pg.wait_for_timeout(200)
 print('shortlist buttons',pg.locator('[data-stage="Shortlisted"]').count())
 pg.locator('[data-stage="Shortlisted"]').click();pg.wait_for_timeout(230)
 pg.locator('[data-act="app-message"]').first.click()
 pg.locator('form[data-form="app-message"] [name="subject"]').fill('Interview instructions')
 pg.locator('form[data-form="app-message"] [name="body"]').fill('Choose a suitable interview time from your candidate portal.')
 pg.locator('form[data-form="app-message"] button[type=submit]').click();pg.wait_for_timeout(200)
 pg.locator('[data-act="public-careers"]').click();pg.wait_for_timeout(220)
 assert 'Interview instructions' in pg.locator('#content').inner_text(), 'Candidate did not receive recruiter correspondence in portal'
 print('candidate correspondence visible in portal')
 pg.locator('[data-act="schedule"]').click()
 pg.locator('form[data-form="interview"] [name="slot"]').fill((date.today()+timedelta(days=10)).isoformat()+'T11:00')
 pg.locator('form[data-form="interview"] button[type=submit]').click();pg.wait_for_timeout(250)
 pg.locator('[data-act="public-exit"]').click();pg.wait_for_timeout(250)
 pg.locator('[data-stage="Interview Completed"]').click();pg.wait_for_timeout(100)
 pg.locator('form[data-form="app-stage"] [name="score"]').fill('5')
 pg.locator('form[data-form="app-stage"] [name="feedback"]').fill('Clear examples, strong customer experience and reflective practice')
 pg.locator('form[data-form="app-stage"] button[type=submit]').click();pg.wait_for_timeout(180)
 for stage in ['Offered','Offer Accepted','Checks Complete','Onboarded']:
  pg.locator(f'[data-stage="{stage}"]').click();pg.wait_for_timeout(200)
 print('onboarded',pg.locator('#content').inner_text().count('Onboarded'))
 assert client.get('/api/health').status_code==200
 pg.screenshot(path=str(root/'docs/qa-recruit-flow.png'),full_page=True)
 # Document lifecycle: real browser form upload, archive, administrator-only expiry, purge.
 switch(pg,1)
 go(pg,'documents')
 pg.locator('[data-act="new-document"]').click()
 pg.locator('form[data-form="document"] input[type=file]').set_input_files(str(root/'docs/signed-declaration-example.txt'))
 pg.locator('form[data-form="document"] button[type=submit]').click();pg.wait_for_timeout(230)
 assert 'signed-declaration-example.txt' in pg.locator('#content').inner_text()
 switch(pg,5)
 go(pg,'documents')
 assert pg.locator('[data-act="archive"]').count()>=1
 pg.locator('[data-act="archive"]').first.click();pg.wait_for_timeout(210)
 switch(pg,9)
 go(pg,'documents')
 assert pg.locator('[data-act="doc-expire"]').count()>=1
 pg.locator('[data-act="doc-expire"]').first.click();pg.wait_for_timeout(220)
 switch(pg,5)
 go(pg,'documents')
 pg.locator('[data-act="purge"]').first.click();pg.wait_for_timeout(210)
 assert 'signed-declaration-example.txt' not in pg.locator('#content').inner_text(), 'Eligible purged document remains visible'
 print('document upload/archive/expiry/purge passed')
 print('page errors:',errors)
 b.close()

assert not errors, 'Browser JavaScript errors: '+repr(errors)
