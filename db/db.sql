CREATE TABLE Users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    admission_date DATE,
    is_professor BOOLEAN
);

CREATE TABLE Courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    nrc VARCHAR(50)
);

CREATE TABLE CoursePrerequisites (
    course_id INT,
    prerequisite_id INT,
    PRIMARY KEY (course_id, prerequisite_id),
    FOREIGN KEY (course_id) REFERENCES Courses(id),
    FOREIGN KEY (prerequisite_id) REFERENCES Courses(id)
);

CREATE TABLE Sections (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course_id INT,
    period VARCHAR(50),
    number INT,
    professor_id INT,
    FOREIGN KEY (course_id) REFERENCES Courses(id),
    FOREIGN KEY (professor_id) REFERENCES Users(id)
);

CREATE TABLE Topics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    section_id INT,
    name VARCHAR(100),
    weight INT,
    weight_or_percentage BOOLEAN,
    FOREIGN KEY (section_id) REFERENCES Sections(id)
);

CREATE TABLE Activities (
    id INT PRIMARY KEY AUTO_INCREMENT,
    topic_id INT,
    name VARCHAR(100),
    weight INT,
    weight_or_percentage BOOLEAN,
    optional_flag BOOLEAN,
    FOREIGN KEY (topic_id) REFERENCES Topics(id)
);

CREATE TABLE Grades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    activity_id INT,
    user_id INT,
    grade INT,
    FOREIGN KEY (activity_id) REFERENCES Activities(id),
    FOREIGN KEY (user_id) REFERENCES Users(id)
);

CREATE TABLE Courses_Taken (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    course_id INT,
    section_id INT,
    final_grade INT,
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (course_id) REFERENCES Courses(id),
    FOREIGN KEY (section_id) REFERENCES Sections(id)
);