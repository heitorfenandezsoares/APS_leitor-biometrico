import time

import cv2
import numpy as np
from blinker import signal
from cvzone.FaceDetectionModule import FaceDetector
from PIL import Image, ImageTk
from deepface import DeepFace;

from db_Config import enviarAoBanco, pegar_imagem_para_comparar, ir_para_plataformaMeioAmbiente


class DetectorRosto():
    def __init__(self, label_mensagem, label_imagem):
        self.label_mensagem = label_mensagem
        self.label_imagem = label_imagem
        self.video = cv2.VideoCapture(0)
        self.detector = FaceDetector()
        self.start_time = 0 
        self.tempo_estipulado = 8  
        self.mensagem = ""
        self.img_salvar_banco = np.array([])
        
        # --- ADICIONADO ---
        self.mask = None  # Variável para a máscara
        self.bg_cv2 = None # Variável para o background redimensionado
        try:
            self.bg_original = cv2.imread("Background.jpg") # Carrega a imagem de fundo
        except Exception as e:
            print(f"Erro ao carregar Background.jpg: {e}")
            self.bg_original = None
        # --- FIM DA ADIÇÃO ---

        self.voltar_cadastro_login = signal('voltar_cadastro_login')
        self.sinal_comparador = signal('chamar_agora_comparador')
        self.sinal_para_enviar_ao_banco = signal('chamar_agora_enviar_banco')
        self.ir_plataformaMeioAmbiente = signal('ir_plataformaMeioAmbiente')

    # Substitua sua função 'iniciar_captura' por esta:
    def iniciar_captura(self):
        # Libera a câmera caso ela esteja "presa" de um uso anterior
        if self.video.isOpened():
            self.video.release()

        # (Re)abre a câmera
        self.video = cv2.VideoCapture(0)
        
        if not self.video.isOpened():
            # Se mesmo assim não abrir, mostra um erro
            self.label_mensagem.config(text="Erro: Não foi possível abrir a câmera.")
            return

        self.start_time = 0
        self.atualizar_video()

    # --- ADICIONADO DE VOLTA ---
    def criar_mascara(self, height, width):
        """Cria uma máscara em forma de elipse."""
        self.mask = np.zeros((height, width), dtype=np.uint8)
        # Ajuste os eixos para uma elipse mais agradável
        center, axes = (width // 2, height // 2), (width // 5, height // 3)
        
        cv2.ellipse(self.mask, center, axes, 0, 0, 360, 255, -1)
    # --- FIM DA ADIÇÃO ---

    def atualizar_video(self):
        success, img = self.video.read()
        if not success:
            print("Falha ao capturar imagem.")
            return

        height, width, _ = img.shape

        # --- LÓGICA DA MÁSCARA E FUNDO ---
        # Cria a máscara na primeira execução
        if self.mask is None:
            self.criar_mascara(height, width)

        # Redimensiona o background na primeira execução
        if self.bg_cv2 is None and self.bg_original is not None:
            self.bg_cv2 = cv2.resize(self.bg_original, (width, height))
        
        # Se o background falhou ao carregar, usa um fundo verde simples
        elif self.bg_cv2 is None and self.bg_original is None:
            self.bg_cv2 = np.full((height, width, 3), (50, 133, 140), dtype=np.uint8) # Cor do seu app

        # 1. Roda a detecção na imagem original
        img_detectada, bboxes = self.detector.findFaces(img, draw=True)

        # 2. Cria a imagem do rosto com fundo preto (para salvar)
        mostra_mask_rosto = cv2.bitwise_and(img, img, mask=self.mask)

        # 3. Cria a imagem do rosto detectado com fundo preto
        img_com_elipse = cv2.bitwise_and(img_detectada, img_detectada, mask=self.mask)

        # 4. Cria o fundo com um "buraco" de elipse (preto)
        # Inverte a máscara (elipse vira 0, fundo vira 255)
        mask_invertida = cv2.bitwise_not(self.mask)
        fundo_com_buraco = cv2.bitwise_and(self.bg_cv2, self.bg_cv2, mask=mask_invertida)

        # 5. Combina o rosto (com fundo preto) + fundo (com buraco preto)
        final_img = cv2.add(img_com_elipse, fundo_com_buraco)
        # --- FIM DA LÓGICA DA MÁSCARA ---


        if bboxes:
            confidence = bboxes[0]["score"][0] * 100
            tempo_atual = time.time() - self.start_time

            if confidence < 89:
                self.mensagem = "Fique no centro para ser visualizado."
            elif confidence >= 93:
                if tempo_atual <= 1.5:
                    self.mensagem = "Aproxime-se para ser reconhecido"
                elif 1.7 <= tempo_atual <= 3.7:
                    self.mensagem = "Rosto detectado, aguarde..."
                elif 3.8 <= tempo_atual <= 7.5:
                    self.mensagem = "Mantenha-se posicionado."
                elif self.start_time == 0:
                    self.start_time = time.time()
                elif time.time() - self.start_time >= self.tempo_estipulado:
                    self.mensagem = "Capturando imagem..."
                    cv2.waitKey(1)
                    time.sleep(1)
                    self.img_salvar_banco = mostra_mask_rosto # Salva só o rosto (fundo preto)
                    self._, self.rosto_png = cv2.imencode('.png', self.img_salvar_banco)
                    self.mostrar_resultado(self.img_salvar_banco) # Passa a imagem salva
                    return
            else:
                self.start_time = 0
        else:
            self.mensagem = "Nenhum rosto detectado."

        # Atualiza a mensagem no Tkinter
        self.label_mensagem.config(text=self.mensagem)

        # Atualiza a imagem no Label
        img_rgb = cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB) # Usa a imagem combinada
        img_pil = Image.fromarray(img_rgb)
        
        # Redimensiona a imagem para caber no label (opcional, mas recomendado)
        img_pil.thumbnail((640, 480))
        
        img_tk = ImageTk.PhotoImage(img_pil)
        self.label_imagem.config(image=img_tk)
        self.label_imagem.image = img_tk  # Mantém uma referência da imagem

        # Chama novamente esta função após um breve intervalo
        self.label_imagem.after(100, self.atualizar_video)


    def mostrar_resultado(self, img):
        # 'img' aqui é o self.img_salvar_banco (rosto com fundo preto)
        
        # --- COMBINA A IMAGEM CAPTURADA COM O FUNDO ---
        height, width, _ = img.shape
        final_img_capturada = img # Default caso o fundo falhe
        
        if self.bg_original is not None:
            # Redimensiona o fundo para o tamanho da imagem capturada
            bg_cv2_resized = cv2.resize(self.bg_original, (width, height))
            # Pega a máscara (deve existir) e inverte
            mask_invertida = cv2.bitwise_not(self.mask)
            # Cria o fundo com o buraco
            fundo_com_buraco = cv2.bitwise_and(bg_cv2_resized, bg_cv2_resized, mask=mask_invertida)
            # Soma a imagem capturada (rosto) + fundo (com buraco)
            final_img_capturada = cv2.add(img, fundo_com_buraco)
        # --- FIM DA COMBINAÇÃO ---

        # Atualiza a mensagem e a imagem
        self.label_mensagem.config(text="Imagem capturada!")
        img_rgb = cv2.cvtColor(final_img_capturada, cv2.COLOR_BGR2RGB) # Usa a imagem combinada
        img_pil = Image.fromarray(img_rgb)
        
        # Redimensiona a imagem para caber no label
        img_pil.thumbnail((640, 480)) 
        
        img_tk = ImageTk.PhotoImage(img_pil)
        self.label_imagem.config(image=img_tk)
        self.label_imagem.image = img_tk
        
        self.video.release()  # Libera a câmera
        self.voltar_cadastro_login.send()
    
    def verificar_sinais(self, sender, **kwargs):
        if sender == self.sinal_comparador:

            comparar_cpf = kwargs.get('comparar_cpf')
            # print(comparar_cpf)
            self.comparar_imagens(comparar_cpf)
        elif sender == self.sinal_para_enviar_ao_banco:

            nome_cadastro = kwargs.get('nome_cadastro')
            cpf_cadastro = kwargs.get('cpf_cadastro')
            self.enviar_dados_banco(nome_cadastro, cpf_cadastro)
        else:
            print("Sinal desconhecido.")


    def comparar_imagens(self, cpf_interface):
        self.label_mensagem.config(text="Analisando imagem, aguarde...")
        
        imagem_banco_bytes = pegar_imagem_para_comparar(cpf_interface)
        
        # --- Adicionado tratamento de erro para CPF não encontrado ---
        if imagem_banco_bytes is None:
            self.label_mensagem.config(text="Erro: CPF não encontrado no banco.")
            # Você pode querer um sinal para voltar para a tela anterior
            return
            
        imagem_banco_array = cv2.imdecode(np.frombuffer(imagem_banco_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        # self.img_salvar_banco é o rosto com fundo preto
        imagem = self.img_salvar_banco
        imagem2 = imagem_banco_array # A imagem do banco também deve ser só o rosto


        if imagem is None or imagem2 is None:
            print("Erro ao decodificar uma das imagens.")
            self.label_mensagem.config(text="Erro ao processar imagem.")
            return

        try:
            # Roda a verificação (imagem do banco vs imagem capturada)
            resultado = DeepFace.verify(imagem, imagem2, model_name='Facenet', enforce_detection=False)
            
            if resultado.get("verified"):
                print("As imagens correspondem: são a mesma pessoa.")
                print(resultado["verified"])
                self.ir_plataformaMeioAmbiente.send()
            else:
                print("As imagens não correspondem: não são a mesma pessoa.")
                print(resultado["verified"])
                self.label_mensagem.config(text="Rosto não compatível. Tente novamente.")
        except Exception as e:
            print(f"Ocorreu um erro durante a verificação: {e}")
            self.label_mensagem.config(text="Erro na análise. Tente novamente.")
    
    def informacoes_banco_plataformaMeioAmbiente(self, cpf_interface):
        array_nome_permissao = ir_para_plataformaMeioAmbiente(cpf_interface)
        return array_nome_permissao
    
    def enviar_dados_banco(self, enviar_nomeCadastro, enviar_cpf):

        enviar_rostoCadastro_binario = self.rosto_png.tobytes()
        
        # 1. Esta é a linha que envia os dados para o banco:
        enviarAoBanco(enviar_nomeCadastro, enviar_cpf, enviar_rostoCadastro_binario)
        
        # --- AQUI É ONDE VOCÊ COLOCA A MENSAGEM ---

        # 2. (OPCIONAL) Mensagem no console/terminal:
        print(f"Usuário {enviar_nomeCadastro} cadastrado com sucesso! Clique em Tela Inicial para logar")

        # 3. (JÁ EXISTE) Mensagem na tela da aplicação:
        # Esta linha atualiza o label "mensagem_resultado"
        self.label_mensagem.config(text="Cadastro realizado com sucesso, Clique em Tela Inicial para logar!")
        
        # Aqui você poderia adicionar um delay e depois
        # enviar um sinal para voltar à tela inicial, por exemplo.