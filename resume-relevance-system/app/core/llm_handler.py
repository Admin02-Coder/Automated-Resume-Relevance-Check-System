import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from typing import Dict, List, Tuple
import numpy as np
from app.config import Config

class LLMHandler:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=Config.GEMINI_API_KEY,
            temperature=0.3
        )
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=Config.GEMINI_API_KEY
        )
        self.vector_store = None
    
    def create_vector_store(self, documents: List[str]) -> Chroma:
        """Create vector store from documents"""
        self.vector_store = Chroma.from_texts(
            texts=documents,
            embedding=self.embeddings,
            persist_directory=Config.CHROMA_PERSIST_DIR
        )
        return self.vector_store
    
    def calculate_semantic_similarity(self, resume_text: str, jd_text: str) -> float:
        """Calculate semantic similarity between resume and JD"""
        try:
            # Get embeddings
            resume_embedding = self.embeddings.embed_query(resume_text)
            jd_embedding = self.embeddings.embed_query(jd_text)
            
            # Calculate cosine similarity
            similarity = np.dot(resume_embedding, jd_embedding) / (
                np.linalg.norm(resume_embedding) * np.linalg.norm(jd_embedding)
            )
            
            # Convert to percentage
            return float(similarity * 100)
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
    
    def analyze_resume_fit(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """Analyze resume fit using LLM"""
        prompt = PromptTemplate(
            input_variables=["resume", "job_description", "required_skills", "preferred_skills"],
            template="""
            You are an expert recruiter analyzing a resume against a job description.
            
            Resume Information:
            {resume}
            
            Job Description:
            {job_description}
            
            Required Skills: {required_skills}
            Preferred Skills: {preferred_skills}
            
            Please analyze and provide:
            1. Overall match percentage (0-100)
            2. Matched skills (list)
            3. Missing required skills (list)
            4. Missing preferred skills (list)
            5. Strengths of the candidate for this role
            6. Gaps or areas of concern
            7. Specific recommendations for the candidate to improve their fit
            
            Format your response as JSON with keys: 
            match_percentage, matched_skills, missing_required_skills, 
            missing_preferred_skills, strengths, gaps, recommendations
            """
        )
        
        try:
            chain = LLMChain(llm=self.llm, prompt=prompt)
            response = chain.run(
                resume=str(resume_data),
                job_description=str(jd_data),
                required_skills=', '.join(jd_data.get('required_skills', [])),
                preferred_skills=', '.join(jd_data.get('preferred_skills', []))
            )
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return self.parse_llm_response(response)
        except Exception as e:
            print(f"LLM analysis error: {e}")
            return {
                'match_percentage': 0,
                'matched_skills': [],
                'missing_required_skills': jd_data.get('required_skills', []),
                'missing_preferred_skills': jd_data.get('preferred_skills', []),
                'strengths': [],
                'gaps': ['Error in analysis'],
                'recommendations': ['Please try again']
            }
    
    def parse_llm_response(self, response: str) -> Dict:
        """Fallback parser for LLM response"""
        result = {
            'match_percentage': 50,
            'matched_skills': [],
            'missing_required_skills': [],
            'missing_preferred_skills': [],
            'strengths': [],
            'gaps': [],
            'recommendations': []
        }
        
        # Basic parsing logic
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'match' in line.lower() and '%' in line:
                try:
                    result['match_percentage'] = int(re.findall(r'\d+', line)[0])
                except:
                    pass
            elif 'matched skills' in line.lower():
                current_section = 'matched_skills'
            elif 'missing required' in line.lower():
                current_section = 'missing_required_skills'
            elif 'missing preferred' in line.lower():
                current_section = 'missing_preferred_skills'
            elif 'strength' in line.lower():
                current_section = 'strengths'
            elif 'gap' in line.lower() or 'concern' in line.lower():
                current_section = 'gaps'
            elif 'recommend' in line.lower():
                current_section = 'recommendations'
            elif current_section and line and not line.endswith(':'):
                if isinstance(result[current_section], list):
                    result[current_section].append(line.strip('- •'))
        
        return result
    
    def generate_feedback(self, analysis_result: Dict, score: float) -> str:
        """Generate personalized feedback for candidate"""
        prompt = PromptTemplate(
            input_variables=["analysis", "score"],
            template="""
            Based on the resume analysis with a relevance score of {score}%, 
            provide constructive feedback to help the candidate improve their application.
            
            Analysis details:
            {analysis}
            
            Please provide:
            1. A brief summary of their current standing
            2. Top 3 specific actions they can take to improve their match
            3. Encouragement and positive reinforcement
            
            Keep the tone professional but friendly and encouraging.
            Limit response to 200 words.
            """
        )
        
        try:
            chain = LLMChain(llm=self.llm, prompt=prompt)
            feedback = chain.run(
                analysis=str(analysis_result),
                score=score
            )
            return feedback
        except Exception as e:
            print(f"Feedback generation error: {e}")
            return "Thank you for your application. Please review the missing skills and consider updating your resume accordingly."