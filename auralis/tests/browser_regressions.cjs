const {chromium}=require('playwright');
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||undefined,args:['--no-sandbox']});
 const p=await b.newPage();const failures=[];
 await p.goto(process.env.APP_URL||'http://127.0.0.1:8765');
 await p.getByRole('button',{name:'Use sample CV & job'}).click();
 await p.getByRole('button',{name:'Build interview plan',exact:true}).click();
 await p.getByRole('button',{name:'Start interview',exact:true}).click();
 await p.waitForFunction(()=>session?.status==='active'&&!working);
 await p.evaluate(()=>{
  session.setup.provider='groq';window.trackStops=0;
  class MockRecorder{constructor(){this.state='inactive';this.mimeType='audio/webm';}static isTypeSupported(){return true;}start(){this.state='recording';}stop(){this.state='inactive';if(this.onstop)this.onstop();}}
  window.MediaRecorder=MockRecorder;
  Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{getUserMedia:()=>new Promise(resolve=>window.resolveMedia=()=>resolve({getTracks:()=>[{stop(){window.trackStops++;}}]}))}});
  capture('answer');show('setup');resolveMedia();
 });
 await p.waitForTimeout(100);
 if(!await p.evaluate(()=>!recorder&&window.trackStops>0))failures.push('Permission resolving after navigation starts microphone');
 await p.evaluate(()=>{stopCapture();show('arena');navigator.mediaDevices.getUserMedia=async()=>({getTracks:()=>[{stop(){window.trackStops++;}}]});});
 await p.evaluate(async()=>{await capture('answer');});
 await p.getByRole('button',{name:'Skip question',exact:true}).click();
 await p.waitForFunction(()=>!working);
 if(!await p.evaluate(()=>!recorder))failures.push('Skipping leaves old-question recording active');
 await p.evaluate(()=>{stopCapture();session.setup.provider='demo';});
 await p.locator('#answer').fill('I use a transaction and test concurrent requests.');
 await p.getByRole('button',{name:'Submit answer',exact:true}).click();
 await p.waitForFunction(()=>!working);
 await p.getByRole('button',{name:'Finish & assess',exact:true}).click();
 await p.waitForFunction(()=>!!session?.report&&!working);
 await p.getByRole('button',{name:'Interview setup',exact:true}).click();
 await p.getByRole('button',{name:'Build interview plan',exact:true}).click();
 await p.waitForFunction(()=>session?.status==='ready'&&!working);
 await p.getByRole('button',{name:'Feedback & replay',exact:true}).click();
 if((await p.locator('#report-content').innerText()).includes('Scripted demonstration report'))failures.push('Old session report remains visible after creating a new session');
 await b.close();
 if(failures.length)throw Error(failures.join('\n'));
 console.log('3 browser regressions passed: pending microphone cancellation, stale recording cancellation, session view isolation.');
})().catch(e=>{console.error(e);process.exit(1)});
