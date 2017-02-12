#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os, sys
import concurrent.futures
import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.escape
import tornado.options
import bcrypt
from sqlalchemy import *
from sqlalchemy.orm import *
import datetime

from identify import identify

engine = create_engine("mysql://root:eisoo.com@localhost:3306/mealer",
         pool_recycle=3600)
Session = sessionmaker(engine)
session = Session()
executor = concurrent.futures.ThreadPoolExecutor(2)

from model import *

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        username = self.get_secure_cookie("username")
        user = session.query(User).filter_by(username=username).first()
        return user if user else None

    @property
    def stop(self):
        return bool(session.query(Switch).first().stop)

    def set_stop(self):
        switch = session.query(Switch).first()
        switch.stop = 1
        session.add(switch); session.commit()

    def set_open(self):
        switch = session.query(Switch).first()
        switch.stop = 0
        session.add(switch); session.commit()


class EntryModule(tornado.web.UIModule):
    def render(self, order):
        return self.render_string("modules/entry.html", order=order)


class HomeHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            return self.redirect("/login")
        today = datetime.date.today()
        orders = session.query(Order).filter(func.date(Order.created_at) == today).all()
        return self.render("home.html", orders=orders, stop=self.stop)


class AdminHandler(BaseHandler):
    @identify(['admin', 'audit'])
    def get(self):
        return self.render("admin.html", stop=self.stop, error=None)

    @identify(['admin', 'audit'])
    def post(self):
        state = self.get_argument("state")
        if state:
            self.set_stop()
        else:
            self.set_open()
        return self.render("admin.html", stop=self.stop,
                message="setup successfully", error=None)


class SigninHandler(BaseHandler):
    """登录"""
    def get(self):
        return self.render("login.html", error=None)

    def post(self):
        username = self.get_body_argument("username")
        password = self.get_body_argument("password")
        user = session.query(User).filter_by(username=username).first()
        if not user:
            return self.render("login.html", error="username not found")
        if not bcrypt.checkpw(tornado.escape.utf8(password), user.password):
            return self.render("login.html", error="incorrect password")
        self.set_secure_cookie("username", username)
        return self.redirect("/")


class SignupHandler(BaseHandler):
    """注册"""
    def get(self):
        return self.render("signup.html", error=None)

    def post(self):
        username = self.get_body_argument("username")
        password = self.get_body_argument("password")
        user = session.query(User).filter_by(username=username).first()
        if user:
            return self.render("signup.html", error="user exist!")
        hashed_pw = bcrypt.hashpw(tornado.escape.utf8(password), bcrypt.gensalt())
        user = User(username=username, password=hashed_pw)
        session.add(user); session.commit()
        self.set_secure_cookie("username", username)
        return self.redirect("/")


class LogoutHandler(BaseHandler):
    """退出"""
    def get(self):
        self.clear_cookie("username")
        return self.redirect("/")


class StopHandler(BaseHandler):
    def get(self):
        self.set_stop()
        return self.redirect("/")


class SetupHandler(BaseHandler):
    """设置, audit可以增加食物"""
    def get(self):
        stop = self.stop
        return self.render("setup.html", stop=stop, error=None)

    @tornado.web.authenticated
    def put(self):
        email = self.get_body_argument("email", "")
        if not email == "":
            self.current_user.email = email
            session.add(self.current_user); session.commit()
            return self.write("邮箱设置成功")

        food_name = self.get_body_argument("food_name", "")
        if not food_name == "":
            food = session.query(Food).filter_by(food_name=food_name).first()
            if food:
                return self.write("该食物名已经存在")
            food = Food(food_name=food_name)
            session.add(food); session.commit()
            return self.write("添加食物成功")

        



        return self.redirect("/")


class NewHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        foods = session.query(Food).all()
        return self.render("new.html", foods=foods, error=None)

    @tornado.web.authenticated
    def post(self):
        food_name = self.get_body_argument("food_name")
        food = session.query(Food).filter_by(food_name=food_name).first()
        if not food:
            raise tornado.web.HTTPError(404, reason="missing food")
        order = Order(user=self.current_user, food=food)
        session.add(order); session.commit()
        return self.redirect("/")


class OrderHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, id):
        order = session.query(order_id=id).first()
        foods = session.query(Food).all()
        if not order:
            raise tornado.web.HTTPError(404, reason="missing order")
        return self.render("order.html", order=order, foods=foods, error=None)

    @tornado.web.authenticated
    def put(self, id):
        order = session.query(order_id=id).first()
        if not order:
            raise tornado.web.HTTPError(404, reason="missing order")
        food_name = self.get_body_arugement("food_name")
        if food_name == order.food.food_name:
            return self.render("order.html", order=order, error="未更改")
        food = session.query(Food).filter_by(food_name=food_name).first()
        if not food:
            raise tornado.web.HTTPError(404, reason="missing food")
        order.food = food
        session.add(order); session.commit()
        return self.redirect("/")

    @identify(['admin', 'audit'])
    def delete(self, id):
        order = session.query(order_id=id).first()
        if not order:
            raise tornado.web.HTTPError(404, reason="missing order")
        session.delete(order); session.commit()
        return self.redirect("/")


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r'/', HomeHandler),
                (r'/setup', SetupHandler),
                (r'/login', SigninHandler),
                (r'/signup', SignupHandler),
                (r'/logout', LogoutHandler),
                (r'/new', NewHandler),
                (r'/stop', StopHandler),
                (r'/admin', AdminHandler),
                (r'/order/([0-9]+)', OrderHandler),
        ]
        settings = dict(
                debug=True,
                template_path=os.path.join(os.path.dirname(__file__), "templates"),
                static_path=os.path.join(os.path.dirname(__file__), "static"),
                ui_modules={"Entry": EntryModule},
                xsrf_cookies=True,
                login_url="/login",
                cookie_secret="hello, qiandiao"
        )
        super(Application, self).__init__(handlers, **settings)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(3000)
    tornado.ioloop.IOLoop.current().start()
