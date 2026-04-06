from rdflib import Graph

TTL_PATH = "ontologies/pipeline_output/final_london_transport_kg.ttl"
TFL = "http://example.org/tfl#"

g = Graph()
g.parse(TTL_PATH, format="turtle")
print(f"Graph loaded: {len(g):,} triples\n")

CQS = [
    (
        "CQ1: Which London Underground lines intersect at King's Cross St Pancras station?",
        f"""SELECT ?lineName WHERE {{
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
        "CQ4: Which fare zones does the Docklands Light Railway (DLR) operate within?",
        f"""SELECT ?zoneLabel WHERE {{
            <{TFL}DLR> <{TFL}operatesInZone> ?zone .
            ?zone rdfs:label ?zoneLabel .
        }} ORDER BY ?zoneLabel"""
    ),
    (
        "CQ5: Which stations on the Jubilee Line feature step-free access from the street to the train?",
        f"""SELECT ?stationName WHERE {{
            ?station <{TFL}servedByLine> <{TFL}JubileeLine> .
            ?station <{TFL}hasStepFreeStreetToPlatform> true .
            ?station rdfs:label ?stationName .
        }} ORDER BY ?stationName"""
    ),
    (
        "CQ6: Does Baker Street station have public restroom facilities available?",
        f"""SELECT ?facilityLabel WHERE {{
            <{TFL}BakerStreetStation> <{TFL}hasFacility> ?fac .
            ?fac a <{TFL}PublicToilet> .
            ?fac rdfs:label ?facilityLabel .
        }}"""
    ),
    (
        "CQ7: Which stations on the Central Line provide public car parking facilities?",
        f"""SELECT ?stationName ?cpName WHERE {{
            ?station <{TFL}servedByLine> <{TFL}CentralLine> .
            ?station <{TFL}hasFacility> ?cp .
            ?cp a <{TFL}CarPark> .
            ?station rdfs:label ?stationName .
            ?cp rdfs:label ?cpName .
        }} ORDER BY ?stationName"""
    ),
    (
        "CQ8: Who is the designated operating company for the London Overground network?",
        f"""SELECT ?opName WHERE {{
            <{TFL}LondonOverground> <{TFL}operatedBy> ?op .
            ?op rdfs:label ?opName .
        }}"""
    ),
    (
        "CQ9: Which specific bus routes terminate at Trafalgar Square?",
        f"""SELECT ?routeNumber WHERE {{
            ?route <{TFL}terminatesAt> <{TFL}TrafalgarSquareBusTerminus> .
            ?route <{TFL}routeNumber> ?routeNumber .
        }} ORDER BY xsd:integer(?routeNumber)"""
    ),
    (
        "CQ10: Which London Underground lines operate the Night Tube service on Fridays and Saturdays?",
        f"""SELECT ?lineName WHERE {{
            ?line <{TFL}isNightTube> true .
            ?line rdfs:label ?lineName .
        }} ORDER BY ?lineName"""
    ),
    (
        "CQ11: What is the peak-hour Oyster fare for an adult journey travelling across zones 1 to 3?",
        f"""SELECT ?amount ?currency WHERE {{
            <{TFL}PeakFare_Adult_Z1to3> <{TFL}fareAmount> ?amount .
            <{TFL}PeakFare_Adult_Z1to3> <http://schema.org/priceCurrency> ?currency .
        }}"""
    ),
    (
        "CQ12: Which transport modes in the TfL network charge a flat fare regardless of distance travelled?",
        f"""SELECT DISTINCT ?typeLabel WHERE {{
            ?line <{TFL}isFlatFare> true .
            ?line a ?type .
            ?type rdfs:label ?typeLabel .
        }} ORDER BY ?typeLabel"""
    ),
    (
        "CQ13: Which TfL lines currently have planned engineering closures scheduled for this weekend?",
        f"""SELECT ?lineName ?desc WHERE {{
            ?line <{TFL}hasDisruption> ?closure .
            ?closure a <{TFL}EngineeringClosure> .
            ?closure <{TFL}closureDescription> ?desc .
            ?line rdfs:label ?lineName .
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
        "CQ15: What is the estimated journey duration and how many legs are required to travel from Brixton to Canary Wharf?",
        f"""SELECT ?minutes ?legs WHERE {{
            <{TFL}Journey_BrixtonToCanaryWharf> <{TFL}estimatedJourneyMinutes> ?minutes .
            <{TFL}Journey_BrixtonToCanaryWharf> <{TFL}numberOfLegs> ?legs .
        }}"""
    ),
    (
        "CQ16: Which stations on the Overground network offer a staff-assisted boarding service for passengers with disabilities?",
        f"""SELECT ?stationName WHERE {{
            ?station <{TFL}hasAccessibilityFeature> ?feat .
            ?feat a <{TFL}AssistedBoardingService> .
            ?station <{TFL}servedByLine> <{TFL}LondonOverground> .
            ?station rdfs:label ?stationName .
        }} ORDER BY ?stationName"""
    ),
    (
        "CQ17: Which specific bus routes operate as night bus services with an N-prefix in the TfL network?",
        f"""SELECT ?routeNumber WHERE {{
            ?route a <{TFL}NightBusRoute> .
            ?route <{TFL}routeNumber> ?routeNumber .
        }} ORDER BY ?routeNumber"""
    ),
    (
        "CQ18: Which Elizabeth Line stations are equipped with audio-visual aids for sensory-impaired passengers?",
        f"""SELECT ?stationName WHERE {{
            ?station a <{TFL}ElizabethLineStation> .
            ?station <{TFL}hasAccessibilityFeature> ?feat .
            ?feat a <{TFL}AudioVisualAid> .
            ?station rdfs:label ?stationName .
        }} ORDER BY ?stationName"""
    ),
    (
        "CQ19: Which TfL lines serve stations located in both zone 2 and zone 3?",
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
        "CQ20: Which fare concessions apply to disabled passengers using the bus network during peak hours?",
        f"""SELECT ?concLabel ?desc WHERE {{
            ?conc a <{TFL}FareConcession> .
            ?conc rdfs:label ?concLabel .
            ?conc <{TFL}concessionDescription> ?desc .
        }} ORDER BY ?concLabel"""
    ),
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
print (f"Passed {passed}/20 competency questions.")