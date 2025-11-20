import sqlite3

# Caminhos dos bancos
BACKUP_DB = 'revest.db.bkp_20251116_172833'
DEST_DB = 'revest.db'

def copiar_doadores(origem, destino):
    conn_origem = sqlite3.connect(origem)
    conn_destino = sqlite3.connect(destino)
    cur_origem = conn_origem.cursor()
    cur_destino = conn_destino.cursor()

    # Busca todos os doadores do banco antigo
    cur_origem.execute('SELECT * FROM doador')
    doadores = cur_origem.fetchall()

    # Descobre os nomes das colunas
    colunas = [desc[0] for desc in cur_origem.description]
    colunas_str = ', '.join(colunas)
    placeholders = ', '.join(['?'] * len(colunas))

    # Insere cada doador no banco novo (ignora duplicados pelo email)
    for doador in doadores:
        try:
            cur_destino.execute(f'INSERT OR IGNORE INTO doador ({colunas_str}) VALUES ({placeholders})', doador)
        except Exception as e:
            print(f'Erro ao inserir doador: {e}')

    conn_destino.commit()
    conn_origem.close()
    conn_destino.close()
    print(f'{len(doadores)} doadores copiados do backup para o banco atual.')

if __name__ == '__main__':
    copiar_doadores(BACKUP_DB, DEST_DB)
    print('Migração concluída.')
