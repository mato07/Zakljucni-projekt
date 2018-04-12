#!/usr/bin/env python
import os
import jinja2
import webapp2
from google.appengine.api import users
from models import Sporocilo


template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if params is None:
            params = {}
        template = jinja_env.get_template(view_filename)
        return self.response.out.write(template.render(params))


class MainHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            logiran = True
            logout_url = users.create_logout_url('/')

            params = {"logiran": logiran, "logout_url": logout_url, "user": user}
        else:
            logiran = False
            login_url = users.create_login_url('/')

            params = {"logiran": logiran, "login_url": login_url, "user": user}

        return self.render_template("home.html", params)

class SendMessageHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()
        params = {"user": user}
        return self.render_template("send_message.html", params)


class SendMessageResultHandler(BaseHandler):
    def post(self):
        vneseno_besedilo = self.request.get("vnos-sporocilo")
        vnesen_prejemnik = self.request.get("vnos-prejemnik")
        user = users.get_current_user()
        posilatelj = user.email()
        sporocilo = Sporocilo(besedilo=vneseno_besedilo, posilatelj=posilatelj, prejemnik=vnesen_prejemnik)
        sporocilo.put()
        return self.render_template("result.html")

class InboxHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()
        trenutni_uporabnik = user.email()
        prejeta_sporocila = Sporocilo.query().filter(Sporocilo.prejemnik == trenutni_uporabnik).fetch()
        params = {"prejeta_sporocila": prejeta_sporocila, "user": user}
        return self.render_template("inbox.html", params)

class OutboxHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()
        trenutni_uporabnik = user.email()
        poslana_sporocila = Sporocilo.query().filter(Sporocilo.posilatelj == trenutni_uporabnik).fetch()
        params = {"poslana_sporocila": poslana_sporocila, "user": user}
        return self.render_template("outbox.html", params)

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/send_message', SendMessageHandler),
    webapp2.Route('/inbox', InboxHandler),
    webapp2.Route('/result', SendMessageResultHandler),
    webapp2.Route('/outbox', OutboxHandler),
], debug=True)
