from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from models import db

csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["3000 per hour", "500 per minute"],
    storage_uri="memory://"
)
cors = CORS()

__all__ = ['db', 'csrf', 'limiter', 'cors']
