# -* encoding: utf-8 *-

import argparse

from gopythongo.utils import highlight
from typing import Any, Iterable


class VersionerHelpAction(argparse.Action):
    def __init__(self,
                 option_strings: str,
                 dest: str,
                 default: Any=None,
                 choices: Iterable[Any]=None,
                 help: str="Show help for GoPythonGo Versioners.") -> None:
        super().__init__(option_strings=option_strings, dest=dest, default=default, nargs="?",
                         choices=choices, help=help)

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 values: str, option_string: str=None) -> None:
        from gopythongo.versioners import versioners
        if values in versioners.keys():
            versioners[values].print_help()
        else:
            print("Versioners\n"
                  "==========\n"
                  "\n"
                  "Versioners are responsible for reading a version string from a source. What the\n"
                  "source is, depends on the Versioner.\n"
                  "\n"
                  "You specify how to read a version using %s and split it into its\n"
                  "parts using %s. The target version is then specified using\n"
                  "%s. The target version can then be optionally modified by setting\n"
                  "%s.\n"
                  "\n"
                  "If you want more information on the available Versioners and their supported\n"
                  "methods, you want to use %s.\n"
                  "You can find out more about Version Parsers by using %s.\n"
                  "\n"
                  "The GoPythonGo versioning system is all oriented around %s\n"
                  "%s. SemVer is very limited in some ways due to a lack of\n"
                  "support for hotfixes, sortable branch versions and unfixable standard\n"
                  "violations (at least in SemVer 2.0.0). However, IT IS the easiest to support\n"
                  "lowest common denominator. GoPythonGo also supports more expressive versioning\n"
                  "systems like Debian system and makes it easy to plug-in your own Version\n"
                  "Parsers with just a few lines of code. Please also read the output of\n"
                  "%s.\n"
                  "\n"
                  "Version process\n"
                  "---------------\n"
                  "\n"
                  "  ,--------.    ,--------.    ,---------.             ,--------.    ,-------.\n"
                  "  | Reader | -> | Parser | -> | Creator | -[action]-> | Packer | -> | Store |\n"
                  "  `--------'    `--------'    `---------'             `--------'    `-------'\n"
                  "\n"
                  "Version actions\n"
                  "---------------\n"
                  "\n"
                  "Typically you want to read a version string and then modify it in some way. I\n"
                  "recommend that you %s, but\n"
                  "create automatically incremented version strings for development versions which\n"
                  "are automatically distributed to your staging/development systems. GoPythonGo\n"
                  "can modify version strings through %s, which supports the\n"
                  "following parameter values:\n"
                  "\n"
                  "    %s - increment the version string epoch\n"
                  "    %s - increment the version string patch level\n"
                  "    %s - increment the version string revision\n"
                  "    %s - do nothing to the version string (the default)\n"
                  "\n"
                  "This action will be performed by the Versioner selected for creating the result\n"
                  "version string which will be used by the packer and store subsystems. For\n"
                  "example: The %s Versioner, when faced with the 'increment-epoch' action, will\n"
                  "first find out the highest Epoch value the target store repository, then\n"
                  "increment that Epoch by 1 and then create the new version string. For more\n"
                  "details, please look at the help pages of the individual Versioners.\n"
                  "\n"
                  "Best practice\n"
                  "-------------\n"
                  "\n"
                  "A good start is to read the version from your Python project so you have a\n"
                  "central point where you change the version. Make sure that your development\n"
                  "model changes the version string according to SemVer when you make a new\n"
                  "release. For example when using git flow, you change the version every time\n"
                  "you create a new release branch.\n"
                  "\n"
                  "Then you just have to make sure that your packaging system will recognize the\n"
                  "automatically incremented new version string as newer than the last one. I like\n"
                  "to use the following configuration for my development branches:\n"
                  "\n"
                  "    --packer='fpm' \\\n"
                  "    --store='aptly' \\\n"
                  "    --versioner='pymodule' \\\n"
                  "    --pymodule-read='myproject.version' \\\n"
                  "    --version-parser='semver' \\\n"
                  "    --version-action='increment-revision'\n"
                  "\n"
                  "This will:\n"
                  "\n"
                  "    * read the %s attribute from the Python module %s in the\n"
                  "      current PYTHONPATH,\n"
                  "    * then parse this value as a SemVer formatted version,\n"
                  "    * then find the highest revision of that version in the current package\n"
                  "      repository,\n"
                  "    * then increment the version revision by 1 and\n"
                  "    * finally output the result as a Debian-compatible version string.\n"
                  "\n"
                  "You can find information about writing and plugging your own Versioners into\n"
                  "GoPythonGo on http://gopythongo.com/.\n" %
                  (highlight("--read-version"), highlight("--version-parser"),
                   highlight("--new-version"), highlight("--version-action"),
                   highlight("--help-versioner=[%s]" % ", ".join(versioners.keys())),
                   highlight("--help-versionparsers"),
                   highlight("Semantic Versioning"), highlight("http://semver.org/)"),
                   highlight("--help-versionparsers"),
                   highlight("keep version strings constant for release versions"),
                   highlight("--version-action"), highlight("increment-epoch"),
                   highlight("increment-patch"), highlight("increment-revision"), highlight("none"),
                   highlight("aptly"), highlight("version"), highlight("myproject")))

        parser.exit()
