# Filename: setup_db.py

from configobj import ConfigObj
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from data import Base


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
        return


if __name__ == "__main__":
    s = Setup()
    s.setup()
