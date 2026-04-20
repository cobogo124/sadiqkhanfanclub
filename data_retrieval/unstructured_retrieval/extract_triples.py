import json
import os
import spacy
import requests
import hashlib
from datetime import date
import re
import time

#SET FALSE TO USE CACHED TRIPLES FILES
###########################
USE_LLM = False  
###########################

#claude setup
API_KEY = ""
model = "claude-sonnet-4-20250514"
url = "https://api.anthropic.com/v1/messages"

CACHE_FILE = "data/caches/triples_cache.json"

#load spacy model (same as lab)
nlp = spacy.load("en_core_web_sm")

#relevant spacy entity types from lab task
RELEVANT_LABELS = {"ORG", "GPE", "LOC", "FAC", "PRODUCT", "EVENT"}

#specifies # of chars to a chunk
CHUNK_SIZE = 1000

#LLM prompt
PROMPT = """You extract RDF triples from text about London public transport.

            Return ONLY lines as: subject | predicate | object
            No bullets, numbers, markdown, or explanation. If nothing to extract: NONE

            ALLOWED PREDICATES (use only these):
            operatedBy, hasStop, hasTerminus, servedByLine, connectsTo,
            operatesInZone, isNightService, isNightTube, hasStepFreeAccess,
            hasAccessibilityFeature, acceptedOn, openedIn, isFlatFare,
            routeNumber, terminatesAt, locatedIn, partOf, replacedBy,
            introducedBy, hasFacility

            RULES:
            - Only facts explicitly in the text. Never infer.
            - Short labels without articles: "Victoria line" not "the Victoria line"
            - Boolean values as "true"
            - Years as 4 digits
            - Zones as "Zone 1", "Zone 2"
            - Max 12 triples
            - Ensure data is correct as of 2026

            EXAMPLES:
            Input: "The Victoria line was opened in 1968 and runs from Brixton to Walthamstow Central. It is operated by London Underground."
            Output:
            Victoria line | openedIn | 1968
            Victoria line | hasTerminus | Brixton
            Victoria line | hasTerminus | Walthamstow Central
            Victoria line | operatedBy | London Underground

            Input: "Stratford station is served by the Jubilee line, Central line, and DLR. It is in Zone 3."
            Output:
            Stratford station | servedByLine | Jubilee line
            Stratford station | servedByLine | Central line
            Stratford station | servedByLine | DLR
            Stratford station | operatesInZone | Zone 3

            Input: "London Buses operate a flat fare of £1.75. The Oyster card and contactless payment are accepted."
            Output:
            London Buses | isFlatFare | true
            Oyster card | acceptedOn | London Buses
            Contactless payment | acceptedOn | London Buses"""

#save and load cached llm output triple files
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


#splits text into approx chunk_size chunks, prevents overloading llm
#avoids cutting of sentences
def chunk_text(text, chunk_size = CHUNK_SIZE):
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) > chunk_size and current:
            chunks.append(current.strip())
            current = para
        else:
            current += " " + para
    if current.strip():
        chunks.append(current.strip())
    return chunks

#Named Entity Recognition (NER)
#uses spacy to identify entities in the text
#example output JSON: { "text": "Victoria line", "label": "ORG" }
def extract_entities_spacy(text):
    doc = nlp(text)
    return [
        {"text": ent.text, "label": ent.label_}
        for ent in doc.ents
        if ent.label_ in RELEVANT_LABELS
    ]



