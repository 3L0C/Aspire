#!/usr/bin/env python3

from datetime import datetime
from app import db
from sqlalchemy.ext.declarative import declared_attr

class BaseEntity(db.Model):
    """Base class for all entities with common attributes."""
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
