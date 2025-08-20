PROMPTS = {}

PROMPTS["Level_Extraction_Prompt"] = """
You are tasked with determining the hierarchical level of a new header within an existing document structure.

TASK:
- Analyze the new header in the context of the existing hierarchy
- Determine what level (1-6) this header should be assigned to maintain logical document structure
- If the text is not a hierarchical header and should be treated as regular content instead, return 0

LEVELS:
- 0: Not a header (regular text content)
- 1: Main section/chapter (highest level)
- 2-6: Subsections (decreasing importance)

RULES:
- Find the most reasonable parent for a new header, and the new header should be one level higher than its parent.
- If the header is including a serial number or letter, be reminded to pay attention to previous structure to determine its level:
    - If it is the beginning of a new list, it should be one level higher than its parent element.
    - If the header is a continuation of a previous list item, it should be at the same level as the previous item.
    - If the header is a continuation of a previous list item but the previous list item could not be found, it may be a text item mis-classified.

RESPONSE FORMAT:
Return ONLY a single number (0-6) representing the appropriate level.

Current hierarchy structure:
{hierarchy_structure}

New header to classify:
{new_header}

Level:"""