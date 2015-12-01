from pyramid.security import Authenticated
from pyramid.security import Allow

import birdie.models

import json
from .models import Redis
    
    
#from cryptacular.bcrypt import BCRYPTPasswordManager

#Crypt = BCRYPTPasswordManager()


class RootFactory(object):
    __acl__ = [
        (Allow, Authenticated, 'registered')
    ]
    def __init__(self, request):
        pass
        

def check_login(login, password):
    session = birdie.models.DBSession()
    user = Redis.hget('users', 'user:' + login)
    if user is not None:
        user = json.loads(user.decode("utf-8").replace("'", '"'))
    
    if user is not None:
        hashed_password = user['password']
        if hashed_password == user['password']:
            return True
    return False
