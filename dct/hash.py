import hashlib


def hash_string(input_string: str, algorithm: str = "md5") -> str:
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(input_string.encode("utf-8"))
    return hash_obj.hexdigest()
