import sqlite3

# Nome do arquivo do banco de dados SQLite
DATABASE_FILE = 'db_Users.db'

def criar_banco_se_nao_existir():
    """Garante que o banco e a tabela existam."""
    conexao = sqlite3.connect(DATABASE_FILE)
    coordenador = conexao.cursor()
    
    # Cria a tabela se ela não existir
    coordenador.execute("""
    CREATE TABLE IF NOT EXISTS tb_usuarios_6_aps (
        usu_nome TEXT NOT NULL,
        usu_permissao TEXT NOT NULL,
        usu_cpf TEXT PRIMARY KEY NOT NULL,
        usu_rosto BLOB NOT NULL
    );
    """)
    
    conexao.commit()
    conexao.close()

def enviarAoBanco(nome, cpf, rosto):
    """Insere um novo usuário no banco de dados SQLite."""
    criar_banco_se_nao_existir() # Garante que o banco e a tabela existam
    
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        coordenador = conexao.cursor()

        inserirTbAps = "INSERT INTO tb_usuarios_6_aps (usu_nome, usu_permissao, usu_cpf, usu_rosto) VALUES (?, ?, ?, ?)"
        valoresTbAps = (nome, "usuario", cpf, rosto)
        
        coordenador.execute(inserirTbAps, valoresTbAps)
        conexao.commit() # Salva as alterações no banco

        print('Enviado no banco SQLite')
        
    except sqlite3.Error as e:
        print(f"Erro ao inserir no SQLite: {e}")
    finally:
        if 'conexao' in locals() and conexao:
            coordenador.close()
            conexao.close()

def pegar_imagem_para_comparar(cpf):
    """Busca a imagem (rosto) de um usuário pelo CPF."""
    criar_banco_se_nao_existir()
    
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        coordenador = conexao.cursor()

        coordenador.execute("SELECT usu_rosto FROM tb_usuarios_6_aps WHERE usu_cpf = ?", (cpf,))
        resultado = coordenador.fetchone()
        
        if resultado:
            imagem_bytes_banco = resultado[0]
            return imagem_bytes_banco
        else:
            print("Nenhuma imagem encontrada para o CPF especificado.")
            return None

    except sqlite3.Error as e:
        print(f"Erro ao buscar no SQLite: {e}")
        return None
    finally:
        if 'conexao' in locals() and conexao:
            coordenador.close()
            conexao.close()

def ir_para_plataformaMeioAmbiente(cpf):
    """Busca o nome e a permissão de um usuário pelo CPF."""
    criar_banco_se_nao_existir()
    
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        coordenador = conexao.cursor()

        coordenador.execute("SELECT usu_nome, usu_permissao FROM tb_usuarios_6_aps WHERE usu_cpf = ?", (cpf,))
        resultado = coordenador.fetchone()
        
        if resultado:
            nome = resultado[0]
            permissao = resultado[1]
            array_nome_permissao = [nome, permissao]
            return array_nome_permissao
        else:
            print("Nenhum nome/permissão encontrado para o CPF especificado.")
            return [None, None] # Retorna uma lista vazia para evitar erros

    except sqlite3.Error as e:
        print(f"Erro ao buscar no SQLite: {e}")
        return [None, None]
    finally:
        if 'conexao' in locals() and conexao:
            coordenador.close()
            conexao.close()


def verificar_cpf_existente(cpf):
    """Verifica se um CPF já existe no banco. Retorna True se existir, False se não."""
    criar_banco_se_nao_existir()
    
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        coordenador = conexao.cursor()

        coordenador.execute("SELECT 1 FROM tb_usuarios_6_aps WHERE usu_cpf = ?", (cpf,))
        resultado = coordenador.fetchone()
        
        if resultado:
            return True  # CPF encontrado
        else:
            return False # CPF não encontrado

    except sqlite3.Error as e:
        print(f"Erro ao verificar CPF no SQLite: {e}")
        return False # Trata o erro como se não existisse para evitar bloqueios
    finally:
        if 'conexao' in locals() and conexao:
            coordenador.close()
            conexao.close()