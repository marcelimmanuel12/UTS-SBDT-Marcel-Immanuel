"""Validasi offline berkas Python, konfigurasi Keycloak, dan manifest Kubernetes."""
import ast
import json
from pathlib import Path
import yaml

root = Path(__file__).resolve().parents[1]
pyfiles = list((root / 'app').glob('*.py')) + list((root / 'tests').glob('*.py'))
for file in pyfiles:
    ast.parse(file.read_text(encoding='utf-8'))
realm = json.loads((root / 'keycloak/realm-sbdt.json').read_text(encoding='utf-8'))
assert realm['realm'] == 'sbdt'
assert {c['clientId'] for c in realm['clients']} >= {'api-service','sbdt-cli'}
resources = []
for f in sorted((root / 'k8s').glob('*.yaml')):
    resources.extend(yaml.safe_load_all(f.read_text(encoding='utf-8')))
kinds = [r['kind'] for r in resources]
assert kinds.count('StatefulSet') == 2
assert 'Ingress' in kinds and 'Secret' in kinds and 'ConfigMap' in kinds
assert len([r for r in resources if r['kind'] == 'Service']) >= 6
print(f'VALID: {len(pyfiles)} Python, {len(resources)} Kubernetes resources, Keycloak realm {realm["realm"]}')
