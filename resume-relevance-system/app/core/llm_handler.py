import google.generativeai as genai
from typing import Dict, List
from app.config import Config

class LLMHandler:
    def __init__(self):
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            print(f"Gemini setup error: {e}")
            self.model = None
    
    def calculate_semantic_similarity(self, resume_text: str, jd_text: str) -> float:
        """Calculate semantic similarity using simple text analysis"""
        try:
            # Simple keyword-based similarity for demo
            resume_words = set(resume_text.lower().split())
            jd_words = set(jd_text.lower().split())
            
            common_words = resume_words.intersection(jd_words)
            total_words = resume_words.union(jd_words)
            
            similarity = len(common_words) / len(total_words) if total_words else 0
            return float(similarity * 100)
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 50.0
    
    def analyze_resume_fit(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """Analyze resume fit using Gemini API directly"""
        try:
            if not self.model:
                return self._fallback_analysis(resume_data, jd_data)
            
            # Create prompt for Gemini
            prompt = f"""
            Analyze this resume against the job requirements and provide a JSON response:
            
            Resume Skills: {', '.join(resume_data.get('skills', []))}
            Job Required Skills: {', '.join(jd_data.get('required_skills', []))}
            Job Preferred Skills: {', '.join(jd_data.get('preferred_skills', []))}
            
            Provide analysis in this exact JSON format:
            {{
                "match_percentage": 75,
                "matched_skills": ["skill1", "skill2"],
                "missing_required_skills": ["skill3"],
                "missing_preferred_skills": ["skill4"],
                "strengths": ["Strong in Python", "Good experience"],
                "gaps": ["Missing cloud skills"],
                "recommendations": ["Learn AWS", "Add Docker experience"]
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # Try to parse JSON from response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self._fallback_analysis(resume_data, jd_data)
                
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._fallback_analysis(resume_data, jd_data)
    
    def _fallback_analysis(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """Fallback analysis without AI"""
        resume_skills = set([s.lower() for s in resume_data.get('skills', [])])
        required_skills = set([s.lower() for s in jd_data.get('required_skills', [])])
        preferred_skills = set([s.lower() for s in jd_data.get('preferred_skills', [])])
        
        matched_required = resume_skills.intersection(required_skills)
        matched_preferred = resume_skills.intersection(preferred_skills)
        missing_required = required_skills - resume_skills
        missing_preferred = preferred_skills - resume_skills
        
        match_percentage = 60 + (len(matched_required) * 10) + (len(matched_preferred) * 5)
        match_percentage = min(100, match_percentage)
        
        return {
            'match_percentage': match_percentage,
            'matched_skills': list(matched_required.union(matched_preferred)),
            'missing_required_skills': list(missing_required),
            'missing_preferred_skills': list(missing_preferred),
            'strengths': ['Good technical background', 'Relevant experience'],
            'gaps': ['Some skills gaps identified'] if missing_required else ['Strong skill match'],
            'recommendations': [f'Consider learning {skill}' for skill in list(missing_required)[:3]] or ['Keep up the good work!']
        }
    
    def generate_feedback(self, analysis_result: Dict, score: float) -> str:
        """Generate feedback using Gemini or fallback"""
        try:
            if not self.model:
                return self._simple_feedback(score)
            
            prompt = f"""
            Generate encouraging feedback for a job candidate based on their {score:.1f}% match score.
            Keep it positive, professional, and under 150 words.
            Include specific advice for improvement.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        except:
            return self._simple_feedback(score)
    
    def _simple_feedback(self, score: float) -> str:
        """Simple feedback without AI"""
        if score >= 75:
            return f"Excellent match! Your profile shows {score:.1f}% relevance. You have most of the required skills and would be a strong candidate for this position."
        elif score >= 50:
            return f"Good match! Your profile shows {score:.1f}% relevance. You have many relevant skills. Consider strengthening the missing areas to become an even stronger candidate."
        else:
            return f"Your profile shows {score:.1f}% relevance. Focus on developing the missing required skills to improve your match for this type of role."
