#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
from pydriller import Repository
import os
import subprocess
import json
import signal
import math
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams

PATH_GITHUB = "parent_dir_containing_mystique"
PATH_VUL4J_DATASET_DIR = PATH_GITHUB + "/mystique"
CHECKOUT_AND_VERIFY = False
VERIFY_ALL_CHECKOUTS_AGAIN = False
VERIFY_PATCHES = False
SEPARATE_OUT_FIXES_FOR_MUTATION_PURPOSE = False
EXECUTE_MUTANTS = False
ANALYZE_MUTANTS_SIMULATIONS = False
CREATE_ML_DATASET = False
ANALYSE_AT_HIGH_LEVEL = False

PATH_VUL4J_CSV = PATH_VUL4J_DATASET_DIR + "/vul4j_dataset.csv"
PATH_PATCHES_DIR = PATH_VUL4J_DATASET_DIR + "/patches"
ALL_METHODS_CSV_NAME = "all_methods.csv"
CHANGED_METHODS_CSV_NAME = "changed_methods.csv"
PATH_CODE_DIR = PATH_VUL4J_DATASET_DIR + "/code"
PATH_FIXED_CODE_DIR = PATH_VUL4J_DATASET_DIR + "/fixed_code"
WASTE_CODE_DIR = PATH_VUL4J_DATASET_DIR + "/waste_code"
WASTE_PATCHES_DIR = PATH_VUL4J_DATASET_DIR + "/waste_patches"
WASTE_FIXED_PATCHES_DIR = PATH_VUL4J_DATASET_DIR + "/waste_fixed_patches"
PATH_FIXES_FOR_MUTATION_DIR = PATH_VUL4J_DATASET_DIR + "/fixes_for_mutation"
PATH_MUTANTS_DIR = PATH_VUL4J_DATASET_DIR + "/mutants_mbert"
PATH_MUTATED_CODE_DIR = PATH_VUL4J_DATASET_DIR + "/mutated_code"
PATH_MUTANTS_ANALYSIS_DIR = PATH_VUL4J_DATASET_DIR + "/mutants_mbert_analysis"
ALL_ANALYSIS_CSV_NAME = "all_analysis.csv"
TIMEOUT = 120
COMPLETED_VUL4J_IDS_CSV_NAME = "completed_vul4j_ids.csv"
PLOT_FILE_NAME = "plot_ochiai.pdf"
PATH_ML_DATASET_DIR = PATH_VUL4J_DATASET_DIR + "/ml_dataset"
PATH_SRC2ABS = PATH_GITHUB + "/src2abs/src2abs/target/src2abs-0.1-jar-with-dependencies.jar"
PATH_IDIOMS = PATH_ML_DATASET_DIR + "/idioms.txt"
ML_DATASET_CSV_NAME = "ml_dataset.csv"
HIGH_LEVEL_ANALYSIS_CSV_NAME = "high_level_analysis.csv"

def compare_between_and_get_methods_details(method_new, allmethods_old):
    long_name = method_new.long_name
    start_line_new = method_new.start_line
    end_line_new = method_new.end_line
    old_method_found = False
    for method_old in allmethods_old:
        if method_old.long_name == method_new.long_name:
            start_line_old = method_old.start_line
            end_line_old = method_old.end_line
            old_method_found = True
            break
    if old_method_found is False:
        print("method", method_new.name,", in new file, ranging from", method_new.start_line, "till", method_new.end_line, 
             "does not exists in old file!")
        start_line_old = -1
        end_line_old = -1
    return "\"" + long_name + "\"", start_line_new, end_line_new, start_line_old, end_line_old

def get_details_from_modified_file(file, df_all_methods, df_changed_methods, path_vul_dir):
    df_mod = pd.DataFrame(columns = ['line_num', 'mod_type', 'mod'])
    df_changed_methods_without_change = pd.DataFrame(columns = ['file_path', 'long_name', 
                                                                'start_line_new', 'end_line_new', 
                                                                'start_line_old', 'end_line_old'])
    file_path = file.old_path
    if file_path is None:
        return df_all_methods, df_changed_methods
    file_path = "\"" + file_path + "\""
    file_name = file.filename
    for method in file.methods:
        long_name, start_line_new, end_line_new, start_line_old, end_line_old = compare_between_and_get_methods_details(method, file.methods_before)
        df_all_methods = df_all_methods.append({'file_path' : file_path, 'long_name' : long_name, 
                        'start_line_new' : start_line_new, 'end_line_new' : end_line_new, 
                        'start_line_old' : start_line_old, 'end_line_old' : end_line_old}, ignore_index = True)

    for method in file.changed_methods:
        long_name, start_line_new, end_line_new, start_line_old, end_line_old = compare_between_and_get_methods_details(method, file.methods_before)
        df_changed_methods_without_change = df_changed_methods_without_change.append({
            'file_path' : file_path, 'long_name' : long_name, 
            'start_line_new' : start_line_new, 'end_line_new' : end_line_new, 
            'start_line_old' : start_line_old, 'end_line_old' : end_line_old}, ignore_index = True)

    for addition in file.diff_parsed.get("added"):
        line_num = addition[0]
        modification_type = "\"added\""
        modification = "\"" + addition[1] + "\""
        df_mod = df_mod.append({'line_num' : line_num, 'mod_type' : modification_type, 'mod' : modification}, 
                               ignore_index = True)

    for deletion in file.diff_parsed.get("deleted"):
        line_num = deletion[0]
        modification_type = "\"deleted\""
        modification = "\"" + deletion[1] + "\""
        df_mod = df_mod.append({'line_num' : line_num, 'mod_type' : modification_type, 'mod' : modification}, 
                               ignore_index = True)

    df_mod = df_mod.sort_values(['line_num', 'mod_type'], ascending = [True, False], ignore_index = True)

    for df_mod_index in df_mod.index:
        is_change_within_function = False
        for df_changed_methods_without_change_index in df_changed_methods_without_change.index:
            if is_change_within_function is False and \
            df_mod['line_num'][df_mod_index] >= df_changed_methods_without_change['start_line_new'][df_changed_methods_without_change_index] and \
            df_mod['line_num'][df_mod_index] <= df_changed_methods_without_change['end_line_new'][df_changed_methods_without_change_index]:
                is_change_within_function = True
                df_changed_methods = df_changed_methods.append({
                    'file_path' : df_changed_methods_without_change['file_path'][df_changed_methods_without_change_index], 
                    'long_name' : df_changed_methods_without_change['long_name'][df_changed_methods_without_change_index], 
                    'start_line_new' : df_changed_methods_without_change['start_line_new'][df_changed_methods_without_change_index], 
                    'end_line_new' : df_changed_methods_without_change['end_line_new'][df_changed_methods_without_change_index], 
                    'start_line_old' : df_changed_methods_without_change['start_line_old'][df_changed_methods_without_change_index], 
                    'end_line_old' : df_changed_methods_without_change['end_line_old'][df_changed_methods_without_change_index], 
                    'line_num' : df_mod['line_num'][df_mod_index], 'mod_type' : df_mod['mod_type'][df_mod_index], 
                    'mod' : df_mod['mod'][df_mod_index]}, ignore_index = True)
        if is_change_within_function is False:
            df_changed_methods = df_changed_methods.append({
                'file_path' : file_path, 
                'long_name' : "\"\"", 
                'start_line_new' : -1, 
                'end_line_new' : -1, 
                'start_line_old' : -1, 
                'end_line_old' : -1, 
                'line_num' : df_mod['line_num'][df_mod_index], 'mod_type' : df_mod['mod_type'][df_mod_index], 
                'mod' : df_mod['mod'][df_mod_index]}, ignore_index = True)


    source_code_after = file.source_code
    source_code_before = file.source_code_before

    if df_changed_methods.empty is False:
        os.makedirs(path_vul_dir, exist_ok=True)  
        after_file = open(path_vul_dir + "/" + file_name.split(".")[0] + "_after.java", "w")
        after_file.write(source_code_after)
        after_file.close()

        if source_code_before is None:
            print("source_code_before is not available, will require to get from the code dir!")
        else: 
            before_file = open(path_vul_dir + "/" + file_name.split(".")[0] + "_before.java", "w")
            before_file.write(source_code_before)
            before_file.close()
    return df_all_methods, df_changed_methods

