"""Shared training/prediction machinery. Checkpoints are local trusted artifacts."""
import copy
import random
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
from .data import batch_arrays, normalize_sessions, load_labels, json_write
from .models import build_model, count_parameters


def setup(seed=42,threads=4):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    torch.set_num_threads(threads)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark=False
    torch.backends.cudnn.deterministic=True


def make_tensors(sessions,indices,config,device):
    arrays=batch_arrays(sessions,indices,config['window_samples'],config['thresholds_N'])
    return tuple(torch.as_tensor(a,device=device) for a in arrays)


def losses(out, y, load, ids, task, cfg):
    force=nn.functional.smooth_l1_loss(out['force'],y)
    load_loss=nn.functional.binary_cross_entropy_with_logits(out['load_logit'],load.float())
    loc=force.new_zeros(())
    if task=='body':
        valid=(load==1)&(ids>=0)&(ids<18)
        if valid.any(): loc=nn.functional.cross_entropy(out['location_logits'][valid],ids[valid])
        else: loc=out['location_logits'].sum()*0
    return force+cfg['load_loss_weight']*load_loss+cfg['location_loss_weight']*loc,force,load_loss,loc


def validate(model,tensors,config):
    # Each term is normalized by its own eligible sample count. In particular,
    # a sparse loaded batch must not receive the same location weight as a full one.
    model.eval()
    force_sum=load_sum=location_sum=0.0
    sample_count=location_count=0
    with torch.inference_mode():
        for begin in range(0,len(tensors[0]),config['batch_size']):
            batch=tuple(t[begin:begin+config['batch_size']] for t in tensors)
            out=model(batch[0])
            _,force,load,location=losses(out,*batch[1:],config['task'],config)
            n=len(batch[0]);sample_count+=n
            force_sum+=float(force)*n;load_sum+=float(load)*n
            if config['task']=='body':
                valid=(batch[2]==1)&(batch[3]>=0)&(batch[3]<18)
                n_location=int(valid.sum())
                location_sum+=float(location)*n_location;location_count+=n_location
    if not sample_count:
        raise ValueError('Validation requires at least one sample')
    force_loss=force_sum/sample_count;load_loss=load_sum/sample_count
    location_loss=location_sum/location_count if location_count else 0.0
    combined=force_loss+config['load_loss_weight']*load_loss+config['location_loss_weight']*location_loss
    return {'loss':combined,'force_loss':force_loss,'load_loss':load_loss,'location_loss':location_loss}


