from flask import current_app
from flask_pymongo import PyMongo

from shared.services.job_service import JobService

mongo = PyMongo(current_app, uri=current_app.config['MONGO']['URI'])

# Mongo collections
job_collection = mongo.db.job

JobService = JobService(current_app, job_collection)

__all__ = [
    'JobService'
]
