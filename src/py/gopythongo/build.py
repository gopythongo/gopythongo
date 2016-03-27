#!/usr/bin/python -u
# -* encoding: utf-8 *-

from configargparse import ArgParser as ArgumentParser


def add_parser(subparsers):
    parser = subparsers.add_parser(name="build",
                                   description="",
                                   help="gopythongo.main build")


def main():
    pass
