from pathlib import Path
import sys
s=Path('deployment-text.json').read_text(encoding='utf-8')
if len(sys.argv)==1:print(len(s))
else:print(s[int(sys.argv[1]):int(sys.argv[1])+int(sys.argv[2])],end='')
