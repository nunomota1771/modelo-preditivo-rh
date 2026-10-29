"""Regras fixas da Fase 3, reutilizadas pelo pipeline nas Fases 4 a 6."""

import numpy as np
import pandas as pd

COLUNAS_ORIGINAIS = [
    'cidade', 'indice_desenvolvimento_cidade', 'genero',
    'experiencia_relevante', 'inscricao_universidade', 'nivel_educacao',
    'area_formacao', 'anos_experiencia', 'dimensao_empresa',
    'tipo_empresa', 'anos_desde_ultimo_emprego', 'horas_formacao',
]


def preparar_registos(dados):
    """Limpar texto e criar variáveis sem aprender parâmetros nem usar o alvo."""
    if not isinstance(dados, pd.DataFrame):
        raise TypeError('Os dados devem ser um DataFrame pandas.')
    em_falta = sorted(set(COLUNAS_ORIGINAIS) - set(dados.columns))
    if em_falta:
        raise ValueError(f'Colunas obrigatórias em falta: {em_falta}')
    resultado = dados[COLUNAS_ORIGINAIS].copy()
    numericas = ['indice_desenvolvimento_cidade', 'horas_formacao']
    for coluna in resultado.columns.difference(numericas):
        texto = (resultado[coluna].astype('string').str.strip()
                 .str.replace(r'\s+', ' ', regex=True).replace('', pd.NA))
        resultado[coluna] = texto.astype(object).where(texto.notna(), np.nan)
    for coluna in numericas:
        original = resultado[coluna]
        convertido = pd.to_numeric(original, errors='coerce')
        if (original.notna() & convertido.isna()).any():
            raise ValueError(f'{coluna}: existem valores que não são números.')
        resultado[coluna] = convertido.astype(float)
    indice = resultado['indice_desenvolvimento_cidade']
    resultado.loc[~indice.between(0, 1), 'indice_desenvolvimento_cidade'] = np.nan
    resultado.loc[resultado['horas_formacao'] < 0, 'horas_formacao'] = np.nan
    texto = resultado['anos_experiencia'].astype('string')
    anos = pd.to_numeric(texto.str.extract(r'(\d+)', expand=False), errors='coerce')
    anos = anos.mask(texto.eq('Menos de 1 ano').fillna(False), 0)
    anos = anos.mask(texto.eq('Mais de 20 anos').fillna(False), 21)
    validas = {'Menos de 1 ano', 'Mais de 20 anos', '1 ano'} | {
        f'{i} anos' for i in range(2, 21)
    }
    if (texto.notna() & ~texto.isin(validas)).any():
        raise ValueError('anos_experiencia: categoria desconhecida; rever os dados.')
    resultado['anos_experiencia_num'] = anos.astype(float)
    resultado['log_horas_formacao'] = np.log1p(resultado['horas_formacao'])
    resultado['pouca_experiencia'] = anos.le(2).astype(float)
    resultado.loc[anos.isna(), 'pouca_experiencia'] = np.nan
    # As horas estão representadas pelo log. A universidade mantém o One-Hot.
    return resultado.drop(columns=['anos_experiencia', 'horas_formacao'])
