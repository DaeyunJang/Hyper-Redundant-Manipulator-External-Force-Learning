import unittest
import numpy as np
from hrm_force.data import parse_timestamp,valid_endpoints,load_labels,split_endpoints,feature_spec

class DataTests(unittest.TestCase):
    def test_integer_timestamp_never_float(self):
        self.assertEqual(parse_timestamp('1790422169951056396'),(1790422169951056396,False))
        self.assertEqual(parse_timestamp('1.79041162535543E+018'),(1790411625355430000,True))
        with self.assertRaises(ValueError): parse_timestamp('NaN')
    def test_gap_and_rejected_row_break_windows(self):
        ts=np.array([0,10,20,30,40,100,110,120,130])
        ok=np.array([1,1,1,0,1,1,1,1,1],bool)
        ends,_=valid_endpoints(ok,ts,3)
        np.testing.assert_array_equal(ends,[2,7,8])
    def test_load_boundary_zero_negative_missing(self):
        thresholds=np.array([.0454,.0436,.0729])
        y=np.array([[0,0,0],thresholds,-thresholds,[0,0,-.073]])
        np.testing.assert_array_equal(load_labels(y),[0,0,0,1])
        with self.assertRaises(ValueError): load_labels([[np.nan,0,0]])
    def test_validation_windows_disjoint_and_purged(self):
        ts=np.arange(100)*100000000
        s={'ts':ts,'ends':np.arange(4,100)}
        cfg={'window_samples':5,'validation_fraction':.2,'validation_purge_seconds':.5}
        splits=split_endpoints(s,cfg)
        self.assertLess(ts[splits['train'][-1]],ts[80]-.5e9)
        self.assertGreater(ts[splits['val'][0]-4],ts[80]+.5e9)
    def test_dynamic_dimensions(self):
        self.assertEqual(len(feature_spec(['wire_length','loadcell_tension','relative_angle'])[0]),26)
        with self.assertRaises(ValueError): feature_spec(['relative_angle','relative_angle'])

if __name__=='__main__': unittest.main()
