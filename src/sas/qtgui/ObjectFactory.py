import sys

this = sys.modules[__name__]

this._objects = {}

def addObject(obj_name, obj):
    this._objects[obj_name] = obj

def deleteObject(obj_name):
    if obj_name in this._objects:
        del this._objects[obj_name]

def getObject(obj_name):
    return this._objects[obj_name] if obj_name in this._objects else None

def listObjects():
    return this._objects.keys()



