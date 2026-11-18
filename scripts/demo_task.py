"""Execute a representative task on synthetic data using pandas 2.2.3."""
import json
import sys
from io import StringIO
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from support_rag.bootstrap import bootstrap
from support_rag.pipeline import Pipeline
from support_rag.settings import settings
from support_rag.utils.io import save


def main():
    if pd.__version__ != '2.2.3':
        raise SystemExit('Este exemplo usa pandas 2.2.3.')
    config = settings()
    if config['answer_mode'] != 'controlled':
        raise SystemExit('Selecione o modo controlado.')
    bootstrap(config)
    engine = Pipeline(config)
    question = 'Como preservar NA como texto no CSV do cadastro?'
    csv_advice = engine.answer(question)
    assert csv_advice.get('contract_id') == 'csv_na_text'
    customers = pd.read_csv(StringIO('id_cliente,codigo\n1,NA\n2,SEM_DADO'),
                            keep_default_na=False, na_values=['SEM_DADO'])
    assert customers.loc[0, 'codigo'] == 'NA' and pd.isna(customers.loc[1, 'codigo'])
    join_advice = engine.answer('Como validar o merge de pedidos com clientes como muitos para um?')
    assert join_advice.get('contract_id') == 'merge_m1'
    orders = pd.DataFrame({'id_cliente': [1, 1, 2], 'pedido': ['A', 'B', 'C']})
    enriched = orders.merge(customers, on='id_cliente', validate='many_to_one')
    assert len(enriched) == len(orders)
    try:
        orders.merge(pd.concat([customers, customers.iloc[:1]]), on='id_cliente', validate='many_to_one')
    except pd.errors.MergeError:
        rejected = True
    else:
        raise AssertionError('A duplicata no cadastro deveria impedir a junção.')
    result = dict(pandas=pd.__version__, synthetic=True, human_timing_measured=False,
                  original_orders=len(orders), joined_orders=len(enriched),
                  literal_na_preserved=True, missing_marker_parsed=True,
                  duplicate_customer_rejected=rejected,
                  outputs=[csv_advice, join_advice])
    save(ROOT/'reports/demo_task.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'outputs'}, indent=2))


if __name__ == '__main__':
    main()
