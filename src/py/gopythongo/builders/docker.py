# -* encoding: utf-8 *-

import gopythongo.shared.docker_args

from gopythongo.utils import print_info, highlight
from gopythongo.builders import BaseBuilder


class DockerBuilder(BaseBuilder):
    def __init__(self, *args, **kwargs):
        super(DockerBuilder, self).__init__(*args, **kwargs)

    @property
    def builder_name(self):
        return u"docker"

    def add_args(self, parser):
        gopythongo.shared.docker_args.add_shared_args(parser)

    def validate_args(self, args):
        gopythongo.shared.docker_args.validate_shared_args(args)

    def build(self, args):
        print_info("Building with %s" % highlight("docker"))


builder_class = DockerBuilder
