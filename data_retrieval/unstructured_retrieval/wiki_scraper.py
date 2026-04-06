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
    # ticket/fare logic
    "Oyster card",
    "Pay-as-you-go",
    "Contactless payment",
    "Fare capping",
    "London fare zones",

    #accessibility and acess semantics
    "Step-free access",
    "Accessibility of transport in London",  
    "London Dial-a-Ride",  
    #"Railway station facilities",

    #night services
    "Night Tube",
    "Night buses in London",
    "Night service (public transport)",

    #system context
    "Transport for London",
    "National Rail",

    #conceptual semantics
    "Rapid transit",
    "Light rail",
    "London Buses",
    "Bus transport in the United Kingdom",
    "Transport hub",
    "Interchange station",
    "Train station",
    "Station building"
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