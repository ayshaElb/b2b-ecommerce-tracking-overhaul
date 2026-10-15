-- 01_reconciliation_client_vs_server.sql
-- Reconciliation query: Client GA4 Browser Hits vs GTM Server-Side Hits vs ERP Actuals
-- Target: Verify 98% data reliability and recover ~40% lost orders

with erp_actuals as (
    select
        order_id,
        order_date,
        total_amount_ht,
        client_id,
        payment_status
    from `company_b2b_analytics.erp_orders`
    where payment_status = 'settled'
      and order_date >= current_date() - 30
),

client_hits as (
    select
        (select value.string_value from unnest(event_params) where key = 'transaction_id') as order_id,
        count(*) as hit_count,
        max(event_timestamp) as client_timestamp
    from `company_b2b_analytics.analytics_XXXXXXXXX.events_*`
    where event_name = 'purchase'
    group by 1
),

server_hits as (
    select
        order_id,
        count(*) as server_hit_count,
        max(received_at) as server_timestamp
    from `company_b2b_analytics.gtm_server_raw_events`
    where event_name = 'Purchase'
    group by 1
)

select
    e.order_id,
    e.order_date,
    e.total_amount_ht,
    coalesce(c.hit_count, 0) as client_browser_hits,
    coalesce(s.server_hit_count, 0) as server_capi_hits,

    -- Status categorization
    case
        when c.hit_count > 0 and s.server_hit_count > 0 then 'Full Parity (Client + Server)'
        when c.hit_count is null and s.server_hit_count > 0 then 'Recovered by Server (AdBlocker/Safari ITP)'
        when c.hit_count > 1 then 'Duplicate Client Hit Detected'
        else 'Untracked Anomaly'
    end as tracking_status

from erp_actuals e
left join client_hits c on e.order_id = c.order_id
left join server_hits s on e.order_id = s.order_id
