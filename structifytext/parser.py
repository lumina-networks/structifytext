import re
import distutils

INT = 0
DOUBLE = 1
BOOLEAN = 2
STRING = 3


def parse_struct(lines, struct):
    parsed = {}
    for k,v in struct.iteritems():
        if isinstance(v, list) and not isinstance(v, basestring) and len(v) > 0:
            if isinstance(v[0], dict):
                chunks = chunk_lines(lines, v[0])
                parsed[k] = [parse_struct(chunk, v[0]) for chunk in chunks]
            else:
                parsed[k] = parse_regex(lines, k, v[0], return_list=True)
        elif isinstance(v, dict):
            parsed[k] = parse_struct(lines, v)
        else:
            parsed[k] = parse_regex(lines, k, v)
    return parsed


def chunk_lines(lines, struct):
    if 'id' not in struct:
        raise KeyError("'id' key is required in a list containing a dictionary")
    id_regex = _compile_regex('id', struct['id'])[0]
    matched_ids = filter(id_regex.search, lines)
    match_indexes = sorted(list(set(map(lambda x: lines.index(x), matched_ids))))

    chunks = []
    block_end = match_indexes[-1]
    for idx, val in enumerate(match_indexes):
        if idx+1 >= len(match_indexes):
            chunks.append(lines[val::])
        elif val <= block_end:
            if match_indexes[idx + 1] >= block_end:
                chunks.append(lines[val:block_end])
            else:
                chunks.append(lines[val:match_indexes[idx + 1]])
    return chunks


def parse_regex(lines, key, regex_tuple, return_list=False):
    regex, type = _compile_regex(key, regex_tuple)
    if regex.groups < 1:
        raise ValueError("The regular expression at key '{}' must contain a regex group (...)".format(key))
    elif regex.groups > 1:
        raise UserWarning("The regular expression at key '{}' should contain only one regex group".format(key))
    values = [m.group(1) for l in lines for m in [regex.search(l)] if m]
    if len(values) > 0 and (not return_list or len(values) < 2):
        return cast_values(values, type)[0]
    return cast_values(values, type)


def _compile_regex(key, regex_tuple):
    if not isinstance(regex_tuple, tuple):
        raise TypeError("The value at key '{}' must be a tuple, containing the regular expression"
                        " and the JSON type".format(key))
    if len(regex_tuple) < 2:
        raise ValueError("The tuple at key '{}' must contain a regular expression"
                         " and the JSON type".format(key))
    regex = regex_tuple[0]
    if not isinstance(regex, basestring):
        raise TypeError("The first value in the tuple must be a regular expression string".format(key))
    return re.compile(regex), regex_tuple[1]


def cast_values(values, type):
    if type == INT:
        return map(int, values)
    if type == DOUBLE:
        return map(float, values)
    if type == BOOLEAN:
        return map(bool, map(distutils.util.strtobool, values))
    return values
