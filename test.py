
import random

def generate_code():
    list = ""
    # range(x)生成x个随机数的验证码
    for i in range(4):
        # 跟随循环生成一个0-4之间的随机数来决定生成的是大小写字母还是数字
        j = random.randrange(0, 4)
        # 随机产生的数字是1时，生成数字
        if j == 1:
            a = random.randrange(0, 10)
            list = list + str(a)
        # 随机产生的数字是2时，生成大写字母
        elif j == 2:
            a = chr(random.randrange(65, 91))
            list = list + a
        # 随机产生的数字是除了1和2时，生成小写字母
        else:
            a = chr(random.randrange(97, 127))
            list = list + a
    return list

print(generate_code())