#!/usr/bin/env python3
"""
Script de inicialização simplificado que usa SQLite em vez de PostgreSQL.
Não requer Docker ou MongoDB para funcionar.
"""

import pandas as pd
from sqlalchemy import create_engine
import os
import sys



def setup_sqlite():
    """Carrega dados de emendas parlamentares no SQLite."""
    print("🔄 Iniciando carga de dados de emendas parlamentares no SQLite...")

    # Cria diretório para dados se não existir
    os.makedirs('local_deploy/data', exist_ok=True)

    # Database URL para SQLite
    db_path = os.path.abspath('local_deploy/data/db_transparencia.db')
    DB_SQL_URL = f"sqlite:///{db_path}"

    try:
        engine = create_engine(DB_SQL_URL)

        # Caminho do CSV
        csv_path = os.path.join('data', 'EmendasParlamentares.csv')

        if not os.path.exists(csv_path):
            print(f"❌ Erro: Arquivo {csv_path} não encontrado")
            return False

        # Carrega o CSV de emendas parlamentares
        print(f"📂 Carregando CSV: {csv_path}")
        df = pd.read_csv(
            csv_path,
            delimiter=';',
            encoding='latin1',
            decimal=',',
            quotechar='"'
        )

        # Renomeia colunas para nomes sem acentos e mais simples
        df.columns = [
            'codigo_emenda', 'ano_emenda', 'tipo_emenda', 'codigo_autor',
            'nome_autor', 'numero_emenda', 'localidade_gasto', 'codigo_municipio_ibge',
            'municipio', 'codigo_uf_ibge', 'uf', 'regiao', 'codigo_funcao',
            'nome_funcao', 'codigo_subfuncao', 'nome_subfuncao', 'codigo_programa',
            'nome_programa', 'codigo_acao', 'nome_acao', 'codigo_plano_orcamentario',
            'nome_plano_orcamentario', 'valor_empenhado', 'valor_liquidado',
            'valor_pago', 'valor_restos_pagar_inscritos', 'valor_restos_pagar_cancelados',
            'valor_restos_pagar_pagos'
        ]

        # Cria a tabela 'emendas_parlamentares'
        print(f"💾 Carregando {len(df)} registros de emendas parlamentares...")
        df.to_sql('emendas_parlamentares', engine, if_exists='replace', index=False, chunksize=1000)

        print(f"✅ Banco SQLite criado com sucesso!")
        print(f"   Localização: {db_path}")
        print(f"   Registros: {len(df)}")
        return True

    except Exception as e:
        print(f"❌ Erro na carga de emendas parlamentares: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  Setup de Banco SQLite para Desenvolvimento Local")
    print("=" * 60)
    print()

    success = setup_sqlite()

    print()
    if success:
        print("✅ Setup concluído com sucesso!")
        print()
        print("Para iniciar a aplicação:")
        print("  ./mcp_client/start_chat.sh")
    else:
        print("❌ Setup falhou. Verifique os erros acima.")
        sys.exit(1)