def extract_patches_and_modifications_information_for_vulnerability (vul_id, patch_url):
    bool_extraction_successful = False
    path_vul_dir = PATH_PATCHES_DIR + "/" + vul_id
    if os.path.exists(path_vul_dir + "/commit_date.txt"):
        return True
    print("processing", vul_id)
    
    if "/commit/" in patch_url:
        patch_arr = patch_url.split("/commit/")
    else:
        print("no commit found in URL!")
        return False
    repo = patch_arr[0]
    commit_id = patch_arr[1].split(",")[0]
    print("searching for commit:", commit_id, "in repo:", repo)
    df_all_methods = pd.DataFrame(columns = ['file_path', 'long_name', 
                                             'start_line_new', 'end_line_new', 
                                             'start_line_old', 'end_line_old'])
    df_changed_methods = pd.DataFrame(columns = ['file_path', 'long_name', 
                                                 'start_line_new', 'end_line_new', 
                                                 'start_line_old', 'end_line_old', 
                                                 'line_num', "mod_type", "mod"])
    
    for commit in Repository(repo, single=commit_id).traverse_commits():
        commit_date = commit.committer_date
        for modified_file in commit.modified_files:
            df_all_methods, df_changed_methods = get_details_from_modified_file(
                modified_file, df_all_methods, df_changed_methods, path_vul_dir)

        if df_changed_methods.empty is False:
            df_all_methods.to_csv(path_vul_dir + "/" + ALL_METHODS_CSV_NAME, index = False)
            df_changed_methods.to_csv(path_vul_dir + "/" + CHANGED_METHODS_CSV_NAME, index = False)

            commit_date_file = open(path_vul_dir + "/commit_date.txt", "w")
            commit_date_file.write(str(commit_date))
            commit_date_file.close()
            bool_extraction_successful = True
    return bool_extraction_successful

def get_changed_code_files_paths (vul_id):
    path_patches_dir_for_vulnerability = PATH_PATCHES_DIR + "/" + vul_id
    lst_changed_code_files_paths = []
    if os.path.exists(path_patches_dir_for_vulnerability + "/" + CHANGED_METHODS_CSV_NAME):
        df_changed_methods = pd.read_csv(path_patches_dir_for_vulnerability + "/" + CHANGED_METHODS_CSV_NAME)
        for df_changed_methods_ind in df_changed_methods.index:
            file_path = df_changed_methods["file_path"][df_changed_methods_ind].replace("\"","")
            if ("/test/" not in file_path) and ("/tests/" not in file_path) and (".java" in file_path) and (file_path not in lst_changed_code_files_paths):
                lst_changed_code_files_paths.append(file_path)
    return lst_changed_code_files_paths

def get_compilation_results(path_dir, vul_id):
    bool_compiled = None
    path_compile_result_text_file = path_dir + "/" + vul_id + "/VUL4J/compile_result.txt"
    if os.path.exists(path_compile_result_text_file):
        compile_result_text_file = open(path_compile_result_text_file, "r")
        content_compile_result_text_file = compile_result_text_file.read()
        compile_result_text_file.close()
        if content_compile_result_text_file == "1":
            bool_compiled = True
        else:
            bool_compiled = False
    return bool_compiled

def get_test_results(path_dir, vul_id):
    test_passed = None
    path_testing_results_json_file = path_dir + "/" + vul_id + "/VUL4J/testing_results.json"
    if os.path.exists(path_testing_results_json_file):
        file_testing_results_json = open(path_testing_results_json_file)
        try:
            content_testing_results_json_file = json.load(file_testing_results_json)
        except:
            print("error in loading json")
            content_testing_results_json_file = ""
        file_testing_results_json.close()
        if content_testing_results_json_file != "":            
            overall_metrics = content_testing_results_json_file["tests"]["overall_metrics"]
            number_error = overall_metrics["number_error"]
            number_failing = overall_metrics["number_failing"]
            if number_error == 0 and number_failing == 0:
                test_passed = True
            else:
                test_passed = False
    return test_passed

def execute_tests_and_get_results(path_dir, vul_id):
    bool_compiled = get_compilation_results(path_dir, vul_id)
    bool_test_passed = None
    if bool_compiled is None:
        print("compiled", vul_id, ", but coudn't find the compilation results!")
    elif bool_compiled is True:
        command_to_execute = ["vul4j","test","-d",path_dir + "/" + vul_id]
        print("executing", command_to_execute)
        try:
            p = subprocess.Popen(command_to_execute, stdout=subprocess.DEVNULL, start_new_session=True)
            p.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            print("timed out!")
            print('Terminating the whole process group...')
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        bool_test_passed = get_test_results(path_dir, vul_id)
        if bool_test_passed is None:
            print("tests executed for", vul_id, ", but coudn't find the test results!")
        elif bool_test_passed is True:
            print("all tests passed for", vul_id)
        else:
            print("tests failed for", vul_id)
    else:
        print(vul_id, "didn't compile!")
    return bool_compiled, bool_test_passed

