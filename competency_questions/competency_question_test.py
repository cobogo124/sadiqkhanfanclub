from rdflib import Graph

TTL_PATH = "ontologies/pipeline_output/final_london_transport_kg.ttl"
TFL = "http://example.org/tfl#"

g = Graph()
g.parse(TTL_PATH, format="turtle")
print(f"Graph loaded: {len(g):,} triples\n")

CQS = [
    # --- STRUCTURED TOPOLOGY QUERIES (12) ---
    (
        "CQ1: Which London Underground lines intersect at King's Cross St Pancras station?",
        f"""SELECT DISTINCT ?lineName WHERE {{
            <{TFL}KingsCrossStPancras> <{TFL}servedByLine> ?line .
            ?line rdfs:label ?lineName .
        }} ORDER BY ?lineName"""
    ),
    (
        "CQ2: What are the terminal stations for the Victoria Line?",
        f"""SELECT ?stationName WHERE {{
            <{TFL}VictoriaLine> <{TFL}hasTerminalStation> ?station .
            ?station rdfs:label ?stationName .
        }} ORDER BY ?stationName"""
    ),
    (
        "CQ3: Which transport modes (e.g., Tube, Bus, DLR, Elizabeth Line) are available for interchange at Stratford station?",
        f"""SELECT ?lineName WHERE {{
            <{TFL}StratfordStation> <{TFL}servedByLine> ?line .
            ?line rdfs:label ?lineName .
        }} ORDER BY ?lineName"""
    ),
    (
        "CQ4: Which stations on the Jubilee Line feature step-free access from the street to the train?",
        f"""SELECT ?stationName WHERE {{
            ?station <{TFL}servedByLine> <{TFL}JubileeLine> .
            ?station <{TFL}hasStepFreeStreetToPlatform> true .
            ?station rdfs:label ?stationName .
        }} ORDER BY ?stationName"""
    ),
    (
        "CQ5: Does Baker Street station have public restroom facilities available?",
        f"""SELECT ?facilityLabel WHERE {{
            <{TFL}BakerStreetStation> <{TFL}hasFacility> ?fac .
            ?fac a <{TFL}PublicToilet> .
            ?fac rdfs:label ?facilityLabel .
        }}"""
    ),
    (
        "CQ6: Which transport modes in the TfL network charge a flat fare regardless of distance travelled?",
        f"""SELECT DISTINCT ?typeLabel WHERE {{
            ?line <{TFL}isFlatFare> true .
            ?line a ?type .
            ?type rdfs:label ?typeLabel .
        }} ORDER BY ?typeLabel"""
    ),
    (
        "CQ7: Which TfL lines serve Paddington station?",
        f"""SELECT DISTINCT ?lineName WHERE {{
            ?station <{TFL}servedByLine> ?line .
            ?station rdfs:label ?stationLabel .
            FILTER(CONTAINS(LCASE(STR(?stationLabel)), "paddington"))
            ?line rdfs:label ?lineName .
        }} ORDER BY ?lineName"""
    ),
    (
        "CQ8: Which TfL lines operate within Zone 1?",
        f"""SELECT DISTINCT ?lineName WHERE {{
            ?line <{TFL}operatesInZone> <{TFL}Zone1> .
            ?stop <{TFL}servedByLine> ?line .
            ?line rdfs:label ?lineName .
        }} ORDER BY ?lineName"""
    ),
    (
        "CQ9: Which specific bus routes operate as night bus services with an N-prefix in the TfL network?",
        f"""SELECT ?routeNumber WHERE {{
            ?route a <{TFL}NightBusRoute> .
            ?route <{TFL}routeNumber> ?routeNumber .
        }} ORDER BY ?routeNumber"""
    ),
    (
        "CQ10: Which TfL lines operate within Zone 4?",
        f"""SELECT DISTINCT ?lineName WHERE {{
            ?line <{TFL}operatesInZone> <{TFL}Zone4> .
            ?stop <{TFL}servedByLine> ?line .
            ?line rdfs:label ?lineName .
        }} ORDER BY ?lineName"""
    ),
    (
        "CQ11: Which TfL lines serve stations located in both zone 2 and zone 3?",
        f"""SELECT DISTINCT ?lineName WHERE {{
            ?s1 <{TFL}servedByLine> ?line .
            ?s1 <{TFL}operatesInZone> <{TFL}Zone2> .
            ?s2 <{TFL}servedByLine> ?line .
            ?s2 <{TFL}operatesInZone> <{TFL}Zone3> .
            ?line rdfs:label ?lineName .
            FILTER(?s1 != ?s2)
        }} ORDER BY ?lineName"""
    ),
    (
        "CQ12: Which TfL lines terminate at Stratford station?",
        f"""SELECT DISTINCT ?lineName WHERE {{
            ?line <{TFL}hasTerminalStation> <{TFL}StratfordStation> .
            ?line rdfs:label ?lineName .
        }} ORDER BY ?lineName"""
    ),

    # --- UNSTRUCTURED WIKIPEDIA QUERIES (8) ---
    (
        "CQ13: Who is the designated operating company for the London Overground network?",
        f"""SELECT ?opName WHERE {{
            <{TFL}LondonOverground> <{TFL}operatedBy> ?op .
            ?op rdfs:label ?opName .
        }}"""
    ),
    (
        "CQ14: What is the official operator of the Docklands Light Railway?",
        f"""SELECT ?opName WHERE {{
            <{TFL}DLR> <{TFL}operatedBy> ?op .
            ?op rdfs:label ?opName .
        }}"""
    ),
    (
        "CQ15: In what year did the Bakerloo line open?",
        f"""SELECT ?year WHERE {{
            <{TFL}BakerlooLine> <{TFL}openedDate> ?year .
        }}"""
    ),
    (
        "CQ16: In what year did the Victoria line open?",
        f"""SELECT ?year WHERE {{
            <{TFL}VictoriaLine> <{TFL}openedDate> ?year .
        }}"""
    ),
    (
        "CQ17: On which transport networks is the Oyster card accepted?",
        f"""SELECT DISTINCT ?networkName WHERE {{
            <{TFL}OysterCard> <{TFL}acceptedOn> ?network .
            ?network rdfs:label ?networkName .
        }} ORDER BY ?networkName"""
    ),
    (
        "CQ18: Which transport networks accept the Freedom Pass?",
        f"""SELECT DISTINCT ?networkName WHERE {{
            <{TFL}FreedomPass> <{TFL}acceptedOn> ?network .
            ?network rdfs:label ?networkName .
        }} ORDER BY ?networkName"""
    ),
    (
        "CQ19: What accessibility features are available on the Docklands Light Railway (DLR)?",
        f"""SELECT DISTINCT ?featureName WHERE {{
            <{TFL}DLR> <{TFL}hasAccessibilityFeature> ?feature .
            ?feature rdfs:label ?featureName .
        }} ORDER BY ?featureName"""
    ),
    (
        "CQ20: In what year did the Jubilee Line Extension open?",
        f"""SELECT ?year WHERE {{
            <{TFL}JubileeLineExtension> <{TFL}openedDate> ?year .
        }}"""
    )
]

passed = 0 
for label, sparql in CQS:
    print(f"\n------{label}-----\n")
    rows = list(g.query(sparql))
    if not rows:
        print("    (no results)")
    else:
        passed += 1
        for row in rows:
            print(f"{', '.join(str(v) for v in row)}")
    print()
print(f"Passed {passed}/20 competency questions.")