import json
import os
import re
from datetime import date
from rdflib import Graph, Literal, Namespace, RDF, RDFS, XSD, URIRef
from rdflib.namespace import DCTERMS

LT = Namespace("http://kcl.ac.uk/ontology/london-transport#")
PROV = Namespace("http://www.w3.org/ns/prov#")

#map common predicate strings from LLM output → ontology properties
#extend this with predicates the LLM produces
PREDICATE_MAP = {
    "acceptedon":          LT.acceptedOn,
    "operatedby":          LT.operatedBy,
    "serves":              LT.serves,
    "contains":            LT.contains,
    "haszones":            LT.inFareZone,
    "connectsto":          LT.connectsTo,
    "isterminus":          LT.isTerminus,
    "hasoperator":         LT.operatedBy,
    "partof":              LT.partOf,
    "locatedin":           LT.locatedIn,
    "opened":              LT.openedDate,
    "operatesnightservice": LT.operatesNightService,
    "introducedby":        LT.introducedBy,
    "replacedby":          LT.replacedBy,
    "costs":               LT.hasFareCost,
}


def slugify(text: str) -> str:
    """Convert a label like 'Victoria line' → 'Victoria_line' for use in URIs."""
    text = text.strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text


def label_to_uri(label: str) -> URIRef:
    """Best-effort conversion of an extracted label to a URI in the LT namespace."""
    return LT[slugify(label)]


def map_predicate(raw: str) -> URIRef:
    """Map a raw predicate string to an ontology property URI."""
    key = raw.lower().replace(" ", "").replace("_", "")
    return PREDICATE_MAP.get(key, LT[slugify(raw)])


def build_wiki_graph(all_results: list[dict]) -> Graph:
    g = Graph()
    g.bind("lt", LT)
    g.bind("dcterms", DCTERMS)
    g.bind("prov", PROV)
    g.bind("rdfs", RDFS)

    for article in all_results:
        source_url = f"https://en.wikipedia.org/wiki/{article['title'].replace(' ', '_')}"
        source_uri = URIRef(source_url)

        for triple in article["triples"]:
            subj_uri = label_to_uri(triple["subject"])
            pred_uri = map_predicate(triple["predicate"])
            obj_label = triple["object"]

            #adds readable label
            g.add((subj_uri, RDFS.label, Literal(triple["subject"])))

            #try to make the object a URI if it looks like a named entity,
            #otherwise fall back to a plain literal
            if len(obj_label.split()) <= 5 and not any(
                c.isdigit() for c in obj_label
            ):
                obj_node = label_to_uri(obj_label)
                g.add((obj_node, RDFS.label, Literal(obj_label)))
            else:
                obj_node = Literal(obj_label)

            g.add((subj_uri, pred_uri, obj_node))

            #record which wiki article this triple came from
            g.add((subj_uri, DCTERMS.source, source_uri))

    return g


def run(repo_root: str = ".") -> None:
    today = str(date.today())
    triples_path = os.path.join(
        repo_root, "downloads", "processed", today, "wiki_triples.json"
    )

    if not os.path.exists(triples_path):
        print(f"wiki_triples.json not found at {triples_path}")
        print("Run nlp_pipeline.py first")
        return

    with open(triples_path, encoding="utf-8") as f:
        all_results = json.load(f)

    print(f"Building RDF graph from {len(all_results)} articles...")
    g = build_wiki_graph(all_results)

    out_path = os.path.join(repo_root, "ontologies", "london-transport-wiki.ttl")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    g.serialize(out_path, format="turtle")

    print(f"Serialised {len(g)} triples → {out_path}")


if __name__ == "__main__":
    run()