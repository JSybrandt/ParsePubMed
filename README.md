# ParsePubMed

A script that parses the pubmed xml release for use in python.

## Install

```
pip install git+https://github.com/JSybrandt/ParsePubMed
```

## Get PubMed Data

The following bash command creates a set of directories,
`ftp.ncbi.nlm.gov/pubmed/baseline` containing many `.xml.gz` files.

```
wget -r ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/
```

## Run the Script

This package will convert each `.xml.gz` file into a pickle. Each pickle
contains a list of dictionaries, corresponding to cache pubmed record in the
corresponding xml file.

```
python3 -m parse_pubmed <path to .xml.gz directory> <path to output pickle dir>
```

Here's a real example:

```
wget -r ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/
python3 -m parse_pubmed \
  ./ftp.ncbi.nlm.nih.gov/pubmed/baseline \
  ./parsed_pubmed_records
```
