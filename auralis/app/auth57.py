"""Supabase GoTrue password authentication with server-verified user identities.

Only the access token is returned to JavaScript (in memory); refresh tokens are
stored in an HttpOnly cookie. Calls to /user validate tokens with Supabase Auth.
No service_role secret is used, and X-Owner-Token is never accepted in cloud mode.
"""
import os
import re
import uuid
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator

class Credentials(BaseModel):
    email: str = Field(min_length=5,max_length=254)
    password: str = Field(min_length=8,max_length=200)
    @field_validator('email')
    @classmethod
    def valid_email(cls,value):
        value=value.strip().lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value):
            raise ValueError('Enter a valid email address.')
        return value

class RecoveryRequest(BaseModel):
    email: str = Field(min_length=5,max_length=254)

class NewPassword(BaseModel):
    password: str = Field(min_length=8,max_length=200)

class AccountRemoval(BaseModel):
    password: str = Field(min_length=8,max_length=200)
    confirmation: str = Field(pattern=r'^DELETE MY ACCOUNT$')


class SupabaseAuth:
    def __init__(self,url,key):
        target=url.rstrip('/')
        parsed=urlparse(target)
        if parsed.scheme!='https' or not re.fullmatch(r'[a-z0-9-]+\.supabase\.co',parsed.hostname or ''):
            raise ValueError('SUPABASE_URL must use your HTTPS *.supabase.co project address.')
        if not key or len(key)<15:raise ValueError('SUPABASE_PUBLISHABLE_KEY is required.')
        self.base=target+'/auth/v1';self.key=key
    def request(self,method,path,body=None,access=None):
        headers={'apikey':self.key,'Content-Type':'application/json'}
        if access:headers['Authorization']='Bearer '+access
        try:
            with httpx.Client(timeout=httpx.Timeout(12,connect=5),follow_redirects=False) as client:
                res=client.request(method,self.base+path,headers=headers,json=body)
        except httpx.RequestError:
            raise HTTPException(503,'Sign-in service temporarily unavailable. Please try again.')
        if res.status_code>=400:
            if res.status_code in (400,401,403):
                raise HTTPException(401 if method=='GET' else 400,'Invalid credentials or expired session. Please sign in again.')
            if res.status_code==429:raise HTTPException(429,'Too many attempts. Try again later.')
            raise HTTPException(503,'Account service unavailable. Try again later.')
        try:return res.json()
        except ValueError:raise HTTPException(502,'Account service returned an invalid response.')
    def user(self,token):
        if not token or len(token)>8192:raise HTTPException(401,'Sign in to continue.')
        user=self.request('GET','/user',access=token)
        if not isinstance(user,dict) or not user.get('id'):
            raise HTTPException(401,'Session could not be verified.')
        try:uuid.UUID(user['id'])
        except (ValueError,TypeError):raise HTTPException(401,'Invalid user identity.')
        return user
    def signup(self,email,password): return self.request('POST','/signup',{'email':email,'password':password})
    def login(self,email,password): return self.request('POST','/token?grant_type=password',{'email':email,'password':password})
    def refresh(self,refresh_token): return self.request('POST','/token?grant_type=refresh_token',{'refresh_token':refresh_token})
    def logout(self,access):return self.request('POST','/logout',access=access)
    def recovery(self,email,redirect):return self.request('POST','/recover?redirect_to='+__import__('urllib.parse',fromlist=['quote']).quote(redirect,safe=''),{'email':email})
    def password(self,token,password):return self.request('PUT','/user',{'password':password},access=token)

    def admin_delete_user(self,uid):
        """Delete a verified account using a server-only Supabase service-role key.

        This key must never be returned to browser JavaScript or committed to Git.
        """
        try:uid=str(uuid.UUID(uid))
        except (TypeError,ValueError):raise HTTPException(422,'Invalid account identity.')
        secret=os.getenv('SUPABASE_SERVICE_ROLE_KEY','')
        if not secret:
            raise HTTPException(503,'Automated account deletion is not configured. Please contact support.')
        headers={'apikey':secret,'Authorization':'Bearer '+secret}
        try:
            with httpx.Client(timeout=httpx.Timeout(15,connect=5),follow_redirects=False) as client:
                result=client.delete(self.base+'/admin/users/'+uid,headers=headers)
        except httpx.RequestError:
            raise HTTPException(503,'Account service unavailable. Try again later.')
        if result.status_code not in (200,204):
            raise HTTPException(503,'Account removal could not be completed. Contact support.')
        return True
