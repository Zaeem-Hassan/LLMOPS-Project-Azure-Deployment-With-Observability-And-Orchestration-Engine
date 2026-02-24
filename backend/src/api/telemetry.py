import os
import logging
from azure.monitor.opentelemetry import configure_azure_monitor

logger = logging.getLogger("brand-guardian.telemetry")

def setup_telemetry():

    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connection_string:
        logger.warning("ApplicationInsights Connection String not found")
        return
    
    configure_azure_monitor(
        connection_string=connection_string,
        logger_name = "brand-guardian-tracer",
        enable_logging=True,
        enable_metrics=True,
        enable_traces=True
    )
    logger.info("Telemetry configured successfully")