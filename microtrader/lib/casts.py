def cast(value, targetType):

    if targetType == bool:
        return toBool(value)

    return targetType(value)

def toBool(value):

    if type(value) == str:
        value = value.strip().lower()
        if value not in ["true", "false"]:
            raise ValueError(f"Can't convert \"{value}\" to boolean value")
        return (value == "true")

    return bool(value)
