#!/usr/bin/python -u
# -* coding: utf-8 *-

from configargparse import ArgParser as ArgumentParser


def get_parser():
    parser = ArgumentParser(description="",
                            fromfile_prefix_chars="@",
                            default_config_files=["./.gopythongo"],
                            add_config_file_help=False,
                            prog="gopythongo.main build")

    return parser


def main():
    pass
