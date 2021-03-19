import datetime
from os.path import dirname
from os.path import join as pjoin

from git import Repo, InvalidGitRepositoryError
from flask import g
from .translate import translate
from .database import kv_get, kv_put


class UpdateException(Exception):
    pass


def should_fetch_updates():
    configured_checks = g.config["CHECK_FOR_UPDATES"]
    if -1 == configured_checks:
        return False

    today = datetime.date.today()
    last_check, _ = kv_get("updates_checked", "date")
    print("last_check: %r" % last_check)
    if last_check is None:
        return True

    if (today - last_check).days >= configured_checks:
        return True

    return False


def get_repo_vars():
    repo = None
    origin = None
    origin_master = None

    try:
        repo = Repo(pjoin(dirname(__file__), ".."))
        try:
            origin = repo.remote("origin")
            try:
                origin_master = origin.refs.master
            except AttributeError:
                raise UpdateException('remote "origin" has no ref called "master"')
        except ValueError:
            raise UpdateException('repository has no remote called "origin"')
    except InvalidGitRepositoryError:
        raise UpdateException("is not a git repository")

    if repo.is_dirty():
        raise UpdateException("repository is dirty")

    return repo, origin, origin_master


def fetch_updates(force=False):
    if not should_fetch_updates() and not force:
        print("not fetching updates")
        return

    repo, origin, origin_master = get_repo_vars()
    print("fetch updates now")
    kv_put("updates_checked", datetime.date.today(), cast="date")
    origin.fetch("master")


def update():
    repo, origin, origin_master = get_repo_vars()
    print("pull updates now")
    origin.pull("master")


def refresh(force=False):
    try:
        fetch_updates(force=force)
        kv_put("updates_available", len(get_commits_behind(force=force)), "int")
    except UpdateException:
        kv_put("updates_available", 0, "int")
        pass


def get_commits_behind(force=False):
    if -1 == g.config["CHECK_FOR_UPDATES"] and not force:
        print("not getting commits behind")
        return []

    repo, origin, origin_master = get_repo_vars()

    local_commits_ahead = list(repo.iter_commits("origin/master..master"))
    local_commits_behind = list(repo.iter_commits("master..origin/master"))

    print("ahead: %r" % local_commits_ahead)
    print("behind: %r" % local_commits_behind)

    if local_commits_ahead:
        raise UpdateException("being ahead of origin was not expected")
        # return local_commits_ahead

    return local_commits_behind
