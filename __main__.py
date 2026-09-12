import pulumi
import pulumi_snowflake as snowflake

# 1. Create the Main Enterprise Database
lumina_db = snowflake.Database("lumina-insurance-db",
    name="LUMINA_PROD",
    comment="Main production database for Lumina Mutual Insurance."
)

# 2. Create the Bronze Layer Schema (For  OneLake Delta files)
raw_delta_schema = snowflake.Schema("raw-delta-schema",
    database=lumina_db.name,
    name="RAW_DELTA",
    comment="Bronze layer pointing to external OneLake Delta tables."
)

# 3. Create the Silver/Gold Layer Schema ( Star Schema)
core_star_schema = snowflake.Schema("core-star-schema",
    database=lumina_db.name,
    name="CORE_STAR",
    comment="Silver/Gold layer containing dimensional models and actuarial facts."
)

# 4. Create the Analytics Schema (For AI and Streamlit views)
analytics_schema = snowflake.Schema("analytics-schema",
    database=lumina_db.name,
    name="ANALYTICS",
    comment="Consumption layer for Cortex AI models and Streamlit Apps."
)

# 5. Create an Internal Stage to act as our Mock OneLake storage
mock_onelake_stage = snowflake.StageInternal("mock-onelake-stage",
    database=lumina_db.name,
    schema=raw_delta_schema.name,
    name="MOCK_ONELAKE_STAGE",
    comment="Internal stage simulating OneLake Delta storage."
)

# 6. Create the Claims Fact Table (Gold Layer)
fact_claim_table = snowflake.Table("fact-claim-table",
    database=lumina_db.name,
    schema=core_star_schema.name,
    name="FACT_CLAIM",
    comment="Central fact table for insurance claims.",
    columns=[
        # Surrogate Key (Auto-incrementing)
        snowflake.TableColumnArgs(
            name="CLAIM_KEY", 
            type="NUMBER(38,0)", 
            identity=snowflake.TableColumnIdentityArgs(
                start_num=1,
                step_num=1
            )
        ),
        # Business Columns
        snowflake.TableColumnArgs(name="CLAIM_ID", type="VARCHAR(50)"),
        snowflake.TableColumnArgs(name="POLICY_ID", type="VARCHAR(50)"),
        snowflake.TableColumnArgs(name="CLAIM_AMOUNT", type="NUMBER(14,2)"),
        snowflake.TableColumnArgs(name="STATUS", type="VARCHAR(20)"),
        # Evolved Schema Column
        snowflake.TableColumnArgs(name="RISK_SCORE", type="NUMBER(38,0)")
    ]
)

# 7. Define the Primary Key Constraint
fact_claim_pk = snowflake.TableConstraint("fact-claim-pk",
    name="PK_FACT_CLAIM",
    table_id=fact_claim_table.fully_qualified_name,
    type="PRIMARY KEY",
    columns=["CLAIM_KEY"]
)

# 8. Create the Analytics Summary View
claims_summary_view = snowflake.View("claims-summary-view",
    database=lumina_db.name,
    schema=analytics_schema.name,
    name="VW_CLAIMS_BY_STATUS",
    comment="Summary of claims aggregated by status.",
    statement="""
        SELECT 
            STATUS, 
            COUNT(CLAIM_KEY) AS TOTAL_CLAIMS, 
            SUM(CLAIM_AMOUNT) AS TOTAL_AMOUNT 
        FROM LUMINA_PROD.CORE_STAR.FACT_CLAIM 
        GROUP BY STATUS
    """
)

# 9. Create a dedicated Warehouse for automated tasks
dataops_warehouse = snowflake.Warehouse("dataops-warehouse",
    name="LUMINA_DATAOPS_WH",
    warehouse_size="X-SMALL",
    auto_suspend=60,
    auto_resume=True,
    comment="Dedicated compute for automated ingestion tasks."
)

# 10. Create the Automated Ingestion Task
ingestion_task = snowflake.Task("claims-ingestion-task",
    database=lumina_db.name,
    schema=core_star_schema.name,
    name="TASK_INGEST_CLAIMS",
    warehouse=dataops_warehouse.name,
    schedule=snowflake.TaskScheduleArgs(
        minutes=60
    ),
    sql_statement="""
        COPY INTO LUMINA_PROD.CORE_STAR.FACT_CLAIM (CLAIM_ID, POLICY_ID, CLAIM_AMOUNT, STATUS, RISK_SCORE) 
        FROM (
            SELECT $1:CLAIM_ID::STRING, $1:POLICY_ID::STRING, $1:CLAIM_AMOUNT::FLOAT, $1:STATUS::STRING, $1:RISK_SCORE::NUMBER 
            FROM @LUMINA_PROD.RAW_DELTA.MOCK_ONELAKE_STAGE/claims_delta/ 
            (FILE_FORMAT => 'LUMINA_PROD.RAW_DELTA.FORMAT_PARQUET', PATTERN => '.*parquet')
        )
    """,
    started=True
)

# 11. Create an Internal Stage for Streamlit code files
streamlit_stage = snowflake.StageInternal("streamlit-stage",
    database=lumina_db.name,
    schema=analytics_schema.name,
    name="STREAMLIT_STAGE",
    comment="Internal stage for holding Streamlit app files."
)

# 12. Deploy Streamlit App natively using the Stage and Query Warehouse
claims_dashboard = snowflake.Streamlit("claims-streamlit-app",
    database=lumina_db.name,
    schema=analytics_schema.name,
    name="STREAMLIT_CLAIMS_DASHBOARD",
    stage=streamlit_stage.fully_qualified_name,
    main_file="app.py",
    query_warehouse="COMPUTE_WH",
    comment="Interactive executive dashboard for claims analysis."
)
# Export the database name to the terminal upon completion
pulumi.export("database_name", lumina_db.name)