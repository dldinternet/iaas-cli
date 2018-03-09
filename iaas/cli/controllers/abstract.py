"""IaaS base controller."""
import importlib
import logging
import string
import sys
import json
from ConfigParser import NoSectionError
from collections import OrderedDict

import re

from cement.core.exc import FrameworkError
from cement.ext.ext_argparse import ArgparseController
from cement.ext.ext_tabulate import TabulateOutputHandler
from cement.ext.ext_yaml import YamlOutputHandler
from cement.utils.misc import is_true
from cement.utils.shell import Prompt
from iaas.core.exc import IaaSError


class ArgPrompt(Prompt):
    class Meta:
        text = "TBD"
        options = []
        # options_separator = '|'
        default = None
        clear = False
        numbered = True
        max_attempts = 3
        auto = False

    # def process_input(self):
    #     if self.input.lower() == 'yes':
    #         # do something crazy
    #         pass
    #     else:
    #         # don't do anything... maybe exit?
    #         sys.exit(1)


class IaaSAbstractController(ArgparseController):
    class Meta:
        label = 'abstract'
        description = 'IaaS'
        min_args = 1
        table_format = 'psql'

    # def __init__(self, *args, **kw):
    #     super(IaaSAbstractController, self).__init__(*args, **kw)
    #     # self._meta.headers = None

    def _pre_argument_parsing(self):
        try:
            if len(self.app._meta.argv) < self._meta.min_args:
                self.app._meta.argv.append('--help')
            else:
                if (len(self.app._meta.argv) == self._meta.min_args and self.app._meta.argv[-1] == 'help'):
                    self.app._meta.argv[-1] = '--help'
                # help_actions = [action for action in self._parser._actions if action.dest == 'help']
                # help_actions[0](self.app.args, None, None)
        except AttributeError as e:
            pass

    def _post_argument_parsing(self):
        pass

    def _process_parsed_arguments(self):
        if self.app.log and not getattr(self.app._meta, 'log_level', None):
            # hack for application debugging
            if is_true(self.app._meta.debug):
                self.app.config.set(self._meta.config_section, 'level', 'DEBUG')
            else:
                if not self.app.pargs.log_level is None:
                    self.app.config.set(self.app.log._meta.config_section, 'level', string.upper(self.app.pargs.log_level))
            level = self.app.config.get(self.app.log._meta.config_section, 'level')
            level = level.upper()
            if level not in self.app.log.levels:
                level = 'INFO'
            ilevel = getattr(logging, level)

            if self.app.log.backend.level != ilevel:
                self.app.log.set_level(level)
            setattr(self.app._meta, 'log_level', level)

    def render(self, data, **kwargs):

        def ascii_encode(x):
            try:
                return x.encode('ascii')
            except UnicodeEncodeError:
                return x
        def ascii_encode_dict(data):
            ascii = {}
            for k,v in data.items():
                if isinstance(v,dict):
                    ascii[k.encode('ascii')] = ascii_encode_dict(v)
                else:
                    if isinstance(v,list):
                        ascii[k.encode('ascii')] = [map(ascii_encode, s) for s in v]
                    else:
                        if isinstance(v,unicode):
                            ascii[k.encode('ascii')] = ascii_encode(v)
                        else:
                            ascii[k.encode('ascii')] = str(v)
            return ascii

        if isinstance(self.app.output, YamlOutputHandler):
            data = json.loads(json.dumps(data, indent=4, sort_keys=True), object_hook=ascii_encode_dict)
        if not self.app.pargs.output_handler_override and isinstance(self.app.output, TabulateOutputHandler):
            for k,v in {
                'headers': 'headers',
                'table_format': 'tablefmt',
                'string_alignment': 'stralign',
                'numeric_alignment': 'numalign',
                'missing_value': 'missingval',
                'float_format': 'floatfmt',
              }.items():
                if hasattr(self._meta,k):
                    kwargs[v] = getattr(self._meta,k)
        self.app.render(data, **kwargs)


    def config(self):
        return self.app.config

    def pargs(self):
        return self.app.pargs

    def setting(self, item):
        if getattr(self.app.pargs, item, None):
            return getattr(self.app.pargs, item)
        for label in [self._meta.label, self._meta.stacked_on, self.app._meta.label]:
            try:
                section = self.app.config.get_section_dict(label)
                if section.get(item, None):
                    return section.get(item)
            except NoSectionError:
                pass
        return None

    def check_recipe(self, recipe=None):
        if recipe is None:
            if not hasattr(self._meta, 'recipe'):
                msg = '{} does not have a recipe!'.format(self.__class__.__name__)
                self.app.log.fatal(msg)
                raise IaaSError(msg)
            recipe = self._meta.recipe
        msg = ''
        for ingredient in recipe:
            if not getattr(self.app.pargs, ingredient['parameter'], None):
                if not is_true(self.setting('batch')) and self.setting('prompt') and ingredient['ask']:
                    self.app.log.info('Prompt here for {}'.format(ingredient['parameter']))
                    prompt = ArgPrompt()
                    if ingredient.get('options', None):
                        prompt._meta.numbered = True
                        options = ingredient['options']
                        if options.get('values', None):
                            prompt._meta.options = options['values']
                        elif options.get('class', None):
                            columns = getattr(self, '_columns', None)
                            ignored = getattr(self, '_ignored', None)
                            try:
                                if options['module'] not in sys.modules:
                                    try:
                                        __import__(options['module'], globals(), locals(), [], 0)
                                    except ImportError as e:
                                        raise IaaSError('Unable to import class needed to pull list of options for {} ({})'.format(ingredient,e.message))
                                klass = getattr(sys.modules[options['module']], options['class'])
                                instance = klass(self.app.config.get_section_dict(options['section']))
                                print('Obtaining a {} of {} ...'.format(options['method'], options['class']))
                                if options['attribute'].get('filters', None):
                                    filters = getattr(self, '_filters', None)
                                    self._filters=options['attribute']['filters']
                                    self.app.log.info('Filter {}.{}.{}'.format(options['section'], options['class'], options['method']))
                                    values = getattr(instance, options['method'])(_filter=self._weigh, _collection=instance)
                                    if filters:
                                        self._filters=filters
                                else:
                                    values = getattr(instance, options['method'])(detailed=True)

                                if not values.__len__() > 0:
                                     raise FrameworkError('There are no {}!'.format(options['class']))
                                if not isinstance(options['attribute']['show'], list):
                                    options['attribute']['show'] = [options['attribute']['show']]
                                self._columns = options['attribute']['show']
                                selection = self._prune(values)
                                i=0
                                while i < selection.__len__():
                                    for show in options['attribute']['show']:
                                        if not selection[i].get(show, None):
                                            for attr in options['attribute']['alternatives']:
                                                sub =  values[i]._evaluate(attr)
                                                if sub:
                                                    selection[i][show] = '{}:{}'.format(attr,sub)
                                                    break
                                    i += 1

                                prompt._meta.options = [','.join(dict(obj).values()) for obj in selection]
                                self._meta.values = instance
                            except KeyError as e:
                                # raise IaaSError('Ingredient {} options for recipe {}.{} requires an unknown class'.format(ingredient,self.__class__.__name__, self._meta.label))
                            # except ValueError as e:
                                raise IaaSError('Ingredient {} for recipe {}.{} requires a "{}" attribute'.format(ingredient,self.__class__.__name__, self._meta.label, e.message))
                            except FrameworkError as e:
                                self.app.log.fatal("'{}': '{}'".format(e.message,e.msg))
                                print('FATAL error: {}'.format(e.msg))
                                raise e
                            except Exception as e:
                                self.app.log.fatal(e.message)
                                print('FATAL error: {}'.format(e.message))
                                raise e

                            if not columns is None:
                                self._columns = columns
                            if not ignored is None:
                                self._ignored = ignored
                        else:
                            raise IaaSError('Ingredient {} options for recipe {}.{} are not valid'.format(ingredient,self.__class__.__name__, self._meta.label))
                        prompt._meta.text = 'Choose {}:'.format(ingredient['description'])
                    else:
                        prompt._meta.numbered = False
                        prompt._meta.options = None
                        prompt._meta.text = 'Enter {}: '.format(ingredient['description'])
                    # prompt._meta.selection_text = 'Enter the {}:'.format(ingredient['parameter'])
                    try:
                        answer = prompt.prompt()
                        if ingredient.get('options', None):
                            options = ingredient['options']
                            if options.get('values', None):
                                setattr(self.app.pargs, ingredient['parameter'], prompt.input)
                            elif options.get('class', None):
                                index = prompt._meta.options.index(answer)
                                values = [self._meta.values[index]]

                                columns = getattr(self, '_columns', None)
                                ignored = getattr(self, '_ignored', None)
                                self._columns = [options['attribute']['use']]
                                selection = self._prune(values)
                                if not columns is None:
                                    self._columns = columns
                                if not ignored is None:
                                    self._ignored = ignored

                                setattr(self.app.pargs, ingredient['parameter'], '{}:{}'.format(options['attribute']['use'], selection[0].get(options['attribute']['use'], None)))
                                print('{} value will be "{}"'.format(ingredient['parameter'], getattr(self.app.pargs, ingredient['parameter'])))

                                # if string.index(options['attribute']['use'], '/') < 0:
                                #     pass
                                # else:
                                #     setattr(self.app.pargs, ingredient['parameter'], selection[0].get(options['attribute']['use'], None))
                        else:
                            setattr(self.app.pargs, ingredient['parameter'], prompt.input)
                    except FrameworkError as e:
                        self.app.log.fatal("'{}': '{}'".format(e.message,e.msg))
                        print('FATAL error: {}'.format(e.msg))
                        raise e
                if not getattr(self.app.pargs, ingredient['parameter'], None):
                    msg += "'{}' is required. ({})\n".format(ingredient['parameter'],ingredient['description'])
        if msg.__len__() > 0:
            raise IaaSError(msg)

    def _filter(self, resp):
        if self.filters():
            nrsp = []
            for obj in resp:
                if self._weigh(obj, resp):
                    nrsp.append(obj)
            resp = nrsp
        return resp

    def _prune(self, resp, arg=None):
        nrsp = []
        if self.columns(arg):
            for obj in resp:
                nobj=OrderedDict()
                for flt in self.columns(arg):
                    part = obj._evaluate(flt)
                    if not part is None:
                        nobj[flt] = part
                if len(nobj) > 0:
                    nrsp.append(nobj)
            resp = nrsp
        if getattr(self, '_ignored', None):
            for obj in resp:
                nobj=OrderedDict()
                for col in obj.keys():
                    if not col in self._ignored:
                        nobj[col] = obj[col]
                nrsp.append(nobj)
            resp = nrsp
        return resp

    def filters(self):
        if not hasattr(self,'_filters'):
            if not self.app.pargs.filters:
                self._filters = None
            else:
                kv = lambda x: re.split(':\s*', x)
                filters = re.split(',\s*', self.app.pargs.filters)
                self._filters = map(kv, filters)
        return self._filters

    def columns(self, arg=None):
        if arg is None:
            arg = 'columns'
        if not hasattr(self, '_'+arg):
            if not getattr(self.app.pargs, arg):
                setattr(self, '_'+arg, None)
                self._ignored = None
            else:
                setattr(self, '_'+arg, None)
                self._ignored = None
                for col in re.split(',\s*', getattr(self.app.pargs, arg)):
                    if col.startswith('!'):
                        self._ignored = self._ignored or []
                        self._ignored.append(string.lstrip(col, '!'))
                    else:
                        setattr(self, '_'+arg, getattr(self, '_'+arg) or [])
                        getattr(self, '_'+arg).append(col)
        return getattr(self, '_'+arg)

    def _weigh(self, obj, collection=None):
        return obj