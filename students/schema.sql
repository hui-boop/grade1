-- 创建用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    fullname TEXT
);

-- 创建课程表
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT UNIQUE NOT NULL,
    course_name TEXT NOT NULL,
    instructor_id INTEGER,
    credit INTEGER,
    FOREIGN KEY (instructor_id) REFERENCES users (id)
);

-- 创建成绩表
CREATE TABLE grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    grade REAL,
    semester TEXT,
    FOREIGN KEY (student_id) REFERENCES users (id),
    FOREIGN KEY (course_id) REFERENCES courses (id)
);

-- 插入初始用户数据
INSERT INTO users (username, password, role, fullname) VALUES
('teacher1', 'password', 'teacher', '张教授'),
('teacher2', 'password', 'teacher', '李教授'),
('student1', 'password', 'student', '李明'),
('student2', 'password', 'student', '王芳'),
('student3', 'password', 'student', '赵阳'),
('student4', 'password', 'student', '刘静'),
('student5', 'password', 'student', '陈涛');

-- 插入课程数据
INSERT INTO courses (course_code, course_name, instructor_id, credit) VALUES
('CS101', '计算机基础', 1, 4),
('MA201', '高等数学', 1, 6),
('EN301', '大学英语', 2, 4),
('PH202', '大学物理', 2, 5),
('CH102', '基础化学', 2, 4);

-- 插入成绩数据
INSERT INTO grades (student_id, course_id, grade, semester) VALUES
-- 学生1的成绩
(3, 1, 85.5, '2023-2024-1'),
(3, 2, 92.0, '2023-2024-1'),
(3, 3, 78.5, '2023-2024-1'),
(3, 4, 88.0, '2023-2024-2'),
(3, 5, 76.0, '2023-2024-2'),

-- 学生2的成绩
(4, 1, 78.0, '2023-2024-1'),
(4, 2, 85.5, '2023-2024-1'),
(4, 3, 92.5, '2023-2024-1'),
(4, 4, 81.0, '2023-2024-2'),
(4, 5, 89.5, '2023-2024-2'),

-- 学生3的成绩
(5, 1, 90.0, '2023-2024-1'),
(5, 2, 76.5, '2023-2024-1'),
(5, 3, 85.0, '2023-2024-1'),
(5, 4, 92.0, '2023-2024-2'),
(5, 5, 83.5, '2023-2024-2'),

-- 学生4的成绩
(6, 1, 82.5, '2023-2024-1'),
(6, 2, 88.0, '2023-2024-1'),
(6, 3, 79.0, '2023-2024-1'),
(6, 4, 75.5, '2023-2024-2'),
(6, 5, 91.0, '2023-2024-2'),

-- 学生5的成绩
(7, 1, 95.0, '2023-2024-1'),
(7, 2, 92.5, '2023-2024-1'),
(7, 3, 88.0, '2023-2024-1'),
(7, 4, 89.5, '2023-2024-2'),
(7, 5, 94.0, '2023-2024-2');

-- 创建索引以提高查询性能
CREATE INDEX idx_grades_student ON grades (student_id);
CREATE INDEX idx_grades_course ON grades (course_id);
CREATE INDEX idx_grades_semester ON grades (semester);
CREATE INDEX idx_users_username ON users (username);
CREATE INDEX idx_courses_code ON courses (course_code);