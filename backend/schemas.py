from pydantic import BaseModel
from typing import List

# Esta clase representa un solo mensaje dentro de una conversacion
class UserMessageModel(BaseModel):
    
    # El rol del usuario que mando el mensaje, para que Ollama pueda entender quien mandó el mensaje
    # Puede ser "user" o "assistant". "system" se reserva para el system prompt del lab
    role: str;

    # El mensaje como tal
    content: str;

# Esta clase representa todo lo que manda el frontend cuando el usuario envía un prompt
class UserChatRequest(BaseModel):
    
    # El id del laboratorio, en base a esto vamos a saber si el modelo tiene que ser más o menos dificil de inyectar
    laboratoryId: str

    # El mensaje que envía el usuario
    userMessage: UserMessageModel

    # El historial de mensajes que envió el usuario, puede ser una lista vacía
    chatHistory: List[UserMessageModel]

    # El modelo de Ollama que estamos usando
    aiCurrentModel: str