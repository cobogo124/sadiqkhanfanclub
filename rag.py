import os
import requests
from rdflib import Graph, Namespace

TFL = Namespace("http://example.org/tfl#")

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"

g = Graph()
g.parse("ontologies/pipeline_output/final_london_transport_kg.ttl", format="turtle")

GAPS = [
    {
        "label": "CQ4: DLR fare zones",
        "question": "Which fare zones does the Docklands Light Railway operate in?",
        "context_query": "SELECT ?p ?o WHERE { <http://example.org/tfl#DLR> ?p ?o . } LIMIT 20",
    },
    #list as many gaps as found
]

#finds context from the existing ttl, based on the context query,
#finds predicates and objects where the subject has the knowledge gap
def get_context(query):
    rows = list(g.query(query))
    return "\n".join(f"  {r[0].split('#')[-1]} → {r[1]}" for r in rows)

def ask_llm(question, context):
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "user", "content": f"""Here are known facts from our London transport knowledge graph:
                {context}

                Using these facts as context, answer the following question. 
                Your answer should be concise and specific to the question. 
                You may use your own knowledge to fill gaps, but clearly indicate 
                when you are adding information not present in the provided triples.

                Question: {question}"""}
            ],
            "max_tokens": 512,
            "temperature": 0.1,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"]

#loop throgh gaps and output
for gap in GAPS:
    print(f"\n--- {gap['label']} ---")
    context = get_context(gap["context_query"])
    print(f"Context from KG:\n{context}")
    answer = ask_llm(gap["question"], context)
    print(f"LLM response: {answer}")