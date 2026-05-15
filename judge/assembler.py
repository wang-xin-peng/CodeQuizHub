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
    ) -> str:
        """Assemble complete executable code from parts."""
        if driver_template:
            # Use custom driver template
            driver = driver_template
        else:
            # Generate default driver
            driver = self._generate_driver(function_name, input_params, parameters_json)

        return self.config["assemble"](prelude_code, user_code, driver)

    def _generate_driver(self, function_name: str, input_params: dict, parameters_json: list[dict]) -> str:
        """Generate a driver based on language that reads input and calls the solution."""
        if self.language == "python":
            return self._python_driver(function_name, input_params, parameters_json)
        elif self.language == "java":
            return self._java_driver(function_name, input_params, parameters_json)
        elif self.language in ("c", "cpp"):
            return self._c_driver(function_name, input_params, parameters_json)
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def _python_driver(self, function_name: str, input_params: dict, parameters_json: list[dict]) -> str:
        param_names = [p["name"] for p in parameters_json]
        args = ", ".join(f'input_data["{name}"]' for name in param_names)

        return f'''import json, sys

def main():
    input_data = json.loads(sys.argv[1])
    result = {function_name}({args})
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

        return f'''import org.json.*;

public class Main {{
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

    def _c_driver(self, function_name: str, input_params: dict, parameters_json: list[dict]) -> str:
        # Simplified C driver - complex types would need more handling
        return f'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "cJSON.h"

int main(int argc, char *argv[]) {{
    if (argc < 2) return 1;
    cJSON *input = cJSON_Parse(argv[1]);
    if (!input) return 1;

    // Call solution function - this is generated per problem
    // For complex types, custom driver_template should be provided
    cJSON_Delete(input);
    return 0;
}}
'''
