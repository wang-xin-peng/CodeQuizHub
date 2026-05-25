def countPrimes(n: int) -> int:
    count = 0
    for i in range(2, n):
        if isPrime(i):
            count += 1
    return count
