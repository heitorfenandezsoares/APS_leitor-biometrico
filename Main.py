import tkinter as tk
from PIL import Image, ImageTk
from DetectorRosto import DetectorRosto
from db_Config import enviarAoBanco, pegar_imagem_para_comparar, verificar_cpf_existente
from blinker import signal
import re
import cv2

#CENTRALIZAR NA JANELA
def centralizar_janela(janela, largura, altura):
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    pos_x = (largura_tela // 2) - (largura // 2)
    pos_y = (altura_tela // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

def formatar_cpf(texto):
    texto = re.sub(r'\D', '', texto)  # Remove caracteres que não são números
    if len(texto) <= 3:
        return texto
    elif len(texto) <= 6:
        return f"{texto[:3]}.{texto[3:]}"
    elif len(texto) <= 9:
        return f"{texto[:3]}.{texto[3:6]}.{texto[6:]}"
    else:
        return f"{texto[:3]}.{texto[3:6]}.{texto[6:9]}-{texto[9:11]}"

# MASCARA PARA CPF
def aplicar_mascara_cpf(event=None):
    # Verificamos se os widgets existem antes de tentar acessá-los
    try:
        if 'cpfCadastro' in globals():
            cpfCadastro_texto = cpfCadastro.get()
            cpfCadastro_formatado = formatar_cpf(cpfCadastro_texto)
            cpfCadastro.delete(0, tk.END)
            cpfCadastro.insert(0, cpfCadastro_formatado)
    except tk.TclError:
        pass # O widget pode não estar visível ou ter sido destruído
        
    try:
        if 'cpfLogin' in globals():
            cpfLogin_texto = cpfLogin.get()
            cpfLogin_formatado = formatar_cpf(cpfLogin_texto)
            cpfLogin.delete(0, tk.END)
            cpfLogin.insert(0, cpfLogin_formatado)
    except tk.TclError:
        pass # O widget pode não estar visível

#PRIMEIRO PARAMETRO ESCONDE, SEGUNDO, APARECE
def mostrar_tela(frame_atual_esconde, frame_novo_aparece):
    frame_atual_esconde.pack_forget()
    frame_novo_aparece.pack(fill="both", expand=True)

#janela
def configurar_janela():
    janela = tk.Tk()
    janela.title("Leitor Biometrico")
    janela.configure(bg="#32858C")
    # --- ALTERADO PARA 1000x600 ---
    centralizar_janela(janela, 1000, 600)
    return janela

#INICIAL
def criar_tela_inicial():
    # --- MUDANÇA PRINCIPAL ---
    # A tela agora é um Label com a imagem de fundo
    inicial = tk.Label(janela, image=background_image)

    # Não precisamos mais do bg_label, pois 'inicial' JÁ É a imagem
    
    # --- REMOVIDO top_filler (era o frame cinza) ---
    
    buttonlogin = tk.Button(inicial, text="LOGIN", bd=0, bg="green", fg="black", font=("Helvetica", 18, 'bold'), width=20, command=lambda: mostrar_tela(inicial, tela_logar))
    # Ajustado o 'row' para centralizar
    buttonlogin.grid(row=1, column=0, pady=10) 

    cadastrar = tk.Button(inicial, text="Não fez o cadastro? Clique, aqui!", bd=0, fg="black", command=lambda: mostrar_tela(inicial, cadastro))
    cadastrar.grid(row=2, column=0, pady=5)






    # --- REMOVIDO bottom_filler (era o frame cinza) ---

    # Configuração de layout para centralização
    # Linha 0 (vazia) expande, empurrando o conteúdo para o meio
    inicial.grid_rowconfigure(0, weight=1) 
    # Linha 3 (vazia, abaixo dos botões) expande
    inicial.grid_rowconfigure(3, weight=1)
    # Coluna 0 expande, centralizando os botões
    inicial.grid_columnconfigure(0, weight=1)
    
    return inicial

#TELA DE LOGIN
def tela_login():
    # --- MUDANÇA PRINCIPAL ---
    tela_logar = tk.Label(janela, image=background_image)

    # --- REMOVIDO top_filler ---
    
    # 'bg' foi removido para o label ficar transparente
    labelCpfCadastro = tk.Label(tela_logar, text="CPF:", fg="black", font=("Helvetica", 16))
    labelCpfCadastro.grid(row=1, column=0, padx=(0, 10), pady=10, sticky="")
    
    
    # ---------------------------------- BOTAO TELA INICIAL ---------------------------------------------------
    botao_voltar = tk.Button(janela, text="TELA INICIAL", borderwidth=2, highlightthickness=0, command=lambda: mostrar_tela(tela_logar, inicial))

    # 3. Posicionar o botão na janela
    botao_voltar.pack(pady=0, anchor="n") # Adiciona um espaçamento vertical


    global cpfLogin
    cpfLogin = tk.Entry(tela_logar, width=20, font=("Helvetica", 24))
    cpfLogin.grid(row=1, column=1, padx=(10, 0), pady=10, sticky="w")
    cpfLogin.bind("<KeyRelease>", aplicar_mascara_cpf)

    global mensagem_login
    # 'bg' foi removido para o label ficar transparente
    mensagem_login = tk.Label(tela_logar, text='', font=("Helvetica", 16, "bold"), fg='black')
    mensagem_login.grid(row=2, column=0, columnspan=2, pady=10)

    logar = tk.Button(tela_logar, text="ENTRAR", font=("Helvetica", 16), command=entrar_login)
    logar.grid(row=3, column=0, columnspan=2, pady=10)

    # --- REMOVIDO bottom_filler ---

    # Linha 0 (vazia) expande
    tela_logar.grid_rowconfigure(0, weight=1) 
    # Linha 4 (vazia, abaixo dos botões) expande
    tela_logar.grid_rowconfigure(4, weight=1)
    # Colunas 0 e 1 expandem para centralizar o conjunto
    tela_logar.grid_columnconfigure(0, weight=1)
    tela_logar.grid_columnconfigure(1, weight=1)
    
    return tela_logar

#ESCONDE A TELA DE LOGIN E CHAMA A TELA FACIAL JUNTO COM PARÂMETRO PARA SABER DE QUAL TELA FOI CHAMADO
def entrar_login():
    if cpfLogin.get() != "":
        mostrar_tela(tela_logar, criar_tela_cadastro_facial("logar"))
    else:
        mensagem_login.config(text="PREENCHER TODOS OS CAMPOS!")
        mensagem_login.after(3000, lambda: mensagem_login.config(text=""))

#CADASTRO NO BANCO
def criar_tela_cadastro():
    # --- MUDANÇA PRINCIPAL ---
    cadastro = tk.Label(janela, image=background_image)

    # --- REMOVIDO top_filler ---
    
    # 'bg' foi removido para o label ficar transparente
    labelNomeCadastro = tk.Label(cadastro, text="NOME:", fg="black", font=("Helvetica", 16))
    labelNomeCadastro.grid(row=1, column=0, padx=(0, 10), pady=10, sticky="")
    
    global nomeCadastro
    nomeCadastro = tk.Entry(cadastro, width=40, font=("Helvetica", 24))
    nomeCadastro.grid(row=1, column=1, padx=(10, 0), pady=10, sticky="")

    # 'bg' foi removido para o label ficar transparente
    labelCpfCadastro = tk.Label(cadastro, text="CPF:", fg="black", font=("Helvetica", 16))
    labelCpfCadastro.grid(row=2, column=0, padx=(0, 10), pady=10, sticky="")
    
    global cpfCadastro
    cpfCadastro = tk.Entry(cadastro, width=40, font=("Helvetica", 24))
    cpfCadastro.grid(row=2, column=1, padx=(10, 0), pady=10, sticky="")
    cpfCadastro.bind("<KeyRelease>", aplicar_mascara_cpf)

    global mensagem_cadastro
    # 'bg' foi removido para o label ficar transparente
    mensagem_cadastro = tk.Label(cadastro, text='', font=("Helvetica", 16, "bold"), fg='black')
    mensagem_cadastro.grid(row=3, column=0, columnspan=2, pady=10)

    botao_enviar_banco = tk.Button(cadastro, text="ENVIAR", font=("Helvetica", 20), command=enviar_cadastro)
    botao_enviar_banco.grid(row=4, column=0, columnspan=2, pady=10)

    # --- REMOVIDO bottom_filler ---

    cadastro.grid_rowconfigure(0, weight=1) 
    # Linha 5 (vazia) expande
    cadastro.grid_rowconfigure(5, weight=1)
    cadastro.grid_columnconfigure(0, weight=1)
    cadastro.grid_columnconfigure(1, weight=1)

    return cadastro

#ESCONDE A TELA DE CADASTRO E CHAMA A TELA FACIAL JUNTO COM PARÂMETRO PARA SABER DE QUAL TELA FOI CHAMADO
def enviar_cadastro():
    nome_digitado = nomeCadastro.get()
    cpf_digitado = cpfCadastro.get()

    if nome_digitado == "" or cpf_digitado == "":
        mensagem_cadastro.config(text="PREENCHER TODOS OS CAMPOS!")
        mensagem_cadastro.after(3000, lambda: mensagem_cadastro.config(text=""))
    
    elif verificar_cpf_existente(cpf_digitado): 
        mensagem_cadastro.config(text="ESTE CPF JÁ ESTÁ CADASTRADO!")
        mensagem_cadastro.after(3000, lambda: mensagem_cadastro.config(text=""))
        
    else:
        mostrar_tela(cadastro, criar_tela_cadastro_facial("cadastrar"))
    

#TELA FACIAL
def criar_tela_cadastro_facial(tipo):
    global sair_facial
    # --- MUDANÇA PRINCIPAL ---
    # Esta tela (que usa .pack()) também vira um Label com a imagem
    cadastroFacial = tk.Label(janela, image=background_image)

    # Não precisamos mais do if background_image e bg_label
    
    button_iniciar = tk.Button(cadastroFacial, text="INICIAR CAPTURA FACIAL", command=iniciar_captura, font=("Helvetica", 16))
    button_iniciar.pack(pady=20)

    # 'bg' removido para transparência
    aviso = tk.Label(cadastroFacial, text="Certifique-se de possuir uma câmera.", font=("Helvetica", 12), fg='black')
    aviso.pack(pady=3)

    global mensagem_resultado
    # 'bg' removido para transparência
    mensagem_resultado = tk.Label(cadastroFacial, font=("Helvetica", 16), fg='black')
    mensagem_resultado.pack(pady=10)

    global imagem_label
    # 'bg' removido para transparência
    imagem_label = tk.Label(cadastroFacial)
    imagem_label.pack(pady=10)

    global sinal_qual_botao_clicou
    sinal_qual_botao_clicou = tipo

    global detector
    detector = DetectorRosto(mensagem_resultado, imagem_label) 

    sair_facial = cadastroFacial

    return cadastroFacial

#INICIA A CAPTURA DO ROSTO
def iniciar_captura():
    mensagem_resultado.config(text="")
    detector.iniciar_captura()

#COM BASE NO PARÂMETRO 'TIPO' DA TELA FACIAL, SERÁ ACEITA UMA DAS CONDIÇÕES
def voltar_cadastro_login(sender, **kwargs):
    if (sinal_qual_botao_clicou == "logar"):
        
        sinal_para_comparar_imagem = signal('chamar_agora_comparador')
        comparar_cpf = cpfLogin.get()
        detector.verificar_sinais(sinal_para_comparar_imagem, comparar_cpf=comparar_cpf)
        
    elif (sinal_qual_botao_clicou == "cadastrar"):

        sinal_para_enviar_ao_banco = signal('chamar_agora_enviar_banco')
        nome_cadastro = nomeCadastro.get()
        cpf_cadastro = cpfCadastro.get()
        detector.verificar_sinais(sinal_para_enviar_ao_banco, nome_cadastro=nome_cadastro, cpf_cadastro=cpf_cadastro)
    return

#SINAL EMITIDO PELO BACK, PARA SABER QUE A CAPTURA TERMINOU
def conectar_sinal_voltar():
    voltar_para_cadastro_login = signal('voltar_cadastro_login')
    voltar_para_cadastro_login.connect(voltar_cadastro_login)


#SINAL QUE É RECEBIDO APÓS SER VALIDADO O LOGIN
def sinal_meioAmbiente():
    ir_plataformaMeioAmbiente = signal('ir_plataformaMeioAmbiente')
    ir_plataformaMeioAmbiente.connect(informacoes_para_meioAmbiente)

#PEGA NOME E PERMISSÃO DO USUARIO E ENVIA PARA A ULTIMA TELA
def informacoes_para_meioAmbiente(sender, **kwargs):
    cpf = cpfLogin.get()
    array_banco = detector.informacoes_banco_plataformaMeioAmbiente(cpf)
   
    nome_banco = array_banco[0]
    permissao_banco = array_banco[1]

    if (nome_banco != '' and permissao_banco != ''):
        mostrar_tela(sair_facial, plataformaMeioAmbiente(nome_banco, permissao_banco))
    else:
        print("array_nome_permissao está vazio")

#PLATAFORMA MEIO AMBIENTE (ULTIMA TELA)
def plataformaMeioAmbiente(nome, permissao):
    # --- MUDANÇA PRINCIPAL ---
    meioAmbiente = tk.Label(janela, image=background_image)

    # --- REMOVIDO top_filler ---
    
    texto_bem_vindo = "BEM VINDO!"
    if nome and permissao:
        texto_bem_vindo = f"BEM VINDO! {nome}, {permissao} da Plataforma Meio Ambiente."

    # 'bg' removido para transparência
    labelMeioAmbiente = tk.Label(meioAmbiente, text=texto_bem_vindo, fg="black", font=("Helvetica", 16))
    labelMeioAmbiente.grid(row=1, column=0, pady=10) #Ajustado 'row'

    # --- REMOVIDO bottom_filler ---

    # Configuração de layout para centralização
    meioAmbiente.grid_rowconfigure(0, weight=1) 
    meioAmbiente.grid_rowconfigure(2, weight=1) # Linha vazia abaixo
    meioAmbiente.grid_columnconfigure(0, weight=1)

    return meioAmbiente


janela = configurar_janela()

# Carrega a imagem e a redimensiona para o tamanho da janela (1000x600)
try:
    img_pil = Image.open("Background.jpg")
    # --- ALTERADO PARA 1000x600 ---
    img_redimensionada = img_pil.resize((1000, 600), Image.LANCZOS)
    background_image = ImageTk.PhotoImage(img_redimensionada)
except Exception as e:
    print(f"Erro ao carregar Background.jpg: {e}")
    background_image = None

# Cria todas as telas (frames)
inicial = criar_tela_inicial()
cadastro = criar_tela_cadastro()
tela_logar = tela_login()
meioAmbiente = plataformaMeioAmbiente(None, None) 

#FUNÇÃO SEMPRE SERÁ CHAMADA PARA SABER QUANDO É FEITO O SINAL NO BACKEND
conectar_sinal_voltar()
sinal_meioAmbiente()

#CHAMA A TELA INICIAL
inicial.pack(fill="both", expand=True)
janela.mainloop()