import json
import os
import re
from datetime import date
from rdflib import Graph, Literal, Namespace, RDF, RDFS, XSD, URIRef
from rdflib.namespace import DCTERMS

TFL = Namespace("http://example.org/tfl#")
PROV = Namespace("http://www.w3.org/ns/prov#")

#map common predicate strings from LLM output → ontology properties
#using output of this script (unmapped preds are printed) and an LLM i made this map
PREDICATE_MAP = {
    #hasStop
    "operatesthrough":     TFL.hasStop,
    "operatesvia":         TFL.hasStop,
    "hasstop":             TFL.hasStop,
    "stopsat":             TFL.hasStop,
    "passesthrough":       TFL.hasStop,
    "passesby":            TFL.hasStop,
    "goesthrough":         TFL.hasStop,
    "servesstation":       TFL.hasStop,
    "hasroutevia":         TFL.hasStop,
    "hasstation":          TFL.hasStop,
    "travelsthrough":      TFL.hasStop,
    "operatesbetween":     TFL.hasStop,
    "goesto":              TFL.hasStop,
    "operatesto":          TFL.hasStop,
    "operatesfrom":        TFL.hasStop,
    "extendsto":           TFL.hasStop,
    "extendedto":          TFL.hasStop,
    "extendedtoserve":     TFL.hasStop,
    "servesarea":          TFL.hasStop,
    "serveshospital":      TFL.hasStop,
    "hasimprovedaccessat": TFL.hasStop,
    "hasstopon":           TFL.hasStop,

    #hasTerminus
    "startsat":            TFL.hasTerminus,
    "endsat":              TFL.hasTerminus,
    "terminatesat":        TFL.hasTerminus,
    "isterminus":          TFL.hasTerminus,
    "startsatstation":     TFL.hasTerminus,
    "endsatstation":       TFL.hasTerminus,
    "terminatesatoriginally": TFL.hasTerminus,
    "terminatesatcurrently": TFL.hasTerminus,

    #operatedBy
    "operatedby":          TFL.operatedBy,
    "hasoperator":         TFL.operatedBy,
    "providedby":          TFL.operatedBy,
    "isoperatedby":        TFL.operatedBy,
    "managedby":           TFL.operatedBy,
    "controlledby":        TFL.operatedBy,
    "ownedby":             TFL.operatedBy,
    "issuedby":            TFL.operatedBy,
    "operatedbyinitially": TFL.operatedBy,
    "operatedbyfrom2007":  TFL.operatedBy,
    "operatedbybefore2009": TFL.operatedBy,
    "operatedbyafter2009": TFL.operatedBy,
    "operatedbyaftere-tendering": TFL.operatedBy,
    "operatedbyfrom1997-04-19": TFL.operatedBy,
    "operatedbyafter2005": TFL.operatedBy,
    "operatedbyafterresume": TFL.operatedBy,
    "initiallyoperatedby": TFL.operatedBy,
    "operatedbyassumingitresumedoperationbythesamecompany": TFL.operatedBy,
    "commissionedby":      TFL.operatedBy,
    "foundedby":           TFL.operatedBy,
    "subsidizedby":        TFL.operatedBy,

    #connectsTo
    "connectsto":          TFL.connectsTo,
    "connectedtoviaroute": TFL.connectsTo,
    "connectswith":        TFL.connectsTo,
    "connectedby":         TFL.connectsTo,
    "connectedviaroute":   TFL.connectsTo,
    "connectswithoutside": TFL.connectsTo,

    #inFareZone
    "haszones":            TFL.inFareZone,
    "includeszone":        TFL.inFareZone,
    "operatesinzone":      TFL.inFareZone,
    "applicableforzones":  TFL.inFareZone,

    #isServedBy
    "servedby":            TFL.isServedBy,
    "servedbyroute":       TFL.isServedBy,
    "servedbyline":        TFL.isServedBy,

    #isNightService
    "operatesnightservice": TFL.isNightService,
    "isnighttube":         TFL.isNightService,
    "operatesnightserviceon": TFL.isNightService,

    #isStepFree
    "hasstepfreeaccess":   TFL.isStepFree,
    "madestepfree":        TFL.isStepFree,
    "willgainstepfreeaccess": TFL.isStepFree,
    "hasstepfreeaccesstoallplatformsatcostof": TFL.isStepFree,

    #hasAccessibilityFeature
    "hasaccessibilityfeature": TFL.hasAccessibilityFeature,
    "offersfeature":       TFL.hasAccessibilityFeature,
    "hasfeature":          TFL.hasAccessibilityFeature,
    "includesfeature":     TFL.hasAccessibilityFeature,
    "includedfeature":     TFL.hasAccessibilityFeature,
    "includesaccessfeature": TFL.hasAccessibilityFeature,
    "equippedwith":        TFL.hasAccessibilityFeature,
    "addedlifts":          TFL.hasAccessibilityFeature,
    "containslifts":       TFL.hasAccessibilityFeature,
    "providesaccessfor":   TFL.hasAccessibilityFeature,
    "providesaccessmethod": TFL.hasAccessibilityFeature,

    #fareAmount
    "costs":               TFL.fareAmount,
    "cost":                TFL.fareAmount,
    "costofconstruction":  TFL.fareAmount,
    "costofupgrade":       TFL.fareAmount,
    "amount":              TFL.fareAmount,
    "initialbudget":       TFL.fareAmount,

    #operatesOn / general operations
    "operateson":          TFL.operatesOn,
    "operates":            TFL.operatesOn,
    "operatesasauthority": TFL.operatesOn,
    "responsiblefor":      TFL.operatesOn,
    "manages":             TFL.operatesOn,
    "oversees":            TFL.operatesOn,
    "isresponsiblefor":    TFL.operatesOn,
    "owns":                TFL.operatesOn,

    #servesMode
    "servesmode":          TFL.servesMode,
    "type":                TFL.servesMode,
    "typeof":              TFL.servesMode,
    "linetype":            TFL.servesMode,

    #dates
    "opened":              TFL.openedDate,
    "openedin":            TFL.openedDate,
    "openeddate":          TFL.openedDate,
    "openedon":            TFL.openedDate,
    "introducedon":        TFL.openedDate,
    "introducedin":        TFL.openedDate,
    "introduced":          TFL.openedDate,
    "startedon":           TFL.openedDate,
    "startedin":           TFL.openedDate,
    "startedoperatingon":  TFL.openedDate,
    "startedoperatingin":  TFL.openedDate,
    "startedoperationon":  TFL.openedDate,
    "commencedon":         TFL.openedDate,
    "commencedoperatingon": TFL.openedDate,
    "establishedin":       TFL.openedDate,
    "launched":            TFL.openedDate,
    "formedinyear":        TFL.openedDate,
    "restartedoperatingon": TFL.openedDate,
    "suspendedon":         TFL.openedDate,
    "reopenedon":          TFL.openedDate,
    "endedon":             TFL.openedDate,
    "endedin":             TFL.openedDate,
    "extendedin":          TFL.openedDate,
    "startednightservice": TFL.openedDate,

    #acceptedOn (payment/ticketing)
    "acceptedon":          TFL.acceptedOn,
    "usedon":              TFL.acceptedOn,
    "validon":             TFL.acceptedOn,
    "acceptspaymentmethod": TFL.acceptedOn,
    "acceptspayment":      TFL.acceptedOn,
    "accepts":             TFL.acceptedOn,
    "acceptedby":          TFL.acceptedOn,
    "acceptspaymentby":    TFL.acceptedOn,
    "acceptedpaymentmethod": TFL.acceptedOn,
    "usedin":              TFL.acceptedOn,

    #misc
    "partof":              TFL.partOf,
    "ispartof":            TFL.partOf,
    "includedin":          TFL.partOf,
    "belongsto":           TFL.partOf,
    "locatedin":           TFL.locatedIn,
    "operatesin":          TFL.locatedIn,
    "locationof":          TFL.locatedIn,
    "locatedinarea":       TFL.locatedIn,
    "locatedat":           TFL.locatedIn,
    "contains":            TFL.contains,
    "includes":            TFL.contains,
    "includesline":        TFL.contains,
    "consistsof":          TFL.contains,
    "introducedby":        TFL.introducedBy,
    "replacedby":          TFL.replacedBy,
    "takenoverby":         TFL.replacedBy,
    "succeededby":         TFL.replacedBy,
    "alongroute":          TFL.onRoute,
    "onroute":             TFL.onRoute,
    "criticisedby":        TFL.criticisedBy,
    "criticisedtflfor":    TFL.criticisedBy,
    "criticizesdecision":  TFL.criticisedBy,
    "criticismtowardstfl": TFL.criticisedBy,
}

