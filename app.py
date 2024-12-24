from flask import Flask, render_template, request, jsonify, redirect, url_for, session, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Score
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 确保 static 目录存在
if not os.path.exists('static'):
    os.makedirs('static')
if not os.path.exists('static/img'):
    os.makedirs('static/img')
if not os.path.exists('static/js'):
    os.makedirs('static/js')

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return '用户名和密码不能为空', 400
            
        if User.query.filter_by(username=username).first():
            return '用户名已存在', 400
            
        user = User(username=username, password=generate_password_hash(password))
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            return '注册失败，请稍后重试', 500
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return '用户名和密码不能为空', 400
            
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        return '用户名或密码错误', 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/save_score', methods=['POST'])
@login_required
def save_score():
    try:
        score_data = request.json
        if not score_data or 'score' not in score_data:
            return jsonify({'status': 'error', 'message': '无效的分数数据'}), 400
            
        new_score = Score(score=score_data['score'], user_id=current_user.id)
        db.session.add(new_score)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_scores')
@login_required
def get_scores():
    try:
        user_scores = Score.query.filter_by(user_id=current_user.id).order_by(Score.date.desc()).limit(10).all()
        scores = [{'score': score.score, 'date': score.date.strftime('%Y-%m-%d %H:%M')} for score in user_scores]
        return jsonify(scores)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 