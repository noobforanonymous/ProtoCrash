from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="protocrash",
    version="1.0.0",
    author="Regaan",
    author_email="regaan48@gmail.com",
    description="Coverage-guided protocol fuzzer for vulnerability discovery",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/noobforanonymous/ProtoCrash",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.11",
    install_requires=[
        "click>=8.1.0",
        "rich>=13.0.0",
        "pwntools>=4.11.0",
        "scapy>=2.5.0",
        "pyshark>=0.6.0",
        "psutil>=5.9.0",
        "pyyaml>=6.0.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "ruff>=0.1.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "analysis": [
            "capstone>=5.0.0",
            "matplotlib>=3.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "protocrash=cli.main:cli",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/noobforanonymous/ProtoCrash/issues",
        "Source": "https://github.com/noobforanonymous/ProtoCrash",
        "Documentation": "https://protocrash.readthedocs.io",
    },
)
