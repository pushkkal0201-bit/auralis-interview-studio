"use strict";
/* Authenticated mode uses a short-lived access token only in memory.
 * The refresh cookie is HttpOnly and rotated server-side by Supabase.
 */
function authHeader(){
 if(window.auralisAuth?.enabled)return window.auralisAuth.token?{'Authorization':'Bearer '+window.auralisAuth.token}:{};
 return {'X-Owner-Token':owner};
}
const auralisAuth={enabled:false,token:null,user:null,ready:null,
 async refresh(){
  try{const r=await fetch('/api/auth/refresh',{method:'POST',credentials:'same-origin'});
   if(!r.ok){this.token=null;return false;}
   const d=await r.json();this.token=d.access_token;this.user=d.user;return true;
  }catch{this.token=null;return false;}
 },
 async logout(){
  try{await fetch('/api/auth/logout',{method:'POST',headers:this.token?{'Authorization':'Bearer '+this.token}:{}});}catch{}
  this.token=null;this.user=null;localStorage.removeItem('auralis-current');
  if(typeof session!=='undefined')session=null;
  document.getElementById('account-auth').hidden=false;document.body.classList.add('auth-locked');
  document.getElementById('account-password').value='';
 },
 setSession(data){this.token=data.access_token;this.user=data.user;
  document.getElementById('account-auth').hidden=true;document.body.classList.remove('auth-locked');
  document.getElementById('account-email-label').textContent=this.user?.email||'Account';
  window.auralisOnLogin?.();
 }
};
window.auralisAuth=auralisAuth;
function authMessage(message,error=false){const box=document.getElementById('account-message');box.textContent=message;box.classList.toggle('error',error);}
async function authSubmit(path,payload){
 const r=await fetch('/api/auth/'+path,{method:'POST',headers:{'Content-Type':'application/json',...(path==='password'?authHeader():{})},body:JSON.stringify(payload)});
 const result=await r.json().catch(()=>({detail:'Something went wrong. Please try again.'}));
 if(!r.ok)throw Error(result.detail||'Account request failed.');
 return result;
}
async function bootAuth(){
 let config;
 try{const response=await fetch('/api/public-config');config=await response.json();}
 catch{return;}
 if(!config.authentication_required)return;
 // The cloud edition stores records against verified accounts, not a browser-only SQLite workspace.
 const privacyCopy=document.querySelector('.privacy-panel p');
 if(privacyCopy)privacyCopy.textContent='Your interview records, uploaded CV details, assessments and learning history are stored with your verified account in the hosted database. You can delete Auralis data here. Removing your Supabase sign-in identity is a separate support request.';
 const deleteButton=document.getElementById('delete-all');
 if(deleteButton)deleteButton.textContent='Delete my Auralis records';
 const accountRemoval=document.getElementById('account-removal');
 if(accountRemoval)accountRemoval.hidden=false;

 auralisAuth.enabled=true;
 document.getElementById('account-auth').hidden=false;
 document.body.classList.add('auth-locked');
 const menu=document.getElementById('account-controls');menu.hidden=false;
 const params=new URLSearchParams(location.hash.substring(1));
 if(params.get('type')==='recovery'&&params.get('access_token')){
   auralisAuth.token=params.get('access_token');
   history.replaceState(null,'',location.pathname+location.search);
   document.getElementById('account-password-reset').hidden=false;
   document.getElementById('account-credentials').hidden=true;
   authMessage('Choose a new password for your account.');return;
 }
 if(await auralisAuth.refresh()){
  auralisAuth.setSession({access_token:auralisAuth.token,user:auralisAuth.user});
 }
}
auralisAuth.ready=bootAuth();
document.addEventListener('DOMContentLoaded',()=>{
 const form=document.getElementById('account-credentials');
 form.addEventListener('submit',async e=>{
  e.preventDefault();authMessage('');
  const submit=document.getElementById('account-login');submit.disabled=true;
  try{
   const data=await authSubmit('login',{email:document.getElementById('account-email').value.trim(),password:document.getElementById('account-password').value});
   auralisAuth.setSession(data);
  }catch(err){authMessage(err.message,true);}finally{submit.disabled=false;}
 });
 document.getElementById('account-register').addEventListener('click',async()=>{
  authMessage('');try{
   const data=await authSubmit('signup',{email:document.getElementById('account-email').value.trim(),password:document.getElementById('account-password').value});
   if(data.verification_required)authMessage(data.message);else auralisAuth.setSession(data);
  }catch(err){authMessage(err.message,true);}
 });
 document.getElementById('account-forgot').addEventListener('click',async()=>{
  authMessage('');try{const d=await authSubmit('recover',{email:document.getElementById('account-email').value.trim()});authMessage(d.message);}catch(err){authMessage(err.message,true);}
 });
 document.getElementById('account-password-reset').addEventListener('submit',async e=>{
  e.preventDefault();authMessage('');try{
   await authSubmit('password',{password:document.getElementById('account-new-password').value});
   await auralisAuth.logout();document.getElementById('account-password-reset').hidden=true;form.hidden=false;
   authMessage('Password updated. Sign in with your new password.');
  }catch(err){authMessage(err.message,true);}
 });
 document.getElementById('account-removal-form')?.addEventListener('submit',async e=>{
  e.preventDefault();
  const feedback=document.getElementById('account-removal-message');
  const submit=e.target.querySelector('button[type="submit"]');
  if(!confirm('Permanently close this account and delete the saved Auralis data?'))return;
  submit.disabled=true;
  try{
   const r=await fetch('/api/auth/delete-account',{method:'POST',headers:{'Content-Type':'application/json',...authHeader()},body:JSON.stringify({password:document.getElementById('account-remove-password').value,confirmation:document.getElementById('account-remove-confirmation').value})});
   const d=await r.json().catch(()=>({}));
   if(!r.ok)throw Error(d.detail||'Account deletion could not be completed.');
   await auralisAuth.logout();
   feedback.textContent='Your account and Auralis records were removed.';
   e.target.reset();
  }catch(err){feedback.textContent=err.message;}
  finally{submit.disabled=false;}
 });
 document.getElementById('account-logout').onclick=()=>auralisAuth.logout();
});
