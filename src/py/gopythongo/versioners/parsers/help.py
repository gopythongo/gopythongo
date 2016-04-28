# -* encoding: utf-8 *-

import argparse


class VersionParserHelpAction(argparse.Action):
    def __init__(self,
                 option_strings,
                 dest,
                 default=None,
                 choices=None,
                 help="Show help for GoPythonGo version parsers."):
        super(VersionParserHelpAction, self).__init__(option_strings=option_strings, dest=dest, default=default,
                                                      nargs="?", choices=choices, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        from gopythongo.versioners import versioners
        if values in versioners.keys():
            versioners[values].print_help()
        else:
            print("Version parsers\n"
                  "===============\n"
                  "\n"
                  "Version Parsers take a version string read by a Versioner in one format and\n"
                  "convert it into a transformable object. The Version Parser then applies any\n"
                  "action selected on the command-line to the version information. Finally, the\n"
                  "version information is then converted (if possible) into the target format.\n")
