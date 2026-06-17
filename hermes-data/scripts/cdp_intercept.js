const WebSocket = require('ws');
const ws = new WebSocket('ws://127.0.0.1:9223/devtools/page/B3F8DF7A128D390FFDD0095560E37D7F');
let msgId = 0;
const pending = new Map();
let patchBody = null;
let postBody = null;

function send(method, params) {
  return new Promise((resolve) => {
    const id = ++msgId;
    pending.set(id, resolve);
    ws.send(JSON.stringify({id, method, params}));
  });
}

ws.on('message', (data) => {
  const r = JSON.parse(data);
  if (r.id && pending.has(r.id)) {
    pending.get(r.id)(r);
    pending.delete(r.id);
  }
  // 拦截请求
  if (r.method === 'Fetch.requestPaused') {
    const url = r.params?.request?.url || '';
    const method = r.params?.request?.method || '';
    const reqId = r.params?.requestId;
    if (url.includes('/rapi/d/customer')) {
      const body = r.params?.request?.postData;
      if (method === 'PATCH') {
        patchBody = body;
        console.log('=== PATCH TEMPLATE CAPTURED ===');
        console.log('Length:', body?.length);
        console.log('Preview:', body?.substring(0, 300));
      }
      if (method === 'POST') {
        postBody = body;
        console.log('=== POST TEMPLATE CAPTURED ===');
        console.log('Length:', body?.length);
        console.log('Preview:', body?.substring(0, 300));
      }
    }
    // 继续请求
    send('Fetch.continueRequest', {requestId: reqId});
  }
});

ws.on('open', async () => {
  try {
    // 启用Fetch拦截
    await send('Fetch.enable', {patterns: [{urlPattern: '*://trade.joinf.com/rapi/d/customer*', requestStage: 'Request'}]});
    console.log('Fetch interceptor enabled');

    // 等一下
    await new Promise(r => setTimeout(r, 2000));

    // 检查当前页面状态
    const r0 = await send('Runtime.evaluate', {
      expression: 'JSON.stringify({url: location.href, inputs: document.querySelectorAll("input:not([type=checkbox]):not([type=hidden]), textarea").length})',
      returnByValue: true
    });
    console.log('Page:', r0.result?.result?.value);

    // 修改一个字段然后保存
    const r1 = await send('Runtime.evaluate', {
      expression: `(async()=>{
        // 找所有可见input/textarea
        var inputs = Array.from(document.querySelectorAll('input:not([type=checkbox]):not([type=hidden]), textarea'));
        var visible = inputs.filter(function(i){return i.offsetParent !== null;});
        if(visible.length === 0) return 'no visible inputs';
        
        // 修改最后一个input（通常是描述字段）
        var last = visible[visible.length - 1];
        var tag = last.tagName;
        var proto = tag === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
        var setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setter.call(last, 'HERMES_INTERCEPT_TEST');
        last.dispatchEvent(new Event('input', {bubbles: true}));
        last.dispatchEvent(new Event('change', {bubbles: true}));
        
        await new Promise(function(r){setTimeout(r, 500);});
        
        // 找保存按钮
        var btns = Array.from(document.querySelectorAll('button'));
        var saveBtn = btns.find(function(b){return b.textContent.trim() === '保存';});
        if(saveBtn){
          saveBtn.click();
          return 'save clicked, modified: ' + (last.placeholder || last.id || 'field_' + visible.length);
        }
        return 'no save button, buttons: ' + btns.map(function(b){return b.textContent.trim();}).filter(function(t){return t.length < 15;}).slice(0,8).join('|');
      })()`,
      awaitPromise: true, returnByValue: true
    });
    console.log('Modify & save:', r1.result?.result?.value);

    // 等一下看有没有捕获
    await new Promise(r => setTimeout(r, 5000));

    if (patchBody) {
      const fs = require('fs');
      fs.writeFileSync('C:/Users/Admin/Desktop/patch_template.json', patchBody);
      console.log('\nPatch template saved to Desktop!');
    }
    if (postBody) {
      const fs = require('fs');
      fs.writeFileSync('C:/Users/Admin/Desktop/post_template.json', postBody);
      console.log('Post template saved to Desktop!');
    }
    if (!patchBody && !postBody) {
      console.log('\nNo templates captured. Trying alternative approach...');
    }

  } catch(e) { console.error(e); }
  ws.close();
});
ws.on('error', e => { console.error(e.message); process.exit(1); });
setTimeout(() => { process.exit(0); }, 20000);
