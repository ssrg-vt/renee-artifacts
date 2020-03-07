#! /usr/bin/env python3

# Some general-purpose functions

import re
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)

file_handler = logging.FileHandler('debug.log', mode='w')
file_handler.setLevel(level=logging.DEBUG)
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


u_name, u_annotation = range(2)

t_tuple, t_type, t_function, t_other = range(4)

argSep = '->'
tupSep = ','
fieldSep = ';'

delimits = {'(': ')', '[': ']', '{': '}'}

importPat = re.compile('(?<=IMPORTING )[a-z][A-Za-z0-9_@]+')
pvsDefPat = re.compile('^[a-z]+[a-zA-Z0-9_]*(\[[a-zA-Z0-9_ :]+\])?[ ]*(?=\()')
constPat = re.compile('^[a-z]+[a-zA-Z0-9_]*(\[[a-zA-Z0-9_ :]+\])?[ ]*(?=:)')
functionAppPat = re.compile('^[a-z]+[a-zA-Z0-9_]*(\[[a-zA-Z0-9_ :]+\])?(?=\()')

enumPat = re.compile('^[a-z]+[a-zA-Z0-9_ ]*{[a-zA-Z0-9_ ,]*}')

openModPat = re.compile('(?<=open )[A-Z][A-Za-z0-9_]+')
includeModPat = re.compile('(?<=include )[A-Z][A-Za-z0-9_]+')
callModPat = re.compile('(?<= )[A-Z][A-Za-z0-9_]+\.')

idPat = re.compile('[a-z]+[a-zA-Z0-9_\']*')
numVarPat = re.compile('[A-Z]')
letPat = re.compile('(?<=LET )[a-z(]+[a-zA-Z0-9_,\' ()]*(?=\=)')
letExpPat = re.compile('(?<=LET )[a-z(]+[a-zA-Z0-9_,\' ()]*=[a-zA-Z0-9_,\' ()]*(?=IN)')

varPat = re.compile(':[ ]*VAR(?=\W)')

caseCondPat = re.compile('(?<=CASES )[ ]*[a-z(]+[a-zA-Z0-9_,\' ()]*(?=OF)')
casePat = re.compile('(?<=CASES )[ ]*[a-z(]+[a-zA-Z0-9_,\' ()\n]* OF[a-zA-Z0-9_,:\'\s\n ()`]+(?=ENDCASES)')


# input: [1, 2, 3]  [1, 2, 4]
# output: [3]
def diff_list(l1, l2):
    return list(set(l1) - set(l2))


def extract_content(expr: str, left_delimit='(') -> str:
    right_delimit = delimits[left_delimit]
    return expr.split(left_delimit, 1)[1].rsplit(right_delimit, 1)[0].strip()


def subtract_list(l1, l2):
    l3 = [elem for elem in l1 if elem not in l2]
    return l3


def flatten(l):
    return [a for sl in l for a in sl]


def has_dup(l):
    return len(l) != len(set(l))


def split_fun_app(app)->Tuple[str, str]:
    args = app.split('(', 1)
    name = args[0].strip()
    if len(args) == 1:
        return name, ''
    else:
        return name, args[1].rsplit(')', 1)[0].strip()


def split_case_line(line: str)->List[str]:
    case_line = line.strip()
    if case_line.startswith('ELSE '):
        return list(map(lambda x: x.strip(), case_line.split(' ', 1)))
    else:
        return list(map(lambda x: x.strip(), case_line.split(':', 1)))


# Extract the contents inside symmetric parentheses inside the string
# input: '(123) 45 (678(42) 235) 56', '(', ')'
# output: ['(123)', '(678(42) 235)']
def extract_bk_content(args:str, left = '(', right = ')')->List[str]:
    result = []
    to_continue = False
    curr = ''
    bk_count = 0
    for c in args:
        if c == left:
            curr += left
            bk_count += 1
            to_continue = True
        elif c == right:
            bk_count -= 1
            curr += right
            if bk_count == 0:
                to_continue = False
                curr = curr.strip()
                if curr != '':
                    result.append(curr)
                curr = ''
                bk_count = 0
        else:
            if to_continue:
                curr += c
    return result


