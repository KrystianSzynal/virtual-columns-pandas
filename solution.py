import ast
import operator
import re
import pandas as pd

_VALID_LABEL_RE = re.compile(r"^[a-zA-Z_]+$")
_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
}


def _is_valid_label(label: object) -> bool:
    return isinstance(label, str) and bool(_VALID_LABEL_RE.fullmatch(label))


def add_virtual_column(
    df: pd.DataFrame, role: str, new_column: str
) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame([])
    if not isinstance(role, str) or not role.strip():
        return pd.DataFrame([])
    if not _is_valid_label(new_column):
        return pd.DataFrame([])
    if not all(_is_valid_label(col) for col in df.columns):
        return pd.DataFrame([])

    try:
        tree = ast.parse(role.strip(), mode="eval")
    except SyntaxError:
        return pd.DataFrame([])

    def _eval_node(node: ast.AST) -> pd.Series:
        if isinstance(node, ast.Name):
            col_name = node.id
            if not _is_valid_label(col_name) or col_name not in df.columns:
                raise ValueError(f"Invalid or missing column: {col_name}")
            if not pd.api.types.is_numeric_dtype(df[col_name]):
                raise TypeError(f"Non-numeric column: {col_name}")
            return df[col_name]
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            return _ALLOWED_OPS[type(node.op)](left, right)
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")

    try:
        computed = _eval_node(tree.body)
    except Exception:
        return pd.DataFrame([])

    result = df.copy()
    result[new_column] = computed
    return result