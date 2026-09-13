import snowflake.snowpark as snowpark
from snowflake.snowpark.session import Session
from snowflake.snowpark.functions import col, when
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

def main():
    # Connect to Snowflake using active session or default connection profile
    session = Session.builder.config("connection_name", "deploy_target").getOrCreate()

    # Explicitly set session context
    session.use_database("LUMINA_PROD")
    session.use_schema("ANALYTICS")
    session.use_warehouse("COMPUTE_WH")

    print("Loading claims data from Gold layer into local environment...")
    df = session.table("LUMINA_PROD.CORE_STAR.FACT_CLAIM")

    # Prepare target labels
    prepared_df = df.with_column(
        "IS_HIGH_RISK",
        when((col("CLAIM_AMOUNT") > 5000) | (col("STATUS") == "IN_REVIEW"), 1).otherwise(0)
    )
    
    # Pull to Pandas dataframe for training
    pdf = prepared_df.to_pandas()

    print(" Training native scikit-learn Random Forest Model...")
    feature_cols = ["CLAIM_AMOUNT", "RISK_SCORE"]
    
    # Handle potential null values
    pdf["CLAIM_AMOUNT"] = pdf["CLAIM_AMOUNT"].fillna(0)
    pdf["RISK_SCORE"] = pdf["RISK_SCORE"].fillna(0)

    X = pdf[feature_cols]
    y = pdf["IS_HIGH_RISK"]

    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X, y)

    print(" Model training complete. Generating risk predictions...")
    pdf["PREDICTED_RISK_LABEL"] = clf.predict(X)

    print(" Publishing predictions back to Snowflake analytics table...")
    output_df = session.create_dataframe(pdf[["CLAIM_ID", "POLICY_ID", "CLAIM_AMOUNT", "STATUS", "RISK_SCORE", "PREDICTED_RISK_LABEL"]])
    output_df.write.mode("overwrite").save_as_table("LUMINA_PROD.ANALYTICS.PREDICTED_CLAIMS_RISK")

    print(" Risk prediction table successfully published to LUMINA_PROD.ANALYTICS.PREDICTED_CLAIMS_RISK!")

if __name__ == "__main__":
    main()