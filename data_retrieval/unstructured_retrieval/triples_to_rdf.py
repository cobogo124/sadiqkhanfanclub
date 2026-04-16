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
    # ── hasStop ──
    "hasstop":             TFL.hasStop,
    "operatesthrough":     TFL.hasStop,
    "operatesvia":         TFL.hasStop,
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
 
    # ── hasTerminus ──
    "hasterminus":         TFL.hasTerminus,
    "startsat":            TFL.hasTerminus,
    "endsat":              TFL.hasTerminus,
    "terminatesat":        TFL.hasTerminus,
    "isterminus":          TFL.hasTerminus,
    "startsatstation":     TFL.hasTerminus,
    "endsatstation":       TFL.hasTerminus,
    "terminatesatoriginally": TFL.hasTerminus,
    "terminatesatcurrently":  TFL.hasTerminus,
 
    # ── operatedBy ──
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
 
    # ── connectsTo ──
    "connectsto":          TFL.connectsTo,
    "connectedtoviaroute": TFL.connectsTo,
    "connectswith":        TFL.connectsTo,
    "connectedby":         TFL.connectsTo,
    "connectedviaroute":   TFL.connectsTo,
    "connectswithoutside": TFL.connectsTo,
 
    # ── operatesInZone ──
    "infareZone":          TFL.operatesInZone,
    "infarezone":          TFL.operatesInZone,
    "haszones":            TFL.operatesInZone,
    "includeszone":        TFL.operatesInZone,
    "operatesinzone":      TFL.operatesInZone,
    "applicableforzones":  TFL.operatesInZone,
    "farezoneis":          TFL.operatesInZone,
    "inzone":              TFL.operatesInZone,
    "zone":                TFL.operatesInZone,
 
    # ── servedByLine ──
    "servedby":            TFL.servedByLine,
    "servedbyroute":       TFL.servedByLine,
    "servedbyline":        TFL.servedByLine,
    "isservedby":          TFL.servedByLine,
 
    # ── isNightTube ── 
    "isnightservice":      TFL.isNightTube,
    "operatesnightservice": TFL.isNightTube,
    "isnighttube":         TFL.isNightTube,
    "operatesnightserviceon": TFL.isNightTube,
    "nightservice":        TFL.isNightTube,
 
    # ── isFlatFare ── 
    "isflatfare":          TFL.isFlatFare,
    "flatfare":            TFL.isFlatFare,
    "chargesflatfare":     TFL.isFlatFare,
 
    # ── hasFacility ── 
    "hasfacility":         TFL.hasFacility,
    "facility":            TFL.hasFacility,
    "hasfacilities":       TFL.hasFacility,
 
    # ── routeNumber ── 
    "routenumber":         TFL.routeNumber,
    "routeno":             TFL.routeNumber,
    "busnumber":           TFL.routeNumber,
    "busroute":            TFL.routeNumber,
 
    # ── hasStepFreeStreetToPlatform ──
    "isstepfree":          TFL.hasStepFreeStreetToPlatform,
    "hasstepfreeaccess":   TFL.hasStepFreeStreetToPlatform,
    "madestepfree":        TFL.hasStepFreeStreetToPlatform,
    "willgainstepfreeaccess": TFL.hasStepFreeStreetToPlatform,
    "hasstepfreeaccesstoallplatformsatcostof": TFL.hasStepFreeStreetToPlatform,
    "stepfree":            TFL.hasStepFreeStreetToPlatform,
 
    # ── hasAccessibilityFeature ──
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
 
    # ── fareAmount ──
    "fareamount":          TFL.fareAmount,
    "costs":               TFL.fareAmount,
    "cost":                TFL.fareAmount,
    "costofconstruction":  TFL.fareAmount,
    "costofupgrade":       TFL.fareAmount,
    "amount":              TFL.fareAmount,
    "initialbudget":       TFL.fareAmount,
 
    # ── operatesOn / general operations ──
    "operateson":          TFL.operatesOn,
    "operates":            TFL.operatesOn,
    "operatesasauthority": TFL.operatesOn,
    "responsiblefor":      TFL.operatesOn,
    "manages":             TFL.operatesOn,
    "oversees":            TFL.operatesOn,
    "isresponsiblefor":    TFL.operatesOn,
    "owns":                TFL.operatesOn,
 
    # ── servesMode ──
    "servesmode":          TFL.servesMode,
    "type":                TFL.servesMode,
    "typeof":              TFL.servesMode,
    "linetype":            TFL.servesMode,
 
    # ── dates ──
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
 
    # ── acceptedOn (payment/ticketing) ──
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
 
    # ── misc ──
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

