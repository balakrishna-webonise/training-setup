with income_data as (
    select
        year,
        month,
        revenue,
        expense,
        revenue - expense as net_income
    from {{ ref('income_statement') }}
)

select
    year,
    month,
    net_income
from income_data
where month > 3
  and net_income <= 0
  