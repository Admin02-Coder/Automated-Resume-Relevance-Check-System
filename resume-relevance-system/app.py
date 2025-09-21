import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import tempfile
from app.core.resume_processor import ResumeProcessor
from app.database.models import DatabaseOperations, JobDescription
from app.config import Config

# Page configuration
st.set_page_config(
    page_title="Resume Relevance Check System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .score-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .high-score {
        background-color: #d4edda;
        border: 2px solid #28a745;
    }
    .medium-score {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
    }
    .low-score {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processor' not in st.session_state:
    st.session_state.processor = ResumeProcessor()
if 'db_ops' not in st.session_state:
    st.session_state.db_ops = DatabaseOperations()
if 'current_results' not in st.session_state:
    st.session_state.current_results = None

def main():
    st.markdown('<h1 class="main-header">🎯 Resume Relevance Check System</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["📝 Single Resume Evaluation", "📚 Batch Processing", "📊 Dashboard", "⚙️ Settings"]
    )
    
    if page == "📝 Single Resume Evaluation":
        single_resume_page()
    elif page == "📚 Batch Processing":
        batch_processing_page()
    elif page == "📊 Dashboard":
        dashboard_page()
    elif page == "⚙️ Settings":
        settings_page()

def single_resume_page():
    st.header("Single Resume Evaluation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Upload Resume")
        resume_file = st.file_uploader(
            "Choose a resume file",
            type=['pdf', 'docx', 'doc'],
            key="resume_upload"
        )
        
        if resume_file:
            st.success(f"✅ Resume uploaded: {resume_file.name}")
            
            # Additional candidate info
            st.subheader("Candidate Information")
            candidate_name = st.text_input("Candidate Name (optional)")
            company = st.text_input("Target Company (optional)")
            location = st.selectbox(
                "Location",
                ["Hyderabad", "Bangalore", "Pune", "Delhi NCR", "Other"]
            )
    
    with col2:
        st.subheader("📋 Upload Job Description")
        jd_file = st.file_uploader(
            "Choose a job description file",
            type=['pdf', 'docx', 'doc', 'txt'],
            key="jd_upload"
        )
        
        if jd_file:
            st.success(f"✅ JD uploaded: {jd_file.name}")
            
            # Or paste JD
            st.subheader("Or Paste Job Description")
            jd_text = st.text_area("Paste JD here (optional)", height=200)
    
    # Process button
    if st.button("🚀 Analyze Resume", type="primary", use_container_width=True):
        if resume_file and (jd_file or jd_text):
            with st.spinner("🔍 Analyzing resume against job description..."):
                # Save uploaded files temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file.name)[1]) as tmp_resume:
                    tmp_resume.write(resume_file.getbuffer())
                    resume_path = tmp_resume.name
                
                if jd_file:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(jd_file.name)[1]) as tmp_jd:
                        tmp_jd.write(jd_file.getbuffer())
                        jd_path = tmp_jd.name
                else:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w') as tmp_jd:
                        tmp_jd.write(jd_text)
                        jd_path = tmp_jd.name
                
                # Process
                candidate_info = {
                    'name': candidate_name or "Unknown",
                    'company': company or "Unknown",
                    'location': location
                }
                
                result = st.session_state.processor.process_resume_and_jd(
                    resume_path, jd_path, candidate_info
                )
                
                # Clean up temp files
                os.unlink(resume_path)
                os.unlink(jd_path)
                
                # Store result
                st.session_state.current_results = result
                
                # Display results
                display_results(result)
        else:
            st.error("❌ Please upload both resume and job description")

