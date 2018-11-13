class A():
    c1=1
    def __init__(self):
        self.b1 =2
        c=self.c1
        self._d =33
               
    def  get_d(self):
        return self._d
    d=property(get_d)
a=A()
print(a.d)
print(a.b1)

print(a.__dict__)

class C:
    def __init__(self):        
        self._x = 1
    def getx(self):        
        return self._x
    def setx(self, value):
	    self._x = value
    def delx(self):
	    del self._x
    #x = property(getx, setx, delx, "I'm the 'x' property.")
    x=property(getx)
    
a=C()

print(a.x)



print(a.__dict__)

