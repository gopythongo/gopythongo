# -* encoding: utf-8 *-

import gopythongo.shared.docker_args
from gopythongo.stores import BaseStore


class DockerStore(BaseStore):
    def __init__(self, *args, **kwargs):
        super(DockerStore, self).__init__(*args, **kwargs)

    @property
    def store_name(self):
        return u"docker"

    def add_args(self, parser):
        gopythongo.shared.docker_args.add_shared_args(parser)

    def validate_args(self, args):
        return True

    def store(self, args):
        pass


store_class = DockerStore
