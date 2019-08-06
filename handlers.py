import json
import tornado.ioloop
import tornado.web
from mysql.connector.errors import ProgrammingError

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from data import Type, Composition, CompositionItem


class MainHandler(tornado.web.RequestHandler):
    def prepare(self):
        print('main  prepare')
        super().prepare()
        self.connectToDatabase()

    def get(self, *args, **kwargs):
        self.write("Hello, get world")

    async def post(self, *args, **kwargs):
        self.set_header("Content-Type", "application/json")
        # self.write({'status': "Hello, post world"})

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


class TypeHandler(MainHandler):
    async def prepare(self):
        print('type  prepare')
        super().prepare()
        self.myModel = Type

    async def Index(self, *args, **kwargs):
        query = self.gdb.query(self.myModel)

        types = query.all()

        resp = []
        for t in types:
            resp.append(t.serialize())

        await self.sendSuccess(resp)

    async def Get(self, *args, **kwargs):
        query = self.gdb.query(self.myModel)

        type_id = self.get_argument('type_id', None)
        if type_id is not None:
            query = query.filter(self.myModel.type_id == type_id)

        types = query.all()

        resp = {}
        for t in types:
            resp[t.type_name] = t.serialize()

        await self.sendSuccess(resp)

    async def Add(self, *args, **kwargs):
        obj = self.myModel()
        obj.type_name = self.data.get('type_name')
        obj.type_type = self.data.get('type_type')
        obj.type_description = self.data.get('type_description', None)

        self.gdb.add(obj)
        self.gdb.commit()

        self.set_header("Content-Type", "application/json")
        self.write({'oid': obj.type_id})

    async def Update(self, *args, **kwargs):
        type_id = self.data.get('type_id')
        t = self.gdb.query(self.myModel).filter(self.myModel.type_id == type_id).one_or_none()
        if t is None:
            self.write('Invalid type id')
            self.finish()
            return

        t.type_name = self.data.get('type_name')
        t.type_type = self.data.get('type_type')
        t.type_description = self.data.get('type_description', None)

        self.gdb.commit()

        self.set_header("Content-Type", "application/json")
        self.write({'oid': t.type_id})

    async def Delete(self, *args, **kwargs):
        type_id = self.data.get('type_id')
        self.gdb.query(self.myModel).filter(self.myModel.type_id == type_id).delete()
        self.gdb.commit()
        self.set_header("Content-Type", "application/json")
        self.write({'oid': type_id})


class CompositionHandler(MainHandler):
    def prepare(self):
        super().prepare()
        self.myModel = Composition

    async def GetByType(self, *args, **kwargs):
        resp = []
        query = self.gdb.query(Composition)
        type_id = self.data['type_id']
        query = query.join(Type, Type.type_id == Composition.type_id)
        query = query.filter(Type.type_id == type_id)
        compositions = query.all()

        print(str(query.statement.compile(compile_kwargs={"literal_binds": True})))

        for comp in compositions:
            resp.append(comp.serialize())

        return await self.sendSuccess(resp)

    async def Add(self, *args, **kwargs):
        type = Type()

        type.type_name = self.data['name']
        type.type_type = self.data['type']
        type.type_description = self.data.get('description', None)

        self.gdb.add(type)
        self.gdb.flush()

        self.iterateJson(data=self.data['data'], parent={}, type_id=type.type_id)
        self.gdb.commit()

        self.add_header('Content-Type', 'application/json')
        self.write({ 'id' : type.type_id})

    def iterateJson(self,data, parent, type_id):
        self.writeToComposition(data, parent, type_id)
        for obj in data['children']:
            self.iterateJson(obj, data, type_id)

    def writeToComposition(self, command, parent, type_id):
        obj = self.myModel()
        obj.name = command['object_id']
        obj.composition_type = command['objectType']
        obj.frame = json.dumps(command['frame'])
        obj.styles = command['backColor']
        obj.imageURL = command.get('url', None)
        obj.labelText = command.get('text', None)
        obj.fontSize = command.get('fontSize', None)
        obj.creator = 'Farid'
        obj.is_private = 0
        obj.type_id = type_id

        self.gdb.add(obj)
        self.gdb.flush()

        id = obj.composition_id
        command['oid'] = id                     # Save parent Id for future use

        parent_oid = parent.get('oid', None)    # get parent id of current item

        obj = CompositionItem()
        obj.child_id = id
        obj.parent_id = parent_oid

        self.gdb.add(obj)
        self.gdb.flush()


class CompositionItemHandler(MainHandler):
    def prepare(self):
        super().prepare()
        self.myModel = CompositionItem

    async def Index(self, *args, **kwargs):
        all = self.gdb.query(self.myModel).all()
        await self.sendSuccess([])