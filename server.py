import tornado.web
from configobj import ConfigObj
from handlers import MainHandler, TypeHandler, CompositionHandler

class MakeApp(tornado.web.Application):
    def __init__(self, conf):
        handlers = [
            (r"/api/type/(.*)", TypeHandler),
            (r"/api/composition/(.*)", CompositionHandler),
            (r"/api/", MainHandler),
        ]
        self.Config = conf

        settings = {
            'template_path': 'templates/',
            'static_url_prefix': '/assets/',
            'autoreload': False,
            'xsrf_cookies': False
        }
        tornado.web.Application.__init__(self, handlers, **settings)
        return


if __name__ == "__main__":
    config = ConfigObj('config.conf')
    app = MakeApp(config)

    port = config['Web']['port']

    app.listen(port)
    print('Server is Listening on port', port)
    tornado.ioloop.IOLoop.current().start()