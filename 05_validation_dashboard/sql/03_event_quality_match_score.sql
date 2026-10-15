-- 03_event_quality_match_score.sql
-- Computes Meta & Google Event Match Quality (EMQ) Score
-- Target: > 8.5/10 (High Quality match on B2B buyers)

select
    date(received_at) as event_date,
    count(*) as total_server_events,
    
    -- Identifier coverage rates
    round(countif(has_hashed_email) / count(*) * 100, 1) as email_match_rate_pct,
    round(countif(has_hashed_phone) / count(*) * 100, 1) as phone_match_rate_pct,
    round(countif(has_fbp_cookie) / count(*) * 100, 1) as fbp_cookie_rate_pct,
    round(countif(has_fbc_click_id) / count(*) * 100, 1) as fbc_click_id_rate_pct,
    round(countif(has_client_ip and has_user_agent) / count(*) * 100, 1) as network_headers_pct,

    -- Overall Composite EMQ Score (1-10)
    round(
        (countif(has_hashed_email) * 3.5 +
         countif(has_hashed_phone) * 2.0 +
         countif(has_fbp_cookie) * 2.0 +
         countif(has_fbc_click_id) * 1.5 +
         countif(has_client_ip) * 1.0) / count(*), 1
    ) as composite_emq_score

from `company_b2b_analytics.gtm_server_event_quality`
where received_at >= timestamp_sub(current_timestamp(), interval 30 day)
group by 1
order by 1 desc