#non london entities appearing in the wiki pages, llm couldnt relia
NON_LONDON = {
    # countries
    "argentina", "australia", "austria", "azerbaijan", "belarus", "belgium",
    "brazil", "bulgaria", "canada", "china", "denmark", "egypt", "finland",
    "france", "germany", "greece", "hungary", "iceland", "india", "indonesia",
    "iran", "ireland", "israel", "italy", "japan", "kazakhstan", "malaysia",
    "mexico", "netherlands", "nigeria", "norway", "pakistan", "philippines",
    "poland", "portugal", "russia", "saudi", "serbia", "singapore", "slovakia",
    "slovenia", "somalia", "south africa", "south korea", "spain", "sri lanka",
    "sudan", "sweden", "switzerland", "taiwan", "thailand", "turkey", "ukraine",
    "venezuela", "yemen",
    # foreign cities
    "milan", "almaty", "copenhagen", "dublin", "adelaide", "glasgow", "nuremberg",
    "cork", "zurich", "žilina", "prešov", "vancouver", "austin", "toronto",
    "palermo", "cairo", "athens", "helsinki", "stockholm", "sydney", "paris",
    "berlin", "madrid", "rome", "amsterdam", "brussels", "vienna", "prague",
    "budapest", "warsaw", "lisbon", "seoul", "tokyo", "beijing", "shanghai",
    "mumbai", "bogota", "santiago", "lima", "buenos", "são", "rio",
    "johannesburg", "barcelona", "moscow", "chicago", "philadelphia", "boston",
    "miami", "houston", "dallas", "denver", "seattle", "portland", "detroit",
    "atlanta", "pittsburgh", "minneapolis", "sacramento", "los angeles",
    "san francisco", "san diego", "new york", "new jersey", "new orleans",
    "cologne", "hamburg", "munich", "stuttgart", "dresden", "frankfurt",
    "strasbourg", "toulouse", "marseille", "lyon", "lille", "nantes", "bordeaux",
    "naples", "turin", "genoa", "bilbao", "manila", "jakarta", "bangkok",
    "hong kong", "taipei", "kaohsiung", "kuala lumpur", "bangalore", "hyderabad",
    "pune", "chennai", "karachi", "lahore", "tehran", "istanbul", "caracas",
    "medellín", "guadalajara", "montreal", "ottawa", "calgary", "edmonton",
    "brisbane", "melbourne", "perth", "auckland", "wellington",
    # foreign transit
    "nitelink", "connexxion", "ret", "movia", "amat", "after midnight",
    "blue night", "metro vancouver", "first glasgow", "ontario", "moonliner",
    "nachtbus", "nachtexpress", "noctilien", "noctambus", "noctis", "nightride",
    "nitbus", "afterbus",
    # non-transport
    "apple", "google", "samsung", "microsoft", "amazon", "visa", "mastercard",
    "barclays", "hsbc", "vodafone", "bbc", "wikipedia", "wikimedia",
    "american express", "delta air", "united airlines", "continental airlines",
    "frontier airlines", "alaska airlines", "pan am", "easyjet", "eurostar",
    "facebook", "whatsapp", "android", "iphone", "sony", "nokia", "fujitsu",
    "siemens", "bombardier", "alstom",
}

#types
LABEL_CLASS_MAP = {
    "ORG":     TFL.TransportOperator,
    "FAC":     TFL.TransitStop,
    "GPE":     TFL.Location,
    "LOC":     TFL.Location,
    "PRODUCT": TFL.TransportService,
    "EVENT":   TFL.TransportEvent,
}

#known tube lines
TUBE_LINES = {
    TFL.BakerlooLine, TFL.CentralLine, TFL.CircleLine, TFL.DistrictLine,
    TFL.HammersmithCityLine, TFL.JubileeLine, TFL.MetropolitanLine,
    TFL.NorthernLine, TFL.PiccadillyLine, TFL.VictoriaLine,
    TFL.WaterlooCityLine, TFL.WaterlooAndCityLine,
    TFL.ElizabethLineRoute, TFL.DLR, TFL.LondonOverground, TFL.Tramlink,
}

#checks if mention of somewhere outside of london
def is_london_entity(text):
    t = text.lower()
    return not any(f" {kw} " in f" {t} " for kw in NON_LONDON)

