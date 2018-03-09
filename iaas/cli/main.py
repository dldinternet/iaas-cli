"""IaaS main application entry point."""
import os
import sys
import traceback

import cement
from cement.core.foundation import CementApp
from cement.utils.misc import init_defaults, minimal_logger, is_true
from cement.core.exc import FrameworkError, CaughtSignal, InterfaceError
from cement.utils import fs, misc
from iaas.core import exc

# Application default.  Should update config/iaas.conf to reflect any
# changes, or additions here.
defaults = init_defaults('iaas')

def hook_pre_setup(app):
    if os.path.isdir('./config'):
        ext = app._meta.config_extension
        label = app._meta.label
        path = os.path.join('.', 'config', '%s%s' % (label, ext))
        if app._meta.config_files is None:
            app._meta.config_files = [
                os.path.join('/', 'etc', label, '%s%s' % (label, ext)),
                os.path.join(fs.HOME_DIR, '.%s%s' % (label, ext)),
                os.path.join(fs.HOME_DIR, '.%s' % label, 'config'),
            ]
            # app._meta.config_files = [path]
        app._meta.config_files.append(path)
    else:
        app.log.debug('There is no ./config in {}'.format(os.path))
    try:
        if 'CEMENT_FRAMEWORK_LOGGING_DEBUG' in os.environ.keys():
            if is_true(os.environ['CEMENT_FRAMEWORK_LOGGING_DEBUG']):
                cement.core.foundation.LOG = minimal_logger(cement.core.foundation.LOG.namespace, True)
                cement.ext.ext_argparse.LOG = minimal_logger(cement.ext.ext_argparse.LOG.namespace, True)
    except:
        pass

class IaaSApp(CementApp):
    class Meta:
        label = 'iaas'
        config_defaults = defaults

        # All built-in application bootstrapping (always run)
        bootstrap = 'iaas.cli.bootstrap'

        # Internal plugins (ship with application code)
        plugin_bootstrap = 'iaas.cli.plugins'

        # Internal templates (ship with application code)
        template_module = 'iaas.cli.templates'

        hooks = [
            ('pre_setup', hook_pre_setup),
        ]

        # call sys.exit() when app.close() is called
        exit_on_close = True

        # define what extensions we want to load
        extensions = ['tabulate', 'json', 'yaml', 'mustache', 'jinja2']

        # define our default output handler
        output_handler = 'tabulate'

        # define our handler override options
        handler_override_options = dict(
            output = (['-o'], dict(help='output format')),
        )


    def validate_config(self):
        # fix up paths
        label = self._meta.label

class IaaSTestApp(IaaSApp):
    """A test app that is better suited for testing."""
    class Meta:
        # default argv to empty (don't use sys.argv)
        argv = []

        # don't look for config files (could break tests)
        config_files = []

        # don't call sys.exit() when app.close() is called in tests
        exit_on_close = False


# Define the applicaiton object outside of main, as some libraries might wish
# to import it as a global (rather than passing it into another class/func)
# app = IaaSApp()

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    app = IaaSApp()
    with app:
        try:
            # app.hook.register('post_argument_parsing', hook_pre_setup_1)
            app.run()
        
        except exc.IaaSError as e:
            # Catch our application errors and exit 1 (error)
            app.log.error('IaaSError > %s' % e.message)
            print(e.msg)
            app.exit_code = 1
        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            app.log.warning('CaughtSignal > %s' % e)
            app.exit_code = 0
        except InterfaceError as e:
            # Catch interface errors and exit 1 (error)
            app.log.fatal('InterfaceError > %s' % e)
            app.exit_code = 1
        except FrameworkError as e:
            # Catch framework errors and exit 1 (error)
            app.log.fatal('FrameworkError > %s' % e)
            app.exit_code = 1
        except SystemExit:
            pass
        except Exception as e:
            app.log.fatal('Uncaught Exception > %s: %s' % (e.__class__, e.message))
            traceback.print_exc(file=sys.stdout)
            app.exit_code = 1


if __name__ == '__main__':
    main()
