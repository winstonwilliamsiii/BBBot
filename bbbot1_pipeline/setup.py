"""
BBBot1 Pipeline Package
Data pipeline and MLFlow tracking for Bentley Budget Bot
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bbbot1-pipeline",
    version="1.0.0",
    author="Winston Williams III",
    description="Data pipeline and MLFlow tracking for financial analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/winstonwilliamsiii/BBBot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        "bbbot1_pipeline": [
            "tickers_config.yaml",
            "config.env",
            "sql/*.sql",
        ],
    },
    entry_points={
        "console_scripts": [
            "bbbot1-mlflow-validate=bbbot1_pipeline.mlflow_config:validate_connection",
        ],
    },
)
