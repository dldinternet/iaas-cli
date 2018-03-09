from cement.core.foundation import CementApp

class MyApp(CementApp):
    class Meta:
        label = 'myapp'

    def setup(self):
        # always run core setup
        super(MyApp, self).setup()

        # define hooks in setup
        self.hook.define('my_hook')

    def run(self):

        # run our custom hook
        for res in self.hook.run('my_hook', app):
            pass

# the following are the function that will run when ``my_hook`` is called
def func1(app):
    print 'Inside hook func1'

def func2(app):
    print 'Inside hook func2'

def func3(app):
    print 'Inside hook func3'


with MyApp() as app:
    # register all hook functions *after* the hook is defined (setup) but
    # also *before* the hook is called (different for every hook)
    app.hook.register('my_hook', func1, weight=0)
    app.hook.register('my_hook', func2, weight=100)
    app.hook.register('my_hook', func3, weight=-99)

    # run the application
    app.run()