# input: '(123) 45 (678(42) 235) 56', '(', ')', ' '
# output: ['(123)', '45', '(678(42) 235)', '56']
def split_sep_bk(data:str, sep:str, left = '(', right = ')')->List[str]:
    sep_first = sep[0]
    sep_len = len(sep)
    result = []
    curr = ''
    to_continue = False
    idx = 0
    length = len(data)
    bk_count = 0
    while idx < length:
        c = data[idx]
        if c == left:
            bk_count += 1
            curr += c
            to_continue = True
            idx += 1
        elif c == right:
            curr += c
            bk_count -= 1
            if bk_count == 0:
                to_continue = False
            idx += 1
        elif c == sep_first and len(data[idx:]) >= sep_len and data[idx: idx + sep_len] == sep:
            if to_continue:
                curr += c
                idx += 1
            else:
                curr = curr.strip()
                if curr != '':
                    result.append(curr)
                curr = ''
                idx += sep_len
        else:
            curr += c
            idx += 1
    result.append(curr.strip())
    return result


# input: '(123) 45 (678(42) 235) 56 [78 9]', ['(', '['], [')', ']'], ' '
# output: ['(123)', '45', '(678(42) 235)', '56', '[78 9]']
def split_sep_bks(data, sep, left = ['(', '[', '{'], right = [')', ']', '}']):
    sep_first = sep[0]
    sep_len = len(sep)
    result = []
    curr = ''
    to_continue = False
    idx = 0
    length = len(data)
    bk_len = len(left)
    bk_count = [0] * bk_len
    while idx < length:
        c = data[idx]
        if c in left:
            c_idx = left.index(c)
            bk_count[c_idx] += 1
            curr += c
            to_continue = True
            idx += 1
        elif c in right:
            c_idx = right.index(c)
            curr += c
            bk_count[c_idx] -= 1
            if all(elem == 0 for elem in bk_count):
                to_continue = False
            idx += 1
        elif c == sep_first and len(data[idx:]) >= sep_len and data[idx: idx + sep_len] == sep:
            if to_continue:
                curr += c
                idx += 1
            else:
                curr = curr.strip()
                if curr != '':
                    result.append(curr)
                curr = ''
                idx += sep_len
        else:
            curr += c
            idx += 1
    result.append(curr.strip())
    return result


def split_sep(data, sep):
    return split_sep_bk(data, sep, '[', ']')


# Rewrite the PVS argument types to a new format
def parse_args(var_dict: Dict[str, str], args: str)->Tuple[str, str]:
    arg_name = ''
    arg_type = ''
    v_args = split_sep_bks(args, ',')
    for v in v_args:
        v = v.strip()
        if ':' in v:
            v_split = v.split(':', 1)
            arg_name = v_split[0]
            a_type = v_split[1]
            # Dependent type
            if '{' in a_type:
                arg_type += v.split('{')[1].split('|')[0].split(':')[1].strip()
            else:
                if v.startswith('('):
                    arg_type += v.split(":")[1].rsplit(')', 1)[0].strip()
                else:
                    arg_type += v.split(":")[1].strip()
        else:
            arg_name = v
            if v in var_dict.keys():
                arg_type += var_dict[v].strip()
            else:
                arg_type += v.strip()
        arg_type += tupSep
    arg_type = arg_type.rsplit(tupSep, 1)[0].strip()
    argList = split_sep(arg_type, tupSep)
    if len(argList) > 1:
        arg_type = '[' + arg_type + ']'
    return arg_name.strip(), arg_type


# Extract the arguments of the first element from a tuple represented as a string
# input: '(cons(x, xs), cons(y, ys))'
# output: ['x', 'xs']
def extract_tuple_first_arg(t: str)->List[str]:
    result = []
    first = ''
    if t:
        if t.startswith('('):
            ts = split_arg_list(t)
            first = ts[0].strip()
        else:
            first = t.strip()
    if first.endswith(')'):
        args = extract_content(first)
        result = split_sep_bks(args, ',')
    return result


