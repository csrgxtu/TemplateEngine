#!/usr/bin/env python
# coding=utf-8
from TemplateEngine import Template

PAGE_HTML = """
<html>
  Hello, {{ username }}!
  <ul>
    {% for job in job_list %}
      <li>{{ job }}</li>
    {% end %}
  </ul>
</html>
"""

t = Template(PAGE_HTML)
print type(t.code), t.code
print type(t.code), t.compiled
print t.generate(username='archer', job_list=['engineer', 'QA', 'PM'])
