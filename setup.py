from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="teif-converter",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="PDF to TEIF (Tunisian Electronic Invoice Format) converter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/teif-converter",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.7",
    install_requires=[
        "pdfplumber>=0.7.0",
        "PyPDF2>=2.0.0",
        "lxml>=4.6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "isort>=5.0",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "teif-converter=teif.cli.main:main",
        ],
    },
)
