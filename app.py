import random
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

# --- 初始化 ---
# 获取当前文件目录
basedir = os.path.abspath(os.path.dirname(__file__))
# 配置数据库文件路径
DATABASE = os.path.join(basedir, 'database.db')

app = Flask(__name__)
# 必须设置一个秘密密钥，用于 session 管理和 flash 消息
app.secret_key = 'your-secret-key-keep-it-safe-and-secret' # 请更换为一个强随机密钥

# --- 数据库操作函数 ---
def get_db():
    """连接到数据库并返回连接对象"""
    conn = sqlite3.connect(DATABASE)
    # 设置行工厂，使查询结果可以像字典一样通过列名访问
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库，创建 users 表"""
    with app.app_context():
        db = get_db()
        # 使用 with 语句自动提交或回滚事务
        with db:
            db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
            ''')
        db.close()

# --- 路由和视图函数 ---
@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if request.method == 'POST':
        # 从表单获取数据
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # 简单的表单验证
        if not username or not email or not password:
            flash('请填写所有必填字段！', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('两次输入的密码不一致！', 'error')
            return redirect(url_for('register'))

        db = get_db()
        try:
            # 使用 with 语句确保事务正确处理
            with db:
                # 检查用户名或邮箱是否已存在
                existing_user = db.execute('SELECT id FROM users WHERE username = ? OR email = ?', 
                                          (username, email)).fetchone()
                if existing_user:
                    flash('用户名或邮箱已被注册！', 'error')
                    return redirect(url_for('register'))
                
                # 密码哈希处理，永远不要存储明文密码！
                password_hash = generate_password_hash(password)
                
                # 插入新用户
                db.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                           (username, email, password_hash))
            
            flash('注册成功！请登录。', 'success')
            return redirect(url_for('login'))
            
        except sqlite3.Error as e:
            # 发生数据库错误时回滚
            db.rollback()
            flash(f'数据库错误: {e}', 'error')
        finally:
            db.close()

    # 如果是 GET 请求，显示注册表单
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        db.close()

        # 验证用户是否存在以及密码是否正确
        if user and check_password_hash(user['password_hash'], password):
            # 将用户ID存入 session，表示用户已登录
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('登录成功！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误！', 'error')
            return redirect(url_for('login'))

    # 如果是 GET 请求，显示登录表单
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """用户仪表盘，需要登录才能访问"""
    # 检查用户是否已登录
    if 'user_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('login'))
    
    # 从 session 获取用户名
    username = session.get('username', '用户')
    return render_template('dashboard.html', username=username)
from flask import Flask, render_template, redirect, url_for, request, session, flash
import sqlite3
import os

# ... (你已有的 app.py 代码) ...

@app.route('/settings')
def settings():
    """用户设置页面，需要登录才能访问"""
    # 1. 检查用户是否登录
    if 'user_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('login'))
    
    # 2. 获取用户名
    username = session.get('username', '用户')
    
    # 3. 渲染 settings.html 模板
    return render_template('settings.html', username=username)

# ... (你已有的 app.py 代码，比如 logout 路由和 app.run) ...
@app.route('/profile')
def profile():
    """个人资料页面，需要登录才能访问"""
    # 登录校验：没登录的话，强制跳转到登录页
    if 'user_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('login'))
    # 从 session 里拿用户名，传给前端模板
    username = session.get('username', '用户')
    return render_template('profile.html', username=username)
@app.route('/games')
def games():
    """游戏选择页面，需要登录才能访问"""
    if 'user_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('login'))
    username = session.get('username', '用户')
    return render_template('games.html', username=username)
@app.route('/guess_number')
def guess_number():
    """猜数字游戏页面，需要登录才能访问"""
    if 'user_id' not in session:
        flash('请先登录！', 'error')
        return redirect(url_for('login'))
    # 生成 1 - 100 的随机数，用于游戏逻辑（后续可完善会话存储等，这里先简单演示）
    session['target_number'] = random.randint(1, 100)
    session['attempts'] = 0
    username = session.get('username', '用户')
    return render_template('guess_number.html', username=username)
@app.route('/check_guess', methods=['POST'])
def check_guess():
    if 'user_id' not in session or 'target_number' not in session:
        flash('请先从游戏中心进入猜数字游戏！', 'error')
        return redirect(url_for('games'))
    guess = int(request.form.get('guess'))
    target = session['target_number']
    session['attempts'] = session.get('attempts', 0) + 1

    if guess < target:
        flash(f'太小啦！这是第 {session["attempts"]} 次尝试～')
    elif guess > target:
        flash(f'太大啦！这是第 {session["attempts"]} 次尝试～')
    else:
        flash(f'恭喜猜对啦！总共用了 {session["attempts"]} 次尝试～', 'success')
        # 猜对后，重新生成新数字，准备下一轮游戏
        session['target_number'] = random.randint(1, 100)
        session['attempts'] = 0
    return redirect(url_for('guess_number'))
@app.route('/logout')
def logout():
    """登出功能"""
    # 清除 session 中的用户信息
    session.pop('user_id', None)
    session.pop('username', None)
    flash('您已成功登出。', 'success')
    return redirect(url_for('index'))

# --- 应用启动 ---
if __name__ == '__main__':
    # 在应用启动时确保数据库已初始化
    init_db()
    # 运行 Flask 应用，开启调试模式 (开发时使用)
    app.run(debug=True)