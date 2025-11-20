import sqlite3
import shutil
import os
import sys
from datetime import datetime

# Config
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'revest.db'))
BAD_IDS = [1, 2]  # IDs de doação a remover

if not os.path.exists(DB_PATH):
    print(f"Erro: banco não encontrado em {DB_PATH}")
    sys.exit(1)

# Backup
now = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = DB_PATH + f'.bkp_{now}'
shutil.copy2(DB_PATH, backup_path)
print(f"Backup criado: {backup_path}")

# Connect
conn = sqlite3.connect(DB_PATH)
# Connect
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

placeholders = ','.join('?' for _ in BAD_IDS)

# Mostrar contagens antes usando os nomes reais das tabelas
print('\nAntes:')
cur.execute(f"SELECT doacao.ID_Doacao, COUNT(doacao_item.ID_Item) FROM doacao LEFT JOIN doacao_item ON doacao.ID_Doacao = doacao_item.ID_Doacao WHERE doacao.ID_Doacao IN ({placeholders}) GROUP BY doacao.ID_Doacao", BAD_IDS)
rows = cur.fetchall()
if rows:
    for r in rows:
        print(f"  Doacao {r[0]} tem {r[1]} itens")
else:
    print("  Nenhuma das doações especificadas foi encontrada ou não têm itens.")

# Contagens específicas
cur.execute(f"SELECT COUNT(*) FROM doacao_item WHERE ID_Doacao IN ({placeholders})", BAD_IDS)
items_before = cur.fetchone()[0]
cur.execute(f"SELECT COUNT(*) FROM doacao WHERE ID_Doacao IN ({placeholders})", BAD_IDS)
doacoes_before = cur.fetchone()[0]
print(f"  Contagem total de itens a remover: {items_before}")
print(f"  Contagem total de doações alvo: {doacoes_before}")

# Deletar itens relacionados
cur.execute(f"DELETE FROM doacao_item WHERE ID_Doacao IN ({placeholders})", BAD_IDS)
# Deletar doacoes
cur.execute(f"DELETE FROM doacao WHERE ID_Doacao IN ({placeholders})", BAD_IDS)

conn.commit()

# Mostrar contagens depois
cur.execute(f"SELECT COUNT(*) FROM doacao_item WHERE ID_Doacao IN ({placeholders})", BAD_IDS)
items_after = cur.fetchone()[0]
cur.execute(f"SELECT COUNT(*) FROM doacao WHERE ID_Doacao IN ({placeholders})", BAD_IDS)
doacoes_after = cur.fetchone()[0]

print('\nOperação executada.')
print(f"  Itens deletados: {items_before - items_after}")
print(f"  Doações deletadas: {doacoes_before - doacoes_after}")
print(f"  Doações restantes com esses IDs: {doacoes_after}")

conn.close()
print('\nPronto.')
