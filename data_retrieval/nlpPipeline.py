import json
import os
import re
import spacy
import requests
from datetime import date
from rdflib import Graph, URIRef, Literal, RDF, RDFS, Namespace
from rdflib.namespace import DCTERMS

#REQUIRED LLM API TO BE SET UP

#load spacy model from lab
nlp = spacy.load("en_core_web_sm")

LT = Namespace("http://kcl.ac.uk/ontology/london-transport#")

#relevant spacy entity types from lab task
RELEVANT_LABELS = {"ORG", "GPE", "LOC", "FAC", "PRODUCT", "EVENT"}

CHUNK_SIZE = 800

# Standardize how URIs are generated across both scripts
def get_uri(name):
    # Convert "Green Park" to "green_park" for consistency
    clean_name = name.strip().lower().replace(" ", "_")
    return URIRef(LT[clean_name])


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Split on paragraphs, accumulate until chunk_size — avoids cutting mid-sentence."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) > chunk_size and current:
            chunks.append(current.strip())
            current = para
        else:
            current += " " + para
    if current.strip():
        chunks.append(current.strip())
    return chunks


def extract_entities_spacy(text: str) -> list[dict]:
    """
    NER using spaCy en_core_web_sm as per Lab 7.
    Returns transport-relevant entities with their labels.
    """
    doc = nlp(text)
    return [
        {"text": ent.text, "label": ent.label_}
        for ent in doc.ents
        if ent.label_ in RELEVANT_LABELS
    ]


def entities_to_rdf(entities: list[dict], source_url: str, g: Graph) -> None:
    """
    Convert spaCy entities to RDF triples using ontology classes.
    Adds to the passed-in graph in place.
    """
    source_uri = URIRef(source_url)

    for ent in entities:
        entity_uri = get_uri(ent["text"])
        g.add((entity_uri, RDFS.label, Literal(ent["text"])))
        g.add((entity_uri, DCTERMS.source, source_uri))

        #class assignment logic
        text_lower = ent["text"].lower()
        if "line" in text_lower:
            g.add((entity_uri, RDF.type, LT.TfLLine))
            g.add((entity_uri, LT.lineName, Literal(ent["text"])))
        elif "station" in text_lower or ent["label"] == "FAC":
            g.add((entity_uri, RDF.type, LT.TransitStop))
            g.add((entity_uri, LT.stopName, Literal(ent["text"])))
        elif ent["label"] == "ORG":
            g.add((entity_uri, RDF.type, LT.TransportOperator))
            g.add((entity_uri, LT.operatorName, Literal(ent["text"])))
        elif ent["label"] in ("GPE", "LOC"):
            #locations
            g.add((entity_uri, RDF.type, LT.TransportLocation))
            g.add((entity_uri, RDFS.label, Literal(ent["text"])))


def extract_triples_llm(passage: str) -> list[dict]:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("OPENAI_API_KEY not set, skipping LLM extraction")
        return []

    prompt = f"""You are a knowledge engineer extracting RDF triples from London transport text.

                Extract factual triples about London transport services, stations, lines, fares, and operators.
                Return ONLY triples, one per line, in the format:
                subject | predicate | object

                Rules:
                - Only include facts directly stated in the text
                - Use short clean labels e.g. "Victoria line" not "the Victoria line"
                - Skip vague or opinion-based statements
                - Maximum 15 triples per passage

                Examples:
                Oyster card | acceptedOn | London Underground
                Elizabeth line | operatedBy | Transport for London
                Zone 1 | contains | King's Cross St. Pancras

                Text:
                {passage}

                Triples:"""

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",   # cheapest model
            "max_tokens": 1000,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        },
    )
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"]

    triples = []
    for line in raw.strip().splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 3 and all(parts):
            triples.append({
                "subject": parts[0],
                "predicate": parts[1],
                "object": parts[2],
            })
    return triples


def process_article(txt_path: str) -> dict:
    """Process one Wikipedia .txt file — runs both spaCy NER and LLM extraction."""
    with open(txt_path, encoding="utf-8") as f:
        text = f.read()

    title = os.path.basename(txt_path).replace(".txt", "").replace("_", " ")
    source_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
    print(f"\nProcessing: {title}")

    chunks = chunk_text(text)
    print(f"  {len(chunks)} chunks")

    all_entities, all_triples = [], []

    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}/{len(chunks)}...", end=" ", flush=True)
        entities = extract_entities_spacy(chunk)
        triples = extract_triples_llm(chunk)
        all_entities.extend(entities)
        all_triples.extend(triples)
        print(f"{len(entities)} entities, {len(triples)} triples")

    #remove duplicate triples
    seen = set()
    unique_triples = []
    for t in all_triples:
        key = (t["subject"], t["predicate"], t["object"])
        if key not in seen:
            seen.add(key)
            unique_triples.append(t)

    print(f"  Total: {len(all_entities)} entities, {len(unique_triples)} unique triples")
    return {
        "title": title,
        "source_url": source_url,
        "source_file": txt_path,
        "entities": all_entities,
        "triples": unique_triples,
    }


def run(repo_root: str = ".") -> None:
    today = str(date.today())
    wiki_dir = os.path.join(repo_root, "downloads", "raw", today, "wikipedia")
    out_dir = os.path.join(repo_root, "downloads", "processed", today)
    os.makedirs(out_dir, exist_ok=True)

    txt_files = [
        os.path.join(wiki_dir, f)
        for f in os.listdir(wiki_dir)
        if f.endswith(".txt")
    ]

    if not txt_files:
        print(f"No .txt files found in {wiki_dir}")
        print("Run wiki_scraper.py first")
        return

    all_results = []
    for txt_path in sorted(txt_files):
        result = process_article(txt_path)
        all_results.append(result)

    #save JSON for wiki_to_rdf.py
    out_path = os.path.join(out_dir, "wiki_triples.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    total = sum(len(r["triples"]) for r in all_results)
    print(f"\nExtracted {total} triples across {len(all_results)} articles")
    print(f"Saved → {out_path}")


if __name__ == "__main__":
    run()