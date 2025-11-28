from prefect import flow, task
from prefect.logging import get_run_logger
from prefect_dbt.cli.commands import DbtCoreOperation
import os


# Configuration constants
DBT_PROJECT_DIR = "/usr/app/dbt_demo"
DBT_PROFILES_DIR = "/usr/app/dbt_demo"
PROJECT_DIR = DBT_PROJECT_DIR
MODELS_DIR = os.path.join(DBT_PROJECT_DIR, "models")
SEEDS_DIR = os.path.join(DBT_PROJECT_DIR, "seeds")


@task
def discover_dbt_paths():
    logger = get_run_logger()
    models = []
    seeds = []

    if os.path.exists(MODELS_DIR):
        for name in os.listdir(MODELS_DIR):
            if name.endswith(".sql"):
                models.append(os.path.splitext(name)[0])
    
    if os.path.exists(SEEDS_DIR):
        for name in os.listdir(SEEDS_DIR):
            if name.endswith(".csv"):
                seeds.append(os.path.splitext(name)[0])
    
    logger.info(f"DBT Project Directory: {PROJECT_DIR}")
    logger.info(f"DBT Profiles Directory: {DBT_PROFILES_DIR}")
    logger.info(f"DBT Models Directory: {MODELS_DIR}")
    logger.info(f"DBT Seeds Directory: {SEEDS_DIR}")

    model_selection = " ".join(models) if models else "*"
    seed_selection = " ".join(seeds) if seeds else "*"

    logger.info(f"Discovered models: {model_selection}")
    logger.info(f"Discovered seeds: {seed_selection}")

    return model_selection, seed_selection


@task
def run_dbt_seed(full_refresh: bool = False, seed_name: str | None = None):
    logger = get_run_logger()
    
    # Build the command
    command = ["dbt", "seed"]
    
    if full_refresh:
        command.append("--full-refresh")
    
    if seed_name:
        command.extend(["--select", seed_name])
    
    logger.info(f"Running command: {' '.join(command)}")
    
    # Execute the command using DbtCoreOperation
    result = DbtCoreOperation(
        commands=[" ".join(command)],
        project_dir=DBT_PROJECT_DIR,
        profiles_dir=DBT_PROFILES_DIR
    ).run()
    
    logger.info("dbt seed completed successfully")
    return result


@task
def run_dbt_models(model_selection: str | None = None):

    logger = get_run_logger()
    
    # Build the command
    command = ["dbt", "run"]
    
    if model_selection and model_selection != "*":
        # Split by space to handle multiple models
        models = model_selection.split()
        command.extend(["--select"] + models)
    
    logger.info(f"Running command: {' '.join(command)}")
    
    # Execute the command using DbtCoreOperation
    result = DbtCoreOperation(
        commands=[" ".join(command)],
        project_dir=DBT_PROJECT_DIR,
        profiles_dir=DBT_PROFILES_DIR
    ).run()
    
    logger.info("dbt run completed successfully")
    return result


@task
def run_dbt_tests(model_selection: str | None = None):
    logger = get_run_logger()
    
    # Build the command
    command = ["dbt", "test"]
    
    # If model_selection is provided and not '*', add --select with models
    if model_selection and model_selection != "*":
        # Split by space to handle multiple models
        models = model_selection.split()
        command.extend(["--select"] + models)
    
    logger.info(f"Running command: {' '.join(command)}")
    
    # Execute the command using DbtCoreOperation
    try:
        result = DbtCoreOperation(
            commands=[" ".join(command)],
            project_dir=DBT_PROJECT_DIR,
            profiles_dir=DBT_PROFILES_DIR
        ).run()
        logger.info("dbt test completed successfully")
        return result
    except RuntimeError as e:
        logger.warning(f"Some dbt tests failed: {str(e)}")
        logger.info("Check the output above for test failure details")
        # Return a mock result indicating test failures but allow flow to continue
        return {"status": "failed_tests", "error": str(e)}


@flow(name="prefect_dbt_subflow_run", log_prints=True)
def prefect_dbt_subflow_run(model_selection: str | None = None, run_tests: bool = True):
    logger = get_run_logger()
    logger.info("Starting DBT models run subflow...")
    
    results = {}
    
    # Run dbt models
    results['models'] = run_dbt_models(model_selection)
    
    # Run tests if requested
    if run_tests:
        logger.info("Running DBT tests...")
        results['tests'] = run_dbt_tests(model_selection)
    else:
        logger.info("Skipping DBT tests (run_tests=False)")
    
    logger.info("DBT models run subflow completed!")
    return results


@flow(name="dbt_flow_run", log_prints=True)
def prefect_dbt_flow_run(
    run_tests: bool = True,
    full_refresh: bool = True,
    seed_name: str | None = None,
    model_selection: str | None = None,
    auto_discover: bool = True
):
    
    logger = get_run_logger()
    
    # Auto-discover models and seeds if enabled and no manual selections provided
    if auto_discover and not seed_name and not model_selection:
        logger.info("Auto-discovery enabled - discovering available models and seeds...")
        discovered_models, discovered_seeds = discover_dbt_paths()
        
        # Use discovered values if not manually specified
        if not model_selection:
            model_selection = discovered_models if discovered_models != "*" else None
        if not seed_name:
            seed_name = discovered_seeds if discovered_seeds != "*" else None
            
        logger.info(f"Auto-discovered model_selection: {model_selection}")
        logger.info(f"Auto-discovered seed_name: {seed_name}")
    
    logger.info("=" * 60)
    logger.info("Starting dbt Flow Run")
    logger.info("=" * 60)
    logger.info(f"Parameters:")
    logger.info(f"  - run_tests: {run_tests}")
    logger.info(f"  - full_refresh: {full_refresh}")
    logger.info(f"  - seed_name: {seed_name}")
    logger.info(f"  - model_selection: {model_selection}")
    logger.info(f"  - auto_discover: {auto_discover}")
    logger.info("=" * 60)
    
    results = {}
    
    # Step 1: Run dbt seed
    logger.info("Step 1: Running dbt seed...")
    results['seed'] = run_dbt_seed(full_refresh=full_refresh, seed_name=seed_name)
    
    # Step 2: Run dbt models
    logger.info("Step 2: Running dbt models...")
    results['run'] = run_dbt_models(model_selection=model_selection)
    
    # Step 3: Optionally run dbt tests
    if run_tests:
        logger.info("Step 3: Running dbt tests...")
        results['test'] = run_dbt_tests(model_selection=model_selection)
    else:
        logger.info("Step 3: Skipping dbt tests (run_tests=False)")
    
    logger.info("=" * 60)
    logger.info("dbt Flow Run completed successfully!")
    logger.info("=" * 60)
    
    return results


if __name__ == "__main__":
    prefect_dbt_flow_run()