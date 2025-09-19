- Critically review recently generated code against project requirements
- Use RAG system to validate implementation accuracy and compliance
- Do not add new data to RAG - only query existing knowledge base
- Ask targeted questions to RAG system to obtain validation insights
- Use `lng_llm_rag_search` with both prompt templates for comprehensive review:
  + `critical_analysis` for finding issues, violations, missing components
  + `project_analysis` for verifying implementation matches documented requirements
- Focus queries on specific code sections, patterns, and architectural decisions
- Compare generated code with documented best practices and standards
- Identify gaps between implementation and requirements through RAG queries
- Use retrieved knowledge to improve existing code changes iteratively
- Ask questions about:
  + Compliance with documented architecture patterns
  + Missing error handling or edge cases
  + Security vulnerabilities or GDPR violations
  + Performance optimization opportunities
  + Code structure and organization issues
- Apply RAG insights to refine and correct existing implementations
- Validate each correction against RAG knowledge before applying changes
