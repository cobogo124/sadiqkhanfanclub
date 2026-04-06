import json
import os
import re
from datetime import date
from rdflib import Graph, Literal, Namespace, RDF, RDFS, XSD, URIRef
from rdflib.namespace import DCTERMS

LT = Namespace("http://kcl.ac.uk/ontology/london-transport#")
PROV = Namespace("http://www.w3.org/ns/prov#")

#map common predicate strings from LLM output → ontology properties
#using output of this script (unmapped preds are printed) and an LLM i made this map
PREDICATE_MAP = {
    #hasStop
    "operatesthrough":     LT.hasStop,
    "operatesvia":         LT.hasStop,
    "hasstop":             LT.hasStop,
    "stopsat":             LT.hasStop,
    "passesthrough":       LT.hasStop,
    "passesby":            LT.hasStop,
    "goesthrough":         LT.hasStop,
    "servesstation":       LT.hasStop,
    "hasroutevia":         LT.hasStop,
    "hasstation":          LT.hasStop,
    "travelsthrough":      LT.hasStop,
    "operatesbetween":     LT.hasStop,
    "goesto":              LT.hasStop,
    "operatesto":          LT.hasStop,
    "operatesfrom":        LT.hasStop,
    "extendsto":           LT.hasStop,
    "extendedto":          LT.hasStop,
    "extendedtoserve":     LT.hasStop,
    "servesarea":          LT.hasStop,
    "serveshospital":      LT.hasStop,
    "hasimprovedaccessat": LT.hasStop,
    "hasstopon":           LT.hasStop,

    #hasTerminus
    "startsat":            LT.hasTerminus,
    "endsat":              LT.hasTerminus,
    "terminatesat":        LT.hasTerminus,
    "isterminus":          LT.hasTerminus,
    "startsatstation":     LT.hasTerminus,
    "endsatstation":       LT.hasTerminus,
    "terminatesatoriginally": LT.hasTerminus,
    "terminatesatcurrently": LT.hasTerminus,

    #operatedBy
    "operatedby":          LT.operatedBy,
    "hasoperator":         LT.operatedBy,
    "providedby":          LT.operatedBy,
    "isoperatedby":        LT.operatedBy,
    "managedby":           LT.operatedBy,
    "controlledby":        LT.operatedBy,
    "ownedby":             LT.operatedBy,
    "issuedby":            LT.operatedBy,
    "operatedbyinitially": LT.operatedBy,
    "operatedbyfrom2007":  LT.operatedBy,
    "operatedbybefore2009": LT.operatedBy,
    "operatedbyafter2009": LT.operatedBy,
    "operatedbyaftere-tendering": LT.operatedBy,
    "operatedbyfrom1997-04-19": LT.operatedBy,
    "operatedbyafter2005": LT.operatedBy,
    "operatedbyafterresume": LT.operatedBy,
    "initiallyoperatedby": LT.operatedBy,
    "operatedbyassumingitresumedoperationbythesamecompany": LT.operatedBy,
    "commissionedby":      LT.operatedBy,
    "foundedby":           LT.operatedBy,
    "subsidizedby":        LT.operatedBy,

    #connectsTo
    "connectsto":          LT.connectsTo,
    "connectedtoviaroute": LT.connectsTo,
    "connectswith":        LT.connectsTo,
    "connectedby":         LT.connectsTo,
    "connectedviaroute":   LT.connectsTo,
    "connectswithoutside": LT.connectsTo,

    #inFareZone
    "haszones":            LT.inFareZone,
    "includeszone":        LT.inFareZone,
    "operatesinzone":      LT.inFareZone,
    "applicableforzones":  LT.inFareZone,

    #isServedBy
    "servedby":            LT.isServedBy,
    "servedbyroute":       LT.isServedBy,
    "servedbyline":        LT.isServedBy,

    #isNightService
    "operatesnightservice": LT.isNightService,
    "isnighttube":         LT.isNightService,
    "startednightservice": LT.isNightService,
    "operatesnightserviceon": LT.isNightService,

    #isStepFree
    "hasstepfreeaccess":   LT.isStepFree,
    "madestepfree":        LT.isStepFree,
    "willgainstepfreeaccess": LT.isStepFree,
    "hasstepfreeaccesstoallplatformsatcostof": LT.isStepFree,

    #hasAccessibilityFeature
    "hasaccessibilityfeature": LT.hasAccessibilityFeature,
    "offersfeature":       LT.hasAccessibilityFeature,
    "hasfeature":          LT.hasAccessibilityFeature,
    "includesfeature":     LT.hasAccessibilityFeature,
    "includedfeature":     LT.hasAccessibilityFeature,
    "includesaccessfeature": LT.hasAccessibilityFeature,
    "equippedwith":        LT.hasAccessibilityFeature,
    "addedlifts":          LT.hasAccessibilityFeature,
    "containslifts":       LT.hasAccessibilityFeature,
    "providesaccessfor":   LT.hasAccessibilityFeature,
    "providesaccessmethod": LT.hasAccessibilityFeature,

    #fareAmount
    "costs":               LT.fareAmount,
    "cost":                LT.fareAmount,
    "costofconstruction":  LT.fareAmount,
    "costofupgrade":       LT.fareAmount,
    "amount":              LT.fareAmount,
    "initialbudget":       LT.fareAmount,

    #operatesOn / general operations
    "operateson":          LT.operatesOn,
    "operates":            LT.operatesOn,
    "operatesasauthority": LT.operatesOn,
    "responsiblefor":      LT.operatesOn,
    "manages":             LT.operatesOn,
    "oversees":            LT.operatesOn,
    "isresponsiblefor":    LT.operatesOn,
    "owns":                LT.operatesOn,

    #servesMode
    "servesmode":          LT.servesMode,
    "type":                LT.servesMode,
    "typeof":              LT.servesMode,
    "linetype":            LT.servesMode,

    #dates
    "opened":              LT.openedDate,
    "openedin":            LT.openedDate,
    "openeddate":          LT.openedDate,
    "openedon":            LT.openedDate,
    "introducedon":        LT.openedDate,
    "introducedin":        LT.openedDate,
    "introduced":          LT.openedDate,
    "startedon":           LT.openedDate,
    "startedin":           LT.openedDate,
    "startedoperatingon":  LT.openedDate,
    "startedoperatingin":  LT.openedDate,
    "startedoperationon":  LT.openedDate,
    "commencedon":         LT.openedDate,
    "commencedoperatingon": LT.openedDate,
    "establishedin":       LT.openedDate,
    "launched":            LT.openedDate,
    "formedinyear":        LT.openedDate,
    "restartedoperatingon": LT.openedDate,
    "suspendedon":         LT.openedDate,
    "reopenedon":          LT.openedDate,
    "endedon":             LT.openedDate,
    "endedin":             LT.openedDate,
    "extendedin":          LT.openedDate,

    #acceptedOn (payment/ticketing)
    "acceptedon":          LT.acceptedOn,
    "usedon":              LT.acceptedOn,
    "validon":             LT.acceptedOn,
    "acceptspaymentmethod": LT.acceptedOn,
    "acceptspayment":      LT.acceptedOn,
    "accepts":             LT.acceptedOn,
    "acceptedby":          LT.acceptedOn,
    "acceptspaymentby":    LT.acceptedOn,
    "acceptedpaymentmethod": LT.acceptedOn,
    "usedin":              LT.acceptedOn,

    #misc
    "partof":              LT.partOf,
    "ispartof":            LT.partOf,
    "includedin":          LT.partOf,
    "belongsto":           LT.partOf,
    "locatedin":           LT.locatedIn,
    "operatesin":          LT.locatedIn,
    "locationof":          LT.locatedIn,
    "locatedinarea":       LT.locatedIn,
    "locatedat":           LT.locatedIn,
    "contains":            LT.contains,
    "includes":            LT.contains,
    "includesline":        LT.contains,
    "consistsof":          LT.contains,
    "introducedby":        LT.introducedBy,
    "replacedby":          LT.replacedBy,
    "takenoverby":         LT.replacedBy,
    "succeededby":         LT.replacedBy,
    "alongroute":          LT.onRoute,
    "onroute":             LT.onRoute,
    "criticisedby":        LT.criticisedBy,
    "criticisedtflfor":    LT.criticisedBy,
    "criticizesdecision":  LT.criticisedBy,
    "criticismtowardstfl": LT.criticisedBy,
}

