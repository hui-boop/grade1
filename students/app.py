import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import matplotlib

matplotlib.use('Agg')  # 使用非GUI后端
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
DATABASE = 'data.db'


# 初始化数据库
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # 创建用户表
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        fullname TEXT
    )
    ''')

    # 创建课程表
    c.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT UNIQUE NOT NULL,
        course_name TEXT NOT NULL,
        instructor_id INTEGER,
        credit INTEGER,
        FOREIGN KEY (instructor_id) REFERENCES users (id)
    )
    ''')

    # 创建成绩表
    c.execute('''
    CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        grade REAL,
        semester TEXT,
        FOREIGN KEY (student_id) REFERENCES users (id),
        FOREIGN KEY (course_id) REFERENCES courses (id)
    )
    ''')

    # 插入初始数据
    try:
        # 插入教师用户
        c.execute("INSERT INTO users (username, password, role, fullname) VALUES (?, ?, ?, ?)",
                  ('teacher1', 'password', 'teacher', '张教授'))
        # 插入学生用户
        c.execute("INSERT INTO users (username, password, role, fullname) VALUES (?, ?, ?, ?)",
                  ('student1', 'password', 'student', '李明'))
        c.execute("INSERT INTO users (username, password, role, fullname) VALUES (?, ?, ?, ?)",
                  ('student2', 'password', 'student', '王芳'))

        # 插入课程
        c.execute("INSERT INTO courses (course_code, course_name, instructor_id, credit) VALUES (?, ?, ?, ?)",
                  ('CS101', '计算机基础', 1, 4))
        c.execute("INSERT INTO courses (course_code, course_name, instructor_id, credit) VALUES (?, ?, ?, ?)",
                  ('MA201', '高等数学', 1, 6))

        # 插入成绩
        c.execute("INSERT INTO grades (student_id, course_id, grade, semester) VALUES (?, ?, ?, ?)",
                  (2, 1, 85.5, '2023-2024-1'))
        c.execute("INSERT INTO grades (student_id, course_id, grade, semester) VALUES (?, ?, ?, ?)",
                  (2, 2, 92.0, '2023-2024-1'))
        c.execute("INSERT INTO grades (student_id, course_id, grade, semester) VALUES (?, ?, ?, ?)",
                  (3, 1, 78.0, '2023-2024-1'))
    except sqlite3.IntegrityError:
        # 数据已存在
        pass

    conn.commit()
    conn.close()


