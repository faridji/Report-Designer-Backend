
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.inspection import inspect
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
DEFAULT_TABLE_ARGS = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci'}


class Serializer:
    def serialize(self):
        obj = {}
        allKeys = inspect(self).attrs.keys()
        allKeys = sorted(allKeys)

        for c in allKeys:
            v = getattr(self, c)

            if hasattr(v, 'serialize'):
                v = v.serialize()
                # continue

            obj[c] = v

        return obj


class Type(Base, Serializer):
    __tablename__ = 'types'
    __table_args__ = DEFAULT_TABLE_ARGS

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(55), nullable=False)


class Composition(Base, Serializer):
    __tablename__ = 'compositions'
    __table_args__ = DEFAULT_TABLE_ARGS

    composition_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)

    type_id = Column(ForeignKey(Type.id, onupdate='RESTRICT', ondelete='RESTRICT'), nullable=False)
    type = relationship(Type, remote_side=Type.id, foreign_keys=type_id, lazy='select')

    name = Column(String(100), nullable=True)
    objectType = Column(String(255), nullable=False)
    object_id = Column(String(55), nullable=False)
    styles = Column(String(255), nullable=False)
    frame = Column(String(255), nullable=False)
    imageURL = Column(String(255), nullable=True)
    labelText = Column(String(255), nullable=True)
    fontSize = Column(Integer, nullable=True)
    creator = Column(String(100), nullable=True)
    is_private = Column(Boolean(0), nullable=True)

class CompositionItem(Base, Serializer):
    __tablename__ = 'composition_items'
    __table_args__ = DEFAULT_TABLE_ARGS

    composition_item_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)

    parent_id = Column(ForeignKey(Composition.composition_id, onupdate='RESTRICT', ondelete='RESTRICT'), nullable=True)
    parent = relationship(Composition, remote_side=Composition.composition_id, foreign_keys=parent_id, lazy='select')

    child_id = Column(ForeignKey(Composition.composition_id, onupdate='RESTRICT', ondelete='RESTRICT'), nullable=False)
    child = relationship(Composition, remote_side=Composition.composition_id, foreign_keys=child_id, lazy='select')

