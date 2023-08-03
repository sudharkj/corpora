import os
import shutil
import sys
from pathlib import Path

from langdetect import detect

from Bio import Entrez

Entrez.email = "EMAIL"


# pubmed

def get_set_articles(records):
    return records["PubmedArticle"]


def get_pmid(record):
    return record["MedlineCitation"]["PMID"]


def get_abstract_text(record):
    all_abstracttexts = []
    try:
        texts = []
        texts.append(record["MedlineCitation"]["Article"]['Abstract']['AbstractText'])
        if 'OtherAbstract' in record["MedlineCitation"]:
            for item in record["MedlineCitation"]['OtherAbstract']:
                texts.append(item['AbstractText'])
        abstracttext = ""
        for text in texts:
            if len(text) > 1:
                abstracttext = ""
                for part in text:
                    if len(part.attributes) > 0:
                        label = part.attributes['Label']
                    else:
                        label = 'None'
                    part = part.replace('"', "'")
                    abstracttext += part + " "
            else:
                abstracttext = text[0]
                abstracttext = abstracttext.replace('"', "'")
            all_abstracttexts.append(abstracttext.strip())
    except:
        print('PMID ' + get_pmid(record) + ' - abstract not found!')
    return all_abstracttexts


def build_article(record):
    articles = []
    langs = []
    all_abstracttexts = get_abstract_text(record)
    for index in range(0, len(all_abstracttexts)):
        article = {}
        article["pmid"] = get_pmid(record)
        article["abstracttext"] = all_abstracttexts[index]
        # lang
        lang = detect(article["abstracttext"])
        article["lang"] = lang
        langs.append(lang)
        articles.append(article)
    return articles, langs


# fetch

def fetch_pubmed_articles(ids):
    ids = ",".join(ids)
    handle = Entrez.efetch(db="pubmed", id=ids, retmode="xml")
    records = Entrez.read(handle)
    # print(records)
    set_articles = []
    set_langs = []
    for record in get_set_articles(records):
        # print(record)
        article, langs = build_article(record)
        set_articles.append(article)
        set_langs.append(langs)
    handle.close()
    # print(len(articles))
    return set_articles, set_langs


def fetch_multiple_articles(pmids, out_dir, lang1, lang2, suffix):
    suffix = str(suffix)
    print(pmids)
    set_articles, set_langs = fetch_pubmed_articles(pmids)
    for index in range(0, len(set_articles)):
        langs = set_langs[index]
        # print(langs)
        if len(langs) < 2 or lang1 not in langs or lang2 not in langs:
            continue
        article = set_articles[index]
        for item in article:
            lang = detect(item["abstracttext"])
            if lang != lang1 and lang != lang2:
                continue
            print(item["pmid"] + "_" + item["lang"])
            # print(item["abstracttext"])
            # print(item["lang"])
            with open(os.path.join(out_dir, item["lang"] + "_" + suffix + ".txt"), "a") as writer:
                abstracttext = item["abstracttext"].replace("\n", " ")
                writer.write(abstracttext + "\n")
            writer.close()


map_langs = {
    "eng": "en",
    "ita": "it",
    "chi": "zh-cn",
    "fre": "fr",
    "ger": "de",
    "por": "pt",
    "spa": "es",
    "rus": "ru"
}


def get_lang1_lang2(filename):
    lang1, lang2 = filename[0:7].split("_")
    lang1 = map_langs[lang1]
    lang2 = map_langs[lang2]
    return lang1, lang2


def retrieve_abstracts(filename, out_dir):
    lang1, lang2 = get_lang1_lang2(filename)
    pmids_total = 0
    pmids = []
    with open(os.path.join(filename), "r") as reader:
        lines = reader.readlines()
        for line in lines:
            pmid = line.strip()
            pmids.append(pmid)
            if len(pmids) < 100:
                continue
            # fetch
            pmids_total += len(pmids)
            fetch_multiple_articles(pmids, out_dir, lang1, lang2, pmids_total // 100)
            pmids = []
    if len(pmids) > 0:
        pmids_total += len(pmids)
        fetch_multiple_articles(pmids, out_dir, lang1, lang2, (pmids_total // 100) + 1)


if __name__ == '__main__':
    """
    Steps to download data:
    1. Clone the repo.
    2. Extract trainWmt22.zip so that the files are in this folder or change the language extraction logic to match the folder structure.
    3. Rename the extracted files to remove train22_ from them or change the language extraction logic to match the file names.
    4. Run this file.
    """
    data_filenames = [
        "eng_fre"
    ]
    output_dir = "data/raw"
    for data_filename in data_filenames:
        output_dir_name = f"{output_dir}/{data_filename}"
        shutil.rmtree(output_dir_name, ignore_errors=True)
        path = Path(output_dir_name)
        path.mkdir(parents=True, exist_ok=True)
        retrieve_abstracts(f"{data_filename}.txt", output_dir_name)
