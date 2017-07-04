import cStringIO


def _parse(reader, in_block=None):
    body = _ChunkList([])
    while True:
        # Find next template directive
        curly = 0
        while True:
            curly = reader.find("{", curly)
            if curly == -1 or curly + 1 == reader.remaining():
                # EOF
                if in_block:
                    raise ParseError("Missing {%% end %%} block for %s" %
                                     in_block)
                body.chunks.append(_Text(reader.consume()))
                return body
            # If the first curly brace is not the start of a special token,
            # start searching from the character after it
            if reader[curly + 1] not in ("{", "%"):
                curly += 1
                continue
            # When there are more than 2 curlies in a row, use the
            # innermost ones.  This is useful when generating languages
            # like latex where curlies are also meaningful
            if (curly + 2 < reader.remaining() and
                reader[curly + 1] == '{' and reader[curly + 2] == '{'):
                curly += 1
                continue
            break

        # Append any text before the special token
        if curly > 0:
            body.chunks.append(_Text(reader.consume(curly)))

        start_brace = reader.consume(2)

        # Expression
        if start_brace == "{{":
            end = reader.find("}}")
            if end == -1 or reader.find("\n", 0, end) != -1:
                raise ParseError("Missing end expression }}")
            contents = reader.consume(end).strip()
            reader.consume(2)
            if not contents:
                raise ParseError("Empty expression")
            body.chunks.append(_Expression(contents))
            continue

        # Block
        assert start_brace == "{%", start_brace
        end = reader.find("%}")
        if end == -1 or reader.find("\n", 0, end) != -1:
            raise ParseError("Missing end block %}")
        contents = reader.consume(end).strip()
        reader.consume(2)
        if not contents:
            raise ParseError("Empty block tag ({% %})")
        operator, space, suffix = contents.partition(" ")
        # End tag
        if operator == "end":
            if not in_block:
                raise ParseError("Extra {% end %} block")
            return body
        elif operator in ("try", "if", "for", "while"):
            # parse inner body recursively
            block_body = _parse(reader, operator)
            block = _ControlBlock(contents, block_body)
            body.chunks.append(block)
            continue
        else:
            raise ParseError("unknown operator: %r" % operator)


def parse_template(template_string):
    reader = _TemplateReader(template_string)
    file_node = _File(_parse(reader))
    writer = _CodeWriter()
    file_node.generate(writer)
    return str(writer)


class _TemplateReader(object):
    def __init__(self, text):
        self.text = text
        self.pos = 0

    def find(self, needle, start=0, end=None):
        pos = self.pos
        start += pos
        if end is None:
            index = self.text.find(needle, start)
        else:
            end += pos
            index = self.text.find(needle, start, end)
        if index != -1:
            index -= pos
        return index

    def consume(self, count=None):
        if count is None:
            count = len(self.text) - self.pos
        newpos = self.pos + count
        s = self.text[self.pos:newpos]
        self.pos = newpos
        return s

    def remaining(self):
        return len(self.text) - self.pos

    def __len__(self):
        return self.remaining()

    def __getitem__(self, key):
        if key < 0:
            return self.text[key]
        else:
            return self.text[self.pos + key]

    def __str__(self):
        return self.text[self.pos:]


class _CodeWriter(object):
    def __init__(self):
        self.buffer = cStringIO.StringIO()
        self._indent = 0

    def indent(self):
        return self

    def indent_size(self):
        return self._indent

    def __enter__(self):
        self._indent += 1
        return self

    def __exit__(self, *args):
        self._indent -= 1

    def write_line(self, line, indent=None):
        if indent == None:
            indent = self._indent
        for i in xrange(indent):
            self.buffer.write("    ")
        print >> self.buffer, line

    def __str__(self):
        return self.buffer.getvalue()


class _Node(object):
    def generate(self, writer):
        raise NotImplementedError()


class _ChunkList(_Node):
    def __init__(self, chunks):
        self.chunks = chunks

    def generate(self, writer):
        for chunk in self.chunks:
            chunk.generate(writer)


class _File(_Node):
    def __init__(self, body):
        self.body = body

    def generate(self, writer):
        writer.write_line("def _execute():")
        with writer.indent():
            writer.write_line("_buffer = []")
            self.body.generate(writer)
            writer.write_line("return ''.join(_buffer)")



class _Expression(_Node):
    def __init__(self, expression):
        self.expression = expression

    def generate(self, writer):
        writer.write_line("_tmp = %s" % self.expression)
        writer.write_line("_buffer.append(str(_tmp))")


class _Text(_Node):
    def __init__(self, value):
        self.value = value

    def generate(self, writer):
        value = self.value
        if value:
            writer.write_line('_buffer.append(%r)' % value)


class _ControlBlock(_Node):
    def __init__(self, statement, body=None):
        self.statement = statement
        self.body = body

    def generate(self, writer):
        writer.write_line("%s:" % self.statement)
        with writer.indent():
            self.body.generate(writer)
