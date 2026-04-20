# sadiqkhanfanclub

# Run without using LLM:

Run 'main.py'

Test 'competency_questions/competency_question_test.py'

# Run full pipeline using LLM:

1. Set USE_LLM to True in 'extract_triples.py'
2. Enter a valid anthropic API key (or change to another API)
3. run "python -m venv .venv"
4. run "pip install -r requirement.txt"
5. run "python -m spacy download en_core_web_sm"
3. Run 'main.py'


# Run rag

1. Enter a valid anthropic API key (or change to another API) into 'rag.py'
2. Enter gaps into the list
3. Run 'rag.py' 
