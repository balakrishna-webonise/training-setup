{{
    config(
        materialized='table'
    )
}}


with trial_balances as (
    select * from {{ source('public', 'tb') }}
),

tb_transformed as (
    select
        row_number() over (order by "Account_ID", "Month") as id,
        "Account_ID" as gl_number,
        "Account_Name" as gl_name,
        "Category" as category,
        left("Month", 4)::int as year,
        right("Month", 2)::int as month,
        "Debit" as debit,
        "Credit" as credit,
        "Debit" - "Credit" as period_amount
    from
        trial_balances
)

select * from tb_transformed
