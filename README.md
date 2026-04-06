<<<<<<< HEAD
# sadiqkhanfanclub
=======
# sadiqkhanfanclub


## Running the project

# Default (no setup required)
The system runs using pre-generated triples to ensure reproducibility:

python -m spacy download en_core_web_sm
python main.py

# Optional: Run full extraction pipeline

1. Install Ollama: https://ollama.com
2. Run in CMD ensure exposed at "http://localhost:11434/api/generate":

   ollama pull mistral

3. Set:
   USE_LLM = True

Then run:
python -m spacy download en_core_web_sm
python main.py
>>>>>>> f71f2eb67065f2eef1fd07f489c808bc3af7b0eb
