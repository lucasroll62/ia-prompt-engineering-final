import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from stablehorde_api import StableHordeAPI
import asyncio
from PIL import Image
import requests
import aiohttp
from time import sleep
import base64

def empty(component):
    if (not component):
        return
    component.empty()
    sleep(0.01)

async def generate_sugested_dish_image(sugested_dish=None):
    try:
        if sugested_dish:
            session = aiohttp.ClientSession()
            client = StableHordeAPI(
                os.environ['STABLE_HORDE_API_KEY'],
                session=session
            )
            response = await client.generate_from_txt(
                sugested_dish
            )
            await session.close()
            image_url = response['img_status'].generations[0].img

            response = requests.get(image_url)

            # Abrir la imagen y convertirla a PNG
            # img_webp = Image.open(io.BytesIO(response.content))
            # img_byte_arr = io.BytesIO()
            # img_webp.save(img_byte_arr, format='PNG')
            # img_byte_arr = img_byte_arr.getvalue()
            # st.session_state['suggested_dish'] = False

            # Print image ready to be displayed
            print("Image ready to be displayed")

            st.session_state['image'] = image_url
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        st.session_state['generating_image'] = False


def retrieve_image():
    asyncio.run(generate_sugested_dish_image(st.session_state['suggested_dish']))

# Load environment variables
load_dotenv()

# Configure genai
api_key = os.environ['GENAI_API_KEY']
genai.configure(api_key=api_key)

# Create a generative model instance
model = genai.GenerativeModel('gemini-pro')

def find_suggested_dish(text):
    parts = text.split("Plato Sugerido:")
    if len(parts) > 1:
        return parts[1]
    else:
        return None
    
# Inicializa el estado de la sesión si no existe
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ''
if 'error' not in st.session_state:
    st.session_state['error'] = False
if 'result' not in st.session_state:
    st.session_state['result'] = False
if 'image' not in st.session_state:
    st.session_state['image'] = False
if 'suggested_dish' not in st.session_state:
    st.session_state['suggested_dish'] = False
if 'generating_image' not in st.session_state:
    st.session_state['generating_image'] = False
if 'result_placeholder' not in st.session_state:
    st.session_state['result_placeholder'] = False
if 'image_placeholder' not in st.session_state:
    st.session_state['image_placeholder'] = False

with st.container(border=True):
    st.title('Donde vamos?')
    st.subheader('Ayuda a tus amigos a encontrar el lugar perfecto para comer')
    st.write('Escribe un mensaje para que el asistente te ayude a encontrar el lugar perfecto para comer')
    st.write('Ejemplo: "Quiero ir a comer sushi en Palermo, tengo un presupuesto de $40000"')
    with st.expander("Ver demostración"):
        file_ = open("./demo.gif", "rb")
        contents = file_.read()
        data_url = base64.b64encode(contents).decode("utf-8")
        file_.close()
        st.markdown(
            f'<img src="data:image/gif;base64,{data_url}" alt="cat gif">',
            unsafe_allow_html=True,
        )
    user_input = st.text_input("Cuéntame que plan tienes para hoy?", 
                              value=st.session_state['user_input'], 
                              key='user_input', 
                              on_change=lambda: generate_content(st.session_state['user_input']))
    
with st.container(border=True):
    if st.session_state['result']:
        st.write('Resultado:')
        st.write(st.session_state['result'])

    if st.session_state['suggested_dish'] and not st.session_state['image']:
        st.write('Imagen del plato...')
        retrieve_image()
    
    if st.session_state['image']:
        st.image(st.session_state['image'], use_column_width=True)
        
def clear_text():
    st.session_state['user_input'] = ''
    st.session_state['result'] = False
    st.session_state['error'] = False
    st.session_state['suggested_dish'] = False
    st.session_state['image'] = False

def generate_content(user_input):
    try:
        clear_text()
        prompt = "Sos un experto conocedor de lugares para comer, debes identificar en que lugar quiere ir la persona " \
        "y que tipo de comida le gustaría comer. Las opciones que debes buscar deben ser cercanas a la ubicación pedida. " \
        "Además, debes tener en cuenta que la persona puede tener restricciones alimenticias. " \
        "Por último, debes tener en cuenta que la persona puede tener un presupuesto limitado. " \
        "La respuesta primero por un resumen para el usuario estilo parrafo " \
        " Luego debe venir ordenada por mejores opciónes. Deberas definir un criterio entre calidad y precio. Los lugares deben ser reales" \
        " por favor incluir, ubicacion completa incluyendo provincia y pais, nombre, tipo, precio, calificacion, restricciones alimenticias, " \
        " mejor plato, telefono, horario, pagina web, etc.' " \
        " Incluir una texto al final que diga un solo plato, de un solo lugar, solamente el nombre del plato (solo nombre de comida): 'Plato Sugerido: XXXX' donde XXXX es el nombre de la comida sugerido." \
        "El usuario te ha dicho: " \
        + user_input

        response = model.generate_content(prompt)

       
        sugested_dish = find_suggested_dish(response.text)
        st.session_state['suggested_dish'] = sugested_dish
        st.session_state['generating_image'] = True
        st.session_state['result'] = response.text
    except Exception as e:
        print(f"An error occurred: {e}")
        st.session_state['error'] = True
    