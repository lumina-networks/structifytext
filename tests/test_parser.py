import os
import ast
import pytest
import logging
from structifytext import parser
from cStringIO import StringIO

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture(scope='module')
def mock_struct(request):
    return {
        'tables': [
            {
                'id': ('\[TABLE (\d{1,2})\]', parser.INT),
                'flows': [
                    {
                        'id': ('\[FLOW_ID(\d+)\]', parser.INT),
                        'timestamp': ('Timestamp\s+=\s+(.+)', parser.STRING)
                    }
                ]
            }
        ]
    }


@pytest.fixture(scope='module')
def mock_group_struct(request):
    return {
        'groups': [
            {
                'id': ('Group id:\s+(\d+)', parser.INT),
                'ref_count': ('Reference count:\s+(\d+)', parser.INT),
                'packet_count': ('Packet count:\s+(\d+)', parser.INT),
                'byte_count': ('Byte count:\s+(\d+)', parser.INT),
                'bucket': [
                    {
                        'id': ('Bucket\s+(\d+)', parser.INT),
                        'packet_count': ('Packet count:\s+(\d+)', parser.INT),
                        'byte_count': ('Byte count:\s+(\d+)', parser.INT),
                    }
                ]
            }
        ]
    }


def read(filename):
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(output_file, 'r') as fin:
        return fin.read()


def test_simple_struct():
    struct = { 'message': ('(.*)', parser.STRING) }
    lines = ["Hello World"]
    expected_output = { 'message': "Hello World" }
    parsed = parser.parse_struct(lines, struct)
    assert parsed == expected_output


def test_simple_list():
    struct = { 'count': [('(\d)', parser.STRING)] }
    lines = ["The count says: 1", "The count says: 2", "The count says: 3",
             "The count says: 4", "The count says: 5"]
    expected_output = { 'count': ['1','2','3','4','5'] }
    parsed = parser.parse_struct(lines, struct)
    assert parsed == expected_output


def test_can_parse_to_int():
    struct = { 'count': [('(\d)', parser.INT)] }
    lines = ["The count says: 1", "The count says: 2", "The count says: 3",
             "The count says: 4", "The count says: 5"]
    expected_output = { 'count': [1,2,3,4,5] }
    parsed = parser.parse_struct(lines, struct)
    assert parsed == expected_output


def test_can_parse_to_double():
    struct = { 'count': [('([-+]?[0-9]*\.?[0-9]+)', parser.DOUBLE)] }
    lines = ["The count says: 1.4", "The count says: 2.7", "The count says: 3",
             "The count says: -4.1", "The count says: -5"]
    expected_output = { 'count': [1.4, 2.7, 3.0, -4.1, -5.0] }
    parsed = parser.parse_struct(lines, struct)
    assert parsed == expected_output


def test_can_parse_to_boolean():
    struct = { 'true_or_false': [('([Tt]rue|[Ff]alse)', parser.BOOLEAN)] }
    lines = ["I choose true", "I choose false", "I choose True", "I choose False"]
    expected_output = { 'true_or_false': [True, False, True, False] }
    parsed = parser.parse_struct(lines, struct)
    assert parsed == expected_output


def test_flows(mock_struct):
    lines = StringIO(read('./flow_output.txt')).readlines()
    expected_output = ast.literal_eval(read('./flow_output_parsed.txt'))
    parsed = parser.parse_struct(lines, mock_struct)
    assert parsed == expected_output


def test_groups(mock_group_struct):
    lines = StringIO(read('./group_output.txt')).readlines()
    expected_output = ast.literal_eval(read('./group_output_parsed.txt'))
    parsed = parser.parse_struct(lines, mock_group_struct)
    assert parsed == expected_output


def test_value_not_tuple_raises_exception():
    struct = {'message': '(.*)'}
    lines = ["Hello World"]
    with pytest.raises(TypeError):
        parser.parse_struct(lines, struct)


def test_short_tuple_raises_exception():
    struct = {'message': ('(.*)',)}
    lines = ["Hello World"]
    with pytest.raises(ValueError):
        parser.parse_struct(lines, struct)


def test_not_regex_string_raises_exception():
    struct = {'message': (123, parser.STRING)}
    lines = ["Hello World"]
    with pytest.raises(TypeError):
        parser.parse_struct(lines, struct)


def test_value_without_group_raises_exception():
    struct = {'message': ('ab', parser.STRING)}
    lines = ["Hello World"]
    with pytest.raises(ValueError):
        parser.parse_struct(lines, struct)


def test_value_with_two_groups_raises_warning():
    struct = {'message': ('(.*)\S+(.*)', parser.STRING)}
    lines = ["Hello World"]
    with pytest.raises(UserWarning):
        parser.parse_struct(lines, struct)


def test_list_with_dict_no_id_raises_exception():
    struct = {'letter': [{'to': ('Dear\s+(\w+)', parser.STRING), 'from': ('Regards,\s+(\w+)', parser.STRING)}]}
    letter = "Dear Einstein,\r\n"
    letter += "I am become Death, the destroyer of worlds.\r\n"
    letter += "And it's all your fault!\r\n"
    letter += "Regards, Oppenheimer\r\n"
    lines = StringIO(letter).readlines()
    logger.debug(lines)
    with pytest.raises(KeyError):
        parser.parse_struct(lines, struct)
