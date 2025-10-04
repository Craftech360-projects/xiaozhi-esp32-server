# Mode Name Normalization - Implementation Plan (Option 3)

## Overview
Handle speech-to-text transcript variations for mode switching using simple normalization and alias mapping.

---

## Problem
When users say "storyteller", the STT transcript may vary:
- "story teller" (space)
- "Story Teller" (capitalization)
- "storyteler" (typo)
- "story mode"

Current implementation passes raw transcript to API, causing failures.

---

## Solution Architecture

### 1. **Mode Alias Dictionary**
Create a mapping of canonical mode names to their variations:

```python
MODE_ALIASES = {
    "cheeko": ["chiko", "chico", "cheeko mode", "default mode"],
    "storyteller": ["story teller", "story-teller", "story mode", "story time"],
    "studyhelper": ["study helper", "study mode", "study buddy"],
    # ... more modes
}
```

### 2. **Normalization Function**
Create `normalize_mode_name(mode_input: str) -> str`:

**Steps:**
1. Convert to lowercase
2. Strip whitespace
3. Replace hyphens/underscores with spaces
4. Check direct match against canonical names
5. Check match against all aliases
6. Return canonical name if matched, else original input

### 3. **Integration Point**
Modify `update_agent_mode()` function in `src/agent/main_agent.py:65`

**Before API call** (currently line 106):
```python
# Current:
payload = {
    "agentId": agent_id,
    "modeName": mode_name  # Raw input
}

# After:
normalized_mode = normalize_mode_name(mode_name)
payload = {
    "agentId": agent_id,
    "modeName": normalized_mode  # Normalized
}
```

---

## Code Changes Required

### File: `src/agent/main_agent.py`

**Location 1**: After imports (line 14)
- Add `MODE_ALIASES` dictionary
- Add `normalize_mode_name()` function

**Location 2**: In `update_agent_mode()` method (line 106)
- Call normalization before creating payload
- Log the normalization result

---

## Configuration

### Mode Aliases to Add
Based on common variations:

```python
MODE_ALIASES = {
    "cheeko": [
        "chiko", "chico", "cheeko mode",
        "default", "normal mode"
    ],
    "storyteller": [
        "story teller", "story-teller", "story mode",
        "story time", "storytelling", "tell stories"
    ],
    "studyhelper": [
        "study helper", "study-helper", "study mode",
        "study buddy", "learning mode", "homework helper"
    ],
    "teacher": [
        "teacher mode", "teaching mode",
        "tutor", "tutor mode", "educator"
    ],
    "companion": [
        "companion mode", "friend mode",
        "buddy mode", "friend"
    ]
}
```

---

## Normalization Logic

```
Input: "Story Teller"
  ↓
Lowercase: "story teller"
  ↓
Strip/Clean: "story teller"
  ↓
Check Direct Match: No match in ["cheeko", "storyteller", ...]
  ↓
Check Aliases: Found in storyteller aliases
  ↓
Output: "storyteller"
```

---

## Logging Strategy

Add logs at key points:
- **Match found**: `🔍 Matched 'story teller' → 'storyteller' via alias`
- **No match**: `⚠️ No alias match for 'xyz', passing as-is`
- **Before API call**: `🔄 Updating agent to mode: {normalized_mode} (from input: {original_input})`

---

## Benefits

✅ **Fast**: No API calls, pure string matching
✅ **Simple**: Easy to add new aliases
✅ **Backward compatible**: Unknown modes pass through unchanged
✅ **No dependencies**: Uses standard Python string operations

---

## Limitations

⚠️ **Manual maintenance**: Must update aliases for new modes
⚠️ **No typo tolerance**: "storytelr" won't match (use fuzzy matching for this)
⚠️ **Exact phrase matching**: Won't handle "I want story mode" (only "story mode")

---

## Testing Scenarios

