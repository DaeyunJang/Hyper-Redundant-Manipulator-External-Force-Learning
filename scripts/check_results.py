#!/usr/bin/env python3
"""Verify completed comparison artifacts and unchanged source hashes."""
from pathlib import Path
import sys
import json
import hashlib
import numpy as np
import pandas as pd


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()


def main():
    root=Path(sys.argv[1]);report={};references={}
    for task in ['tip','body']:
        folder=root/task;cfg=json.loads((folder/'config.json').read_text())
        models=pd.read_csv(folder/'training_comparison.csv').model.tolist()
        assert len(models)==11, (task,models)
        audit=json.loads((folder/'dataset_audit.json').read_text())
        for item in audit:
            assert digest(item['path'])==item['sha256'],item['path']
            repair=item.get('timestamp_repair')
            if repair:
                assert digest(repair['original_angle_csv'])==repair['original_angle_sha256']
            parent=Path(item['path']).parent
            for name,h in item['metadata_sha256'].items():
                path=parent/name if name in ['manifest.json','summary.schema.json'] else parent.parent/name
                assert digest(path)==h,str(path)
        splits=pd.read_csv(folder/'split_manifest.csv',dtype={'source_time_ns':str})
        test_ids=set(splits.loc[splits.split=='test','session_id'])
        assert not test_ids & set(splits.loc[splits.split!='test','session_id'])
        for sid,group in splits.loc[splits.split!='test'].groupby('session_id'):
            tr=group.loc[group.split=='train'];va=group.loc[group.split=='val']
            assert tr.source_row.max()<va.source_row.min()-cfg['window_samples']+1
            assert int(va.source_time_ns.iloc[0])-int(tr.source_time_ns.iloc[-1])>4e9
        reference=None;reports=[]
        for name in models:
            path=folder/name/'test_predictions/predictions.csv'
            df=pd.read_csv(path,dtype={'source_time_ns':str})
            identity=df[['session_id','source_row','source_time_ns','true_fx_N','true_fy_N','true_fz_N']]
            if reference is None:reference=identity
            else:pd.testing.assert_frame_equal(identity,reference)
            force=df[[f'pred_f{a}_N' for a in 'xyz']].to_numpy()
            truth=df[[f'true_f{a}_N' for a in 'xyz']].to_numpy()
            assert np.isfinite(force).all()
            predicted=(np.abs(force)>np.asarray(cfg['thresholds_N'])).any(1)
            np.testing.assert_array_equal(predicted,df.pred_load)
            np.testing.assert_array_equal(np.where(predicted,df.conditional_pred_id,0),df.pred_id)
            metrics=json.loads((path.parent/'metrics.json').read_text())
            rmse=float(np.sqrt(np.mean((force-truth)**2)))
            assert np.isclose(metrics['force_rmse_N'],rmse,rtol=1e-6)
            assert (df.true_id==18).all()
            if task=='tip':assert (df.conditional_pred_id==18).all()
            reports.append({'model':name,'test_rows':len(df),'recomputed_rmse_N':rmse})
        references[task]=reference
        report[task]={'models_checked':len(models),'source_sessions_checked':len(audit),'models':reports}
    pd.testing.assert_frame_equal(references['tip'],references['body'])
    report['status']='passed'
    report['checks']=['source_and_metadata_hashes_unchanged','independent_test_sessions','purged_validation_windows','same_test_rows_targets_all_models_both_tasks','finite_predictions','threshold_and_id_rules','recomputed_force_rmse']
    (root/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'passed','models':22,'common_test_rows':len(references['tip'])}))
if __name__=='__main__':main()