def train_model(name,sessions,indices,scaler,config,outdir,device,tensors=None,init_checkpoint=None):
    """현재 데이터로 새 optimizer를 학습한다. warm-start는 부모 척도를 동결한다."""
    from .data import sha256

    if config['max_epochs'] < 1:
        raise ValueError('max_epochs must be positive')
    setup(config['seed'],config.get('threads',4))
    outdir=Path(outdir)
    if outdir.exists():
        raise FileExistsError(f'{outdir} exists; choose a new output')
    columns=sessions[0]['columns']
    if any(s['columns'] != columns for s in sessions):
        raise ValueError('Input column order differs between sessions')
    roles={s['info']['session_id']:{'folder':s['info']['folder'],'roles':[],
                                 'sha256':s['info']['sha256']} for s in sessions}
    for part in ('train','val','test'):
        for session_index in sorted({int(pair[0]) for pair in indices.get(part,[])}):
            roles[sessions[session_index]['info']['session_id']]['roles'].append(part)
    current_seen={sid for sid,info in roles.items() if set(info['roles']) & {'train','val'}}
    current_test={sid for sid,info in roles.items() if 'test' in info['roles']}
    reserved_ids=set(config.get('protected_test_session_ids',[]))
    reserved_hashes=set(config.get('protected_test_hashes',[]))
    if current_seen & reserved_ids or any(roles[sid]['sha256'] in reserved_hashes for sid in current_seen):
        raise ValueError('A protected test recording cannot be used for train/validation')
    seen_history=set(current_seen);held_out_history=set(current_test)|reserved_ids
    seen_hash_history={roles[sid]['sha256'] for sid in current_seen}
    test_hash_history={roles[sid]['sha256'] for sid in current_test}|reserved_hashes
    parent=None;warm_start=None
    if init_checkpoint is not None:
        parent_path=Path(init_checkpoint).resolve(strict=True)
        if parent_path.is_relative_to(outdir.resolve()):
            raise ValueError('Warm-start output must not contain the parent checkpoint')
        parent=torch.load(parent_path,map_location='cpu',weights_only=True)
        parent_config=parent['config']
        if parent.get('model') != name:
            raise ValueError('Warm-start model differs from checkpoint')
        if parent.get('feature_columns') != columns:
            raise ValueError('Warm-start input column order differs from checkpoint')
        required_contract=('task','force_source','source_force_unit','window_samples','thresholds_N')
        for key in required_contract:
            if key not in config or key not in parent_config or config[key] != parent_config[key]:
                raise ValueError(f'Warm-start incompatible {key}')
        optional_contract=('threshold_policy','load_threshold_source','thresholds_source',
                           'calibration_file','calibration_hash','baseline_N','target_offset_N',
                           'max_matching_skew_ms','gap_factor')
        for key in optional_contract:
            if config.get(key) != parent_config.get(key):
                raise ValueError(f'Warm-start incompatible {key}')
        physical_contract={'force_frame':'hrm_base','force_unit':'N',
                           'training_sign_multiplier':1,'future_hrm_control_multiplier':-1}
        for key,expected in physical_contract.items():
            if parent.get(key) != expected or config.get(key,expected) != expected:
                raise ValueError(f'Warm-start incompatible {key}')
            if parent_config.get(key,expected) != expected:
                raise ValueError(f'Warm-start parent config incompatible {key}')
        # A transformed input must retain the normalization under which weights were learned.
        frozen={}
        for key,size in (('x_mean',len(columns)),('x_std',len(columns)),('y_mean',3),('y_std',3)):
            value=np.asarray(parent['scaler'][key],dtype=np.float64)
            if value.shape != (size,) or not np.isfinite(value).all():
                raise ValueError(f'Warm-start invalid scaler {key}')
            if key.endswith('_std') and np.any(value<=0):
                raise ValueError(f'Warm-start nonpositive scaler {key}')
            frozen[key]=value.copy()
        scaler=frozen

        parent_roles=parent.get('source_session_roles')
        audit_source=None
        if parent_roles is None:
            # Initial project checkpoints predate role provenance; verify their adjacent audit.
            audit_path=parent_path.parent.parent/'dataset_audit.json'
            if not audit_path.is_file():
                raise ValueError('Warm-start cannot verify prior train/val/test roles: missing dataset_audit.json')
            import json
            audit=json.loads(audit_path.read_text())
            if not isinstance(audit,list):
                raise ValueError('Warm-start invalid legacy dataset audit')
            parent_roles={}
            for item in audit:
                sid=item.get('session_id');counts=item.get('split_counts')
                if sid in parent_roles or not isinstance(counts,dict) or any(p not in counts for p in ('train','val','test')):
                    raise ValueError('Warm-start ambiguous legacy session roles')
                parent_roles[sid]={'folder':item.get('folder'),
                                   'roles':[p for p in ('train','val','test') if counts[p]>0],
                                   'sha256':item.get('sha256')}
            audit_source={'path':str(audit_path.resolve()),'sha256':sha256(audit_path)}
        if set(parent_roles) != set(parent.get('source_hashes',{})):
            raise ValueError('Warm-start cannot verify all parent session roles')
        for sid,role in parent_roles.items():
            if not isinstance(role,dict) or not isinstance(role.get('roles'),list):
                raise ValueError('Warm-start malformed parent session roles')
            if set(role['roles'])-{'train','val','test'}:
                raise ValueError('Warm-start unknown parent session role')
            if role.get('sha256') != parent['source_hashes'][sid]:
                raise ValueError('Warm-start parent role/source hash mismatch')
            if 'test' in role['roles'] and set(role['roles']) & {'train','val'}:
                raise ValueError('Warm-start parent session spans test and training')
        previous_seen={sid for sid,r in parent_roles.items() if set(r['roles']) & {'train','val'}}
        previous_seen.update(parent.get('seen_training_validation_session_ids',[]))
        previous_test={sid for sid,r in parent_roles.items() if 'test' in r['roles']}
        previous_test.update(parent.get('held_out_test_session_ids',[]))
        if config.get('validation_strategy') == 'grouped_session_by_contact_id':
            current_val={sid for sid,r in roles.items() if 'val' in r['roles']}
            previous_hashes={r['sha256'] for sid,r in parent_roles.items() if sid in previous_seen}
            if current_val & previous_seen or any(roles[sid]['sha256'] in previous_hashes for sid in current_val):
                raise ValueError('Grouped validation recordings were seen by the parent; use fresh initialization or new validation recordings')
        if (current_test | reserved_ids) & (previous_seen | current_seen):
            raise ValueError('Warm-start current test session was used for train/val')
        if current_seen & previous_test:
            raise ValueError('Warm-start cannot move a prior held-out test session into train/val')
        trained_hashes={r['sha256'] for sid,r in parent_roles.items() if sid in previous_seen}
        trained_hashes.update(parent.get('seen_training_validation_hashes',[]))
        previous_test_hashes={r['sha256'] for sid,r in parent_roles.items() if sid in previous_test}
        previous_test_hashes.update(parent.get('held_out_test_hashes',[]))
        if seen_hash_history & previous_test_hashes:
            raise ValueError('Warm-start cannot use a prior held-out test data hash for train/val')
        if test_hash_history & trained_hashes:
            raise ValueError('Warm-start current test data hash matches prior train/val data')
        seen_history.update(previous_seen);held_out_history.update(previous_test)
        seen_hash_history.update(trained_hashes);test_hash_history.update(previous_test_hashes)
        warm_start={'parent_checkpoint':str(parent_path),'parent_sha256':sha256(parent_path),
                    'parent_role_audit':audit_source,'scaler_policy':'frozen_parent_x_and_y',
                    'optimizer_policy':'new_AdamW_current_config_no_optimizer_resume',
                    'dataset_policy':'full_current_config_only_no_automatic_parent_replay',
                    'parent_best_epoch':parent.get('stats',{}).get('best_epoch')}
        # Rebuild even when the caller supplied tensors; their normalization is untrusted.
        tensors=None

    model=build_model(name,len(scaler['x_mean']),task=config['task'],seq_len=config['window_samples']).to(device)
    if parent is not None:
        model.load_state_dict(parent['state_dict'],strict=True)
    if tensors is None:
        normalize_sessions(sessions,scaler)
        tensors={k:make_tensors(sessions,indices[k],config,device) for k in ['train','val']}
    train=tensors['train'];val=tensors['val']
    optim=torch.optim.AdamW(model.parameters(),lr=config['learning_rate'],weight_decay=config['weight_decay'])
    scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(optim,patience=3,factor=.5)
    best=float('inf');best_state=None;best_epoch=0;stale=0;history=[];start=time.perf_counter()
    initial_validation=None
    if parent is not None:
        initial_validation=validate(model,val,config)
        if not np.isfinite(initial_validation['loss']):
            raise ValueError('Warm-start initial validation loss is nonfinite')
        best=initial_validation['loss']
        best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
        history.append({'epoch':0,'train_loss':float('nan'),
                        **{'val_'+k:v for k,v in initial_validation.items()},
                        'learning_rate':config['learning_rate'],'elapsed_seconds':time.perf_counter()-start})
        print(f"{config['task']}/{name} warm-start epoch 000 val={best:.5f}",flush=True)
    outdir.mkdir(parents=True,exist_ok=False)
    if initial_validation is not None:
        json_write(outdir/'initial_validation.json',initial_validation)
        pd.DataFrame(history).to_csv(outdir/'history.csv',index=False)
    for epoch in range(1,config['max_epochs']+1):
        model.train();perm=torch.randperm(len(train[0]),device=device);total=0.;steps=0
        for begin in range(0,len(perm),config['batch_size']):
            ix=perm[begin:begin+config['batch_size']];batch=tuple(t[ix] for t in train)
            optim.zero_grad(set_to_none=True)
            out=model(batch[0]);loss,*_=losses(out,*batch[1:],config['task'],config)
            if not torch.isfinite(loss): raise RuntimeError(f'{name}: nonfinite training loss')
            loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.0);optim.step()
            total+=loss.item()*len(ix);steps+=len(ix)
        v=validate(model,val,config);scheduler.step(v['loss'])
        history.append({'epoch':epoch,'train_loss':total/steps,**{'val_'+k:x for k,x in v.items()},'learning_rate':optim.param_groups[0]['lr'],'elapsed_seconds':time.perf_counter()-start})
        pd.DataFrame(history).to_csv(outdir/'history.csv',index=False)
        if v['loss']<best-1e-6:
            best=v['loss'];best_epoch=epoch;stale=0
            best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
        else: stale+=1
        print(f"{config['task']}/{name} epoch {epoch:03d} train={total/steps:.5f} val={v['loss']:.5f} best={best_epoch}",flush=True)
        if stale>=config['patience']: break
    elapsed=time.perf_counter()-start
    model.load_state_dict(best_state)
    stats={'model':name,'task':config['task'],'parameters':count_parameters(model),'epochs_run':epoch,'best_epoch':best_epoch,'validation_loss':best,'training_seconds':elapsed,'device':str(device)}
    if warm_start is not None:
        stats.update({'initial_validation_loss':initial_validation['loss'],
                      'warm_start_checkpoint':warm_start['parent_checkpoint'],
                      'warm_start_checkpoint_sha256':warm_start['parent_sha256'],
                      'scaler_policy':warm_start['scaler_policy']})
    bundle={'state_dict':best_state,'model':name,'config':config,'scaler':{k:np.asarray(v).tolist() for k,v in scaler.items()},'feature_columns':columns,'stats':stats,'force_frame':'hrm_base','force_unit':'N','training_sign_multiplier':1,'future_hrm_control_multiplier':-1,'torch_version':str(torch.__version__), 'source_hashes':{s['info']['session_id']:s['info']['sha256'] for s in sessions}, 'source_provenance':{s['info']['session_id']:{'metadata_sha256':s['info']['metadata_sha256'],'timestamp_repair':s['info'].get('timestamp_repair')} for s in sessions},
            'source_session_roles':roles,'seen_training_validation_session_ids':sorted(seen_history),
            'held_out_test_session_ids':sorted(held_out_history),
            'seen_training_validation_hashes':sorted(seen_hash_history),
            'held_out_test_hashes':sorted(test_hash_history),'warm_start':warm_start}
    torch.save(bundle,outdir/'checkpoint.pt')
    json_write(outdir/'training_summary.json',stats)
    json_write(outdir/'bundle_metadata.json',{k:v for k,v in bundle.items() if k!='state_dict'})
    return stats

