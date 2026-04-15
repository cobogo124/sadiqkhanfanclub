import json
import os
import requests
from datetime import date

#unfinsihed article list suggest additions
"""ARTICLES = [
    "Oyster card",
    "London Underground",
    "Elizabeth line",
    "Docklands Light Railway",
    "London Overground",
    "Trams in Croydon",
    "London fare zones",
    "Transport for London",
]"""

ARTICLES = [
    # ── core lines (each has operator, terminus, zone, history facts) ──
    "London Underground",
    "Victoria line",
    "Jubilee line",
    "Central line",
    "Northern line",
    "Piccadilly line",
    "Bakerloo line",
    "Circle line (London Underground)",
    "District line",
    "Metropolitan line",
    "Hammersmith & City line",
    "Waterloo & City line",
    "Elizabeth line",
    "Docklands Light Railway",
    "London Overground",
    "Tramlink",
    "London River Services",
    "IFS Cloud Cable Car",
 
    # ── key interchange stations (CQ1, CQ3) ──
    "King's Cross St Pancras tube station",
    "Stratford station",
    "Baker Street tube station",
    "Bank and Monument stations",
    "Canary Wharf tube station",
    "Brixton tube station",
    "London terminal stations",
    # ── ticketing & fares (CQ11, CQ12) ──
    "Oyster card",
    "CPAY",
    "London fare zones",
    "Travelcard",
 
    # ── night services (CQ10, CQ17) ──
    "Night Tube",
    "Night buses in London",
 
    # ── accessibility (CQ5, CQ16, CQ18) ──
    "Step-free access",
    "Accessibility of transport in London",
 
    # ── operators & governance (CQ8, CQ14) ──
    "Transport for London",
    "Arriva Rail London",
 
    # ── buses (CQ9, CQ17) ──
    "London Buses",
    "List of bus routes in London",
 
    # ── concessions (CQ20) ──
    "Freedom Pass",
    "Disabled Persons Railcard",
    
    # buses
    "iBus (London)",
    "Countdown (bus arrival system)",
    "CentreComm",
    "List of bus stations in London",
    "List of bus garages in London",
    "Superloop (London)",
    "Go-Ahead London",
    "Stagecoach London",
    "Metroline",
    "Transport UK London Bus",
    "Hopper fare",
    # Infrastructure & Nodes for hasStop/hasTerminus
    "List of bus stations in London",
    "List of bus garages in London",
    "Category:Railway termini in London",
    
    # Operators for operatedBy/replacedBy
    "Go-Ahead London",
    "Stagecoach London",
    "Metroline",
    "London United Busways", # High turnover of operators here
    
    # Projects for fareAmount (Cost/Budget)
    "Crossrail", 
    "Northern line extension to Battersea",
    "Upgrade of the Jubilee line",
    
    # Technology for hasAccessibilityFeature/acceptedOn
    "iBus (London)",
    "Lifts on the London Underground",
    
    # Vehicles for servesMode/criticisedBy
    "New Routemaster",
    "London Underground rolling stock",
    "British Rail Class 345",

    "Elizabeth line",
    

]

#inputs wiki article title, outputs plain text
def get_wikipedia_text(title):

    #update K_NUMBER to email for submission
    headers = {
        "User-Agent": "TfL_Ontology_Scraper/1.0 (K_NUMBER@kcl.ac.uk)"
    }

    response = requests.get(
        "https://en.wikipedia.org/w/api.php",
        headers=headers,
        params={
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "explaintext": True,
            "redirects": 1,
            "exsectionformat": "plain",
            "format": "json",
        },
    )
    response.raise_for_status()

    pages = response.json()["query"]["pages"]
    
    page = next(iter(pages.values()))
    if "missing" in page:
        print(f"{title} page does not exist")
        return ""
    
    return page.get("extract", "")



def snapshot_dir(snapshot_date):
    path = os.path.join("data", "raw", snapshot_date, "wikipedia")
    os.makedirs(path, exist_ok=True)
    return path


def run_wiki_scraper():
    today = str(date.today())
    out_dir = snapshot_dir(today)
    manifest = []

    for title in ARTICLES:
        print(f"Fetching: {title}")
        text = get_wikipedia_text(title)

        #
        filename = title.replace(" ", "_") + ".txt"
        filepath = os.path.join(out_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

        manifest.append({
            "title": title,
            "filename": filename,
            "characters": len(text),
            "retrieved_at": today,
            "source_url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
        })
        print(f"  Saved {len(text)} characters to {filename}")

    #save manifest alongside the text files
    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest saved → {manifest_path}")


if __name__ == "__main__":
    run_wiki_scraper()