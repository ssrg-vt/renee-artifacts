#! /usr/bin/env python
# -*- coding: utf-8 -*-
import json
from io import FileIO
from os import listdir
from os.path import isfile, join
import os
import re
import copy
import helper
import util
import argparse

S_STATE, S_DATATYPE, S_TYPE, S_CONST, S_INSTANCE = range(5)

T_TestDir, T_ProveitPath, T_LibList, T_MLSrcFile, T_ExtCmd, T_ExtML, T_Function, T_Const, T_Type, T_Instance, T_Pattern, T_Prefix = range(12)

json_path = os.path.join(helper.dir_path, 'tag.json')

util.logger.debug(json_path)
with open(json_path) as json_file:
    data = json.load(json_file)
    tags = data['tags']
    pvs_lib_list = data[tags[T_LibList]] if tags[T_LibList] in data.keys() else []
    
def composeStr(s):
    newS = '(?<=\n)[ ]*let (rec )?' + s + '( |:)'
    return newS


def setTestDir():
    testDir = os.path.join(helper.udir_path, "Test_Cases")
    if not os.path.exists(testDir):
        os.makedirs(testDir)
    util.logger.debug('Test Dir:')
    util.logger.debug(testDir)
    data[tags[T_TestDir]] = testDir

def setPVSHome():
    pvs_home = os.environ.get('PVS_HOME')
    if pvs_home is None:
        sys.exit("The environment variable PVS_HOME has not been set")
    util.logger.debug('PVS HOME:')
    util.logger.debug(pvs_home)
    data[tags[T_ProveitPath]]=os.path.join(pvs_home, "proveit")

def setup_pvs():
    pvs_home = os.environ.get('PVS_HOME')
    cmd = 'cp -R ./pvs-patches ' + pvs_home + '; '
    cmd += 'cp ./Test_Cases/pvs-strategies ' + data[tags[T_TestDir]]
    helper.execute_command(cmd)

def verifySrcFile(srcFile):
    if not srcFile.endswith(".ml"):
        raise NameError('Not a .ml source file')
    if not os.path.exists(srcFile):
        raise ValueError('The .ml source file does not exist')

def verifyPVSLib(pvsLib):
    pvs_lib_path = data[pvsLib]["library_path"]
    if os.path.exists(pvs_lib_path):
        return True
    else:
        raise ValueError('The pvs library ' + pvsLib + 'does not exist')

def constr_externals(name):
    lib_data = data[name]
    external_mls = lib_data[tags[T_ExtML]]
    external_cmds = lib_data[tags[T_ExtCmd]]
    for index, ext_ml in enumerate(external_mls):
        if not ext_ml.startswith('#mod_use'):
            ext_ml = helper.preprocess_path(ext_ml)
            lib_data[tags[T_ExtML]][index] = '#mod_use \"' + ext_ml + '\";;'
    for index, ext_cmd in enumerate(external_cmds):
        if not ext_cmd.startswith('#load') and not ext_cmd.startswith('#require'):
            if '.cma' in ext_cmd:
                lib_data[tags[T_ExtCmd]][index] = '#load \"' + ext_cmd + '\";;'
            elif '.' not in ext_cmd:
                lib_data[tags[T_ExtCmd]][index] = '#require \"' + ext_cmd + '\";;'
    lib_data[tags[T_ExtCmd]] = external_cmds
    lib_data[tags[T_ExtML]] = external_mls

def update_library_data(pvs_lib_name):
    lib_data = data[pvs_lib_name]
    verifyPVSLib(pvs_lib_name)
    pvs_lib_path = helper.preprocess_path(lib_data["library_path"])
    lib_data["library_path"] = pvs_lib_path
    mlSrcFiles = lib_data[tags[T_MLSrcFile]]
    for index, itemName in enumerate(mlSrcFiles):
        if not '.ml' in itemName:
            lib_data[tags[T_MLSrcFile]].clear()
            itemName = helper.preprocess_path(itemName)
            fileNames = [f for f in listdir(itemName) if isfile(join(itemName, f)) and f.endswith('.ml')]
            for f in fileNames:
                ml_src_file = helper.preprocess_path(join(itemName, f))
                verifySrcFile(ml_src_file)
                lib_data[tags[T_MLSrcFile]].append(ml_src_file)
        else:
            ml_src_file = helper.preprocess_path(itemName)
            lib_data[tags[T_MLSrcFile]][index] = ml_src_file
    constr_externals(pvs_lib_name)
        

