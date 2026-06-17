const WebSocket = require('ws');
const fs = require('fs');

// 用工作台页面（已验证fetch能用）
const PAGE_ID = 'B3F8DF7A128D390FFDD0095560E37D7F';
const ws = new WebSocket(`ws://127.0.0.1:9223/devtools/page/${PAGE_ID}`);

let msgId = 0;
const pending = new Map();
let interceptedBodies = [];

function send(method, params) {
  return new Promise((resolve, reject) => {
    const id = ++msgId;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error('timeout')); }, 15000);
    pending.set(id, (r) => { clearTimeout(timer); resolve(r); });
    ws.send(JSON.stringify({id, method, params}));
  });
}

ws.on('message', (data) => {
  try {
    const r = JSON.parse(data);
    if (r.id && pending.has(r.id)) { pending.get(r.id)(r); pending.delete(r.id); }
    
    // 拦截请求
    if (r.method === 'Fetch.requestPaused') {
      const url = r.params?.request?.url || '';
      const method = r.params?.request?.method || '';
      const reqId = r.params?.requestId;
      const body = r.params?.request?.postData;
      
      if (url.includes('/rapi/d/customer') && (method === 'PATCH' || method === 'POST')) {
        console.log('=== INTERCEPTED ' + method + ' ===');
        console.log('URL:', url);
        console.log('Body length:', body?.length);
        interceptedBodies.push({method, url, body});
        
        // 保存到文件
        const filename = method === 'PATCH' ? 'patch_template.json' : 'post_template.json';
        fs.writeFileSync('C:/Users/Admin/Desktop/' + filename, body || '{}');
        console.log('Saved to Desktop/' + filename);
      }
      
      // 继续请求
      send('Fetch.continueRequest', {requestId: reqId}).catch(() => {});
    }
  } catch(e) {}
});

ws.on('error', (e) => { console.error('WS Error:', e.message); process.exit(1); });

