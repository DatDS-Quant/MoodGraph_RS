"""
Shared pytest fixtures for Task 3A tests.
Provides a single session-scoped SparkSession to prevent Py4J gateway connection teardown issues
when running multiple test suites in a single pytest process.
"""

import os
import sys
import pytest
from pyspark.sql import SparkSession

# Windows Hadoop configuration
os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable


@pytest.fixture(scope="session")
def spark_session() -> SparkSession:
    """Session-scoped SparkSession shared across all Task 3A tests with increased stack size for iterative ALS."""
    spark = (
        SparkSession.builder.appName("MoodGraph_Task3A_Shared_Tests")
        .master("local[2]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.extraJavaOptions", "-Xss4m")
        .config("spark.executor.extraJavaOptions", "-Xss4m")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.memory", "1g")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    yield spark
    spark.stop()

