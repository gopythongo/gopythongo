# -* encoding: utf-8 *-
import argparse
import shlex

from typing import Any, Sequence, Union, Dict, cast, List

import gopythongo.shared.aptly_args as _aptly_args

from gopythongo.shared.aptly_args import get_aptly_cmdline
from gopythongo.stores import BaseStore
from gopythongo.utils import print_debug, highlight, print_info, run_process, ErrorMessage, print_warning
from gopythongo.utils.buildcontext import the_context
from gopythongo.utils.debversion import DebianVersion
from gopythongo.versioners.parsers import VersionContainer
from gopythongo.versioners.parsers.debianparser import DebianVersionParser
from gopythongo.versioners.aptly import AptlyVersioner


class AptlyStore(BaseStore):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def store_name(self) -> str:
        return u"aptly"

    @property
    def supported_version_parsers(self) -> List[str]:
        return ["debian"]

    def add_args(self, parser: argparse.ArgumentParser) -> None:
        _aptly_args.add_shared_args(parser)

        gp_ast = parser.add_argument_group("Aptly Store options")
        gp_ast.add_argument("--aptly-distribution", dest="aptly_distribution", default="", env_var="APTLY_DISTRIBUTION",
                            help="Set the target distribution for aptly builds.")
        gp_ast.add_argument("--aptly-repo-opts", dest="aptly_repo_opts", default="", env_var="APTLY_REPO_OPTS",
                            help="Specify additional command-line parameters which will be appended to every "
                                 "'aptly repo' command executed by the Aptly Store.")
        gp_ast.add_argument("--aptly-publish-opts", dest="aptly_publish_opts", default="", env_var="APTLY_PUBLISH_OPTS",
                            help="Specify additional command-line parameters which will be appended to every "
                                 "'aptly publish' command executed by the Aptly Store.")
        gp_ast.add_argument("--aptly-publish-endpoint", dest="aptly_publish_endpoint", metavar="ENDPOINT", default=None,
                            env_var="APTLY_PUBLISH_ENDPOINT",
                            help="Publish the Aply repo to the specified endpoint after generated packages have been "
                                 "added to the repo. Please note that you will have to add additional configuration to "
                                 "the aptly config file, for example when you want to publish to S3. It's also likely "
                                 "that you want to set --aptly-publish-opts and pass aptly -passphrase-file, -keyring "
                                 "and other necessary arguments for signing the repo. Please note: You will probably "
                                 "want to set these arguments using environment variables on your build server if "
                                 "you're using a CI environment.")
        gp_ast.add_argument("--aptly-dont-remove", dest="aptly_dont_remove", action="store_true", default=False,
                            env_var="APTLY_DONT_REMOVE",
                            help="By default, if a created package already exists in the repo specified by --repo, "
                                 "the aptly store will overwrite it. Setting --aptly-dont-remove will instead lead "
                                 "to an error if the package already exists.")
        gp_ast.add_argument("--aptly-overwrite-newer", dest="aptly_overwrite_newer", action="store_true", default=False,
                            env_var="APTLY_OVERWRITE_NEWER",
                            help="If set, the aptly Store will store newly generated packages in the repo which are "
                                 "older than the packages already there. By default, it will raise an error message "
                                 "instead.")

    def validate_args(self, args: argparse.Namespace) -> None:
        _aptly_args.validate_shared_args(args)

        from gopythongo.versioners import get_version_parsers
        debvp = cast(DebianVersionParser, get_version_parsers()["debian"])  # type: DebianVersionParser
        if args.version_action not in debvp.supported_actions:
            raise ErrorMessage("Version Action is set to '%s', but you chose the Aptly Store which relies on Debian "
                               "version strings. Unfortunately the Debian Versioner does not support the '%s' action. "
                               "It only supports: %s." %
                               (highlight(args.version_action), highlight(args.version_action),
                                highlight(", ".join(debvp.supported_actions))))

        if "-distribution" in args.aptly_publish_opts:
            print_warning("You are using %s in your Aptly Store options. You should use the %s GoPythonGo argument "
                          "instead, since using -distribution in the aptly command line is invalid when GoPythonGo "
                          "tries to update a published repo." %
                          (highlight("-distribution"), highlight("--aptly-distribution")))

    @staticmethod
    def _get_aptly_versioner() -> AptlyVersioner:
        from gopythongo.versioners import get_versioners
        from gopythongo.versioners.aptly import AptlyVersioner
        aptlyv = cast(AptlyVersioner, get_versioners()["aptly"])
        return aptlyv

    @staticmethod
    def _get_debian_versionparser() -> DebianVersionParser:
        from gopythongo.versioners import get_version_parsers
        debvp = cast(DebianVersionParser, get_version_parsers()["debian"])
        return debvp

    def _check_version_exists(self, package_name: str, version: str, args: argparse.Namespace) -> bool:
        aptlyv = self._get_aptly_versioner()
        if aptlyv.query_repo_versions("Name (%s), $Version (= %s)" %
                                      (package_name, version), args,
                                      allow_fallback_version=False):
            return True
        else:
            return False

    def _check_package_exists(self, package_name: str, args: argparse.Namespace) -> bool:
        aptlyv = self._get_aptly_versioner()
        if aptlyv.query_repo_versions("Name (%s)" % package_name, args, allow_fallback_version=False):
            return True
        else:
            return False

    def _find_new_version(self, package_name: str, version: VersionContainer[DebianVersion], action: str,
                          args: argparse.Namespace) -> VersionContainer[DebianVersion]:
        """
        Find the next version given `action` in the target repo for `package_name`.
        """
        print_debug("Finding a version string in the aptly store for package %s" % highlight(package_name))
        aptlyv = self._get_aptly_versioner()
        debvp = self._get_debian_versionparser()

        debversions = aptlyv.query_repo_versions("Name (%s), $Version (%% *%s*)" %
                                                 (package_name, version.version), args, allow_fallback_version=False)

        if debversions:
            # we already have a version in the repo
            new_base = debversions[-1]
            print_debug("Found an existing version %s for package %s" %
                        (highlight(str(new_base)), highlight(package_name)))
            after_action = debvp.execute_action(debvp.deserialize(str(new_base)), action)
            if after_action.version < version.version:
                if args.aptly_overwrite_newer:
                    print_info("Will overwrite same or newer version in repo with older version (existing: %s, "
                               "new: %s)" % (highlight(str(version.version)), highlight(str(after_action.version))))
                    return after_action
                else:
                    raise ErrorMessage("Repo already contains a newer version of %s than the one that was going to be "
                                       "added (existing: %s new: %s)" %
                                       (highlight(package_name), highlight(str(new_base)),
                                        highlight(str(version.version))))
            if self._check_version_exists(package_name, str(after_action.version), args):
                print_debug("The new after-action (%s) version %s, based off %s, derived from %s is already taken, so "
                            "we now recursively search for an unused version string for %s" %
                            (action, highlight(str(after_action.version)), highlight(str(new_base)),
                             highlight(str(version.version)), highlight(package_name)))
                self._find_new_version(package_name, after_action, action, args)
            else:
                print_info("After executing action %s, the selected next version for %s is %s" %
                            (highlight(action), highlight(package_name), highlight(str(after_action.version))))
                return after_action
        else:
            print_info("%s seems to be as yet unused" % highlight(str(version.version)))
            return version

    def generate_future_versions(self, artifact_names: Sequence[str], base_version: VersionContainer[Any], action: str,
                                 args: argparse.Namespace) -> Union[Dict[str, VersionContainer[DebianVersion]], None]:
        ret = {}  # type: Dict[str, VersionContainer[DebianVersion]]
        base_debv = base_version.convert_to("debian")
        for package_name in artifact_names:
            next_version = self._find_new_version(package_name, base_debv, action, args)
            ret[package_name] = next_version
        return ret

    def store(self, args: argparse.Namespace) -> None:
        # add each package to the repo
        for pkg in the_context.packer_artifacts:
            if not args.aptly_dont_remove:  # aptly DO remove
                if self._check_package_exists(pkg.artifact_metadata["package_name"], args):
                    print_info("Removing existing package %s from repo %s" %
                               (highlight(pkg.artifact_metadata["package_name"]), args.aptly_repo))
                    cmdline = get_aptly_cmdline(args)
                    cmdline += ["repo", "remove", args.aptly_repo, pkg.artifact_metadata["package_name"]]
                    run_process(*cmdline)

            print_info("Adding %s to repo %s" % (highlight(pkg.artifact_filename), highlight(args.aptly_repo)))
            cmdline = get_aptly_cmdline(args)
            cmdline += shlex.split(args.aptly_repo_opts)

            cmdline += ["repo", "add", args.aptly_repo, pkg.artifact_filename]
            run_process(*cmdline)

        # publish the repo or update it if it has been previously published
        if args.aptly_publish_endpoint:
            print_info("Publishing repo %s to endpoint %s" %
                       (highlight(args.aptly_repo), highlight(args.aptly_publish_endpoint)))
            cmdline = get_aptly_cmdline(args) + ["publish"]

            # check whether the publishing endpoint is already in use by executing "aptly publish list" and if so,
            # execute "aptly publish update" instead of "aptly publish repo"
            query_publish = cmdline + ["list", "-raw"]
            out = run_process(*query_publish)
            cmd = "repo"
            if out.output:
                lines = out.output.split("\n")  # type: List[str]
                for l in lines:
                    if l.strip() != "":
                        endpoint, dist = l.split(" ", 1)
                        if endpoint == args.aptly_publish_endpoint:
                            print_info("Publishing endpoint %s already in use. Executing update..." %
                                       highlight(args.aptly_publish_endpoint))
                            cmd = "update"

            cmdline += [cmd, "-batch=true"]  # -batch=true enables gpg to run without an attached TTY on a build server

            # when publishing the repo for the first time we need to add the -distribution flag
            if cmd == "repo":
                cmdline += shlex.split(args.aptly_publish_opts)
                cmdline += ["-distribution", args.aptly_distribution]
                cmdline += [args.aptly_repo, args.aptly_publish_endpoint]
            else:
                cmdline += shlex.split(args.aptly_publish_opts)
                cmdline += [args.aptly_distribution, args.aptly_publish_endpoint]

            run_process(*cmdline)


store_class = AptlyStore
