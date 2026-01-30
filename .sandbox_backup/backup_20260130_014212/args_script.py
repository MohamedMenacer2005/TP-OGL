
import sys
print(f"Script name: {sys.argv[0]}")
if len(sys.argv) > 1:
    print(f"Arguments: {sys.argv[1:]}")
    print(f"Sum: {sum(int(x) for x in sys.argv[1:])}")
