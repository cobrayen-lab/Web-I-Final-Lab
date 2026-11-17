#!/usr/bin/env python3
"""Web I final CTF: local-only educational site (Python standard library)."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit, quote
from http.cookies import SimpleCookie
from pathlib import Path
import html
import json
import re
import secrets
import threading
import webbrowser
import sys

HOST = '127.0.0.1'
PORT = 8765
ROOT = Path(__file__).resolve().parent
STATIC = ROOT / 'static'
FLAGS = {
    'lab1': 'NISRA{3Gcrd2WahGRVdrt4}',
    'lab2': 'NISRA{9UwmSmrHuGXG1WJZ}',
    'lab3': 'NISRA{FpqySq2TthUbJ9ak}',
    'lab4': 'NISRA{Mukf2SakraGtgmwu}',
    'lab5': 'NISRA{UD2ZwrOsR42ywYCQ}',
}
# Local educational verifier only. No resistance to local source inspection/tampering.
TOKENS = {}  # ephemeral per-load challenge tokens for labs 1,3,4
LOCK = threading.Lock()
TASKS = [
    ('lab1','Just Search It','Cobra Tech 最近推出了一款全新的搜尋引擎。開發團隊對這項新功能充滿信心，認為它能完美呈現使用者想搜尋的內容。不過，這個看似普通的搜尋系統，似乎還藏著一些意想不到的問題……你能發現其中的秘密嗎？',50),
    ('lab2','Cookie Monster','Cookie Monster 最近從 Cobra Tech 偷走了一份重要的機密資料。他不但沒有逃跑，反而留下了一個奇怪的網站，還自信地宣稱：「秘密就在你身邊，只是你沒有發現而已。」你能找回這份機密資料嗎？',50),
    ('lab3','The Perfect Defense','經歷上一次的安全事件後，Cobra Tech 決定重新檢查搜尋系統。工程師花了不少時間修補問題，終於完成了他引以為傲的防護措施。「這一次，應該真的萬無一失了吧？」你能證明他的想法是錯的嗎？',100),
    ('lab4','One Last Fix','接連發生的安全事件，讓 Cobra Tech 的工程師決定徹底重新設計搜尋系統。這次，他不只修改了防護措施，還改變了網站處理資料的方式。工程師相信，新的設計終於能解決所有問題。但事情真的如他所想嗎？',100),
    ('lab5','The Forbidden Room','在 Cobra Tech 的總部深處，有一間禁止一般員工進入的秘密房間。據說，房間裡存放著公司最重要的機密。為了防止外人闖入，工程師設計了一套嚴格的驗證機制，並自信地宣稱：「沒有獲得許可的人，絕對不可能進入這裡。」你能挑戰這道看似牢不可破的防線嗎？',150),
]

def shell(title, body, scripts='', body_attrs='', additional_head=''):
    # IMPORTANT: The body_attrs parameter is intentionally unsafe in lab4 only.
    return f'''<!DOCTYPE html>
<html lang="zh-Hant-TW"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | NISRA Web I CTF</title>
<link rel="stylesheet" href="/static/style.css">
{additional_head}
</head><body {body_attrs}><header class="topbar"><a href="/" class="brand">NISRA <span>/ WEB I</span></a><span class="mini">LOCAL CTF · 5 CHALLENGES</span></header>
<main class="wrap">{'<nav class="challenge-nav"><a class="back-home" href="/">← 回到目錄</a></nav>' if title != 'Challenge Board' else ''}{body}</main>
<footer>Web I Final CTF · Offline training</footer>
{scripts}</body></html>'''

def title_block(lab):
    _, title, description, score = next(item for item in TASKS if item[0] == lab)
    return (f'<div class="eyebrow">CHALLENGE {lab[-1]} <span class="points">{score} PTS</span></div>'
            f'<h1>{html.escape(title)}</h1><p class="story">{html.escape(description)}</p>')

def verifier_script(lab, token):
    # Local educational checker: start verification before blocking alert dialogs.
    template = r'''<script>
(() => {
  const realAlert = window.alert.bind(window);
  const proof = __TOKEN__;
  let verificationStarted = false;
  function displayResult(message, isError = false) {
    const show = () => {
      const output = document.getElementById('completion');
      if (!output) return;
      output.hidden = false;
      output.textContent = message;
      output.classList.toggle('flag-error', isError);
      if (!isError) output.scrollIntoView({behavior:'smooth', block:'nearest'});
    };
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', show, {once:true});
    } else show();
  }
  window.alert = function(message) {
    // Accept both alert() and alert(1), which have been used in class.
    if (!verificationStarted && (arguments.length === 0 || String(message) === '1')) {
      verificationStarted = true;
      fetch('/__LAB__/verify', {method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({token:proof, result:'1'})})
        .then(r => { if (!r.ok) throw new Error('verification failed'); return r.json(); })
        .then(data => {
          if (data.flag) displayResult('Challenge Complete!\n' + data.flag);
          else displayResult('驗證未完成，請重新整理後再嘗試。', true);
        })
        .catch(() => displayResult('驗證連線失敗，請重新整理後再嘗試。', true));
    }
    return realAlert(...arguments);
  };
})();
</script>'''
    return template.replace('__LAB__', lab).replace('__TOKEN__', json.dumps(token))

def new_token(lab):
    token=secrets.token_urlsafe(18)
    with LOCK:
        if len(TOKENS)>5000: TOKENS.clear()
        TOKENS[token] = lab
    return token

class Handler(BaseHTTPRequestHandler):
    server_version = 'NISRA-Local/1.0'
    def log_message(self, format, *args):
        sys.stdout.write('[web] %s - %s\n' % (self.address_string(), format % args))
    def respond(self, body, status=200, ctype='text/html; charset=utf-8', headers=None):
        if isinstance(body, str): body=body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        parsed=urlsplit(self.path); path=parsed.path; qs=parse_qs(parsed.query,keep_blank_values=True)
        if path == '/':
            cards=''.join(f'<a class="challenge" href="/{lab}"><div class="card-meta">LAB {lab[-1]} · {points} PTS</div><h2>{html.escape(name)}</h2><span class="card-action">進入挑戰 ›</span></a>' for lab,name,_,points in TASKS)
            self.respond(shell('Challenge Board', '<div class="eyebrow">NISRA · 2026</div><h1>Web I — Final CTF</h1><p class="story">五個獨立的挑戰，找出每個網站隱藏的 Flag。</p><div class="challenge-grid">'+cards+'</div>'))
        elif path == '/static/style.css':
            self.respond((STATIC/'style.css').read_bytes(),ctype='text/css; charset=utf-8')
        elif path == '/static/lab5.js':
            self.respond((STATIC/'lab5.js').read_bytes(),ctype='application/javascript; charset=utf-8')
        elif path in ('/lab1','/lab3'):
            lab=path[1:]; query=qs.get('q',[''])[0]
            if lab=='lab3':
                # Deliberately incomplete, pedagogical script-tag blacklist.
                query=re.sub(r'(?is)<\s*script\b[^>]*>.*?<\s*/\s*script\s*>','',query)
                query=re.sub(r'(?is)<\s*/?\s*script\b[^>]*>','',query)
            token=new_token(lab)
            form=f'''<form class="searchbar" method="get" action="/{lab}"><input name="q" placeholder="Search something..." value="{html.escape(qs.get('q',[''])[0], quote=True)}" autocomplete="off"><button>Search</button></form>'''
            result=('<div class="result"><div class="eyebrow">SEARCH RESULTS</div><div class="result-text">Search results for: '+query+'</div></div>') if 'q' in qs else '<div class="empty">Enter a keyword to begin searching.</div>'
            # Header verifier runs before the intentionally untrusted HTML.
            checker=verifier_script(lab,token)
            page=shell(TASKS[int(lab[-1])-1][1],title_block(lab)+form+result+'<div id="completion" class="flag" hidden></div>',additional_head=checker)
            self.respond(page)
        elif path == '/lab2':
            page=shell('Cookie Monster',title_block('lab2')+'<div class="cookie-visual">🍪</div><section class="panel center"><h2>The secret is already yours.</h2><p>Every visitor receives something.</p></section>')
            self.respond(page,headers={'Set-Cookie':f'lab2_treasure={FLAGS["lab2"]}; Path=/; SameSite=Lax'})
        elif path == '/lab4':
            q=qs.get('q',[''])[0]
            # Escape angle brackets and ampersands, but intentionally NOT the quote character.
            escaped=q.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            token=new_token('lab4')
            checker=verifier_script('lab4',token)
            form='<form class="searchbar" method="get" action="/lab4"><input name="q" placeholder="Search something..." value="'+html.escape(q,quote=True)+'" autocomplete="off"><button>Search</button></form>'
            body=title_block('lab4')+form+'<section class="panel"><h2>Search Results</h2><p>Searching...</p></section><div id="completion" class="flag" hidden></div>'
            self.respond(shell('One Last Fix',body,body_attrs=f'data-search="{escaped}"',additional_head=checker))
        elif path == '/lab5':
            content=title_block('lab5')+'''
            <section class="panel room">
              <div class="room-icon">▣</div><h2>Administrator Verification</h2>
              <p>Restricted area. Authorized personnel only.</p>
              <label for="admin-password">Password</label>
              <input type="password" id="admin-password" placeholder="Enter password" autocomplete="off">
              <button type="button" id="unlock-btn">Unlock Room</button>
              <p id="room-message" class="error-msg" aria-live="polite"></p>
            </section>
            <form id="secretForm" action="/lab5/secret-room" method="POST" hidden>
              <input type="hidden" name="action" value="unlock">
            </form>'''
            self.respond(shell('The Forbidden Room',content,scripts='<script src="/static/lab5.js"></script>'))
        elif path == '/lab5/secret-room':
            self.respond(shell('Restricted','<div class="panel"><h2>Method Not Allowed</h2><p>This room does not accept that request.</p><a href="/lab5">Return</a></div>'),status=405,headers={'Allow':'POST'})
        else:
            self.respond(shell('Not Found','<h1>404</h1><p>Nothing here.</p><a href="/">Back</a>'),status=404)
    def do_POST(self):
        path=urlsplit(self.path).path
        if path in ('/lab1/verify','/lab3/verify','/lab4/verify'):
            size=int(self.headers.get('Content-Length','0') or '0')
            if size>4096:
                self.respond('{"error":"too large"}',status=413,ctype='application/json'); return
            try: payload=json.loads(self.rfile.read(size))
            except (json.JSONDecodeError,UnicodeDecodeError):
                self.respond('{"error":"invalid"}',status=400,ctype='application/json'); return
            lab=path.split('/')[1]
            token=payload.get('token') if isinstance(payload,dict) else None
            with LOCK:
                valid=bool(token and TOKENS.get(token)==lab)
                if valid: del TOKENS[token]
            if valid and payload.get('result')=='1':
                self.respond(json.dumps({'flag':FLAGS[lab]}),ctype='application/json')
            else: self.respond('{"error":"not completed"}',status=403,ctype='application/json')
        elif path == '/lab5/secret-room':
            size=int(self.headers.get('Content-Length','0') or '0')
            if size>2048:
                self.respond('Too large',status=413); return
            data=parse_qs(self.rfile.read(size).decode('utf-8',errors='replace'))
            if data.get('action',[''])[0] == 'unlock':
                page=shell('Room Unlocked','<div class="eyebrow">ACCESS GRANTED</div><h1>The Forbidden Room</h1><section class="panel center"><h2>Welcome to the room.</h2><p>You found the secret.</p><div class="flag">'+FLAGS['lab5']+'</div></section>')
                self.respond(page)
            else:
                self.respond(shell('Invalid Request','<h1>Invalid Request</h1>'),status=400)
        else:
            self.respond('Not Found',status=404,ctype='text/plain; charset=utf-8')

def main():
    try: server=ThreadingHTTPServer((HOST,PORT), Handler)
    except OSError as ex:
        print(f'Cannot start at {HOST}:{PORT}: {ex}')
        print('Close any program already using port 8765.'); sys.exit(1)
    url=f'http://{HOST}:{PORT}/'
    print('NISRA Web I Final CTF (local only)')
    print('Open:',url)
    print('Press Ctrl+C to stop.')
    threading.Timer(0.7,lambda:webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: print('\nStopped.')
    finally: server.server_close()
if __name__=='__main__': main()
