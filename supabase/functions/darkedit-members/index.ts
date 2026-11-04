const origins=new Set(['https://darkedit-vendas.vercel.app','http://127.0.0.1:5190']);
const releases={installer:{path:'windows/DarkEdit-Setup-1.2.1-x64.exe',name:'DarkEdit-Setup-1.2.1-x64.exe'},extension:{path:'bonus/DarkDownload-0.6.0.zip',name:'DarkDownload-0.6.0.zip'}};
const sha=async(s:string)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s)))).map(b=>b.toString(16).padStart(2,'0')).join('');
Deno.serve(async(req:Request)=>{
 const origin=req.headers.get('origin')||'';const headers:Record<string,string>={'Content-Type':'application/json','Cache-Control':'no-store','Vary':'Origin'};
 if(origins.has(origin))headers['Access-Control-Allow-Origin']=origin;
 const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers});
 if(req.method==='OPTIONS')return new Response(null,{status:origins.has(origin)?204:403,headers:{...headers,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'content-type'}});
 if(req.method!=='POST')return json({error:'method_not_allowed'},405);
 if(origin&&!origins.has(origin))return json({error:'not_allowed'},403);
 try{
  if(Number(req.headers.get('content-length')||0)>4096)return json({error:'invalid_request'},413);
  const reader=req.body?.getReader();if(!reader)return json({error:'invalid_request'},400);const chunks:Uint8Array[]=[];let size=0;while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>4096){await reader.cancel();return json({error:'invalid_request'},413);}chunks.push(value);}const data=new Uint8Array(size);let offset=0;for(const part of chunks){data.set(part,offset);offset+=part.length;}let body;try{body=JSON.parse(new TextDecoder().decode(data));}catch{return json({error:'invalid_request'},400);}
  if(!body||typeof body!=='object'||Array.isArray(body))return json({error:'invalid_request'},400);
  const email=typeof body.email==='string'?body.email.trim().toLowerCase():'';const action=body.action||'list';if(!email||email.length>254||!['list','installer','extension','activate'].includes(action))return json({error:'invalid_request'},400);
  const base=Deno.env.get('SUPABASE_URL'),key=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');if(!base||!key)return json({error:'unavailable'},503);
  const ip=req.headers.get('cf-connecting-ip')||req.headers.get('x-forwarded-for')?.split(',')[0].trim()||'unknown';const ipHash=await sha(ip+key);
  const rpc=await fetch(base+'/rest/v1/rpc/darkedit_member_access',{method:'POST',headers:{apikey:key,Authorization:'Bearer '+key,'Content-Type':'application/json'},body:JSON.stringify({p_email:email,p_ip_hash:ipHash,p_action:action,p_device_hash:typeof body.device_hash==='string'?body.device_hash:null,p_token_hash:typeof body.token_hash==='string'?body.token_hash:null,p_device_name:typeof body.device_name==='string'?body.device_name.slice(0,120):null}),signal:AbortSignal.timeout(15000)});
  if(!rpc.ok)return json({error:'unavailable'},503);const permission=await rpc.json();
  if(!permission.allowed)return json({error:permission.limited?'try_later':permission.device_conflict?'device_already_bound':'access_not_available'},permission.limited?429:403);
  if(action==='activate')return json({allowed:true,device_bound:true});
  if(action==='list')return json({allowed:true,downloads:[{id:'installer',title:'DarkEdit para Windows',version:'1.2.1'},{id:'extension',title:'Bônus DarkDownload',version:'0.6.0'}]});
  const release=releases[action as 'installer'|'extension'];const signed=await fetch(base+'/storage/v1/object/sign/darkedit-downloads/'+release.path,{method:'POST',headers:{apikey:key,Authorization:'Bearer '+key,'Content-Type':'application/json'},body:JSON.stringify({expiresIn:120}),signal:AbortSignal.timeout(15000)});
  if(!signed.ok)return json({error:'download_unavailable'},503);const result=await signed.json();if(!result.signedURL)return json({error:'download_unavailable'},503);
  return json({url:base+'/storage/v1'+result.signedURL,filename:release.name,expires_in:120});
 }catch{return json({error:'unavailable'},503);}
});