#frequently seen non london entities also used llm to help compile this list
NON_LONDON = {"milan", "almaty", "copenhagen", "dublin", "adelaide", "glasgow",
              "nuremberg", "cork", "zurich", "žilina", "prešov", "vancouver",
              "austin", "toronto", "dpmp", "dpmž", "palermo", "cairo", "athens",
              "helsinki", "stockholm", "sydney", "paris", "berlin", "madrid",
              "rome", "amsterdam", "brussels", "vienna", "prague", "budapest",
              "warsaw", "lisbon", "seoul", "tokyo", "beijing", "shanghai",
              "mumbai", "mexico", "bogota", "santiago", "lima", "buenos",
              "são", "rio", "cape", "johannesburg", "nitelink", "connexxion",
              "ret", "movia", "amat", "after_midnight", "blue_night",
              "metro_vancouver", "first_glasgow", "ontario"}

#types
LABEL_CLASS_MAP = {
    "ORG":     TFL.TransportOperator,
    "FAC":     TFL.TransitStop,
    "GPE":     TFL.Location,
    "LOC":     TFL.Location,
    "PRODUCT": TFL.TransportService,
    "EVENT":   TFL.TransportEvent,
}

#checks if mention of somewhere outside of london
def is_london_entity(text):
    t = text.lower()
    return not any(f" {kw} " in f" {t} " for kw in NON_LONDON)


