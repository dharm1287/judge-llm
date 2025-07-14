from langchain.prompts import PromptTemplate

# Define prompt for risk detection and RMF mapping
prompt_template_risk = PromptTemplate(
    input_variables=["doc_content"],
    template="""
You are a risk analysis engine for scope documents. Given the following text, do two things:
1. List at least 4 types of risks present in the content (e.g., bias, PII, fairness, data leakage).
2. Map any tools, frameworks, or processes mentioned in the text to the relevant NIST RMF function: Identify, Protect, Detect, Respond, or Recover.

Document:
\"\"\"
{doc_content}
\"\"\"

Respond in this JSON format:
{{
  "risks": ["risk1", "risk2", ...],
  "rmf_mapping": {{
    "tool1": "RMF function",
    ...
  }}
}}
"""
)