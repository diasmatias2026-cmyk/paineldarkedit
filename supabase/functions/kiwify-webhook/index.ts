const json=(data:unknown,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
Deno.serve(async(req:Request)=>{
 if(req.method!=='POST')return json({error:'method_not_allowed'},405);
 const token=new URL(req.url).searchParams.get('token');
 if(!token||token.length<40||token.length>128)return json({error:'unauthorized'},401);
 if(!req.headers.get('content-type')?.includes('application/json'))return json({error:'json_required'},415);
 if(Number(req.headers.get('content-length')||0)>32768)return json({error:'payload_too_large'},413);
 try{
  const reader=req.body?.getReader();if(!reader)return json({error:'invalid_body'},400);const parts:Uint8Array[]=[];let size=0;
  while(true){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>32768){await reader.cancel();return json({error:'payload_too_large'},413);}parts.push(value);}
  const bytes=new Uint8Array(size);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.length;}
  let payload;try{payload=JSON.parse(new TextDecoder().decode(bytes));}catch{return json({error:'invalid_json'},400);}
  if(!payload||typeof payload!=='object'||Array.isArray(payload))return json({error:'invalid_payload'},400);
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(token)))).map(b=>b.toString(16).padStart(2,'0')).join('');
  const base=Deno.env.get('SUPABASE_URL'),key=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');if(!base||!key)return json({error:'not_configured'},503);
  const response=await fetch(base+'/rest/v1/rpc/darkedit_process_kiwify',{method:'POST',headers:{apikey:key,Authorization:'Bearer '+key,'Content-Type':'application/json'},body:JSON.stringify({p_token_hash:hash,p_payload:payload}),signal:AbortSignal.timeout(15000)});
  if(!response.ok){const detail=await response.json().catch(()=>({}));return json({error:detail.code==='42501'?'unauthorized':detail.code==='22023'?'invalid_payload':'processing_failed'},detail.code==='42501'?403:detail.code==='22023'?400:503);}
  return json(await response.json());
 }catch{return json({error:'processing_failed'},503);}
});