# 数据库连接助手
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# 登录路由
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['fullname'] = user['fullname']
            flash('登录成功！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'danger')

    return render_template('login.html')


# 注销
@app.route('/logout')
def logout():
    session.clear()
    flash('您已成功注销', 'info')
    return redirect(url_for('login'))


# 仪表盘
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()

    if session['role'] == 'teacher':
        # 教师仪表盘数据
        c.execute("SELECT COUNT(*) FROM courses WHERE instructor_id = ?", (session['user_id'],))
        course_count = c.fetchone()[0]

        c.execute(
            "SELECT COUNT(DISTINCT student_id) FROM grades WHERE course_id IN (SELECT id FROM courses WHERE instructor_id = ?)",
            (session['user_id'],))
        student_count = c.fetchone()[0]

        c.execute("""
            SELECT courses.course_name, AVG(grades.grade) as avg_grade
            FROM grades
            JOIN courses ON grades.course_id = courses.id
            WHERE courses.instructor_id = ?
            GROUP BY courses.id
        """, (session['user_id'],))
        course_avg = c.fetchall()

        return render_template('dashboard.html',
                               role='teacher',
                               course_count=course_count,
                               student_count=student_count,
                               course_avg=course_avg)

    else:
        # 学生仪表盘数据
        c.execute("""
            SELECT courses.course_code, courses.course_name, grades.grade, grades.semester
            FROM grades
            JOIN courses ON grades.course_id = courses.id
            WHERE grades.student_id = ?
        """, (session['user_id'],))
        grades = c.fetchall()

        c.execute("""
            SELECT AVG(grade) FROM grades WHERE student_id = ?
        """, (session['user_id'],))
        avg_grade = c.fetchone()[0] or 0

        return render_template('dashboard.html',
                               role='student',
                               grades=grades,
                               avg_grade=round(avg_grade, 2))


# 课程管理
@app.route('/courses', methods=['GET', 'POST'])
def courses():
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('无访问权限', 'danger')
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        course_code = request.form['course_code']
        course_name = request.form['course_name']
        credit = request.form['credit']
        try:
            c.execute("""
                        INSERT INTO courses (course_code, course_name, instructor_id, credit)
                        VALUES (?, ?, ?, ?)
                    """, (course_code, course_name, session['user_id'], credit))
            conn.commit()
            flash('课程添加成功', 'success')
        except sqlite3.IntegrityError:
            flash('课程代码已存在', 'danger')

        # 获取当前教师的所有课程
    c.execute("SELECT * FROM courses WHERE instructor_id = ?", (session['user_id'],))
    courses = c.fetchall()
    conn.close()

    return render_template('courses.html', courses=courses)


# 学生管理
@app.route('/students')
def students():
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('无访问权限', 'danger')
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()

    # 获取所有学生
    c.execute("SELECT * FROM users WHERE role = 'student'")
    students = c.fetchall()

    # 获取每个学生的课程数量
    student_data = []
    for student in students:
        c.execute("SELECT COUNT(*) FROM grades WHERE student_id = ?", (student['id'],))
        course_count = c.fetchone()[0]

        c.execute("SELECT AVG(grade) FROM grades WHERE student_id = ?", (student['id'],))
        avg_grade = c.fetchone()[0] or 0

        student_data.append({
            'id': student['id'],
            'fullname': student['fullname'],
            'username': student['username'],
            'course_count': course_count,
            'avg_grade': round(avg_grade, 2)
        })

    conn.close()

    return render_template('students.html', students=student_data)


# 成绩管理
@app.route('/grades', methods=['GET', 'POST'])
def grades():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()

    if session['role'] == 'teacher':
        # 教师添加/修改成绩
        if request.method == 'POST':
            student_id = request.form['student_id']
            course_id = request.form['course_id']
            grade = request.form['grade']
            semester = request.form['semester']

            # 检查成绩是否已存在
            c.execute("""
                SELECT id FROM grades 
                WHERE student_id = ? AND course_id = ? AND semester = ?
            """, (student_id, course_id, semester))
            existing_grade = c.fetchone()

            if existing_grade:
                # 更新已有成绩
                c.execute("""
                    UPDATE grades SET grade = ?
                    WHERE id = ?
                """, (grade, existing_grade['id']))
                flash('成绩更新成功', 'success')
            else:
                # 添加新成绩
                c.execute("""
                    INSERT INTO grades (student_id, course_id, grade, semester)
                    VALUES (?, ?, ?, ?)
                """, (student_id, course_id, grade, semester))
                flash('成绩添加成功', 'success')

            conn.commit()

        # 获取教师教授的课程
        c.execute("SELECT id, course_code, course_name FROM courses WHERE instructor_id = ?", (session['user_id'],))
        courses = c.fetchall()

        # 获取所有学生
        c.execute("SELECT id, fullname FROM users WHERE role = 'student'")
        students = c.fetchall()

        conn.close()
        return render_template('grades_teacher.html', courses=courses, students=students)
    else:
        # 学生查看成绩
        c.execute("""
            SELECT courses.course_code, courses.course_name, grades.grade, grades.semester, courses.credit
            FROM grades
            JOIN courses ON grades.course_id = courses.id
            WHERE grades.student_id = ?
            ORDER BY grades.semester DESC
        """, (session['user_id'],))
        grades = c.fetchall()

        # 计算GPA
        total_credit = 0
        total_grade_point = 0

        for grade in grades:
            credit = grade['credit']
            score = grade['grade']

            # 转换成绩点到GPA (简单转换)
            if score >= 90:
                grade_point = 4.0
            elif score >= 85:
                grade_point = 3.7
            elif score >= 82:
                grade_point = 3.3
            elif score >= 78:
                grade_point = 3.0
            elif score >= 75:
                grade_point = 2.7
            elif score >= 72:
                grade_point = 2.3
            elif score >= 68:
                grade_point = 2.0
            elif score >= 64:
                grade_point = 1.5
            elif score >= 60:
                grade_point = 1.0
            else:
                grade_point = 0

            total_credit += credit
            total_grade_point += grade_point * credit

        gpa = total_grade_point / total_credit if total_credit > 0 else 0

        conn.close()
        return render_template('grades_student.html', grades=grades, gpa=round(gpa, 2))

# 成绩分析
@app.route('/analytics')
def analytics():
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('无访问权限', 'danger')
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()

    # 获取当前教师教授的课程
    c.execute("SELECT id, course_name FROM courses WHERE instructor_id = ?", (session['user_id'],))
    courses = c.fetchall()

    # 如果没有课程，返回空页面
    if not courses:
        conn.close()
        return render_template('analytics.html')

    # 成绩分布统计
    course_id = request.args.get('course_id', courses[0]['id'])

    # 获取成绩数据
    c.execute("""
        SELECT grade FROM grades 
        WHERE course_id = ? AND grade IS NOT NULL
    """, (course_id,))
    grades = [row['grade'] for row in c.fetchall()]

    # 生成成绩分布图
    img = io.BytesIO()

    plt.figure(figsize=(10, 6))
    plt.hist(grades, bins=10, edgecolor='black', alpha=0.7)
    plt.title('成绩分布')
    plt.xlabel('分数')
    plt.ylabel('学生人数')
    plt.grid(True, linestyle='--', alpha=0.7)

    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    # 获取课程平均分
    c.execute("""
        SELECT AVG(grade) as avg_grade FROM grades 
        WHERE course_id = ?
    """, (course_id,))
    avg_grade = c.fetchone()['avg_grade'] or 0

    # 获取最高分和最低分
    c.execute("SELECT MAX(grade) as max_grade FROM grades WHERE course_id = ?", (course_id,))
    max_grade = c.fetchone()['max_grade'] or 0

    c.execute("SELECT MIN(grade) as min_grade FROM grades WHERE course_id = ?", (course_id,))
    min_grade = c.fetchone()['min_grade'] or 0

    # 及格率
    c.execute("""
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN grade >= 60 THEN 1 ELSE 0 END) as passed
        FROM grades 
        WHERE course_id = ?
    """, (course_id,))
    pass_data = c.fetchone()
    total = pass_data['total']
    passed = pass_data['passed']
    pass_rate = (passed / total * 100) if total > 0 else 0

    conn.close()

    return render_template('analytics.html',
                          courses=courses,
                          selected_course=course_id,
                          plot_url=plot_url,
                          avg_grade=round(avg_grade, 2),
                          max_grade=max_grade,
                          min_grade=min_grade,
                          pass_rate=round(pass_rate, 2))

# 个人资料
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        fullname = request.form['fullname']
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        # 验证当前密码
        c.execute("SELECT password FROM users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()

        if user and user['password'] == current_password:
            # 更新资料
            if new_password:
                c.execute("UPDATE users SET fullname = ?, password = ? WHERE id = ?",
                         (fullname, new_password, session['user_id']))
            else:
                c.execute("UPDATE users SET fullname = ? WHERE id = ?",
                         (fullname, session['user_id']))
            conn.commit()
            session['fullname'] = fullname
            flash('资料更新成功', 'success')
        else:
            flash('当前密码错误', 'danger')

    # 获取用户信息
    c.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    conn.close()

    return render_template('profile.html', user=user)

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
