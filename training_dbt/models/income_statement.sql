
with tb as (
    select * from {{ ref('staging_trial_balances') }}
),

income_statement as (
    select
        year,
        month,
        sum(
            case
                when category = 'Revenue'
                then period_amount
                else 0
            end
        ) as revenue,
        sum(
            case
                when category = 'Expense'
                then period_amount
                else 0
            end
        ) as expense
    from tb
    group by year, month
    order by year, month
)

select
    year,
    month,
    revenue,
    expense,
    revenue - expense as net_income,
    sum(revenue - expense) over (
        partition by year
        order by month
        rows between unbounded preceding and current row
    ) as ytd_net_income
from income_statement
where revenue - expense > 0
order by year, month
