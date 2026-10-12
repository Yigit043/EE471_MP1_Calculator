from custom_classes import Calculator

calc = Calculator()
s = calc.add(10, 5)
m = calc.multiply(s, 2)
r = calc.divide(m, 3)
print("(10 + 5) * 2 / 3 =", r)
print("current_val:", calc._current_val)