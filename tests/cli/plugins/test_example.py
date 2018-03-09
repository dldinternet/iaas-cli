"""Tests for Example Plugin."""

from iaas.utils import test

class ExamplePluginTestCase(test.IaaSTestCase):
    def test_load_example_plugin(self):
        self.app.setup()
        self.app.plugin.load_plugin('example')
