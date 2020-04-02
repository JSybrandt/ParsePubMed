#!/usr/bin/env python3
from fire import Fire
import gzip
from lxml import etree
from pathlib import Path
import pickle
import re
from tqdm import tqdm
from typing import List, Dict, Any, Iterable

Record = Dict[str, Any]
XmlElement = etree._Element

def xml_obj_to_date(elem:XmlElement)->str:
  "Converts date XML element into formatted YYYY-MM-DD string"
  year_elem = elem.find("Year")
  month_elem = elem.find("Month")
  day_elem = elem.find("Day")
  year = int(year_elem.text) if year_elem is not None else 0
  month = int(month_elem.text) if month_elem is not None else 0
  day = int(day_elem.text) if day_elem is not None else 0
  return f"{year:04}-{month:02}-{day:02}"

def pubmed_xml_to_record(pubmed_elem:XmlElement)->Record:
  """
  Given a PubmedArticle element, parse out all the fields we care about.
  Fields are represented as a dictionary.
  """
  record = {
      "pmid": None,
      "version": None,
      "date": None,
      "language": None,
      "medline_status": None,
      "text_data": [],
      "publication_types": [],
      "mesh_headings": [],
      "data_banks": [],
      # Stores authors in order
      "authors": [],
  }

  medline_cite_elem = pubmed_elem.find("MedlineCitation")
  if medline_cite_elem is not None:
    record["medline_status"] = medline_cite_elem.attrib["Status"]

    pmid_elem = medline_cite_elem.find("PMID")
    if pmid_elem is not None:
      record["pmid"] = int(pmid_elem.text)
      record["version"] = int(pmid_elem.attrib["Version"])

    article_elem = medline_cite_elem.find("Article")
    if article_elem is not None:
      language_elem = article_elem.find("Language")
      if language_elem is not None:
        record["language"] = language_elem.text

      title_elem = article_elem.find("ArticleTitle")
      if title_elem is not None:
        record["text_data"].append({
          "text": "".join(title_elem.itertext()),
          "type": "title",
        })

      abstract_elem = article_elem.find("Abstract")
      if abstract_elem is not None:
        text_elems = abstract_elem.findall("AbstractText")
        if text_elems is not None:
          for abstract_text_elem in text_elems:
            if "NlmCategory" in abstract_text_elem.attrib:
              sub_type = abstract_text_elem.attrib["NlmCategory"].lower()
            else:
              sub_type = "raw"
            # Want to address weird whitespace characters
            text_data = "".join(abstract_text_elem.itertext())
            # replace all spaces with the typical space
            # This handles weird stuff, like newlines, tabs, and \u205f
            text_data = re.sub(r'\s', ' ', text_data)
            record["text_data"].append({
              "text": text_data,
              "type": f"abstract:{sub_type}"
            })

      # Author list appears right after abstract
      author_list_elem = article_elem.find("AuthorList")
      if author_list_elem is not None:
        author_elems = author_list_elem.findall("Author")
        if author_elems is not None:
          for author_elem in author_elems:
            author_name = ""
            initials_elem = author_elem.find("Initials")
            if initials_elem is not None:
              initials = "".join(initials_elem.itertext()).strip()
              author_name = f"{initials}. "
            last_name_elem = author_elem.find("LastName")
            if last_name_elem is not None:
              last_name = "".join(last_name_elem.itertext()).strip()
              author_name += last_name
              record["authors"].append(author_name)


      pub_type_list_elem = article_elem.find("PublicationTypeList")
      if pub_type_list_elem is not None:
        pub_type_elems = pub_type_list_elem.findall("PublicationType")
        if pub_type_elems is not None:
          for x in pub_type_elems:
            record["publication_types"].append("".join(x.itertext()))

      data_bank_list_elem = article_elem.find("DataBankList")
      if data_bank_list_elem is not None:
        data_bank_elems = data_bank_list_elem.findall("DataBank")
        if data_bank_elems is not None:
          for data_bank_elem in data_bank_elems:
            bank_name_elem = data_bank_elem.find("DataBankName")
            if bank_name_elem is not None:
              bank_name = "".join(bank_name_elem.itertext())
            else:
              bank_name = None
            num_list_elem = data_bank_elem.find("AccessionNumberList")
            if num_list_elem is not None:
              num_list_elems = num_list_elem.findall("AccessionNumber")
              if num_list_elems is not None:
                for num_elem in num_list_elems:
                  record["data_banks"].append({
                    "name": bank_name,
                    "id": "".join(num_elem.itertext())
                  })

    chemical_list_elem = medline_cite_elem.find("ChemicalList")
    if chemical_list_elem is not None:
      chemical_elems = chemical_list_elem.findall("Chemical")
      if chemical_elems is not None:
        for chem_elem in chemical_elems:
          name_elem = chem_elem.find("NameOfSubstance")
          if name_elem is not None:
            record["mesh_headings"].append(name_elem.attrib["UI"])

    mesh_heading_list_elem = medline_cite_elem.find("MeshHeadingList")
    if mesh_heading_list_elem is not None:
      mesh_heading_elems = mesh_heading_list_elem.find("MeshHeading")
      if mesh_heading_elems is not None:
        for mesh_elem in mesh_heading_elems:
          desc_elem = mesh_elem.find("DescriptorName")
          if desc_elem is not None:
            record["mesh_headings"].append(desc_elem.attrib["UI"])

  pubmed_data_elem = pubmed_elem.find("PubmedData")
  if pubmed_data_elem is not None:
    history_elem = pubmed_data_elem.find("History")
    if history_elem is not None:
      pm_date_elems = history_elem.findall("PubMedPubDate")
      if pm_date_elems is not None:
        for date_elem in pm_date_elems:
          date = xml_obj_to_date(date_elem)
          if date == "0000-00-00": continue
          if record["date"] is None or record["date"] > date:
            record["date"] = xml_obj_to_date(date_elem)

  return record

