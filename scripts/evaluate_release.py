"""Avaliação real, com checkpoints e configuração congelada."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from support_rag.settings import settings
from support_rag.pipeline import Pipeline
from support_rag.utils.io import read,save,sha,canonical
from support_rag.evaluation.metrics import retrieval_metrics,percentile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--split',choices=['development','test'],required=True)
    ap.add_argument('--output-dir',type=Path,help='Pasta nova para reproduzir sem reutilizar checkpoints publicados')
    ap.add_argument('--ids',help='Subamostra explícita de desenvolvimento, separada por vírgulas')
    args=ap.parse_args()
    config=settings()
    if config['answer_mode'] != 'experimental_llm' or not args.output_dir:
        ap.error('Selecione RAG_ANSWER_MODE=experimental_llm e uma pasta --output-dir própria.')
    p=Pipeline(config)
    cases=[c for c in read(ROOT/'evaluation/cases.json') if c['split']==args.split]
    if args.ids:
        if args.split!='development':raise ValueError('Seleção por IDs é permitida apenas em desenvolvimento')
        chosen=set(args.ids.split(','));cases=[c for c in cases if c['id'] in chosen]
        if len(cases)!=len(chosen):raise ValueError('ID não encontrado no desenvolvimento')
    folder=args.output_dir or ROOT/'reports'/'release_evaluation'/(args.split+'_selection' if args.ids else args.split)
    frozen={'config':{k:v for k,v in config.items() if k not in ('root','data_dir')},'prompt_sha256':sha(p.prompt),'verifier_sha256':sha(p.verifier_prompt),'planner_sha256':sha(p.planner_prompt),
            'cases_sha256':sha(canonical(cases)),'corpus_id':p.manifest['corpus_id'],
            'reference_status':'source-authored; independent human review not performed',
            'model':config['model'],'started_at':time.time()}
    if (folder/'protocol.json').exists():
        previous=read(folder/'protocol.json')
        for k in ['config','prompt_sha256','verifier_sha256','planner_sha256','cases_sha256','corpus_id']:
            if previous[k]!=frozen[k]:raise ValueError('Execução anterior usa outra configuração; arquive antes de repetir.')
    else:save(folder/'protocol.json',frozen)
    rows=[]
    for i,case in enumerate(cases,1):
        checkpoint=folder/(case['id']+'.json')
        if checkpoint.exists():
            row=read(checkpoint)
        else:
            output=p.answer(case['question'],case.get('context',''),case.get('version'),config['default_method'])
            row={'case_id':case['id'],'family':case['family'],'question':case['question'],'topic':case['topic'],
                 'expected_action':case['expected_action'],'reference_facts':case['reference_facts'],
                 'retrieval':retrieval_metrics(output.get('sources',[]),case['evidence']),'output':output}
            save(checkpoint,row)
        rows.append(row)
        print(i,len(cases),case['id'],row['output']['action'],round(row['output']['total_ms']/1000,2),flush=True)
    actions={}
    for row in rows:
        action=row['output']['action'];actions[action]=actions.get(action,0)+1
    report={'protocol':frozen,'n':len(rows),'actions':actions,'rows':rows,
            'latency_median_ms':percentile([r['output']['total_ms'] for r in rows],.5),
            'latency_p95_ms':percentile([r['output']['total_ms'] for r in rows],.95),
            'action_matches':sum(r['output']['action']==r['expected_action'] for r in rows),
            'semantic_review':'not yet reviewed'}
    save(folder/'results.json',report)
    print('Concluído:',folder/'results.json',flush=True)
if __name__=='__main__':main()
