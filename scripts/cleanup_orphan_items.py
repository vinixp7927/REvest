import sqlite3
from pathlib import Path
import shutil
import time

BASE = Path(__file__).resolve().parents[1]
DB = BASE / 'revest.db'
if not DB.exists():
    print(f"Banco de dados não encontrado em: {DB}")
    raise SystemExit(1)

# Backup
bak = BASE / f"revest.db.bak.{int(time.time())}"
shutil.copy2(DB, bak)
print(f"Backup criado: {bak}")

conn = sqlite3.connect(str(DB))
cur = conn.cursor()

# Count orphans before
cur.execute("SELECT COUNT(*) FROM doacao_item WHERE ID_Doacao NOT IN (SELECT ID_Doacao FROM doacao);")
before = cur.fetchone()[0]
print(f"Itens órfãos antes: {before}")

if before > 0:
    cur.execute("DELETE FROM doacao_item WHERE ID_Doacao NOT IN (SELECT ID_Doacao FROM doacao);")
    deleted = cur.rowcount
    print(f"Itens deletados: {deleted}")
else:
    print("Nenhum item órfão encontrado.")

# Fechar conexão atual após alterações e commitar para permitir VACUUM
conn.commit()
conn.close()

# Abrir nova conexão apenas para VACUUM (não pode estar dentro de uma transação)
conn2 = sqlite3.connect(str(DB))
cur2 = conn2.cursor()
print("Executando VACUUM (pode demorar)...")
cur2.execute("VACUUM;")
conn2.commit()
conn2.close()

# Reabrir para contagem final
conn3 = sqlite3.connect(str(DB))
cur3 = conn3.cursor()
cur3.execute("SELECT COUNT(*) FROM doacao_item WHERE ID_Doacao NOT IN (SELECT ID_Doacao FROM doacao);")
after = cur3.fetchone()[0]
print(f"Itens órfãos depois: {after}")
conn3.close()
print("Limpeza finalizada com sucesso.")
