"""
AI-powered email personalization using LangChain.

This module uses LangChain framework for better:
- Prompt management with templates
- Structured output parsing
- Chain multiple AI operations
- Memory for context
- Error handling and retries

LangChain makes the AI integration more robust, maintainable, and powerful.

Usage:
    from modules.ai_personalizer import AIPersonalizer
    
    ai = AIPersonalizer()
    result = ai.personalize_email(contact, scraped_data, template)
"""

import logging
import json
from typing import Dict, Optional, List

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain, SequentialChain
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from config.settings import Config

logger = logging.getLogger(__name__)


# ============================================
# OUTPUT SCHEMAS (Pydantic Models)
# ============================================

class TalkingPoints(BaseModel):
    """Structured output for talking points."""
    points: List[str] = Field(description="List of 3-5 key talking points")


class PersonalizedOpening(BaseModel):
    """Structured output for opening line."""
    opening: str = Field(description="Personalized opening line for email")
    references: List[str] = Field(description="What specific things were referenced")


class PersonalizedEmail(BaseModel):
    """Complete personalized email structure."""
    opening: str = Field(description="Personalized opening line")
    body: str = Field(description="Main email body with personalization")
    talking_points: List[str] = Field(description="Key points mentioned")
    confidence_score: float = Field(description="Confidence in personalization (0-1)")
    references_used: List[str] = Field(description="What data was used for personalization")


class PersonalizedSubject(BaseModel):
    """Personalized subject line."""
    subject: str = Field(description="Personalized email subject")
    reasoning: str = Field(description="Why this subject was chosen")


# ============================================
# LANGCHAIN PERSONALIZER
# ============================================

class AIPersonalizer:
    """
    AI email personalization using LangChain framework.
    
    Benefits over direct OpenAI calls:
    - Reusable prompt templates
    - Automatic output parsing
    - Chain multiple operations
    - Better error handling
    - Memory management
    """
    
    def __init__(self, temperature: float = 0.7):
        """
        Initialize LangChain personalizer.
        
        Args:
            temperature: AI creativity level (0=deterministic, 1=creative)
        """
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name=Config.OPENAI_MODEL,
            temperature=temperature,
            openai_api_key=Config.OPENAI_API_KEY,
            request_timeout=30,
            max_retries=2  # Automatic retries on failure
        )
        
        # Setup output parsers
        self.talking_points_parser = PydanticOutputParser(pydantic_object=TalkingPoints)
        self.opening_parser = PydanticOutputParser(pydantic_object=PersonalizedOpening)
        self.email_parser = PydanticOutputParser(pydantic_object=PersonalizedEmail)
        self.subject_parser = PydanticOutputParser(pydantic_object=PersonalizedSubject)
        
        # Setup prompt templates
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup reusable prompt templates."""
        
        # Template for generating talking points
        self.talking_points_template = PromptTemplate(
            input_variables=["company_info", "description", "news", "products"],
            template="""Based on this company information, generate 3-5 specific, relevant 
talking points for a business development email.

Company: {company_info}
Description: {description}
Recent News: {news}
Products/Services: {products}

Focus on:
- Recent achievements or news
- Their products/services
- Industry positioning
- Potential synergies

{format_instructions}
""",
            partial_variables={"format_instructions": self.talking_points_parser.get_format_instructions()}
        )
        
        # Template for personalized opening
        self.opening_template = PromptTemplate(
            input_variables=["name", "company", "context"],
            template="""Write a highly personalized, engaging opening line for a business email.

Recipient: {name}
Company: {company}

Context:
{context}

Requirements:
- Reference something SPECIFIC about their company
- Keep it under 40 words
- Sound genuine and researched, not generic
- Start with "Hi {name},"

{format_instructions}
""",
            partial_variables={"format_instructions": self.opening_parser.get_format_instructions()}
        )
        
        # Template for full email body
        self.email_body_template = ChatPromptTemplate.from_messages([
            ("system", "You are an expert business development writer creating highly personalized emails."),
            ("human", """Create a personalized email based on this context.