def parseFiles(module_list, srcData, libName, specialString):
    functionItems = {}
    constItems = {}
    typeItems = {}
    instanceItems = {}
    patternItems = {}
    lib_data = data[libName]
    pathName = lib_data["library_path"]
    pvsFiles = [f for f in os.listdir(pathName) if os.path.isfile(os.path.join(pathName, f)) and f.endswith('.pvs') and not f.endswith('_adt.pvs')]
    for fileName in pvsFiles:
        with open(os.path.join(pathName, fileName)) as pvsFile:
            theoryName = fileName.split('.')[0]
            libData = pvsFile.readlines()
            varDict = {}
            constDict = {}
            tyName = ''
            tyContent = ''
            decType = ''
            state = S_STATE
            toContinue = False
            for line in libData:
                if line.startswith('%') or 'LEMMA' in line:
                    continue
                elif state == S_STATE:
                    if ':VAR' in line.replace(' ', ''):
                        decs = line.split(':')
                        variables = decs[0].replace(' ', '').split(',')
                        vtype = decs[1].split("VAR")[1]
                        for v in variables:
                            varDict[v] = vtype.replace(' ', '')
                    elif 'DATATYPE' in line:
                        decType = ''
                        tyName = util.split_sep_bk(line, ':', '[', ']')[0].split('[')[0]
                        tyContent = ''
                        state = S_DATATYPE
                    elif ':TYPE=' in line.replace(' ', '') or ':TYPE+=' in line.replace(' ', '') :
                        decType = line
                        tyName = util.split_sep_bk(line, ':', '[', ']')[0].split('[')[0]
                        state = S_TYPE
                    elif ':TYPE\n' in line.replace(' ', ''):
                        tyName = util.split_sep_bk(line, ':', '[', ']')[0].split('[')[0]
                        typeItems[tyName] = ("type", '')
                    elif ': THEORY' in line and ']' in line:
                        tvblocks = util.split_sep_bk(line, ':', '[', ']')[0].split('[')[1].split(']')[0].split(':')
                        for i in range(len(tvblocks[:-1])):
                            if i == 0:
                                tvNames = tvblocks[i].split(',')
                            else:
                                tvNames = tvblocks[i].split(',')[1:]
                            tvp = tvblocks[i + 1].strip().split(',', 1)[0]
                            for tv in tvNames:
                                tv = tv.strip()
                                constDict[tv] = tvp
                    elif util.constPat.search(line) and '->' not in line and 'THEORY' not in line and 'LAMBDA' not in line and not line.endswith(',\n') and '(#' not in line:
                        if '=' not in line:
                            decs = line.split(':')
                            cName = decs[0].replace(" ","")
                            cType = decs[1].strip().replace(" ","")
                            constDict[cName] = cType
                    elif (util.pvsDefPat.search(line) or util.constPat.search(line)) and ':' in line and '=' in line and specialString in fileName:
                        funcDecls = util.split_sep_bks(line, ':')
                        functionName = funcDecls[0].split('[', 1)[0].split('(', 1)[0]
                        newStr = composeStr(functionName)
                        util.funcPat = re.compile(newStr)
                        for moduleName in module_list:
                            modData = srcData[moduleName]
                            if util.funcPat.search(modData):
                                if len(funcDecls) > 1:
                                    returnType = funcDecls[1].split('=', 1)[0].strip()
                                    returnType = util.split_sep_bk(returnType, ' ', '[', ']')[-1]
                                    returnType = util.parseReturnType(returnType)
                                    if '(#' in line and ')' not in line:
                                        if '[' in returnType:
                                            tvars = returnType.split('[', 1)
                                            rType = tvars[0]
                                            tvargs = tvars[1].rsplit(']', 1)[0]
                                            instanceItems[rType] = instanceItems[rType] if rType in instanceItems.keys() else []
                                            instanceItems[rType].append(tvargs + ':' + moduleName + '.' + functionName)
                                        else:
                                            instanceItems[returnType] = instanceItems[returnType] if returnType in instanceItems.keys() else []
                                            instanceItems[returnType].append(moduleName + '.' + functionName)
                                    elif not line.startswith('instance_'):
                                        # print(theoryName + ":" + functionName)
                                        vArgList = util.extract_bk_content(funcDecls[0])
                                        if len(vArgList) > 0:
                                            functionType = util.argSep.join(map(lambda arg: util.parseFunctionType(varDict, arg.split('(', 1)[1].rsplit(')', 1)[0].strip()), vArgList))
                                            functionType = functionType + '->' + returnType
                                        else:
                                            functionType = returnType
                                        functionType = functionType.replace(' ', '').replace('\n', '')
                                        functionItems[moduleName + '.' + functionName] = (functionType, theoryName)
                                break
                    elif (util.pvsDefPat.search(line) or util.constPat.search(line)) and ':' in line and '=' in line:
                        funcDecls = util.split_sep_bks(line, ':')
                        functionName = funcDecls[0].split('[', 1)[0].split('(', 1)[0]
                        returnType = funcDecls[1].split('=', 1)[0].strip()
                        returnType = util.split_sep_bk(returnType, ' ', '[', ']')[-1]
                        returnType = util.parseReturnType(returnType)
                        if ':TYPE' in line.replace(' ', '') or ')' in line:
                            vArgList = util.extract_bk_content(funcDecls[0])
                            if len(vArgList) > 0:
                                functionType = util.argSep.join(map(lambda arg: util.parseFunctionType(varDict, arg.split('(', 1)[1].rsplit(')', 1)[0].strip()), vArgList))
                                functionType = functionType + '->' + returnType
                            else:
                                functionType = returnType
                            if ']' not in functionType:
                                functionType = functionType.replace(' ', '').replace('\n', '')
                                patternItems[functionType] = patternItems[functionType] if functionType in patternItems.keys() else []
                                patternItems[functionType].append(theoryName + '.' + functionName)
                elif state == S_DATATYPE:
                    toContinue = True
                    if 'END ' in line:
                        tyContent = tyContent.rsplit(util.fieldSep, 1)[0]
                        typeItems[tyName] = ("datatype", tyContent)
                        state = S_STATE
                        toContinue = False
                    if toContinue:
                        if '?' in line:
                            decType += line
                            decType = decType.replace(' ', '').replace('\n', '')
                            constructor = decType.split(':')[0].split('(')[0]
                            functionType = ''
                            argDecls = util.split_sep_bk(decType, ':')
                            vArgList = util.extract_bk_content(argDecls[0])
                            argType = util.argSep.join(map(lambda arg: util.parseFunctionType(varDict, arg.split('(', 1)[1].rsplit(')', 1)[0].strip()), vArgList))
                            argType = argType.replace(' ', '')
                            tyContent += constructor.strip() + ':' + argType.replace(' ', '') + util.fieldSep
                            decType = ''
                        elif 'BEGIN' not in line:
                            decType += line
                elif state == S_TYPE:
                    toContinue = True
                    if '}' in line or '#]' in line or line.replace(' ', '') == '' or line.replace(' ', '') == '\n':
                        decType += line
                        if util.enumPat.search(decType):
                            vArgList = decType.split('{', 1)[1].rsplit('}', 1)[0].replace('\n', '').replace(' ', '').split(',')
                            tyContent = util.fieldSep.join(map(lambda arg: arg.strip(), vArgList))
                            typeItems[tyName] = ("datatype", tyContent)
                        elif '#]' in decType:
                            fields = decType.split('[#', 1)[1].rsplit('#]', 1)[0].replace('\n', '').replace(' ', '')
                            fieldList = util.split_sep_bk(fields, ',', '[', ']')
                            tyContent = util.fieldSep.join(map(lambda field: field.split(':', 1)[0].strip() + ':' + field.split(':', 1)[1].replace(' ', ''), fieldList))
                            typeItems[tyName] = ("record", tyContent)
                        else:
                            tydecl = decType.strip().split('=', 1)[1].strip()
                            if '{' in tydecl and '|' in tydecl:
                                tyTP = tydecl.split(':', 1)[1].split('|', 1)[0].strip()
                                tyDec = tydecl.split('|', 1)[1].split('}', 1)[0].strip()
                                nVars = list(set(util.numVarPat.findall(tyDec)))
                                if len(nVars) > 0:
                                    typeItems[tyName] = ("type", tyTP + ':' + ','.join(nVars) + ':' + tyDec)
                                else:
                                    typeItems[tyName] = ("type", tyTP + ':' + tyDec)  
                            else:
                                if ':' in tydecl:
                                    tydecl = ''.join(map(lambda arg: util.removeLastExtraID(arg.strip()).strip(), tydecl.split(':'))) 
                                typeItems[tyName] = ("type", tydecl.replace('\n', '').replace(' ', ''))
                        state = S_STATE
                        toContinue = False
                    if toContinue:
                        decType += line
            if constDict:
                constItems[theoryName] = constDict
    return (functionItems, constItems, typeItems, instanceItems, patternItems)

