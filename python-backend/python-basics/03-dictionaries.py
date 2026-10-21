
def asserts():
    calls = [
        {"id": 1, "facility": "F1", "status": "answered"},
        {"id": 2, "facility": "F1", "status": "missed"},
        {"id": 3, "facility": "F2", "status": "missed"},
        {"id": 4, "facility": "F2", "status": "missed"},
    ]

    # unfolded count
    counts = {}
    for c in calls:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    assert counts == {"answered": 1, "missed": 3}

    by_fac = {}
    for c in calls:
        by_fac[c["facility"]] = by_fac.get(c["facility"], 0) + 1
    assert by_fac == {"F1":2, "F2":2}

    # using setdefault
    by_fac = {}
    for c in calls:
        by_fac.setdefault(c["facility"], []).append(c["id"])
    assert by_fac == {"F1": [1, 2], "F2": [3, 4]}

    # using defaultdict
    from collections import defaultdict
    by_fac = defaultdict(list)
    for c in calls:
        by_fac[c["facility"]].append(c["id"])

    assert dict(by_fac) == {"F1": [1, 2], "F2": [3, 4]}

    # key-value inversion
    inv = {v: k for k, v in {"a": 1, "b": 2}.items()}
    assert inv == {1: "a", 2: "b"}

    # dictionary fusion with right winner
    defaults, overrides = {"limit": 50, "offset": 0}, {"limit": 10}
    assert defaults | overrides == {"limit": 10, "offset": 0}
    assert {**defaults, **overrides} == {"limit": 10, "offset": 0}

    # reverse dictionary sorting
    ranked = dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))
    assert ranked == {"missed": 3, "answered": 1}
    assert list(ranked) == ["missed", "answered"]

    # nested unpack
    cfg = {"db": {"pool": {"size": 5}}}
    assert cfg.get("db", {}).get("pool", {}).get("size") == 5
    assert cfg.get("cache", {}).get("ttl", 60) == 60
    by_id = {c["id"]: c for c in calls}
    assert by_id[3]["facility"] == "F2" and 9 not in by_id
    for k, v in list(by_id.items())[:1]:
        assert k == 1 and v["status"] == "answered"

if __name__ == "__main__":
    asserts()
    print("All tests passed!")