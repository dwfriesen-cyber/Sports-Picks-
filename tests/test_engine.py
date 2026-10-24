import unittest
from collections import defaultdict
from engine import weight,expected,predict
class Tests(unittest.TestCase):
 def test_weights(self):
  self.assertEqual(weight(10),.8);self.assertAlmostEqual(weight(25),.4);self.assertEqual(weight(40),0)
 def test_v1(self):
  h=defaultdict(list,{"A":[(3,2,30,20)]*3,"B":[(2,3,20,30)]*3})
  self.assertAlmostEqual(expected("A","B",h),3)
 def test_v6(self):
  h=defaultdict(list,{"A":[(3,2,30,20)]*3,"B":[(2,3,20,30)]*3})
  self.assertEqual(predict({"home":"A","away":"B"},h,defaultdict(float))["winner"],"A")
if __name__=="__main__":unittest.main()
