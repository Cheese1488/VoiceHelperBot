import soundcard, speech_recognition, os, json, sys, pyautogui, random, requests, platform, threading
import win32com.client

def ask_ai(history):
    server_url = "https://heartfelt-nourishment-production-9ff3.up.railway.app/chat"
    try:
        resp = requests.post(server_url, json={"messages": history}, timeout=120)
        if resp.status_code == 200:
            return resp.json()["reply"]
        else:
            return f"Ошибка сервера: {resp.json().get('error', 'Неизвестная ошибка')}"
    except requests.exceptions.Timeout:
        return "Сервер ИИ просыпается, повторите запрос через 10 секунд."
    except Exception as e:
        return f"Ошибка связи с сервером: {e}"

def get_answer(words, engine):
    prot = True
    commandIndex = 0

    if "отмена" in words or "отмени" in words:
        commandIndex = 5

    elif "как меня зовут" in words:
        print(f"BOT: Вас зовут: {os.getlogin()}")
        speak_interruptible(f"Вас зовут: {os.getlogin()}", mic_index, engine)
        commandIndex = 1

    elif "открой" in words:
        commandIndex = 2

    elif "привет" in words:
        print("BOT: Привет!")
        speak_interruptible("Привет!", mic_index, engine)
        commandIndex = 1

    elif "закрой окно" in words or "закрой приложение" in words or "закрой программу" in words or "закрой прогу" in words or "закрой ок" in words:
        pyautogui.hotkey('alt', 'f4')
        print("BOT: Закрываю открытое окно")
        speak_interruptible("Закрываю открытое окно", mic_index, engine)

    elif "сменить микрофон" in words or "смени микрофон" in words:
        commandIndex = 3
    elif "сменить имя" in words or "смени имя" in words or "изменить имя" in words or "измени имя" in words:
        commandIndex = 6

    elif "удали историю" in words:
        ai_history_path = os.path.join(get_script_dir(), 'AiHistory.json')
        if os.path.exists(ai_history_path):
            os.remove(ai_history_path)
            print("BOT: История удалена.")
            speak_interruptible("История удалена.", mic_index, engine)
        else:
            print("BOT: Истории нет.")
            speak_interruptible("Истории нет.", mic_index, engine)

    elif "пока" in words:
        print("BOT: Пока!")
        speak_interruptible("Пока!", mic_index, engine)
        prot = False

    elif "спящий режим" in words or "включи спящий режим" in words:
        print("BOT: Включаю спящий режим. До встречи!")
        speak_interruptible("Включаю спящий режим. До встречи!", mic_index, engine)
        match platform.system():
            case "Linux":
                os.system("systemctl suspend")
            case "Darwin":
                os.system("pmset sleepnow")
            case "Windows":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            case "Java":
                raise NotImplementedError("Sleep command not implemented for Java")
            case "":
                raise ValueError("Can't determine operation system")

    else:
        phrases = [
                "Подожди... я подумаю...",
                "Хмм... дай-ка подумать...",
                "Сейчас... я подумаю...",
                "Дай-ка подумать...",
                "Так... я подумаю...",
                "Секундочку... я подумаю..."
            ]
        chosen = random.choice(phrases)
        print(chosen)
        speak_interruptible(chosen, mic_index, engine)
        commandIndex = 4

    return prot, commandIndex

def Get_Words(microphoneIndex):
    try:
        with speech_recognition.Microphone(microphoneIndex) as source:
            rec = speech_recognition.Recognizer()
            rec.adjust_for_ambient_noise(source, duration=1)
            audio = rec.listen(source, timeout=5, phrase_time_limit=5)
        words = rec.recognize_google(audio, language="ru-RU")
        print(f"YOU {words}")
        return words
    except speech_recognition.WaitTimeoutError:
        return ""
    except speech_recognition.UnknownValueError:
        return ""
    except Exception as e:
        print(f"Ошибка микрофона: {e}")
        return ""

def listen_for_stop(stop_event, stopped_event, mic_index, engine):
    try:
        rec = speech_recognition.Recognizer()
        with speech_recognition.Microphone(mic_index) as source:
            rec.adjust_for_ambient_noise(source, duration=0.5)
            while not stop_event.is_set():
                try:
                    audio = rec.listen(source, timeout=0.5, phrase_time_limit=0.8)
                    text = rec.recognize_google(audio, language="ru-RU").lower()
                    if "стоп" in text or "тихо" in text:
                        print("BOT: Понял!")
                        stopped_event.set()    
                        break
                except speech_recognition.WaitTimeoutError:
                    continue
                except speech_recognition.UnknownValueError:
                    continue
                except speech_recognition.RequestError:
                    continue
    except Exception as e:
        print(f"Ошибка слушателя стоп-слова: {e}") 

def speak_interruptible(text, mic_index, engine):
    stopped_event = threading.Event()
    stop_event = threading.Event()

    t = threading.Thread(target=listen_for_stop, args=(stop_event, stopped_event, mic_index, engine))
    t.daemon = True
    t.start()

    engine.speak(text, 1)  

    while not engine.WaitUntilDone(10): 
        if stopped_event.is_set():
            engine.Skip(1)          
            break

    stop_event.set()
    t.join(timeout=1)

    if stopped_event.is_set():
        engine.speak("Понял!", 1)

