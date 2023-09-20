from flask import current_app
from flask_pymongo import PyMongo

from shared.services.job_service import JobService
from modules.mongo_model import IndexStore

mongo = PyMongo(current_app, uri=current_app.config['MONGO']['URI'])

# Mongo collections
index_store_collection = mongo.db.index_store
job_collection = mongo.db.job

index_store = IndexStore(collection=index_store_collection)
JobService = JobService(current_app, job_collection)

__all__ = [
    'JobService'
]
