import fitz  # PyMuPDF
import docx2txt
from docx import Document
import re
import spacy
from typing import Dict, List, Optional

class DocumentParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
    
    def parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return self.clean_text(text)
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return ""
    
    def parse_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            text = docx2txt.process(file_path)
            return self.clean_text(text)
        except Exception as e:
            print(f"Error parsing DOCX: {e}")
            return ""
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\-\.\,\@\+\#]', '', text)
        return text.strip()
    
    def extract_resume_sections(self, text: str) -> Dict:
        """Extract structured information from resume text"""
        sections = {
            'contact': self.extract_contact(text),
            'skills': self.extract_skills(text),
            'experience': self.extract_experience(text),
            'education': self.extract_education(text),
            'projects': self.extract_projects(text),
            'certifications': self.extract_certifications(text)
        }
        return sections
    
    def extract_contact(self, text: str) -> Dict:
        """Extract contact information"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'[\+KATEX_INLINE_OPEN]?[1-9][0-9 .\-KATEX_INLINE_OPENKATEX_INLINE_CLOSE]{8,}[0-9]'
        
        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)
        
        return {
            'email': emails[0] if emails else None,
            'phone': phones[0] if phones else None
        }
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume"""
        # Common skill keywords
        skill_patterns = [
            r'(?i)skills?[:]\s*(.*?)(?:\n|$)',
            r'(?i)technical skills?[:]\s*(.*?)(?:\n|$)',
            r'(?i)core competenc(?:y|ies)[:]\s*(.*?)(?:\n|$)'
        ]
        
        skills = []
        for pattern in skill_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Split by common delimiters
                skill_list = re.split(r'[,|;|\n|•|·]', match)
                skills.extend([s.strip() for s in skill_list if s.strip()])
        
        return list(set(skills))
    
    def extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience"""
        experience_section = re.search(
            r'(?i)(work experience|experience|employment history)(.*?)(?:education|skills|projects|$)',
            text, re.DOTALL
        )
        
        experiences = []
        if experience_section:
            exp_text = experience_section.group(2)
            # Basic extraction - can be enhanced
            lines = exp_text.split('\n')
            current_exp = {}
            
            for line in lines:
                if re.search(r'\d{4}', line):  # Contains year
                    if current_exp:
                        experiences.append(current_exp)
                    current_exp = {'description': line}
                elif current_exp:
                    current_exp['description'] += ' ' + line
            
            if current_exp:
                experiences.append(current_exp)
        
        return experiences
    
    def extract_education(self, text: str) -> List[Dict]:
        """Extract education information"""
        education_section = re.search(
            r'(?i)(education|academic|qualification)(.*?)(?:experience|skills|projects|certifications|$)',
            text, re.DOTALL
        )
        
        education = []
        if education_section:
            edu_text = education_section.group(2)
            # Extract degrees
            degree_patterns = [
                r'(?i)(bachelor|b\.[a-z]+|btech|b\.tech)',
                r'(?i)(master|m\.[a-z]+|mtech|m\.tech|mba)',
                r'(?i)(phd|doctorate)'
            ]
            
            for pattern in degree_patterns:
                if re.search(pattern, edu_text):
                    education.append({'level': pattern, 'text': edu_text[:200]})
        
        return education
    
    def extract_projects(self, text: str) -> List[str]:
        """Extract projects from resume"""
        project_section = re.search(
            r'(?i)(projects?)(.*?)(?:experience|skills|education|certifications|$)',
            text, re.DOTALL
        )
        
        projects = []
        if project_section:
            proj_text = project_section.group(2)
            # Split by common project delimiters
            proj_items = re.split(r'(?:^|\n)(?:•|·|\d+\.|\-)', proj_text)
            projects = [p.strip() for p in proj_items if len(p.strip()) > 20]
        
        return projects
    
    def extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        cert_patterns = [
            r'(?i)certifications?[:]\s*(.*?)(?:\n\n|$)',
            r'(?i)certified\s+in\s+(.*?)(?:\n|$)'
        ]
        
        certifications = []
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                cert_list = re.split(r'[,|\n|•|·]', match)
                certifications.extend([c.strip() for c in cert_list if c.strip()])
        
        return certifications

class JobDescriptionParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
    
    def parse_job_description(self, text: str) -> Dict:
        """Parse job description and extract requirements"""
        jd_data = {
            'title': self.extract_job_title(text),
            'required_skills': self.extract_required_skills(text),
            'preferred_skills': self.extract_preferred_skills(text),
            'experience_required': self.extract_experience_requirement(text),
            'education_required': self.extract_education_requirement(text),
            'responsibilities': self.extract_responsibilities(text)
        }
        return jd_data
    
    def extract_job_title(self, text: str) -> str:
        """Extract job title from JD"""
        title_patterns = [
            r'(?i)position[:]\s*(.*?)(?:\n|$)',
            r'(?i)job title[:]\s*(.*?)(?:\n|$)',
            r'(?i)role[:]\s*(.*?)(?:\n|$)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # If no pattern matches, take first line
        return text.split('\n')[0].strip()
    
    def extract_required_skills(self, text: str) -> List[str]:
        """Extract required/must-have skills"""
        required_patterns = [
            r'(?i)required skills?[:]\s*(.*?)(?:preferred|desired|responsibilities|$)',
            r'(?i)must.?have[:]\s*(.*?)(?:nice.?to.?have|preferred|$)',
            r'(?i)mandatory skills?[:]\s*(.*?)(?:optional|preferred|$)'
        ]
        
        skills = []
        for pattern in required_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                skill_text = match.group(1)
                skill_list = re.split(r'[,|\n|•|·|;]', skill_text)
                skills.extend([s.strip() for s in skill_list if s.strip() and len(s.strip()) < 50])
        
        return list(set(skills))
    
    def extract_preferred_skills(self, text: str) -> List[str]:
        """Extract preferred/nice-to-have skills"""
        preferred_patterns = [
            r'(?i)preferred skills?[:]\s*(.*?)(?:responsibilities|requirements|$)',
            r'(?i)nice.?to.?have[:]\s*(.*?)(?:responsibilities|requirements|$)',
            r'(?i)desired skills?[:]\s*(.*?)(?:responsibilities|requirements|$)'
        ]
        
        skills = []
        for pattern in preferred_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                skill_text = match.group(1)
                skill_list = re.split(r'[,|\n|•|·|;]', skill_text)
                skills.extend([s.strip() for s in skill_list if s.strip() and len(s.strip()) < 50])
        
        return list(set(skills))
    
    def extract_experience_requirement(self, text: str) -> str:
        """Extract experience requirements"""
        exp_patterns = [
            r'(?i)(\d+[\+\-]?\s*(?:to\s*\d+)?\s*years?)',
            r'(?i)(minimum\s*\d+\s*years?)',
            r'(?i)(at least\s*\d+\s*years?)'
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return "Not specified"
    
    def extract_education_requirement(self, text: str) -> str:
        """Extract education requirements"""
        edu_patterns = [
            r'(?i)(bachelor|b\.[a-z]+|btech|b\.tech)',
            r'(?i)(master|m\.[a-z]+|mtech|m\.tech|mba)',
            r'(?i)(graduation|graduate|pg|post.?graduate)'
        ]
        
        requirements = []
        for pattern in edu_patterns:
            if re.search(pattern, text):
                requirements.append(pattern.replace('(?i)', '').replace('\\', ''))
        
        return ', '.join(requirements) if requirements else "Not specified"
    
    def extract_responsibilities(self, text: str) -> List[str]:
        """Extract job responsibilities"""
        resp_section = re.search(
            r'(?i)(responsibilities|duties|you will)(.*?)(?:requirements|qualifications|skills|$)',
            text, re.DOTALL
        )
        
        responsibilities = []
        if resp_section:
            resp_text = resp_section.group(2)
            resp_items = re.split(r'(?:^|\n)(?:•|·|\d+\.|\-)', resp_text)
            responsibilities = [r.strip() for r in resp_items if len(r.strip()) > 20]
        
        return responsibilities[:10]  # Limit to top 10