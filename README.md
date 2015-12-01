Thomas Le Gougaud - Claire Remy
================================

# Installation
## Birdie
Télécharger Birdie sur [https://github.com/gr-/birdie](https://github.com/gr-/birdie)

La suite des commandes va expliquer comment installer birdie.
Créer et installer l'environnement virtuel de python:

    > pyvenv venv
	> source venv/bin/activate

L'installation de l'application et de ses dépendances en `develop` mode:

	$ unzip birdie-<ver>.zip
	$ cd <path to this README.md file>
	$ python setup.py develop
	$ initialize_birdie_db development.ini
	$ pserve development.ini --reload

## Redis
Dans un premier temps il faut télécharger l'archive et procéder à son installation :

    $ wget http://download.redis.io/redis-stable.tar.gz
    $ tar xvzf redis-stable.tar.gz
    $ cd redis-stable
    $ make

On peut copier l'interface de ligne de commande ainsi que le serveur Redis à l'endroit approprié avec ces deux commandes :

    $ sudo cp src/redis-server /venv/bin/
    $ sudo cp src/redis-cli /venv/bin/

# Exécution
Pour lancer le serveur on execute la commande :

    $ /venv/redis-server

# Vérification
Pour vérifier si Redis est bien installé on peut vérifier que la commande suivante renvoie bien PONG:

    $ /venv/redis-cli ping
    $ PONG
    
Les étapes d'installation de Redis sont décrites sur leur site officiel.

On vérifie le bon fonctionnement du serveur sur [http://localhost:6543](http://localhost:6543)

[Redis] - HTML enhanced for web apps!

[Redis]: <http://redis.io/topics/quickstart>
    