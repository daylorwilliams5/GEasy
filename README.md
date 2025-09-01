# GEasy — GE Course Recommender 

## Overview
GEasy is a course recommender tool designed to make UCLA’s General Education (GE) requirements easier to navigate.  
While UCLA provides GE requirement lists, students often find it confusing and time-consuming to identify courses that fit their schedule and interests. GEasy solves this by storing GE courses in a searchable database — built off real student data about which classes are most useful and popular — and offering a clean interface to explore options.  

## Motivation
Choosing GE classes at UCLA is frustrating. The official tools are static and difficult to filter by student needs. I built GEasy to simplify this process, helping students quickly discover courses that meet requirements while also aligning with their academic goals.  

## Features
- **Course Database** – curated from UCLA GE requirements and real student data  
- **Search by Requirement** – filter courses by GE category, department, or schedule  
- **Interactive Interface** – lightweight frontend to explore courses more easily  
- **DuckDB + SQL Backend** – efficient storage and querying of course data  

## Quickstart
pip install -r requirements.txt

python build_db.py

streamlit run app_sql.py

Try searches like:  
- "Life Sciences GE"  
- "Humanities GE"  
- "Courses that satisfy Writing II"  

Results are displayed instantly from the database.  

## Screenshot 
<img width="1449" height="709" alt="Screenshot 2025-09-01 at 3 39 38 PM" src="https://github.com/user-attachments/assets/b4065f22-e3ad-42b6-9982-c63302a2dc01" />


## Tech Stack
- Python (pandas, sqlite/duckdb)  
- BeautifulSoup / custom scrapers for course data  
- SQL schema for structured storage  
- Streamlit (for frontend)  
- GitHub Pages for deployment  

## Status
The project is in active development. Planned improvements include: 
- Adding more student reviews 
- Expanding coverage to non-GE electives  
- Adding advanced filters (e.g., time of day, professor)  
- Improving UI for a smoother student experience  

## Author
Daylor Williams – UCLA Cognitive Science + Computing | AI + Product Builder

