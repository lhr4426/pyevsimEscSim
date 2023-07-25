my_list = list(range(10))
print(my_list)

del my_list[0]
print(my_list)
# 예상값 : 1, 2, 3, 4, 5, 6, 7, 8, 9

del my_list[1]
print(my_list)
# 예상값 : 1, 3, 4, 5, 6, 7, 8, 9
