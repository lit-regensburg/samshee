import setuptools

with open("README.md", "r") as fh:
    description = fh.read()

setuptools.setup(
    name="ilsa2",
    version="0.0.5",
    author="Jakob Simeth",
    author_email="jakob.simeth@ukr.de",
    packages=["ilsa2"],
    description="A schema-agnostic parser for illumina sample sheets v2.",
    long_description=description,
    long_description_content_type="text/markdown",
    url="https://git.uni-regensburg.de/rci_ngscore/ilsa2",
    license="MIT",
    python_requires=">=3.8",
    install_requires=["jsonschema"],
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Development Status :: 2 - Pre-Alpha",
    ]
)
