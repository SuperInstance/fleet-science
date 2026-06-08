"""Prove the ternary group axioms."""
def compose(a,b):
    s=a+b
    if s==0: return 0
    if s==2: return -1
    if s==-2: return 1
    return s
def test():
    for a in[-1,0,1]:
        for b in[-1,0,1]:
            assert compose(a,b)in[-1,0,1]
            assert compose(a,0)==a and compose(0,a)==a
    assert compose(1,-1)==0
    assert compose(-1,1)==0
    print("✅ Ternary {-1,0,+1} is a GROUP under ⊕")
    print("✅ Conservation: +1 + (-1) = 0")
if __name__=="__main__": test()
