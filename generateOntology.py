import os
from rdflib import Graph, Literal, RDF, RDFS, OWL, XSD, Namespace, URIRef

def generateOntology(output_path="ontologies/manual/tfl_kamyar_final.ttl"):
    g = Graph()

    # Namespaces
    TFL = Namespace("http://example.org/tfl#")
    GTFS = Namespace("http://vocab.gtfs.org/terms#")
    SCHEMA = Namespace("http://schema.org/")
    DCT = Namespace("http://purl.org/dc/terms/")
    
    g.bind("tfl", TFL)
    g.bind("gtfs", GTFS)
    g.bind("schema", SCHEMA)
    g.bind("dct", DCT)
    g.bind("owl", OWL)

    # Ontology Declaration
    onto = URIRef("http://example.org/tfl")
    g.add((onto, RDF.type, OWL.Ontology))
    g.add((onto, RDFS.label, Literal("TfL London Public Transport Ontology", lang="en")))
    g.add((onto, OWL.imports, URIRef("http://vocab.gtfs.org/terms#")))
    g.add((onto, OWL.imports, URIRef("http://schema.org/")))
    g.add((onto, DCT.creator, Literal("Los Caballos – 5CCSAKNE CW2")))
    g.add((onto, DCT.date, Literal("2025-03-01", datatype=XSD.date)))

    # --- TBOX: CLASSES ---
    # (Excluding all Individual/ABox instances)
    classes = [
        (TFL.TfLLine, GTFS.Route, "TfL Line"),
        (TFL.UndergroundLine, TFL.TfLLine, "London Underground Line"),
        (TFL.NightTubeLine, TFL.UndergroundLine, "Night Tube Line"),
        (TFL.OvergroundLine, TFL.TfLLine, "London Overground Line"),
        (TFL.ElizabethLineService, TFL.TfLLine, "Elizabeth Line Service"),
        (TFL.DLRLine, TFL.TfLLine, "Docklands Light Railway Line"),
        (TFL.TramLine, TFL.TfLLine, "TfL Tram Line"),
        (TFL.BusRoute, TFL.TfLLine, "TfL Bus Route"),
        (TFL.NightBusRoute, TFL.BusRoute, "Night Bus Route"),
        (TFL.TfLStation, GTFS.Station, "TfL Station"),
        (TFL.UndergroundStation, TFL.TfLStation, "London Underground Station"),
        (TFL.InterchangeStation, TFL.TfLStation, "Interchange Station"),
        (TFL.TerminalStation, TFL.TfLStation, "Terminal Station"),
        (TFL.BusTerminus, TFL.TfLStation, "Bus Terminus"),
        (TFL.ElizabethLineStation, TFL.TfLStation, "Elizabeth Line Station"),
        (TFL.OvergroundStation, TFL.TfLStation, "London Overground Station"),
        (TFL.DLRStation, TFL.TfLStation, "DLR Station"),
        (TFL.OysterFare, SCHEMA.PriceSpecification, "Oyster Fare"),
        (TFL.PeakFare, TFL.OysterFare, "Peak Hour Oyster Fare"),
        (TFL.OffPeakFare, TFL.OysterFare, "Off-Peak Oyster Fare"),
        (TFL.FlatFare, TFL.OysterFare, "Flat Fare"),
        (TFL.OysterFareZone, GTFS.Zone, "Oyster Fare Zone"),
        (TFL.FareConcession, None, "Fare Concession"),
        (TFL.AccessibilityFeature, None, "Accessibility Feature"),
        (TFL.StepFreeAccess, TFL.AccessibilityFeature, "Step-Free Access"),
        (TFL.AudioVisualAid, TFL.AccessibilityFeature, "Audio-Visual Aid"),
        (TFL.AssistedBoardingService, TFL.AccessibilityFeature, "Assisted Boarding Service"),
        (TFL.StationFacility, None, "Station Facility"),
        (TFL.PublicToilet, TFL.StationFacility, "Public Toilet"),
        (TFL.CarPark, TFL.StationFacility, "Station Car Park"),
        (TFL.ServiceDisruption, None, "Service Disruption"),
        (TFL.EngineeringClosure, TFL.ServiceDisruption, "Engineering Closure"),
        (TFL.AlternativeService, None, "Alternative Service"),
        (TFL.Journey, SCHEMA.Trip, "TfL Journey"),
        (TFL.JourneyLeg, None, "Journey Leg"),
        (TFL.TfLOperator, GTFS.Agency, "TfL Operator")
    ]

    for cls_uri, parent, label in classes:
        g.add((cls_uri, RDF.type, OWL.Class))
        g.add((cls_uri, RDFS.label, Literal(label, lang="en")))
        if parent:
            g.add((cls_uri, RDFS.subClassOf, parent))

    # --- TBOX: OBJECT PROPERTIES ---
    obj_props = [
        (TFL.servedByLine, GTFS.route, TFL.TfLStation, TFL.TfLLine, "Links a TfL station to one of the lines that calls at it."),
        (TFL.hasTerminalStation, None, TFL.TfLLine, TFL.TerminalStation, "Links a TfL line to one of its terminal stations."),
        (TFL.operatesInZone, GTFS.zone, None, TFL.OysterFareZone, "Links a line or station to an Oyster fare zone."),
        (TFL.hasAccessibilityFeature, None, TFL.TfLStation, TFL.AccessibilityFeature, "Links a station to an accessibility feature."),
        (TFL.hasFacility, None, TFL.TfLStation, TFL.StationFacility, "Links a station to a physical facility."),
        (TFL.operatedBy, SCHEMA.provider, TFL.TfLLine, TFL.TfLOperator, "Links a line to its operator."),
        (TFL.terminatesAt, None, TFL.BusRoute, TFL.BusTerminus, "Links a bus route to its terminus."),
        (TFL.hasDisruption, None, TFL.TfLLine, TFL.ServiceDisruption, "Links a line to a service disruption."),
        (TFL.hasAlternativeService, None, TFL.ServiceDisruption, TFL.AlternativeService, "Links disruption to recommended alternatives."),
        (TFL.alternativeUsing, None, TFL.AlternativeService, TFL.TfLLine, "Links recommendation to a replacement line."),
        (TFL.hasJourneyLeg, None, TFL.Journey, TFL.JourneyLeg, "Links a journey to its segments."),
        (TFL.legUsesLine, None, TFL.JourneyLeg, TFL.TfLLine, "Links a leg to the line used."),
        (TFL.journeyOrigin, SCHEMA.departureStation, TFL.Journey, TFL.TfLStation, "Departure station."),
        (TFL.journeyDestination, SCHEMA.arrivalStation, TFL.Journey, TFL.TfLStation, "Arrival station."),
        (TFL.legBoardsAt, None, TFL.JourneyLeg, TFL.TfLStation, "Boarding station for leg."),
        (TFL.legAlightsAt, None, TFL.JourneyLeg, TFL.TfLStation, "Alighting station for leg."),
        (TFL.appliesInZoneFrom, None, TFL.OysterFare, TFL.OysterFareZone, "Lowest zone in fare range."),
        (TFL.appliesInZoneTo, None, TFL.OysterFare, TFL.OysterFareZone, "Highest zone in fare range."),
        (TFL.fareAppliesTo, None, TFL.OysterFare, None, "Links fare to transport mode."),
        (TFL.concessionAppliesTo, None, TFL.FareConcession, TFL.TfLLine, "Links concession to valid lines.")
    ]

    for prop, sub_of, domain, range_cls, comment in obj_props:
        g.add((prop, RDF.type, OWL.ObjectProperty))
        g.add((prop, RDFS.comment, Literal(comment, lang="en")))
        if sub_of: g.add((prop, RDFS.subPropertyOf, sub_of))
        if domain: g.add((prop, RDFS.domain, domain))
        if range_cls: g.add((prop, RDFS.range, range_cls))

    # --- TBOX: DATA PROPERTIES ---
    data_props = [
        (TFL.fareAmount, SCHEMA.price, TFL.OysterFare, XSD.decimal, "Fare amount in GBP."),
        (TFL.farePassengerType, None, TFL.OysterFare, XSD.string, "Passenger category (e.g. Adult)."),
        (TFL.isNightTube, None, TFL.UndergroundLine, XSD.boolean, "Is 24-hour weekend service?"),
        (TFL.isFlatFare, None, TFL.TfLLine, XSD.boolean, "Charges fixed fare regardless of distance?"),
        (TFL.routeNumber, GTFS.shortName, TFL.BusRoute, XSD.string, "Bus route alphanumeric code."),
        (TFL.lineColour, GTFS.color, TFL.TfLLine, XSD.string, "Hex colour code."),
        (TFL.nightTubeOperatingDays, None, TFL.NightTubeLine, XSD.string, "Description of operating days."),
        (TFL.hasStepFreeStreetToPlatform, None, TFL.TfLStation, XSD.boolean, "Full step-free access status."),
        (TFL.zoneNumber, None, TFL.OysterFareZone, XSD.positiveInteger, "Integer zone ID."),
        (TFL.estimatedJourneyMinutes, None, TFL.Journey, XSD.nonNegativeInteger, "Total travel time."),
        (TFL.numberOfLegs, None, TFL.Journey, XSD.nonNegativeInteger, "Total number of segments."),
        (TFL.legSequence, None, TFL.JourneyLeg, XSD.positiveInteger, "Ordinal position in journey."),
        (TFL.closureStartDate, None, TFL.EngineeringClosure, XSD.dateTime, "Start of closure."),
        (TFL.closureEndDate, None, TFL.EngineeringClosure, XSD.dateTime, "End of closure."),
        (TFL.closureDescription, None, TFL.EngineeringClosure, XSD.string, "Details of closure."),
        (TFL.concessionDescription, None, TFL.FareConcession, XSD.string, "Benefits of concession.")
    ]

    for prop, sub_of, domain, range_type, comment in data_props:
        g.add((prop, RDF.type, OWL.DatatypeProperty))
        g.add((prop, RDFS.comment, Literal(comment, lang="en")))
        if sub_of: g.add((prop, RDFS.subPropertyOf, sub_of))
        if domain: g.add((prop, RDFS.domain, domain))
        if range_type: g.add((prop, RDFS.range, range_type))

    
    inverses = [
        (TFL.hasStop, TFL.servedByLine),
        (TFL.operatedBy, TFL.operates),
        (TFL.hasFacility, TFL.facilityAt),
        (TFL.hasTerminalStation, TFL.isTerminalOf),
        (TFL.hasAccessibilityFeature, TFL.accessibilityFeatureAt),
        (TFL.locatedIn, TFL.contains),
        (TFL.hasDisruption, TFL.affectsLine),
    ]
    
    for prop, inv in inverses:
        g.add((prop, OWL.inverseOf, inv))
        g.add((inv, OWL.inverseOf, prop))
        # ensure both are declared as object properties
        g.add((prop, RDF.type, OWL.ObjectProperty))
        g.add((inv, RDF.type, OWL.ObjectProperty))

    # Save to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    g.serialize(destination=output_path, format="turtle")
    print(f"Schema (TBox) generated successfully at {output_path}")
    return g