# Child Profile Integration: Approach Comparison

## 📋 Two Approaches

---

## ❌ Approach 1: Dynamic Injection (OLD - Removed)

### How it worked:

1. **Database** - Store clean prompt without templates
2. **Manager API** - Inject templates dynamically when fetched
3. **LiveKit** - Render templates with actual values

### Code:
```java
// ConfigServiceImpl.java:479-507
String systemPrompt = agent.getSystemPrompt();  // Clean prompt from DB

if (device.getKidId() != null) {
    // Build template section
    String childProfileSection = "{% if child_name %}...";

    // Inject it
    systemPrompt = systemPrompt.replace("<identity>",
                                       "<identity>" + childProfileSection);
}

return systemPrompt;  // With templates injected
```

### Pros:
- ✅ Database prompts stay clean
- ✅ Template injection controlled by code
- ✅ Easy to update template logic without touching database

### Cons:
- ❌ Extra complexity in Java code
- ❌ Template code duplicated in Java strings
- ❌ Harder to test and visualize
- ❌ Mixing concerns (data access + template building)

---

## ✅ Approach 2: Static Template (NEW - Recommended)

### How it works:

1. **Database** - Store prompt WITH templates already included
2. **Manager API** - Simply return prompt as-is
3. **LiveKit** - Render templates with actual values

### Code:
```java
// ConfigServiceImpl.java:460-481 (Simplified)
String systemPrompt = agent.getSystemPrompt();  // Already has templates
return systemPrompt;  // Return as-is
```

### Pros:
- ✅ Much simpler code
- ✅ Single source of truth (database)
- ✅ Easy to edit templates via SQL or admin UI
- ✅ Clear separation of concerns
- ✅ Easier to test and debug
- ✅ No Java code changes needed for template updates

### Cons:
- ⚠️ Need to update database once (one-time task)
- ⚠️ Template visible in database (but that's fine)

---

## 🔄 Migration Steps

### Step 1: Update Database Prompt

Run SQL script: `update_agent_prompt_with_template.sql`

```sql
UPDATE ai_agent
SET system_prompt = '<identity>

{% if child_name %}
🎯 **Child Profile:**
- **Name:** {{ child_name }}
...
{% endif %}

You are Cheeko...
</identity>
...'
WHERE id = 'your_agent_id';
```

### Step 2: Simplify Java Code

Already done! Code updated in `ConfigServiceImpl.java:460-481`

### Step 3: Test

```bash
# Test prompt fetching
python test_prompt_rendering.py

# Verify templates are in prompt
python test_prompt_with_kid_profile.py
```

---

## 📊 Comparison Table

| Aspect | Dynamic Injection (OLD) | Static Template (NEW) |
|--------|------------------------|----------------------|
| **Code Complexity** | High (50 lines) | Low (20 lines) |
| **Database** | Clean prompt | Prompt with templates |
| **Maintainability** | Hard (need Java changes) | Easy (just SQL update) |
| **Testing** | Complex | Simple |
| **Debugging** | Difficult | Easy |
| **Flexibility** | Template in code | Template in DB |
| **Performance** | Slightly slower (injection) | Faster (direct return) |
| **Best Practice** | ❌ Mixing concerns | ✅ Separation of concerns |

---

## 🎯 Recommendation

**Use Approach 2 (Static Template)** because:

1. **Simpler** - Less code to maintain
2. **Clearer** - Template is where it should be (in data)
3. **Faster** - No runtime injection overhead
4. **Flexible** - Easy to update via database
5. **Standard** - Templates belong in data, not code

---

## 📝 Template Format

The database prompt should contain:

```
<identity>

{% if child_name %}
🎯 **Child Profile:**
- **Name:** {{ child_name }}
{% if child_age %}- **Age:** {{ child_age }} years old{% endif %}
{% if age_group %}- **Age Group:** {{ age_group }}{% endif %}
{% if child_gender %}- **Gender:** {{ child_gender }}{% endif %}
{% if child_interests %}- **Interests:** {{ child_interests }}{% endif %}

**Important:** Always address this child by their name ({{ child_name }})...
{% endif %}

Your actual agent instructions...
</identity>
```

### Key Points:

- `{% if child_name %}` - Conditional wrapper (section only shows if child exists)
- `{{ child_name }}` - Variable placeholder (replaced by LiveKit)
- `{% endif %}` - End of conditional block
- Works for ALL devices (shows child info if assigned, hidden if not)

---

## 🔧 Files Updated

### Removed Dynamic Injection:
- ✅ `ConfigServiceImpl.java:460-481` - Simplified to just return prompt

### Created:
- ✅ `UPDATED_AGENT_PROMPT_TEMPLATE.txt` - Template file for reference
- ✅ `update_agent_prompt_with_template.sql` - SQL script to update database
- ✅ `APPROACH_COMPARISON.md` - This file

### No Changes Needed:
- ✅ `main.py` - LiveKit rendering logic stays the same
- ✅ `database_helper.py` - Child profile fetching stays the same
- ✅ All DTOs, Controllers, Services - No changes needed

---

## ✅ Result

After migration:

1. **Database** contains prompt with templates
2. **Manager API** returns prompt as-is (no injection)
3. **LiveKit** renders templates with child data
4. **Agent** receives personalized prompt

**Everything works the same**, but the code is **much simpler**!

---

**Created:** 2025-10-09
**Status:** ✅ Migration Complete
**Approach:** Static Template (Recommended)