def predict_model(bundle,sessions,indices,device='cpu',batch_size=1024):
    config=bundle['config'];scaler=bundle['scaler']
    if any(s['columns'] != bundle['feature_columns'] for s in sessions):
        raise ValueError('Input column order differs from checkpoint')
    normalize_sessions(sessions,scaler)
    setup(config['seed'],config.get('threads',4))
    model=build_model(bundle['model'],len(scaler['x_mean']),task=config['task'],seq_len=config['window_samples']).to(device)
    model.load_state_dict(bundle['state_dict']);model.eval()
    predictions=[];probabilities=[];locations=[]
    with torch.inference_mode():
        for begin in range(0,len(indices),batch_size):
            ix=indices[begin:begin+batch_size]
            x=np.stack([sessions[s]['x_scaled'][i-config['window_samples']+1:i+1] for s,i in ix])
            out=model(torch.as_tensor(x,device=device))
            predictions.append(out['force'].cpu().numpy()*np.asarray(scaler['y_std'])+np.asarray(scaler['y_mean']))
            probabilities.append(out['load_logit'].sigmoid().cpu().numpy())
            locations.append(out['location_logits'].argmax(-1).cpu().numpy()+1 if config['task']=='body' else np.full(len(ix),18))
    pred=np.concatenate(predictions);prob=np.concatenate(probabilities);conditional=np.concatenate(locations)
    y=np.stack([sessions[s]['y'][i] for s,i in indices]);thresholds=np.asarray(config['thresholds_N'])
    pred_load=load_labels(pred,thresholds);true_load=load_labels(y,thresholds)
    rows={'session_id':[sessions[s]['info']['session_id'] for s,i in indices],
          'source_folder':[sessions[s]['info']['folder'] for s,i in indices],
          'source_row':[int(i) for s,i in indices],
          'source_time_ns':[int(sessions[s]['ts'][i]) for s,i in indices],
          'original_source_time_text':[(sessions[s]['original_ts'][i] if 'original_ts' in sessions[s] else '') for s,i in indices],
          'elapsed_s':[(int(sessions[s]['ts'][i])-int(sessions[s]['ts'][0]))/1e9 for s,i in indices],
          'source_contact_segment_id':[sessions[s]['source_id'] for s,i in indices],
          'true_id':[sessions[s]['id'] for s,i in indices],
          'conditional_pred_id':conditional,'pred_id':np.where(pred_load,conditional,0),
          'true_load':true_load,'pred_load':pred_load,'load_probability':prob,'load_head_pred':(prob>=.5).astype(int)}
    for a,axis in enumerate('xyz'):
        rows['true_f'+axis+'_N']=y[:,a];rows['pred_f'+axis+'_N']=pred[:,a]
        rows['true_f'+axis+'_mN']=y[:,a]*1000;rows['pred_f'+axis+'_mN']=pred[:,a]*1000
        # Requested no-load display; continuous force estimates remain available above.
        rows['display_f'+axis+'_N']=np.where(pred_load,pred[:,a],0.)
    return pd.DataFrame(rows),model


def benchmark_cpu(model,input_dim,window,repeats=100):
    model=model.cpu().eval();x=torch.zeros(1,window,input_dim)
    times=[]
    with torch.inference_mode():
        for _ in range(15): model(x)
        for _ in range(repeats):
            start=time.perf_counter();model(x);times.append((time.perf_counter()-start)*1000)
    return {f'cpu_forward_p{q}_ms':float(np.percentile(times,q)) for q in [50,95,99]}
