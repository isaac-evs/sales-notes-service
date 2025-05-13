# app/middleware/metrics.py for Sales Notes Service
import os
import time
import boto3
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import logging

# Configure logger
logger = logging.getLogger("sales_notes_service")

class CloudWatchMetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.service_name = "sales-notes-service"

        # Initialize CloudWatch client only in production environment
        if self.environment == "production":
            self.cloudwatch = boto3.client('cloudwatch',
                region_name=os.getenv("AWS_REGION"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
        else:
            self.cloudwatch = None
            logger.info("Running in development mode. CloudWatch metrics disabled.")

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Extract path and method for metric dimensions
        path = request.url.path
        method = request.method

        try:
            # Process the request and get response
            response = await call_next(request)

            # Record request success
            self.record_health_metric(path, method, 1)  # 1 indicates success

            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            # Record execution time metric
            self.record_performance_metric(path, method, execution_time)

            return response

        except Exception as e:
            # Record request failure
            self.record_health_metric(path, method, 0)  # 0 indicates failure

            # Calculate execution time even for failed requests
            execution_time = (time.time() - start_time) * 1000

            # Record execution time metric
            self.record_performance_metric(path, method, execution_time)

            # Log the error
            logger.error(f"Error processing request: {str(e)}")

            # Return error response
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"}
            )

    def record_health_metric(self, path, method, success):
        metric_name = "HealthCheck"

        # Log metric for development environment
        if self.environment != "production":
            logger.info(f"[DEV] {metric_name}: Path={path}, Method={method}, Success={success}")
            return

        # In production, send to CloudWatch
        try:
            self.cloudwatch.put_metric_data(
                Namespace=f"{self.service_name}/{self.environment}",
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Dimensions': [
                            {'Name': 'Path', 'Value': path},
                            {'Name': 'Method', 'Value': method},
                            {'Name': 'Environment', 'Value': self.environment}
                        ],
                        'Value': success,
                        'Unit': 'Count'
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to publish health metric to CloudWatch: {str(e)}")

    def record_performance_metric(self, path, method, execution_time):
        metric_name = "ExecutionTime"

        # Log metric for development environment
        if self.environment != "production":
            logger.info(f"[DEV] {metric_name}: Path={path}, Method={method}, Time={execution_time}ms")
            return

        # In production, send to CloudWatch
        try:
            self.cloudwatch.put_metric_data(
                Namespace=f"{self.service_name}/{self.environment}",
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Dimensions': [
                            {'Name': 'Path', 'Value': path},
                            {'Name': 'Method', 'Value': method},
                            {'Name': 'Environment', 'Value': self.environment}
                        ],
                        'Value': execution_time,
                        'Unit': 'Milliseconds'
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to publish performance metric to CloudWatch: {str(e)}")
