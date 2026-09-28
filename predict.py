#!/usr/bin/env python3
"""Predict and evaluate frozen checkpoints without fitting on test data."""
import argparse
import json
from pathlib import Path
import pandas as pd
import torch
from hrm_force.data import prepare,load_session,json_write
from hrm_force.engine import predict_model,benchmark_cpu
from hrm_force.evaluation import save_evaluation


def run_checkpoint(checkpoint,split='test',device='cpu',csv_session=None,data_root=None):
    checkpoint=Path(checkpoint);bundle=torch.load(checkpoint,map_location='cpu',weights_only=True)
    cfg=dict(bundle['config'])
    if data_root is not None: cfg['data_root']=str(Path(data_root).resolve())
    if csv_session:
        session=load_session(csv_session,cfg);sessions=[session]
        import numpy as np
        ix=np.column_stack([np.zeros(len(session['ends']),dtype=int),session['ends']])
    else:
        sessions,indices,_=prepare(cfg);ix=indices[split]
        if not len(ix):
            raise ValueError(f'No frozen {split} windows; use --test-root for separate test folders')
        if bundle['source_hashes']!={s['info']['session_id']:s['info']['sha256'] for s in sessions}:
            raise ValueError('Dataset changed after training')
        provenance=bundle.get('source_provenance')
        audit_path=checkpoint.parent.parent/'dataset_audit.json'
        if provenance is None and audit_path.exists():
            provenance={s['session_id']:{'metadata_sha256':s['metadata_sha256'],'timestamp_repair':s.get('timestamp_repair')} for s in json.loads(audit_path.read_text())}
        actual={s['info']['session_id']:{'metadata_sha256':s['info']['metadata_sha256'],'timestamp_repair':s['info'].get('timestamp_repair')} for s in sessions}
        if provenance is not None and provenance != actual:
            raise ValueError('Metadata or timestamp repair source changed after training')
    df,model=predict_model(bundle,sessions,ix,device=device)
    out=checkpoint.parent/(('external' if csv_session else split)+'_predictions');out.mkdir(exist_ok=True)
    df.to_csv(out/'predictions.csv',index=False)
    metrics=save_evaluation(df,out,cfg['task'])
    latency=benchmark_cpu(model,len(bundle['feature_columns']),cfg['window_samples'])
    summary={**bundle['stats'],**metrics,**latency,'split':split,'prediction_csv':str(out/'predictions.csv')}
    json_write(out/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--run');g.add_argument('--checkpoint')
    p.add_argument('--split',choices=['train','val','test'],default='test');p.add_argument('--device',default='cpu')
    p.add_argument('--data-root',help='Alternate root for the identical historical dataset; checkpoint hash checks still apply')
    p.add_argument('--session',help='Optional new folder containing csv/summary.csv plus metadata')
    p.add_argument('--test-root', help='Evaluate every recording folder under a separate testsets root')
    p.add_argument('--output', help='New output directory, required with --test-root')
    a=p.parse_args()
    if a.test_root:
        if a.session or a.data_root or a.split != 'test':
            p.error('--test-root cannot be combined with --session, --data-root, or --split train/val')
        if not a.output:
            p.error('--test-root requires --output pointing to a new directory')
    elif a.output:
        p.error('--output is currently supported only with --test-root')
    checkpoints=sorted(Path(a.run).glob('*/checkpoint.pt')) if a.run else [Path(a.checkpoint)]
    if not checkpoints: p.error('No checkpoints')
    if a.test_root:
        from hrm_force.folder_prediction import run_folder_prediction
        run_folder_prediction(checkpoints, a.test_root, a.output, a.device)
        print('Prediction complete:', a.output, flush=True)
        return
    rows=[]
    for ck in checkpoints:
        print('Predicting',ck,flush=True);rows.append(run_checkpoint(ck,a.split,a.device,a.session,a.data_root))
        if a.run: pd.DataFrame(rows).sort_values('validation_loss').to_csv(Path(a.run)/(a.split+'_comparison.csv'),index=False)
    print('Prediction complete',flush=True)
if __name__=='__main__':main()