CANONICAL = {
    # Acronyms
    'Dlr': 'DLR',
    'Tfl': 'TfL',
    'DocklandsLightRailway': 'DLR',
    'Jubilee': 'JubileeLine',
    'Central': 'CentralLine',
    'Victoria': 'VictoriaLine',
    'Northern': 'NorthernLine',
    'Piccadilly': 'PiccadillyLine',
    'Bakerloo': 'BakerlooLine',
    'Circle': 'CircleLine',
    'District': 'DistrictLine',
    'Metropolitan': 'MetropolitanLine',
    'HammersmithCity': 'HammersmithCityLine',
    'WaterlooCity': 'WaterlooAndCityLine',
    'ElizabethLine': 'ElizabethLineRoute',
    'BakerStreet': 'BakerStreetStation',
    'KingsCross': 'KingsCrossStPancras',
    'Stratford': 'StratfordStation',
    'TrafalgarSquare': 'TrafalgarSquareBusTerminus',
}

def normalize_entity(text: str) -> str:
    text = text.strip().lower()

    text = text.replace("&", "and")

    #remove common suffixes
    suffixes = [" line", " railway", " station"]
    for s in suffixes:
        if text.endswith(s):
            text = text[: -len(s)]

    #remove whitespace
    text = " ".join(text.split())

    return text

#makes pascal case to match modelling team
def slugify(text):
    
    text = normalize_entity(text) 

    text = re.sub(r"[^\w\s-]", "", text)
    text = "".join(word.capitalize() for word in text.split())
    return CANONICAL.get(text, text)

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
    labelled = set() 
    for article in all_resuTFLs:
        source_url = f"https://en.wikipedia.org/wiki/{article['title'].replace(' ', '_')}"
        source_uri = URIRef(source_url)
        
        #add rdf:type
        for ent in article.get("entities", []):
            text = ent["text"]
            # skip non-London
            if not is_london_entity(text):
                continue
            # skip if too short (single chars, numbers)
            if len(text) <= 2:
                continue
            # skip if it's just a number or date
            if text.replace(" ", "").replace(":", "").replace("-", "").isdigit():
                continue
            # skip overly long concatenated entities
            if len(text) > 40:
                continue
            cls = LABEL_CLASS_MAP.get(ent["label"])
            if cls:
                ent_uri = label_to_uri(text)
                g.add((ent_uri, RDF.type, cls))
                if ent_uri not in labelled: 
                    
                    g.add((ent_uri, RDFS.label, Literal(text)))
                    labelled.add(ent_uri)
        
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
            elif obj_label.lower() in ("true", "false"): 
                obj_node = Literal(obj_label.lower() == "true")
            elif len(obj_label.split()) <= 5 and not any(c.isdigit() for c in obj_label):
                obj_node = label_to_uri(obj_label)
                if obj_node not in labelled: 
                    g.add((obj_node, RDFS.label, Literal(obj_label)))
                    labelled.add(obj_node)

            else:
                obj_node = Literal(obj_label)

            #adds readable rdfs:labels
            if subj_uri not in labelled: 
                g.add((subj_uri, RDFS.label, Literal(triple["subject"])))
                labelled.add(subj_uri)
            
            #another duplicate check
            if (subj_uri, pred_uri, obj_node) not in g:
                g.add((subj_uri, pred_uri, obj_node))
                g.add((subj_uri, PROV.wasGeneratedBy, pipeline_uri))
                valid += 1

            #add data provenance (wiki for all)
            g.add((subj_uri, DCTERMS.source, source_uri))

    print(f"Valid triples: {valid}, Skipped: {skipped}")       
    return g




