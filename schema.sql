-- Enhanced schema for GEasy with college-specific requirements

CREATE TABLE IF NOT EXISTS courses (
  course_id INTEGER PRIMARY KEY,
  dept TEXT NOT NULL,
  number TEXT NOT NULL,
  title TEXT NOT NULL,
  ge_area TEXT,
  units INTEGER DEFAULT 4,
  has_lab BOOLEAN DEFAULT FALSE,
  has_writing_ii BOOLEAN DEFAULT FALSE,
  description TEXT,
  prerequisites TEXT
);

CREATE TABLE IF NOT EXISTS professors (
  prof_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  department TEXT,
  overall_rating DECIMAL(3,2)
);

CREATE TABLE IF NOT EXISTS sections (
  section_id INTEGER PRIMARY KEY,
  course_id INTEGER REFERENCES courses(course_id),
  prof_id INTEGER REFERENCES professors(prof_id),
  term TEXT NOT NULL,
  year INTEGER NOT NULL,
  section_code TEXT,
  enrollment_cap INTEGER,
  enrollment_current INTEGER
);

CREATE TABLE IF NOT EXISTS reviews (
  review_id INTEGER PRIMARY KEY,
  section_id INTEGER REFERENCES sections(section_id),
  quality INTEGER CHECK (quality >= 1 AND quality <= 5),
  workload INTEGER CHECK (workload >= 1 AND workload <= 10),
  text TEXT,
  review_date DATE,
  would_recommend BOOLEAN,
  grade_received TEXT
);

-- Table for college/school information
CREATE TABLE IF NOT EXISTS colleges (
  college_id INTEGER PRIMARY KEY,
  college_name TEXT NOT NULL,
  college_short_name TEXT NOT NULL,
  total_ge_courses INTEGER,
  total_ge_units INTEGER
);

-- Table for specific GE requirements by college
CREATE TABLE IF NOT EXISTS ge_requirements (
  requirement_id INTEGER PRIMARY KEY,
  college_id INTEGER REFERENCES colleges(college_id),
  ge_area TEXT NOT NULL,
  courses_required INTEGER DEFAULT 1,
  units_required INTEGER,
  special_notes TEXT
);

-- Table for tracking GE area mappings (for complex requirements)
CREATE TABLE IF NOT EXISTS ge_area_mappings (
  mapping_id INTEGER PRIMARY KEY,
  ge_area TEXT NOT NULL,
  foundation_area TEXT NOT NULL, -- Arts/Humanities, Society/Culture, Scientific Inquiry
  subgroup TEXT -- Literary/Cultural, Historical, Life Sciences, etc.
);

-- Insert college data
INSERT OR REPLACE INTO colleges VALUES 
(1, 'School of the Arts and Architecture / Herb Alpert School of Music', 'Arts and Architecture/Music', 8, 38),
(2, 'School of Education and Information Studies / College of Letters and Science / Luskin School of Public Affairs', 'Education and Information Studies/Letters and Science/Public Affairs', 10, 47),
(3, 'Henry Samueli School of Engineering and Applied Science', 'Engineering and Applied Science', 5, 24),
(4, 'School of Nursing', 'Nursing', 10, 48),
(5, 'School of Theater, Film, and Television', 'Theater, Film, and Television', 10, 48);

-- Insert GE requirements data
INSERT OR REPLACE INTO ge_requirements VALUES 
-- Arts and Architecture/Music
(1, 1, 'Literary and Cultural Analysis', 1, 5, NULL),
(2, 1, 'Philosophic and Linguistic Analysis', 1, 5, NULL),
(3, 1, 'Visual and Performance Arts Analysis and Practice', 1, 5, NULL),
(4, 1, 'Historical Analysis', 1, 5, NULL),
(5, 1, 'Social Analysis', 1, 5, NULL),
(6, 1, 'Society and Culture Additional', 1, 5, 'Third course from either Historical or Social Analysis'),
(7, 1, 'Life Sciences', 2, 8, 'If both from same subgroup, must be different departments'),

-- Letters and Science (and similar colleges)
(8, 2, 'Literary and Cultural Analysis', 1, 5, NULL),
(9, 2, 'Philosophic and Linguistic Analysis', 1, 5, NULL),
(10, 2, 'Visual and Performance Arts Analysis and Practice', 1, 5, NULL),
(11, 2, 'Historical Analysis', 1, 5, NULL),
(12, 2, 'Social Analysis', 1, 5, NULL),
(13, 2, 'Society and Culture Additional', 1, 5, 'Third course from either Historical or Social Analysis'),
(14, 2, 'Life Sciences', 2, 8, 'Two from each subgroup'),
(15, 2, 'Physical Sciences', 2, 9, 'One course must have lab/demo/Writing II credit'),

-- Engineering
(16, 3, 'Literary and Cultural Analysis', 2, 10, 'Each from different subgroup'),
(17, 3, 'Historical Analysis', 1, 5, NULL),
(18, 3, 'Social Analysis', 1, 5, NULL),
(19, 3, 'Life Sciences', 1, 4, NULL),

-- Nursing
(20, 4, 'Literary and Cultural Analysis', 1, 5, NULL),
(21, 4, 'Philosophic and Linguistic Analysis', 1, 5, NULL),
(22, 4, 'Visual and Performance Arts Analysis and Practice', 1, 5, NULL),
(23, 4, 'Historical Analysis', 1, 5, NULL),
(24, 4, 'Social Analysis', 1, 5, NULL),
(25, 4, 'Society and Culture Additional', 1, 5, 'Third course from either Historical or Social Analysis'),
(26, 4, 'Life Sciences', 2, 8, NULL),
(27, 4, 'Physical Sciences', 2, 10, NULL),

-- Theater, Film, and Television  
(28, 5, 'Literary and Cultural Analysis', 5, 25, 'Not more than two in any one subgroup'),
(29, 5, 'Historical Analysis', 1, 5, NULL),
(30, 5, 'Social Analysis', 1, 5, NULL),
(31, 5, 'Society and Culture Additional', 1, 5, 'Third course from either Historical or Social Analysis'),
(32, 5, 'Life Sciences', 1, 4, NULL),
(33, 5, 'Physical Sciences', 1, 4, NULL);

-- Insert GE area mappings
INSERT OR REPLACE INTO ge_area_mappings VALUES
(1, 'Literary and Cultural Analysis', 'Arts and Humanities', 'Literary and Cultural Analysis'),
(2, 'Philosophic and Linguistic Analysis', 'Arts and Humanities', 'Philosophic and Linguistic Analysis'),
(3, 'Visual and Performance Arts Analysis and Practice', 'Arts and Humanities', 'Visual and Performance Arts'),
(4, 'Historical Analysis', 'Society and Culture', 'Historical Analysis'),
(5, 'Social Analysis', 'Society and Culture', 'Social Analysis'),
(6, 'Life Sciences', 'Scientific Inquiry', 'Life Sciences'),
(7, 'Physical Sciences', 'Scientific Inquiry', 'Physical Sciences');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_courses_ge_area ON courses(ge_area);
CREATE INDEX IF NOT EXISTS idx_sections_course_id ON sections(course_id);
CREATE INDEX IF NOT EXISTS idx_sections_prof_id ON sections(prof_id);
CREATE INDEX IF NOT EXISTS idx_reviews_section_id ON reviews(section_id);
CREATE INDEX IF NOT EXISTS idx_reviews_quality ON reviews(quality);
CREATE INDEX IF NOT EXISTS idx_reviews_workload ON reviews(workload);