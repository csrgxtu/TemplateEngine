#!/usr/bin/env python
# coding=utf-8
from templite import Templite

PAGE_HTML = """
<html>
  Hello, {{ username }}!
  <ul>
    {% for job in job_list %}
      <li>{{ job }}</li>
    {% endfor %}
  </ul>
</html>
"""

data = {
  'username': 'archer',
  'job_list': ['engineer', 'qa', 'pm']
}
t = Templite(PAGE_HTML)
print t.render(data)
