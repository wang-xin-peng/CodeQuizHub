"""
Code Assembler - Combines prelude, user solution, and driver into executable code.
"""

import json
from languages import get_language_config


class CodeAssembler:
    def __init__(self, language: str):
        self.language = language
        self.config = get_language_config(language)

    def assemble(
        self,
        prelude_code: str,
        user_code: str,
        driver_template: str,
        function_name: str,
        input_params: dict,
        parameters_json: list[dict],
        return_type: str = "int",
    ) -> str:
        """Assemble complete executable code from parts."""
        if driver_template:
            # Use custom driver template
            driver = driver_template
        else:
            # Generate default driver, passing user_code for calling-convention detection
            driver = self._generate_driver(function_name, input_params, parameters_json, user_code, return_type)

        return self.config["assemble"](prelude_code, user_code, driver)

    def _generate_driver(self, function_name: str, input_params: dict, parameters_json: list[dict], user_code: str = "", return_type: str = "int") -> str:
        """Generate a driver based on language that reads input and calls the solution."""
        if self.language == "python":
            return self._python_driver(function_name, input_params, parameters_json, user_code)
        elif self.language == "java":
            return self._java_driver(function_name, input_params, parameters_json)
        elif self.language == "cpp":
            return self._cpp_driver(function_name, input_params, parameters_json, user_code)
        elif self.language == "c":
            return self._c_driver(function_name, input_params, parameters_json, return_type)
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def _python_driver(self, function_name: str, input_params: dict, parameters_json: list[dict], user_code: str = "") -> str:
        param_names = [p["name"] for p in parameters_json]
        args = ", ".join(f'input_data["{name}"]' for name in param_names)

        # Auto-detect calling convention
        has_class_solution = "class Solution" in (user_code or "")
        if has_class_solution:
            call_line = f'sol = Solution()\n    result = sol.{function_name}({args})'
        else:
            call_line = f'result = {function_name}({args})'

        return f'''import json, sys

def main():
    input_data = json.loads(sys.argv[1])
    {call_line}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
'''

    def _java_driver(self, function_name: str, input_params: dict, parameters_json: list[dict]) -> str:
        # Build argument parsing and method call for Java
        parse_lines = []
        call_args = []
        for p in parameters_json:
            name = p["name"]
            ptype = p["type"]
            if ptype == "int":
                parse_lines.append(f'        int {name} = input.getInt("{name}");')
                call_args.append(name)
            elif ptype == "int[]":
                parse_lines.append(f'        org.json.JSONArray arr_{name} = input.getJSONArray("{name}");')
                parse_lines.append(f'        int[] {name} = new int[arr_{name}.length()];')
                parse_lines.append(f'        for(int i=0;i<arr_{name}.length();i++) {name}[i]=arr_{name}.getInt(i);')
                call_args.append(name)
            elif ptype == "String":
                parse_lines.append(f'        String {name} = input.getString("{name}");')
                call_args.append(name)
            else:
                parse_lines.append(f'        // TODO: parse {name} of type {ptype}')
                call_args.append(name)

        args_str = ", ".join(call_args)
        parse_block = "\n".join(parse_lines)

        return f'''class Main {{
    public static void main(String[] args) throws Exception {{
        JSONObject input = new JSONObject(args[0]);
{parse_block}
        Solution sol = new Solution();
        Object result = sol.{function_name}({args_str});
        if (result instanceof int[]) {{
            System.out.println(new JSONArray((int[])result).toString());
        }} else {{
            System.out.println(new JSONObject().put("result", result).get("result"));
        }}
    }}
}}
'''

    def _c_driver(self, function_name: str, input_params: dict, parameters_json: list[dict], return_type: str = "int") -> str:
        reads = []
        call_args = []
        cleanup = []
        output_size_var = None

        for p in parameters_json:
            name = p["name"]
            raw_type = (p.get("type") or "int").strip()

            if raw_type == "int":
                if name in input_params:
                    reads.append(f'    int {name} = cJSON_GetObjectItem(input, "{name}")->valueint;')
                else:
                    # Derived param (e.g., numsSize from array nums in input_params)
                    found = False
                    for ap in parameters_json:
                        if ap["name"] != name and ap["name"] in input_params and ap.get("type", "").strip() in ("int*", "int[]"):
                            base = ap["name"]
                            if name in (base + "Size", base + "_size", base + "Len", base + "_len"):
                                reads.append(f'    int {name} = {base}_size;')
                                found = True
                                break
                    if not found:
                        reads.append(f'    int {name} = 0; /* unhandled */')
                call_args.append(name)

            elif raw_type in ("int*", "int[]"):
                if name in input_params:
                    reads.append(f'    cJSON *{name}_json = cJSON_GetObjectItem(input, "{name}");')
                    reads.append(f'    int {name}_size = cJSON_GetArraySize({name}_json);')
                    reads.append(f'    int* {name} = (int*)malloc({name}_size * sizeof(int));')
                    reads.append(f'    for (int i = 0; i < {name}_size; i++) {{')
                    reads.append(f'        {name}[i] = cJSON_GetArrayItem({name}_json, i)->valueint;')
                    reads.append(f'    }}')
                    call_args.append(name)
                    cleanup.append(f'    free({name});')
                else:
                    # Output parameter (e.g., int* returnSize)
                    reads.append(f'    int {name}_val;')
                    call_args.append(f'&{name}_val')
                    output_size_var = f'{name}_val'

            elif raw_type in ("char*", "char[]", "String", "str"):
                reads.append(f'    char* {name} = cJSON_GetObjectItem(input, "{name}")->valuestring;')
                call_args.append(name)

            elif raw_type in ("int**", "int[][]"):
                reads.append(f'    cJSON *{name}_json = cJSON_GetObjectItem(input, "{name}");')
                reads.append(f'    int {name}_rows = cJSON_GetArraySize({name}_json);')
                reads.append(f'    int** {name} = (int**)malloc({name}_rows * sizeof(int*));')
                reads.append(f'    for (int i = 0; i < {name}_rows; i++) {{')
                reads.append(f'        cJSON *row = cJSON_GetArrayItem({name}_json, i);')
                reads.append(f'        int cols = cJSON_GetArraySize(row);')
                reads.append(f'        {name}[i] = (int*)malloc(cols * sizeof(int));')
                reads.append(f'        for (int j = 0; j < cols; j++) {{')
                reads.append(f'            {name}[i][j] = cJSON_GetArrayItem(row, j)->valueint;')
                reads.append(f'        }}')
                reads.append(f'    }}')
                call_args.append(name)
                cleanup.append(f'    for (int i = 0; i < {name}_rows; i++) free({name}[i]);')
                cleanup.append(f'    free({name});')

            elif raw_type in ("float", "double"):
                reads.append(f'    {raw_type} {name} = cJSON_GetObjectItem(input, "{name}")->valuedouble;')
                call_args.append(name)

            elif raw_type == "bool":
                reads.append(f'    int {name} = cJSON_GetObjectItem(input, "{name}")->valueint;')
                call_args.append(name)

            else:
                reads.append(f'    // TODO: parse {name} of type {raw_type}')
                call_args.append(name)

        read_block = "\n".join(reads)
        args_str = ", ".join(call_args)

        ret = (return_type or "int").strip()

        if ret == "void":
            output_block = f'    {function_name}({args_str});'
        elif ret == "int":
            output_block = f'''    int result = {function_name}({args_str});
    printf("%d", result);'''
        elif ret == "bool":
            output_block = f'''    int result = {function_name}({args_str});
    printf("%s", result ? "true" : "false");'''
        elif ret in ("int*", "int[]"):
            if output_size_var:
                output_block = f'''    int* result = {function_name}({args_str});
    if (result != NULL && {output_size_var} > 0) {{
        printf("[");
        for (int i = 0; i < {output_size_var}; i++) {{
            printf("%d%s", result[i], i < {output_size_var} - 1 ? "," : "");
        }}
        printf("]");
    }} else {{
        printf("[]");
    }}'''
                cleanup.append('    if (result) free(result);')
            else:
                output_block = f'''    int* result = {function_name}({args_str});
    if (result != NULL) {{
        fprintf(stderr, "ERROR: int* return type requires a returnSize parameter in the function signature for proper array output");
        free(result);
        return 1;
    }} else {{
        printf("[]");
    }}'''
        elif ret in ("char*", "char[]"):
            output_block = f'''    char* result = {function_name}({args_str});
    printf("%s", result != NULL ? result : "null");'''
        elif ret in ("float", "double"):
            output_block = f'''    {ret} result = {function_name}({args_str});
    printf("%g", result);'''
        elif ret in ("int**", "int[][]"):
            output_block = f'''    // TODO: 2D array return printing
    int** result = {function_name}({args_str});
    printf("[]");
    free(result);'''
        else:
            output_block = f'''    // TODO: handle return type {ret}
    {function_name}({args_str});'''

        cleanup_block = "\n".join(cleanup) if cleanup else "    /* no cleanup */"

        return f'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "cJSON.h"

