"""Setup script for Genonaut package."""

from setuptools import setup, find_packages

setup(
    name="genonaut",
    version="0.1.0",
    description="Genonaut - Recommender systems for generative AI",
    author="Genonaut Team",
    python_requires=">=3.11",
    packages=find_packages(exclude=["test", "test.*", "docs", "notes", "infra"]),
    install_requires=[
        # Core dependencies are in requirements.txt
        # This is intentionally minimal to avoid duplication
    ],
    entry_points={
        "console_scripts": [
            "genonaut=genonaut.cli_main:app",
        ],
    },
    include_package_data=True,
)
