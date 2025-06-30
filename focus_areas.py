"""
focus_areas.py - Conversation Focus Areas and Themes

This file contains predefined focus areas that can be used to anchor 
podcast conversations around specific themes or perspectives.
"""

FOCUS_AREAS = {
    "None": {
        "name": "No Specific Focus",
        "description": "General discussion without specific thematic constraints",
        "prompt_modifier": ""
    },
    
"llms_hpss_research_methodology": {
    "name": "LLMs as Methodological Tools in HPSS Research",
    "description": "Focus specifically on methodological applications of LLMs in the history and philosophy and sociology of science (HPSS)",
    "prompt_modifier": """
**CRITICAL FOCUS REQUIREMENT**: This conversation must be specifically anchored around Large Language Models (LLMs) as methodological research tools within the history and philosophy and sociology of science (HPSS) research workflows.

The discussion should explore:
- **Research Workflow Integration**: How LLMs can be integrated into existing HPSS research methodologies
- **Literature Review Assistance**: Using LLMs for systematic literature searches, citation analysis, and identifying research gaps
- **Data Analysis Applications**: Text analysis, coding qualitative data, identifying patterns in historical documents
- **Hypothesis Generation**: How LLMs can help formulate research questions and theoretical frameworks
- **Research Design Support**: Assistance with survey design, interview guides, and research protocols
- **Writing and Analysis**: Support for academic writing, argument development, and critical analysis
- **Source Evaluation**: Using LLMs to assess source credibility and identify potential biases
- **Cross-linguistic Research**: Translation assistance and cross-cultural analysis capabilities
- **Methodological Rigor**: Ensuring scientific validity when incorporating AI tools into HPSS research
- **Best Practices**: Established protocols for responsible LLM use in academic research

DO NOT focus on:
- LLMs as objects of study themselves (unless directly relevant to their methodological use)
- General AI technology discussions without clear methodological applications
- Computer science or engineering aspects of LLMs
- Commercial applications outside academic research contexts
- LLMs as creative writing tools (unless for research communication)

CRITICAL PERSPECTIVE: Frame all discussions through the lens of "How does this help HPSS researchers conduct better, more rigorous research?" Every technical detail should connect back to practical methodological applications in humanities, philosophy, and social sciences contexts.

Ensure the guest speaks as a researcher who actively uses these tools in their HPSS work, not as a technologist explaining how LLMs work.
"""
},

"llms_digital_humanities_methods": {
    "name": "LLMs in Digital Humanities Methodology", 
    "description": "Focus on LLMs as tools for digital humanities research methods and computational approaches to humanistic inquiry",
    "prompt_modifier": """
**CRITICAL FOCUS REQUIREMENT**: This conversation must center on Large Language Models as tools within Digital Humanities methodological frameworks.

The discussion should explore:
- **Computational Text Analysis**: Using LLMs for close and distant reading approaches
- **Digital Archive Processing**: Automated analysis of large textual corpora and historical documents
- **Cultural Analytics**: Applying LLMs to study cultural patterns and literary trends
- **Multilingual Humanities**: Cross-linguistic analysis and comparative literature studies
- **Digital Philology**: Using LLMs for manuscript analysis and textual scholarship
- **Network Analysis**: Extracting and analyzing relationships from humanities texts
- **Digital Preservation**: How LLMs can assist in digitizing and preserving cultural heritage
- **Visualization Integration**: Combining LLM analysis with humanities data visualization
- **Collaborative Annotation**: LLM-assisted scholarly annotation and markup
- **Ethical Considerations**: Responsible use of AI in humanities scholarship

Emphasize practical applications, methodological considerations, and scholarly rigor specific to digital humanities research contexts.
"""
},
    
    "ai_ethics_policy": {
        "name": "AI Ethics and Policy Implications",
        "description": "Focus on ethical considerations and policy implications of AI technologies",
        "prompt_modifier": """
**CRITICAL FOCUS REQUIREMENT**: This conversation must center on the ethical and policy implications of the content discussed.

The discussion should explore:
- Ethical considerations and moral implications
- Policy recommendations and regulatory frameworks
- Societal impact and governance challenges
- Rights, responsibilities, and stakeholder perspectives
- Implementation challenges for ethical AI practices

Frame all technical details through the lens of ethics and policy rather than purely technical or commercial perspectives.
"""
    },
    
    "practical_implementation": {
        "name": "Practical Implementation and Applications",
        "description": "Focus on real-world applications, implementation challenges, and practical considerations",
        "prompt_modifier": """
**CRITICAL FOCUS REQUIREMENT**: This conversation must emphasize practical implementation and real-world applications.

The discussion should explore:
- Concrete use cases and practical applications
- Implementation challenges and solutions
- Cost-benefit analysis and resource requirements
- Step-by-step approaches and best practices
- Real-world examples and case studies
- Barriers to adoption and how to overcome them

Prioritize actionable insights over theoretical discussions.
"""
    },
    
    "historical_context": {
        "name": "Historical Context and Evolution",
        "description": "Focus on historical development, evolution, and lessons from the past",
        "prompt_modifier": """
**CRITICAL FOCUS REQUIREMENT**: This conversation must be anchored in historical context and evolutionary perspectives.

The discussion should explore:
- Historical development and key milestones
- Evolution of ideas, technologies, or practices over time
- Lessons learned from past successes and failures
- Comparison with historical precedents
- How current developments fit into broader historical patterns
- What history can teach us about future directions

Frame contemporary issues through the lens of historical understanding.
"""
    },
    
    "interdisciplinary_connections": {
        "name": "Interdisciplinary Connections",
        "description": "Focus on connections across disciplines and cross-domain insights",
        "prompt_modifier": """
**CRITICAL FOCUS REQUIREMENT**: This conversation must emphasize interdisciplinary connections and cross-domain insights.

The discussion should explore:
- Connections between different fields and disciplines
- How insights from one domain apply to others
- Collaborative opportunities across disciplines
- Shared challenges and common solutions
- Cross-pollination of ideas and methods
- Breaking down silos between fields

Actively seek out and highlight interdisciplinary perspectives and applications.
"""
    },
    
    "future_implications": {
        "name": "Future Implications and Scenarios",
        "description": "Focus on future trends, implications, and scenario planning",
        "prompt_modifier": """
**CRITICAL FOCUS REQUIREMENT**: This conversation must be oriented toward future implications and scenario planning.

The discussion should explore:
- Future trends and developments
- Potential scenarios and their implications
- Long-term consequences and considerations
- Emerging opportunities and challenges
- Preparation strategies for different futures
- Uncertainty and risk assessment

Emphasize forward-looking perspectives and strategic thinking about what's to come.
"""
    },
    
    "critical_analysis": {
        "name": "Critical Analysis and Debate",
        "description": "Focus on critical examination, counterarguments, and balanced analysis",
        "prompt_modifier": """
**CRITICAL FOCUS REQUIREMENT**: This conversation must emphasize critical analysis and examination of different perspectives.

The discussion should explore:
- Critical examination of assumptions and claims
- Counterarguments and alternative viewpoints
- Limitations, weaknesses, and potential problems
- Balanced analysis of pros and cons
- Questioning conventional wisdom
- Examining biases and blind spots

Maintain a healthy skepticism and ensure multiple perspectives are considered.
"""
    },
    
# You can also create project-specific focus areas:

"archival_research_llms": {
    "name": "LLMs for Archival and Historical Research",
    "description": "Focus on using LLMs specifically for archival research, historical document analysis, and primary source investigation",
    "prompt_modifier": """
**CRITICAL FOCUS REQUIREMENT**: This conversation must focus on Large Language Models as tools for archival research and historical document analysis.

The discussion should explore:
- **Document Transcription**: OCR error correction and manuscript transcription assistance
- **Historical Context Analysis**: Understanding historical documents within their temporal context
- **Named Entity Recognition**: Identifying people, places, and events in historical texts
- **Chronological Analysis**: Dating documents and understanding temporal relationships
- **Source Comparison**: Comparing multiple primary sources and identifying discrepancies
- **Language Evolution**: Analyzing how language has changed over time in historical documents
- **Research Discovery**: Finding relevant sources and making archival connections
- **Metadata Generation**: Creating detailed cataloging information for archival materials
- **Bias Detection**: Identifying potential biases in historical sources and accounts
- **Research Validation**: Cross-referencing findings across multiple archival sources

Focus specifically on how these tools enhance traditional archival research methods rather than replacing historian expertise.
"""
}

}


# Helper function to get focus choices for UI
def get_focus_choices():
    """Return a list of focus area choices for the UI dropdown."""
    return [(key, focus["name"]) for key, focus in FOCUS_AREAS.items()]

def get_focus_names():
    """Return a list of focus area names for the UI dropdown."""
    return [focus["name"] for focus in FOCUS_AREAS.values()]

def get_focus_modifier(focus_key: str) -> str:
    """Get the prompt modifier for a specific focus area."""
    if focus_key in FOCUS_AREAS:
        return FOCUS_AREAS[focus_key]["prompt_modifier"]
    return ""

def get_focus_description(focus_key: str) -> str:
    """Get the description for a specific focus area."""
    if focus_key in FOCUS_AREAS:
        return FOCUS_AREAS[focus_key]["description"]
    return ""

# Function to add custom focus areas (for future extensibility)
def add_custom_focus(key: str, name: str, description: str, prompt_modifier: str):
    """Add a custom focus area (useful for extending the system)."""
    FOCUS_AREAS[key] = {
        "name": name,
        "description": description,
        "prompt_modifier": prompt_modifier
    }