def enrich_graph(g):
 
    enriched = 0
 
    #servedByLine inverse
    for station, line in g.subject_objects(TFL.servedByLine):
        if (line, TFL.hasStop, station) not in g:
            g.add((line, TFL.hasStop, station))
            enriched += 1
    for line, station in g.subject_objects(TFL.hasStop):
        if line in TUBE_LINES and (station, TFL.servedByLine, line) not in g: 
            g.add((station, TFL.servedByLine, line))
            enriched += 1
 
    #hasTerminus inverse
    for s, o in g.subject_objects(TFL.hasTerminus):
        if o in TUBE_LINES:
            if (o, TFL.hasTerminalStation, s) not in g:
                g.add((o, TFL.hasTerminalStation, s))
                enriched += 1
        if s in TUBE_LINES: 
            if (s, TFL.hasTerminalStation, o) not in g:
                g.add((s, TFL.hasTerminalStation, o))
                enriched += 1
 

    #checks for information on zones
    zone_pattern = re.compile(r"^Zone\s*(\d+)$", re.IGNORECASE)
    for s, o in list(g.subject_objects(TFL.operatesInZone)):
        if isinstance(o, Literal):
            m = zone_pattern.match(str(o))
            if m:
                zone_num = m.group(1)
                zone_uri = TFL[f"Zone{zone_num}"]
                if (s, TFL.operatesInZone, zone_uri) not in g:
                    g.add((s, TFL.operatesInZone, zone_uri))
                    g.add((zone_uri, RDFS.label, Literal(f"Zone {zone_num}")))
                    enriched += 1



    for line in TUBE_LINES:
        for station in g.subjects(TFL.servedByLine, line):
            for zone in g.objects(station, TFL.operatesInZone):
                if (line, TFL.operatesInZone, zone) not in g:
                    g.add((line, TFL.operatesInZone, zone))
                    enriched += 1
 
    #nightbus check (checks for n prefix)
    for s in g.subjects(RDFS.label, None):
        for label in g.objects(s, RDFS.label):
            lab = str(label)
            if re.match(r"^N\d+$", lab):
                if (s, RDF.type, TFL.NightBusRoute) not in g:
                    g.add((s, RDF.type, TFL.NightBusRoute))
                    g.add((s, TFL.routeNumber, Literal(lab)))
                    enriched += 1
                break
    #make sure bus lines arent counted as tube lines
    for s, o in list(g.subject_objects(TFL.isNightTube)):
        if s not in TUBE_LINES:
            g.remove((s, TFL.isNightTube, o))
 
 
    #elizabeth line specifics
    for s in g.subjects(TFL.servedByLine, TFL.ElizabethLineRoute):
        if (s, RDF.type, TFL.ElizabethLineStation) not in g:
            g.add((s, RDF.type, TFL.ElizabethLineStation))
            enriched += 1

 
    for s, o in g.subject_objects(TFL.hasTerminus):
        if (s, TFL.terminatesAt, o) not in g:
            g.add((s, TFL.terminatesAt, o))
            enriched += 1
    
    #add facility types
    FACILITY_CLASSES = {
        "toilets": TFL.PublicToilet,
        "restroom": TFL.PublicToilet,
        "car park": TFL.CarPark,
        "parking": TFL.CarPark,
    }

    for s, o in list(g.subject_objects(TFL.hasFacility)):
        for label in g.objects(o, RDFS.label):
            key = str(label).lower()
            if key in FACILITY_CLASSES:
                g.add((o, RDF.type, FACILITY_CLASSES[key]))

    #change wiki accesibility terms to namespace specific ones
    FEATURE_CLASSES = {
        "audio-visual announcements": TFL.AudioVisualAid,
        "audio visual announcements": TFL.AudioVisualAid,
        "audiovisual announcements":  TFL.AudioVisualAid,
        "audiovisual passenger information": TFL.AudioVisualAid,
        "audio induction loop":       TFL.AudioVisualAid,
        "hearing loops":              TFL.AudioVisualAid,
        "staffed for safety reasons":  TFL.AssistedBoardingService,
    }
    for s, o in list(g.subject_objects(TFL.hasAccessibilityFeature)):
        #check if o has label to classify
        for feat_label in g.objects(o, RDFS.label):
            feat_key = str(feat_label).lower().strip()
            if feat_key in FEATURE_CLASSES:
                cls = FEATURE_CLASSES[feat_key]
                if (o, RDF.type, cls) not in g:
                    g.add((o, RDF.type, cls))
                    enriched += 1

    for uri in [TFL.FreedomPass, TFL.DisabledPersonsRailcard,
                TFL.DisabledPersonsFreedomPass, TFL.OlderPersonsFreedomPass,
                TFL.BusTramDiscountCard, TFL.ZipCard]:
        if (uri, RDFS.label, None) in g:
            if (uri, RDF.type, TFL.FareConcession) not in g:
                g.add((uri, RDF.type, TFL.FareConcession))
                enriched += 1

    print(f"  Enrichment added {enriched} derived triples")
    return g
 


##### MAIN FUNCTIONS
def run_triples_to_rdf():
    #finds most recent triples output
    processed_dir = os.path.join("data", "processed")
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
    g = enrich_graph(g)

    out_path = os.path.join("ontologies", "pipeline_output", "unstructured_london_transport.ttl")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    g.serialize(out_path, format="turtle")
    
    print(f"Serialised {len(g)} triples → {out_path}")


if __name__ == "__main__":
    run_triples_to_rdf()