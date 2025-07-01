"""
multi_stage_extended.py - Generate very long conversations by chaining multiple dialogues
"""

from typing import List, Dict, Any, Union
from schema import ExtendedDialogue, LongDialogue, DialogueItem
import json

def extract_conversation_summary(dialogue_items: List[DialogueItem]) -> Dict[str, Any]:
    """
    Extract key topics and insights from a completed conversation for context passing.
    """
    
    # Extract topics discussed and key points made
    topics_covered = []
    key_insights = []
    
    for item in dialogue_items:
        text = item.text.lower()
        
        # Simple keyword extraction for topics (could be enhanced with NLP)
        if any(word in text for word in ['discuss', 'explore', 'examine', 'analyze']):
            # This is likely introducing a new topic
            topics_covered.append(item.text[:100] + "...")
        
        if item.speaker == "Guest" and any(word in text for word in ['research', 'study', 'found', 'evidence']):
            key_insights.append(item.text[:150] + "...")
    
    # Get the last few exchanges for natural transition
    recent_context = dialogue_items[-3:] if len(dialogue_items) >= 3 else dialogue_items
    
    return {
        "topics_covered": topics_covered[:5],  # Top 5 topics
        "key_insights": key_insights[:3],      # Top 3 insights
        "recent_context": [{"speaker": item.speaker, "text": item.text} for item in recent_context],
        "conversation_length": len(dialogue_items),
        "guest_name": None  # Will be filled by caller
    }

def generate_conversation_stage(
    stage_number: int,
    original_content: str,
    previous_summaries: List[Dict[str, Any]],
    guest_name: str,
    system_prompt: str,
    call_llm_func, 
    target_length: str = "Long (8-12 min)"
) -> Dict[str, Any]:
    """
    Generate a single conversation stage with context from previous stages.
    """
    
    # Choose dialogue format - use LongDialogue for each stage
    dialogue_format = LongDialogue
    target_exchanges = "25-35"
    
    # Build context-aware system prompt
    if stage_number == 1:
        # First conversation - introductory and broad coverage
        stage_prompt = f"""{system_prompt}

🎯 CONVERSATION STAGE 1 of 3: FOUNDATIONAL DISCUSSION

This is the FIRST part of an extended 3-part conversation. Your goals:
1. Introduce the topic and guest expertise
2. Cover the fundamental concepts and main themes  
3. Establish a foundation for deeper discussion in later stages
4. Aim for {target_exchanges} exchanges

APPROACH:
- Start with introductions and broad overview
- Cover the most important/accessible aspects first
- Leave complex details and implications for later stages
- End with a natural transition suggesting more to explore

CRITICAL: Generate exactly {target_exchanges} exchanges that establish the foundation.
Count your exchanges: 1, 2, 3... up to {target_exchanges.split('-')[0]} minimum."""

    elif stage_number == 2:
        # Second conversation - deeper dive into specifics
        prev_summary = previous_summaries[0]
        recent_context = prev_summary["recent_context"]
        topics_covered = prev_summary["topics_covered"]
        
        stage_prompt = f"""{system_prompt}

🎯 CONVERSATION STAGE 2 of 3: DEEP DIVE ANALYSIS

This is the SECOND part of an extended conversation. Context from Stage 1:

PREVIOUSLY DISCUSSED:
{json.dumps(topics_covered, indent=2)}

RECENT CONTEXT (how Stage 1 ended):
{json.dumps(recent_context, indent=2)}

Your goals for Stage 2:
1. Reference specific points from the previous conversation naturally
2. Go much deeper into technical details and complexities
3. Challenge assumptions and explore nuances  
4. Introduce advanced concepts not covered in Stage 1
5. Aim for {target_exchanges} exchanges

CONVERSATION FLOW:
- Start with: "Building on our earlier discussion about..."
- Reference specific points the guest made previously
- Push for more detailed explanations and examples
- Explore counterarguments and alternative perspectives
- Use phrases like "You mentioned earlier..." or "Expanding on that point..."

AVOID: Simply repeating topics from Stage 1. Go DEEPER, not broader.

CRITICAL: Generate exactly {target_exchanges} exchanges that significantly deepen the analysis."""

    else:  # stage_number == 3
        # Third conversation - implications, applications, future directions
        all_topics = []
        all_insights = []
        for summary in previous_summaries:
            all_topics.extend(summary["topics_covered"])
            all_insights.extend(summary["key_insights"])
        
        stage_prompt = f"""{system_prompt}

🎯 CONVERSATION STAGE 3 of 3: IMPLICATIONS & SYNTHESIS

This is the FINAL part of an extended conversation. Context from previous stages:

ALL TOPICS COVERED SO FAR:
{json.dumps(all_topics[:8], indent=2)}

KEY INSIGHTS FROM PREVIOUS DISCUSSIONS:  
{json.dumps(all_insights[:5], indent=2)}

Your goals for Stage 3:
1. Synthesize insights from the entire conversation
2. Explore real-world applications and implications
3. Discuss future directions and unanswered questions
4. Challenge the guest to connect ideas across topics
5. Provide a satisfying conclusion to the extended discussion
6. Aim for {target_exchanges} exchanges

CONVERSATION FLOW:
- Reference the "journey" of the conversation
- Ask about broader implications: "Given everything we've discussed..."
- Explore practical applications: "How would this apply to..."
- Discuss future research/developments
- Synthesize connections between different topics discussed
- End with key takeaways and future outlook

CRITICAL: Generate exactly {target_exchanges} exchanges that synthesize and conclude the discussion."""

    # Truncate original content to leave room for dialogue generation
    if len(original_content) > 4000:
        content_for_stage = original_content[:4000] + f"\n[Content truncated for Stage {stage_number} generation]"
    else:
        content_for_stage = original_content

    # Generate the conversation stage
    try:
        print(f"   🔄 Calling LLM for Stage {stage_number}...")
        result = call_llm_func(
            system_prompt=stage_prompt,
            text=content_for_stage,
            dialogue_format=dialogue_format
        )
        
        print(f"   ✅ Stage {stage_number} LLM call successful: {len(result.dialogue)} exchanges")
        
        return {
            "stage_number": stage_number,
            "scratchpad": result.scratchpad,
            "name_of_guest": result.name_of_guest,
            "dialogue": result.dialogue,
            "success": True,
            "exchanges_generated": len(result.dialogue)
        }
    
    except Exception as e:
        print(f"   ❌ Stage {stage_number} LLM call failed: {e}")
        return {
            "stage_number": stage_number,
            "error": str(e),
            "success": False,
            "exchanges_generated": 0
        }