def display_results(result):
    if not result.get('success'):
        st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
        return
    
    # Overall Score Card
    score = result.get('overall_score', 0)
    verdict = result.get('verdict', 'UNKNOWN')
    
    # Determine score class
    if verdict == "HIGH":
        score_class = "high-score"
        emoji = "🎉"
    elif verdict == "MEDIUM":
        score_class = "medium-score"
        emoji = "👍"
    else:
        score_class = "low-score"
        emoji = "📈"
    
    st.markdown(f'<div class="score-card {score_class}">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        st.metric("Overall Score", f"{score:.1f}%")
    with col2:
        st.metric("Verdict", f"{emoji} {verdict}")
    with col3:
        st.metric("Job Match", result.get('job_title', 'Unknown'))
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Detailed Breakdown
    st.subheader("📊 Score Breakdown")
    breakdown = result.get('breakdown', {})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Hard Match", f"{breakdown.get('hard_match_score', 0):.1f}%")
    with col2:
        st.metric("Semantic Match", f"{breakdown.get('semantic_score', 0):.1f}%")
    with col3:
        st.metric("Experience Match", f"{breakdown.get('experience_score', 0):.1f}%")
    
    # Skills Analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Matched Skills")
        matched_skills = breakdown.get('matched_skills', [])
        if matched_skills:
            for skill in matched_skills[:10]:  # Show top 10
                st.write(f"• {skill}")
        else:
            st.write("No matching skills found")
    
    with col2:
        st.subheader("❌ Missing Required Skills")
        missing_skills = breakdown.get('missing_required_skills', [])
        if missing_skills:
            for skill in missing_skills[:10]:  # Show top 10
                st.write(f"• {skill}")
        else:
            st.write("All required skills matched!")
    
    # Recommendations
    st.subheader("💡 Recommendations")
    recommendations = breakdown.get('recommendations', [])
    if recommendations:
        for i, rec in enumerate(recommendations[:5], 1):
            st.write(f"{i}. {rec}")
    
    # Feedback
    st.subheader("📝 Personalized Feedback")
    feedback = result.get('feedback', '')
    if feedback:
        st.info(feedback)
    
    # Visualization
    st.subheader("📈 Visual Analysis")
    
    # Score gauge chart
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Resume Relevance Score"},
        delta = {'reference': 75},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 75], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Download report button
    if st.button("📥 Download Report", use_container_width=True):
        report = generate_report(result)
        st.download_button(
            label="Download PDF Report",
            data=report,
            file_name=f"resume_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

def batch_processing_page():
    st.header("Batch Resume Processing")
    
    st.info("📁 Upload multiple resumes to evaluate against a single job description")
    
    # Job Description Upload
    st.subheader("📋 Upload Job Description")
    jd_file = st.file_uploader(
        "Choose a job description file",
        type=['pdf', 'docx', 'doc', 'txt'],
        key="batch_jd_upload"
    )
    
    # Multiple Resume Upload
    st.subheader("📄 Upload Multiple Resumes")
    resume_files = st.file_uploader(
        "Choose resume files",
        type=['pdf', 'docx', 'doc'],
        accept_multiple_files=True,
        key="batch_resume_upload"
    )
    
    if resume_files:
        st.success(f"✅ {len(resume_files)} resumes uploaded")
    
    # Process button
    if st.button("🚀 Process Batch", type="primary", use_container_width=True):
        if jd_file and resume_files:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            
            # Save JD temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(jd_file.name)[1]) as tmp_jd:
                tmp_jd.write(jd_file.getbuffer())
                jd_path = tmp_jd.name
            
            # Process each resume
            for i, resume_file in enumerate(resume_files):
                status_text.text(f"Processing {resume_file.name}...")
                progress_bar.progress((i + 1) / len(resume_files))
                
                # Save resume temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file.name)[1]) as tmp_resume:
                    tmp_resume.write(resume_file.getbuffer())
                    resume_path = tmp_resume.name
                
                try:
                    result = st.session_state.processor.process_resume_and_jd(
                        resume_path, jd_path
                    )
                    results.append(result)
                except Exception as e:
                    results.append({
                        'success': False,
                        'error': str(e),
                        'resume_filename': resume_file.name
                    })
                
                # Clean up
                os.unlink(resume_path)
            
            # Clean up JD
            os.unlink(jd_path)
            
            status_text.text("✅ Batch processing complete!")
            
            # Display results table
            display_batch_results(results)
        else:
            st.error("❌ Please upload job description and at least one resume")

def display_batch_results(results):
    st.subheader("📊 Batch Processing Results")
    
    # Create DataFrame
    df_data = []
    for result in results:
        if result.get('success'):
            df_data.append({
                'Resume': result.get('resume_filename', 'Unknown'),
                'Candidate': result.get('candidate_name', 'Unknown'),
                'Email': result.get('candidate_email', ''),
                'Score': result.get('overall_score', 0),
                'Verdict': result.get('verdict', 'Unknown'),
                'Missing Skills': len(result.get('breakdown', {}).get('missing_required_skills', []))
            })
        else:
            df_data.append({
                'Resume': result.get('resume_filename', 'Unknown'),
                'Candidate': 'Error',
                'Email': '',
                'Score': 0,
                'Verdict': 'ERROR',
                'Missing Skills': 0
            })
    
    df = pd.DataFrame(df_data)
    
    # Sort by score
    df = df.sort_values('Score', ascending=False)
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Resumes", len(results))
    with col2:
        high_count = len(df[df['Verdict'] == 'HIGH'])
        st.metric("High Matches", high_count)
    with col3:
        medium_count = len(df[df['Verdict'] == 'MEDIUM'])
        st.metric("Medium Matches", medium_count)
    with col4:
        avg_score = df['Score'].mean()
        st.metric("Average Score", f"{avg_score:.1f}%")
    
    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score",
                help="Overall relevance score",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        }
    )
    
    # Visualization
    fig = px.histogram(
        df, 
        x='Score', 
        color='Verdict',
        title='Score Distribution',
        nbins=20,
        color_discrete_map={'HIGH': 'green', 'MEDIUM': 'yellow', 'LOW': 'red', 'ERROR': 'gray'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Export results
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Results CSV",
        data=csv,
        file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

def dashboard_page():
    st.header("Dashboard")
    
    # Get all evaluations from database
    evaluations = st.session_state.db_ops.get_evaluations()
    
    if not evaluations:
        st.info("No evaluations found. Start by processing some resumes!")
        return
    
    # Convert to DataFrame
    df_data = []
    for eval in evaluations:
        df_data.append({
            'ID': eval.id,
            'Candidate': eval.candidate_name,
            'Email': eval.candidate_email,
            'Job Title': eval.job_title,
            'Company': eval.company,
            'Location': eval.location,
            'Score': eval.overall_score,
            'Verdict': eval.verdict,
            'Date': eval.evaluation_date
        })
    
    df = pd.DataFrame(df_data)
    
    # Filters
    st.subheader("🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        job_titles = df['Job Title'].unique()
        selected_job = st.selectbox("Filter by Job Title", ["All"] + list(job_titles))
    
    with col2:
        verdicts = df['Verdict'].unique()
        selected_verdict = st.selectbox("Filter by Verdict", ["All"] + list(verdicts))
    
    with col3:
        locations = df['Location'].unique()
        selected_location = st.selectbox("Filter by Location", ["All"] + list(locations))
    
    # Apply filters
    filtered_df = df.copy()
    if selected_job != "All":
        filtered_df = filtered_df[filtered_df['Job Title'] == selected_job]
    if selected_verdict != "All":
        filtered_df = filtered_df[filtered_df['Verdict'] == selected_verdict]
    if selected_location != "All":
        filtered_df = filtered_df[filtered_df['Location'] == selected_location]
    
    # Display metrics
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Evaluations", len(filtered_df))
    with col2:
        avg_score = filtered_df['Score'].mean()
        st.metric("Average Score", f"{avg_score:.1f}%")
    with col3:
        high_matches = len(filtered_df[filtered_df['Verdict'] == 'HIGH'])
        st.metric("High Matches", high_matches)
    with col4:
        conversion_rate = (high_matches / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
        st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Verdict distribution
        verdict_counts = filtered_df['Verdict'].value_counts()
        fig = px.pie(
            values=verdict_counts.values,
            names=verdict_counts.index,
            title="Verdict Distribution",
            color_discrete_map={'HIGH': 'green', 'MEDIUM': 'yellow', 'LOW': 'red'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Score distribution by location
        fig = px.box(
            filtered_df,
            x='Location',
            y='Score',
            title="Score Distribution by Location",
            color='Location'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Time series
    if 'Date' in filtered_df.columns:
        filtered_df['Date'] = pd.to_datetime(filtered_df['Date'])
        daily_counts = filtered_df.groupby(filtered_df['Date'].dt.date).size()
        
        fig = px.line(
            x=daily_counts.index,
            y=daily_counts.values,
            title="Evaluations Over Time",
            labels={'x': 'Date', 'y': 'Number of Evaluations'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    st.subheader("📋 Evaluation Details")
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score",
                help="Overall relevance score",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        }
    )
    
    # Export
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Export to CSV",
        data=csv,
        file_name=f"evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

def settings_page():
    st.header("Settings")
    
    # API Configuration
    st.subheader("🔑 API Configuration")
    
    current_key = Config.GEMINI_API_KEY
    if current_key:
        st.success("✅ Gemini API Key is configured")
        if st.button("Update API Key"):
            new_key = st.text_input("Enter new Gemini API Key", type="password")
            if new_key and st.button("Save"):
                # Update .env file
                with open('.env', 'r') as f:
                    lines = f.readlines()
                with open('.env', 'w') as f:
                    for line in lines:
                        if line.startswith('GEMINI_API_KEY'):
                            f.write(f'GEMINI_API_KEY={new_key}\n')
                        else:
                            f.write(line)
                st.success("API Key updated successfully!")
                st.rerun()
    else:
        st.warning("⚠️ Gemini API Key not configured")
        api_key = st.text_input("Enter Gemini API Key", type="password")
        if api_key and st.button("Save API Key"):
            with open('.env', 'a') as f:
                f.write(f'\nGEMINI_API_KEY={api_key}')
            st.success("API Key saved successfully!")
            st.rerun()
    
    # Scoring Weights
    st.subheader("⚖️ Scoring Weights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        hard_weight = st.slider(
            "Hard Match Weight",
            0.0, 1.0, Config.HARD_MATCH_WEIGHT, 0.1
        )
    
    with col2:
        semantic_weight = st.slider(
            "Semantic Match Weight",
            0.0, 1.0, Config.SEMANTIC_MATCH_WEIGHT, 0.1
        )
    
    with col3:
        experience_weight = st.slider(
            "Experience Weight",
            0.0, 1.0, Config.EXPERIENCE_WEIGHT, 0.1
        )
    
    total_weight = hard_weight + semantic_weight + experience_weight
    if abs(total_weight - 1.0) > 0.01:
        st.error(f"⚠️ Weights must sum to 1.0 (current sum: {total_weight:.2f})")
    else:
        st.success(f"✅ Total weight: {total_weight:.2f}")
    
    # Thresholds
    st.subheader("📏 Score Thresholds")
    
    col1, col2 = st.columns(2)
    
    with col1:
        high_threshold = st.number_input(
            "High Relevance Threshold",
            0, 100, Config.HIGH_RELEVANCE_THRESHOLD
        )
    
    with col2:
        medium_threshold = st.number_input(
            "Medium Relevance Threshold",
            0, 100, Config.MEDIUM_RELEVANCE_THRESHOLD
        )
    
    if st.button("Save Settings", type="primary"):
        # Update configuration
        Config.HARD_MATCH_WEIGHT = hard_weight
        Config.SEMANTIC_MATCH_WEIGHT = semantic_weight
        Config.EXPERIENCE_WEIGHT = experience_weight
        Config.HIGH_RELEVANCE_THRESHOLD = high_threshold
        Config.MEDIUM_RELEVANCE_THRESHOLD = medium_threshold
        
        st.success("✅ Settings saved successfully!")
    
    # Database Management
    st.subheader("🗄️ Database Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        evaluations_count = len(st.session_state.db_ops.get_evaluations())
        st.metric("Total Evaluations", evaluations_count)
    
    with col2:
        jds_count = len(st.session_state.db_ops.get_job_descriptions())
        st.metric("Total Job Descriptions", jds_count)
    
    if st.button("Clear All Data", type="secondary"):
        if st.checkbox("I understand this will delete all data"):
            # Clear database
            st.warning("Database cleared!")
    
    # System Info
    st.subheader("ℹ️ System Information")
    st.info(f"""
    - Python Version: 3.x
    - Streamlit Version: {st.__version__}
    - Database: SQLite
    - Vector Store: Chroma
    - LLM: Google Gemini
    """)

def generate_report(result):
    """Generate a text report from evaluation results"""
    report = f"""
RESUME EVALUATION REPORT
========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CANDIDATE INFORMATION
--------------------
Name: {result.get('candidate_name', 'Unknown')}
Email: {result.get('candidate_email', 'Not provided')}
Resume: {result.get('resume_filename', 'Unknown')}

JOB INFORMATION
--------------
Position: {result.get('job_title', 'Unknown')}
Company: {result.get('company', 'Unknown')}
Location: {result.get('location', 'Unknown')}

EVALUATION RESULTS
-----------------
Overall Score: {result.get('overall_score', 0):.1f}%
Verdict: {result.get('verdict', 'Unknown')}

Score Breakdown:
- Hard Match Score: {result.get('breakdown', {}).get('hard_match_score', 0):.1f}%
- Semantic Score: {result.get('breakdown', {}).get('semantic_score', 0):.1f}%
- Experience Score: {result.get('breakdown', {}).get('experience_score', 0):.1f}%

SKILLS ANALYSIS
--------------
Matched Skills:
{chr(10).join(['• ' + skill for skill in result.get('breakdown', {}).get('matched_skills', [])])}

Missing Required Skills:
{chr(10).join(['• ' + skill for skill in result.get('breakdown', {}).get('missing_required_skills', [])])}

RECOMMENDATIONS
--------------
{chr(10).join(['• ' + rec for rec in result.get('breakdown', {}).get('recommendations', [])])}

FEEDBACK
--------
{result.get('feedback', 'No feedback available')}
"""
    return report

if __name__ == "__main__":
    main()