# tools/integrations.py
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from datasets import Dataset
import random

def run_with_ragas(plan, suite):
    # Use one prompt randomly (or iterate)
    prompt = random.choice(suite.sample_prompts or ["What is AI?"])
    
    # Simulate input-output-context for now (use real RAG/RAG pipeline in full flow)
    data = {
        "question": [prompt],
        "answer": ["AI is the simulation of human intelligence by machines."],
        "contexts": [["AI enables machines to mimic cognitive functions."]]
    }
    
    ds = Dataset.from_dict(data)
    metrics = [faithfulness, answer_relevancy, context_precision]
    results = {m.name: m.score(ds).scores[0] for m in metrics}

    return {
        "tool": "RAGAS",
        "rmf_tags": ["RMF.MEASURE", "RMF.GOV"],
        "scores": results
    }


def run_with_promptfoo(plan, suite):
    suite_config = {
        "prompts": suite.sample_prompts,
        "models": [{"id": plan.model}]
    }
    result = evaluate(suite_config)  # Placeholder for real PromptFoo execution
    return {
        "tool": "PromptFoo",
        "rmf_tags": suite.rmf_tags or ["RMF.MEASURE"],
        "scores": result
    }
