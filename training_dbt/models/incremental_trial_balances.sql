{{ 
    config(
        materialized='incremental',
        unique_key='id',
        incremental_strategy='merge'
    ) 
}}

select
    *,
    current_timestamp as loaded_at
from {{ ref('staging_trial_balances') }}
{% if is_incremental() %}
  where id not in (select id from {{ this }})
{% endif %}
