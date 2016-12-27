import collections

from more_itertools import peekable


class Tokens:
    target = 'target'
    command = 'command'
    expression = 'expression'


def tokenizer(fd):
    it = enumerate(fd)

    def glue_multiline(line):
        lines = []
        strip_line = line.strip()
        while strip_line[-1] == '\\':
            lines.append(strip_line.rstrip('\\').strip())
            line_num, line = next(it)
            strip_line = line.strip()
        lines.append(strip_line.rstrip('\\').strip())
        return ' '.join(lines)

    for line_num, line in it:
        strip_line = line.strip()
        # skip empty lines
        if not strip_line:
            continue
        # skip comments
        if strip_line[0] == '#':
            continue
        elif line[0] == '\t':
            yield (Tokens.command, glue_multiline(line))
        elif ':' in line and '=' not in line:
            yield (Tokens.target, glue_multiline(line))
        else:
            yield (Tokens.expression, line.strip())


def parse(fd):
    ast = []
    it = peekable(tokenizer(fd))

    def parse_target(token):
        line = token[1]
        target, deps = line.split(':', 1)
        raw_deps = deps.strip().split('|', 1)
        deps = raw_deps[0]
        order_deps = raw_deps[1] if raw_deps[1:] else ''
        body = parse_body()
        ast.append((
            token[0],
            {
                'target': target.strip(),
                'deps': [
                    sorted(deps.split()) if deps else [],
                    list(order_deps.split()) if order_deps else []
                ],
                'body': body
            })
        )

    def parse_body():
        body = []
        try:
            while it.peek()[0] != Tokens.target:
                token = next(it)
                if token[0] == Tokens.command:
                    body.append((token[0], token[1]))
                else:
                    body.append(token)
        except StopIteration:
            pass
        return body

    for token in it:
        if token[0] == Tokens.target:
            parse_target(token)
        else:
            # expression
            ast.append(token)

    return ast


def get_dependencies_influences(ast):
    dependencies = {}
    influences = collections.defaultdict(set)
    order_only = set()

    for item_t, item in ast:
        if item_t != Tokens.target:
            continue
        target = item['target']
        deps, order_deps = item['deps']

        if target not in ('.PHONY',):
            dependencies[target] = [deps, order_deps]

        # influences
        influences[target]
        for k in deps:
            influences[k].add(target)
        for k in order_deps:
            influences[k]
        order_only.update(order_deps)
    return (dependencies, influences, order_only)