#converts text to rdf triples: subject predicate object, i.e. oysterCard acceptedOn DLR
#finds the relationships, but non deterministic
def extract_triples_llm(passage, cache):
    
    key = hashlib.md5(passage.encode()).hexdigest()
        
    #only uses cache if USE_LLM is false, otherwise runs FULL process
    ############ DELETE, THIS IS TO SAVE TIME ON 05/04/26
    """
    if key in cache:
            print("Using cached triples.")
            return cache[key]
    """
    ############
    if not USE_LLM:
        if key in cache:
            print("Using cached triples.")
            return remove_junk(cache[key])
        else:
            print("LLM disabled and no cache found.")
            return []
        
    else:
        time.sleep(1)
        print("sonnet llm is extracting triples.")
        raw = None
        response = None

        for attempt in range(3):
            try:
                response = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": API_KEY,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            
                            {"role": "user", "content": f"{PROMPT} Extract triples from this passage:\n{passage}"}
                        ],
                        "max_tokens": 1024,
                        "temperature": 0.1, #low temp for reproducibility
                    },
                    timeout=30,
                )
                response.raise_for_status()
                raw = response.json()["content"][0]["text"]
            except requests.exceptions.HTTPError:
                if response is None:
                    print("no response")
                    return []
                if response.status_code == 429 and attempt < 2:
                    wait = 3 * (attempt + 1)
                    print(f"  Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"  API error: {response.status_code} {response.text}")
                    return []
            except Exception as e:
                if attempt < 2:
                    print(f"  Request failed: {e}, retrying in 10s...")
                    time.sleep(20)
                else:
                    print(f"  API error after 3 attempts: {e}")
                    return []
        # all 3 attempts failed without success
       
        if not raw or raw == None:
            return []

        triples = []
        #checks to stop outlandish responses
        for line in raw.strip().splitlines():
            
            #validate outputs
            if "|" not in line:
                continue
            
            parts = [p.strip().strip('"') for p in line.split("|")]
            

            #check has length
            if len(parts) == 3 and all(parts):
                #check length is sensible
                if len(parts[0]) > 60 or len(parts[2]) > 60: 
                    continue
                
                # clean prefixes found in mistral output
                parts[0] = re.sub(r"^(subject:\s*)", "", parts[0], flags=re.IGNORECASE)
                parts[1] = re.sub(r"^(predicate:\s*)", "", parts[1], flags=re.IGNORECASE)
                parts[2] = re.sub(r"^(object:\s*)", "", parts[2], flags=re.IGNORECASE)

                parts[0] = re.sub(r"^\d+[\.\)]\s*", "", parts[0])
                parts[0] = re.sub(r"^[-\d\.\)]+\s*", "", parts[0])
            
                if "{" in parts[0] or "{" in parts[2]:
                    continue
                if parts[0].lower() == "subject":
                    continue
                if "NOTHING" in parts[2] or "(" in parts[2]:
                    continue

                triples.append({
                    "subject": parts[0],
                    "predicate": re.sub(r"\s+(\w)", lambda m: m.group(1).upper(), parts[1].strip()), #cleans whitespace from predicates turns to 'likeThis'
                    "object": parts[2],
                })

        triples = remove_junk(triples)
        #save to cache
        cache[key] = triples
        save_cache(cache)

        return triples
    


def remove_junk(triples):
    JUNK_OBJECTS = {"none", "true", "false", "accessible", "NONE",
                "trains", "stations", "changes", "escalator",
                "roundel", "tunnel", "access", "walls", "ceilings",
                "exits", "pavements", "walkways", "unknown"}

    BOOLEAN_PREDS = {"isNightService", "isNightTube", "isFlatFare",
                    "hasStepFreeAccess"}

        
    triples = [t for t in triples if not (
        #junk objects (unless boolean predicate)
        t["object"].lower() in JUNK_OBJECTS and t["predicate"] not in BOOLEAN_PREDS
        #outside scope
        or (t["predicate"] == "operatesInZone" and any(z in t["object"] for z in ["10","11","12","13","14","15","16"]))
        #empty subjects
        or not t["subject"].strip()
        # object equals "true" on non-boolean preds
        or (t["object"].lower() == "true" and t["predicate"] not in BOOLEAN_PREDS)
        # duplicate-style: subject == object
        or t["subject"].strip().lower() == t["object"].strip().lower()
    )]

    return triples

#validates LLM triples against the entities from spacy
# IMPORTANT: if too many triples dropped loosen the filter, i.e. check if its a substring instead of exact
def filter_triples_by_entities(triples, entities):
    #build set of entities for fast lookup
    entity_names = {
        ent["text"].strip().lower()
        for ent in entities
    }

    filtered = []
    for t in triples:
        subj_match = any(e in t["subject"].strip().lower() or t["subject"].strip().lower() in e for e in entity_names)
        obj_match = any(e in t["object"].strip().lower() or t["object"].strip().lower() in e for e in entity_names)
        

        if subj_match or obj_match:
            filtered.append(t)

    return filtered

#processes 1 wiki article at a time 1. chunks 2. NER with spacy 3. LLM relationship extraction
def process_article(txt_path, cache):
    with open(txt_path, encoding="utf-8") as f:
        text = f.read()
        #text = text[:10000] #useful facts near top of article

    title = os.path.basename(txt_path).replace(".txt", "").replace("_", " ")
    source_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
    print(f"\nProcessing: {title}")

    chunks = chunk_text(text)
    print(f"  {len(chunks)} chunks")

    all_entities, all_triples = [], []

    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}/{len(chunks)}...", end=" ", flush=True)

        entities = extract_entities_spacy(chunk)
        triples = extract_triples_llm(chunk, cache)

        all_entities.extend(entities)
        all_triples.extend(triples)

    #validate triples against spacy entities
    print("Validating triples against spacy identified entities.")
    validated_triples = filter_triples_by_entities(all_triples, all_entities)
    print(f"{len(all_entities)} entities, {len(all_triples)} raw triples, {len(validated_triples)} validated")

    #remove repeated entites
    seen_ents = set()
    unique_entities = []
    for e in all_entities:
        key = (e["text"], e["label"])
        if key not in seen_ents:
            seen_ents.add(key)
            unique_entities.append(e)

    #remove repeated triples, IMPORTANT
    seen = set()
    unique_triples = []
    for t in validated_triples:
        key = (t["subject"], t["predicate"], t["object"])
        if key not in seen:
            seen.add(key)
            unique_triples.append(t)



    print(f"  Total: {len(all_entities)} entities, {len(unique_triples)} unique triples")
    return {
        "title": title,
        "source_url": source_url,
        "entities": unique_entities,
        "triples": unique_triples,
    }





################################################################

#finds input files 
#and saves output files 
def run_extract_triples():

    #finds most recent wiki pulls
    today = str(date.today())

    processed_dir = os.path.join("data", "raw")
    latest = sorted(os.listdir(processed_dir))[-1]
    wiki_dir = os.path.join(processed_dir, latest, "wikipedia")

    out_dir = os.path.join("data", "processed", today)
    os.makedirs(out_dir, exist_ok=True)

    txt_files = [
        os.path.join(wiki_dir, f)
        for f in os.listdir(wiki_dir)
        if f.endswith(".txt")
    ]

    if not txt_files:
        print(f"no .txt files found in {wiki_dir}")
        print("run wiki_scraper.py first")
        return

    all_results = []
    cache = load_cache()
    for txt_path in sorted(txt_files):

        result = process_article(txt_path, cache)
        all_results.append(result)

    #save JSON with the triples for next stage
    out_path = os.path.join(out_dir, "wiki_triples.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    total = sum(len(r["triples"]) for r in all_results)
    print(f"\nExtracted {total} triples across {len(all_results)} articles")
    print(f"Saved → {out_path}")


if __name__ == "__main__":
    run_extract_triples()