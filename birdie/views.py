from pyramid.response import Response
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
    )
from pyramid.renderers import get_renderer
from pyramid.security import (
    remember, 
    forget, 
    authenticated_userid,
    )
from pyramid.view import (
    view_config,
    forbidden_view_config,
    )
from pyramid.url import route_url

from repoze.timeago import get_elapsed
from datetime import datetime

from .security import check_login

import json
from .models import Redis

conn_err_msg = """\
Pyramid is having a problem using your database.  The problem
might be caused by the fact that your database server may not be running. 
Check that the database server referred to by the "sqlalchemy.url"
setting in your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

MAX_CHIRPS = 15
MAX_MY_CHIRPS = 5
MAX_USERS = 5
MAX_FRIENDS = 0
MAX_FOLLOWERS = 0

class BirdieViews(object):
    def __init__(self, request):
        self.request = request
        renderer = get_renderer("templates/layout-bootstrap.pt")
        self.layout = renderer.implementation().macros['layout']
        self.logged_in = authenticated_userid(request)
        self.app_url = request.application_url
        self.static_url = request.static_url

    #Prend un hset Redis et le retourne sous forme de json
    def hsetToJson(self, hset):
        return json.loads(hset.decode("utf-8").replace("'", '"'))

    #recupère les membres d'un set avec la clé key et les retourne sous forme d'un tableau
    def getUsersFromSet(self, key):
        users = []
        membersNames = Redis.smembers(key)
        for name in membersNames:
            name = name.decode("utf-8")
            user = self.hsetToJson(Redis.hget('users', 'user:' + name))
            users.append(user)

        return users

    @view_config(route_name='about',
                renderer='templates/about-bootstrap.pt')
    def about_page(self):
        return {}            
                
    @view_config(route_name='home',
                renderer='templates/birdie-bootstrap.pt')
    def birdie_view(self):
        username = self.logged_in
        user = None
        chirps, users, friends = [], [], []
        if username:        
            users = Redis.hgetall('usernames')
            for userhash in users:
                if userhash.decode("utf-8") == username:
                    user = Redis.hget('users', Redis.hget('usernames', userhash))
                    user = self.hsetToJson(user)
                    #liste les amis de l'utilisateur loggé
                    friends = str(Redis.smembers('friends:' + username))
                    

        #tous les tweets du plus récent au plus ancien
        chirps = []
        redischirps = Redis.smembers('chirps')
        for chirp in redischirps:
            chirps.append(self.hsetToJson(chirp))

        #liste de tous les utilisateurs
        users = Redis.hgetall('dor')
        
        #trouve les derniers utilisateurs
        sortedUsers = sorted(users)
        sortedUsers = sortedUsers[:MAX_USERS]
        latestUsers = []
        for sortedDor in sortedUsers:
            userToAdd = Redis.hget('users', Redis.hget('dor', sortedDor))
            userToAdd = self.hsetToJson(userToAdd)
            latestUsers.append(userToAdd)
        
        return {'elapsed': get_elapsed,
            'user': user,
            'chirps': chirps[:MAX_CHIRPS],
            'latest_users': latestUsers,
            'users_count': len(users),
            'chirps_count': len(chirps),
            'friends' : friends,
        }


    @view_config(route_name='mybirdie',
                permission='registered',
                renderer='templates/mybirdie-bootstrap.pt')
    def my_birdie_view(self):
        username = self.logged_in
        chirps = []
        my_chirps, friends, followers = [], [], []
        
        user = Redis.hget('users', Redis.hget('usernames', username))
        user = self.hsetToJson(user)
    
        #trouve les amis que l'utilisateur follow
        friends = self.getUsersFromSet('friends:' + username)
        
        #cherche les followers de l'utilisateur
        followers = self.getUsersFromSet('followers:' + username)

        if ('form.submitted' in self.request.params and self.request.params.get('chirp')):
            chirp = self.request.params.get('chirp')
            timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H:%M:%S")
            
            Redis.sadd('chirps', {
                'timestamp' : timestamp,
                'author' : {
                    'username' : user['username'],
                    'fullname' : user['fullname']
                    },
                'chirp' : chirp
                })
            Redis.hset(username + ':chirps', timestamp, {
                'timestamp' : timestamp,
                'chirp' : chirp,
                'author' : {
                    'username' : user['username'], 
                    'fullname' : user['fullname']
                    }
                })
           
            url = self.request.route_url('mybirdie', username=username)
            return HTTPFound(url)

        #find user chirps
        my_chirps = []
        userChirps = Redis.hgetall(username + ':chirps')
        for chirp in userChirps:
            my_chirps.append(self.hsetToJson(userChirps[chirp]))


        return {'elapsed': get_elapsed,
                'user': user,
                'chirps': chirps[:MAX_CHIRPS],
                'my_chirps': my_chirps[:MAX_MY_CHIRPS],
                'friends': friends,
                'followers' : followers,
                }

    @view_config(route_name='login',
                renderer='templates/login-bootstrap.pt')
    @forbidden_view_config(renderer='birdie:templates/login-bootstrap.pt')
    def login(self):
        request = self.request
        login_url = request.route_url('login')
        join_url = request.route_url('join')
        came_from = request.params.get('came_from')
        if not came_from : # first time it enters the login page
            came_from = request.referer
        message = ''
        login = ''
        password = ''
        if 'form.submitted' in request.params:
            login = request.params['login']
            password = request.params['password']
            if check_login(login, password):
                headers = remember(request, login)
                if (came_from == login_url or came_from == join_url or came_from == self.app_url):
                    came_from = request.route_url('mybirdie', username=login)  # never use login form itself as came_from
                return HTTPFound(location=came_from,
                                 headers=headers)
            message = 'Failed login'

        return {'message': message,
                'came_from': came_from,
                'login': login,
                'password': password}
                

    @view_config(route_name='logout')
    def logout(self):
        headers = forget(self.request)
        url = self.request.route_url('home')
        return HTTPFound(location=url,
                         headers=headers)

    @view_config(route_name='join',
                renderer='birdie:templates/join-bootstrap.pt')
    def join(self):

        request = self.request
        join_url = request.route_url('join')
        login_url = request.route_url('login')
        came_from = request.params.get('came_from')
        if not came_from: # first time it enters the join page
            came_from = request.referer
        
        if 'form.submitted' in request.params:
        # registration form has been submitted
            username = request.params.get('username')
            password = request.params.get('password')
            confirm = request.params.get('confirm')
            fullname = request.params.get('fullname')
            about = request.params.get('about')
            message = ''

            #search for existing user
            users = Redis.hgetall('usernames')
            user = None
            for userhash in users:
                if userhash.decode("utf-8") == username:
                    user = Redis.hget('users', Redis.hget('usernames', userhash))
                    user = self.hsetToJson(user)
            
            if username is '':
                message = "The username is required."
            elif (password is '' and confirm is ''):
                message = "The password is required."
            elif user:
                message = "The username {} already exists.".format(username)
            elif confirm != password:
                message = "The passwords don't match."
            elif len(password) < 6:
                message = "The password is too short."

            if message:
                return {'message': message,
                        'came_from': came_from,
                        'username': username,
                        'fullname': fullname,
                        'about': about}
           
           # register new user
            dor = datetime.utcnow()
            dor = dor.strftime("%Y-%m-%d-%H:%M:%S")

            #add to usernames hset and users hset
            Redis.hset('usernames', username, 'user:' + username)
            Redis.hset('dor', dor, 'user:' + username)
            Redis.hset('users', 'user:' + username,  {
                'username' : username, 
                'password' : password, 
                'fullname' : fullname, 
                'about' : about,
                'dor' : dor                
                }) 

            headers = remember(request, username)
            
            if (came_from == join_url or came_from == login_url or came_from == self.app_url):
                came_from = request.route_url('mybirdie', username=username)  # never use login form itself as came_from
            return HTTPFound(location = came_from,
                             headers = headers)

        # default - prepare empty sign in form
        return {'message': '',
                'came_from': came_from,
                'username': '',
                'fullname': '',
                'about': ''}


    @view_config(route_name='profile',
                 permission='registered',
                 renderer='birdie:templates/user-bootstrap.pt')
    def profile_view(self):
        auth_username = self.logged_in
        username = self.request.matchdict['username']
        chirps, auth_friends, auth_followers, friends, followers = [], [], [], [], []
        
        if auth_username==username: # redirect to my_birdie page
            return HTTPFound(location = self.request.route_url('mybirdie', username=username))

        auth_user = self.hsetToJson(Redis.hget('users', 'user:' + auth_username))
        user = self.hsetToJson(Redis.hget('users', 'user:' + username))
        
        redisChirps = Redis.hgetall(username + ':chirps')
        for stamp in redisChirps:
            chirps.append(self.hsetToJson(redisChirps[stamp]))
        
        #trouve les amis que l'utilisateur follow
        auth_friends = self.getUsersFromSet('friends:' + auth_username)
        
        #cherche les followers de l'utilisateur
        auth_followers = self.getUsersFromSet('followers:' + auth_username)
        
        # friendUsernames = Redis.smembers('friends:' + username)
        friendUsernames = self.getUsersFromSet('friends:' + username)

        #cherche les followers de l'utilisateur
        followers = self.getUsersFromSet('followers:' + username)

        return {'elapsed': get_elapsed,
                'auth_user' : auth_user,
                'user': user,
                'chirps': chirps[:MAX_CHIRPS], 
                'friends': friends,
                'followers': followers,
                'auth_friends': auth_friends, 
                'auth_followers': auth_followers,
                }
                

    @view_config(route_name='follow',
                 permission="registered",
                 renderer='birdie:templates/fake.pt')
    def follow(self):
        username = self.logged_in
        came_from= self.request.referer
        if not came_from:
            came_from = self.app_url
        
        friend_username = self.request.matchdict.get('username')
        friend = Redis.hget('users', Redis.hget('usernames', friend_username))
        
        if (len(friend) > 0 and friend_username != username):
            Redis.sadd('friends:' + username, friend_username)
            Redis.sadd('followers:' + friend_username, username)
                        
        return HTTPFound(location=came_from)


    @view_config(route_name='unfollow',
                 permission="registered",
                 renderer='birdie:templates/fake.pt')
    def unfollow(self):
        username = self.logged_in
        came_from=self.request.referer
        if not came_from:
            came_from=self.app_url
        
        friend_username = self.request.matchdict.get('username')
        friend = Redis.hget('users', Redis.hget('usernames', friend_username))

        if (len(friend)> 0):
            Redis.srem('friends:' + username, friend_username)
            Redis.srem('followers:' + friend_username, username)
            
        return HTTPFound(location=came_from)


    