def get_script_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
    import time 

    config_path = os.path.join(get_script_dir(), 'config.json')
    if not os.path.exists(config_path):
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({"apps": {}}, f, indent=4)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    engine = win32com.client.Dispatch("SAPI.SpVoice")
    microphones = soundcard.all_microphones()

    with open(os.path.join(get_script_dir(), 'Settings.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
        mic_index = data["Settings"]["MicrophoneIndex"] or 0

    print("Бот запущен!")

    while True:
        try:
            words = Get_Words(mic_index).lower()
            if not words:
                continue

            with open(os.path.join(get_script_dir(), 'Settings.json'), 'r', encoding='utf-8') as f:
                settings = json.load(f)

            bot_names = settings.get("Settings", {}).get("BotName", [])
            if not bot_names or words.split()[0] not in bot_names:
                continue
            answer, commandIndex = get_answer(words, engine)

            if commandIndex == 5:
                print("BOT: Отмена команды")
                speak_interruptible("Отмена команды", mic_index, engine)

            elif commandIndex == 2:
                words_list = words.lower().split()
                idx = words_list.index("открой") if "открой" in words_list else -1
                appSite = " ".join(words_list[idx+1:]) if idx != -1 else ""

                try:
                    if appSite in config.get("apps", {}):
                        app = config["apps"][appSite]
                        print(f"BOT: Открываю: {appSite}")
                        speak_interruptible(f"Открываю: {appSite}", mic_index, engine)
                        os.startfile(app)
                    else:
                        print(f"BOT: Открываю: {appSite}")
                        speak_interruptible(f"Открываю: {appSite}", mic_index, engine)
                        try:
                            os.startfile(str.lower(appSite) + "://")
                        except Exception:
                            print(f"BOT: Неизвестное приложение или сайт: {appSite}")
                            speak_interruptible(f"Неизвестное приложение или сайт: {appSite}", mic_index, engine)
                except Exception as e:
                    print(f"Ошибка: {e}")
                    speak_interruptible(f"Ошибка: {e}", mic_index, engine)

            elif commandIndex == 3:
                print("BOT: Смена микрофона")
                speak_interruptible("Смена микрофона", mic_index, engine)
                for i, mic in enumerate(microphones):
                    print(f"{i}: {mic.name}")
                try:
                    new_index = int(input("Введите индекс микрофона: "))
                    with open(os.path.join(get_script_dir(), 'Settings.json'), 'r+', encoding='utf-8') as f:
                        data = json.load(f)
                        data["Settings"]["MicrophoneIndex"] = new_index
                        f.seek(0)
                        json.dump(data, f, indent=4)
                        f.truncate()
                    mic_index = new_index
                    print(f"Микрофон успешно изменён на: {microphones[mic_index].name}")
                    speak_interruptible(f"Микрофон успешно изменён на: {microphones[mic_index].name}", mic_index, engine)
                except Exception as e:
                    print(f"Ошибка: {e}")
                    speak_interruptible(f"Ошибка: {e}", mic_index, engine)

            elif commandIndex == 6:
                print("BOT: Смена имени бота")
                speak_interruptible("Смена имени бота", mic_index, engine)
                try:
                    new_name = input("Введите новое имя бота: ")
                    with open(os.path.join(get_script_dir(), 'Settings.json'), 'r+', encoding='utf-8') as f:
                        data = json.load(f)
                        data["Settings"]["BotName"] = new_name.split()
                        print(data["Settings"]["BotName"])
                        f.seek(0)
                        json.dump(data, f, indent=4)
                        f.truncate()
                    print(f"Имя бота успешно изменено на: {data['Settings']['BotName']}")
                    speak_interruptible(f"Имя бота успешно изменено на: {data['Settings']['BotName']}", mic_index, engine)
                except Exception as e:
                    print(f"Ошибка: {e}")
                    speak_interruptible(f"Ошибка: {e}", mic_index, engine)

            elif commandIndex == 4:
                ai_history_path = os.path.join(get_script_dir(), 'AiHistory.json')
                try:
                    if not os.path.exists(ai_history_path) or os.path.getsize(ai_history_path) == 0:
                        history = [{"role": "system", "content": "Ты — участник диалога. Отвечай кратко и естественно не используй форматирование текста (жирный, курсив, подчеркивание итд)."}]
                        with open(ai_history_path, 'w', encoding='utf-8') as f:
                            json.dump(history, f, ensure_ascii=False, indent=2)
                    else:
                        with open(ai_history_path, 'r', encoding='utf-8') as f:
                            try:
                                history = json.load(f)
                            except json.JSONDecodeError:
                                print("История повреждена, создаю новую...")
                                speak_interruptible("История повреждена, создаю новую...", mic_index, engine)
                                history = [{"role": "system", "content": "Ты — участник диалога. Отвечай кратко и естественно не используй форматирование текста (жирный, курсив, подчеркивание итд)."}]
                                with open(ai_history_path, 'w', encoding='utf-8') as fw:
                                    json.dump(history, fw, ensure_ascii=False, indent=2)

                    history.append({"role": "user", "content": words})
                    assistant_reply = ask_ai(history)
                    history.append({"role": "assistant", "content": assistant_reply})

                    if len(history) > 50:
                        history = [history[0]] + history[-49:]

                    with open(ai_history_path, 'w', encoding='utf-8') as f:
                        json.dump(history, f, ensure_ascii=False, indent=2)

                    print(f"BOT: {assistant_reply}")
                    speak_interruptible(assistant_reply, mic_index, engine)

                except Exception as e:
                    print(f"Ошибка API: {e}")
                    speak_interruptible("Произошла ошибка при обращении к нейросети", mic_index, engine)

            if answer == False:
                break

        except Exception as e:
            if not isinstance(e, speech_recognition.UnknownValueError):
                print(f"Ошибка: {e}")
                speak_interruptible(f"Ошибка: {e}", mic_index, engine)