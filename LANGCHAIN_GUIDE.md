# LangChain Integration Guide

## 🤔 What is LangChain?

**LangChain** is a framework that makes building AI applications MUCH easier. Think of it as **scaffolding for AI**—it handles the messy parts so you can focus on the logic.

## 📊 Current vs LangChain Comparison

### **Without LangChain (Current `ai_personalizer.py`):**

```python
# ❌ Manual prompt building
prompt = f"""
You are an expert...

Context: {context}
Base template: {template}

Return JSON: {{"body": "...", "talking_points": [...]}}
"""

# ❌ Direct API call
response = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[...]
)

# ❌ Manual JSON parsing (can break!)
try:
    result = json.loads(response.choices[0].message.content)
except:
    # Handle error...
```

**Problems:**
- 🔴 Lots of string formatting
- 🔴 Manual error handling
- 🔴 Hard to reuse prompts
- 🔴 JSON parsing can fail
- 🔴 Can't chain operations
- 🔴 No retry logic

---

### **With LangChain (New `ai_personalizer_langchain.py`):**

```python
# ✅ Reusable template
template = PromptTemplate(
    input_variables=["company", "context"],
    template="Personalize email for {company}. Context: {context}"
)

# ✅ Structured output (automatic parsing!)
class PersonalizedEmail(BaseModel):
    body: str
    talking_points: List[str]
    confidence_score: float

parser = PydanticOutputParser(pydantic_object=PersonalizedEmail)

# ✅ Chain with automatic retry
chain = LLMChain(llm=llm, prompt=template)
result = chain.run(company="Acme", context="...")

# ✅ Automatic parsing - guaranteed structure!
email = parser.parse(result)
print(email.body)  # Always works!
```

**Benefits:**
- ✅ Clean, reusable templates
- ✅ Automatic error handling & retries
- ✅ Structured output (no JSON parsing headaches)
- ✅ Chain multiple AI operations
- ✅ Memory for context
- ✅ Much easier to maintain

## 🎯 How We Use LangChain in This Project

### **1. Prompt Templates**

**Before (messy string formatting):**
```python
def generate_opening(self, contact):
    name = contact['name']
    company = contact['company']
    prompt = f"""
Write an opening line for {name} at {company}.
Make it personal.
Reference their recent news.
Keep it under 40 words.
"""
```

**After (clean LangChain template):**
```python
opening_template = PromptTemplate(
    input_variables=["name", "company", "news"],
    template="""Write an opening line for {name} at {company}.
Recent news: {news}
Keep it under 40 words and reference the news."""
)

# Reusable!
chain = LLMChain(llm=llm, prompt=opening_template)
result = chain.run(name="John", company="Acme", news="Raised $10M")
```

---

### **2. Structured Outputs (Pydantic Models)**

**Before (unreliable JSON parsing):**
```python
response = openai.chat(...)
result = json.loads(response.content)  # Can break!

body = result['body']  # KeyError if missing!
points = result.get('talking_points', [])  # Manual defaults
```

**After (guaranteed structure):**
```python
# Define schema
class PersonalizedEmail(BaseModel):
    body: str = Field(description="Email body")
    talking_points: List[str] = Field(description="Key points")
    confidence_score: float = Field(description="0-1 confidence")

# Parse with validation
parser = PydanticOutputParser(pydantic_object=PersonalizedEmail)
email = parser.parse(ai_response)

# Always has these fields, guaranteed!
print(email.body)           # Always a string
print(email.talking_points) # Always a list
print(email.confidence_score) # Always a float
```

---

### **3. Chaining Multiple Operations**

**The Power of LangChain: Chain multiple AI calls together!**

```python
# Step 1: Analyze company data
analyze_chain = LLMChain(
    llm=llm,
    prompt=PromptTemplate(
        input_variables=["scraped_data"],
        template="Analyze this company: {scraped_data}"
    ),
    output_key="insights"
)

# Step 2: Generate talking points from analysis
talking_points_chain = LLMChain(
    llm=llm,
    prompt=PromptTemplate(
        input_variables=["insights"],
        template="Generate 3 talking points from: {insights}"
    ),
    output_key="talking_points"
)

# Step 3: Write email using both
email_chain = LLMChain(
    llm=llm,
    prompt=PromptTemplate(
        input_variables=["insights", "talking_points", "name"],
        template="""Write email to {name}.
Insights: {insights}
Points: {talking_points}"""
    ),
    output_key="email"
)

# Chain them together! One call does all 3 steps
overall_chain = SequentialChain(
    chains=[analyze_chain, talking_points_chain, email_chain],
    input_variables=["scraped_data", "name"],
    output_variables=["insights", "talking_points", "email"]
)

# Run entire pipeline
result = overall_chain({
    "scraped_data": company_data,
    "name": "John Smith"
})

# Get all outputs
insights = result['insights']
points = result['talking_points']
email = result['email']
```

**This is impossible to do cleanly with direct OpenAI calls!**

---

### **4. Memory & Context**

LangChain can remember previous interactions:

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()

# First contact
result1 = personalize_email(contact1, memory=memory)

# Second contact - AI remembers tone/style from first!
result2 = personalize_email(contact2, memory=memory)

# Maintains consistency across batch
```

---

### **5. Automatic Retries**

```python
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    temperature=0.7,
    max_retries=3,  # Automatic retry on failure!
    request_timeout=30
)

