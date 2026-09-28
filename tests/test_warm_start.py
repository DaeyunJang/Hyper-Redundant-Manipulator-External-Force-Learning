"""부모 모델을 초기값으로 추가 학습할 때 척도·계약·holdout을 보존한다."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np
import pandas as pd
import torch

import train as train_cli
from hrm_force.data import sha256
from hrm_force.engine import predict_model, train_model


class WarmStartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_threads=torch.get_num_threads();torch.set_num_threads(1)
        cls.temporary=tempfile.TemporaryDirectory();cls.root=Path(cls.temporary.name)
        cls.config={"seed":23,"threads":1,"task":"tip","force_source":"kalman",
                    "source_force_unit":"mN","window_samples":3,"thresholds_N":[.0454,.0436,.0729],
                    "threshold_policy":"user_supplied_axis_1sigma_zero_centered_box_not_confidence_interval",
                    "batch_size":4,"learning_rate":.001,"weight_decay":0.,"max_epochs":2,
                    "patience":3,"load_loss_weight":.2,"location_loss_weight":.5,
                    "training_sign_multiplier":1,"future_hrm_control_multiplier":-1,
                    "sessions":["training","right"],"test_sessions":["right"]}
        rng=np.random.default_rng(9)
        cls.sessions=[]
        for sid,folder in (("training-id","training"),("external-right-id","right")):
            x=rng.normal(size=(30,4)).astype(np.float32)
            y=np.stack([x[:,0]*.1,x[:,1]*-.2,x[:,2]*.3],axis=-1)
            cls.sessions.append({"x":x,"y":y,"ts":np.arange(30,dtype=np.int64)*33_333_333,
                "columns":[f"feature_{i}" for i in range(4)],"id":18,"source_id":18,
                "info":{"session_id":sid,"folder":folder,"sha256":f"hash-{sid}","metadata_sha256":{}}})
        cls.indices={"train":np.array([(0,i) for i in range(2,16)]),
                     "val":np.array([(0,i) for i in range(19,25)]),
                     "test":np.array([(1,i) for i in range(2,10)])}
        cls.scaler={"x_mean":np.array([.1,.2,-.3,.4]),"x_std":np.array([.8,1.2,1.5,.7]),
                    "y_mean":np.array([.01,-.02,.03]),"y_std":np.array([.1,.2,.3])}
        cls.parent_path=cls.root/'original'/'mlp'/'checkpoint.pt'
        with contextlib.redirect_stdout(io.StringIO()):
            train_model('mlp',copy.deepcopy(cls.sessions),cls.indices,cls.scaler,cls.config,
                        cls.parent_path.parent,torch.device('cpu'))
        cls.parent=torch.load(cls.parent_path,map_location='cpu',weights_only=True)
        cls.parent_hash=sha256(cls.parent_path)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup();torch.set_num_threads(cls.original_threads)

    def setUp(self):
        self.sessions_current=copy.deepcopy(self.sessions)
        self.cfg=dict(self.config,learning_rate=0.,max_epochs=1)
        self.out=self.root/self._testMethodName/'mlp'

    def tearDown(self):
        self.assertEqual(sha256(self.parent_path),self.parent_hash)

    def run_warm(self,**kwargs):
        arguments=dict(name='mlp',sessions=self.sessions_current,indices=self.indices,
                       scaler={k:np.full_like(v,99.) for k,v in self.scaler.items()},
                       config=self.cfg,outdir=self.out,device=torch.device('cpu'),
                       init_checkpoint=self.parent_path)
        arguments.update(kwargs)
        with contextlib.redirect_stdout(io.StringIO()):
            return train_model(**arguments)

    def test_learned_checkpoint_reproduction_and_frozen_scales(self):
        # The supplied candidate scaler/tensors must not silently change the learned coordinate system.
        stats=self.run_warm(tensors={'train':'untrusted','val':'untrusted'})
        child=torch.load(self.out/'checkpoint.pt',map_location='cpu',weights_only=True)
        self.assertEqual(child['scaler'],self.parent['scaler'])
        self.assertEqual(stats['best_epoch'],0)
        self.assertLessEqual(stats['validation_loss'],stats['initial_validation_loss'])
        for key in self.parent['state_dict']:
            torch.testing.assert_close(child['state_dict'][key],self.parent['state_dict'][key],atol=0,rtol=0)
        expected,_=predict_model(self.parent,copy.deepcopy(self.sessions),self.indices['test'])
        actual,_=predict_model(child,copy.deepcopy(self.sessions),self.indices['test'])
        np.testing.assert_array_equal(expected[[f'pred_f{axis}_N' for axis in 'xyz']],
                                      actual[[f'pred_f{axis}_N' for axis in 'xyz']])
        self.assertEqual(child['warm_start']['parent_checkpoint'],str(self.parent_path.resolve()))
        self.assertEqual(child['warm_start']['parent_sha256'],self.parent_hash)
        self.assertEqual(child['warm_start']['dataset_policy'],
                         'full_current_config_only_no_automatic_parent_replay')
        history=pd.read_csv(self.out/'history.csv')
        self.assertEqual(history.epoch.tolist(),[0,1])

    def test_worse_updates_keep_epoch_zero_and_use_new_optimizer(self):
        self.cfg.update(learning_rate=.01,max_epochs=2)
        def metrics(value):
            return {'loss':value,'force_loss':value,'load_loss':0.,'location_loss':0.}
        adam=torch.optim.AdamW
        with mock.patch('hrm_force.engine.validate',side_effect=[metrics(1.),metrics(5.),metrics(9.)]), \
             mock.patch('hrm_force.engine.torch.optim.AdamW',wraps=adam) as create_optimizer:
            stats=self.run_warm()
        self.assertEqual(create_optimizer.call_args.kwargs['lr'],.01)
        self.assertEqual(stats['best_epoch'],0);self.assertEqual(stats['validation_loss'],1.)
        child=torch.load(self.out/'checkpoint.pt',map_location='cpu',weights_only=True)
        for key in self.parent['state_dict']:
            torch.testing.assert_close(child['state_dict'][key],self.parent['state_dict'][key],atol=0,rtol=0)

    def test_changed_sessions_are_supported_and_recorded_without_replay(self):
        self.sessions_current[0]['info'].update(session_id='new-training-id',folder='new-training',sha256='new-data-hash')
        self.sessions_current[0]['x']+=2.
        self.cfg.update(sessions=['new-training','right'])
        self.run_warm()
        child=torch.load(self.out/'checkpoint.pt',map_location='cpu',weights_only=True)
        self.assertNotIn('training-id',child['source_hashes'])
        self.assertIn('training-id',child['seen_training_validation_session_ids'])
        self.assertIn('new-training-id',child['seen_training_validation_session_ids'])
        self.assertIn('hash-training-id',child['seen_training_validation_hashes'])
        self.assertIn('new-data-hash',child['seen_training_validation_hashes'])
        self.assertEqual(child['held_out_test_session_ids'],['external-right-id'])
        np.testing.assert_allclose(self.sessions_current[0]['x_scaled'],
            ((self.sessions_current[0]['x']-self.scaler['x_mean'])/self.scaler['x_std']).astype(np.float32))

    def test_incompatible_training_contracts_fail_before_output_creation(self):
        changed={'task':'body','force_source':'raw','source_force_unit':'N','window_samples':4,
                 'thresholds_N':[.1,.1,.1],'threshold_policy':'different',
                 'force_frame':'sensor','force_unit':'mN','training_sign_multiplier':-1}
        for key,value in changed.items():
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,key):
                self.run_warm(config=dict(self.cfg,**{key:value}))
        self.assertFalse(self.out.exists())
        with self.assertRaisesRegex(ValueError,'model differs'):
            self.run_warm(name='gru')
        self.sessions_current[0]['columns']=list(reversed(self.sessions_current[0]['columns']))
        self.sessions_current[1]['columns']=list(self.sessions_current[0]['columns'])
        with self.assertRaisesRegex(ValueError,'column order'):
            self.run_warm()

    def test_previously_trained_session_cannot_become_current_test(self):
        self.sessions_current[1]=copy.deepcopy(self.sessions[0])
        self.sessions_current[0]['info'].update(session_id='new-training-id',sha256='new-hash')
        with self.assertRaisesRegex(ValueError,'test session was used for train/val'):
            self.run_warm()

    def test_previous_test_cannot_move_into_training(self):
        self.sessions_current[0]=copy.deepcopy(self.sessions[1])
        self.sessions_current[1]['info'].update(session_id='new-test-id',sha256='new-test-hash')
        with self.assertRaisesRegex(ValueError,'prior held-out test'):
            self.run_warm()

    def test_previous_test_hash_cannot_move_into_training_with_changed_id(self):
        self.sessions_current[0]['info'].update(session_id='renamed-heldout',
                                              sha256=self.sessions[1]['info']['sha256'])
        self.sessions_current[1]['info'].update(session_id='new-test-id',sha256='new-test-hash')
        with self.assertRaisesRegex(ValueError,'prior held-out test data hash'):
            self.run_warm()
        self.assertFalse(self.out.exists())

    def test_group_validation_seen_by_parent_is_rejected(self):
        self.cfg['validation_strategy']='grouped_session_by_contact_id'
        with self.assertRaisesRegex(ValueError,'Grouped validation recordings were seen'):
            self.run_warm()
        self.assertFalse(self.out.exists())

    def test_reserved_test_recording_is_rejected_before_training(self):
        self.cfg['protected_test_session_ids']=['training-id']
        with self.assertRaisesRegex(ValueError,'protected test recording'):
            self.run_warm()
        self.assertFalse(self.out.exists())

    def test_legacy_checkpoint_requires_and_verifies_adjacent_role_audit(self):
        legacy=copy.deepcopy(self.parent);legacy.pop('source_session_roles')
        legacy_root=self.root/'legacy';path=legacy_root/'mlp'/'checkpoint.pt'
        path.parent.mkdir(parents=True);torch.save(legacy,path)
        with self.assertRaisesRegex(ValueError,'cannot verify prior'):
            self.run_warm(init_checkpoint=path)
        audit=[]
        for index,session in enumerate(self.sessions):
            counts={part:int((pairs[:,0]==index).sum()) for part,pairs in self.indices.items()}
            audit.append(dict(session['info'],split_counts=counts))
        (legacy_root/'dataset_audit.json').write_text(json.dumps(audit))
        self.run_warm(init_checkpoint=path)
        child=torch.load(self.out/'checkpoint.pt',map_location='cpu',weights_only=True)
        self.assertEqual(child['warm_start']['parent_role_audit']['sha256'],
                         sha256(legacy_root/'dataset_audit.json'))

    def test_cli_exports_parent_scaler_before_training(self):
        cfg_path=self.root/'warm_config.json';cfg_path.write_text(json.dumps(self.cfg))
        output=self.out.parent
        fitted={k:np.full_like(v,77.) for k,v in self.scaler.items()}
        with mock.patch('train.prepare',return_value=(self.sessions_current,self.indices,fitted)), \
             mock.patch('train.subprocess.check_output',return_value='test-environment\n'), \
             contextlib.redirect_stdout(io.StringIO()):
            train_cli.main(['--config',str(cfg_path),'--output',str(output),'--models','mlp',
                            '--device','cpu','--init-checkpoint',str(self.parent_path)])
        self.assertEqual(json.loads((output/'scaler.json').read_text()),self.parent['scaler'])
        self.assertTrue((output/'warm_start.json').is_file())
        child=torch.load(output/'mlp'/'checkpoint.pt',map_location='cpu',weights_only=True)
        self.assertEqual(child['scaler'],self.parent['scaler'])

    def test_existing_parent_output_is_never_overwritten(self):
        with self.assertRaises(FileExistsError):
            self.run_warm(outdir=self.parent_path.parent)
        cfg_path=self.root/'no_clobber.json';cfg_path.write_text(json.dumps(self.cfg))
        with self.assertRaisesRegex(ValueError,'separate from the parent run'):
            train_cli.main(['--config',str(cfg_path),'--output',str(self.parent_path.parent.parent),
                            '--models','mlp','--init-checkpoint',str(self.parent_path)])


if __name__=='__main__':
    unittest.main()
