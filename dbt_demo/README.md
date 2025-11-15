# �� Trial Balance Demo Project

## 📋 Project Overview

This project demonstrates how to:
- Work with seed data in dbt
- Create staging models to transform raw data
- Build analytical models for financial reporting
- Use dbt best practices like `ref()` and `source()`

## 📁 Project Structure

```
dbt_demo/
├── seeds/
│   └── trial_balances.csv          # Seed data with trial balance entries
├── models/
│   ├── staging_trial_balances.sql  # Staging model for raw data transformation
│   ├── tb_report.sql               # Report model aggregating by category
│   └── models.yml                  # Schema definitions and sources
└── README.md                       # This file
```

## 🌱 Seed Data

### `seeds/trial_balances.csv`

This CSV file contains trial balance data with the following columns:

- **Account_ID**: Unique identifier for each account (e.g., 10000, 20000)
- **Account_Name**: Name of the account (e.g., Cash, Accounts Payable)
- **Category**: Account category (Asset, Liability, Equity, Revenue, Expense)
- **Month**: Period in YYYY-MM format (e.g., 2024-01)
- **Debit**: Debit amount for the period
- **Credit**: Credit amount for the period

**Data Coverage**: 
- Accounts: 24 accounts across 5 categories
- Time Period: January 2024 through December 2025 (24 months)

**Account Categories**:
- **Assets**: Cash, Accounts Receivable, Inventory, Prepaid Expenses, Fixed Assets
- **Liabilities**: Accounts Payable, Accrued Expenses, Short-Term Debt, Long-Term Debt
- **Equity**: Common Stock, Retained Earnings
- **Revenue**: Sales Revenue, Service Revenue, Interest Income, Other Income
- **Expense**: Various expense accounts (Salary, Rent, Utilities, Supplies, etc.)

## 📊 Models

### 1. `staging_trial_balances.sql`

**Purpose**: Staging model that cleans and transforms the raw trial balance data.

**Key Transformations**:
- Extracts year and month from the `Month` column
- Renames columns to use snake_case convention:
  - `Account_ID` → `gl_number`
  - `Account_Name` → `gl_name`
  - `Category` → `category`
- Calculates `period_amount` as `Debit - Credit`
- Materialized as a `table` for performance

**Output Columns**:
- `gl_number` (integer)
- `gl_name` (text)
- `category` (text)
- `year` (integer)
- `month` (integer)
- `debit` (numeric)
- `credit` (numeric)
- `period_amount` (numeric)

**Example Query**:
```sql
SELECT * FROM {{ ref('staging_trial_balances') }}
WHERE year = 2024 AND month = 1
```

---

### 2. `tb_report.sql`

**Purpose**: Analytical model that aggregates trial balance data by period and category.

**Key Features**:
- Groups data by `year` and `month`
- Calculates totals for:
  - **Revenue**: Sum of all Revenue category accounts
  - **Expense**: Sum of all Expense category accounts
  - **Asset**: Sum of all Asset category accounts
- Uses conditional aggregation with `CASE` statements
- Ordered by year and month chronologically

**Output Columns**:
- `year` (integer)
- `month` (integer)
- `revenue` (numeric)
- `expense` (numeric)
- `asset` (numeric)

**Business Use Case**: Provides a high-level view of financial performance and position by period.

**Example Query**:
```sql
SELECT * FROM {{ ref('tb_report') }}
WHERE year = 2024
ORDER BY month
```

---

## 🎯 Practice Exercises

### Exercise 1: Income Statement (P&L Report)

**Objective**: Create a profit and loss statement showing revenue, expenses, and net income.

**File to Create**: `models/income_statement.sql`

**Requirements**:
1. Reference `staging_trial_balances` using `{{ ref() }}`
2. Group by `year` and `month`
3. Calculate:
   - `total_revenue`: Sum of all Revenue accounts
   - `total_expenses`: Sum of all Expense accounts
   - `net_income`: Revenue - Expenses
   - `ytd_net_income`: Year-to-date cumulative net income (use window functions)
4. Filter to show only profitable months (positive net income)
5. Order by year, month

**Hint**: Use `SUM() OVER (PARTITION BY year ORDER BY month)` for YTD calculation.

**Expected Output Columns**:
- `year`, `month`
- `total_revenue`
- `total_expenses`
- `net_income`
- `ytd_net_income`

---

### Exercise 2: Balance Sheet Report

**Objective**: Create a balance sheet showing assets, liabilities, equity, and validate the accounting equation.

**File to Create**: `models/balance_sheet.sql`

**Requirements**:
1. Reference `staging_trial_balances` using `{{ ref() }}`
2. Group by `year` and `month`
3. Calculate:
   - `total_assets`: Sum of all Asset accounts
   - `total_liabilities`: Sum of all Liability accounts
   - `total_equity`: Sum of all Equity accounts
   - `total_liabilities_and_equity`: Liabilities + Equity
   - `accounting_equation_valid`: Boolean check if Assets = Liabilities + Equity
4. Show only the latest month's balance sheet (most recent year and month)
5. Include a comment explaining why the equation should balance

**Hint**: Use `RANK() OVER (ORDER BY year DESC, month DESC)` or `MAX()` to get the latest period.

**Expected Output Columns**:
- `year`, `month`
- `total_assets`
- `total_liabilities`
- `total_equity`
- `total_liabilities_and_equity`
- `accounting_equation_valid`

---

## 🚀 Getting Started

### Prerequisites
- dbt installed and configured
- Database connection set up in `profiles.yml`
- PostgreSQL (or compatible database) access
- Run `dbt deps` command to install dbt dependencies

### Setup Steps

1. **Load seed data into your database**:
   ```bash
   dbt seed
   ```
   This loads `trial_balances.csv` into your database.

2. **Run the existing models**:
   ```bash
   dbt run
   ```
   This creates the staging and report models.

3. **View compiled SQL** (optional):
   ```bash
   dbt compile
   ```
   Check the `target/compiled/` directory to see the compiled SQL.

4. **Run all models and seeds together**:
   ```bash
   dbt build
   ```

### Verify Your Work

After creating the practice exercise models:

```bash
# Verify DBT project and connection
dbt debug

# Run the new models
dbt run --select income_statement balance_sheet

# Run seeds 
dbt seed

# Run all models
dbt run

# Or run everything
dbt build

NOTE: If you face any compatibility issues while running seeds/models, then run commands with `--full-refresh` flag.
dbt run --full-refresh
dbt seed --full-refresh
```

Query the models to verify:
```sql
-- Check income statement
SELECT * FROM {{ ref('income_statement') }} LIMIT 10;

-- Check balance sheet
SELECT * FROM {{ ref('balance_sheet') }};
```

---

## 📚 Key dbt Concepts Demonstrated

1. **Seeds**: CSV files loaded as tables using `dbt seed`
2. **Sources**: Defining external data sources in `models.yml`
3. **Staging Models**: First layer of transformation from raw data
4. **Analytical Models**: Business logic and aggregations
5. **Refs**: Using `{{ ref() }}` to reference other models
6. **Config**: Setting materialization strategies
7. **CTEs**: Organizing SQL with Common Table Expressions

---

## 📖 Learning Resources

- [dbt Documentation](https://docs.getdbt.com/)
