def jan_to_asin(jan13):
    s = str(jan13)[3:12]
    a = 10
    c = 0
   
    for i in range(0, len(s)):
        c += int(s[i]) *(a-i)

    d = c % 11
    d = 11 - d 
    if d == 10:
        d = "X"
    return str(s) + str(d)

ASIN = jan_to_asin(9784774183619)