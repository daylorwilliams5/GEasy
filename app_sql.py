import streamlit as st
import duckdb
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="GEasy — GE Course Recommender", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86C1;
        font-size: 3rem;
        margin-bottom: 2rem;
    }
    .college-info {
        background-color: #EBF5FB;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #F8F9FA;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .status-success { color: #28a745; }
    .status-warning { color: #ffc107; }
    .status-error { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🧠 GEasy — GE Course Recommender</h1>', unsafe_allow_html=True)

DB_PATH = os.environ.get("GEASY_DB_PATH", "geasy.duckdb")
con = duckdb.connect(DB_PATH)

# Execute schema
try:
    con.execute(open("schema.sql","r", encoding="utf-8").read())
    schema_loaded = True
except FileNotFoundError:
    st.error("❌ Schema file not found. Please ensure schema.sql exists.")
    schema_loaded = False
except Exception as e:
    st.error(f"❌ Error loading schema: {e}")
    schema_loaded = False

if not schema_loaded:
    st.stop()

# Check if we have data and offer to load/enhance it
def check_data_status():
    """Check what data we have in the database"""
    try:
        course_count = con.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        review_count = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        prof_count = con.execute("SELECT COUNT(*) FROM professors").fetchone()[0]
        return course_count, review_count, prof_count
    except:
        return 0, 0, 0

course_count, review_count, prof_count = check_data_status()

# Data status and management section
st.sidebar.header("📊 Data Status")
col1, col2, col3 = st.sidebar.columns(3)
with col1:
    st.metric("Courses", f"{course_count:,}")
with col2:
    st.metric("Reviews", f"{review_count:,}")
with col3:
    st.metric("Professors", f"{prof_count:,}")

# Data management buttons
if course_count == 0:
    st.sidebar.warning("⚠️ No course data found")
    if st.sidebar.button("🔄 Load Initial Data", help="Load data from CSV files"):
        with st.spinner("Loading initial data..."):
            try:
                # Try to run build_db.py
                import subprocess
                result = subprocess.run(['python', 'build_db.py'], capture_output=True, text=True)
                if result.returncode == 0:
                    st.sidebar.success("✅ Data loaded successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.sidebar.error(f"❌ Error loading data: {result.stderr}")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {e}")

elif review_count < 100:
    st.sidebar.info("💡 Consider enhancing with BruinWalk reviews")
    if st.sidebar.button("🔄 Enhance with BruinWalk", help="Add real student reviews from BruinWalk"):
        with st.spinner("Fetching BruinWalk reviews... This may take a few minutes."):
            try:
                # Use the improved scraper
                from improved_bruinwalk_scraper import BruinWalkEnhancer
                
                enhancer = BruinWalkEnhancer(delay=2.0)
                
                # Show progress
                progress_bar = st.sidebar.progress(0)
                status_text = st.sidebar.empty()
                
                status_text.text("Enhancing courses with BruinWalk data...")
                enhanced_count = enhancer.enhance_existing_courses(limit=30)
                progress_bar.progress(1.0)
                
                if enhanced_count > 0:
                    st.sidebar.success(f"✅ Enhanced {enhanced_count} courses!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.sidebar.warning("⚠️ No courses could be enhanced")
                    
            except ImportError:
                st.sidebar.error("❌ BruinWalk enhancer not found")
            except Exception as e:
                st.sidebar.error(f"❌ Enhancement error: {str(e)}")

# College definitions (same as before)
COLLEGES = {
    "Arts and Architecture/Music": {
        "name": "School of the Arts and Architecture / Herb Alpert School of Music",
        "requirements": {
            "Literary and Cultural Analysis": 1,
            "Philosophic and Linguistic Analysis": 1, 
            "Visual and Performance Arts Analysis and Practice": 1,
            "Historical Analysis": 1,
            "Social Analysis": 1,
            "Society and Culture (3rd course)": 1,
            "Life Sciences": 2,
            "Physical Sciences": 0
        },
        "total_courses": 8,
        "total_units": 38,
        "notes": "Major courses cannot satisfy Arts & Humanities requirements"
    },
    "Education and Information Studies/Letters and Science/Public Affairs": {
        "name": "School of Education / College of Letters and Science / Luskin School of Public Affairs",
        "requirements": {
            "Literary and Cultural Analysis": 1,
            "Philosophic and Linguistic Analysis": 1,
            "Visual and Performance Arts Analysis and Practice": 1, 
            "Historical Analysis": 1,
            "Social Analysis": 1,
            "Society and Culture (3rd course)": 1,
            "Life Sciences": 2,
            "Physical Sciences": 2
        },
        "total_courses": 10,
        "total_units": 47,
        "notes": "One course must have lab/demo/Writing II credit"
    },
    "Engineering and Applied Science": {
        "name": "Henry Samueli School of Engineering and Applied Science",
        "requirements": {
            "Literary and Cultural Analysis": 2,
            "Philosophic and Linguistic Analysis": 0,
            "Visual and Performance Arts Analysis and Practice": 0,
            "Historical Analysis": 1,
            "Social Analysis": 1,
            "Society and Culture (3rd course)": 0,
            "Life Sciences": 1,
            "Physical Sciences": 0
        },
        "total_courses": 5,
        "total_units": 24,
        "notes": "Minimum requirements - additional school requirements apply"
    },
    "Nursing": {
        "name": "School of Nursing", 
        "requirements": {
            "Literary and Cultural Analysis": 1,
            "Philosophic and Linguistic Analysis": 1,
            "Visual and Performance Arts Analysis and Practice": 1,
            "Historical Analysis": 1,
            "Social Analysis": 1,
            "Society and Culture (3rd course)": 1,
            "Life Sciences": 2,
            "Physical Sciences": 2
        },
        "total_courses": 10,
        "total_units": 48,
        "notes": "Major prep courses may overlap with GE"
    },
    "Theater, Film, and Television": {
        "name": "School of Theater, Film, and Television",
        "requirements": {
            "Literary and Cultural Analysis": 5,
            "Philosophic and Linguistic Analysis": 0,
            "Visual and Performance Arts Analysis and Practice": 0,
            "Historical Analysis": 1,
            "Social Analysis": 1,
            "Society and Culture (3rd course)": 1,
            "Life Sciences": 1,
            "Physical Sciences": 1
        },
        "total_courses": 10,
        "total_units": 48,
        "notes": "Max 2 courses per subgroup in Literary & Cultural Analysis"
    }
}

# Sidebar college selection
st.sidebar.header("🎓 Select Your School")
college_key = st.sidebar.selectbox(
    "UCLA School/College",
    options=list(COLLEGES.keys()),
    format_func=lambda x: COLLEGES[x]["name"].split(" / ")[0]  # Shorter display
)

selected_college = COLLEGES[college_key]

# Display requirements
st.sidebar.markdown(f"""
<div class="college-info">
    <h4>📋 Your GE Requirements</h4>
    <p><strong>Total:</strong> {selected_college['total_courses']} courses ({selected_college['total_units']} units)</p>
</div>
""", unsafe_allow_html=True)

for req_area, num_courses in selected_college["requirements"].items():
    if num_courses > 0:
        st.sidebar.write(f"• {req_area}: **{num_courses}** course{'s' if num_courses > 1 else ''}")

if selected_college["notes"]:
    st.sidebar.info(f"💡 {selected_college['notes']}")

# Check if we have any data to work with
if course_count == 0:
    st.warning("⚠️ No course data found. Please load your initial data using the sidebar.")
    st.info("💡 Make sure you have your CSV files (courses.csv, professors.csv, sections.csv, reviews.csv) in a 'data/' directory, then click 'Load Initial Data'.")
    st.stop()

# Get available GE areas
try:
    areas = [r[0] for r in con.execute("""
        SELECT DISTINCT ge_area 
        FROM courses 
        WHERE ge_area IS NOT NULL AND ge_area != ''
        ORDER BY ge_area
    """).fetchall()]
except:
    st.error("❌ Could not load GE areas from database")
    st.stop()

if not areas:
    st.warning("⚠️ No GE areas found in course data")
    st.stop()

# Filter controls
st.sidebar.header("🔍 Filter Courses")
area = st.sidebar.selectbox("GE Area", areas)

# Show what this area fulfills
fulfills = []
for req_name, req_count in selected_college["requirements"].items():
    if req_count > 0 and any(word in req_name.lower() for word in area.lower().split()):
        fulfills.append(f"{req_name} ({req_count} needed)")

if fulfills:
    st.info(f"✅ **{area}** fulfills: {', '.join(fulfills)}")
else:
    st.warning(f"⚠️ **{area}** may not fulfill requirements for your college")

# Advanced filters
with st.sidebar.expander("Advanced Filters"):
    min_q = st.slider("Min Quality", 1.0, 5.0, 2.5, 0.1)
    max_w = st.slider("Max Workload", 1, 10, 8)
    min_reviews = st.slider("Min Reviews", 1, 20, 1)
    top_n = st.number_input("Results to Show", 1, 100, 20)

# Main query
if review_count > 0:
    # If we have reviews, use the full ranking system
    query = '''
    WITH course_stats AS (
      SELECT 
        c.course_id,
        c.dept,
        c.number,
        c.title, 
        c.ge_area,
        p.name AS professor,
        COUNT(r.review_id) as review_count,
        AVG(CAST(r.quality AS FLOAT)) AS avg_quality, 
        AVG(CAST(r.workload AS FLOAT)) AS avg_workload,
        (AVG(CAST(r.quality AS FLOAT)) * 0.7 + (11 - AVG(CAST(r.workload AS FLOAT))) * 0.3) AS score
      FROM courses c
      JOIN sections s ON s.course_id = c.course_id
      JOIN professors p ON p.prof_id = s.prof_id
      JOIN reviews r ON r.section_id = s.section_id
      WHERE c.ge_area = ?
      GROUP BY c.course_id, c.dept, c.number, c.title, c.ge_area, p.name
      HAVING COUNT(r.review_id) >= ?
    )
    SELECT 
      dept || ' ' || number as course_code,
      title,
      professor,
      review_count,
      ROUND(avg_quality, 2) as avg_quality,
      ROUND(avg_workload, 2) as avg_workload,
      ROUND(score, 2) as score
    FROM course_stats
    WHERE avg_quality >= ? AND avg_workload <= ?
    ORDER BY score DESC, avg_quality DESC
    LIMIT ?
    '''
    
    try:
        df = con.execute(query, [area, min_reviews, min_q, max_w, int(top_n)]).df()
    except Exception as e:
        st.error(f"❌ Error with review-based query: {e}")
        df = pd.DataFrame()
else:
    # If no reviews, just show courses by title
    query = '''
    SELECT DISTINCT
      c.dept || ' ' || c.number as course_code,
      c.title,
      'No reviews available' as professor,
      0 as review_count,
      0.0 as avg_quality,
      0.0 as avg_workload,
      0.0 as score
    FROM courses c
    WHERE c.ge_area = ?
    ORDER BY c.dept, c.number
    LIMIT ?
    '''
    
    try:
        df = con.execute(query, [area, int(top_n)]).df()
    except Exception as e:
        st.error(f"❌ Error with basic query: {e}")
        df = pd.DataFrame()

# Display results
if df.empty:
    st.warning(f"🔍 No courses found for **{area}** with your current filters.")
    if min_q > 1.0 or max_w < 10 or min_reviews > 1:
        st.info("💡 Try relaxing your filters to see more results.")
else:
    st.header(f"🏆 Best {area} Courses")
    
    # Summary stats
    if review_count > 0:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Courses Found", len(df))
        with col2:
            avg_quality = df['avg_quality'].mean() if df['avg_quality'].sum() > 0 else 0
            st.metric("Avg Quality", f"{avg_quality:.1f}/5.0")
        with col3:
            avg_workload = df['avg_workload'].mean() if df['avg_workload'].sum() > 0 else 0
            st.metric("Avg Workload", f"{avg_workload:.1f}/10")
        with col4:
            total_reviews = df['review_count'].sum()
            st.metric("Total Reviews", f"{total_reviews:,}")
        
        # Visualization if we have meaningful data
        if df['avg_quality'].sum() > 0:
            fig = px.scatter(
                df, 
                x='avg_workload', 
                y='avg_quality',
                size='review_count',
                color='score',
                hover_data=['course_code', 'professor'],
                title="Course Quality vs Workload",
                labels={
                    'avg_workload': 'Workload (lower = easier)',
                    'avg_quality': 'Quality (higher = better)'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Results table
    st.subheader("📋 Course List")
    
    # Style the dataframe
    if review_count > 0:
        # Color code based on scores
        def highlight_scores(row):
            styles = []
            for col in row.index:
                if col == 'score':
                    if row[col] >= 7:
                        styles.append('background-color: #d4edda')
                    elif row[col] >= 5:
                        styles.append('background-color: #fff3cd') 
                    else:
                        styles.append('background-color: #f8d7da')
                elif col == 'avg_quality':
                    if row[col] >= 4:
                        styles.append('background-color: #d4edda')
                    elif row[col] >= 3:
                        styles.append('background-color: #fff3cd')
                    else:
                        styles.append('background-color: #f8d7da')
                elif col == 'avg_workload':
                    if row[col] <= 4:
                        styles.append('background-color: #d4edda')
                    elif row[col] <= 6:
                        styles.append('background-color: #fff3cd')
                    else:
                        styles.append('background-color: #f8d7da')
                else:
                    styles.append('')
            return styles
        
        try:
            styled_df = df.style.apply(highlight_scores, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        except:
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Export options
    col1, col2 = st.columns(2)
    with col1:
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download CSV",
            csv_data,
            f"geasy_{area.lower().replace(' ', '_')}.csv",
            "text/csv"
        )
    
    with col2:
        # Create a simple report
        report = f"""# GEasy Recommendations: {area}

**College:** {selected_college['name']}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Filters Applied
- Minimum Quality: {min_q}/5.0
- Maximum Workload: {max_w}/10  
- Minimum Reviews: {min_reviews}

## Top Courses Found: {len(df)}

"""
        for idx, row in df.iterrows():
            report += f"### {row['course_code']} - {row['title']}\n"
            if row['review_count'] > 0:
                report += f"- Professor: {row['professor']}\n"
                report += f"- Quality: {row['avg_quality']}/5.0\n"
                report += f"- Workload: {row['avg_workload']}/10\n"
                report += f"- Reviews: {row['review_count']}\n\n"
            else:
                report += "- No reviews available\n\n"
        
        st.download_button(
            "📄 Download Report",
            report.encode('utf-8'),
            f"geasy_{area.lower().replace(' ', '_')}_report.md",
            "text/markdown"
        )

# Help section
with st.expander("❓ How to Use GEasy"):
    st.markdown("""
    ### 🎯 Quick Start
    1. **Select your UCLA school** (sidebar) to see your specific GE requirements
    2. **Choose a GE area** you need to fulfill
    3. **Adjust filters** based on your preferences
    4. **Review results** - courses are ranked by quality and ease
    
    ### 📊 Understanding the Data
    - **Quality (1-5):** How good students think the course is
    - **Workload (1-10):** How much work/difficulty (lower = easier)
    - **Score:** Combined rating favoring high quality + manageable workload
    
    ### 💡 Tips for Best Results
    - Start with relaxed filters to see all options
    - Look for courses with multiple reviews for reliability  
    - Consider your current course load when choosing workload limits
    - Check if courses fulfill multiple requirements for your college
    
    ### 🔄 Enhancing Your Data
    - Use "Enhance with BruinWalk" to add real student reviews
    - This connects to UCLA's BruinWalk platform for authentic feedback
    - More reviews = more reliable recommendations
    """)

# Progress tracker (simplified)
with st.expander("📈 GE Progress Tracker"):
    st.info("💡 **Feature Preview:** Track your completed GE requirements")
    
    progress_data = []
    for req_area, req_count in selected_college["requirements"].items():
        if req_count > 0:
            progress_data.append({
                "Requirement": req_area,
                "Courses Needed": req_count,
                "Status": "Not Started"  # In future: track actual progress
            })
    
    if progress_data:
        progress_df = pd.DataFrame(progress_data)
        st.dataframe(progress_df, use_container_width=True, hide_index=True)
        st.write("*Coming soon: Save completed courses and track progress automatically*")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7F8C8D; padding: 1rem;'>
    <p><strong>🧠 GEasy</strong> - Making UCLA GE requirements simple</p>
    <p>Built for UCLA students • Enhanced with BruinWalk reviews</p>
</div>
""", unsafe_allow_html=True)

# Debug info (only show if there are issues)
if st.sidebar.checkbox("🔧 Show Debug Info"):
    st.subheader("Debug Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Database Status:**")
        st.write(f"- Courses: {course_count}")
        st.write(f"- Reviews: {review_count}")  
        st.write(f"- Professors: {prof_count}")
        
    with col2:
        st.write("**Available GE Areas:**")
        for area in areas:
            course_count_for_area = con.execute(
                "SELECT COUNT(*) FROM courses WHERE ge_area = ?", [area]
            ).fetchone()[0]
            st.write(f"- {area}: {course_count_for_area} courses")
    
    if st.button("Test Database Connection"):
        try:
            test_result = con.execute("SELECT 1").fetchone()
            st.success("✅ Database connection working!")
        except Exception as e:
            st.error(f"❌ Database error: {e}")