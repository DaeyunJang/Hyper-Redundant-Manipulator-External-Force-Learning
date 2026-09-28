"""Read-only CSV loading, audited masks and purged temporal validation."""
from pathlib import Path
from decimal import Decimal, InvalidOperation
import csv
import hashlib
import json
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS_N = np.array([0.0454, 0.0436, 0.0729], dtype=np.float64)

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def json_write(path, value):
    def clean(v):
        if isinstance(v, dict): return {str(k): clean(x) for k,x in v.items()}
        if isinstance(v, (list, tuple)): return [clean(x) for x in v]
        if isinstance(v, np.ndarray): return clean(v.tolist())
        if isinstance(v, np.generic): return clean(v.item())
        if isinstance(v, float) and not np.isfinite(v): return None
        if isinstance(v, Path): return str(v)
        return v
    Path(path).write_text(json.dumps(clean(value), indent=2, ensure_ascii=False, allow_nan=False)+'\n')

def feature_spec(groups):
    catalog = json.loads((ROOT/'configs/feature_catalog.json').read_text())
    cols, flags, prefixes = [], [], []
    for group in groups:
        spec = catalog['groups'][group]
        cols += [spec['column_template'].format(i=i) for i in range(spec['first_index'],spec['last_index']+1)]
        flags += spec['required_true_columns']
        if spec['time_prefix']: prefixes.append(spec['time_prefix'])
    if len(set(cols)) != len(cols): raise ValueError('Duplicate input columns')
    return cols, list(dict.fromkeys(flags)), list(dict.fromkeys(prefixes))

def parse_timestamp(value):
    """Parse decimal text without float; bool marks non-integer original notation."""
    s = str(value).strip()
    if re.fullmatch(r'[0-9]+', s): return int(s), False
    try:
        d = Decimal(s)
        if not d.is_finite() or d != d.to_integral_value() or d < 0:
            raise ValueError('Invalid timestamp')
        return int(d), True
    except (InvalidOperation, ValueError):
        raise ValueError(f'Invalid timestamp: {s!r}')

def load_labels(force, thresholds=THRESHOLDS_N):
    y = np.asarray(force)
    if not np.isfinite(y).all(): raise ValueError('Nonfinite force cannot be labeled unloaded')
    return (np.abs(y) > thresholds).any(axis=-1).astype(np.int64)

def valid_endpoints(valid, timestamps, window, gap_factor=1.5):
    """Original row adjacency is preserved: rejected rows break every window."""
    ts = np.asarray(timestamps, dtype=np.int64)
    dt = np.diff(ts)
    positive = dt[dt > 0]
    if not len(positive): return np.empty(0, dtype=np.int64), np.nan
    median = float(np.median(positive))
    ends, run = [], 0
    for i, ok in enumerate(valid):
        if i and (dt[i-1] <= 0 or dt[i-1] > gap_factor*median): run = 0
        run = run + 1 if ok else 0
        if run >= window: ends.append(i)
    return np.asarray(ends, dtype=np.int64), median