def gen_deps(dep_dict):
    mod_list = list(dep_dict.keys())
    module_list = []
    mod_num = len(mod_list)
    while len(module_list) < mod_num:
        for mod in mod_list:
            dep_list = list(dep_dict[mod])
            if dep_list == []:
                if mod not in module_list:
                    module_list.append(mod)
            dep_dict[mod] = util.diff_list(dep_list, module_list)
    return module_list

                    
def genDepForMlFiles(module_dict, src_data, lib_name):
    modules = list(module_dict.keys())
    new_mod_dict = copy.deepcopy(module_dict)
    lib_data = data[lib_name]
    ml_src_list = []
    external_cmds = lib_data[tags[T_ExtCmd]] if tags[T_ExtCmd] in lib_data else []
    external_mls = lib_data[tags[T_ExtML]] if tags[T_ExtML] in lib_data else []
    dep_dict = {}
    for module in modules:
        dep_dict[module] = []
        srcData = src_data[module]
        open_modules = re.findall(util.openModPat, srcData)
        include_modules = re.findall(util.includeModPat, srcData)
        call_modules = list(map(lambda x: x.rsplit('.', 1)[0], re.findall(util.callModPat, srcData)))
        modules = open_modules + include_modules + call_modules
        for line in modules:
            import_module_name = line
            if import_module_name in list(new_mod_dict.keys()):
                dep_dict[module].append(import_module_name)
    module_list = gen_deps(dep_dict)
    for mod in module_list:
        ml_src_list.append(new_mod_dict[mod])
    return ml_src_list[:-1]

                    
