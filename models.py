from google.appengine.ext import ndb

class Sporocilo(ndb.Model):
    besedilo = ndb.StringProperty()
    posilatelj = ndb.StringProperty()
    prejemnik = ndb.StringProperty()
    nastanek = ndb.DateTimeProperty(auto_now_add=True)

class Uporabnik(ndb.Model):
    email = ndb.StringProperty()