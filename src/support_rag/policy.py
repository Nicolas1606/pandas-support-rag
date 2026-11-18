"""Pré-condições explícitas para sintomas sem exemplo mínimo."""
import re,unicodedata

def clarification_needed(question,context=''):
    if len(context.strip())>=30:
        return None
    q=''.join(c for c in unicodedata.normalize('NFKD',question.casefold()) if not unicodedata.combining(c))
    personal=re.search(r'\b(meu|minha|meus|minhas|my|our)\b|nao sei',q)
    subject=re.search(r'\b(arquivo|file|csv|excel|merge|join|coluna|column|date|data|leitura)\b',q)
    symptom=re.search(r'duplic|errad|falh|nao abre|does not open|wrong|invertid|estranh',q)
    if personal and subject and symptom:
        return 'Qual é o exemplo mínimo da entrada, a operação executada e o resultado esperado? Inclua a mensagem de erro, se houver.'
    return None
