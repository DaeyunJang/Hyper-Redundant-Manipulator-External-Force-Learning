import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import predict


class PredictionRootTests(unittest.TestCase):
    def test_replay_root_keeps_hash_checks_and_original_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            ck=Path(tmp)/'model/checkpoint.pt';ck.parent.mkdir()
            config={'data_root':'original','task':'body','window_samples':30}
            bundle={'config':config,'source_hashes':{'s':'expected'},'source_provenance':{'s':{'metadata_sha256':{},'timestamp_repair':None}},'stats':{},'feature_columns':['x']}
            session={'info':{'session_id':'s','sha256':'expected','metadata_sha256':{}}}
            with patch.object(predict.torch,'load',return_value=bundle), \
                 patch.object(predict,'prepare',return_value=([session],{'val':np.array([[0,0]])},{})) as prepare, \
                 patch.object(predict,'predict_model',return_value=(pd.DataFrame({'x':[1]}),object())), \
                 patch.object(predict,'save_evaluation',return_value={}), \
                 patch.object(predict,'benchmark_cpu',return_value={}):
                predict.run_checkpoint(ck,'val',data_root=tmp)
                self.assertEqual(prepare.call_args.args[0]['data_root'],str(Path(tmp).resolve()))
                self.assertEqual(config['data_root'],'original')
                session['info']['sha256']='changed'
                with self.assertRaisesRegex(ValueError,'Dataset changed'):
                    predict.run_checkpoint(ck,'val',data_root=tmp)

if __name__=='__main__':unittest.main()
