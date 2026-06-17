const WebSocket = require('ws');
const ws = new WebSocket('ws://127.0.0.1:9223/devtools/page/B3F8DF7A128D390FFDD0095560E37D7F');
let msgId = 0;
const pending = new Map();
let capturedPatch = null;

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
  if (r.method === 'Network.requestWillBeSent') {
    const url = r.params.request?.url || '';
    const method = r.params.request?.method || '';
    if (url.includes('/rapi/d/customer') && method === 'PATCH') {
      capturedPatch = r.params.request?.postData;
      console.log('=== PATCH CAPTURED ===');
      console.log('Length:', capturedPatch?.length);
    }
  }
});

ws.on('open', async () => {
  try {
    await send('Network.enable', {});
    await new Promise(r => setTimeout(r, 1000));

    // Step 1: 检查页面上的Vue组件
    const r1 = await send('Runtime.evaluate', {
      expression: '(function(){var allEls=document.querySelectorAll("*");var vueEls=[];for(var i=0;i<allEls.length;i++){var el=allEls[i];if(el.__vue__&&el.__vue__.$options&&el.__vue__.$options.name){vueEls.push(el.__vue__.$options.name);}}return vueEls.join(",");})()',
      returnByValue: true
    });
    console.log('Vue components:', r1.result?.result?.value);

    // Step 2: 找编辑相关的组件
    const r2 = await send('Runtime.evaluate', {
      expression: '(function(){var allEls=document.querySelectorAll("*");for(var i=0;i<allEls.length;i++){var el=allEls[i];if(el.__vue__&&el.__vue__.$options&&el.__vue__.$options.name&&(el.__vue__.$options.name.toLowerCase().indexOf("edit")>=0||el.__vue__.$options.name.toLowerCase().indexOf("customer")>=0)){var methods=Object.getOwnPropertyNames(Object.getPrototypeOf(el.__vue__)).filter(function(m){return typeof el.__vue__[m]==="function";});return el.__vue__.$options.name+":"+methods.slice(0,20).join(",");}}return "not found";})()',
      returnByValue: true
    });
    console.log('Edit component:', r2.result?.result?.value);

    // Step 3: 直接触发XHR拦截来抓PATCH
    const r3 = await send('Runtime.evaluate', {
      expression: '(function(){window.__capturedPatch=null;var origOpen=XMLHttpRequest.prototype.open;var origSend=XMLHttpRequest.prototype.send;XMLHttpRequest.prototype.open=function(m,u){this.__url=u;return origOpen.apply(this,arguments);};XMLHttpRequest.prototype.send=function(b){if(this.__url&&this.__url.indexOf("/rapi/d/customer")>=0){window.__capturedPatch=b;return {ok:true,status:200,text:function(){return JSON.stringify({code:0,success:true});}};}return origSend.apply(this,arguments);};return "XHR interceptor installed";})()',
      returnByValue: true
    });
    console.log('XHR interceptor:', r3.result?.result?.value);

  } catch(e) { console.error(e); }
  ws.close();
});
ws.on('error', e => { console.error(e.message); process.exit(1); });
setTimeout(() => { process.exit(0); }, 15000);
