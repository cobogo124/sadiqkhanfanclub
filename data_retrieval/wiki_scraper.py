import json
import os
import requests
from datetime import date

#unfinsihed article list suggest additions
ARTICLES = [
    "Oyster card",
    "London Underground",
    "Elizabeth line",
    "Docklands Light Railway",
    "London Overground",
    "Trams in Croydon",
    "London fare zones",
    "Transport for London",
]

#inputs wiki article title, outputs plain text
def get_wikipedia_text(title: str) -> str:
    response = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "explaintext": True,
            "exsectionformat": "plain",
            "format": "json",
        },
    )
    response.raise_for_status()
    pages = response.json()["query"]["pages"]
    page = next(iter(pages.values()))
    return page.get("extract", "")



def snapshot_dir(repo_root: str, snapshot_date: str) -> str:
    path = os.path.join(repo_root, "downloads", "raw", snapshot_date, "wikipedia")
    os.makedirs(path, exist_ok=True)
    return path


def run(repo_root: str = ".") -> None:
    today = str(date.today())
    out_dir = snapshot_dir(repo_root, today)
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
        print(f"  Saved {len(text)} characters → {filename}")

    #save manifest alongside the text files
    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest saved → {manifest_path}")


if __name__ == "__main__":
    run()