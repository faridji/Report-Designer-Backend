# Filename: setup_db.py

from data import Base
import json, os
from configobj import ConfigObj

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

from data import Type, Composition, CompositionItem

class Setup:
    def __init__(self):
        config = ConfigObj('config.conf')
        self.Config = config
        return

    def setup(self):
        db_config = {
            'user': self.Config['Db']['User'],
            'password': self.Config['Db']['Password'],
            'host': self.Config['Db']['Server'],
            'database': self.Config['Db']['Database']
        }

        db_url = 'mysql+mysqlconnector://{user}:{password}@{host}/{database}'.format(**db_config)
        engine = create_engine(db_url, echo=self.Config['Db'].as_bool('DebugDb'))

        if not database_exists(engine.url):
            create_database(engine.url)

        Base.metadata.create_all(engine)

        sessionMaker = sessionmaker(bind=engine)
        self.gdb = sessionMaker()

        type_id = self.createRootType()
        self.insertPreLoadedData(type_id)

    def createRootType(self):
        type = Type()

        type.name = 'ROOT ELEMENT'

        self.gdb.add(type)
        self.gdb.commit()

        print('type_id -> ', type.id)
        return type.id

    def insertPreLoadedData(self, type_id):

        currDir = os.path.dirname(os.path.realpath(__file__))
        basicElementDataFile = 'preloaded_data.json'.format(currDir)

        with open(basicElementDataFile) as data_file:
            data = json.load(data_file)

        for composition in data:
            self.iterateJson(data=composition, parent={}, type_id=type_id)

        self.gdb.commit()
        self.gdb.close()
        print('Preloaded Data Successfully Inserted.')
        return

    def iterateJson(self,data, parent, type_id):
        self.writeToComposition(data, parent, type_id)
        for obj in data['children']:
            self.iterateJson(obj, data, type_id)

    def writeToComposition(self, command, parent, type_id):
        obj = Composition()
        obj.type_id = type_id

        obj.name = command['name']
        obj.object_id = command['object_id']
        obj.objectType = command['objectType']
        obj.frame = json.dumps(command['frame'])
        obj.styles = command['backColor']
        obj.imageURL = command.get('url', None)
        obj.labelText = command.get('text', None)
        obj.fontSize = command.get('fontSize', None)
        obj.creator = 'Farid'
        obj.is_private = 0

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

if __name__ == "__main__":
    s = Setup()
    s.setup()
