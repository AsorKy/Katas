def asserts():
    from operator import itemgetter

    RANK = {"critical": 0, "warning": 1, "info": 2}
    leads = [("Ana", "warning", 3), ("Bea", "critical", 1), ("Caro", "warning", 5),
             ("Dani", "critical", 1), ("Eli", "info", 9)]

    ordered = sorted(leads, key=lambda r: (RANK[r[1]], -r[2], r[0]))
    assert [r[0] for r in ordered] == ["Bea", "Dani", "Caro", "Ana", "Eli"]

    by_days = sorted(leads, key=itemgetter(2), reverse=True)
    assert by_days[0][0] == "Eli"

    # double step sorting
    step1 = sorted(leads, key=itemgetter(0))
    step2 = sorted(step1, key=lambda r: RANK[r[1]])
    assert [r[0] for r in step2][:2] == ["Bea", "Dani"]


    words = ["banana", "Apple", "cherry"]
    assert sorted(words) == ["Apple", "banana", "cherry"]
    assert sorted(words, key=len)[0] == "Apple"
    assert max(leads, key=itemgetter(2))[0] == "Eli" and min(leads, key=itemgetter(2))[2] == 1
 

if __name__ == "__main__":
    asserts()
    print("All tests passed")

