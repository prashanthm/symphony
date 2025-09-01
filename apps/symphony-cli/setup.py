from setuptools import setup, find_packages

setup(
    name="symphony-cli",
    version="0.1.0",
    description="Symphony CLI - Command line interface for Symphony platform",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "symphony-core",
        "symphony-integrations", 
        "symphony-templates",
        "click>=8.0.0",
        "rich>=12.0.0",  # for beautiful CLI output
        "typer>=0.7.0",  # modern CLI framework
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-click>=1.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "symphony=symphony_cli.main:cli",
        ],
    },
    python_requires=">=3.9",
    author="Symphony Team",
    author_email="team@symphony.ai",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)