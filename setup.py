from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="wcag-auditor",
    version="0.1.0",
    author="WCAG Auditor Contributors",
    description="CLI tool to audit websites for WCAG 2.2 compliance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/wcag-auditor",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "lxml>=4.9.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "urllib3>=1.26.0",
        "tqdm>=4.64.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "flake8>=5.0.0",
            "black>=22.0.0",
            "mypy>=0.990"
        ]
    },
    entry_points={
        "console_scripts": [
            "wcag-auditor=wcag_auditor.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
        "Topic :: Internet :: WWW/HTTP",
    ],
)