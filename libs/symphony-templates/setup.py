from setuptools import find_packages, setup

setup(
    name="symphony-templates",
    version="0.1.0",
    description="Symphony Templates - Workspace and repository templates for Linear, GitHub, etc.",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "symphony_templates": [
            "templates/**/*.yaml",
            "templates/**/*.yml",
            "templates/**/*.json",
        ],
    },
    install_requires=[
        "symphony-core",
        "symphony-integrations",
        "jinja2>=3.1.0",  # for template rendering
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
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
