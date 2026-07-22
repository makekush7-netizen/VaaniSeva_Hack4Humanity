import ast, sys
try:
    with open("lambdas/call_handler/handler.py", encoding="utf-8") as f:
        ast.parse(f.read())
    print("SYNTAX OK")
    sys.exit(0)
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
    sys.exit(1)
