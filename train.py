#!/usr/bin/env python3
"""Train a common model comparison or warm-start one model with frozen scales."""
import argparse
from pathlib import Path
import json
import shutil
import subprocess
import numpy as np
import pandas as pd
import torch
from hrm_force.data import prepare,normalize_sessions,json_write,sha256
from hrm_force.engine import setup,make_tensors,train_model
from hrm_force.models import MODEL_NAMES
from hrm_force.folder_datasets import resolve_folder_config


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    p.add_argument('--models',nargs='+',default=['all']);p.add_argument('--device',default='auto')
    p.add_argument('--epochs',type=int)
    p.add_argument('--prepare-only',action='store_true',help='Validate folders and save a frozen split/scaler audit without training')
    p.add_argument('--resume',action='store_true',help='Skip completed models; does not resume optimizer state')
    p.add_argument('--init-checkpoint',help='Warm-start exactly one explicit --models model; freeze parent X/Y scalers')
    args=p.parse_args(argv);cfg=resolve_folder_config(json.loads(Path(args.config).read_text()))
    if args.epochs is not None: cfg['max_epochs']=args.epochs
    if cfg['max_epochs']<1: p.error('--epochs/max_epochs must be positive')
    models=list(MODEL_NAMES) if args.models==['all'] else args.models
    if any(m not in MODEL_NAMES for m in models): p.error('unknown model')
    if args.init_checkpoint and (args.models==['all'] or len(models)!=1):
        p.error('--init-checkpoint requires one explicit --models name')
    if args.init_checkpoint and args.resume:
        p.error('--init-checkpoint starts a new run; do not combine with --resume')
    if args.prepare_only and (args.init_checkpoint or args.resume):
        p.error('--prepare-only cannot be combined with --init-checkpoint/--resume')
    parent_path=None;parent_bundle=None
    root=Path(args.output)
    if args.init_checkpoint:
        parent_path=Path(args.init_checkpoint).resolve(strict=True)
        if parent_path.is_relative_to(root.resolve()):
            raise ValueError('Warm-start output must be separate from the parent run')
        parent_bundle=torch.load(parent_path,map_location='cpu',weights_only=True)
        if parent_bundle['model']!=models[0]:
            raise ValueError('Warm-start model differs from checkpoint')
    if (root/'config.json').exists() and json.loads((root/'config.json').read_text()) != cfg:
        raise ValueError('Output contains different configuration')
    setup(cfg['seed'],cfg.get('threads',4))
    device=torch.device('cpu' if args.prepare_only else (('cuda' if torch.cuda.is_available() else 'cpu') if args.device=='auto' else args.device))
    print('Preparing',cfg['task'],device,flush=True)
    sessions,indices,scaler=prepare(cfg)
    if parent_bundle is not None:
        # Newly fitted candidate scales are deliberately discarded before normalization/export.
        scaler={k:np.asarray(parent_bundle['scaler'][k],dtype=np.float64).copy()
                for k in ('x_mean','x_std','y_mean','y_std')}
    normalize_sessions(sessions,scaler)
    root.mkdir(parents=True,exist_ok=True)
    json_write(root/'config.json',cfg)
    json_write(root/'dataset_audit.json',[s['info'] for s in sessions]);json_write(root/'scaler.json',scaler)
    if parent_path is not None:
        json_write(root/'warm_start.json',{'parent_checkpoint':str(parent_path),
                   'parent_sha256':sha256(parent_path),'scaler_policy':'frozen_parent_x_and_y',
                   'optimizer_policy':'new_AdamW_current_config_no_optimizer_resume',
                   'dataset_policy':'full_current_config_only_no_automatic_parent_replay'})
    rows=[]
    for part,ix in indices.items():
        for s,i in ix: rows.append({'split':part,'session_id':sessions[s]['info']['session_id'],'source_row':int(i),'source_time_ns':int(sessions[s]['ts'][i])})
    pd.DataFrame(rows).to_csv(root/'split_manifest.csv',index=False)
    if args.prepare_only:
        print('Dataset preparation complete (no training):',root,
              {part:len(ix) for part,ix in indices.items()},flush=True)
        return
    json_write(root/'environment.json',{'torch':str(torch.__version__),'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,'device':str(device)})
    (root/'pip_freeze.txt').write_text(subprocess.check_output([__import__('sys').executable,'-m','pip','freeze'],text=True))
    code=root/'code_snapshot';code.mkdir(exist_ok=True)
    project=Path(__file__).resolve().parent
    for src in [project/'train.py',project/'predict.py',project/'model_zoo.py',
                *(project/'hrm_force').glob('*.py'),*(project/'configs').glob('*.json')]:
        dest=code/src.relative_to(project);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
    # Warm-start rebuilds tensors in the engine after all compatibility checks.
    tensors=None if parent_path is not None else {k:make_tensors(sessions,indices[k],cfg,device) for k in ['train','val']}
    tensor_cache={} if tensors is None else {str(device):tensors}
    stats=[]
    for name in models:
        dest=root/name
        if dest.exists():
            if args.resume and (dest/'training_summary.json').exists():
                stats.append(json.loads((dest/'training_summary.json').read_text()));continue
            raise FileExistsError(f'{dest} exists; choose a new output or --resume completed models')
        model_device=torch.device(cfg.get('model_device_overrides',{}).get(name,str(device)))
        if tensors is not None and str(model_device) not in tensor_cache:
            tensor_cache[str(model_device)]={k:tuple(t.to(model_device) for t in tensors[k]) for k in tensors}
        stat=train_model(name,sessions,indices,scaler,cfg,dest,model_device,
                         tensor_cache.get(str(model_device)),init_checkpoint=parent_path)
        stats.append(stat)
        pd.DataFrame(stats).sort_values('validation_loss').to_csv(root/'training_comparison.csv',index=False)
    print('Training complete:',root,flush=True)
if __name__=='__main__': main()
