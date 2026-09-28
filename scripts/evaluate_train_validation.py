#!/usr/bin/env python3
"""Evaluate saved best checkpoints on their original train/validation splits."""
import argparse
import hashlib
from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from predict import run_checkpoint
from hrm_force.data import json_write


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',required=True)
    p.add_argument('--data-root')
    a=p.parse_args();root=Path(a.run)
    ranking=pd.read_csv(root/'training_comparison.csv').sort_values('validation_loss')
    checkpoints={name:root/name/'checkpoint.pt' for name in ranking.model}
    original={name:digest(path) for name,path in checkpoints.items()}
    for split in ['val','train']:
        rows=[]
        for name,path in checkpoints.items():
            device='cpu' if name in ['tcn','residual_tcn'] else 'cuda'
            print(f'Evaluating {split}/{name} on {device}',flush=True)
            rows.append(run_checkpoint(path,split,device,data_root=a.data_root))
            pd.DataFrame(rows).sort_values('validation_loss').to_csv(root/f'{split}_comparison.csv',index=False)
            print(f"  location={rows[-1]['location_accuracy_loaded']:.4f} force_rmse_mN={rows[-1]['force_rmse_mN']:.2f}",flush=True)
    after={name:digest(path) for name,path in checkpoints.items()}
    if original!=after: raise RuntimeError('Checkpoint changed during read-only evaluation')
    json_write(root/'train_val_checkpoint_verification.json',{'status':'passed','checkpoint_sha256':after,'weights_unchanged':True,'splits':['val','train']})
    print('Train/validation evaluation complete.',flush=True)
if __name__=='__main__':main()
