import confuse

_config = confuse.Configuration('traktor_ice', __name__)

_template = {
    'icecast': {
        'source': {
            'user': confuse.String(default='source'),
            'password': confuse.String(default='hackme'),
        },
        'admin': {
            'user': confuse.String(default='admin'),
            'password': confuse.String(default='hackme'),
        },
        'port': confuse.Integer(default=8000),
        'server': confuse.String(default='localhost'),
    },
    'stream': {
        'title': confuse.String(default='Stream Title'),
        'description': confuse.String(default='Stream description'),
        'genre': confuse.String(default='Stream Genre'),
        'url': confuse.String(default='http://localhost'),
    },
    'traktor': {
        'recordings-path': confuse.Path(),
        'recordings-extension': confuse.String(default='wav')
    },
    'nowplaying': {
        'port': confuse.Integer(default=8001)
    }
}

config = _config.get(_template)
