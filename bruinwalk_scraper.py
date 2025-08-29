import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import re
import json
import duckdb
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, quote

class BruinWalkEnhancer:
    """
    Enhanced BruinWalk scraper that works with your existing course data
    """
    
    def __init__(self, delay=2.0):
        self.base_url = "https://bruinwalk.com"
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def course_to_url_slug(self, dept: str, number: str) -> str:
        """
        Convert course department and number to BruinWalk URL slug
        e.g., 'COM SCI' + '174A' -> 'com-sci-174a'
        """
        # Clean and format department
        dept_clean = dept.strip().lower().replace(' ', '-').replace('&', 'and')
        number_clean = number.strip().lower()
        return f"{dept_clean}-{number_clean}"
    
    def get_course_reviews(self, dept: str, number: str) -> Optional[Dict]:
        """
        Get reviews for a specific course from BruinWalk
        
        Args:
            dept: Department code (e.g., 'COM SCI', 'MATH')
            number: Course number (e.g., '174A', '32A')
            
        Returns:
            Dictionary with course reviews and ratings, or None if not found
        """
        slug = self.course_to_url_slug(dept, number)
        course_url = f"{self.base_url}/classes/{slug}/"
        
        try:
            response = self.session.get(course_url)
            if response.status_code == 404:
                self.logger.warning(f"Course {dept} {number} not found on BruinWalk")
                return None
                
            response.raise_for_status()
            time.sleep(self.delay)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            course_data = {
                'dept': dept,
                'number': number,
                'course_code': f"{dept} {number}",
                'url': course_url,
                'title': '',
                'overall_rating': 0.0,
                'total_reviews': 0,
                'professors': [],
                'reviews': []
            }
            
            # Extract course title
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                title_text = title_elem.get_text().strip()
                # Remove course code from title if present
                if ' - ' in title_text:
                    course_data['title'] = title_text.split(' - ', 1)[-1]
                else:
                    course_data['title'] = title_text
            
            # Find all professor sections
            prof_sections = soup.find_all('div', class_=re.compile(r'professor|instructor', re.I))
            if not prof_sections:
                # Try alternative selectors
                prof_sections = soup.find_all('div', attrs={'data-professor': True})
                if not prof_sections:
                    prof_sections = soup.find_all('h3')  # Fallback to h3 headers
            
            for prof_section in prof_sections:
                prof_data = self._extract_professor_reviews(prof_section, dept, number)
                if prof_data and prof_data['reviews']:
                    course_data['professors'].append(prof_data)
                    course_data['reviews'].extend(prof_data['reviews'])
            
            course_data['total_reviews'] = len(course_data['reviews'])
            
            # Calculate overall rating
            if course_data['reviews']:
                qualities = [r['quality'] for r in course_data['reviews'] if r['quality'] > 0]
                course_data['overall_rating'] = sum(qualities) / len(qualities) if qualities else 0.0
            
            return course_data if course_data['total_reviews'] > 0 else None
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {course_url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing course data for {dept} {number}: {e}")
            return None
    
    def _extract_professor_reviews(self, section, dept: str, number: str) -> Optional[Dict]:
        """Extract reviews for a specific professor from a page section"""
        try:
            prof_data = {
                'name': 'Unknown',
                'rating': 0.0,
                'reviews': []
            }
            
            # Extract professor name
            name_elem = section.find(['h3', 'h4']) or section.find(class_=re.compile(r'name|professor', re.I))
            if name_elem:
                prof_data['name'] = name_elem.get_text().strip()
            
            # Find review elements
            review_elements = section.find_all('div', class_=re.compile(r'review', re.I))
            if not review_elements:
                # Alternative: look for rating patterns
                review_elements = section.find_all('div', string=re.compile(r'\d+(\.\d+)?.*?/.*?5'))
            
            for review_elem in review_elements:
                review_data = self._parse_review_element(review_elem, prof_data['name'], dept, number)
                if review_data:
                    prof_data['reviews'].append(review_data)
            
            # Calculate professor average rating
            if prof_data['reviews']:
                qualities = [r['quality'] for r in prof_data['reviews'] if r['quality'] > 0]
                prof_data['rating'] = sum(qualities) / len(qualities) if qualities else 0.0
            
            return prof_data if prof_data['reviews'] else None
            
        except Exception as e:
            self.logger.error(f"Error extracting professor reviews: {e}")
            return None
    
    def _parse_review_element(self, elem, professor: str, dept: str, number: str) -> Optional[Dict]:
        """Parse individual review element"""
        try:
            review_data = {
                'professor': professor,
                'dept': dept,
                'number': number,
                'quality': 0.0,
                'workload': 0.0,
                'text': '',
                'quarter': '',
                'year': 2024,
                'grade': '',
                'would_recommend': None
            }
            
            # Extract review text
            text_elem = elem.find(string=True) or elem
            if hasattr(text_elem, 'get_text'):
                review_data['text'] = text_elem.get_text().strip()[:500]  # Limit length
            elif isinstance(text_elem, str):
                review_data['text'] = text_elem.strip()[:500]
            
            # Extract numerical ratings using regex
            text_content = elem.get_text() if hasattr(elem, 'get_text') else str(elem)
            
            # Look for rating patterns (e.g., "4.5/5", "3 out of 5", "Rating: 4.2")
            quality_patterns = [
                r'(\d+(?:\.\d+)?)\s*/\s*5',  # "4.5/5"
                r'(\d+(?:\.\d+)?)\s*out\s*of\s*5',  # "4 out of 5"
                r'rating:?\s*(\d+(?:\.\d+)?)',  # "Rating: 4.2"
                r'quality:?\s*(\d+(?:\.\d+)?)',  # "Quality: 4.2"
            ]
            
            for pattern in quality_patterns:
                match = re.search(pattern, text_content, re.I)
                if match:
                    try:
                        rating = float(match.group(1))
                        if 0 <= rating <= 5:
                            review_data['quality'] = rating
                            break
                    except (ValueError, IndexError):
                        continue
            
            # Look for workload/difficulty patterns
            workload_patterns = [
                r'workload:?\s*(\d+(?:\.\d+)?)',  # "Workload: 3.5"
                r'difficulty:?\s*(\d+(?:\.\d+)?)',  # "Difficulty: 7"
                r'(\d+(?:\.\d+)?)\s*/\s*10.*?(?:workload|difficulty)',  # "7/10 difficulty"
            ]
            
            for pattern in workload_patterns:
                match = re.search(pattern, text_content, re.I)
                if match:
                    try:
                        workload = float(match.group(1))
                        if 0 <= workload <= 10:
                            review_data['workload'] = workload
                            break
                    except (ValueError, IndexError):
                        continue
            
            # Extract quarter/year
            quarter_pattern = r'(fall|winter|spring|summer)\s*(\d{4})'
            quarter_match = re.search(quarter_pattern, text_content, re.I)
            if quarter_match:
                review_data['quarter'] = quarter_match.group(1).title()
                review_data['year'] = int(quarter_match.group(2))
            
            # Extract grade
            grade_pattern = r'\b([A-F][+-]?|P|NP)\b'
            grade_match = re.search(grade_pattern, text_content)
            if grade_match:
                review_data['grade'] = grade_match.group(1)
            
            # Only return if we have some meaningful data
            if review_data['quality'] > 0 or len(review_data['text']) > 10:
                return review_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing review element: {e}")
            return None
    
    def enhance_existing_courses(self, db_path: str = "geasy.duckdb", limit: int = 50) -> int:
        """
        Enhance your existing course data with BruinWalk reviews
        
        Args:
            db_path: Path to your existing database
            limit: Maximum number of courses to enhance (for testing)
            
        Returns:
            Number of courses successfully enhanced
        """
        con = duckdb.connect(db_path)
        
        # Get existing courses
        try:
            courses_df = con.execute("""
                SELECT DISTINCT dept, number, title, ge_area 
                FROM courses 
                WHERE dept IS NOT NULL AND number IS NOT NULL
                ORDER BY dept, number
                LIMIT ?
            """, [limit]).df()
        except:
            self.logger.error("Could not read existing courses from database")
            return 0
        
        enhanced_count = 0
        
        for idx, course in courses_df.iterrows():
            self.logger.info(f"Enhancing {course['dept']} {course['number']} ({idx+1}/{len(courses_df)})")
            
            # Get BruinWalk data for this course
            bruinwalk_data = self.get_course_reviews(course['dept'], course['number'])
            
            if bruinwalk_data and bruinwalk_data['reviews']:
                # Add this course's BruinWalk data to database
                self._save_course_to_db(bruinwalk_data, course['ge_area'], con)
                enhanced_count += 1
                self.logger.info(f"✅ Enhanced {course['dept']} {course['number']} with {len(bruinwalk_data['reviews'])} reviews")
            else:
                self.logger.warning(f"⚠️  No BruinWalk data found for {course['dept']} {course['number']}")
            
            # Rate limiting
            time.sleep(self.delay)
        
        con.close()
        self.logger.info(f"Enhanced {enhanced_count} courses with BruinWalk data")
        return enhanced_count
    
    def _save_course_to_db(self, course_data: Dict, ge_area: str, con):
        """Save BruinWalk course data to database"""
        try:
            # Get or create course
            course_result = con.execute("""
                SELECT course_id FROM courses 
                WHERE dept = ? AND number = ?
            """, [course_data['dept'], course_data['number']]).fetchone()
            
            if course_result:
                course_id = course_result[0]
            else:
                # Insert new course
                course_id = con.execute("SELECT MAX(course_id) + 1 FROM courses").fetchone()[0] or 1
                con.execute("""
                    INSERT INTO courses (course_id, dept, number, title, ge_area)
                    VALUES (?, ?, ?, ?, ?)
                """, [course_id, course_data['dept'], course_data['number'], 
                     course_data.get('title', ''), ge_area])
            
            # Process reviews by professor
            professor_cache = {}
            
            # Get existing professors
            existing_profs = con.execute("SELECT prof_id, name FROM professors").fetchall()
            for prof_id, name in existing_profs:
                professor_cache[name] = prof_id
            
            next_prof_id = con.execute("SELECT MAX(prof_id) + 1 FROM professors").fetchone()[0] or 1
            next_section_id = con.execute("SELECT MAX(section_id) + 1 FROM sections").fetchone()[0] or 1
            next_review_id = con.execute("SELECT MAX(review_id) + 1 FROM reviews").fetchone()[0] or 1
            
            for review in course_data['reviews']:
                prof_name = review['professor']
                
                # Get or create professor
                if prof_name not in professor_cache:
                    con.execute("""
                        INSERT INTO professors (prof_id, name)
                        VALUES (?, ?)
                    """, [next_prof_id, prof_name])
                    professor_cache[prof_name] = next_prof_id
                    next_prof_id += 1
                
                current_prof_id = professor_cache[prof_name]
                
                # Insert section
                con.execute("""
                    INSERT INTO sections (section_id, course_id, prof_id, term, year)
                    VALUES (?, ?, ?, ?, ?)
                """, [next_section_id, course_id, current_prof_id, 
                     review.get('quarter', 'Unknown'), review.get('year', 2024)])
                
                # Insert review - convert ratings to expected scales
                quality = max(1, min(5, int(review.get('quality', 3))))
                workload = max(1, min(10, int(review.get('workload', 5)) if review.get('workload', 0) > 0 else 5))
                
                con.execute("""
                    INSERT INTO reviews (review_id, section_id, quality, workload, text)
                    VALUES (?, ?, ?, ?, ?)
                """, [next_review_id, next_section_id, quality, workload, review.get('text', '')[:500]])
                
                next_section_id += 1
                next_review_id += 1
                
        except Exception as e:
            self.logger.error(f"Error saving course to database: {e}")


def main():
    """Example usage - enhance existing courses with BruinWalk data"""
    enhancer = BruinWalkEnhancer(delay=2.0)
    
    print("🔄 Enhancing existing courses with BruinWalk reviews...")
    print("This will take your existing course data and add real BruinWalk reviews to it.")
    
    # Start with a small number for testing
    enhanced_count = enhancer.enhance_existing_courses(limit=20)
    
    print(f"\n✅ Enhanced {enhanced_count} courses with BruinWalk data!")
    print("You can now run your Streamlit app to see the enhanced course recommendations.")


if __name__ == "__main__":
    main()