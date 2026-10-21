if __name__ == "__main__":
#-----------------------------------
    def parse_line(line: str) -> tuple[str, dict[str, str]]:
        ts, * pairs = line.split()
        return ts, dict(p.partition("=")[::2] for p in pairs)


    ts , kv = parse_line("2026-10-01T12:00:00Z lead=6f1c status=paa from=inquiry")

    # assertions - validations
    assert ts == "2026-10-01T12:00:00Z"
    assert kv == {"lead": "6f1c", "status": "paa", "from": "inquiry"}

    # maxsplit just the forst one
    assert "a=b=c".split('=', 1) == ["a", "b=c"] 

    rows = [("answered", 120.5), ("missed", 7.25), ("voicemail", 1234.0)]
    lines = [f"{name:<12}{value:>10.2f}" for name, value in rows]

    # string allignment
    lines = [f"{name:<12}{value:>10.2f}" for name, value in rows]
    assert lines[0] == "answered        120.50"
    assert lines[2] == "voicemail      1234.00"

    # numeric string comma and decimal formating
    assert f"{0.456:.1%}" == "45.6%" and f"{1234567:,}" == "1,234,567"

    # string expansion
    assert f"{'x':*^7}" == "***x***" and f"{42:05d}" == "00042"

#-----------------------------------
    print("All tests passed!")
