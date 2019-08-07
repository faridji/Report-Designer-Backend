import json
from .main_handler import MainHandler
from data import Composition, CompositionItem, Type

class CompositionHandler(MainHandler):
    def prepare(self):
        super().prepare()
        self.myModel = Composition

    async def GetByType(self, *args, **kwargs):
        query = self.gdb.query(Composition)
        type_id = self.data['type_id']
        query = query.join(Type, Type.type_id == Composition.type_id)
        query = query.filter(Type.type_id == type_id)
        compositions = query.all()

        print(str(query.statement.compile(compile_kwargs={"literal_binds": True})))

        canvas = compositions[0].serialize()
        data = {
            'type': 'create2',
            'object_id': canvas['name'],
            'element_id': canvas['name'],
            'objectType': canvas['composition_type'],
            'backColor': canvas['styles'],
            'frame': self.replaceNoneWithNull(json.loads(canvas['frame'])),
            'children': self.getChildren(canvas['composition_id'], compositions)
        }

        return await self.sendSuccess(data)

    def replaceNoneWithNull(self,frame):
        for key in frame:
            if frame[key] == None:
                frame[key] = "null"
        return frame

    def getChildData(self, child_id, data):
        child_data = {}
        for item in data:
            item = item.serialize()
            if item['composition_id'] == child_id:
                child_data = {
                    'type': 'create2',
                    'object_id': item['name'],
                    'objectType': item['composition_type'],
                    'backColor': item['styles'],
                    'frame': self.replaceNoneWithNull(json.loads(item['frame'])),
                    'children': self.getChildren(child_id, data)
                }

                if item['composition_type'] == 'Image':
                    child_data['url'] = item['imageURL']

                if item['composition_type'] == 'Label':
                    child_data['text'] = item['labelText']
                    child_data['fontSize'] = item['fontSize']

                if item['composition_type'] == 'HTMLEditor':
                    child_data['text'] = item['labelText']

                return child_data

    def getChildren(self, parent_id, data):
        childs = []

        self.myModel = CompositionItem

        query = self.gdb.query(self.myModel)
        query = query.join(Composition, CompositionItem.parent_id == Composition.composition_id)
        query = query.filter(CompositionItem.parent_id == parent_id)
        composition_items = query.all()

        for child in composition_items:
            child = child.serialize()
            childs.append(self.getChildData(child['child_id'], data))
        return childs


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