def parse_zipped_file(xml_path:Path)->Iterable[Record]:
  """
  Copies the given xml file to local scratch, and then gets the set of
  articles, represented by a list of dicts.
  """
  xml_path = Path(xml_path)
  assert xml_path.is_file(), \
      f"Cannot find {xml_path}"
  assert str(xml_path).endswith(".xml.gz"), \
      f"Path {xml_path} must end with .xml.gz"

  with gzip.open(str(xml_path), 'rb') as xml_file:
    # For each pubmed article in the xml file
    for _, elem in etree.iterparse(xml_file, tag="PubmedArticle"):
      yield pubmed_xml_to_record(elem)


def main(
    input_dir:Path="./",
    output_dir:Path="./parsed_xml",
):
  """
  Parses each .xml.gz file in input_dir to a separate pickle file.
  """
  # set types
  input_dir = Path(input_dir)
  output_dir = Path(output_dir)

  # look for xml files
  assert input_dir.is_dir(), \
      f"Failed to find {input_dir}. Either does not exist, or is not directory."
  xml_paths = list(input_dir.glob("*.xml.gz"))
  assert any(xml_paths), f"Failed to find any .xml.gz files in {input_dir}"

  # setup output dir
  output_dir.mkdir(exist_ok=True, parents=True)
  assert not any(output_dir.glob("*")), \
      f"Output dir: {output_dir} is not empty. Halting for safety."

  # Parse
  for xml_path in tqdm(xml_paths):
    name = xml_path.name.split(".", 1)[0]
    pickle_path = output_dir.joinpath(name + ".pickle")
    assert not pickle_path.exists(), \
        f"Output file, {pickle_path}, already exists. Halting."
    records = [r for r in tqdm(parse_zipped_file(xml_path))]
    with open(pickle_path, 'wb') as pickle_file:
      pickle.dump(records, pickle_file)

if __name__ == "__main__":
  Fire(main)

