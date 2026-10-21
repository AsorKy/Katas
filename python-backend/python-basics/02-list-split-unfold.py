data = list(range(10))

def asserts():
    assert data == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    # firsts and lasts elements
    assert data[:3] == [0, 1, 2] and data[-3:] == [7, 8, 9]
    # each 2 numbers
    assert data[::2] == [0,2,4,6,8]
    # inverted list copy
    assert data[::-1] == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    assert data[::-1][:3] == [9, 8, 7]

    # list slicing never fails
    assert data[2:5] == [2,3,4] and data[8:100] == [8, 9]

    # superficial copy
    assert data[:] == data and data[:] is not data

    # first vs rest slicing
    first, *middle,  last = data
    assert first == 0 and last ==9 and middle == list(range(1,9))

    head, *rest = "a"
    assert head == "a" and rest == []

    # value swapping
    a, b = 1, 2
    a, b = b, a
    assert (a, b) == (2, 1)
    
    # zip and list comprehension
    stamps = [0, 3, 3, 10, 14]
    gaps = [y - x for x, y in zip(stamps, stamps[1:])]
    assert gaps == [3, 0, 7, 4]

    def blocks(seq, n):
        return [seq[i:i + n] for i in range(0, len(seq), n)]
    
    assert blocks(data, 4) == [[0,1,2,3], [4,5,6,7], [8, 9]]
    assert data[-1] == 9 and data[len(data) // 2] == 5

if __name__ == "__main__":
    asserts()
    print("All tests passed")
