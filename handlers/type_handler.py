from .main_handler import MainHandler
from data import Type

class TypeHandler(MainHandler):
    async def prepare(self):
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
        resp = []

        for type in types:
            type = type.serialize()

        # for t in types:
        #     t = t.serialize()
        #     if len(resp) == 0:
        #         resp.append({
        #             "name": t['type_type'],
        #             "selected": 0,
        #             "children": [ t ]
        #         })
        #     else:
        #         isFound = False
        #         _obj = None
        #
        #         for obj in resp:
        #             if  obj['name'] == t['type_type']:
        #                 _obj = obj['children']
        #                 isFound = True
        #
        #         if isFound:
        #             _obj.append(t)
        #         else:
        #             resp.append({
        #                 "name": t['type_type'],
        #                 "selected": 0,
        #                 "children": [t]
        #             })

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