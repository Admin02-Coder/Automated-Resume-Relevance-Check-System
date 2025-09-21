import os
from typing import Dict, Tuple, Optional
from app.core.parser import DocumentParser, JobDescriptionParser
from app.core.llm_handler import LLMHandler
from app.core.scoring_engine import ScoringEngine
from app.database.models import DatabaseOperations

class ResumeProcessor:
    def __init__(self):
        self.doc_parser = DocumentParser()
        self.jd_parser = JobDescriptionParser()
        self.llm_handler = LLMHandler()
        self.scoring_engine = ScoringEngine()
        self.db_ops = DatabaseOperations()
    
    def process_resume_and_jd(
        self, 
        resume_path: str, 
        jd_path: str,
        candidate_info: Dict = None
    ) -> Dict:
        """Main processing pipeline"""
        
        # Parse documents
        resume_text = self.parse_document(resume_path)
        jd_text = self.parse_document(jd_path)
        
        if not resume_text or not jd_text:
            return {
                'error': 'Failed to parse documents',
                'success': False
            }
        
        # Extract structured data
        resume_data = self.doc_parser.extract_resume_sections(resume_text)
        jd_data = self.jd_parser.parse_job_description(jd_text)
        
        # Calculate semantic similarity
        semantic_score = self.llm_handler.calculate_semantic_similarity(
            resume_text, jd_text
        )
        
        # Get LLM analysis
        llm_analysis = self.llm_handler.analyze_resume_fit(resume_data, jd_data)
        
        # Calculate overall score
        overall_score, verdict, breakdown = self.scoring_engine.calculate_overall_score(
            resume_data, jd_data, semantic_score, llm_analysis
        )
        
        # Generate feedback
        feedback = self.llm_handler.generate_feedback(breakdown, overall_score)
        
        # Prepare result
        result = {
            'success': True,
            'candidate_name': candidate_info.get('name', 'Unknown') if candidate_info else 'Unknown',
            'candidate_email': resume_data['contact'].get('email', ''),
            'job_title': jd_data.get('title', 'Unknown Position'),
            'company': candidate_info.get('company', 'Unknown') if candidate_info else 'Unknown',
            'location': candidate_info.get('location', 'Unknown') if candidate_info else 'Unknown',
            'overall_score': overall_score,
            'verdict': verdict,
            'breakdown': breakdown,
            'feedback': feedback,
            'resume_filename': os.path.basename(resume_path),
            'jd_filename': os.path.basename(jd_path)
        }
        
        # Save to database
        self.save_to_database(result)
        
        return result
    
    def parse_document(self, file_path: str) -> str:
        """Parse document based on file type"""
        if file_path.lower().endswith('.pdf'):
            return self.doc_parser.parse_pdf(file_path)
        elif file_path.lower().endswith(('.docx', '.doc')):
            return self.doc_parser.parse_docx(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def save_to_database(self, result: Dict):
        """Save evaluation result to database"""
        evaluation_data = {
            'candidate_name': result.get('candidate_name'),
            'candidate_email': result.get('candidate_email'),
            'job_title': result.get('job_title'),
            'company': result.get('company'),
            'location': result.get('location'),
            'resume_filename': result.get('resume_filename'),
            'jd_filename': result.get('jd_filename'),
            'overall_score': result.get('overall_score'),
            'verdict': result.get('verdict'),
            'hard_match_score': result['breakdown'].get('hard_match_score'),
            'semantic_score': result['breakdown'].get('semantic_score'),
            'experience_score': result['breakdown'].get('experience_score'),
            'matched_skills': result['breakdown'].get('matched_skills'),
            'missing_required_skills': result['breakdown'].get('missing_required_skills'),
            'missing_preferred_skills': result['breakdown'].get('missing_preferred_skills'),
            'recommendations': result['breakdown'].get('recommendations'),
            'feedback': result.get('feedback')
        }
        
        self.db_ops.save_evaluation(evaluation_data)
    
    def batch_process_resumes(self, resume_folder: str, jd_path: str) -> list:
        """Process multiple resumes against a single JD"""
        results = []
        
        # Get all resume files
        resume_files = [
            f for f in os.listdir(resume_folder) 
            if f.endswith(('.pdf', '.docx', '.doc'))
        ]
        
        for resume_file in resume_files:
            resume_path = os.path.join(resume_folder, resume_file)
            try:
                result = self.process_resume_and_jd(resume_path, jd_path)
                results.append(result)
            except Exception as e:
                print(f"Error processing {resume_file}: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'resume_filename': resume_file
                })
        
        return results