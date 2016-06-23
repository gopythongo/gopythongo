# -* encoding: utf-8 *-
from typing import Dict, Union, Iterable, Any, Type, TypeVar

import pkg_resources


T = TypeVar("T")


def load_plugins(entrypoint: str, registry: Dict[str, T], plugin_class_attribute: str,
                 plugin_baseclass: Type[T], plugin_name_property: str,
                 initargs: Union[Iterable[Any], None]=None) -> None:
    """
    Loads ``entrypoint`` via ``pkg_resources.iter_entry_points`` and imports all modules attached to it. It then
    looks at the attribute ``plugin_class_attribute`` of the module, which is set to the plugin class. It instantiates
    an instance of the plugin class by calling it's constructor, passing the optional ``initargs``. It then reads the
    ``plugin_name_property`` of the instance which is a string that contains the plugin id, i.e. the "registration
    name" of that module.``registry`` is a ``dict``-like in which a reference to each module will be saved
    using the value of the attribute named by ``plugin_name_property`` as the key.

    :param entrypoint: the name of the setuptools plugin entry point
    :param registry: a dict-like that serves as a registry for the plugins. Each plug-in class is set using
                     ``plugin_name_attribute``
    :param plugin_class_attribute: the attribute on the plugin module that identifies the plugin class
    :param plugin_baseclass: the class that the plugins are supposed to inherit from
    :param plugin_name_property: the property on an instance of ``plugin_class_atrribute`` that will yield the plugin id
    :param initargs: parameters that will be passed to the constructor of ``plugin_class_attribute`` when
                     ``load_plugins`` instantiates it
    """

    if initargs is None:
        initargs = []

    # load external modules
    for ep in pkg_resources.iter_entry_points(entrypoint):  # type: ignore
        module = ep.load()
        if not hasattr(module, plugin_class_attribute):
            raise ImportError("Plugin modules for entry point %s must all have an attribute called %s, but %s has "
                              "none." % (entrypoint, plugin_class_attribute, ep.module_name))

        if not issubclass(plugin_baseclass, getattr(module, plugin_class_attribute)):
            raise ImportError("The plugin class for module %s in plugin entry point %s does not inherit from %s." %
                              (ep.module_name, entrypoint, plugin_baseclass.__name__))

        plugin_instance = getattr(module, plugin_class_attribute)(*initargs)

        if isinstance(getattr(plugin_instance, plugin_name_property), str):
            module_id = getattr(plugin_instance, plugin_name_property)
        else:
            raise ImportError("Plugin class in %s has an attribute %s, but it does not return unicode string." %
                              (ep.module_name, plugin_name_property))

        registry[module_id] = module