#frequently seen non london entities
NON_LONDON = {"milan", "almaty", "copenhagen", "dublin", "adelaide", "glasgow",
              "nuremberg", "cork", "zurich", "žilina", "prešov", "vancouver",
              "austin", "toronto", "dpmp", "dpmž"}

#types
LABEL_CLASS_MAP = {
    "ORG":     LT.TransportOperator,
    "FAC":     LT.TransitStop,
    "GPE":     LT.Location,
    "LOC":     LT.Location,
    "PRODUCT": LT.TransportService,
    "EVENT":   LT.TransportEvent,
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
    return LT[slugify(label)]

#takes predicateLikeThis from LLM and maps to uri in nameopsace
def map_predicate(raw):
    key = raw.lower().replace(" ", "").replace("_", "").replace("(", "").replace(")", "")
    return PREDICATE_MAP.get(key)


def build_wiki_graph(all_results):
    g = Graph()
    g.bind("lt", LT)
    g.bind("dcterms", DCTERMS)
    g.bind("prov", PROV)
    g.bind("rdfs", RDFS)

    #pipeline provenance
    pipeline_uri = LT["UnstructuredPipeline"]

    g.add((pipeline_uri, RDF.type, PROV.Activity))
    g.add((pipeline_uri, RDFS.label, Literal("LLM Wikipedia Extraction Pipeline")))

    #metrics
    valid = 0
    skipped = 0

    for article in all_results:
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

            #one last filter, check for non london enitites
            if not is_london_entity(triple["subject"]):
                skipped += 1
                continue

            if not is_london_entity(obj_label):
                skipped += 1
                continue
            
            #adds date datatype
            if pred_uri == LT.openedDate:
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
        all_results = json.load(f)

    print(f"Building RDF graph from {len(all_results)} articles...")
    g = build_wiki_graph(all_results)

    out_path = os.path.join("ontologies", "pipeline_output", "unstructured_london_transport.ttl")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    g.serialize(out_path, format="turtle")
    
    print(f"Serialised {len(g)} triples → {out_path}")


if __name__ == "__main__":
    run()