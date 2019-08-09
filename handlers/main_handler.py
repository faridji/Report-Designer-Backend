import json
import tornado.web
from mysql.connector.errors import ProgrammingError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class MainHandler(tornado.web.RequestHandler):
    def prepare(self):
        super().prepare()
        self.connectToDatabase()

    def get(self, *args, **kwargs):
        self.write("Hello, get world")

    async def post(self, *args, **kwargs):
        self.set_header("Content-Type", "application/json")

        func = None

        if self.request.uri.endswith('/'):
            func = getattr(self, 'Index', None)
        else:
            path = self.request.uri.split('?')[0].split('/')
            print('path', path)
            method = path[-1]
            print('method', method)
            func = getattr(self, method, None)

        if func is None:
            raise tornado.web.HTTPError(404)

        resp = {}

        try:
            return await func(args, kwargs)
        except ProgrammingError as pe:
            print('kw', pe)
            resp['status'] = 'KeyError'
            resp['ErrorMessage'] = pe.args[0]
        except KeyError as ke:
            print('kw', ke)
            resp['status'] = 'KeyError'
            resp['ErrorMessage'] = ke.args[0]
        except BaseException as ex:
            print('ex', ex)
            resp['status'] = 'Error'
            resp['ErrorMessage'] = str(ex)

        self.write(resp)

    def on_finish(self):
        if hasattr(self, 'gdb'):
            self.gdb.close()
            self.gdb = None

    async def sendSuccess(self, data):
        resp = {'status': 'Ok', 'data': data}
        self.write(resp)

    def connectToDatabase(self):
        db_config = {
            'user': self.application.Config['Db']['User'],
            'password': self.application.Config['Db']['Password'],
            'host': self.application.Config['Db']['Server'],
            'database': self.application.Config['Db']['Database']
        }

        db_url = 'mysql+mysqlconnector://{user}:{password}@{host}/{database}'.format(**db_config)
        engine = create_engine(db_url, echo=self.application.Config['Db'].as_bool('DebugDb'))
        sessionMaker = sessionmaker(bind=engine)
        self.gdb = sessionMaker()

        # get body data
        self.data = {}

        if len(self.request.arguments) > 0:
            self.data = {k: self.get_argument(k) for k in self.request.arguments}
        elif len(self.request.body) > 0:
            self.data = json.loads(self.request.body.decode('utf8'))