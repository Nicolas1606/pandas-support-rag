"""Leitura do snapshot Markdown distribuído; versão fixada para reprodução."""
import re
def parse_snapshot(path,markdown):
    title=path;section=path;blocks=[];buffer=[]
    def flush():
        if buffer:
            text='\n'.join(buffer).strip()
            if text:blocks.append({'section':section,'anchor':'','kind':'markdown','text':text})
            buffer.clear()
    for line in markdown.splitlines():
        if re.match(r'^#{1,4} ',line):
            flush();section=re.sub(r'^#+ ','',line)
            if line.startswith('# '):title=section
        else:buffer.append(line)
    flush()
    return {'url':'https://pandas.pydata.org/pandas-docs/version/2.2.3/'+path,
            'title':title,'version':'2.2.3','blocks':blocks}
