from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rdl-mcp",
    version="0.1.0",
    author="Beth Maloney",
    author_email="",
    description="Edit SSRS reports using AI - MCP server for RDL files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bethmaloney/rdl-mcp",
    py_modules=["rdl_mcp_server"],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "defusedxml>=0.7.1",
        "fastmcp>=2.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "rdl-mcp=rdl_mcp_server:main",
        ],
    },
)
