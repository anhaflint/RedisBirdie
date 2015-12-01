from redis.client import Redis, StrictRedis
from redis.connection import (
    BlockingConnectionPool,
    ConnectionPool,
    Connection,
    SSLConnection,
    UnixDomainSocketConnection
)

# connexion à redis
Redis = StrictRedis(host='localhost', port=6379, db=0, charset='utf-8')
