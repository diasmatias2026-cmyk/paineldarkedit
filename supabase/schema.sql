create schema if not exists darkedit_private;
revoke all on schema darkedit_private from public, anon;
grant usage on schema darkedit_private to authenticated;
create table darkedit_private.administrators(email text primary key check(email=lower(email)));
alter table darkedit_private.administrators enable row level security;
insert into darkedit_private.administrators(email) values ('diasmatias2026@gmail.com');
create function darkedit_private.is_admin() returns boolean language sql stable security definer set search_path='' as $$
 select exists(select 1 from auth.users u join darkedit_private.administrators a on a.email=lower(u.email)
 where u.id=(select auth.uid()) and u.email_confirmed_at is not null and not coalesce(u.is_anonymous,false)
 and exists(select 1 from auth.sessions s where s.user_id=u.id and s.id::text=(select auth.jwt()->>'session_id')));
$$;
revoke all on function darkedit_private.is_admin() from public,anon;
grant execute on function darkedit_private.is_admin() to authenticated;
create table public.darkedit_clients(
 id uuid primary key default gen_random_uuid(), name text not null check(length(trim(name)) between 1 and 100),
 email text not null unique check(email=lower(trim(email)) and length(email)<=254 and email ~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$'),
 status text not null default 'ativa' check(status in ('ativa','pendente','bloqueada')),
 created_at timestamptz not null default now(), device_name text check(length(device_name)<=120),
 device_platform text check(device_platform in ('Windows','Android')), device_seen_at timestamptz,
 check((device_name is null and device_platform is null and device_seen_at is null) or (device_name is not null and device_platform is not null))
);
create table public.darkedit_events(id bigint generated always as identity primary key, actor uuid, text text not null, created_at timestamptz not null default now());
create table public.darkedit_offer(id integer primary key check(id=1), price_cents integer not null check(price_cents between 1 and 10000000),phone text not null check(phone ~ '^[0-9]{10,13}$'));
insert into public.darkedit_offer values(1,9790,'34999929764');
alter table public.darkedit_clients enable row level security;
alter table public.darkedit_events enable row level security;
alter table public.darkedit_offer enable row level security;
revoke all on public.darkedit_clients,public.darkedit_events,public.darkedit_offer from anon,authenticated;
grant select,insert on public.darkedit_clients to authenticated;
grant update(name,email,status,device_name,device_platform,device_seen_at) on public.darkedit_clients to authenticated;
grant select on public.darkedit_events,public.darkedit_offer to authenticated;
grant update(price_cents,phone) on public.darkedit_offer to authenticated;
create policy admin_select on public.darkedit_clients for select to authenticated using((select darkedit_private.is_admin()));
create policy admin_insert on public.darkedit_clients for insert to authenticated with check((select darkedit_private.is_admin()));
create policy admin_update on public.darkedit_clients for update to authenticated using((select darkedit_private.is_admin())) with check((select darkedit_private.is_admin()));
create policy admin_select on public.darkedit_events for select to authenticated using((select darkedit_private.is_admin()));
create policy admin_select on public.darkedit_offer for select to authenticated using((select darkedit_private.is_admin()));
create policy admin_update on public.darkedit_offer for update to authenticated using((select darkedit_private.is_admin())) with check((select darkedit_private.is_admin()));
create function darkedit_private.audit_change() returns trigger language plpgsql security definer set search_path='' as $$
begin
 if not darkedit_private.is_admin() then raise exception 'not authorized' using errcode='42501'; end if;
 if tg_table_name='darkedit_clients' then
 insert into public.darkedit_events(actor,text) values(auth.uid(),case when tg_op='INSERT' then 'Cliente cadastrado: '||new.name when old.status is distinct from new.status then 'Licença alterada para '||new.status||': '||new.name when old.device_name is not null and new.device_name is null then 'Aparelho desvinculado: '||new.name else 'Cliente atualizado: '||new.name end);
 else insert into public.darkedit_events(actor,text) values(auth.uid(),'Configurações da oferta atualizadas.'); end if;
 return new;
end;$$;
revoke all on function darkedit_private.audit_change() from public,anon,authenticated;
create trigger audit_clients after insert or update on public.darkedit_clients for each row execute function darkedit_private.audit_change();
create trigger audit_offer after update on public.darkedit_offer for each row execute function darkedit_private.audit_change();
create index darkedit_clients_created on public.darkedit_clients(created_at desc);
create index darkedit_events_created on public.darkedit_events(created_at desc);
