"""Strict JSON configuration validation; paths are relative to the config."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator


def load_json(path):
    def reject(value):
        raise ValueError(f'Non-finite JSON number: {value}')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'),
                      parse_constant=reject, object_pairs_hook=unique)


def load_run_config(path, schema_path):
    path = Path(path).resolve()
    config = load_json(path)
    if not isinstance(config, dict):
        raise ValueError('Configuration must be an object')
    config.setdefault('warmup_frames', 0)
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)
    validator.validate(config)
    if config.get('record_type') != 'run_config':
        raise ValueError('Expected run_config')
    resolved = dict(config)
    for key in ('input_manifest_path', 'output_root', 'adapter_options_path'):
        if config[key] is not None:
            resolved[key] = str((path.parent / config[key]).resolve())
    resolved['assets'] = [dict(asset, path=str((path.parent / asset['path']).resolve()))
                          for asset in config['assets']]
    return resolved
