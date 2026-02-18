"""
voice_service.py - Patrón Facade
Responsabilidad: Ocultar la complejidad de la captura de audio y transcripción.
Proporciona una interfaz simple para capturar y transcribir voz.

Usa sounddevice en lugar de PyAudio (PyAudio no tiene wheel para Python 3.14).
"""
import time
import queue
import threading
import numpy as np
import sounddevice as sd
import speech_recognition as sr


# Configuración de captura
SAMPLE_RATE = 16000       # Hz óptimo para Google Web Speech
CHANNELS = 1              # Mono
DURACION_SILENCIO = 0.8   # segundos de silencio para parar la grabación
DURACION_MAX = 10         # segundos máximos de grabación
UMBRAL_ENERGIA = 500      # energía mínima para considerar que hay voz


class VoiceService:
    """
    Facade sobre sounddevice + SpeechRecognition.
    El programador solo necesita llamar a `capturar_frase()`.
    Detecta automáticamente el inicio y fin del habla.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()

    def capturar_frase(self) -> dict:
        """
        Captura audio del micrófono con sounddevice y lo transcribe
        con Google Web Speech API.

        Returns:
            dict con claves:
                - 'texto': str con la frase reconocida (o None si falla)
                - 'confianza': float entre 0 y 1 (o None)
                - 'alternativas': list de textos alternativos
                - 'latencia': str con el tiempo de respuesta en segundos
                - 'error': str con el motivo del error (o None)
                - 'hardware_db': float con el nivel de energía capturado (o None)
        """
        resultado = {
            "texto": None,
            "confianza": None,
            "alternativas": [],
            "latencia": None,
            "error": None,
            "hardware_db": None,
        }

        try:
            # ── Calibrar ruido de fondo ──────────────────────────────────────
            print("[VOZ] Calibrando ruido de fondo...")
            ruido = sd.rec(
                int(0.8 * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
            )
            sd.wait()
            nivel_ruido = float(np.abs(ruido).mean())
            umbral = max(UMBRAL_ENERGIA, nivel_ruido * 2.5)
            resultado["hardware_db"] = round(nivel_ruido, 2)
            print(f"[VOZ] Umbral de voz: {umbral:.0f}  |  Habla ahora...")

            # ── Grabación con detección de silencio ──────────────────────────
            bloques = []
            cola = queue.Queue()
            stop_event = threading.Event()

            def callback(indata, frames, time_info, status):
                cola.put(indata.copy())

            stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=int(SAMPLE_RATE * 0.1),  # bloques de 100ms
                callback=callback,
            )

            silencio_acumulado = 0.0
            hablando = False
            tiempo_total = 0.0

            with stream:
                while tiempo_total < DURACION_MAX:
                    try:
                        bloque = cola.get(timeout=0.2)
                    except queue.Empty:
                        continue

                    energia = float(np.abs(bloque).mean())
                    bloques.append(bloque)
                    tiempo_total += 0.1

                    if energia > umbral:
                        hablando = True
                        silencio_acumulado = 0.0
                    elif hablando:
                        silencio_acumulado += 0.1
                        if silencio_acumulado >= DURACION_SILENCIO:
                            print("[VOZ] Silencio detectado, procesando...")
                            break

            if not hablando:
                resultado["error"] = "timeout"
                return resultado

            # ── Convertir audio a AudioData de speech_recognition ────────────
            audio_np = np.concatenate(bloques, axis=0)
            audio_bytes = audio_np.tobytes()
            audio_sr = sr.AudioData(audio_bytes, SAMPLE_RATE, 2)  # 2 bytes = int16

            print("[VOZ] Procesando audio con Google Web Speech...")
            inicio = time.time()

            # show_all=True devuelve el JSON completo con confianza y alternativas
            respuesta = self.recognizer.recognize_google(
                audio_sr, language="es-ES", show_all=True
            )

            resultado["latencia"] = f"{round(time.time() - inicio, 2)}s"

            if respuesta and "alternative" in respuesta:
                alternativas = respuesta["alternative"]
                mejor = alternativas[0]
                resultado["texto"] = mejor.get("transcript", "")
                resultado["confianza"] = round(mejor.get("confidence", 0.0), 4)
                resultado["alternativas"] = [
                    a.get("transcript", "") for a in alternativas[1:]
                ]
            else:
                resultado["error"] = "no_speech_detected"

        except sd.PortAudioError as e:
            resultado["error"] = f"mic_not_found: {e}"
        except sr.UnknownValueError:
            resultado["error"] = "unintelligible_audio"
        except sr.RequestError as e:
            resultado["error"] = f"api_error: {e}"
        except Exception as e:
            resultado["error"] = f"error: {e}"

        return resultado
