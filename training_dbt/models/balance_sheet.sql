with tb as (
    select * from {{ ref('staging_trial_balances') }}
),

-- Aggregate totals by period and account category
period_totals as (
    select
        year,
        month,
        sum(case when category = 'Asset' then coalesce(period_amount,0) else 0 end) as total_assets,
        -- Liability and Equity balances are stored as credit balances (period_amount = debit - credit => negative)
        -- Negate to represent positive liabilities/equity totals
        sum(case when category = 'Liability' then -coalesce(period_amount,0) else 0 end) as total_liabilities,
        sum(case when category = 'Equity' then -coalesce(period_amount,0) else 0 end) as total_equity
    from tb
    where category in ('Asset','Liability','Equity')
    group by year, month
),

-- Compute derived columns and ranking to pick the most recent period
period_calculated as (
    select
        year,
        month,
        total_assets,
        total_liabilities,
        total_equity,
        (total_liabilities + total_equity) as total_liabilities_and_equity,
        case when total_assets = (total_liabilities + total_equity) then true else false end as accounting_equation_valid,
        row_number() over (order by year desc, month desc) as rn
    from period_totals
)

select
    year,
    month,
    total_assets,
    total_liabilities,
    total_equity,
    total_liabilities_and_equity,
    accounting_equation_valid
from period_calculated
where rn = 1  -- show only the latest month
order by year desc, month desc

-- The accounting equation (Assets = Liabilities + Equity) should always balance
-- because on a double-entry accounting system every debit has a corresponding credit.
-- Assets represent debit balances and Liabilities/Equity represent credit balances,
-- so after sign normalization the totals should be equal for a balanced ledger.
