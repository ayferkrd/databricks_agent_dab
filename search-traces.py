import time

# Search only the last hour of traces, so the query scans less data
one_hour_ago_ms = int(time.time() * 1000) - 60 * 60 * 1000

# Find error traces
error_traces = mlflow.search_traces(
    locations=[experiment_id],
    filter_string=f"trace.status = 'ERROR' AND trace.timestamp_ms > {one_hour_ago_ms}",
    max_results=100
)
print(f"Error traces found: {len(error_traces)}")

# Find slow traces (over 5 seconds)
slow_traces = mlflow.search_traces(
    locations=[experiment_id],
    filter_string=f"trace.execution_time_ms > 5000 AND trace.timestamp_ms > {one_hour_ago_ms}",
    max_results=100
)
print(f"Slow traces (>5s): {len(slow_traces)}")

# Find traces by a span attribute set in C1
version_traces = mlflow.search_traces(
    locations=[experiment_id],
    filter_string=f"span.attributes.app_version = '1.2.0' AND trace.timestamp_ms > {one_hour_ago_ms}",
    max_results=100
)
print(f"Traces from app version 1.2.0: {len(version_traces)}")