int main(int argc, char *argv[]) {{
    if (argc < 2) return 1;
    cJSON *input = cJSON_Parse(argv[1]);
    if (!input) return 1;

{read_block}

{output_block}

{cleanup_block}

    cJSON_Delete(input);
    return 0;
}}
'''

    def _cpp_driver(self, function_name: str, input_params: dict, parameters_json: list[dict], user_code: str) -> str:
        """Generate a C++ driver using nlohmann/json for parsing.

        Auto-detects whether the user code wraps the solution in
        ``class Solution {{ ... }}``.  If it does, invokes via
        ``Solution sol; sol.func(...)``, otherwise calls the standalone
        function directly.
        """
        reads = []
        call_args = []
        for p in parameters_json:
            name = p["name"]
            raw_type = p.get("type", "int")
            # Strip reference (&), const, and pointer (*) qualifiers for type matching
            ptype = raw_type.replace("&", "").replace("const", "").replace("*", "").replace(" ", "")
            if ptype == "int":
                reads.append(f'    int {name} = input["{name}"];')
                call_args.append(name)
            elif ptype in ("int[]", "vector<int>"):
                reads.append(f'    vector<int> {name} = input["{name}"].get<vector<int>>();')
                call_args.append(name)
            elif ptype in ("string", "String"):
                reads.append(f'    string {name} = input["{name}"];')
                call_args.append(name)
            elif ptype == "vector<vector<int>>":
                reads.append(f'    auto {name} = input["{name}"].get<vector<vector<int>>>();')
                call_args.append(name)
            else:
                reads.append(f'    auto {name} = input["{name}"];')
                call_args.append(name)

        read_block = "\n".join(reads)
        args_str = ", ".join(call_args)

        # Auto-detect calling convention based on user code
        has_class_solution = "class Solution" in (user_code or "")
        if has_class_solution:
            call_line = f'    Solution sol;\n    auto result = sol.{function_name}({args_str});'
        else:
            call_line = f'    auto result = {function_name}({args_str});'

        return f'''#include <nlohmann/json.hpp>

using json = nlohmann::json;

int main(int argc, char* argv[]) {{
    if (argc < 2) return 1;
    json input = json::parse(argv[1]);

{read_block}

{call_line}
    cout << json(result).dump() << endl;
    return 0;
}}
'''