def load_session(folder, config):
    folder = Path(folder)
    path = folder/'csv/summary.csv'
    meta = json.loads((folder/'session.json').read_text())
    manifest = json.loads((folder/'csv/manifest.json').read_text())
    schema = json.loads((folder/'csv/summary.schema.json').read_text())
    rec = json.loads((folder/'recording_config.json').read_text())
    cols, flags, prefixes = feature_spec(config['feature_groups'])
    source = config['force_source']
    prefix = {'kalman':'fts_kalman','raw':'fts'}[source]
    target = [f'{prefix}.aligned_f{a}' for a in 'xyz']
    flags += [f'{prefix}.matched', f'{prefix}.aligned_force_valid']
    prefixes = list(dict.fromkeys(prefixes+[prefix]))
    skews = [f'{p}.time_difference_ms' for p in prefixes]
    frame = f'{prefix}.aligned_frame_id'
    required = cols+target+flags+skews+[frame,'source_time_ns','contact_segment_id']
    with path.open() as f: header=next(csv.reader(f))
    if len(header) != len(set(header)): raise ValueError(f'{folder}: duplicate headers')
    missing = set(required)-set(header)
    if missing: raise ValueError(f'{folder}: missing selected columns {missing}')
    if schema['columns'] != header: raise ValueError(f'{folder}: schema/header mismatch')
    if schema.get('status') != 'complete' or manifest.get('status') != 'complete':
        raise ValueError(f'{folder}: incomplete export')
    align = meta['snapshot']['force_alignment']
    if not align.get('enabled') or align.get('target_frame') != 'hrm_base':
        raise ValueError(f'{folder}: invalid alignment')
    for key in ['axes','matrix_base_from_sensor','target_frame']:
        if align.get(key) != manifest['force_alignment'].get(key):
            raise ValueError(f'{folder}: conflicting alignment {key}')
    units_note=rec.get('notes',{}).get('source_units',{}).get('fts_force','')
    if 'mN' not in str(units_note) or config['source_force_unit'] != 'mN':
        raise ValueError(f'{folder}: source force unit needs explicit verification')
    df = pd.read_csv(path, usecols=required, dtype=str, keep_default_na=False)
    trimmed=config.get('known_trimmed_exports',{}).get(folder.name,0)
    if len(df) != schema['rows_written']-trimmed:
        raise ValueError(f'{folder}: unexpected row count mismatch')
    ts, notation = zip(*(parse_timestamp(s) for s in df['source_time_ns']))
    ts = np.asarray(ts,dtype=np.int64)
    repair_evidence=None
    if trimmed:
        from .time_repair import repair_timestamps
        ts,repair_evidence=repair_timestamps(folder,df)
    vals = df[cols+target].apply(pd.to_numeric,errors='coerce').to_numpy(dtype=np.float64)
    valid = np.isfinite(vals).all(axis=1)
    reasons = {'nonfinite_selected': int((~valid).sum())}
    for flag in flags:
        ok = df[flag].str.lower().eq('true').to_numpy()
        reasons[flag] = int((~ok).sum()); valid &= ok
    for col in skews:
        a=pd.to_numeric(df[col],errors='coerce').to_numpy(dtype=float)
        ok=np.isfinite(a)&(np.abs(a)<=config['max_matching_skew_ms']+1e-6)
        reasons[col]=int((~ok).sum());valid &= ok
    ok=df[frame].eq('hrm_base').to_numpy();reasons['wrong_frame']=int((~ok).sum());valid &=ok
    labels=pd.to_numeric(df['contact_segment_id'],errors='coerce').to_numpy(dtype=float)
    saved_id=meta['snapshot']['contact_segment_id']
    override=config.get('label_overrides',{}).get(folder.name)
    csv_id=saved_id
    summary_hash=sha256(path)
    if override:
        if override.get('original_id') != saved_id:
            raise ValueError(f'{folder}: label override original_id mismatch')
        csv_id=override.get('csv_id',saved_id)
        if csv_id != saved_id:
            # A user-corrected CSV can differ from frozen recording metadata only
            # for the exact explicitly approved session and source bytes.
            if (not override.get('basis') or
                    override.get('session_id') != meta['session_id'] or
                    override.get('summary_sha256') != summary_hash):
                raise ValueError(f'{folder}: CSV ID override requires matching session/hash/basis')
    for document in (manifest,schema):
        if document.get('contact_segment_id',saved_id) != saved_id:
            raise ValueError(f'{folder}: conflicting frozen metadata contact ID')
    if not (np.isfinite(labels)&(labels==csv_id)).all():
        raise ValueError(f'{folder}: CSV/session ID conflict')
    effective_id=override['training_id'] if override else saved_id
    match=re.search(r'seg-id-(\d+)',folder.name)
    if match is None: raise ValueError(f'{folder}: folder name must contain seg-id-<ID>')
    folder_id=int(match.group(1))
    if folder_id != effective_id: raise ValueError(f'{folder}: unapproved folder/source ID mismatch')
    y=vals[:,len(cols):]*0.001
    endpoints, median=valid_endpoints(valid,ts,config['window_samples'],config['gap_factor'])
    info={'folder':folder.name,'path':str(path.resolve()),'session_id':meta['session_id'],
          'source_id':saved_id,'csv_contact_segment_id':int(csv_id),'training_id':effective_id,'label_override':override,
          'rows':len(df),'valid_rows':int(valid.sum()),'window_endpoints':len(endpoints),
          'rejected_reason_counts_overlapping':reasons,'sha256':summary_hash,
          'metadata_sha256':{str(p.name):sha256(p) for p in [folder/'session.json',folder/'recording_config.json',folder/'csv/manifest.json',folder/'csv/summary.schema.json']},
          'timestamp_repair':repair_evidence,'timestamp_noninteger_notation_rows':sum(notation),'timestamp_precision_note':'Decimal conversion preserves recorded precision only; original ns precision not recovered',
          'median_dt_ms':median/1e6,'nonincreasing_dt':int((np.diff(ts)<=0).sum()),
          'gap_count':int((np.diff(ts)>config['gap_factor']*median).sum()),
          'alignment_axes':align['axes'],'force_units_evidence':units_note,
          'force_units_status':'legacy mN declaration; physical calibration not independently verified',
          'positive_matching_skew_rows':{c:int((pd.to_numeric(df[c],errors='coerce')>0).sum()) for c in skews}}
    return dict(x=vals[:,:len(cols)].astype(np.float32),y=y.astype(np.float32),ts=ts,
                valid=valid,ends=endpoints,original_ts=df['source_time_ns'].tolist(),info=info,id=int(effective_id),source_id=int(csv_id),columns=cols)