def execute_and_get_vul4j_results (path_dir, vul_id):
    command_to_execute = ["vul4j","compile","-d",path_dir + "/" + vul_id]
    print("executing", command_to_execute)
    try:
        p = subprocess.Popen(command_to_execute, stdout=subprocess.DEVNULL, start_new_session=True)
        p.wait(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        print("timed out!")
        print('Terminating the whole process group...')
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
    return execute_tests_and_get_results(path_dir, vul_id)

def checkout_vulnerability(path_dir, vul_id):
    if os.path.exists(path_dir + "/" + vul_id):
        return False
    else:
        command_to_execute = ["vul4j", "checkout", "--id", vul_id, "-d", path_dir + "/" + vul_id]
        print("executing", command_to_execute)
        subprocess.run(command_to_execute, stdout=subprocess.DEVNULL)
        return True

def recheckout_vulnerability(path_dir, vul_id):
    if os.path.exists(path_dir + "/" + vul_id):
        command_to_execute = ["rm", "-r", path_dir + "/" + vul_id]
        print("executing", command_to_execute)
        subprocess.run(command_to_execute, stdout=subprocess.DEVNULL)
    checkout_vulnerability(path_dir, vul_id)

def verify_checkout_and_retry(vul_id):
    bool_verified_ok = False
    bool_compiled, bool_test_passed = execute_and_get_vul4j_results (PATH_CODE_DIR, vul_id)
    if (bool_compiled is None) or (bool_compiled is False) or (bool_test_passed is True) :
        recheckout_vulnerability(PATH_CODE_DIR, vul_id)
        bool_compiled, bool_test_passed = execute_and_get_vul4j_results (PATH_CODE_DIR, vul_id)
        if (bool_compiled is None) or (bool_compiled is False) or (bool_test_passed is True):
            print("re-downloading", vul_id, "didn't solve the problem!")
            if os.path.exists(PATH_CODE_DIR + "/" + vul_id):
                command_to_execute = ["mv", PATH_CODE_DIR + "/" + vul_id, WASTE_CODE_DIR + "/"]
                print("executing", command_to_execute)
                subprocess.run(command_to_execute, stdout=subprocess.DEVNULL)
            return bool_verified_ok
    command_to_execute = ["cp", "-r", PATH_CODE_DIR + "/" + vul_id, PATH_FIXED_CODE_DIR + "/"]
    print("executing", command_to_execute)
    subprocess.run(command_to_execute, stdout=subprocess.DEVNULL)
    return True
    
def verify_extracted_vulnerable_files(vul_id):
    path_code_dir_for_vulnerability = PATH_CODE_DIR + "/" + vul_id
    path_patches_dir_for_vulnerability = PATH_PATCHES_DIR + "/" + vul_id
    if os.path.exists(path_patches_dir_for_vulnerability) is False:
        print(path_patches_dir_for_vulnerability, "does not exist!")
        return False
    lst_changed_code_files_paths = get_changed_code_files_paths (vul_id)
    for changed_code_file_path in lst_changed_code_files_paths:
        arr_changed_code_file_path = changed_code_file_path.split("/")
        changed_code_file_name = arr_changed_code_file_path[len(arr_changed_code_file_path) - 1]
        
        original_vulnerable_file = open(path_code_dir_for_vulnerability + "/" + changed_code_file_path, "r")
        content_original_vulnerable_file = original_vulnerable_file.read()
        original_vulnerable_file.close()
        
        extracted_vulnerable_file = open(path_patches_dir_for_vulnerability + "/" + changed_code_file_name.replace(".java", "_before.java"), "r")
        content_extracted_vulnerable_file = extracted_vulnerable_file.read()
        extracted_vulnerable_file.close()
        
        if content_original_vulnerable_file.replace(" ","") != content_extracted_vulnerable_file.replace(" ",""):
            print("File mismatch for", vul_id)
            print(path_code_dir_for_vulnerability + "/" + changed_code_file_path,"does not match with", \
                  path_patches_dir_for_vulnerability + "/" + changed_code_file_name.replace(".java", "_before.java"))
            command_to_execute = ["mv", PATH_PATCHES_DIR + "/" + vul_id, WASTE_PATCHES_DIR + "/"]
            print("executing", command_to_execute)
            subprocess.run(command_to_execute, stdout=subprocess.DEVNULL)
            return False
    return True
        
        
def verify_extracted_fixed_files(vul_id):
    path_fixed_code_dir_for_vulnerability = PATH_FIXED_CODE_DIR + "/" + vul_id
    path_patches_dir_for_vulnerability = PATH_PATCHES_DIR + "/" + vul_id
    if os.path.exists(path_patches_dir_for_vulnerability) is False:
        print(path_patches_dir_for_vulnerability, "does not exist!")
        return False
    
    if os.path.exists(path_fixed_code_dir_for_vulnerability) is False:
        command_to_execute = ["cp", "-r", PATH_CODE_DIR + "/" + vul_id, PATH_FIXED_CODE_DIR + "/"]
        print("executing", command_to_execute)
        subprocess.run(command_to_execute, stdout=subprocess.DEVNULL)

    lst_changed_code_files_paths = get_changed_code_files_paths (vul_id)
    dict_vulnerable_files = {}
    for changed_code_file_path in lst_changed_code_files_paths:
        arr_changed_code_file_path = changed_code_file_path.split("/")
        changed_code_file_name = arr_changed_code_file_path[len(arr_changed_code_file_path) - 1]
        extracted_fixed_file = open(path_patches_dir_for_vulnerability + "/" + changed_code_file_name.replace(".java", "_after.java"), "r")
        content_extracted_fixed_file = extracted_fixed_file.read()
        extracted_fixed_file.close()
        
        original_file = open(path_fixed_code_dir_for_vulnerability + "/" + changed_code_file_path, "w")
        original_file.write(content_extracted_fixed_file)
        original_file.close()
    
    bool_compiled, test_passed = execute_and_get_vul4j_results (PATH_FIXED_CODE_DIR, vul_id)
    if test_passed is not True:
        print("Test suite didn't pass, restoring files...")
        command_to_execute = ["rm", "-r", PATH_FIXED_CODE_DIR + "/" + vul_id]
        print("executing", command_to_execute)
        subprocess.run(command_to_execute, stdout=subprocess.DEVNULL)
        
        command_to_execute = ["mv", PATH_PATCHES_DIR + "/" + vul_id, WASTE_FIXED_PATCHES_DIR + "/"]
        print("executing", command_to_execute)
        subprocess.run(command_to_execute, stdout=subprocess.DEVNULL)
        return False
    return True

def checkout_and_verify():
    df_csv = pd.read_csv(PATH_VUL4J_CSV)
    if os.path.exists(PATH_CODE_DIR) is False:
        os.mkdir(PATH_CODE_DIR)
    if os.path.exists(WASTE_CODE_DIR) is False:
        os.mkdir(WASTE_CODE_DIR)
    if os.path.exists(PATH_FIXED_CODE_DIR) is False:
        os.mkdir(PATH_FIXED_CODE_DIR)
    if os.path.exists(PATH_PATCHES_DIR) is False:
        os.mkdir(PATH_PATCHES_DIR)
    for df_csv_ind in df_csv.index:
        vul_id = df_csv["vul_id"][df_csv_ind]
        patch_url = df_csv["human_patch"][df_csv_ind]
        # checkout vulnerability and return if it is new
        bool_is_new = checkout_vulnerability(PATH_CODE_DIR, vul_id)
        
        if VERIFY_ALL_CHECKOUTS_AGAIN is True:
            bool_is_new = True
        
        if bool_is_new is True:        
            
            #returns if verified ok or not
            bool_verified_ok = verify_checkout_and_retry(vul_id)
            
            if bool_verified_ok is not True:
                continue

            # extract patches for vulnerabilities using commit IDs and returns if successful or not
            bool_extraction_successful = extract_patches_and_modifications_information_for_vulnerability (vul_id, patch_url)
            
def process_this_mutant(vul_id, mutant_id, mutant_file_name, mutant_desired_path):
    dir_class_mutants = mutant_file_name.replace(".java","_mutants")
    path_mutant = PATH_MUTANTS_DIR + "/" + vul_id + "/" + dir_class_mutants + "/" + mutant_id + "/" + mutant_file_name
    file_mutant = open(path_mutant, "r")
    content_mutant = file_mutant.read()
    file_mutant.close()    
    
    path_fixed = PATH_MUTATED_CODE_DIR + "/" + vul_id + "/" + mutant_desired_path
    file_fixed = open(path_fixed, "r")
    content_fixed = file_fixed.read()
    file_fixed.close()
    
    file_to_change = open(path_fixed, "w")
    file_to_change.write(content_mutant)
    file_to_change.close()
    
    bool_compiled, test_passed = execute_and_get_vul4j_results (PATH_MUTATED_CODE_DIR, vul_id)
    command_to_execute = ["cp", "-r", PATH_MUTATED_CODE_DIR + "/" + vul_id + "/VUL4J", \
                          PATH_MUTANTS_DIR + "/" + vul_id + "/" + dir_class_mutants + "/" + mutant_id + "/"]
    print("executing", command_to_execute)
    subprocess.run(command_to_execute, stdout=subprocess.DEVNULL)    
    
    file_to_change = open(path_fixed, "w")
    file_to_change.write(content_fixed)
    file_to_change.close()

def execute_mutants(vul_id):
    print("\nexecuting mutants for", vul_id, "\n")
    path_mutated_code_dir_for_vulnerability = PATH_MUTATED_CODE_DIR + "/" + vul_id
    lst_changed_code_files_paths = get_changed_code_files_paths (vul_id)
    dict_changed_files_with_path = {}
    for changed_code_file_path in lst_changed_code_files_paths:
        arr_changed_code_file_path = changed_code_file_path.split("/")
        changed_code_file_name = arr_changed_code_file_path[len(arr_changed_code_file_path) - 1]
        if changed_code_file_name not in dict_changed_files_with_path:
            dict_changed_files_with_path[changed_code_file_name] = changed_code_file_path
        
    if os.path.exists(path_mutated_code_dir_for_vulnerability) is True:
        command_to_execute = ["rm", "-r", path_mutated_code_dir_for_vulnerability]
        print("executing", command_to_execute)
        subprocess.run(command_to_execute, stdout=subprocess.DEVNULL)
    
    path_fixed_code_dir_for_vulnerability = PATH_FIXED_CODE_DIR + "/" + vul_id
    if os.path.exists(path_fixed_code_dir_for_vulnerability) is False:
        print(path_fixed_code_dir_for_vulnerability, "does not exist!")
        return
    else:
        command_to_execute = ["cp", "-r", path_fixed_code_dir_for_vulnerability, PATH_MUTATED_CODE_DIR + "/"]
        print("executing", command_to_execute)
        subprocess.run(command_to_execute, stdout=subprocess.DEVNULL)

    for changed_file in dict_changed_files_with_path:
        dir_class_mutants = changed_file.replace(".java","_mutants")
        path_mutants_dir_for_vulnerability = PATH_MUTANTS_DIR + "/" + vul_id + "/" + dir_class_mutants
        if os.path.exists(path_mutants_dir_for_vulnerability) is False:
            continue
        for mutant_id in os.listdir(path_mutants_dir_for_vulnerability):
            print("\nprocessing for mutant", mutant_id)
            if os.path.isdir(path_mutants_dir_for_vulnerability + "/" + mutant_id) is False:
                continue
            if os.path.exists(path_mutants_dir_for_vulnerability + "/" + mutant_id + \
                             "/VUL4J") is True:
                continue
            path_looking_for = path_mutants_dir_for_vulnerability + "/" + mutant_id + "/" + changed_file
            print("looking for", path_looking_for)
            if os.path.exists(path_looking_for):
                process_this_mutant(vul_id, mutant_id, changed_file, \
                                    dict_changed_files_with_path[changed_file]) 

def get_cve_id_and_failed_test_details(path_dir, vul_id):
    dict_failed_tests = {}
    path_testing_results_json_file = path_dir + "/" + vul_id + "/VUL4J/testing_results.json"
    cve_id = ""
    if os.path.exists(path_testing_results_json_file):
        file_testing_results_json = open(path_testing_results_json_file)
        content_testing_results_json_file = json.load(file_testing_results_json)
        file_testing_results_json.close()
        cve_id = content_testing_results_json_file["cve_id"]
        failures = content_testing_results_json_file["tests"]["failures"]
        for failure in failures:
            failed_test = failure["test_class"] + "#" + failure["test_method"]
            failure_name = failure["failure_name"]
            if failed_test not in dict_failed_tests:
                dict_failed_tests[failed_test] = failure_name
    return cve_id, dict_failed_tests

def get_intersection_and_ochiai (broken_tests_by_vuln, broken_tests_by_mutant):
    if len(broken_tests_by_vuln) == 0 or len(broken_tests_by_mutant) == 0:
        return "\"\"", 0
    intersection = []
    for broken_test_by_vuln in broken_tests_by_vuln:
        if broken_test_by_vuln in broken_tests_by_mutant:
            intersection.append(broken_test_by_vuln)
    if len(intersection) == 0:
        return "\"\"", 0
    prod = len(broken_tests_by_vuln) * len(broken_tests_by_mutant)
    ochiai = round((len(intersection) / math.sqrt(prod)), 4)
    
    string_intersection = "\""
    for interesection_test in intersection:
        if string_intersection == "\"":
            string_intersection = string_intersection + interesection_test
        else:
            string_intersection = string_intersection + "," + interesection_test
    string_intersection = string_intersection + "\""
    return string_intersection, ochiai

def get_mutant_vulnerability_comparison_scores(vul_id, dir_class_mutants, mutant_id, dict_failed_tests_by_vuln):
    did_mutant_compile = False
    did_tests_fail = False
    imitates_vuln = False
    ochiai = 0
    failed_tests_intersection = "\"\""
    failed_tests = ""
    failures = ""
    path_mutants_dir_for_vulnerability = PATH_MUTANTS_DIR + "/" + vul_id + "/" + dir_class_mutants
    
    bool_compiled = get_compilation_results(path_mutants_dir_for_vulnerability, mutant_id)
    bool_test_passed = get_test_results(path_mutants_dir_for_vulnerability, mutant_id)

    if bool_compiled is True:
        did_mutant_compile = True
        if bool_test_passed is False:
            did_tests_fail = True
            cve_id, dict_failed_tests_by_mutant = get_cve_id_and_failed_test_details(path_mutants_dir_for_vulnerability, mutant_id)
            if set(dict_failed_tests_by_mutant.keys()) == set(dict_failed_tests_by_vuln.keys()):
                print(mutant_id, "immitates vulnerability!")
                imitates_vuln = True
            failed_tests_intersection, ochiai = get_intersection_and_ochiai (set(dict_failed_tests_by_vuln.keys()), set(dict_failed_tests_by_mutant.keys()))
            for failed_test in dict_failed_tests_by_mutant:
                if failed_tests == "":
                    failed_tests = failed_test
                    failures = dict_failed_tests_by_mutant[failed_test]
                else:
                    failed_tests = failed_tests + "," + failed_test
                    failures = failures + "," + dict_failed_tests_by_mutant[failed_test]
    failed_tests = "\"" + failed_tests + "\""
    failures = "\"" + failures + "\""
    return did_mutant_compile, did_tests_fail, imitates_vuln, ochiai, failed_tests_intersection, failed_tests, failures

def separate_out_fixed_files(vul_id):
    path_patches_dir_for_vulnerability = PATH_PATCHES_DIR + "/" + vul_id
    dir_fixes_this_vuln = PATH_FIXES_FOR_MUTATION_DIR + "/" + vul_id
    if os.path.exists(dir_fixes_this_vuln):
        return
    lst_changed_code_files_paths = get_changed_code_files_paths (vul_id)
    if len(lst_changed_code_files_paths) > 0:
        os.mkdir(dir_fixes_this_vuln)
        print("created directory:", dir_fixes_this_vuln)

    for changed_code_file_path in lst_changed_code_files_paths:
        arr_changed_code_file_path = changed_code_file_path.split("/")
        changed_code_file_name = arr_changed_code_file_path[len(arr_changed_code_file_path) - 1]
        
        path_fixed_file = path_patches_dir_for_vulnerability + "/" + changed_code_file_name.replace(".java", "_after.java")
        command_to_execute = ["cp", path_fixed_file, dir_fixes_this_vuln + "/" + changed_code_file_name]
        print("executing", command_to_execute)
        subprocess.run(command_to_execute, stdout=subprocess.DEVNULL)

def analyze_mutants_simulations_and_get_analysis():
    if os.path.exists(PATH_MUTANTS_ANALYSIS_DIR + "/" + ALL_ANALYSIS_CSV_NAME):
        df_analysis_csv = pd.read_csv(PATH_MUTANTS_ANALYSIS_DIR + "/" + ALL_ANALYSIS_CSV_NAME)
        return df_analysis_csv
    if os.path.exists(PATH_MUTANTS_ANALYSIS_DIR) is False:
        os.mkdir(PATH_MUTANTS_ANALYSIS_DIR)
    df_analysis_csv = pd.DataFrame(columns = ['vul_id', 'cve_id', 'class', 'mut_id', 'did_mutant_compile', 'did_tests_fail', \
                                              'imitates_vuln', 'ochiai', 'failed_tests_intersection', 'failed_tests', 'failures'])
    for vul_id in os.listdir(PATH_MUTANTS_DIR):
        if os.path.exists(PATH_MUTANTS_ANALYSIS_DIR + "/" + ALL_ANALYSIS_CSV_NAME.replace("all",vul_id)):
            df_vul_id_analysis_csv = pd.read_csv(PATH_MUTANTS_ANALYSIS_DIR + "/" + ALL_ANALYSIS_CSV_NAME.replace("all",vul_id))
            df_analysis_csv = df_analysis_csv.append(df_vul_id_analysis_csv, ignore_index=True)
            continue
            
        df_vul_id_analysis_csv = pd.DataFrame(columns = ['vul_id', 'cve_id', 'class', 'mut_id', 'did_mutant_compile', 'did_tests_fail', \
                                                         'imitates_vuln', 'ochiai', 'failed_tests_intersection', 'failed_tests', 'failures'])
        if os.path.isdir(PATH_MUTANTS_DIR + "/" + vul_id) is False:
            continue        
        dict_changed_files_with_path = {}
        lst_changed_code_files_paths = get_changed_code_files_paths (vul_id)
        for changed_code_file_path in lst_changed_code_files_paths:
            arr_changed_code_file_path = changed_code_file_path.split("/")
            changed_code_file_name = arr_changed_code_file_path[len(arr_changed_code_file_path) - 1]
            if changed_code_file_name not in dict_changed_files_with_path:
                dict_changed_files_with_path[changed_code_file_name] = changed_code_file_path

        for changed_file in dict_changed_files_with_path:
            dir_class_mutants = changed_file.replace(".java","_mutants")
            path_mutants_dir_for_vulnerability = PATH_MUTANTS_DIR + "/" + vul_id + "/" + dir_class_mutants
            if os.path.exists(path_mutants_dir_for_vulnerability) is False:
                continue
            cve_id, dict_failed_tests_by_vuln = get_cve_id_and_failed_test_details(PATH_CODE_DIR, vul_id)
            if len(dict_failed_tests_by_vuln) == 0:
                continue
            for mutant_id in os.listdir(path_mutants_dir_for_vulnerability):
                if os.path.isdir(path_mutants_dir_for_vulnerability + "/" + mutant_id) is False:
                    continue
                print("\nanalyzing vul_id:", vul_id, "| class:", changed_file, "| mut_id:", mutant_id)
                did_mutant_compile, did_tests_fail, imitates_vuln, ochiai, failed_tests_intersection, failed_tests, failures = \
                get_mutant_vulnerability_comparison_scores(vul_id, dir_class_mutants, mutant_id, dict_failed_tests_by_vuln)
                df_vul_id_analysis_csv = df_vul_id_analysis_csv.append({'vul_id' : "\"" + vul_id + "\"", 
                                                          'cve_id' : "\"" + cve_id + "\"",
                                                          'class' : "\"" + changed_file + "\"",
                                                          'mut_id' : mutant_id, 
                                                          'did_mutant_compile': did_mutant_compile, 
                                                          'did_tests_fail' : did_tests_fail, 
                                                          'imitates_vuln' : imitates_vuln, 
                                                          'ochiai' : ochiai, 
                                                          'failed_tests_intersection' : failed_tests_intersection, 
                                                          'failed_tests' : failed_tests, 
                                                          'failures' : failures}, ignore_index = True)
                df_analysis_csv = df_analysis_csv.append({'vul_id' : "\"" + vul_id + "\"", 
                                                          'cve_id' : "\"" + cve_id + "\"",
                                                          'class' : "\"" + changed_file + "\"",
                                                          'mut_id' : mutant_id, 
                                                          'did_mutant_compile': did_mutant_compile, 
                                                          'did_tests_fail' : did_tests_fail, 
                                                          'imitates_vuln' : imitates_vuln, 
                                                          'ochiai' : ochiai, 
                                                          'failed_tests_intersection' : failed_tests_intersection, 
                                                          'failed_tests' : failed_tests, 
                                                          'failures' : failures}, ignore_index = True)
        if len(df_vul_id_analysis_csv) > 0:
            print("writing", ALL_ANALYSIS_CSV_NAME.replace("all",vul_id), "in", PATH_MUTANTS_ANALYSIS_DIR)
            df_vul_id_analysis_csv.to_csv(PATH_MUTANTS_ANALYSIS_DIR + "/" + ALL_ANALYSIS_CSV_NAME.replace("all",vul_id), index = False)
    print("writing", ALL_ANALYSIS_CSV_NAME, "in", PATH_MUTANTS_ANALYSIS_DIR)
    df_analysis_csv.to_csv(PATH_MUTANTS_ANALYSIS_DIR + "/" + ALL_ANALYSIS_CSV_NAME, index = False)
    return df_analysis_csv

def write_to_completed_vul4j_ids_file(file_path, vul_id):
    print("writing to", file_path)
    df_completed_vul4j_ids = pd.DataFrame(columns = ['vul_id'])
    if os.path.exists(file_path):
        df_completed_vul4j_ids = pd.read_csv(file_path)
    df_completed_vul4j_ids = df_completed_vul4j_ids.append({'vul_id' : vul_id}, ignore_index = True)
    df_completed_vul4j_ids.to_csv(file_path, index = False)

def plot (df_analysis_csv):
    df = df_analysis_csv.loc[(df_analysis_csv['did_mutant_compile'] == True) & (df_analysis_csv['did_tests_fail'] == True)]
    rcParams['figure.figsize'] = 15,7
    f = plt.figure(1)
    ax = sns.boxplot(x=df["cve_id"], y=df["ochiai"] )
    ax.set_xticklabels(ax.get_xticklabels(),rotation=70)
    plt.xlabel('CVE', fontsize=16);
    plt.ylabel('Ochiai', fontsize=16);
    plt.tick_params(axis='both', which='major', labelsize=12)
    plt.tight_layout()
    plt.savefig(PATH_MUTANTS_ANALYSIS_DIR + "/" + PLOT_FILE_NAME)

def execute_command_with_timeout(command_to_execute):
    try:
        print("executing", command_to_execute)
        p = subprocess.Popen(command_to_execute, stdout=subprocess.DEVNULL, start_new_session=True)
        p.wait(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        print("timed out!")
        print('Terminating the whole process group...')
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
    
def iterate_over_analysis_csv ():
    if os.path.exists(PATH_ML_DATASET_DIR + "/" + ML_DATASET_CSV_NAME):
        print(PATH_ML_DATASET_DIR + "/" + ML_DATASET_CSV_NAME, "exists. Skipping...")
        return
    if os.path.exists(PATH_MUTANTS_ANALYSIS_DIR + "/" + ALL_ANALYSIS_CSV_NAME) is False:
        print(PATH_MUTANTS_ANALYSIS_DIR + "/" + ALL_ANALYSIS_CSV_NAME, "does not exist!")
        return
    df_ml_dataset = pd.DataFrame(columns = ['vul_id', 'cve_id', 'class', 'mut_id', 'did_mutant_compile', 'did_tests_fail', \
                                           'imitates_vuln', 'ochiai', 'failed_tests_intersection', 'failed_tests', 'failures', \
                                           'abs_seq'])
    df_analysis_csv = pd.read_csv(PATH_MUTANTS_ANALYSIS_DIR + "/" + ALL_ANALYSIS_CSV_NAME)
    df_compilable_mutants = df_analysis_csv.loc[(df_analysis_csv['did_mutant_compile'] == True)]
    dict_vuln_mapping_csv = {}
    for df_compilable_mutants_index in df_compilable_mutants.index:
        vul_id = df_compilable_mutants['vul_id'][df_compilable_mutants_index].replace("\"","")
        class_name = df_compilable_mutants['class'][df_compilable_mutants_index].replace("\"","")
        mut_id = df_compilable_mutants['mut_id'][df_compilable_mutants_index]
        file_from_src2abs_name = vul_id + "_" + class_name.replace(".java","") + "_" + str(mut_id) + "_abs.txt"
        
        if os.path.exists(PATH_ML_DATASET_DIR + "/" + file_from_src2abs_name) is False:
            class_mutants_dir_name = class_name.replace(".java","_mutants")
            class_mutants_mapping_csv_name = class_name.replace(".java","-mapping.csv")
            class_mutants_mapping_csv_path = PATH_MUTANTS_DIR + "/" + vul_id + "/" + class_mutants_dir_name + "/" + class_mutants_mapping_csv_name
            if vul_id not in dict_vuln_mapping_csv:
                print("searching for", class_mutants_mapping_csv_path)
                if os.path.exists(class_mutants_mapping_csv_path) is False:
                    continue
                df_class_mutants_mapping_csv = pd.read_csv(class_mutants_mapping_csv_path)
                dict_vuln_mapping_csv[vul_id] = df_class_mutants_mapping_csv
            df_class_mutants_mapping_csv = dict_vuln_mapping_csv[vul_id]
            df_selected_mapping = df_class_mutants_mapping_csv.loc[(df_class_mutants_mapping_csv['id'] == mut_id)]
            for df_selected_mapping_index in df_selected_mapping.index:
                mut_operator = df_selected_mapping["mut_operator"][df_selected_mapping_index]
                orig_token =  df_selected_mapping["orig_token"][df_selected_mapping_index]
                orig_token = str(orig_token)
                masked_expr = df_selected_mapping["masked_expr"][df_selected_mapping_index]
                masked_seq = df_selected_mapping["masked_seq"][df_selected_mapping_index]
                break
            
            original_seq_with_mutation_operator = masked_seq.replace("<mask>", " " + orig_token + " [MUTATION_OPERATOR] ")

            file_for_src2abs_name = vul_id + "_" + class_name.replace(".java","") + "_" + str(mut_id) + ".txt"
            file_for_src2abs = open(PATH_ML_DATASET_DIR + "/" + file_for_src2abs_name, "w")
            file_for_src2abs.write(original_seq_with_mutation_operator)
            file_for_src2abs.close()

            command_to_execute = ["java", "-jar", PATH_SRC2ABS, "single", "method", PATH_ML_DATASET_DIR + "/" + file_for_src2abs_name, PATH_ML_DATASET_DIR + "/" + file_from_src2abs_name, PATH_IDIOMS]
            execute_command_with_timeout(command_to_execute)
            command_to_execute = ["rm", PATH_ML_DATASET_DIR + "/" + file_for_src2abs_name]
            execute_command_with_timeout(command_to_execute)
            if os.path.exists(PATH_ML_DATASET_DIR + "/" + file_from_src2abs_name + ".map"):
                command_to_execute = ["rm", PATH_ML_DATASET_DIR + "/" + file_from_src2abs_name + ".map"]
                execute_command_with_timeout(command_to_execute)
            if os.path.exists(PATH_ML_DATASET_DIR + "/" + file_from_src2abs_name) is False:
                continue

            file_from_src2abs = open(PATH_ML_DATASET_DIR + "/" + file_from_src2abs_name, "r")
            abstracted_seq_with_mutation_operator = file_from_src2abs.read()
            file_from_src2abs.close()

            if abstracted_seq_with_mutation_operator is None or abstracted_seq_with_mutation_operator == "":
                continue
            if "[ MUTATION_OPERATOR ]" not in abstracted_seq_with_mutation_operator:
                continue
            abstracted_seq_final = abstracted_seq_with_mutation_operator.replace("[ MUTATION_OPERATOR ]", mut_operator)
            command_to_execute = ["rm", PATH_ML_DATASET_DIR + "/" + file_from_src2abs_name]
            execute_command_with_timeout(command_to_execute)
            
            file_from_src2abs = open(PATH_ML_DATASET_DIR + "/" + file_from_src2abs_name, "w")
            file_from_src2abs.write(abstracted_seq_final)
            file_from_src2abs.close()
            
        file_from_src2abs = open(PATH_ML_DATASET_DIR + "/" + file_from_src2abs_name, "r")
        abstracted_seq_final = file_from_src2abs.read()
        file_from_src2abs.close()
        
        if abstracted_seq_final is None or abstracted_seq_final == "":
            continue
        row_vul_id = df_compilable_mutants['vul_id'][df_compilable_mutants_index]
        row_cve_id = df_compilable_mutants['cve_id'][df_compilable_mutants_index]
        row_class = df_compilable_mutants['class'][df_compilable_mutants_index]
        row_mut_id = df_compilable_mutants['mut_id'][df_compilable_mutants_index]
        row_did_mutant_compile = df_compilable_mutants['did_mutant_compile'][df_compilable_mutants_index]
        row_did_tests_fail = df_compilable_mutants['did_tests_fail'][df_compilable_mutants_index]
        row_imitates_vuln = df_compilable_mutants['imitates_vuln'][df_compilable_mutants_index]
        row_ochiai = df_compilable_mutants['ochiai'][df_compilable_mutants_index]
        row_failed_tests_intersection = df_compilable_mutants['failed_tests_intersection'][df_compilable_mutants_index]
        row_failed_tests = df_compilable_mutants['failed_tests'][df_compilable_mutants_index]
        row_failures = df_compilable_mutants['failures'][df_compilable_mutants_index]
        df_ml_dataset = df_ml_dataset.append({'vul_id' : row_vul_id, 
                                                  'cve_id' : row_cve_id, 
                                                  'class' : row_class, 
                                                  'mut_id' : row_mut_id, 
                                                  'did_mutant_compile': row_did_mutant_compile, 
                                                  'did_tests_fail' : row_did_tests_fail, 
                                                  'imitates_vuln' : row_imitates_vuln, 
                                                  'ochiai' : row_ochiai, 
                                                  'failed_tests_intersection' : row_failed_tests_intersection, 
                                                  'failed_tests' : row_failed_tests, 
                                                  'failures' : row_failures, 
                                                  'abs_seq' : "\"" + abstracted_seq_final + "\""}, ignore_index = True)
    df_ml_dataset.to_csv(PATH_ML_DATASET_DIR + "/" + ML_DATASET_CSV_NAME, index = False)

def get_changed_code_files_and_methods_nums (vul_id):
    lst_changed_files = []
    lst_changed_methods = []
    path_patches_dir_for_vulnerability = PATH_PATCHES_DIR + "/" + vul_id
    lst_changed_code_files_paths = []
    if os.path.exists(path_patches_dir_for_vulnerability + "/" + CHANGED_METHODS_CSV_NAME):
        df_changed_methods = pd.read_csv(path_patches_dir_for_vulnerability + "/" + CHANGED_METHODS_CSV_NAME)
        for df_changed_methods_ind in df_changed_methods.index:
            file_path = df_changed_methods["file_path"][df_changed_methods_ind]
            long_name = df_changed_methods["long_name"][df_changed_methods_ind]
            if ("/test/" not in file_path) and ("/tests/" not in file_path) and (".java" in file_path) and (file_path not in lst_changed_code_files_paths):
                if file_path not in lst_changed_files:
                    lst_changed_files.append(file_path)
                if long_name not in lst_changed_methods:
                    lst_changed_methods.append(long_name)
    return len(lst_changed_files), len(lst_changed_methods)

def analyze_csvs_at_high_level ():
    if os.path.exists(PATH_MUTANTS_ANALYSIS_DIR + "/" + HIGH_LEVEL_ANALYSIS_CSV_NAME):
        df_analysis_csv = pd.read_csv(PATH_MUTANTS_ANALYSIS_DIR + "/" + HIGH_LEVEL_ANALYSIS_CSV_NAME)
        return df_analysis_csv
    if os.path.exists(PATH_MUTANTS_ANALYSIS_DIR) is False:
        os.mkdir(PATH_MUTANTS_ANALYSIS_DIR)
    df_analysis_csv = pd.DataFrame(columns = ['vul_id', 'cve_id', 'changed_files_num', 'changed_methods_num', 'failed_tests_by_vuln', 'total_mutants', 'mutants_failing_tests_num', 'mutants_imitating_vuln_num', 'ochiai_avg'])
    for vul_id in os.listdir(PATH_MUTANTS_DIR):
        if os.path.isdir(PATH_MUTANTS_DIR + "/" + vul_id) is False:
            continue        
        dict_changed_files_with_path = {}
        lst_changed_code_files_paths = get_changed_code_files_paths (vul_id)
        changed_files_num, changed_methods_num = get_changed_code_files_and_methods_nums (vul_id)
        for changed_code_file_path in lst_changed_code_files_paths:
            arr_changed_code_file_path = changed_code_file_path.split("/")
            changed_code_file_name = arr_changed_code_file_path[len(arr_changed_code_file_path) - 1]
            if changed_code_file_name not in dict_changed_files_with_path:
                dict_changed_files_with_path[changed_code_file_name] = changed_code_file_path
        
        total_mutants = 0
        mutants_failing_tests_num = 0
        mutants_imitating_vuln_num = 0
        ochiai_sum = 0
        
        for changed_file in dict_changed_files_with_path:
            print("\nanalyzing vul_id:", vul_id, "| class:", changed_file)
            dir_class_mutants = changed_file.replace(".java","_mutants")
            path_mutants_dir_for_vulnerability = PATH_MUTANTS_DIR + "/" + vul_id + "/" + dir_class_mutants
            if os.path.exists(path_mutants_dir_for_vulnerability) is False:
                continue
            cve_id, dict_failed_tests_by_vuln = get_cve_id_and_failed_test_details(PATH_CODE_DIR, vul_id)
            failed_tests_by_vuln = len(dict_failed_tests_by_vuln)
            if len(dict_failed_tests_by_vuln) == 0:
                continue
            for mutant_id in os.listdir(path_mutants_dir_for_vulnerability):
                if os.path.isdir(path_mutants_dir_for_vulnerability + "/" + mutant_id) is False:
                    continue
                did_mutant_compile, did_tests_fail, imitates_vuln, ochiai, failed_tests_intersection, failed_tests, failures = \
                get_mutant_vulnerability_comparison_scores(vul_id, dir_class_mutants, mutant_id, dict_failed_tests_by_vuln)
                if did_mutant_compile == True:
                    total_mutants = total_mutants + 1
                    if did_tests_fail == True:
                        mutants_failing_tests_num = mutants_failing_tests_num + 1
                        if imitates_vuln == True:
                            mutants_imitating_vuln_num = mutants_imitating_vuln_num + 1
                    ochiai_sum = ochiai_sum + ochiai
        if total_mutants == 0:
            ochiai_avg = 0
        else:                
            ochiai_avg = ochiai_sum / total_mutants
        df_analysis_csv = df_analysis_csv.append({'vul_id' : vul_id, 
                                                  'cve_id' : cve_id,
                                                  'changed_files_num' : changed_files_num,
                                                  'changed_methods_num' : changed_methods_num,
                                                  'failed_tests_by_vuln' : failed_tests_by_vuln, 
                                                  'total_mutants': total_mutants, 
                                                  'mutants_failing_tests_num' : mutants_failing_tests_num, 
                                                  'mutants_imitating_vuln_num' : mutants_imitating_vuln_num, 
                                                  'ochiai_avg' : ochiai_avg}, ignore_index = True)
    print("writing", HIGH_LEVEL_ANALYSIS_CSV_NAME, "in", PATH_MUTANTS_ANALYSIS_DIR)
    df_analysis_csv.to_csv(PATH_MUTANTS_ANALYSIS_DIR + "/" + HIGH_LEVEL_ANALYSIS_CSV_NAME, index = False)
    return df_analysis_csv
    
def main():
    if CHECKOUT_AND_VERIFY is True:
        checkout_and_verify()
    
    if VERIFY_PATCHES is True:
        if os.path.exists(WASTE_PATCHES_DIR) is False:
            os.mkdir(WASTE_PATCHES_DIR)
        if os.path.exists(WASTE_FIXED_PATCHES_DIR) is False:
            os.mkdir(WASTE_FIXED_PATCHES_DIR)
            
        for vul_id in os.listdir(PATH_CODE_DIR):
            # verify extracted vulnerable files from commit IDs
            verification_successful = verify_extracted_vulnerable_files(vul_id)

            if verification_successful is True:
                # verify extracted fixed files from commit IDs
                verification_successful = verify_extracted_fixed_files(vul_id)

    if SEPARATE_OUT_FIXES_FOR_MUTATION_PURPOSE is True:
        if os.path.exists(PATH_FIXES_FOR_MUTATION_DIR) is False:
            os.mkdir(PATH_FIXES_FOR_MUTATION_DIR)

        for vul_id in os.listdir(PATH_PATCHES_DIR):
            # separate out fixed files for vul_id
            separate_out_fixed_files(vul_id)

    if EXECUTE_MUTANTS is True:
        if os.path.exists(PATH_MUTATED_CODE_DIR) is False:
            os.mkdir(PATH_MUTATED_CODE_DIR)
        path_completed_vul4j_ids_file = PATH_MUTANTS_DIR + "/" + COMPLETED_VUL4J_IDS_CSV_NAME
        for vul_id in os.listdir(PATH_MUTANTS_DIR):
            if os.path.isdir(PATH_MUTANTS_DIR + "/" + vul_id) is False:
                continue
            should_process_vul_id = True
            if os.path.exists(path_completed_vul4j_ids_file):
                df_completed_vul4j_ids = pd.read_csv(path_completed_vul4j_ids_file)
                for df_completed_vul4j_ids_ind in df_completed_vul4j_ids.index:
                    completed_vul_id = df_completed_vul4j_ids["vul_id"][df_completed_vul4j_ids_ind]
                    if completed_vul_id == vul_id:
                        should_process_vul_id = False
            if should_process_vul_id:        
                execute_mutants(vul_id)
                write_to_completed_vul4j_ids_file(path_completed_vul4j_ids_file, vul_id)
            else:
                print("\nalready processed", vul_id,"\n")
    
    if ANALYZE_MUTANTS_SIMULATIONS is True:
        df_analysis_csv = analyze_mutants_simulations_and_get_analysis()
        plot(df_analysis_csv)
    
    if CREATE_ML_DATASET is True:
        if os.path.exists(PATH_ML_DATASET_DIR) is False:
            os.mkdir(PATH_ML_DATASET_DIR)
        iterate_over_analysis_csv()
        
    if ANALYSE_AT_HIGH_LEVEL is True:
        analyze_csvs_at_high_level()

main()


# In[ ]:




