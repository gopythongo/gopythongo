.. _plugins:

The GoPythonGo plugin system
============================

Each process step in GoPythonGo's execution plan (versioners, versionparsers, builders, assemblers, packers, stores)
has a setuptools entry point where plugins can be registered allowing you to put your own code into each of these
steps. It makes sense to look at GoPythonGo's source code since all existing functionality is also just provided
by such plugins (though the builtin plugins sidestep the setuptools entry_point infrastructure).

List of setuptools entry points
-------------------------------

Modules linking to ``gopythongo.assemblers`` must have a ``assembler_class`` property which must be a subclass of
``gopythongo.assemblers.BaseAssembler``.

Modules linking to ``gopythongo.builders`` must have a ``builder_class`` property which must be a subclass of
``gopythongo.builders.BaseBuilder``.

Modules linking to ``gopythongo.initializers`` must have a ``initializer_class`` property which must be a subclass of
``gopythongo.initializers.BaseInitializer``.

Modules linking to ``gopythongo.packers`` must have a ``packer_class`` property which must be a subclass of
``gopythongo.packers.BasePacker``.

Modules linking to ``gopythongo.stores`` must have a ``store_class`` property which must be a subclass of
``gopythongo.stores.BaseStore``.

Modules linking to ``gopythongo.versioners`` must have a ``versioner_class`` property which must be a subclass of
``gopythongo.versioners.BaseVersioner``.

Modules linkting to ``gopythongo.versionparsers`` must have a ``versionparser_class`` property which must be a subclass
of ``gopythongo.versioners.parsers.BaseVersionParser``.

