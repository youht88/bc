import testGlobal as t
import testGlobal.a as ta
print (t.a,t.b)
t.a=3
t.b=4
print (t.a,t.b)
ta.a=9
print(ta)