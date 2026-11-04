import sys,json,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'commercial/editor'))
from licensing import License,protect,machine_hash
with tempfile.TemporaryDirectory() as d:
    data=b'local-secret';encrypted=protect(data);assert data not in encrypted;assert protect(encrypted,True)==data
    assert len(machine_hash())==64
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,*args):return b'{"allowed":true}'
    with patch('urllib.request.urlopen',return_value=Response()) as request:
        license=License(d);license.activate(' Test@example.invalid ')
        first=json.loads(request.call_args.args[0].data)
        assert first['email']=='test@example.invalid' and 'device_hash' in first
        stored=Path(d,'activation.bin').read_bytes();assert b'test@example.invalid' not in stored
        restored=License(d);restored.require();second=json.loads(request.call_args.args[0].data)
        assert first['token_hash']==second['token_hash'] and first['device_hash']==second['device_hash']
        assert restored.active
    with patch('urllib.request.urlopen',side_effect=OSError('network')):
        try:restored.require();raise AssertionError('offline authorization bypass')
        except ValueError:pass
        assert not restored.active
print('PASS: Windows DPAPI roundtrip; stable credential/device; encrypted cache; online validation; no offline bypass')
