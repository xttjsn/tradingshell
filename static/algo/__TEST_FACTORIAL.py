def gen():
    def factorial(n):
        if n < 2: yield n
        else:
            yield n
            yield from factorial(n - 1)
    return factorial(10)

    
