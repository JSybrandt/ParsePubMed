import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="parse_pubmed",
    version="2020.04.02dev3",
    author="Justin Sybrandt",
    author_email="justin@sybrandt.com",
    description="Parses the XML distribution of PubMed into pickles",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JSybrandt/ParsePubMed",
    packages=["parse_pubmed"],
    install_requires=[
      "fire",
      "lxml",
      "tqdm",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
