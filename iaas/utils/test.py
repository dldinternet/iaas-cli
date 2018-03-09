"""Testing utilities for IaaS."""

from iaas.cli.main import IaaSTestApp
from cement.utils.test import *

class IaaSTestCase(CementTestCase):
    app_class = IaaSTestApp

    def setUp(self):
        """Override setup actions (for every test)."""
        super(IaaSTestCase, self).setUp()

    def tearDown(self):
        """Override teardown actions (for every test)."""
        super(IaaSTestCase, self).tearDown()

