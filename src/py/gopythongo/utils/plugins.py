# -* encoding: utf-8 *-

import six
import pkg_resources


def load_plugins(entrypoint, registry, registry_name_attribute_name, requirements):
    """
    Loads ``entrypoint`` via ``pkg_resources.iter_entry_points`` and imports all modules attached to it.
    ``registry_name_attribute_name`` is a string which names an attribute of each module that contains the
    "registration name" of that module.``registry`` is a ``dict`` in which a reference to each module will be saved
    using the value of the attribute named by ``registry_name_attribute_name`` as the key.

    ``requirements`` is a list of strings identifying attributes that each module *must* have to be valid. Not having
    all attributes named in ``requirements`` (boolean "and") will lead to ``load_plugins`` raising ``ImportError``.
    If any item in ``requirements`` is a ``list`` then a module will only need to have *at least one* of the attributes
    named in the sublist (boolean "or").
    """
    # load external modules
    for ep in pkg_resources.iter_entry_points(entrypoint):
        module = ep.load()
        if hasattr(module, registry_name_attribute_name):
            if isinstance(getattr(module, registry_name_attribute_name), six.text_type):
                module_id = getattr(module, registry_name_attribute_name)
            else:
                raise ImportError("Plug-in module %s has an attribute %s, but it's not a unicode string." %
                                  (module.__name__, registry_name_attribute_name))

            for req in requirements:
                if isinstance(req, list):
                    has_any = False
                    for subreq in req:
                        if hasattr(module, subreq):
                            has_any = True
                            break
                    if not has_any:
                        raise ImportError("Plug-in module %s for entry point %s must have at least one of '%s'. It has "
                                          "none." % (module.__name__, entrypoint, ", ".join(req)))
                else:
                    if not hasattr(module, req):
                        raise ImportError("Plug-in module %s for entry point %s must have an attribute called '%s'. "
                                          "It doesn't." % (module.__name__, entrypoint, req))

            registry[module_id] = module