def parseSrcFiles(lib_name):
    update_library_data(lib_name)
    lib_data = data[lib_name]
    src_data = {}
    module_dict = {}
    ml_src_list = lib_data[tags[T_MLSrcFile]]
    for srcFileName in ml_src_list:
        moduleName = srcFileName.split('/')[-1].split('.ml')[0].capitalize()
        module_dict[moduleName] = srcFileName
        with open(srcFileName) as srcFile:
            src_data[moduleName] = srcFile.read()
    specialString = lib_data[tags[T_Prefix]]
    (functionItems, constItems, typeItems, instanceItems, patternItems) = parseFiles([moduleName for moduleName in list(module_dict.keys()) if moduleName.lower().startswith(specialString)], src_data, lib_name, specialString)
    lib_data[tags[T_Function]] = functionItems
    lib_data[tags[T_Const]] = constItems
    lib_data[tags[T_Type]] = typeItems
    lib_data[tags[T_Instance]] = instanceItems
    lib_data[tags[T_Pattern]] = patternItems
    mlSrcFiles = genDepForMlFiles(module_dict, src_data, lib_name)
    lib_data[tags[T_MLSrcFile]] = mlSrcFiles


def clean():
    cmd = 'cd ' + data[tags[T_TestDir]] + '; '
    cmd += 'rm -f *.pvs *.prf *.prf~ *.summary'
    helper.execute_command(cmd)

if __name__ == '__main__':
    setTestDir()
    setPVSHome()
    setup_pvs()
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate', action='store_true',
                        help='Generate the intermediate type annotation for a library')
    parser.add_argument('--clean', action='store_true',
                        help='Clean the generated data.json and all the test files')
    args = parser.parse_args()
    if args.generate:
        for lib_name in pvs_lib_list:
            parseSrcFiles(lib_name)
    elif args.clean:
        clean()
    with open(os.path.join(helper.dir_path, 'data.json'), 'w+') as json_file:
        json_file.write(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))


