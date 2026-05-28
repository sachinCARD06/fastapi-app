import ulid

def generate_prefixed_id(prefix: str) -> str:
    return f"{prefix}-{str(ulid.new())}"