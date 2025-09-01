from setuptools import setup, find_packages

setup(
    name="symphony-integrations",
    version="0.1.0",
    description="Symphony Integrations - External tool integrations for Linear, GitHub, Slack, etc.",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "symphony-core",
        "aiohttp>=3.8.0",
        "requests>=2.28.0",
        "slack-sdk>=3.19.0",
        "PyGithub>=1.57.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "responses>=0.22.0",  # for mocking HTTP requests
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
