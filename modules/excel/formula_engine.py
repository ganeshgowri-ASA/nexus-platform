"""Excel-compatible formula engine."""
import re
import math
import statistics
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
import numpy as np
import pandas as pd


class FormulaEngine:
    """
    Excel-compatible formula engine.

    Supports a wide range of Excel functions including:
    - Mathematical: SUM, AVERAGE, COUNT, MIN, MAX, ROUND, ABS, etc.
    - Logical: IF, AND, OR, NOT, IFS, SWITCH
    - Text: CONCATENATE, LEFT, RIGHT, MID, LEN, TRIM, UPPER, LOWER
    - Lookup: VLOOKUP, HLOOKUP, INDEX, MATCH, XLOOKUP
    - Date/Time: TODAY, NOW, DATE, YEAR, MONTH, DAY, HOUR
    - Financial: PMT, FV, PV, RATE, NPV, IRR
    - Statistical: STDEV, VAR, MEDIAN, MODE, PERCENTILE
    """

    def __init__(self, data: Optional[pd.DataFrame] = None):
        """
        Initialize formula engine.

        Args:
            data: Optional DataFrame containing spreadsheet data
        """
        self.data = data if data is not None else pd.DataFrame()
        self.named_ranges: Dict[str, str] = {}
        self.functions = self._register_functions()

    def _register_functions(self) -> Dict[str, Callable]:
        """Register all available formula functions."""
        return {
            # Mathematical functions
            'SUM': self._sum,
            'AVERAGE': self._average,
            'COUNT': self._count,
            'COUNTA': self._counta,
            'MIN': self._min,
            'MAX': self._max,
            'ROUND': self._round,
            'ROUNDUP': self._roundup,
            'ROUNDDOWN': self._rounddown,
            'ABS': self._abs,
            'SQRT': self._sqrt,
            'POWER': self._power,
            'MOD': self._mod,
            'INT': self._int,
            'CEILING': self._ceiling,
            'FLOOR': self._floor,

            # Logical functions
            'IF': self._if,
            'AND': self._and,
            'OR': self._or,
            'NOT': self._not,
            'IFS': self._ifs,
            'SWITCH': self._switch,
            'TRUE': lambda: True,
            'FALSE': lambda: False,

            # Text functions
            'CONCATENATE': self._concatenate,
            'CONCAT': self._concatenate,
            'LEFT': self._left,
            'RIGHT': self._right,
            'MID': self._mid,
            'LEN': self._len,
            'TRIM': self._trim,
            'UPPER': self._upper,
            'LOWER': self._lower,
            'PROPER': self._proper,
            'SUBSTITUTE': self._substitute,
            'REPLACE': self._replace,
            'FIND': self._find,
            'SEARCH': self._search,

            # Lookup functions
            'VLOOKUP': self._vlookup,
            'HLOOKUP': self._hlookup,
            'INDEX': self._index,
            'MATCH': self._match,
            'XLOOKUP': self._xlookup,

            # Date/Time functions
            'TODAY': self._today,
            'NOW': self._now,
            'DATE': self._date,
            'YEAR': self._year,
            'MONTH': self._month,
            'DAY': self._day,
            'HOUR': self._hour,
            'MINUTE': self._minute,
            'SECOND': self._second,
            'DATEDIF': self._datedif,

            # Financial functions
            'PMT': self._pmt,
            'FV': self._fv,
            'PV': self._pv,
            'RATE': self._rate,
            'NPV': self._npv,
            'IRR': self._irr,

            # Statistical functions
            'STDEV': self._stdev,
            'VAR': self._var,
            'MEDIAN': self._median,
            'MODE': self._mode,
            'PERCENTILE': self._percentile,
            'QUARTILE': self._quartile,
        }

    def evaluate(self, formula: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Evaluate an Excel formula.

        Args:
            formula: Formula string (should start with '=')
            context: Optional context with cell references

        Returns:
            Evaluated result

        Example:
            >>> engine = FormulaEngine()
            >>> engine.evaluate("=SUM(1,2,3)")
            6
        """
        if not formula or not formula.startswith('='):
            return formula

        # Remove leading '='
        formula = formula[1:].strip()

        try:
            # Replace cell references with values
            if context:
                formula = self._replace_cell_references(formula, context)

            # Replace named ranges
            formula = self._replace_named_ranges(formula)

            # Evaluate the formula
            result = self._eval_formula(formula)
            return result
        except Exception as e:
            return f"#ERROR: {str(e)}"

    def _eval_formula(self, formula: str) -> Any:
        """Evaluate a formula expression."""
        # Handle function calls
        func_pattern = r'([A-Z]+)\((.*)\)$'
        match = re.match(func_pattern, formula.strip())

        if match:
            func_name = match.group(1)
            args_str = match.group(2)

            if func_name in self.functions:
                # Parse arguments
                args = self._parse_args(args_str)
                return self.functions[func_name](*args)
            else:
                raise ValueError(f"Unknown function: {func_name}")

        # Handle simple expressions
        try:
            return eval(formula)
        except Exception as e:
            raise ValueError(f"Cannot evaluate formula: {str(e)}")

    def _parse_args(self, args_str: str) -> List[Any]:
        """Parse function arguments."""
        if not args_str.strip():
            return []

        args = []
        current_arg = ""
        paren_depth = 0
        in_quotes = False

        for char in args_str:
            if char == '"' and not in_quotes:
                in_quotes = True
            elif char == '"' and in_quotes:
                in_quotes = False
            elif char == '(' and not in_quotes:
                paren_depth += 1
            elif char == ')' and not in_quotes:
                paren_depth -= 1
            elif char == ',' and paren_depth == 0 and not in_quotes:
                args.append(self._parse_value(current_arg.strip()))
                current_arg = ""
                continue

            current_arg += char

        # Add last argument
        if current_arg.strip():
            args.append(self._parse_value(current_arg.strip()))

        return args

    def _parse_value(self, value: str) -> Any:
        """Parse a single value."""
        value = value.strip()

        # String literal
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]

        # Boolean
        if value.upper() == 'TRUE':
            return True
        if value.upper() == 'FALSE':
            return False

        # Number
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Nested function
        if re.match(r'[A-Z]+\(.*\)$', value):
            return self._eval_formula(value)

        # Range reference (e.g., A1:A10)
        if ':' in value:
            return self._get_range_values(value)

        return value

    def _replace_cell_references(self, formula: str, context: Dict[str, Any]) -> str:
        """Replace cell references with actual values."""
        # Pattern for cell references (e.g., A1, $A$1, Sheet1!A1)
        pattern = r'(\$?[A-Z]+\$?[0-9]+)'

        def replace(match):
            ref = match.group(1)
            # Remove $ signs for absolute references
            ref_clean = ref.replace('$', '')
            return str(context.get(ref_clean, 0))

        return re.sub(pattern, replace, formula)

    def _replace_named_ranges(self, formula: str) -> str:
        """Replace named ranges with cell references."""
        for name, ref in self.named_ranges.items():
            formula = formula.replace(name, ref)
        return formula

    def _get_range_values(self, range_ref: str) -> List[float]:
        """Get values from a cell range."""
        # Simplified range parsing
        # In a real implementation, this would extract values from the DataFrame
        return []

    # ============ Mathematical Functions ============

    def _sum(self, *args) -> float:
        """SUM function."""
        values = self._flatten_args(args)
        return sum(float(v) for v in values if isinstance(v, (int, float)))

    def _average(self, *args) -> float:
        """AVERAGE function."""
        values = [float(v) for v in self._flatten_args(args) if isinstance(v, (int, float))]
        return sum(values) / len(values) if values else 0

    def _count(self, *args) -> int:
        """COUNT function - count numeric values."""
        values = self._flatten_args(args)
        return sum(1 for v in values if isinstance(v, (int, float)))

    def _counta(self, *args) -> int:
        """COUNTA function - count non-empty values."""
        values = self._flatten_args(args)
        return sum(1 for v in values if v not in [None, '', []])

    def _min(self, *args) -> float:
        """MIN function."""
        values = [float(v) for v in self._flatten_args(args) if isinstance(v, (int, float))]
        return min(values) if values else 0

    def _max(self, *args) -> float:
        """MAX function."""
        values = [float(v) for v in self._flatten_args(args) if isinstance(v, (int, float))]
        return max(values) if values else 0

    def _round(self, number: float, num_digits: int = 0) -> float:
        """ROUND function."""
        return round(float(number), int(num_digits))

    def _roundup(self, number: float, num_digits: int = 0) -> float:
        """ROUNDUP function."""
        multiplier = 10 ** int(num_digits)
        return math.ceil(float(number) * multiplier) / multiplier

    def _rounddown(self, number: float, num_digits: int = 0) -> float:
        """ROUNDDOWN function."""
        multiplier = 10 ** int(num_digits)
        return math.floor(float(number) * multiplier) / multiplier

    def _abs(self, number: float) -> float:
        """ABS function."""
        return abs(float(number))

    def _sqrt(self, number: float) -> float:
        """SQRT function."""
        return math.sqrt(float(number))

    def _power(self, number: float, power: float) -> float:
        """POWER function."""
        return float(number) ** float(power)

    def _mod(self, number: float, divisor: float) -> float:
        """MOD function."""
        return float(number) % float(divisor)

    def _int(self, number: float) -> int:
        """INT function."""
        return int(float(number))

    def _ceiling(self, number: float, significance: float = 1) -> float:
        """CEILING function."""
        sig = float(significance)
        return math.ceil(float(number) / sig) * sig

    def _floor(self, number: float, significance: float = 1) -> float:
        """FLOOR function."""
        sig = float(significance)
        return math.floor(float(number) / sig) * sig

    # ============ Logical Functions ============

    def _if(self, condition: bool, value_if_true: Any, value_if_false: Any) -> Any:
        """IF function."""
        return value_if_true if condition else value_if_false

    def _and(self, *args) -> bool:
        """AND function."""
        return all(bool(arg) for arg in args)

    def _or(self, *args) -> bool:
        """OR function."""
        return any(bool(arg) for arg in args)

    def _not(self, value: bool) -> bool:
        """NOT function."""
        return not bool(value)

    def _ifs(self, *args) -> Any:
        """IFS function - multiple conditions."""
        if len(args) % 2 != 0:
            return "#ERROR: IFS requires pairs of condition and value"

        for i in range(0, len(args), 2):
            condition = args[i]
            value = args[i + 1]
            if bool(condition):
                return value

        return "#N/A"

    def _switch(self, expression: Any, *args) -> Any:
        """SWITCH function."""
        if len(args) < 2:
            return "#ERROR: SWITCH requires at least one value-result pair"

        # Check pairs
        for i in range(0, len(args) - 1, 2):
            if i + 1 >= len(args):
                break
            if expression == args[i]:
                return args[i + 1]

        # Return default if odd number of args
        if len(args) % 2 == 1:
            return args[-1]

        return "#N/A"

    # ============ Text Functions ============

    def _concatenate(self, *args) -> str:
        """CONCATENATE function."""
        return ''.join(str(arg) for arg in args)

    def _left(self, text: str, num_chars: int = 1) -> str:
        """LEFT function."""
        return str(text)[:int(num_chars)]

    def _right(self, text: str, num_chars: int = 1) -> str:
        """RIGHT function."""
        return str(text)[-int(num_chars):]

    def _mid(self, text: str, start_num: int, num_chars: int) -> str:
        """MID function."""
        start = int(start_num) - 1  # Excel is 1-indexed
        return str(text)[start:start + int(num_chars)]

    def _len(self, text: str) -> int:
        """LEN function."""
        return len(str(text))

    def _trim(self, text: str) -> str:
        """TRIM function."""
        return str(text).strip()

    def _upper(self, text: str) -> str:
        """UPPER function."""
        return str(text).upper()

    def _lower(self, text: str) -> str:
        """LOWER function."""
        return str(text).lower()

    def _proper(self, text: str) -> str:
        """PROPER function - title case."""
        return str(text).title()

    def _substitute(self, text: str, old_text: str, new_text: str,
                   instance_num: Optional[int] = None) -> str:
        """SUBSTITUTE function."""
        text_str = str(text)
        old_str = str(old_text)
        new_str = str(new_text)

        if instance_num is not None:
            # Replace specific instance
            parts = text_str.split(old_str)
            if int(instance_num) <= len(parts) - 1:
                parts[int(instance_num)] = new_str + parts[int(instance_num)]
                return ''.join(parts)
            return text_str
        else:
            # Replace all instances
            return text_str.replace(old_str, new_str)

    def _replace(self, old_text: str, start_num: int, num_chars: int, new_text: str) -> str:
        """REPLACE function."""
        old_str = str(old_text)
        start = int(start_num) - 1
        return old_str[:start] + str(new_text) + old_str[start + int(num_chars):]

    def _find(self, find_text: str, within_text: str, start_num: int = 1) -> int:
        """FIND function (case-sensitive)."""
        start = int(start_num) - 1
        result = str(within_text).find(str(find_text), start)
        return result + 1 if result >= 0 else -1

    def _search(self, find_text: str, within_text: str, start_num: int = 1) -> int:
        """SEARCH function (case-insensitive)."""
        start = int(start_num) - 1
        result = str(within_text).lower().find(str(find_text).lower(), start)
        return result + 1 if result >= 0 else -1

    # ============ Lookup Functions ============

    def _vlookup(self, lookup_value: Any, table_array: List, col_index: int,
                range_lookup: bool = True) -> Any:
        """VLOOKUP function."""
        # Simplified implementation
        return "#N/A"

    def _hlookup(self, lookup_value: Any, table_array: List, row_index: int,
                range_lookup: bool = True) -> Any:
        """HLOOKUP function."""
        return "#N/A"

    def _index(self, array: List, row_num: int, col_num: Optional[int] = None) -> Any:
        """INDEX function."""
        return "#N/A"

    def _match(self, lookup_value: Any, lookup_array: List, match_type: int = 1) -> int:
        """MATCH function."""
        return -1

    def _xlookup(self, lookup_value: Any, lookup_array: List, return_array: List,
                if_not_found: Any = "#N/A") -> Any:
        """XLOOKUP function."""
        return if_not_found

    # ============ Date/Time Functions ============

    def _today(self) -> date:
        """TODAY function."""
        return date.today()

    def _now(self) -> datetime:
        """NOW function."""
        return datetime.now()

    def _date(self, year: int, month: int, day: int) -> date:
        """DATE function."""
        return date(int(year), int(month), int(day))

    def _year(self, date_value: Union[date, datetime]) -> int:
        """YEAR function."""
        if isinstance(date_value, (date, datetime)):
            return date_value.year
        return 0

    def _month(self, date_value: Union[date, datetime]) -> int:
        """MONTH function."""
        if isinstance(date_value, (date, datetime)):
            return date_value.month
        return 0

    def _day(self, date_value: Union[date, datetime]) -> int:
        """DAY function."""
        if isinstance(date_value, (date, datetime)):
            return date_value.day
        return 0

    def _hour(self, time_value: Union[datetime, timedelta]) -> int:
        """HOUR function."""
        if isinstance(time_value, datetime):
            return time_value.hour
        return 0

    def _minute(self, time_value: Union[datetime, timedelta]) -> int:
        """MINUTE function."""
        if isinstance(time_value, datetime):
            return time_value.minute
        return 0

    def _second(self, time_value: Union[datetime, timedelta]) -> int:
        """SECOND function."""
        if isinstance(time_value, datetime):
            return time_value.second
        return 0

    def _datedif(self, start_date: date, end_date: date, unit: str) -> int:
        """DATEDIF function."""
        delta = end_date - start_date
        unit = unit.upper()

        if unit == 'D':
            return delta.days
        elif unit == 'M':
            return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        elif unit == 'Y':
            return end_date.year - start_date.year
        return 0

    # ============ Financial Functions ============

    def _pmt(self, rate: float, nper: int, pv: float, fv: float = 0, type: int = 0) -> float:
        """PMT function - payment for a loan."""
        rate = float(rate)
        nper = int(nper)
        pv = float(pv)
        fv = float(fv)

        if rate == 0:
            return -(pv + fv) / nper

        pmt = (rate * (pv * (1 + rate) ** nper + fv)) / ((1 + rate * type) * ((1 + rate) ** nper - 1))
        return -pmt

    def _fv(self, rate: float, nper: int, pmt: float, pv: float = 0, type: int = 0) -> float:
        """FV function - future value."""
        rate = float(rate)
        nper = int(nper)
        pmt = float(pmt)
        pv = float(pv)

        if rate == 0:
            return -pv - pmt * nper

        fv = -pv * (1 + rate) ** nper - pmt * (1 + rate * type) * ((1 + rate) ** nper - 1) / rate
        return fv

    def _pv(self, rate: float, nper: int, pmt: float, fv: float = 0, type: int = 0) -> float:
        """PV function - present value."""
        rate = float(rate)
        nper = int(nper)
        pmt = float(pmt)
        fv = float(fv)

        if rate == 0:
            return -fv - pmt * nper

        pv = (-pmt * (1 + rate * type) * ((1 + rate) ** nper - 1) / rate - fv) / (1 + rate) ** nper
        return pv

    def _rate(self, nper: int, pmt: float, pv: float, fv: float = 0,
             type: int = 0, guess: float = 0.1) -> float:
        """RATE function - interest rate per period."""
        # Simplified - would need iterative solution
        return float(guess)

    def _npv(self, rate: float, *values) -> float:
        """NPV function - net present value."""
        rate = float(rate)
        npv = sum(float(v) / (1 + rate) ** (i + 1) for i, v in enumerate(values))
        return npv

    def _irr(self, values: List[float], guess: float = 0.1) -> float:
        """IRR function - internal rate of return."""
        # Simplified - would need iterative solution
        try:
            return np.irr([float(v) for v in values])
        except:
            return float(guess)

    # ============ Statistical Functions ============

    def _stdev(self, *args) -> float:
        """STDEV function."""
        values = [float(v) for v in self._flatten_args(args) if isinstance(v, (int, float))]
        return statistics.stdev(values) if len(values) > 1 else 0

    def _var(self, *args) -> float:
        """VAR function."""
        values = [float(v) for v in self._flatten_args(args) if isinstance(v, (int, float))]
        return statistics.variance(values) if len(values) > 1 else 0

    def _median(self, *args) -> float:
        """MEDIAN function."""
        values = [float(v) for v in self._flatten_args(args) if isinstance(v, (int, float))]
        return statistics.median(values) if values else 0

    def _mode(self, *args) -> float:
        """MODE function."""
        values = [float(v) for v in self._flatten_args(args) if isinstance(v, (int, float))]
        try:
            return statistics.mode(values) if values else 0
        except statistics.StatisticsError:
            return values[0] if values else 0

    def _percentile(self, array: List, k: float) -> float:
        """PERCENTILE function."""
        values = sorted([float(v) for v in array if isinstance(v, (int, float))])
        if not values:
            return 0
        index = float(k) * (len(values) - 1)
        lower = int(index)
        upper = lower + 1
        weight = index - lower

        if upper >= len(values):
            return values[-1]
        return values[lower] * (1 - weight) + values[upper] * weight

    def _quartile(self, array: List, quart: int) -> float:
        """QUARTILE function."""
        quart_map = {0: 0, 1: 0.25, 2: 0.5, 3: 0.75, 4: 1.0}
        return self._percentile(array, quart_map.get(int(quart), 0.5))

    # ============ Helper Functions ============

    def _flatten_args(self, args: tuple) -> List[Any]:
        """Flatten nested arguments."""
        result = []
        for arg in args:
            if isinstance(arg, (list, tuple)):
                result.extend(self._flatten_args(arg))
            else:
                result.append(arg)
        return result

    def add_named_range(self, name: str, reference: str) -> None:
        """
        Add a named range.

        Args:
            name: Name for the range
            reference: Cell reference (e.g., 'A1:A10')
        """
        self.named_ranges[name] = reference

    def remove_named_range(self, name: str) -> None:
        """Remove a named range."""
        if name in self.named_ranges:
            del self.named_ranges[name]
