{% test sequential_months(model, year_column, month_column) %}


with ordered_months as (
    select
        {{ year_column }} as year,
        {{ month_column }} as month,
        ({{ year_column }} * 100) + {{ month_column }} as year_month,
        row_number() over (order by {{ year_column }}, {{ month_column }}) as rn
    from {{ model }}
    group by {{ year_column }}, {{ month_column }}
),

gaps as (
    select
        o1.year as current_year,
        o1.month as current_month,
        o1.year_month as current_year_month,
        o2.year as next_year,
        o2.month as next_month,
        o2.year_month as next_year_month,
        o2.year_month - o1.year_month as month_diff
    from ordered_months o1
    left join ordered_months o2
        on o2.rn = o1.rn + 1
    where o2.year_month - o1.year_month > 1
       or (o2.year_month is null and o1.rn < (select max(rn) from ordered_months))
)

select * from gaps

{% endtest %}
