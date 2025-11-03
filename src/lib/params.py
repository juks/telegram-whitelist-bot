"""
Parameters parsing class for handling named parameters and conditions
"""
import re


class Params:
    """
    Class for parsing named parameters from command line arguments
    Supports various parameter types including conditions with logical operators
    """
    
    @staticmethod
    def parse_condition(condition_str):
        """
        Parse condition string with operators =, !=, <, >, in, not in
        Examples:
        - column=5 -> {'operator': '=', 'value': 5}
        - column!=5 -> {'operator': '!=', 'value': 5}
        - column<10 -> {'operator': '<', 'value': 10}
        - column>10 -> {'operator': '>', 'value': 10}
        - column in (1,2,3,"foo") -> {'operator': 'in', 'value': [1, 2, 3, "foo"]}
        - column not in (1,2,3) -> {'operator': 'not in', 'value': [1, 2, 3]}
        
        Args:
            condition_str: Condition string to parse
            
        Returns:
            Dictionary with 'operator', 'value', and 'param' keys, or None if parsing fails
        """
        # Pattern for 'not in' (must be checked first, before 'in')
        not_in_match = re.match(r'^(.+?)\s+not\s+in\s+\((.+?)\)$', condition_str.strip())
        if not_in_match:
            param_name = not_in_match.group(1).strip()
            values_str = not_in_match.group(2).strip()
            # Parse values: split by comma and strip, convert to appropriate types
            values = []
            for v in values_str.split(','):
                v = v.strip().strip('"\'')
                # Try to parse as number, otherwise keep as string
                try:
                    if '.' in v:
                        values.append(float(v))
                    else:
                        values.append(int(v))
                except ValueError:
                    values.append(v)
            return {'operator': 'not in', 'value': values, 'param': param_name}
        
        # Pattern for 'in'
        in_match = re.match(r'^(.+?)\s+in\s+\((.+?)\)$', condition_str.strip())
        if in_match:
            param_name = in_match.group(1).strip()
            values_str = in_match.group(2).strip()
            # Parse values: split by comma and strip, convert to appropriate types
            values = []
            for v in values_str.split(','):
                v = v.strip().strip('"\'')
                # Try to parse as number, otherwise keep as string
                try:
                    if '.' in v:
                        values.append(float(v))
                    else:
                        values.append(int(v))
                except ValueError:
                    values.append(v)
            return {'operator': 'in', 'value': values, 'param': param_name}
        
        # Pattern for != (must be checked before =)
        ne_match = re.match(r'^(.+?)!=(.+)$', condition_str.strip())
        if ne_match:
            param_name = ne_match.group(1).strip()
            value_str = ne_match.group(2).strip().strip('"\'')
            # Try to convert to number
            try:
                if '.' in value_str:
                    value = float(value_str)
                else:
                    value = int(value_str)
            except ValueError:
                value = value_str
            return {'operator': '!=', 'value': value, 'param': param_name}
        
        # Pattern for <
        lt_match = re.match(r'^(.+?)<(.+)$', condition_str.strip())
        if lt_match:
            param_name = lt_match.group(1).strip()
            value_str = lt_match.group(2).strip().strip('"\'')
            try:
                if '.' in value_str:
                    value = float(value_str)
                else:
                    value = int(value_str)
            except ValueError:
                value = value_str
            return {'operator': '<', 'value': value, 'param': param_name}
        
        # Pattern for >
        gt_match = re.match(r'^(.+?)>(.+)$', condition_str.strip())
        if gt_match:
            param_name = gt_match.group(1).strip()
            value_str = gt_match.group(2).strip().strip('"\'')
            try:
                if '.' in value_str:
                    value = float(value_str)
                else:
                    value = int(value_str)
            except ValueError:
                value = value_str
            return {'operator': '>', 'value': value, 'param': param_name}
        
        # Pattern for = (must be checked last)
        eq_match = re.match(r'^(.+?)=(.+)$', condition_str.strip())
        if eq_match:
            param_name = eq_match.group(1).strip()
            value_str = eq_match.group(2).strip().strip('"\'')
            # Try to convert to number
            try:
                if '.' in value_str:
                    value = float(value_str)
                else:
                    value = int(value_str)
            except ValueError:
                value = value_str
            return {'operator': '=', 'value': value, 'param': param_name}
        
        # If no pattern matches, return None
        return None
    
    @staticmethod
    def check_condition(condition, value, lower_case: bool = False):
        """
        Check if a value matches the condition
        
        Args:
            condition: Dictionary returned by parse_condition with keys:
                - 'operator': one of '=', '!=', '<', '>', 'in', 'not in'
                - 'value': value to compare against
                - 'param': parameter name (not used in checking)
            value: Value to check against the condition
            lower_case: If True, normalize string comparisons to lower-case
        
        Returns:
            True if value matches the condition, False otherwise
        """
        if condition is None:
            return False

        operator = condition.get('operator')
        condition_value = condition.get('value')

        if operator is None or condition_value is None:
            return False
        
        # Try to convert value to the same type as condition_value for comparison
        # This handles cases where we compare numbers with strings that look like numbers
        try:
            # If condition_value is numeric, try to convert value to the same type
            if isinstance(condition_value, (int, float)):
                if isinstance(condition_value, float):
                    value = float(value)
                else:
                    # Try int first, fall back to float if decimal
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        value = float(value)
            elif isinstance(condition_value, str) and isinstance(value, (int, float)):
                # If condition is string but value is number, convert condition to number
                try:
                    if '.' in str(value):
                        condition_value = float(condition_value)
                        value = float(value)
                    else:
                        condition_value = int(condition_value)
                        value = int(value)
                except (ValueError, TypeError):
                    pass  # Keep as strings
        except (ValueError, TypeError):
            # If conversion fails, compare as strings
            pass

        # Normalize strings to lower-case if requested
        if lower_case:
            if isinstance(value, str):
                value = value.lower()
            if isinstance(condition_value, str):
                condition_value = condition_value.lower()
        
        # Check condition based on operator
        if operator == '=':
            return value == condition_value
        elif operator == '!=':
            return value != condition_value
        elif operator == '<':
            # For < and >, values should be comparable (numbers)
            try:
                return value < condition_value
            except TypeError:
                return False
        elif operator == '>':
            try:
                return value > condition_value
            except TypeError:
                return False
        elif operator == 'in':
            # condition_value should be a list
            if not isinstance(condition_value, list):
                return False
            # If lower_case, normalize string list items
            normalized_list = []
            if lower_case:
                for item in condition_value:
                    normalized_list.append(item.lower() if isinstance(item, str) else item)
            else:
                normalized_list = condition_value
            # Try to convert value to match types in the list
            for item in condition_value:
                try:
                    if isinstance(item, (int, float)) and isinstance(value, str):
                        # Try to convert value to number
                        if isinstance(item, float):
                            test_value = float(value)
                        else:
                            test_value = int(value)
                        if test_value == item:
                            return True
                    elif isinstance(item, str) and isinstance(value, (int, float)):
                        # Try to convert item to number
                        if '.' in item:
                            test_item = float(item)
                        else:
                            test_item = int(item)
                        if value == test_item:
                            return True
                except (ValueError, TypeError):
                    pass
            return value in normalized_list
        elif operator == 'not in':
            # condition_value should be a list
            if not isinstance(condition_value, list):
                return False
            # If lower_case, normalize string list items
            normalized_list = []
            if lower_case:
                for item in condition_value:
                    normalized_list.append(item.lower() if isinstance(item, str) else item)
            else:
                normalized_list = condition_value
            # Try to convert value to match types in the list
            for item in condition_value:
                try:
                    if isinstance(item, (int, float)) and isinstance(value, str):
                        # Try to convert value to number
                        if isinstance(item, float):
                            test_value = float(value)
                        else:
                            test_value = int(value)
                        if test_value == item:
                            return False
                    elif isinstance(item, str) and isinstance(value, (int, float)):
                        # Try to convert item to number
                        if '.' in item:
                            test_item = float(item)
                        else:
                            test_item = int(item)
                        if value == test_item:
                            return False
                except (ValueError, TypeError):
                    pass
            return value not in normalized_list
        else:
            return False
    
    @staticmethod
    def parse_params(args, params_config, check_missing=True, set_default=False):
        """
        Parse named parameters from args array in format parameter_name=parameter_value
        Uses params_config to determine supported parameters and their types
        
        Args:
            args: Array of command line arguments
            params_config: Dictionary defining parameter configurations with structure:
                {
                    'param_name': {
                        'type': type or 'condition',
                        'default': default_value  # optional
                    }
                }
        
        Returns:
            Dictionary with parsed parameter values
            
        Raises:
            Exception: If invalid condition format or missing required parameter
        """
        params = {}
        
        # Apply defaults first
        if set_default is not False:
            for param_name, param_config in params_config.items():
                if 'default' in param_config:
                    params[param_name] = param_config['default']
        
        # Parse named parameters from args
        for arg in args:
            if '=' in arg:
                parts = arg.split('=', 1)
                if len(parts) == 2:
                    param_name = parts[0].strip()
                    param_value = parts[1].strip()
                    
                    # Check if parameter is supported
                    if param_name not in params_config:
                        continue  # Skip unknown parameters
                    
                    param_config = params_config[param_name]
                    param_type = param_config.get('type')
                    
                    # Handle condition type specially
                    if param_type == 'condition':
                        condition = Params.parse_condition(param_value)
                        if condition:
                            params[param_name] = condition
                        else:
                            raise Exception(f'Invalid condition format: {param_value}')
                    # Handle int type
                    elif param_type == int:
                        try:
                            params[param_name] = int(param_value)
                        except ValueError:
                            raise Exception(f'Invalid integer value for parameter {param_name}: {param_value}')
                    # Handle str type (default)
                    else:
                        params[param_name] = param_value
        
        # Check required parameters (those without defaults)
        if check_missing:
            for param_name, param_config in params_config.items():
                if 'default' not in param_config and param_name not in params:
                    raise Exception(f'Required parameter {param_name} is missing')
        
        return params

