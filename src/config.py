import json


def config_load(file, *args: str) -> tuple:
    with open(file) as f:
        config = json.load(f)
    return tuple(config[k] for k in args)


def config_save(file, **kwargs):
    with open(file, "w") as f:
        json.dump(kwargs, f)
