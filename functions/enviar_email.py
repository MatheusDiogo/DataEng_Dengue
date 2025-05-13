import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

def enviar_email(corpo, email_destinatario, emails_cc=None):
    DATA_ONTEM = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")

    # Configuração do e-mail
    email_remetente = "mdas@poli.br"
    senha = "ngoauffnyynhidaj" # Essa senha deveria ser colocada em uma variável de ambiente para não expor no github

    # Criar a mensagem
    msg = MIMEMultipart()
    msg["From"] = email_remetente
    msg["To"] = email_destinatario
    msg["Subject"] = f"Atualização Dados Dengue - DataSUS ({DATA_ONTEM})"
        # Verifica se emails_cc é None ou não
    if emails_cc:
        msg["Cc"] = ", ".join(emails_cc)
    else:
        msg["Cc"] = ""

    # Corpo do e-mail
    msg.attach(MIMEText(corpo, "plain"))

    # Conectar ao servidor SMTP do Gmail e enviar o e-mail
    try:
        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()  # Segurança na conexão
        servidor.login(email_remetente, senha)
        servidor.sendmail(email_remetente, [email_destinatario] + (emails_cc if emails_cc else []), msg.as_string())
        servidor.quit()
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")