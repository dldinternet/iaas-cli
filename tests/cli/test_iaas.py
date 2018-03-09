"""CLI tests for iaas."""

from iaas.utils import test

class CliTestCase(test.IaaSTestCase):
    def test_iaas_cli(self):
        argv = ['--foo=bar']
        with self.make_app(argv=argv) as app:
            app.run()
            self.eq(app.pargs.foo, 'bar')
