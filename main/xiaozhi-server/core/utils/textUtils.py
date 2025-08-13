def get_string_no_punctuation_or_emoji(s):
    """Remove leading and trailing spaces, punctuation marks and emojis from string"""
    chars = list(s)
    
    # Process characters at the beginning
    start = 0
    while start < len(chars) and is_punctuation_or_emoji(chars[start]):
        start += 1
    
    # Process characters at the end
    end = len(chars) - 1
    while end >= start and is_punctuation_or_emoji(chars[end]):
        end -= 1
    
    return "".join(chars[start : end + 1])

def is_punctuation_or_emoji(char):
    """Check if character is space, specified punctuation or emoji"""
    # Define Chinese and English punctuation to be removed (including full-width/half-width)
    punctuation_set = {
        "，", ",",  # Chinese comma + English comma
        "。", ".",  # Chinese period + English period
        "！", "!",  # Chinese exclamation mark + English exclamation mark
        "-", "－",  # English hyphen + Chinese full-width dash
        "、",       # Chinese pause mark
        "[", "]",   # Square brackets
        "【", "】", # Chinese square brackets
    }
    
    if char.isspace() or char in punctuation_set:
        return True
    
    # Check emojis (preserve original logic)
    code_point = ord(char)
    emoji_ranges = [
        (0x1F600, 0x1F64F),
        (0x1F300, 0x1F5FF),
        (0x1F680, 0x1F6FF),
        (0x1F900, 0x1F9FF),
        (0x1FA70, 0x1FAFF),
        (0x2600, 0x26FF),
        (0x2700, 0x27BF),
    ]
    
    return any(start <= code_point <= end for start, end in emoji_ranges)
