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
        self.mask = None  # Variável para a máscara
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

    def criar_mascara(self, height, width):
        """Cria uma máscara em forma de elipse."""
        self.mask = np.zeros((height, width), dtype=np.uint8)
        center, axes = (width // 2, height // 2), (width // 5, height // 3)
        
        cv2.ellipse(self.mask, center, axes, 0, 0, 360, 255, -1)
        

    def atualizar_video(self):
        success, img = self.video.read()
        if not success:
            print("Falha ao capturar imagem.")
            return

        height, width, _ = img.shape
        if self.mask is None:
            self.criar_mascara(height, width)

        # Aplica a máscara
        img_masked = cv2.bitwise_and(img, img, mask=self.mask)
        mostra_mask_rosto = cv2.bitwise_and(img, img, mask=self.mask)

        img_masked, bboxes = self.detector.findFaces(img_masked, draw=True)

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
                    self.img_salvar_banco = mostra_mask_rosto
                    self._, self.rosto_png = cv2.imencode('.png', self.img_salvar_banco)
                    self.mostrar_resultado(mostra_mask_rosto)
                    return
            else:
                self.start_time = 0
        else:
            self.mensagem = "Nenhum rosto detectado."

        # Atualiza a mensagem no Tkinter
        self.label_mensagem.config(text=self.mensagem)

        # Atualiza a imagem no Label
        img_rgb = cv2.cvtColor(img_masked, cv2.COLOR_BGR2RGB)  # Usar a imagem mascarada
        img_pil = Image.fromarray(img_rgb)
        img_tk = ImageTk.PhotoImage(img_pil)
        self.label_imagem.config(image=img_tk)
        self.label_imagem.image = img_tk  # Mantém uma referência da imagem

        # Chama novamente esta função após um breve intervalo
        self.label_imagem.after(100, self.atualizar_video)



    def mostrar_resultado(self, img):
        # Atualiza a mensagem e a imagem
        self.label_mensagem.config(text="Imagem capturada!")
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
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
        imagem_banco_array = cv2.imdecode(np.frombuffer(imagem_banco_bytes, np.uint8), cv2.IMREAD_COLOR)
        

        imagem = self.img_salvar_banco
        imagem2 = imagem_banco_array


        if imagem is None or imagem2 is None:
            print("Erro ao decodificar uma das imagens.")
            return

        try:
            resultado = DeepFace.verify(imagem, imagem2, model_name='Facenet', enforce_detection=False)
            if resultado.get("verified"):
                print("As imagens correspondem: são a mesma pessoa.")
                print(resultado["verified"])
                self.ir_plataformaMeioAmbiente.send()
            else:
                print("As imagens não correspondem: não são a mesma pessoa.")
                print(resultado["verified"])
        except Exception as e:
            print(f"Ocorreu um erro durante a verificação: {e}")
    
    def informacoes_banco_plataformaMeioAmbiente(self, cpf_interface):
        array_nome_permissao = ir_para_plataformaMeioAmbiente(cpf_interface)
        return array_nome_permissao
    
    def enviar_dados_banco(self, enviar_nomeCadastro, enviar_cpf):

        enviar_rostoCadastro_binario = self.rosto_png.tobytes()
        enviarAoBanco(enviar_nomeCadastro, enviar_cpf, enviar_rostoCadastro_binario)