# If OpenAI API fails, LangChain automatically retries 3 times
chain = LLMChain(llm=llm, prompt=template)
result = chain.run(...)  # More reliable
```

## 🚀 Complete Example: With vs Without LangChain

### **Scenario:** Generate personalized email with talking points

### **WITHOUT LangChain (Current):**

```python
def personalize_email(contact, scraped_data, template):
    # Step 1: Build prompt manually
    prompt = f"""
    Generate personalized email.
    
    Name: {contact['name']}
    Company: {contact['company']}
    Description: {scraped_data.get('description', '')}
    News: {', '.join(scraped_data.get('recent_news', []))}
    
    Template: {template}
    
    Return JSON with:
    {{"body": "email text", "talking_points": ["point1", "point2"]}}
    """
    
    # Step 2: Call OpenAI
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert..."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Step 3: Parse JSON (can fail!)
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Step 4: Validate (manual)
        if 'body' not in result:
            raise ValueError("Missing body")
        
        return result
        
    except json.JSONDecodeError:
        # AI didn't return valid JSON
        return {"body": template, "talking_points": []}
    except Exception as e:
        # Something went wrong
        print(f"Error: {e}")
        return {"body": template, "talking_points": []}
```

**Lines of code:** ~40  
**Error handling:** Manual  
**Reusable:** ❌  
**Reliable:** ⚠️ (JSON parsing can break)

---

### **WITH LangChain:**

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel

# Define output structure (once)
class PersonalizedEmail(BaseModel):
    body: str
    talking_points: List[str]

# Create parser (once)
parser = PydanticOutputParser(pydantic_object=PersonalizedEmail)

# Create template (once, reusable!)
template = PromptTemplate(
    input_variables=["name", "company", "description", "news", "template"],
    template="""Generate personalized email.
    
Name: {name}
Company: {company}
Description: {description}
Recent News: {news}
Base Template: {template}

{format_instructions}
""",
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# Create chain (once)
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7, max_retries=3)
chain = LLMChain(llm=llm, prompt=template)

# Use it (simple!)
def personalize_email(contact, scraped_data, template):
    result = chain.run(
        name=contact['name'],
        company=contact['company'],
        description=scraped_data.get('description', ''),
        news=', '.join(scraped_data.get('recent_news', [])),
        template=template
    )
    
    # Automatic parsing, guaranteed structure!
    email = parser.parse(result)
    return {
        "body": email.body,
        "talking_points": email.talking_points
    }
```

**Lines of code:** ~15 (setup once, use many times)  
**Error handling:** Automatic  
**Reusable:** ✅ (template + chain)  
**Reliable:** ✅ (structured output)

## 📦 Installation

Add to `requirements.txt`:
```
langchain>=0.1.0
langchain-openai>=0.0.5
```

Install:
```bash
pip install langchain langchain-openai
```

## 🎓 Key LangChain Concepts

| Concept | What It Does | Example |
|---------|-------------|---------|
| **PromptTemplate** | Reusable prompt with variables | `PromptTemplate(template="Hi {name}")` |
| **LLMChain** | Link LLM with prompt | `LLMChain(llm=llm, prompt=template)` |
| **OutputParser** | Parse AI response into structure | `PydanticOutputParser(pydantic_object=Model)` |
| **SequentialChain** | Chain multiple operations | `SequentialChain(chains=[step1, step2, step3])` |
| **Memory** | Remember context across calls | `ConversationBufferMemory()` |
| **Agents** | Let AI make decisions | `initialize_agent(tools, llm)` |

## 🔄 Data Flow with LangChain

```
Contact Data + Scraped Data
         ↓
┌──────────────────────────┐
│  PromptTemplate          │
│  - Variables filled in   │
│  - Formatted prompt      │
└──────────┬───────────────┘
           ↓
┌──────────────────────────┐
│  LLMChain                │
│  - Send to OpenAI        │
│  - Automatic retry       │
│  - Get response          │
└──────────┬───────────────┘
           ↓
┌──────────────────────────┐
│  OutputParser            │
│  - Parse to Pydantic     │
│  - Validate structure    │
│  - Return typed object   │
└──────────┬───────────────┘
           ↓
    Structured Result!
    {
      body: str,
      talking_points: List[str],
      confidence: float
    }
```

## 🎯 Which Should You Use?

| Feature | Direct OpenAI | LangChain |
|---------|--------------|-----------|
| **Simple use case** | ✅ Good enough | Overkill |
| **Complex chains** | ❌ Hard to maintain | ✅ Built for this |
| **Structured output** | ⚠️ Manual parsing | ✅ Automatic |
| **Reusability** | ❌ Copy-paste code | ✅ Templates |
| **Error handling** | ❌ Write yourself | ✅ Built-in |
| **Memory/Context** | ❌ Manual | ✅ Built-in |
| **Learning curve** | Low | Medium |

## 💡 Recommendation

**For this project:**

✅ **Use LangChain** because:
1. We have **complex multi-step personalization** (scrape → analyze → personalize)
2. We need **structured outputs** (opening, body, talking points, confidence)
3. We want **reusable prompts** across different emails
4. We need **reliable parsing** (can't have JSON errors in production)
5. **Batch processing** benefits from memory/consistency

**Both implementations are available:**
- `ai_personalizer.py` - Direct OpenAI (simpler, currently active)
- `ai_personalizer_langchain.py` - LangChain (more powerful, better for production)

To switch:
```python
# Old way
from modules.ai_personalizer import AIPersonalizer

# New way (LangChain)
from modules.ai_personalizer_langchain import LangChainPersonalizer
```

Both have the same interface, so you can swap them easily! 🔄
