"""
Multi-pass transcript generator for creating very long podcasts (5+ pages)
"""

import re
from typing import List, Dict, Any
from utils import generate_script
from schema import MediumDialogue
from prompts import SYSTEM_PROMPT

def split_content_into_sections(text: str, max_section_length: int = 3000) -> List[Dict[str, str]]:
    """Split long content into logical sections for processing."""
    
    # Try to split by headers/sections first
    sections = []
    
    # Look for common section markers
    section_patterns = [
        r'\n#+\s+(.+)',  # Markdown headers
        r'\n\*\*(.+)\*\*',  # Bold headers
        r'\n([A-Z][A-Za-z\s]+):\s*\n',  # Category headers
        r'\n(\d+\.\s+[A-Z][^.]+\.)',  # Numbered sections
    ]
    
    # Try to find natural breakpoints
    paragraphs = text.split('\n\n')
    current_section = ""
    current_title = "Introduction"
    section_count = 1
    
    for i, paragraph in enumerate(paragraphs):
        # Check if this looks like a section header
        is_header = False
        for pattern in section_patterns:
            if re.match(pattern, paragraph):
                is_header = True
                if current_section.strip():
                    sections.append({
                        "title": current_title,
                        "content": current_section.strip(),
                        "section_number": len(sections) + 1
                    })
                current_title = re.sub(r'[#*:\d\.\s]+', '', paragraph).strip()[:50]
                current_section = ""
                break
        
        if not is_header:
            current_section += paragraph + "\n\n"
            
            # If section gets too long, force a break
            if len(current_section) > max_section_length:
                sections.append({
                    "title": current_title,
                    "content": current_section.strip(),
                    "section_number": len(sections) + 1
                })
                current_title = f"Section {len(sections) + 2}"
                current_section = ""
    
    # Add the last section
    if current_section.strip():
        sections.append({
            "title": current_title,
            "content": current_section.strip(),
            "section_number": len(sections) + 1
        })
    
    # If no natural sections found, split by length
    if len(sections) <= 1:
        sections = []
        words = text.split()
        current_chunk = ""
        
        for i, word in enumerate(words):
            current_chunk += word + " "
            if len(current_chunk) > max_section_length or i == len(words) - 1:
                sections.append({
                    "title": f"Section {len(sections) + 1}",
                    "content": current_chunk.strip(),
                    "section_number": len(sections) + 1
                })
                current_chunk = ""
    
    return sections

def generate_section_dialogue(section: Dict[str, str], context: str = "") -> List[Dict[str, str]]:
    """Generate detailed dialogue for a specific section."""
    
    section_prompt = f"""{SYSTEM_PROMPT}

**SECTION-SPECIFIC INSTRUCTIONS:**
- This is part {section['section_number']} of a longer podcast discussion
- Focus specifically on: {section['title']}
- Create detailed, in-depth dialogue about this section
- Include follow-up questions and explanations
- Aim for 12-20 exchanges for this section alone
- Make sure the guest provides specific details and examples

**CONTEXT:** {context}

**SECTION FOCUS:** Create dialogue specifically discussing "{section['title']}" in detail."""

    try:
        result = generate_script(
            system_prompt=section_prompt,
            input_text=section['content'],
            output_model=MediumDialogue
        )
        
        # Convert to list of dicts for easier handling
        dialogue_items = []
        for item in result.dialogue:
            dialogue_items.append({
                "speaker": item.speaker,
                "text": item.text
            })
        
        return dialogue_items
    
    except Exception as e:
        print(f"Error generating section dialogue: {e}")
        return []

def generate_long_transcript(text: str, target_length: str = "Extended (15+ min)") -> Dict[str, Any]:
    """Generate a very long transcript by processing content in sections."""
    
    print("🔄 Generating long transcript using multi-pass approach...")
    
    # Split content into sections
    sections = split_content_into_sections(text, max_section_length=2500)
    print(f"📊 Split content into {len(sections)} sections")
    
    # Generate opening
    opening_prompt = f"""{SYSTEM_PROMPT}

**OPENING SECTION INSTRUCTIONS:**
- This is the opening of a comprehensive podcast discussion
- Introduce the topic and guest enthusiastically  
- Provide a brief overview of what will be covered
- Create 3-5 exchanges for the introduction
- Set up the detailed discussion that will follow

**SECTIONS TO BE COVERED:**
{', '.join([section['title'] for section in sections[:5]])}"""

    print("🎙️ Generating opening section...")
    try:
        opening_result = generate_script(
            system_prompt=opening_prompt,
            input_text=f"Introduction to: {text[:1000]}",
            output_model=MediumDialogue
        )
        
        combined_dialogue = []
        guest_name = opening_result.name_of_guest
        scratchpad_parts = [opening_result.scratchpad]
        
        # Add opening dialogue
        for item in opening_result.dialogue:
            combined_dialogue.append({
                "speaker": item.speaker,
                "text": item.text
            })
        
    except Exception as e:
        print(f"Error generating opening: {e}")
        combined_dialogue = [
            {"speaker": "Host (Jane)", "text": "Welcome to our comprehensive podcast discussion!"},
            {"speaker": "Guest", "text": "Thank you for having me. I'm excited to explore this topic in detail."}
        ]
        guest_name = "Expert Guest"
        scratchpad_parts = ["Opening section"]
    
    # Generate detailed sections
    for i, section in enumerate(sections[:4]):  # Limit to 4 sections to stay within reasonable length
        print(f"🔄 Generating section {i+1}/{min(len(sections), 4)}: {section['title']}")
        
        # Create context for this section
        context = f"This is part {i+1} of our discussion. Previous topics covered: {', '.join([item['title'] for item in sections[:i]])}"
        
        section_dialogue = generate_section_dialogue(section, context)
        
        if section_dialogue:
            # Add transition from host
            if i > 0:
                transition_text = f"Now let's explore {section['title']}. Can you tell us more about this?"
                combined_dialogue.append({
                    "speaker": "Host (Jane)", 
                    "text": transition_text
                })
            
            # Add section dialogue
            combined_dialogue.extend(section_dialogue)
            scratchpad_parts.append(f"Section {i+1}: {section['title']}")
    
    # Generate closing
    print("🎙️ Generating closing section...")
    closing_dialogue = [
        {
            "speaker": "Host (Jane)",
            "text": "This has been a fascinating and comprehensive discussion. Before we wrap up, what would you say is the most important takeaway for our listeners?"
        },
        {
            "speaker": "Guest", 
            "text": "I think the key point is how all these different aspects we've discussed connect together to form a complete picture. It's been a pleasure sharing these insights with your audience."
        },
        {
            "speaker": "Host (Jane)",
            "text": "Thank you so much for this in-depth conversation. This has been incredibly informative for our listeners."
        }
    ]
    
    combined_dialogue.extend(closing_dialogue)
    
    print(f"✅ Generated {len(combined_dialogue)} total exchanges")
    
    return {
        "scratchpad": " | ".join(scratchpad_parts),
        "name_of_guest": guest_name,
        "dialogue": combined_dialogue,
        "sections_processed": len(sections),
        "total_exchanges": len(combined_dialogue)
    }

def estimate_page_count(dialogue_items: List[Dict[str, str]]) -> float:
    """Estimate how many pages the transcript will be."""
    total_chars = sum(len(item["text"]) for item in dialogue_items)
    # Rough estimate: 2500-3000 characters per page including speaker labels and formatting
    return total_chars / 2750