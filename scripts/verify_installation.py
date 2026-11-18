"""Reprodução em dados temporários, HTTP real e uma pergunta conhecida."""
import sys,json,tempfile,threading,time
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from support_rag.settings import settings
from support_rag.bootstrap import bootstrap
from support_rag.api.server import make_server
from support_rag.utils.io import save
with tempfile.TemporaryDirectory() as temp:
    config=settings();config['data_dir']=temp;bootstrap(config)
    server=make_server(config,port=0)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base='http://127.0.0.1:'+str(server.server_address[1])
    results={'answer_mode':config['answer_mode'],'isolated_data_directory':True,'steps':[]}
    try:
        for path in ['/health','/ready','/']:
            with urlopen(base+path,timeout=5) as r:
                body=r.read().decode();results['steps'].append({'endpoint':path,'status':r.status,'body':body[:500] if path!='/' else 'UI HTML loaded'})
        for question,expected in [('Como validar um merge muitos para um usando validate?','answer'),
                                  ('Como configurar um cluster Spark?','handoff'),
                                  ('Meu merge duplicou linhas. Como resolver?','clarify')]:
            started=time.perf_counter()
            req=Request(base+'/answer',data=json.dumps({'question':question,'method':config['default_method']}).encode(),headers={'Content-Type':'application/json'})
            with urlopen(req,timeout=240) as r:output=json.load(r)
            passed=output['action']==expected
            if expected=='answer':
                text=' '.join(c['text'] for c in output['claims'])
                passed=passed and ('many_to_one' in text or 'm:1' in text) and 'one_to_many' not in text
            results['steps'].append({'question':question,'expected':expected,'passed':passed,'seconds':time.perf_counter()-started,'output':output})
            print(question,output['action'],passed,flush=True)
        results['passed']=all(s.get('passed',True) for s in results['steps'])
    finally:
        server.shutdown();server.server_close();thread.join()
    output_file = 'clean_installation_v3.json' if config['answer_mode'] == 'controlled' else 'clean_installation_experimental.json'
    save(ROOT/'reports'/output_file,results)
    print(json.dumps({'passed':results['passed']},indent=2))
    sys.exit(0 if results['passed'] else 1)
