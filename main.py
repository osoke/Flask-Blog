from flask import g, Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBO6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()  # 登录管理器
login_manager.init_app(app)  # 配置app

# 用户加载===========
@login_manager.user_loader
def load_user(user_id):  # 回调,从服务器 session 存储的user_id 加载 用户对象
    return User.query.get(user_id)

##CONFIGURE TABLES

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    posts = relationship("BlogPost", backref="author")  # 参数2: 反向连接->在子类对应 author列(假列)
    comments = relationship('Comment', backref='author')

    def to_dict(self):  # 对象=>字典
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, ForeignKey('users.id'))  # Fore('父类-表名.属性id') 隐藏属性 author

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    comments = relationship('Comment', backref='post')


class Comment(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, ForeignKey('users.id')) # 隐藏属性 author
    post_id = db.Column(db.Integer, ForeignKey('blog_posts.id')) # 隐藏属性 post
    text = db.Column(db.Text, nullable=False)


# 初始化DB - 仅运行1次
# db.create_all()


def admin_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.get_id() != '1':  # 注意: get_id() 返回 str
            return abort(403)
        return f(*args, **kwargs)
    return wrapper


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("You've signed up with this email,log in instead.")
            return redirect(url_for('login'))
        else:
            form.password.data = generate_password_hash(
                form.password.data,
                method='pbkdf2:sha256',
                salt_length=8
            )
            new_user = User()
            form.populate_obj(new_user)  # 填充 user
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)

            return redirect(url_for('get_all_posts'))

    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                flash('Password error, try again.')
        else:
            flash('Email not exist, try again.')
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    if form.validate_on_submit():  # 登录之后-提交评论
        if current_user.is_authenticated:
            new_comment = Comment(
                author=current_user,
                post=requested_post,
                text=form.comment.data
            )

            db.session.add(new_comment)
            db.session.commit()
        else:
            flash('Please log in to comment.')
            return redirect(url_for('login'))


    return render_template("post.html", post=requested_post, form=form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=['GET', 'POST'])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(author=current_user, date=date.today().strftime("%B %d, %Y"))
        form.populate_obj(new_post)

        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(obj=post)
    if edit_form.validate_on_submit():
        edit_form.populate_obj(post)
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5000)
    # db.create_all() # 初始化DB
    app.run(debug=True)
