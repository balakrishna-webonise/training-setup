from prefect import flow, task
from prefect.logging import get_run_logger
import requests
import pandas as pd
from sqlalchemy import create_engine

@task
def extract():
    logger = get_run_logger()
    logger.info("Extracting data from API")
    url = "https://jsonplaceholder.typicode.com/users"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)
    logger.info("Extracted users data from API")
    return df

@task
def transform(
    df,
    drop_columns=None,
    rename_columns=None,
    filter_conditions=None,
    type_conversions=None,
    enrich_function=None
):
    logger = get_run_logger()
    logger.info("Starting data transformation")
    
    # Make a copy to avoid modifying the original
    df_transformed = df.copy()
    
    # Convert dictionary columns to JSON strings to avoid PostgreSQL adaptation errors
    import json
    for column in df_transformed.columns:
        if df_transformed[column].dtype == 'object':
            # Check if any values in this column are dictionaries
            sample_value = df_transformed[column].dropna().iloc[0] if not df_transformed[column].dropna().empty else None
            if isinstance(sample_value, dict):
                logger.info(f"Converting dictionary column '{column}' to JSON string")
                df_transformed[column] = df_transformed[column].apply(
                    lambda x: json.dumps(x) if isinstance(x, dict) else x
                )
    
    # Drop columns
    if drop_columns:
        existing_cols = [col for col in drop_columns if col in df_transformed.columns]
        if existing_cols:
            df_transformed = df_transformed.drop(columns=existing_cols)
            logger.info(f"Dropped columns: {existing_cols}")
    
    # Rename columns
    if rename_columns:
        valid_renames = {old: new for old, new in rename_columns.items() 
                        if old in df_transformed.columns}
        if valid_renames:
            df_transformed = df_transformed.rename(columns=valid_renames)
            logger.info(f"Renamed columns: {valid_renames}")
    
    # Apply filters
    if filter_conditions:
        for column, condition in filter_conditions.items():
            if column in df_transformed.columns:
                if isinstance(condition, (list, tuple)):
                    df_transformed = df_transformed[df_transformed[column].isin(condition)]
                    logger.info(f"Filtered {column} to values in {condition}")
                else:
                    df_transformed = df_transformed[df_transformed[column] == condition]
                    logger.info(f"Filtered {column} to value {condition}")
    
    if type_conversions:
        for column, dtype in type_conversions.items():
            if column in df_transformed.columns:
                try:
                    df_transformed[column] = df_transformed[column].astype(dtype)
                    logger.info(f"Converted {column} to {dtype}")
                except Exception as e:
                    logger.warning(f"Failed to convert {column} to {dtype}: {e}")
    
    if enrich_function:
        df_transformed = enrich_function(df_transformed)
        logger.info("Applied custom enrichment function")
    
    logger.info(f"Transformation complete. Result shape: {df_transformed.shape}")
    return df_transformed

@task
def load_to_postgres(df):
    logger = get_run_logger()
    logger.info("Loading data to Postgres")
    import os
    # Use environment variables or fallback values
    db_host = os.getenv("DBT_HOST", "ctm_db")
    db_user = os.getenv("DBT_USER", "postgres")  
    db_pass = os.getenv("DBT_PASS", "haptiq123#")
    db_name = os.getenv("DBT_DATABASE", "dbt_demo")
    
    connection_string = f"postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}"
    logger.info(f"Connecting to database at {db_host}")
    
    engine = create_engine(connection_string)
    df.to_sql("users_api", engine, if_exists="replace", index=False)
    logger.info(f"Loaded {len(df)} rows into table 'users_api'")
    logger.info("Loaded data to Postgres")

@flow
def main():
    logger = get_run_logger()
    logger.info("Starting flow")
    df = extract()
    df = transform(df, drop_columns=['address', 'company'])
    load_to_postgres(df)
    logger.info("Flow completed successfully")

@flow
def custom_transform_flow():
    logger = get_run_logger()
    logger.info("Starting custom transform flow")
    
    df = extract()
    
    df = transform(
        df,
        drop_columns=['address', 'company'],
        rename_columns={
            'name': 'full_name',
            'username': 'user_login',
            'email': 'email_address'
        },
        type_conversions={'id': 'str'}
    )
    
    load_to_postgres(df)
    logger.info("Custom transform flow completed successfully")

@flow
def filtered_transform_flow():
    logger = get_run_logger()
    logger.info("Starting filtered transform flow")
    
    df = extract()
    
    df = transform(
        df,
        drop_columns=['address', 'company', 'phone'],
        filter_conditions={'id': [1, 2, 3, 4, 5]}  # Only keep first 5 users
    )
    
    load_to_postgres(df)
    logger.info("Filtered transform flow completed successfully")

@flow
def enriched_transform_flow():
    logger = get_run_logger()
    logger.info("Starting enriched transform flow")
    
    df = extract()
    
    def add_domain_and_status(df):
        """Add email domain and active status columns"""
        df['email_domain'] = df['email'].str.split('@').str[1]
        df['status'] = 'active'
        df['full_name_upper'] = df['name'].str.upper()
        return df
    

    df = transform(
        df,
        drop_columns=['address', 'company'],
        rename_columns={'username': 'login'},
        enrich_function=add_domain_and_status
    )
    
    load_to_postgres(df)
    logger.info("Enriched transform flow completed successfully")

@flow
def minimal_transform_flow():
    logger = get_run_logger()
    logger.info("Starting minimal transform flow")
    
    df = extract()
    
    df = transform(
        df,
        rename_columns={
            'name': 'user_name',
            'email': 'contact_email'
        }
    )
    
    load_to_postgres(df)
    logger.info("Minimal transform flow completed successfully")

if __name__ == "__main__":   
    main()  # Basic flow - drops address and company
    
    # custom_transform_flow()  # Multiple transformations with renaming
    # filtered_transform_flow()  # Filter specific records
    # enriched_transform_flow()  # Add custom columns
    # minimal_transform_flow()  # Only rename columns