#replaces " " with "_"
def slugify(text):
    text = text.strip()
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text

#wraps slugify and produces a uri within the namespace
def label_to_uri(label):
    return TFL[slugify(label)]

#takes predicateLikeThis from LLM and maps to uri in nameopsace
def map_predicate(raw):
    key = raw.lower().replace(" ", "").replace("_", "").replace("(", "").replace(")", "")
    return PREDICATE_MAP.get(key)


def build_wiki_graph(all_resuTFLs):
    g = Graph()
    g.bind("TFL", TFL)
    g.bind("dcterms", DCTERMS)
    g.bind("prov", PROV)
    g.bind("rdfs", RDFS)

    #pipeline provenance
    pipeline_uri = TFL["UnstructuredPipeline"]

    g.add((pipeline_uri, RDF.type, PROV.Activity))
    g.add((pipeline_uri, RDFS.label, Literal("LLM Wikipedia Extraction Pipeline")))

    #metrics
    valid = 0
    skipped = 0

    for article in all_resuTFLs:
        source_url = f"https://en.wikipedia.org/wiki/{article['title'].replace(' ', '_')}"
        source_uri = URIRef(source_url)
        
        #add rdf:type
        for ent in article.get("entities", []):

        
            if not is_london_entity(ent["text"]):
                continue

            cls = LABEL_CLASS_MAP.get(ent["label"])
            if cls:
                ent_uri = label_to_uri(ent["text"])
                g.add((ent_uri, RDF.type, cls))
                g.add((ent_uri, RDFS.label, Literal(ent["text"])))
        
        for triple in article["triples"]:

            subj_uri = label_to_uri(triple["subject"])
            pred_uri = map_predicate(triple["predicate"])

            if pred_uri is None:

                print("UNMAPPED:", triple["predicate"])
                skipped += 1
                continue  #discard preds with no match in map
            obj_label = triple["object"]

            #check for non london enitites
            if not is_london_entity(triple["subject"]):
                skipped += 1
                continue
            
            #check nothing over 40 characters
            if len(triple["subject"]) > 40 or len(triple["object"]) > 40:
                skipped += 1
                continue

            if not is_london_entity(obj_label):
                skipped += 1
                continue
            
            #adds date datatype
            if pred_uri == TFL.openedDate:
                try:
                    obj_node = Literal(obj_label, datatype=XSD.gYear)
                except:
                    obj_node = Literal(obj_label)
            elif len(obj_label.split()) <= 5 and not any(c.isdigit() for c in obj_label):
                obj_node = label_to_uri(obj_label)
                g.add((obj_node, RDFS.label, Literal(obj_label)))

            else:
                obj_node = Literal(obj_label)

            #adds readable rdfs:labels
            if (subj_uri, RDFS.label, Literal(triple["subject"])) not in g:
                g.add((subj_uri, RDFS.label, Literal(triple["subject"])))
            
            #another duplicate check
            if (subj_uri, pred_uri, obj_node) not in g:
                g.add((subj_uri, pred_uri, obj_node))
                g.add((subj_uri, PROV.wasGeneratedBy, pipeline_uri))
                valid += 1

            #add data provenance (wiki for all)
            g.add((subj_uri, DCTERMS.source, source_uri))

    print(f"Valid triples: {valid}, Skipped: {skipped}")       
    return g


def run():
    #finds most recent triples output
    processed_dir = os.path.join("downloads", "processed")
    latest = sorted(os.listdir(processed_dir))[-1]
    triples_path = os.path.join(processed_dir, latest, "wiki_triples.json")

    if not os.path.exists(triples_path):
        print(f"wiki_triples.json not found at {triples_path}")
        print("Run nlp_pipeline.py first")
        return

    with open(triples_path, encoding="utf-8") as f:
        all_resuTFLs = json.load(f)

    print(f"Building RDF graph from {len(all_resuTFLs)} articles...")
    g = build_wiki_graph(all_resuTFLs)

    out_path = os.path.join("ontologies", "pipeline_output", "unstructured_london_transport.ttl")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    g.serialize(out_path, format="turtle")
    
    print(f"Serialised {len(g)} triples → {out_path}")


if __name__ == "__main__":
    run()