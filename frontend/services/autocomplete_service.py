from pathlib import Path
from typing import List, Dict, Any
from fuzzywuzzy import fuzz
import re
import logging

logger = logging.getLogger(__name__)


class AutoCompleteService:
    def __init__(self, prompts_file: str):
        self.prompts_file = Path(prompts_file)
        self.prompts = []
        self.categories = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """Load and parse sample prompts from markdown file"""
        try:
            if not self.prompts_file.exists():
                logger.warning(f"Prompts file not found: {self.prompts_file}")
                return
            
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            current_category = "General"
            current_tool = None
            
            for line in content.split('\n'):
                line = line.strip()
                
                # Category headers (## CATEGORY)
                if line.startswith('## ') and 'SERVER' in line:
                    current_category = line.replace('##', '').strip()
                    continue
                
                # Tool headers (### tool_name)
                if line.startswith('### '):
                    current_tool = line.replace('###', '').strip()
                    continue
                
                # Query lines (start with -)
                if line.startswith('- "') and line.endswith('"'):
                    query_text = line[3:-1]  # Remove '- "' and '"'
                    
                    self.prompts.append({
                        'text': query_text,
                        'category': current_category,
                        'tool': current_tool or 'Unknown'
                    })
                    
                    # Track categories
                    if current_category not in self.categories:
                        self.categories[current_category] = []
                    self.categories[current_category].append(query_text)
            
            logger.info(f"Loaded {len(self.prompts)} sample prompts from {len(self.categories)} categories")
        
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
    
    def get_suggestions(self, query: str, max_results: int = 5, min_score: float = 0.3) -> List[Dict[str, Any]]:
        """Get autocomplete suggestions using hybrid matching: exact substring first, then fuzzy matching"""
        if not query or len(query) < 2:
            return []
        
        exact_matches = []
        fuzzy_candidates = []
        query_lower = query.lower()
        
        # First pass: exact substring matching
        for prompt in self.prompts:
            prompt_text = prompt['text']
            prompt_lower = prompt_text.lower()
            
            if query_lower in prompt_lower:
                # Exact substring match found
                match_index = prompt_lower.find(query_lower)
                
                # Higher score for matches at the beginning
                if match_index == 0:
                    score = 1.0
                elif match_index < 10:
                    score = 0.9
                elif match_index < 20:
                    score = 0.8
                else:
                    score = 0.7
                
                exact_matches.append({
                    'text': prompt_text,
                    'category': prompt['category'],
                    'tool': prompt['tool'],
                    'score': score
                })
            else:
                # Store for potential fuzzy matching
                fuzzy_candidates.append(prompt)
        
        # Sort exact matches by score descending
        exact_matches.sort(key=lambda x: (-x['score'], x['text']))
        
        # If we have enough exact matches, return them
        if len(exact_matches) >= max_results:
            return exact_matches[:max_results]
        
        # Second pass: fuzzy matching for remaining slots
        remaining_slots = max_results - len(exact_matches)
        fuzzy_matches = []
        
        for prompt in fuzzy_candidates:
            prompt_text = prompt['text']
            
            # Calculate similarity scores using fuzzy matching
            partial_score = fuzz.partial_ratio(query_lower, prompt_text.lower()) / 100.0
            token_score = fuzz.token_set_ratio(query_lower, prompt_text.lower()) / 100.0
            
            # Use the higher score, but cap at 0.6 to keep fuzzy matches below exact matches
            score = min(max(partial_score, token_score), 0.6)
            
            if score >= min_score:
                fuzzy_matches.append({
                    'text': prompt_text,
                    'category': prompt['category'],
                    'tool': prompt['tool'],
                    'score': score
                })
        
        # Sort fuzzy matches by score descending
        fuzzy_matches.sort(key=lambda x: (-x['score'], x['text']))
        
        # Combine exact and fuzzy matches
        return exact_matches + fuzzy_matches[:remaining_slots]
    
    def get_category_prompts(self, category: str) -> List[str]:
        """Get all prompts for a specific category"""
        return self.categories.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """Get list of all categories"""
        return list(self.categories.keys())
    
    def get_random_prompts(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get random sample prompts"""
        import random
        
        if len(self.prompts) <= count:
            return self.prompts
        
        return random.sample(self.prompts, count)
