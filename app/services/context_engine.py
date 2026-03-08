
def vark_to_context(v, a, r, k):
    total = v + a + r + k
    if total == 0:
        return [0.25, 0.25, 0.25, 0.25]
    return [
        v / total,
        a / total,
        r / total,
        k / total
    ]
