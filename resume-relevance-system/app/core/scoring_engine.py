from typing import Dict, List, Tuple
from fuzzywuzzy import fuzz
import re
from app.config import Config

class ScoringEngine:
    def __init__(self):
        self.hard_weight = 0.4
        self.semantic_weight = 0.4
        self.experience_weight = 0.2
    
    def calculate_overall_score(
        self, 
        resume_data: Dict, 
        jd_data: Dict, 
        semantic_score: float,
        llm_analysis: Dict
    ) -> Tuple[float, str, Dict]:
        """Calculate overall relevance score"""
        
        # Calculate component scores
        hard_match_score = self.calculate_hard_match_score(resume_data, jd_data)
        experience_score = 70  # Simplified for demo
        
        # Use LLM analysis score if available
        if 'match_percentage' in llm_analysis:
            overall_score = llm_analysis['match_percentage']
        else:
            # Weighted average fallback
            overall_score = (
                hard_match_score * self.hard_weight +
                semantic_score * self.semantic_weight +
                experience_score * self.experience_weight
            )
        
        # Determine verdict
        if overall_score >= 75:
            verdict = "HIGH"
        elif overall_score >= 50:
            verdict = "MEDIUM"
        else:
            verdict = "LOW"
        
        # Compile detailed breakdown
        breakdown = {
            'overall_score': round(overall_score, 2),
            'hard_match_score': round(hard_match_score, 2),
            'semantic_score': round(semantic_score, 2),
            'experience_score': round(experience_score, 2),
            'verdict': verdict,
            'matched_skills': llm_analysis.get('matched_skills', []),
            'missing_required_skills': llm_analysis.get('missing_required_skills', []),
            'missing_preferred_skills': llm_analysis.get('missing_preferred_skills', []),
            'recommendations': llm_analysis.get('recommendations', [])
        }
        
        return overall_score, verdict, breakdown
    
    def calculate_hard_match_score(self, resume_data: Dict, jd_data: Dict) -> float:
        """Calculate hard match score based on keywords and skills"""
        score = 0
        
        # Extract resume skills
        resume_skills = set([s.lower() for s in resume_data.get('skills', [])])
        
        # Check required skills
        required_skills = jd_data.get('required_skills', [])
        if required_skills:
            matched_required = 0
            for skill in required_skills:
                skill_lower = skill.lower()
                if skill_lower in resume_skills:
                    matched_required += 1
                elif any(fuzz.ratio(skill_lower, rs) > 80 for rs in resume_skills):
                    matched_required += 0.8
            
            score = (matched_required / len(required_skills)) * 100 if required_skills else 50
        
        return min(100, max(0, score))
