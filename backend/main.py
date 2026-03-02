from fastapi import FastAPI
import httpx
from schemas import UserChatRequest
from pydantic import *
from labs_config import LAB_SYSTEM_PROMPTS, LAB_SECRETS

OLLAMA_SERVER_URL = "http://127.0.0.1:11434"

app = FastAPI(title="Proyecto Prompt PWNed - Backend", description="Este es un proyecto educativo cuyo fin es concientizar acerca de diferentes formas básicas de vulnerar un modelo de IA a traves de ingeniería social y prompt injection. Todo lo demostrado aquí es únicamente con fines educativos. Happy hacking!")

@app.get("/")
def root():
    return {"message": "Prompt PWNed API running!"}

@app.get("/api/models")
async def get_models():
    #Aca se implementa la parte que devuelve los modelos de Ollama. Se devuelve el nombre del modelo y el tamaño en GB
    async with httpx.AsyncClient() as client:
        try:
            # Hacemos la peticion y guardamos el resultado (exitoso) en la variable response
            response = await client.get(f"{OLLAMA_SERVER_URL}/api/tags", timeout=10.0)

            # Revisamos el codigo de la response, y si es 2XX seguimos ejecutando, sino, lanzamos una excepcion

            response.raise_for_status()

            # Creamos la lista de modelos que devolveremos
            models = []

            # Para la respuesta de la peticion, vamos a convertirlo a un json, entrar a la clave "models" e iterar sobre ellos
            # Si no tenemos modelos cargados, vamos a devolver una lista vacia
            for model in response.json().get("models", []):

                # Creamos un objeto nuevo que tendra como atributos el nombre y tamaño del modelo
                model_info = {"modelName": model["name"], "modelSize":f"{model['size'] / 1e9:.2f} GB"}

                # Lo agregamos a la lista de modelos
                models.append(model_info)
            
            # Devolvemos la lista de modelos
            return {
                "models":models
            }
        
        # Esta excepcion maneja los errores de codigo de error (4XX, 5XX)
        except httpx.HTTPStatusError as error:
            return {"message":f"Se produjo un error al hacer la peticion a la url {OLLAMA_SERVER_URL}. Código de error: {error.response.status_code}"}
        # Esta excepcion maneja los errores de conexion (cuando no se puede llegar al servidor porque Ollama está apagado, o nos pegamos con el timeout)
        except httpx.RequestError as error:
            return {"message":f"Se produjo un error de conexion al hacer la peticion a la url {error.request.url}"}

@app.post("/api/chat")
async def chat(request: UserChatRequest):
    async with httpx.AsyncClient() as client:
        try:
            # Convierto la petición en un diccionario (porque viene en formato BaseModel por Pydantic)
            request = request.model_dump()

            # Separo el historial de mensajes, para pasarlo con el último mensaje incluido como pide la documentación de Ollama
            currentMessages = request["chatHistory"]

            # Añado el último mensaje
            currentMessages.append(request["userMessage"])

            # Añado primero que todo el system prompt
            # request["laboratoryId"] me va a dar el id del laboratorio que viene del front: "lab1", ... , "lab4"
            # Y luego busco con esta clave en el diccionario LABS_SYSTEM_PROMPTS
            
            system_prompt = LAB_SYSTEM_PROMPTS[request["laboratoryId"]]
            currentMessages.insert(0, {"role":"system", "content":system_prompt})


            # Armo el cuerpo de la petición. "stream" va en False porque sino me devuelve la respuesta token por token
            requestBody = {
                "model": request["aiCurrentModel"],
                "messages":currentMessages,
                "stream": False
            }

            print(f"Este es el request body: \n {requestBody}")

            # Guardo la respuesta en la variable response
            response = await client.post(f"{OLLAMA_SERVER_URL}/api/chat", json=requestBody, timeout=60.0)

            # Verifico que la respuesta es 2XX
            response.raise_for_status()

            # Convierto la respuesta a un diccionario
            data = response.json()

            print(f"Esta es la data de la response: \n {data}")

            # Creo una variable para guardar la respuesta
            chatResponse = {
                "chatResponse":data["message"]["content"],
                "totalTime":data["total_duration"],
                "done":data["done"],
                "doneReason":data["done_reason"],
                "pwned":LAB_SECRETS[request['laboratoryId']] in data['message']['content']
            }

            # Devolvemos la respuesta

            return chatResponse


        # Esta excepcion maneja los errores de codigo de error (4XX, 5XX)
        except httpx.HTTPStatusError as error:
            return {"message":f"Se produjo un error al hacer la peticion a la url {OLLAMA_SERVER_URL}. Código de error: {error.response.status_code}"}
        # Esta excepcion maneja los errores de conexion (cuando no se puede llegar al servidor porque Ollama está apagado, o nos pegamos con el timeout)
        except httpx.RequestError as error:
            print(f"Este es el error: \n {error}")
            return {"message":f"Se produjo un error de conexion al hacer la peticion a la url {error.request.url}"}
