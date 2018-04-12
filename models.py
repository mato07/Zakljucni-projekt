from google.appengine.ext import ndb

class Sporocilo(ndb.Model):
    besedilo = ndb.StringProperty()
    posilatelj = ndb.StringProperty()
    prejemnik = ndb.StringProperty()