| User Says | Transcript | Normalized | Result |
|-----------|-----------|------------|--------|
| "storyteller" | "storyteller" | "storyteller" | ✅ Direct match |
| "storyteller" | "story teller" | "storyteller" | ✅ Alias match |
| "storyteller" | "Story Mode" | "storyteller" | ✅ Alias match |
| "study helper" | "study helper" | "studyhelper" | ✅ Alias match |
| "unknown mode" | "unknown mode" | "unknown mode" | ⚠️ Pass to API |

---

## Future Enhancements

**Phase 2 considerations:**
1. Fetch mode list from API dynamically
2. Add fuzzy matching (RapidFuzz) for typo tolerance
3. Add confidence scoring and user confirmation
4. Cache normalized mappings for performance

---

## Implementation Checklist

- [ ] Add `MODE_ALIASES` dictionary after imports
- [ ] Implement `normalize_mode_name()` function
- [ ] Integrate normalization in `update_agent_mode()` before API call
- [ ] Add logging for matches/misses
- [ ] Test with common variations
- [ ] Document mode aliases in code comments
- [ ] Update function tool description to mention supported variations

---

## Example Implementation

### Step 1: Add Mode Aliases Dictionary

```python
# In src/agent/main_agent.py, after line 14 (after imports)

# Mode name aliases for handling transcript variations
MODE_ALIASES = {
    "cheeko": ["chiko", "chico", "cheeko mode", "default mode", "normal mode"],
    "storyteller": ["story teller", "story-teller", "story mode", "story time", "storytelling"],
    "studyhelper": ["study helper", "study-helper", "study mode", "study buddy", "learning mode"],
    "teacher": ["teacher mode", "teaching mode", "tutor", "tutor mode"],
    "companion": ["companion mode", "friend mode", "buddy mode"],
}
```

### Step 2: Add Normalization Function

```python
def normalize_mode_name(mode_input: str) -> str:
    """
    Normalize mode name input to handle transcript variations

    Args:
        mode_input: Raw mode name from speech transcript

    Returns:
        Normalized canonical mode name or original input if no match
    """
    if not mode_input:
        return mode_input

    # Normalize: lowercase, strip whitespace, remove special chars
    normalized = mode_input.lower().strip()
    normalized = normalized.replace("-", " ").replace("_", " ")

    # Direct match first (after normalization)
    for canonical_name in MODE_ALIASES.keys():
        if normalized == canonical_name:
            return canonical_name

    # Check aliases
    for canonical_name, aliases in MODE_ALIASES.items():
        if normalized in [alias.lower() for alias in aliases]:
            logger.info(f"🔍 Matched '{mode_input}' → '{canonical_name}' via alias")
            return canonical_name

    # No match found - return original for backend to handle
    logger.warning(f"⚠️ No alias match found for '{mode_input}', passing as-is")
    return mode_input
```

### Step 3: Integrate in update_agent_mode()

```python
# In update_agent_mode() method, around line 96-106

logger.info(f"🔄 Updating agent {agent_id} to mode: {mode_name}")

# Normalize mode name to handle transcript variations
normalized_mode = normalize_mode_name(mode_name)
if normalized_mode != mode_name:
    logger.info(f"🔄 Mode name normalized: '{mode_name}' → '{normalized_mode}'")

# 4. Call update-mode API
url = f"{manager_api_url}/agent/update-mode"
headers = {
    "Authorization": f"Bearer {manager_api_secret}",
    "Content-Type": "application/json"
}
payload = {
    "agentId": agent_id,
    "modeName": normalized_mode  # Use normalized name instead of raw input
}
```

---

## Maintenance

### Adding New Mode Aliases

When adding a new mode to the system:

1. Add the canonical mode name to `MODE_ALIASES` as a key
2. List all expected variations as array values
3. Test with voice commands
4. Update this README with the new mode

Example:
```python
MODE_ALIASES = {
    # ... existing modes
    "newmode": ["new mode", "new-mode", "activate new mode"],
}
```

---

## Support

For questions or issues:
- Check function implementation in `src/agent/main_agent.py:65`
- Review logs for normalization results
- Add new aliases to `MODE_ALIASES` dictionary as needed
