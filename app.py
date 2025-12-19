from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import check_password_hash
from config import Config
import markdown

# 初始化应用
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ============================================
# 1. 装饰器与辅助函数
# ============================================


def admin_required(f):
    """
    自定义装饰器：用于保护需要管理员权限的路由
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查 session 中是否有管理员标记
        if not session.get("is_admin"):
            flash("该操作需要管理员权限，请先登录。", "warning")
            # 记录用户想去的页面 (next)，登录后跳回
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


@app.template_filter("markdown")
def render_markdown(text):
    """模版过滤器：将 Markdown 文本转换为 HTML"""
    if not text:
        return ""
    # 启用扩展：fenced_code(代码块), tables(表格), nl2br(换行)
    return markdown.markdown(text, extensions=["fenced_code", "tables", "nl2br"])


@app.context_processor
def inject_admin_status():
    """
    上下文处理器：让所有模版都能直接使用 is_admin 变量
    无需在每个 render_template 中手动传递
    """
    return dict(is_admin=session.get("is_admin", False))


# ============================================
# 2. 数据模型 (Models)
# ============================================

# 关联表：Post 与 Tag 多对多关系
post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("post.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return self.name


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系定义
    tags = db.relationship(
        "Tag",
        secondary=post_tags,
        lazy="subquery",
        backref=db.backref("posts", lazy=True),
    )

    def update_tags(self, tag_string):
        """
        解析标签字符串并更新当前文章的标签关联
        :param tag_string: "Python, Flask, Web"
        """
        self.tags.clear()
        if not tag_string:
            return

        # 分割、去空、去重
        tag_names = set([t.strip() for t in tag_string.split(",") if t.strip()])

        for name in tag_names:
            # 查找是否存在，不存在则创建
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                tag = Tag(name=name)
                db.session.add(tag)
            self.tags.append(tag)

    def __repr__(self):
        return f"<Post {self.title}>"


# ============================================
# 3. 视图路由
# ============================================


@app.route("/")
@app.route("/home")
def home():
    # 分页显示
    page = request.args.get("page", 1, type=int)  # 当前页码，默认第1页
    per_page = 10
    pagination = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    posts = pagination.items  # 当前页的文章列表
    
    # 获取所有标签用于侧边栏展示
    tags = Tag.query.all()
    
    return render_template("home.html", posts=posts, tags=tags, pagination=pagination)


@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post_detail.html", post=post)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/cube_timer")
def cube_timer():
    return render_template("cube_timer.html")


# --- 认证相关 ---


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        
        ok_user = username == app.config["ADMIN_USERNAME"]
        ok_pass = check_password_hash(app.config["ADMIN_PASSWORD_HASH"], password)

        # 验证账号密码
        if ok_user and ok_pass:
            session["is_admin"] = True
            flash("欢迎回来，管理员！", "success")

            # 如果有 next 参数（即用户之前想访问受限页面），则跳转过去；否则回首页
            next_page = request.args.get("next")
            return redirect(next_page or url_for("home"))
        else:
            flash("账号或密码错误", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("is_admin", None)
    flash("已安全退出", "info")
    return redirect(url_for("home"))


# --- 管理功能 (使用 @admin_required 保护) ---


@app.route("/post/new", methods=["GET", "POST"])
@admin_required
def create_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        tag_str = request.form.get("tags", "").strip()

        if not title or not content:
            flash("标题和内容不能为空", "warning")
            # 保留用户已输入的内容避免重填
            return render_template(
                "post_form.html", post={"title": title, "content": content, "tags": []}
            )

        # 创建文章并处理标签
        post = Post(title=title, content=content)
        post.update_tags(tag_str)  # 使用模型方法

        db.session.add(post)
        db.session.commit()

        flash("文章发布成功！", "success")
        return redirect(url_for("home"))

    return render_template("post_form.html", post=None)


@app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        tag_str = request.form.get("tags", "").strip()

        if not title or not content:
            flash("标题和内容不能为空", "warning")
            return render_template("post_form.html", post=post)

        # 更新字段
        post.title = title
        post.content = content
        post.update_tags(tag_str)  # 使用模型方法

        db.session.commit()
        flash("文章已更新", "success")
        return redirect(url_for("post_detail", post_id=post.id))

    return render_template("post_form.html", post=post)


@app.route("/post/<int:post_id>/delete", methods=["POST"])
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    tags_to_check = list(post.tags)

    db.session.delete(post)
    db.session.commit()

    # 删除无用标签
    for tag in tags_to_check:
        if not tag.posts:
            db.session.delete(tag)

    db.session.commit()

    flash("文章已删除，无用标签以及关联关系已删除", "info")
    return redirect(url_for("home"))


# ============================================
# 4. 程序入口
# ============================================

if __name__ == "__main__":
    app.run(debug=True)
