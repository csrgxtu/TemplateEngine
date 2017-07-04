from TemplateEngineHelper import *


class Template(object):
    def __init__(self, template_string):
        """ init and parsing the template into python code """
        self.code = parse_template(template_string)
        self.compiled = compile(self.code, '<string>', 'exec')

    def generate(self, **kwargs):
        """ redenering to html """
        namespace = {}
        namespace.update(kwargs)
        exec self.compiled in namespace
        execute = namespace["_execute"]
        return execute()
