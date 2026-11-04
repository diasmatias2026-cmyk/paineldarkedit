create table darkedit_private.access_limits(scope text not null,window_at timestamptz not null,count integer not null,primary key(scope,window_at));
alter table darkedit_private.access_limits enable row level security;
create table darkedit_private.device_bindings(client_id uuid primary key references public.darkedit_clients(id),device_hash text not null,token_hash text not null);
alter table darkedit_private.device_bindings enable row level security;
create function darkedit_private.member_access(p_email text,p_ip_hash text,p_action text,p_device_hash text default null,p_token_hash text default null,p_device_name text default null) returns jsonb language plpgsql security definer set search_path='' as $$
declare client public.darkedit_clients%rowtype;binding darkedit_private.device_bindings%rowtype;hits integer;window_time timestamptz:=date_trunc('hour',now());
begin
 if coalesce(auth.jwt()->>'role','')<>'service_role' then raise exception 'not authorized' using errcode='42501';end if;
 if p_ip_hash !~ '^[0-9a-f]{64}$' or length(p_email)>254 or p_email !~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$' then return jsonb_build_object('allowed',false);end if;
 insert into darkedit_private.access_limits(scope,window_at,count) values(p_ip_hash,window_time,1) on conflict(scope,window_at) do update set count=access_limits.count+1 returning count into hits;
 if hits>120 then return jsonb_build_object('allowed',false,'limited',true);end if;
 delete from darkedit_private.access_limits where window_at<now()-interval '2 days';
 select * into client from public.darkedit_clients where email=lower(trim(p_email)) for update;
 if not found or client.status<>'ativa' then return jsonb_build_object('allowed',false);end if;
 if p_action in ('list','installer','extension') then return jsonb_build_object('allowed',true);end if;
 if p_action<>'activate' or p_device_hash is null or p_token_hash is null or p_device_hash !~ '^[0-9a-f]{64}$' or p_token_hash !~ '^[0-9a-f]{64}$' then return jsonb_build_object('allowed',false);end if;
 select * into binding from darkedit_private.device_bindings where client_id=client.id;
 if found then
  if binding.device_hash<>p_device_hash or binding.token_hash<>p_token_hash then return jsonb_build_object('allowed',false,'device_conflict',true);end if;
 else
  if client.device_name is not null then return jsonb_build_object('allowed',false,'device_conflict',true);end if;
  insert into darkedit_private.device_bindings(client_id,device_hash,token_hash) values(client.id,p_device_hash,p_token_hash);
  insert into public.darkedit_events(actor,text) values(null,'Primeiro aparelho ativado: '||client.name||'.');
 end if;
 update public.darkedit_clients set device_name=left(coalesce(p_device_name,'Computador Windows'),120),device_platform='Windows',device_seen_at=now() where id=client.id;
 return jsonb_build_object('allowed',true,'device_bound',true);
end;$$;
revoke all on function darkedit_private.member_access(text,text,text,text,text,text) from public,anon,authenticated;
grant execute on function darkedit_private.member_access(text,text,text,text,text,text) to service_role;
create function public.darkedit_member_access(p_email text,p_ip_hash text,p_action text,p_device_hash text default null,p_token_hash text default null,p_device_name text default null) returns jsonb language sql security invoker set search_path='' as $$select darkedit_private.member_access(p_email,p_ip_hash,p_action,p_device_hash,p_token_hash,p_device_name);$$;
revoke all on function public.darkedit_member_access(text,text,text,text,text,text) from public,anon,authenticated;
grant execute on function public.darkedit_member_access(text,text,text,text,text,text) to service_role;
create function darkedit_private.unlink_device_binding() returns trigger language plpgsql security definer set search_path='' as $$begin if old.device_name is not null and new.device_name is null and darkedit_private.is_admin() then delete from darkedit_private.device_bindings where client_id=new.id;end if;return new;end;$$;
revoke all on function darkedit_private.unlink_device_binding() from public,anon,authenticated;
create trigger unlink_device_binding after update on public.darkedit_clients for each row execute function darkedit_private.unlink_device_binding();
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types) values('darkedit-downloads','darkedit-downloads',false,52428800,array['application/octet-stream','application/zip','application/x-msdownload']);
create policy darkedit_admin_upload on storage.objects for insert to authenticated with check(bucket_id='darkedit-downloads' and (select darkedit_private.is_admin()));
create policy darkedit_admin_read on storage.objects for select to authenticated using(bucket_id='darkedit-downloads' and (select darkedit_private.is_admin()));
