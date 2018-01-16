import sys

this = sys.modules[__name__]

this._objects = {}

def addObject(obj_name, obj):
    this._objects[obj_name] = obj

def deleteObjectByRef(obj):
    for name, object in this._objects.items():
        if object == obj:
            del this._objects[name]
            break

def deleteObjectByName(obj_name):
    if obj_name in this._objects:
        del this._objects[obj_name]

def getObject(obj_name):
    return this._objects[obj_name] if obj_name in this._objects else None

def listObjects():
    return list(this._objects.keys())



