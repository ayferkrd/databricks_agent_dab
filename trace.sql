display(spark.sql(f"""
    SELECT trace_metadata:['mlflow.trace.session']::STRING AS session_id,
           COUNT(*) AS turns,
           ROUND(AVG(execution_duration_ms)) AS avg_duration_ms
    FROM {catalog_name}.{schema_name}.prod_tracing_trace_unified
    WHERE trace_metadata:['mlflow.trace.session'] IS NOT NULL
    GROUP BY 1
"""))