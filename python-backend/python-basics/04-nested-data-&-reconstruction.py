def asserts():
    
    # recirsive data flattening
    def flatten(d: dict, prefix: str = "") -> dict:
        out = {}
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                out |= flatten(v, key)
            else:
                out[key] = v
        return out 

    # recursive data unflattenings
    def unflatten(flat:dict) -> dict:
        root: dict = {}
        for path, value in flat.items():
            *parents, leaf = path.split(".")
            node = root
            for p in parents:
                node = node.setdefault(p, {})
            node[leaf] = value
        return root

    nested = {"a": {"b": 1, "c": {"d": 2}}, "e": 3}
    flat = flatten(nested)
    assert flat == {"a.b": 1, "a.c.d": 2, "e": 3}
    assert unflatten(flat) == nested
    assert flatten({}) == {}


if __name__ == "__main__":
    asserts()
    print("All tests passed")