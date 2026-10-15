import os,tempfile,json,sys
from pathlib import Path
os.environ['SHEFFIELD_DATA_DIR']=tempfile.mkdtemp(prefix='sheffield-browser-')
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from fastapi.testclient import TestClient
from app.main import app
from playwright.sync_api import sync_playwright
# project root derived from test file
html=(root/'app/static/index.html').read_text().replace('<script src="/static/app.js" defer></script>','').replace('<link rel="stylesheet" href="/static/styles.css">','')
css=(root/'app/static/styles.css').read_text();js=(root/'app/static/app.js').read_text()
client=TestClient(app)
def bridge(url,method,body,headers):
    r=client.request(method,url,content=body if body else None,headers=headers or {})
    return {'status':r.status_code,'body':r.text}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 pg=b.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
 errors=[]
 pg.on('pageerror',lambda e:errors.append(str(e)))
 pg.expose_function('__bridge',bridge)
 pg.set_content(html)
 pg.add_style_tag(content=css)
 pg.evaluate('''() => {
  const ls={};Object.defineProperty(window,'localStorage',{value:{getItem:k=>ls[k]||null,setItem:(k,v)=>ls[k]=String(v),removeItem:k=>delete ls[k]}});
  window.fetch=async (path,options={})=>{const response=await window.__bridge(path,options.method||'GET',options.body||null,options.headers||{});return new Response(response.body,{status:response.status,headers:{'content-type':'application/json'}})};
 }''')
 pg.add_script_tag(content=js)
 pg.wait_for_timeout(350)
 print('login',pg.locator('#login').is_visible(),'personas',pg.locator('#personaSelect option').count())
 pg.screenshot(path=str(root/'docs/qa-login.png'),full_page=True)
 pg.locator('#loginForm button').click()
 pg.wait_for_timeout(550)
 print('workspace',pg.locator('#workspace').is_visible(),'head',pg.locator('#content h1').first.inner_text())
 pg.screenshot(path=str(root/'docs/qa-overview.png'),full_page=True)
 for key in ['profile','time','leave','org','recruit','documents','tasks','learning','payroll','optional','messages','guide','matrix']:
  pg.locator(f'nav [data-page="{key}"]').first.click()
  pg.wait_for_timeout(140)
  print(key,'=',pg.locator('#content h1').first.inner_text(),'errorCards',pg.locator('#content .note.error').count())
 pg.locator('nav [data-page="recruit"]').first.click();pg.wait_for_timeout(160)
 pg.locator('[data-act="public-careers"]').first.click();pg.wait_for_timeout(280)
 print('career mode',pg.locator('#content h1').first.inner_text())
 pg.screenshot(path=str(root/'docs/qa-careers.png'),full_page=True)
 print('javascript errors',json.dumps(errors))
 pg.set_viewport_size({'width':390,'height':844});pg.wait_for_timeout(220)
 metrics=pg.evaluate('''() => ({viewport:innerWidth,scroll:document.documentElement.scrollWidth,head:document.querySelector('#content h1')?.innerText})''')
 print('mobile candidate viewport',metrics)
 assert metrics['scroll']<=metrics['viewport']+2, 'Mobile public careers has horizontal overflow'
 pg.screenshot(path=str(root/'docs/qa-mobile-careers.png'),full_page=True)
 b.close()

assert not errors, 'Browser JavaScript errors: '+repr(errors)