Recipient Information:
Name: {name}
Company: {company}
Title: {title}
Company Description: {description}
Recent News: {news}
Products: {products}
Additional Context: {context}

Base Template (for tone/structure reference):
{base_template}

Requirements:
1. Reference specific information about their company
2. Include 2-3 relevant talking points
3. Keep concise (150-200 words)
4. Professional but friendly tone
5. Clear call-to-action
6. Calculate confidence score based on data quality

{format_instructions}
""")
        ])
        
        # Template for subject personalization
        self.subject_template = PromptTemplate(
            input_variables=["base_subject", "company", "context"],
            template="""Personalize this email subject line.

Base Subject: {base_subject}
Company: {company}
Context: {context}

Requirements:
- Keep under 70 characters
- Reference the company name
- Make it specific and attention-grabbing
- Maintain professional tone

{format_instructions}
""",
            partial_variables={"format_instructions": self.subject_parser.get_format_instructions()}
        )
    
    def personalize_email(self, contact: Dict, scraped_data: Dict,
                         base_template: str, subject: str = None) -> Dict:
        """
        Generate personalized email using LangChain.
        
        Args:
            contact: Contact information
            scraped_data: Scraped website data
            base_template: Base email template
            subject: Email subject (optional)
        
        Returns:
            dict: Personalized email content
        """
        logger.info(f"Personalizing email with LangChain for {contact.get('email')}")
        
        try:
            # Extract contact info
            name = contact.get('first_name') or contact.get('full_name', 'there')
            company = contact.get('company', '')
            title = contact.get('job_title', '')
            
            # Extract scraped data
            description = scraped_data.get('description', '')
            news = ', '.join(scraped_data.get('recent_news', [])[:3])
            products = ', '.join(scraped_data.get('products', [])[:3])
            context = scraped_data.get('raw_text', '')[:800]
            
            # Chain 1: Generate talking points
            talking_points_chain = LLMChain(
                llm=self.llm,
                prompt=self.talking_points_template
            )
            
            talking_points_result = talking_points_chain.run(
                company_info=company,
                description=description,
                news=news,
                products=products
            )
            
            talking_points_obj = self.talking_points_parser.parse(talking_points_result)
            
            # Chain 2: Generate opening line
            opening_chain = LLMChain(
                llm=self.llm,
                prompt=self.opening_template
            )
            
            opening_result = opening_chain.run(
                name=name,
                company=company,
                context=f"{description}\n{news}\n{products}"
            )
            
            opening_obj = self.opening_parser.parse(opening_result)
            
            # Chain 3: Generate full email body
            email_chain = LLMChain(
                llm=self.llm,
                prompt=self.email_body_template
            )
            
            # Add format instructions to the template
            format_instructions = self.email_parser.get_format_instructions()
            
            email_result = email_chain.run(
                name=name,
                company=company,
                title=title,
                description=description,
                news=news,
                products=products,
                context=context,
                base_template=base_template[:500],
                format_instructions=format_instructions
            )
            
            email_obj = self.email_parser.parse(email_result)
            
            # Chain 4: Personalize subject (if provided)
            personalized_subject = None
            if subject:
                subject_chain = LLMChain(
                    llm=self.llm,
                    prompt=self.subject_template
                )
                
                subject_result = subject_chain.run(
                    base_subject=subject,
                    company=company,
                    context=f"{description}\n{news}"
                )
                
                subject_obj = self.subject_parser.parse(subject_result)
                personalized_subject = subject_obj.subject
            
            # Combine results
            result = {
                'personalized_opening': email_obj.opening,
                'personalized_body': email_obj.body,
                'talking_points': email_obj.talking_points,
                'confidence_score': email_obj.confidence_score,
                'references_used': email_obj.references_used
            }
            
            if personalized_subject:
                result['personalized_subject'] = personalized_subject
            
            logger.info(f"Successfully personalized with LangChain (confidence: {email_obj.confidence_score})")
            return result
            
        except Exception as e:
            logger.error(f"LangChain personalization error: {e}")
            return self._fallback_personalization(contact, base_template)
    
    def generate_talking_points(self, scraped_data: Dict) -> List[str]:
        """
        Generate talking points using LangChain.
        
        More reliable than direct API calls due to structured output.
        """
        try:
            chain = LLMChain(
                llm=self.llm,
                prompt=self.talking_points_template
            )
            
            result = chain.run(
                company_info=scraped_data.get('url', ''),
                description=scraped_data.get('description', ''),
                news=', '.join(scraped_data.get('recent_news', [])),
                products=', '.join(scraped_data.get('products', []))
            )
            
            parsed = self.talking_points_parser.parse(result)
            return parsed.points
            
        except Exception as e:
            logger.error(f"Error generating talking points: {e}")
            return []
    
    def personalize_batch_with_memory(self, contacts: List[Dict], 
                                     scraped_data_list: List[Dict],
                                     base_template: str) -> List[Dict]:
        """
        Personalize batch of emails with conversation memory.
        
        LangChain's memory helps maintain consistency across batch.
        """
        # This is where LangChain shines - maintaining context across multiple operations
        from langchain.memory import ConversationBufferMemory
        
        memory = ConversationBufferMemory()
        results = []
        
        for contact, scraped_data in zip(contacts, scraped_data_list):
            result = self.personalize_email(contact, scraped_data, base_template)
            results.append(result)
            
            # Store in memory for consistency
            memory.save_context(
                {"input": f"Personalized email for {contact.get('company')}"},
                {"output": f"Generated email with {result['confidence_score']} confidence"}
            )
        
        return results
    
    def _fallback_personalization(self, contact: Dict, template: str) -> Dict:
        """Fallback if LangChain fails."""
        name = contact.get('first_name') or contact.get('full_name', '')
        company = contact.get('company', '')
        
        body = template.replace('{name}', name).replace('{company}', company)
        
        return {
            'personalized_opening': f"Hi {name},",
            'personalized_body': body,
            'talking_points': [],
            'confidence_score': 0.3,
            'references_used': []
        }


# ============================================
# ADVANCED: MULTI-STEP CHAIN
# ============================================

def create_personalization_chain():
    """
    Create a sophisticated multi-step LangChain that:
    1. Analyzes scraped data
    2. Generates talking points
    3. Creates opening
    4. Writes body
    5. Personalizes subject
    
    This is the power of LangChain - chaining multiple operations!
    """
    from langchain.chains import SequentialChain
    
    llm = ChatOpenAI(
        model_name=Config.OPENAI_MODEL,
        temperature=0.7,
        openai_api_key=Config.OPENAI_API_KEY
    )
    
    # Step 1: Analyze company
    analyze_chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            input_variables=["scraped_data"],
            template="Analyze this company data and extract key insights:\n{scraped_data}"
        ),
        output_key="insights"
    )
    
    # Step 2: Generate talking points from insights
    talking_points_chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            input_variables=["insights"],
            template="Generate 3 talking points from these insights:\n{insights}"
        ),
        output_key="talking_points"
    )
    
    # Step 3: Write personalized email
    email_chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            input_variables=["insights", "talking_points", "name", "company"],
            template="""Write a personalized email to {name} at {company}.
            
Insights: {insights}
Talking Points: {talking_points}

Write the email:"""
        ),
        output_key="email"
    )
    
    # Chain them together!
    overall_chain = SequentialChain(
        chains=[analyze_chain, talking_points_chain, email_chain],
        input_variables=["scraped_data", "name", "company"],
        output_variables=["insights", "talking_points", "email"],
        verbose=True  # See each step
    )
    
    return overall_chain