def split_endpoints(session, config, test=False):
    ends=session['ends']; n=len(session['ts']); window=config['window_samples']
    if test: return {'train':np.array([],dtype=int),'val':np.array([],dtype=int),'test':ends}
    cut=int(n*(1-config['validation_fraction']))
    ts=session['ts']; guard=int(config['validation_purge_seconds']*1e9)
    cut_time=ts[min(cut,n-1)]
    # Both the last train target and the first validation input are purged in time.
    train=ends[(ends<cut)&(ts[ends]<cut_time-guard)]
    starts=ends-window+1
    val=ends[(starts>=cut)&(ts[starts]>cut_time+guard)]
    return {'train':train,'val':val,'test':np.array([],dtype=int)}

def prepare(config):
    if config.get('dataset_layout') == 'train_test_folders':
        from .folder_datasets import resolve_folder_config
        config=resolve_folder_config(config)
    root=Path(config['data_root'])
    if not root.is_absolute(): root=ROOT/root
    keys=config['sessions']
    test_keys=set(config['test_sessions'])
    val_keys=set(config.get('validation_sessions',[]))
    if len(keys)!=len(set(keys)) or (test_keys | val_keys)-set(keys) or test_keys & val_keys:
        raise ValueError('Invalid or overlapping explicit session split lists')
    grouped=config.get('validation_strategy') == 'grouped_session_by_contact_id'
    if val_keys and not grouped:
        raise ValueError('validation_sessions requires grouped_session_by_contact_id')
    folders=[root/name for name in keys]
    sessions=[load_session(p,config) for p in folders]
    ids=[s['info']['session_id'] for s in sessions]
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate physical session')
    if config.get('expected_sources') is not None:
        from .folder_datasets import source_identity
        actual={key:source_identity(s['info']) for key,s in zip(keys,sessions)}
        if actual != config['expected_sources']:
            raise ValueError('Dataset or metadata changed after folder snapshot')
    indices={k:[] for k in ['train','val','test']}
    train_rows=[]
    for sid,s in enumerate(sessions):
        key=keys[sid]
        if grouped:
            part='test' if key in test_keys else 'val' if key in val_keys else 'train'
            split={p:s['ends'] if p==part else np.array([],dtype=int)
                   for p in ('train','val','test')}
        else:
            split=split_endpoints(s,config,test=key in test_keys)
        s['info']['split_counts']={k:len(v) for k,v in split.items()}
        for part,ends in split.items(): indices[part] += [(sid,int(i)) for i in ends]
        # fit input scaler on unique rows actually consumed by training windows
        mask=np.zeros(len(s['x']),dtype=bool)
        for end in split['train']: mask[end-config['window_samples']+1:end+1]=True
        if mask.any(): train_rows.append(s['x'][mask])
    for k,v in indices.items():
        if not v and not (k=='test' and config.get('allow_empty_test',False)):
            raise ValueError(f'No usable {k} windows')
        indices[k]=np.asarray(v,dtype=np.int64).reshape(-1,2)
    train_x=np.concatenate(train_rows)
    train_y=np.asarray([sessions[s]['y'][i] for s,i in indices['train']])
    scaler={'x_mean':train_x.mean(0,dtype=np.float64),'x_std':train_x.std(0,dtype=np.float64),
            'y_mean':train_y.mean(0,dtype=np.float64),'y_std':train_y.std(0,dtype=np.float64)}
    scaler['x_std']=np.maximum(scaler['x_std'],1e-6);scaler['y_std']=np.maximum(scaler['y_std'],1e-6)
    return sessions,indices,scaler

def normalize_sessions(sessions,scaler):
    for s in sessions:
        s['x_scaled']=((s['x']-np.asarray(scaler['x_mean']))/np.asarray(scaler['x_std'])).astype(np.float32)
        # invalid rows are never window members; keep NaNs to catch misuse
        s['y_scaled']=((s['y']-np.asarray(scaler['y_mean']))/np.asarray(scaler['y_std'])).astype(np.float32)

def batch_arrays(sessions,indices,window,thresholds):
    x=np.stack([sessions[s]['x_scaled'][i-window+1:i+1] for s,i in indices])
    y=np.stack([sessions[s]['y_scaled'][i] for s,i in indices])
    raw_y=np.stack([sessions[s]['y'][i] for s,i in indices])
    labels=load_labels(raw_y,np.asarray(thresholds))
    ids=np.asarray([sessions[s]['id']-1 for s,i in indices],dtype=np.int64)
    return x,y,labels,ids
