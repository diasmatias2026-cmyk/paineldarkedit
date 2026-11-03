alter table public.darkedit_clients add column payment_block boolean not null default false;
create function darkedit_private.mark_manual_license() returns trigger language plpgsql security invoker set search_path='' as $$begin if darkedit_private.is_admin() then new.payment_block:=false;end if;return new;end;$$;
revoke all on function darkedit_private.mark_manual_license() from public,anon,authenticated;
create trigger mark_manual_license before update on public.darkedit_clients for each row execute function darkedit_private.mark_manual_license();
create or replace function darkedit_private.process_kiwify(p_token_hash text,p_payload jsonb) returns jsonb language plpgsql security definer set search_path='' as $$
declare cfg darkedit_private.kiwify_config%rowtype; oid text; event_type text; email_value text; customer_name text; new_status text; old_order darkedit_private.kiwify_orders%rowtype; event_key text; inserted_key text;
begin
 if coalesce(auth.jwt()->>'role','')<>'service_role' then raise exception 'not authorized' using errcode='42501'; end if;
 select * into cfg from darkedit_private.kiwify_config where id=1;
 if not found or cfg.token_hash<>p_token_hash then raise exception 'invalid webhook authentication' using errcode='42501'; end if;
 if p_payload->'Product'->>'product_id' is distinct from cfg.product_id then return jsonb_build_object('accepted',true,'action','ignored_product'); end if;
 if p_payload->>'sale_type' is distinct from 'producer' then return jsonb_build_object('accepted',true,'action','ignored_sale_type'); end if;
 oid:=p_payload->>'order_id';event_type:=p_payload->>'webhook_event_type';
 if oid is null or length(oid)>100 or oid !~ '^[A-Za-z0-9_-]+$' then raise exception 'invalid order id' using errcode='22023'; end if;
 new_status:=case when event_type='order_approved' and p_payload->>'order_status'='paid' then 'paid' when event_type='order_refunded' and p_payload->>'order_status'='refunded' then 'refunded' when event_type='order_chargeback' and p_payload->>'order_status' in ('chargedback','chargeback') then 'chargedback' else null end;
 if new_status is null then return jsonb_build_object('accepted',true,'action','ignored_event'); end if;
 email_value:=lower(trim(p_payload->'Customer'->>'email'));
 if email_value is null or length(email_value)>254 or email_value !~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$' then raise exception 'invalid buyer email' using errcode='22023'; end if;
 customer_name:=left(coalesce(nullif(trim(p_payload->'Customer'->>'full_name'),''),email_value),100);
 event_key:=md5(oid||':'||event_type||':'||new_status);
 perform pg_advisory_xact_lock(hashtextextended('kiwify-order:'||oid,0));
 insert into darkedit_private.kiwify_receipts(event_key,order_id,event_type,mode) values(event_key,oid,event_type,case when cfg.enabled then 'live' else 'dry_run' end) on conflict do nothing returning kiwify_receipts.event_key into inserted_key;
 if inserted_key is null then return jsonb_build_object('accepted',true,'action','duplicate'); end if;
 if not cfg.enabled then return jsonb_build_object('accepted',true,'action','dry_run','license_changed',false); end if;
 perform pg_advisory_xact_lock(hashtextextended('kiwify-email:'||email_value,0));
 select * into old_order from darkedit_private.kiwify_orders where order_id=oid;
 if found then
  if old_order.email<>email_value or old_order.product_id<>cfg.product_id then raise exception 'order identity mismatch' using errcode='22023'; end if;
  if old_order.status in ('refunded','chargedback') and new_status='paid' then return jsonb_build_object('accepted',true,'action','ignored_late_approval'); end if;
 end if;
 insert into darkedit_private.kiwify_orders(order_id,product_id,email,status) values(oid,cfg.product_id,email_value,new_status) on conflict(order_id) do update set status=excluded.status,updated_at=now();
 if new_status='paid' then
  insert into public.darkedit_clients(name,email,status,license_origin) values(customer_name,email_value,'ativa','kiwify') on conflict(email) do update set status='ativa',payment_block=false where darkedit_clients.license_origin='kiwify' and darkedit_clients.payment_block;
 else
  if not exists(select 1 from darkedit_private.kiwify_orders where email=email_value and status='paid') then
   update public.darkedit_clients set status='bloqueada',payment_block=true where email=email_value and license_origin='kiwify';
  end if;
 end if;
 insert into public.darkedit_events(actor,text) values(null,'Kiwify: pedido '||oid||' — '||new_status||'.');
 return jsonb_build_object('accepted',true,'action',new_status);
end;$$;