async function run() {
  // 启用Fetch拦截
  console.log('Enabling Fetch interceptor...');
  await send('Fetch.enable', {
    patterns: [
      {urlPattern: '*://trade.joinf.com/rapi/d/customer*', requestStage: 'Request'}
    ]
  });
  
  // 导航到编辑页
  console.log('Navigating to edit page...');
  await send('Page.navigate', {url: 'https://trade.joinf.com/tms/customer/customers?type=edit&id=238855638&tab=0'});
  await new Promise(r => setTimeout(r, 5000));
  
  // 检查页面
  const t1 = await send('Runtime.evaluate', {
    expression: 'JSON.stringify({url:location.href, inputs: document.querySelectorAll("input:not([type=checkbox]):not([type=hidden]), textarea").length})',
    returnByValue: true
  });
  console.log('Page:', t1.result?.result?.value);
  
  // 修改一个字段
  const t2 = await send('Runtime.evaluate', {
    expression: `(async function(){
      var inputs = Array.from(document.querySelectorAll('input:not([type=checkbox]):not([type=hidden]), textarea'));
      var visible = inputs.filter(function(i){return i.offsetParent !== null;});
      if(visible.length === 0) return 'no visible inputs';
      
      // 找描述字段
      var descInput = null;
      for(var i=0; i<visible.length; i++){
        var prev = visible[i].previousElementSibling;
        var parent = visible[i].closest('.el-form-item') || visible[i].parentElement;
        var label = parent ? (parent.querySelector('label') || parent.querySelector('.el-form-item__label')) : null;
        if(label && (label.textContent.indexOf('描述') >= 0 || label.textContent.indexOf('简介') >= 0)){
          descInput = visible[i];
          break;
        }
      }
      if(!descInput) descInput = visible[visible.length - 1];
      
      var tag = descInput.tagName;
      var proto = tag === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
      var setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
      setter.call(descInput, 'HERMES_TEMPLATE_CAPTURE');
      descInput.dispatchEvent(new Event('input', {bubbles: true}));
      descInput.dispatchEvent(new Event('change', {bubbles: true}));
      
      await new Promise(function(r){setTimeout(r, 1000);});
      
      // 点保存
      var btns = Array.from(document.querySelectorAll('button'));
      var saveBtn = btns.find(function(b){return b.textContent.trim() === '保存';});
      if(saveBtn){ saveBtn.click(); return 'save clicked'; }
      return 'no save button';
    })()`,
    awaitPromise: true, returnByValue: true, timeout: 10000
  });
  console.log('Modify & save:', t2.result?.result?.value);
  
  // 等一下看有没有拦截到
  await new Promise(r => setTimeout(r, 5000));
  
  console.log('\nIntercepted bodies:', interceptedBodies.length);
  for(const b of interceptedBodies) {
    console.log(b.method, b.url, 'length:', b.body?.length);
  }
  
  if(interceptedBodies.length === 0) {
    console.log('\nNo interception. Trying XHR override approach...');
    
    // 用XHR override来捕获
    const t3 = await send('Runtime.evaluate', {
      expression: `(function(){
        window.__patchBody = null;
        var origXHROpen = XMLHttpRequest.prototype.open;
        var origXHRSend = XMLHttpRequest.prototype.send;
        XMLHttpRequest.prototype.open = function(m,u){ this.__url=u; this.__method=m; return origXHROpen.apply(this,arguments); };
        XMLHttpRequest.prototype.send = function(b){
          if(this.__url && this.__url.indexOf('/rapi/d/customer') >= 0 && (this.__method === 'PATCH' || this.__method === 'POST')){
            window.__patchBody = b;
            window.__patchMethod = this.__method;
          }
          return origXHRSend.apply(this,arguments);
        };
        // Also override fetch
        var origFetch = window.fetch;
        window.fetch = function(url, opts){
          if(url && url.indexOf && url.indexOf('/rapi/d/customer') >= 0 && opts && opts.body){
            window.__patchBody = typeof opts.body === 'string' ? opts.body : JSON.stringify(opts.body);
            window.__patchMethod = opts.method || 'POST';
          }
          return origFetch.apply(this, arguments);
        };
        return 'interceptors installed';
      })()`,
      returnByValue: true
    });
    console.log('XHR interceptor:', t3.result?.result?.value);
    
    // 再次尝试保存
    const t4 = await send('Runtime.evaluate', {
      expression: `(async function(){
        var inputs = Array.from(document.querySelectorAll('input:not([type=checkbox]):not([type=hidden]), textarea'));
        var visible = inputs.filter(function(i){return i.offsetParent !== null;});
        if(visible.length === 0) return 'no inputs';
        
        var last = visible[visible.length - 1];
        var tag = last.tagName;
        var proto = tag === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
        var setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setter.call(last, 'HERMES_XHR_CAPTURE');
        last.dispatchEvent(new Event('input', {bubbles: true}));
        
        await new Promise(function(r){setTimeout(r, 500);});
        
        var btns = Array.from(document.querySelectorAll('button'));
        var saveBtn = btns.find(function(b){return b.textContent.trim() === '保存';});
        if(saveBtn){ saveBtn.click(); return 'save clicked'; }
        return 'no save';
      })()`,
      awaitPromise: true, returnByValue: true, timeout: 10000
    });
    console.log('Second save attempt:', t4.result?.result?.value);
    
    await new Promise(r => setTimeout(r, 3000));
    
    // 读取捕获的body
    const t5 = await send('Runtime.evaluate', {
      expression: 'JSON.stringify({method: window.__patchMethod, body: window.__patchBody ? window.__patchBody.substring(0,500) : null})',
      returnByValue: true
    });
    console.log('Captured via XHR:', t5.result?.result?.value);
    
    // 如果有完整body，保存
    const t6 = await send('Runtime.evaluate', {
      expression: 'window.__patchBody',
      returnByValue: true
    });
    if (t6.result?.result?.value) {
      fs.writeFileSync('C:/Users/Admin/Desktop/captured_template.json', t6.result.result.value);
      console.log('Full template saved!');
    }
  }
  
  ws.close();
}

ws.on('open', () => {
  run().then(() => { console.log('Done!'); process.exit(0); }).catch(e => { console.error(e); process.exit(1); });
});
setTimeout(() => { console.log('Global timeout'); process.exit(1); }, 60000);
