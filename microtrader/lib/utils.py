from lib.casts import cast

def mapDict(sourceDict, keyMap):
    return {    
        targetKey: sourceDict[sourceKey]
        for targetKey, sourceKey in keyMap.items()
        if sourceKey in sourceDict
    }

def mergeDefaults(sourceDict, defaults):
    return sourceDict | {
        defaultKey: cast(sourceDict[defaultKey], type(defaultValue))
        if defaultKey in sourceDict else defaultValue
        for defaultKey, defaultValue in defaults.items()
    }

def apply(func, value):
    return None if value is None else func(value)

def coalesce(*values):
    return next((value for value in values if value is not None), None) 
