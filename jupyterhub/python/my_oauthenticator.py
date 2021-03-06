"""
A simple subclass of LocalGoogleOAuthenticator that strips off the @domain.com
portion of a username, allowing us to create valid system usernames.
"""
# From https://github.com/jupyterhub/jupyterhub/blob/master/jupyterhub/auth.py
from grp import getgrnam
import pipes
import pwd
import os, os.path
import re
from shutil import which
import sys
from subprocess import Popen, PIPE, STDOUT
import shlex

from tornado import gen
import pamela

from traitlets.config import LoggingConfigurable
from traitlets import Bool, Set, Unicode, Dict, Any, default, observe

import oauthenticator

HOME_BASE='/mnt/nfs/home/'

class LocalGoogleOAuthenticator(oauthenticator.LocalGoogleOAuthenticator):
    def normalize_username(self, username):
        """Normalize the given username and return it

        Override in subclasses if usernames need different normalization rules.

        The default attempts to lowercase the username and apply `username_map` if it is
        set.
        """
        username = username.split('@')[0].lower()
        username = self.username_map.get(username, username)
        return username

    @gen.coroutine
    def add_user(self, user):
        """Hook called whenever a new user is added
        If self.create_system_users, the user will attempt to be created if it doesn't exist.
        """
        user_exists = yield gen.maybe_future(self.system_user_exists(user))
        if not user_exists:
            if self.create_system_users:
                yield gen.maybe_future(self.add_system_user(user))
            else:
                raise KeyError("User %s does not exist." % user.name)
        else: self.set_home_permissions(user)

        yield gen.maybe_future(super().add_user(user))


    def add_system_user(self, user):
        """Create a new local UNIX user on the system.

        Tested to work on FreeBSD and Linux, at least.
        """
        name = user.name
        cmd = [ arg.format(username=name) for arg in self.add_user_cmd ] + [name]
        self.log.info("Creating user: %s", ' '.join(map(pipes.quote, cmd)))
        p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
        p.wait()
        if p.returncode:
            err = p.stdout.read().decode('utf8', 'replace')
            raise RuntimeError("Failed to create system user %s: %s" % (name, err))
        
        #TODO JMF 16 May 2017: append user's email to userlist?
        #     They'll be added to JHub's DB and the stuff to add them will be run again,
        #     so it might not be necessary to do this here.
        #with open('/srv/jupyterhub/userlist', 'a') as f:
        #    myfile.write(user)
        
        self.set_home_permissions(user)
        
        #TODO JMF 16 May 2017: this is a bit of a hack
        self.rsync_update(user.name, '/home/ec2-user/repos/jupyterhub_AWS_deployment/notebooks/', 'example_notebooks')


    def set_home_permissions(self, user):
        try:
            home = '/mnt/nfs/home/{username}'.format(username=user.name)
            os.system('chown -R {username}:{username} {home}'.format(username=user.name, home=home))
            os.system('chmod +rx {home}'.format(home=home))
            self.log.info('Changed ownership & permissions for user {} (home={})'.format(user.name, home))
        except Exception as e: # what's the right Exception?
            print(e)
            raise Warning('Adding user {} failed!'.format(user.name))


    def rsync_update(self, username, indir, name):
        home = os.path.join(HOME_BASE, username)
        outdir = os.path.join(home, name)
        try:
            self.log.info("rsync-ing notebook directory to {user}'s home".format(user=username))
            os.system('rsync -ru {indir} {outdir}'.format(
                indir=indir, outdir=outdir))
            
            make_notebooks_readonly(indir, outdir)

        except:
            raise Warning('Failded to copy files to ')


def make_notebooks_readonly(indir, outdir):
    """
    chmod -w all notebooks that have been copied into the user's home directory.
    This will force them to duplicate the notebook to work on it (when you duplicate
    a notebook in Jupyter, it will give it 'rw' permissions for your user).
    
    The goal of this is to allow us to safely use our stoopid rsync to update
    notebooks in-place in user's home directories.
    """
    print('doing a stupid chmod -w thing for notebook files')

    nb_matcher = re.compile(r'.*.ipynb')
    
    # Get relative path of all notebook files in indir
    indir_notebooks = []
    for root, dirs, files in os.walk(indir):
        indir_notebooks.extend(os.path.relpath(os.path.join(root, f), indir) for f in files if nb_matcher.match(f))
    
    # Call chmod -w on those same files in the output directory
    outdir_notebooks = map(lambda f: os.path.join(outdir, f), indir_notebooks)
    try:
                                                   # https://stackoverflow.com/a/35857/9291478
        cmd = 'chmod -w ' + ' '.join(map(lambda f: shlex.quote(f), outdir_notebooks))
        os.system(cmd)

    except:
        raise Warning('stupid chmod -w failed')


