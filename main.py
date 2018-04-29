#!/usr/bin/env python
import os
import jinja2
import webapp2
from google.appengine.api import users # uporabljeno za login
from models import Sporocilo
from models import Uporabnik
from google.appengine.ext import ndb


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
            logout_url = users.create_logout_url('/') # ustvari povezavo za logout

            uporabniki = Uporabnik.query().fetch() # uvozi shranjene uporabnike iz baze
            emailuporabniki = []
            for item in uporabniki:
                if item.email not in emailuporabniki:
                    emailuporabniki.append(item.email)

            if user.email() not in emailuporabniki: # ce trenutno logiran uporabnik se ni v bazi uporabnikov se ga tja shrani
                uporabnik = Uporabnik(email=user.email())
                uporabnik.put()

            params = {"logiran": logiran, "logout_url": logout_url, "user": user}
        else:
            logiran = False
            login_url = users.create_login_url('/') # ustvari povezavo za login

            params = {"logiran": logiran, "login_url": login_url, "user": user}

        return self.render_template("home.html", params)

class SendMessageHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()
        params = {"user": user}
        return self.render_template("send_message.html", params) # vrne send message stran


class SendMessageResultHandler(BaseHandler):
    def post(self):
        vneseno_besedilo = self.request.get("vnos-sporocilo") # dobi vneseno besedilo
        vnesen_prejemnik = self.request.get("vnos-prejemnik") # dobi vnesenega prejemnika
        user = users.get_current_user()
        posilatelj = user.email()
        sporocilo = Sporocilo(besedilo=vneseno_besedilo, posilatelj=posilatelj, prejemnik=vnesen_prejemnik)
        sporocilo.put() # spravi sporocilo v bazo
        return self.render_template("result.html")

class InboxHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()
        trenutni_uporabnik = user.email()
        prejeta_sporocila = Sporocilo.query().filter(Sporocilo.prejemnik == trenutni_uporabnik)\
            .order(Sporocilo.nastanek).fetch() # prikaze prejeta sporocila logiranega uporabnika; order ukaz jih razvrsti po datumu
        params = {"prejeta_sporocila": prejeta_sporocila, "user": user}
        return self.render_template("inbox.html", params)

class OutboxHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()
        trenutni_uporabnik = user.email()
        poslana_sporocila = Sporocilo.query().filter(Sporocilo.posilatelj == trenutni_uporabnik)\
            .order(Sporocilo.nastanek).fetch() # prikaze poslana sporocila logiranega uporabnika; order ukaz jih razvrsti po datumu
        params = {"poslana_sporocila": poslana_sporocila, "user": user}
        return self.render_template("outbox.html", params)

class ConversationHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()
        trenutni_uporabnik = user.email()
        uporabnik_sporocila = Sporocilo.query(ndb.OR(Sporocilo.posilatelj == trenutni_uporabnik,
                                                     Sporocilo.prejemnik == trenutni_uporabnik))\
            .order(Sporocilo.nastanek).fetch() # vrne vsa sporocila v katerih je posilatelj ali prejemnik logirani uporabnik; za ukaz order nisem preprican da ima kaksen pomen tu
        uporabniki_pogovor = [] # v to listo se shrani uporabnik ki je logiranemu kaj posiljal ali pa od njega prejel sporocila
        for sporocilce in uporabnik_sporocila:
            if sporocilce.prejemnik not in uporabniki_pogovor and sporocilce.prejemnik!=trenutni_uporabnik:
                uporabniki_pogovor.append(sporocilce.prejemnik)
            if sporocilce.posilatelj not in uporabniki_pogovor and sporocilce.posilatelj!=trenutni_uporabnik:
                uporabniki_pogovor.append(sporocilce.posilatelj)
        if uporabniki_pogovor != []: # ta if zanka je potrebna ker drugace za uporabnika ki se ni nic posiljal povezava pogovori ne dela
            relevantni_uporabniki = Uporabnik.query(Uporabnik.email.IN(uporabniki_pogovor)).fetch() # iz baze shranjenih uporabnikov s pomocjo liste uporabniki_pogovor potegnemo te uporabnike
        else:
            relevantni_uporabniki = []
        params = {"user": user, "uporabniki_pogovor": uporabniki_pogovor, "relevantni_uporabniki": relevantni_uporabniki}
        return self.render_template("conversation.html", params)

class AconversationHandler(BaseHandler):
    def get(self, uporabnik_id):
        user = users.get_current_user()
        trenutni_uporabnik = user.email()
        uporabnik = Uporabnik.get_by_id(int(uporabnik_id))
        uporabnik_mail = uporabnik.email
        # pogovor prikaze vsa sporocila v katerih sodelujeta ista uporabnika
        pogovor = Sporocilo.query(ndb.OR(ndb.AND(Sporocilo.posilatelj == trenutni_uporabnik, Sporocilo.prejemnik == uporabnik_mail),
                                          ndb.AND(Sporocilo.posilatelj == uporabnik_mail, Sporocilo.prejemnik == trenutni_uporabnik)))\
            .order(Sporocilo.nastanek).fetch()
        params = {"pogovor": pogovor, "user": user}
        return self.render_template("aconversation.html", params)


app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/send_message', SendMessageHandler),
    webapp2.Route('/inbox', InboxHandler),
    webapp2.Route('/result', SendMessageResultHandler),
    webapp2.Route('/outbox', OutboxHandler),
    webapp2.Route('/conversation', ConversationHandler),
    webapp2.Route('/conversation/<uporabnik_id:\d+>', AconversationHandler),
], debug=True)
