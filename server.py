import tornado
from configobj import ConfigObj
from handlers import TypeHandler, CompositionHandler, CompositionItemHandler, MainHandler

class MakeApp(tornado.web.Application):
    def __init__(self, conf):
        handlers = [
            (r"/type/(.*)", TypeHandler),
            (r"/composition/(.*)", CompositionHandler),
            (r"/ci/(.*)", CompositionItemHandler),
            (r"/", MainHandler),
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