"""High quality module."""


def calculate(value_a: int, value_b: int) -> int:
    """Calculate sum of two values."""
    return value_a + value_b


def main() -> None:
    """Main function."""
    result = calculate(10, 20)
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