# Remove the first element from a tuple represented as a string
# input: '(cons(x, xs), cons(y, ys))'
# output: 'cons(y, ys)'
def remove_tuple_first_element(t: str)->str:
    result = ''
    if t.startswith('('):
        ts = split_sep_bks(extract_content(t), ',')
        result = '(' + ','.join(ts[1:]) + ')'
    return result


def generate_new_variable(tup_idx: int, arg_idx: int)->str:
    tup_str = 'v_' + chr(ord('a') + tup_idx)
    result = tup_str + ('' if arg_idx == 0 else str(arg_idx))
    return result


def replace_expr_variable(expr: str, ov: str, nv: str)->str:
    reg = '(?<=\W)' + ov + '(?=\W)'
    result = re.sub(reg, nv, expr)
    return result


# Split a arguments representation
# '(T,list[T])'
# ['T', 'list[T]']
def split_arg_list(expr: str, delimit='(')->List[str]:
    if expr.startswith(delimit):
        expr = extract_content(expr, delimit)
    return split_sep_bks(expr, ',')


# Construct a new pattern expression using the give constructor name and arguments list
def construct_field_expression(tup_idx: int, name: str, arg_types: str) -> Tuple[str, List[str]]:
    result = name
    arg_list = []
    if len(arg_types) > 0:
        result += '('
        if arg_types.startswith('['):
            args = split_arg_list(arg_types, '[')
            for i in range(len(args)):
                t = generate_new_variable(tup_idx, i)
                result += t + ', '
                arg_list.append(t)
            result = result.rsplit(',', 1)[0]
        else:
            t = generate_new_variable(tup_idx, 0)
            result += t
            arg_list.append(t)
        result += ')'
    return result, arg_list


# Indent multiple lines
def block_indent(expr: str)->str:
    return re.sub('\n', '\n  ', expr)


# Replace multiple variables
def replace_multiple(expr, os, ns):
    result = expr
    n = len(os)
    for i in range(n):
        o = os[i]
        n = ns[i]
        result = re.sub(o, n, result)
    return result


def get_type_variables(line: str)->List[str]:
    if '[' not in line: return []
    annotation = extract_content(line, '[')
    tv_annots = annotation.split(',')
    type_variables = []
    for tv in tv_annots:
        type_variables.append(tv.split(':', 1)[0].strip())
    return type_variables



def parseFunctionType(varDict, args):
    argType = ''
    vArgs = split_sep_bks(args, ',')
    # vArgs = '{', '}', ',')
    for v in vArgs:
        v = v.strip()
        if ':' in v:
            fType = v.split(':')[1]
            if '{' in fType:
                argType += v.split('{')[1].split('|')[0].split(':')[1]
                argType += tupSep
            else:
                if v.startswith('('):
                    argType += v.split(":")[1].rsplit(')', 1)[0].strip()
                else:
                    argType += v.split(":")[1].strip()
                argType += tupSep
        else:
            if v in varDict.keys():
                argType += varDict[v]
            else:
                argType += v
            argType += tupSep
    argType = argType.rsplit(tupSep, 1)[0]
    argList = split_sep_bk(argType, tupSep, '[', ']')
    if len(argList) > 1:
        argType = '[' + argType + ']'
    return argType
    

def parseReturnType(arg):
    result = arg
    if '->' in arg and arg.startswith('[') and arg.endswith(']'):
        block = arg.strip().split('[', 1)[1].rsplit(']', 1)[0].strip()
        args = split_sep_bk(block, '->', '[', ']')
        if len(args) == 1:
            result = '[' + block + ']'
        elif len(args) == 2:
            result = args[0].strip() + '->' + parseReturnType(args[1].strip())
    return result

def removeLastExtraID(str):
    args = str[::-1]
    id_count = 0
    for c in args:
        if idPat.search(c):
            id_count += 1
        else:
            break
    result = args[id_count:][::-1]
    return result

