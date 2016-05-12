# -* encoding: utf-8 *-
from typing import Dict, Iterable, Any, Union


def load_plugins(entrypoint: str, registry: Dict[str, object], plugin_class_attribute: str,
                 plugin_baseclass: type, plugin_name_property: str, initargs: Union[Iterable[Any], None]=None): ...
