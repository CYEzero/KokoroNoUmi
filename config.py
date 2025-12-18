import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = "PgK7Vrnf!a:Ak+.nwW0JuZd>%AyKR~"  # 用于 session
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "blog.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 管理员账号
    ADMIN_USERNAME = "CYE_zero"
    ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$ajOoPzk1PzsViOrD$d5c9f909ea90de19f41ed5934cba8d60c13102bc705918f1d07599ead52f6005259c53470db944bc6c622d7db8fecd12d36075bba8f492aac04b23ab9eea352d"
