from typing import Dict, List, Tuple
from fuzzywuzzy import fuzz
import re
from app.config import Config

class ScoringEngine:
    def __init__(self):
        self.hard_weight = Config.HARD_MATCH_WEIGHT
        self.semantic_weight = Config.SEMANTIC_MATCH_WEIGHT
        self.experience_weight = Config.EXPERIENCE_WEIGHT
    
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
        experience_score = self.calculate_experience_score(resume_data, jd_data)
        
        # Weighted average
        overall_score = (
            hard_match_score * self.hard_weight +
            semantic_score * self.semantic_weight +
            experience_score * self.experience_weight
        )
        
        # Determine verdict
        if overall_score >= Config.HIGH_RELEVANCE_THRESHOLD:
            verdict = "HIGH"
        elif overall_score >= Config.MEDIUM_RELEVANCE_THRESHOLD:
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
        total_requirements = 0
        
        # Extract resume skills
        resume_skills = set([s.lower() for s in resume_data.get('skills', [])])
        resume_text = ' '.join([str(v) for v in resume_data.values() if v]).lower()
        
        # Check required skills
        required_skills = jd_data.get('required_skills', [])
        if required_skills:
            matched_required = 0
            for skill in required_skills:
                skill_lower = skill.lower()
                # Check exact match
                if skill_lower in resume_skills:
                    matched_required += 1
                # Check fuzzy match
                elif any(fuzz.ratio(skill_lower, rs) > 85 for rs in resume_skills):
                    matched_required += 0.8
                # Check if skill appears in resume text
                elif skill_lower in resume_text:
                    matched_required += 0.6
            
            if len(required_skills) > 0:
                score += (matched_required / len(required_skills)) * 60
                total_requirements += 60
        
        # Check preferred skills
        preferred_skills = jd_data.get('preferred_skills', [])
        if preferred_skills:
            matched_preferred = 0
            for skill in preferred_skills:
                skill_lower = skill.lower()
                if skill_lower in resume_skills:
                    matched_preferred += 1
                elif any(fuzz.ratio(skill_lower, rs) > 85 for rs in resume_skills):
                    matched_preferred += 0.8
                elif skill_lower in resume_text:
                    matched_preferred += 0.6
            
            if len(preferred_skills) > 0:
                score += (matched_preferred / len(preferred_skills)) * 40
                total_requirements += 40
        
        return score if total_requirements > 0 else 50
    
    def calculate_experience_score(self, resume_data: Dict, jd_data: Dict) -> float:
        """Calculate experience match score"""
        score = 50  # Default score
        
        # Extract years of experience from resume
        resume_experience = self.extract_years_of_experience(resume_data)
        
        # Extract required experience from JD
        required_experience = jd_data.get('experience_required', 'Not specified')
        
        if required_experience != 'Not specified':
            required_years = self.parse_experience_requirement(required_experience)
            if required_years and resume_experience:
                if resume_experience >= required_years:
                    score = 100
                elif resume_experience >= required_years * 0.75:
                    score = 75
                elif resume_experience >= required_years * 0.5:
                    score = 50
                else:
                    score = 25
        
        return score
    
    def extract_years_of_experience(self, resume_data: Dict) -> float:
        """Extract years of experience from resume"""
        experience_list = resume_data.get('experience', [])
        if not experience_list:
            return 0
        
        # Simple heuristic: count number of experiences
        # Can be improved with date parsing
        years = 0
        for exp in experience_list:
            exp_text = exp.get('description', '')
            # Look for year ranges
            year_matches = re.findall(r'20\d{2}', exp_text)
            if len(year_matches) >= 2:
                years += abs(int(year_matches[-1]) - int(year_matches[0]))
        
        # If no years found, estimate based on number of positions
        if years == 0:
            years = len(experience_list) * 2  # Assume 2 years per position
        
        return years
    
    def parse_experience_requirement(self, exp_text: str) -> float:
        """Parse experience requirement text to extract years"""
        # Extract numbers from experience text
        numbers = re.findall(r'\d+', exp_text)
        if numbers:
            # Take the first number as minimum requirement
            return float(numbers[0])
        return 0