def generate_extended_multi_stage(
    original_content: str,
    system_prompt: str,
    call_llm_func, 
    focus_area: str = None
) -> Dict[str, Any]:
    """
    Generate an extended conversation using multiple stages.
    """
    
    print("🎭 Starting Multi-Stage Extended Conversation Generation...")
    
    all_dialogue_items = []
    all_summaries = []
    guest_name = "Expert Guest"
    combined_scratchpad = []
    
    # Generate 3 conversation stages
    for stage in range(1, 4):
        print(f"🎯 Generating Stage {stage}/3...")
        
        stage_result = generate_conversation_stage(
            stage_number=stage,
            original_content=original_content,
            previous_summaries=all_summaries,
            guest_name=guest_name,
            system_prompt=system_prompt,
            call_llm_func=call_llm_func,
            target_length="Long (8-12 min)"
        )
        
        if not stage_result["success"]:
            print(f"❌ Stage {stage} failed: {stage_result.get('error', 'Unknown error')}")
            # Continue with what we have if we have at least one stage
            if stage == 1:
                # If first stage fails, abort multi-stage
                raise Exception(f"Stage 1 failed: {stage_result.get('error', 'Unknown error')}")
            else:
                # If later stages fail, continue with what we have
                break
        
        print(f"✅ Stage {stage} completed: {stage_result['exchanges_generated']} exchanges")
        
        # Update guest name from first successful stage
        if stage == 1 and stage_result["name_of_guest"]:
            guest_name = stage_result["name_of_guest"]
        
        # Collect dialogue items
        stage_dialogue = stage_result["dialogue"]
        
        # Add stage transitions (except for first stage)
        if stage > 1:
            # Add a natural transition
            transition_text = f"Let's dive deeper into some of the aspects we've touched on."
            if stage == 3:
                transition_text = f"As we wrap up our comprehensive discussion, I'd like to explore the broader implications of what we've covered."
            
            transition_item = DialogueItem(
                speaker="Host (Jane)",
                text=transition_text
            )
            all_dialogue_items.append(transition_item)
        
        # Add this stage's dialogue
        all_dialogue_items.extend(stage_dialogue)
        
        # Extract summary for next stage
        if stage < 3:  # Don't need summary for the last stage
            summary = extract_conversation_summary(stage_dialogue)
            summary["guest_name"] = guest_name
            all_summaries.append(summary)
        
        combined_scratchpad.append(f"Stage {stage}: {stage_result['scratchpad']}")
    
    total_exchanges = len(all_dialogue_items)
    print(f"🎉 Multi-stage generation complete: {total_exchanges} total exchanges")
    
    # Create final result
    final_scratchpad = " | ".join(combined_scratchpad)
    if focus_area:
        final_scratchpad += f" | Focus: {focus_area}"
    
    return {
        "scratchpad": final_scratchpad,
        "name_of_guest": guest_name,
        "dialogue": all_dialogue_items,
        "total_exchanges": total_exchanges,
        "stages_completed": len([s for s in all_summaries]) + 1,  # +1 for final stage
        "success": total_exchanges >= 50  # Success if we got at least 50 exchanges
    }

def enhance_for_deep_discussion(stage_prompt: str, stage_number: int) -> str:
    """
    Add Deep Discussion enhancements to stage prompts.
    """
    
    deep_discussion_addon = """

🧠 DEEP DISCUSSION MODE ACTIVATED:

CRITICAL REQUIREMENTS for Academic-Level Discussion:
- Host asks probing, intellectually challenging questions
- Guest provides sophisticated, evidence-based responses
- Challenge assumptions and explore underlying mechanisms
- Use precise academic language while remaining accessible
- Address potential counterarguments and limitations
- Explore interdisciplinary connections
- Push beyond surface-level explanations

CONVERSATION DYNAMICS:
- Host: Acts as well-informed interviewer who won't accept superficial answers
- Guest: Responds as thoughtful expert capable of nuanced analysis
- Both: Engage in intellectual discourse worthy of graduate seminar
- Include moments where host pushes for clarification or challenges points
- Guest acknowledges complexities: "It's more nuanced than that..." or "The research shows mixed results..."

Make this feel like a substantive academic conversation where both participants are genuinely engaged in exploring complex ideas."""

    return stage_prompt + deep_discussion_addon