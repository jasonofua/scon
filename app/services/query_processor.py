"""
Query processing and intent classification service for SCONIA.
Handles query preprocessing, intent detection, and entity extraction.
"""
from typing import Dict, List, Any, Optional, Tuple
import logging
import re
from datetime import datetime
import spacy
from collections import Counter

from app.config import INTENT_CATEGORIES, QUICK_OPTIONS_PROMPT

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Service for processing and classifying user queries."""
    
    def __init__(self):
        """Initialize query processor."""
        self.nlp = None
        self._load_nlp_model()
        
        # Intent classification patterns
        self.intent_patterns = {
            'constitutional_query': [
                r'\b(constitution|constitutional|fundamental rights?|bill of rights?)\b',
                r'\b(chapter|section|article)\s+\d+\b',
                r'\b(right to|freedom of|liberty|equality)\b',
                r'\b(amendment|provision)\b'
            ],
            'judge_information': [
                r'\b(judge|justice|chief justice|cjn)\b',
                r'\b(court personnel|judicial officer)\b',
                r'\b(appointment|biography|background)\b',
                r'\b(who is|tell me about)\s+.*justice\b'
            ],
            'court_schedule': [
                r'\b(schedule|calendar|session|sitting)\b',
                r'\b(when|what time|date)\b.*\b(court|hearing)\b',
                r'\b(next session|upcoming|today|tomorrow)\b',
                r'\b(court hours|opening time)\b'
            ],
            'case_law': [
                r'\b(case|precedent|judgment|ruling|decision)\b',
                r'\b(appeal|appellant|respondent)\b',
                r'\b(landmark case|supreme court case)\b',
                r'\b(citation|case law|jurisprudence)\b'
            ],
            'procedural_information': [
                r'\b(how to|procedure|process|steps)\b',
                r'\b(file|filing|submit|application)\b',
                r'\b(requirements|documents needed|what do i need)\b',
                r'\b(appeal process|court procedure)\b'
            ],
            'fee_calculation': [
                r'\b(fee|cost|charge|payment|amount)\b',
                r'\b(how much|price|expense)\b',
                r'\b(filing fee|court fee|legal fee)\b',
                r'\b(payment method|pay|money)\b'
            ],
            'general_information': [
                r'\b(information|about|what is|explain)\b',
                r'\b(supreme court|court system)\b',
                r'\b(legal system|judiciary)\b',
                r'\b(help|assistance|guide)\b'
            ],
            'greeting': [
                r'\b(hello|hi|good morning|good afternoon|good evening)\b',
                r'\b(greetings|welcome)\b',
                r'\b(how are you|nice to meet)\b'
            ],
            'help_request': [
                r'\b(help|assist|support|guidance)\b',
                r'\b(i need|can you|please)\b',
                r'\b(confused|don\'t understand|unclear)\b'
            ]
        }
        
        # Legal entity patterns
        self.entity_patterns = {
            'section_number': r'\b(?:section|sec\.?)\s+(\d+(?:\.\d+)?)\b',
            'chapter_number': r'\b(?:chapter|chap\.?)\s+([IVX]+|\d+)\b',
            'article_number': r'\b(?:article|art\.?)\s+(\d+)\b',
            'case_number': r'\b(\d{4})\s*[A-Z]+\s*(\d+)\b',
            'year': r'\b(19|20)\d{2}\b',
            'judge_name': r'\b(?:justice|judge)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            'court_name': r'\b(supreme court|court of appeal|high court|federal high court)\b',
            'legal_term': r'\b(appellant|respondent|plaintiff|defendant|petitioner)\b'
        }
    
    def _load_nlp_model(self):
        """Load spaCy NLP model."""
        try:
            # Try to load English model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy English model")
        except OSError:
            logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def preprocess_query(self, query: str) -> str:
        """Preprocess and clean user query."""
        try:
            # Convert to lowercase for processing
            processed = query.lower().strip()
            
            # Remove extra whitespace
            processed = re.sub(r'\s+', ' ', processed)
            
            # Fix common typos in legal terms
            typo_corrections = {
                r'\bconstitition\b': 'constitution',
                r'\bjudge?ment\b': 'judgment',
                r'\bappelant\b': 'appellant',
                r'\bdefendant\b': 'defendant',
                r'\bsupreme\s+court\b': 'supreme court'
            }
            
            for pattern, correction in typo_corrections.items():
                processed = re.sub(pattern, correction, processed, flags=re.IGNORECASE)
            
            return processed.strip()
            
        except Exception as e:
            logger.error(f"Error preprocessing query: {e}")
            return query.strip()
    
    def classify_intent(self, query: str) -> Tuple[str, float]:
        """
        Classify the intent of a user query.
        
        Args:
            query: Preprocessed user query
            
        Returns:
            Tuple of (intent, confidence_score)
        """
        try:
            query_lower = query.lower()
            intent_scores = {}
            
            # Score each intent based on pattern matches
            for intent, patterns in self.intent_patterns.items():
                score = 0
                matches = 0
                
                for pattern in patterns:
                    if re.search(pattern, query_lower, re.IGNORECASE):
                        matches += 1
                        score += 1
                
                # Normalize score
                if matches > 0:
                    intent_scores[intent] = score / len(patterns)
            
            # Get the highest scoring intent
            if intent_scores:
                best_intent = max(intent_scores.items(), key=lambda x: x[1])
                return best_intent[0], best_intent[1]
            else:
                return 'general_information', 0.5
                
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return 'general_information', 0.0
    
    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract legal entities from query.
        
        Args:
            query: User query
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        try:
            # Extract using regex patterns
            for entity_type, pattern in self.entity_patterns.items():
                matches = re.findall(pattern, query, re.IGNORECASE)
                if matches:
                    # Flatten tuples if necessary
                    if isinstance(matches[0], tuple):
                        matches = [' '.join(match) if isinstance(match, tuple) else match for match in matches]
                    entities[entity_type] = list(set(matches))  # Remove duplicates
            
            # Use spaCy for additional entity extraction if available
            if self.nlp:
                doc = self.nlp(query)
                
                # Extract named entities
                spacy_entities = {}
                for ent in doc.ents:
                    entity_type = ent.label_.lower()
                    if entity_type not in spacy_entities:
                        spacy_entities[entity_type] = []
                    spacy_entities[entity_type].append(ent.text)
                
                # Merge with regex entities
                for entity_type, values in spacy_entities.items():
                    if entity_type in entities:
                        entities[entity_type].extend(values)
                        entities[entity_type] = list(set(entities[entity_type]))
                    else:
                        entities[entity_type] = values
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {}
    
    def generate_quick_options(self, intent: str, entities: Dict[str, List[str]]) -> List[Dict[str, str]]:
        """
        Generate relevant quick options based on intent and entities.
        
        Args:
            intent: Classified intent
            entities: Extracted entities
            
        Returns:
            List of quick option dictionaries
        """
        try:
            quick_options = []
            
            # Base options for each intent
            intent_options = {
                'constitutional_query': [
                    {"text": "View fundamental rights", "action": "constitutional_rights", "category": "constitution"},
                    {"text": "Browse constitution chapters", "action": "constitution_chapters", "category": "constitution"},
                    {"text": "Search specific section", "action": "section_search", "category": "constitution"}
                ],
                'judge_information': [
                    {"text": "Current Supreme Court justices", "action": "current_judges", "category": "judges"},
                    {"text": "Chief Justice information", "action": "chief_justice", "category": "judges"},
                    {"text": "Court hierarchy", "action": "court_structure", "category": "information"}
                ],
                'case_law': [
                    {"text": "Landmark cases", "action": "landmark_cases", "category": "cases"},
                    {"text": "Recent judgments", "action": "recent_cases", "category": "cases"},
                    {"text": "Case search", "action": "case_search", "category": "cases"}
                ],
                'procedural_information': [
                    {"text": "Filing procedures", "action": "filing_guide", "category": "procedures"},
                    {"text": "Required documents", "action": "document_requirements", "category": "procedures"},
                    {"text": "Appeal process", "action": "appeal_guide", "category": "procedures"}
                ],
                'fee_calculation': [
                    {"text": "Calculate filing fees", "action": "fee_calculator", "category": "fees"},
                    {"text": "Payment methods", "action": "payment_info", "category": "fees"},
                    {"text": "Fee schedule", "action": "fee_schedule", "category": "fees"}
                ],
                'court_schedule': [
                    {"text": "Today's sessions", "action": "today_schedule", "category": "schedule"},
                    {"text": "Upcoming hearings", "action": "upcoming_schedule", "category": "schedule"},
                    {"text": "Court calendar", "action": "full_calendar", "category": "schedule"}
                ],
                'general_information': [
                    {"text": "About Supreme Court", "action": "court_info", "category": "information"},
                    {"text": "Legal resources", "action": "resources", "category": "information"},
                    {"text": "Contact information", "action": "contact", "category": "information"}
                ]
            }
            
            # Get base options for intent
            base_options = intent_options.get(intent, intent_options['general_information'])
            quick_options.extend(base_options[:3])  # Limit to 3 options
            
            # Add entity-specific options
            if 'section_number' in entities:
                quick_options.append({
                    "text": f"More about Section {entities['section_number'][0]}",
                    "action": f"section_{entities['section_number'][0]}",
                    "category": "constitution"
                })
            
            if 'judge_name' in entities:
                quick_options.append({
                    "text": f"More about Justice {entities['judge_name'][0]}",
                    "action": f"judge_{entities['judge_name'][0].replace(' ', '_')}",
                    "category": "judges"
                })
            
            # Always include help option
            quick_options.append({
                "text": "Need more help?",
                "action": "help",
                "category": "help"
            })
            
            return quick_options[:4]  # Limit to 4 total options
            
        except Exception as e:
            logger.error(f"Error generating quick options: {e}")
            return [{"text": "Ask a legal question", "action": "legal_chat", "category": "chat"}]
    
    def enhance_query(self, query: str, context: Optional[str] = None) -> str:
        """
        Enhance query with additional context for better retrieval.
        
        Args:
            query: Original user query
            context: Previous conversation context
            
        Returns:
            Enhanced query string
        """
        try:
            enhanced = query
            
            # Add legal context keywords
            intent, _ = self.classify_intent(query)
            
            context_keywords = {
                'constitutional_query': 'Nigerian Constitution fundamental rights',
                'judge_information': 'Supreme Court Nigeria Justice',
                'case_law': 'Supreme Court Nigeria case law precedent',
                'procedural_information': 'court procedure filing process',
                'fee_calculation': 'court fees Nigeria Supreme Court',
                'court_schedule': 'Supreme Court Nigeria schedule session'
            }
            
            if intent in context_keywords:
                enhanced = f"{query} {context_keywords[intent]}"
            
            # Add context from previous conversation
            if context:
                # Extract relevant terms from context
                context_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', context)
                if context_terms:
                    enhanced += f" {' '.join(context_terms[:3])}"
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error enhancing query: {e}")
            return query
    
    def process_query(
        self,
        query: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete query processing pipeline.
        
        Args:
            query: Raw user query
            context: Previous conversation context
            
        Returns:
            Dictionary with processed query information
        """
        try:
            # Preprocess query
            processed_query = self.preprocess_query(query)
            
            # Classify intent
            intent, confidence = self.classify_intent(processed_query)
            
            # Extract entities
            entities = self.extract_entities(query)  # Use original query for entity extraction
            
            # Generate quick options
            quick_options = self.generate_quick_options(intent, entities)
            
            # Enhance query for retrieval
            enhanced_query = self.enhance_query(processed_query, context)
            
            return {
                'original_query': query,
                'processed_query': processed_query,
                'enhanced_query': enhanced_query,
                'intent': intent,
                'confidence': confidence,
                'entities': entities,
                'quick_options': quick_options,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'original_query': query,
                'processed_query': query,
                'enhanced_query': query,
                'intent': 'general_information',
                'confidence': 0.0,
                'entities': {},
                'quick_options': [{"text": "Ask a legal question", "action": "legal_chat", "category": "chat"}],
                'timestamp': datetime.utcnow().isoformat()
            }


# Global query processor instance
query_processor = QueryProcessor()
