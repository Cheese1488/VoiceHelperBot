import soundcard, pyaudio, speech_recognition, os, json, sys, pyautogui, random, requests

import win32com.client

def ask_ai(history):
    server_url = "https://heartfelt-nourishment-production-9ff3.up.railway.app/chat"
    try:
        resp = requests.post(server_url, json={"messages": history}, timeout=30)
        if resp.status_code == 200:
            return resp.json()["reply"]
        else:
            return f"Ошибка сервера: {resp.json().get('error', 'Неизвестная ошибка')}"
    except Exception as e:
        return f"Ошибка связи с сервером: {e}"

def get_answer(words, engine):
    prot = True
    commandIndex = 0

    if "привет" in words:
        print("BOT: Привет!")
        engine.speak("Привет!")
        commandIndex = 1

    elif "как меня зовут" in words:
        print(f"BOT: Вас зовут: {os.getlogin()}")
        engine.speak(f"Вас зовут: {os.getlogin()}")

    elif "открой" in words:
        commandIndex = 2

    elif "закрой окно" in words or "закрой приложение" in words or "закрой программу" in words or "закрой прогу" in words:
        commandIndex = 4

    elif "Сменить микрофон" in words or "смени микрофон" in words:
        commandIndex = 3
    elif "удали историю" in words:
        ai_history_path = os.path.join(get_script_dir(), 'AiHistory.json')
        if os.path.exists(ai_history_path):
            os.remove(ai_history_path)
            print("BOT: История удалена.")
            engine.speak("История удалена.")
        else:
            print("BOT: Истории нет.")
            engine.speak("Истории нет.")

    elif "пока" in words:
        print("BOT: Пока!")
        engine.speak("Пока!")
        prot = False

    else:
        waitAnswer = random.randint(0, 5)
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
        engine.speak(chosen)
        commandIndex = 5


    return prot, commandIndex

def Get_Words(engine, microphoneIndex):
    with speech_recognition.Microphone(microphoneIndex) as sourse:
        audio = rec.listen(sourse, phrase_time_limit=5)
    words = rec.recognize_google(audio, language="ru-RU")
    print(f"YOU {words}")
    return words

def get_script_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
    
    

if __name__ == '__main__':
    config_path = os.path.join(get_script_dir(), 'config.json')
    if not os.path.exists(config_path):
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({"apps": {}}, f, indent=4)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    rec = speech_recognition.Recognizer()
    engine = win32com.client.Dispatch("SAPI.SpVoice")
    microphones = soundcard.all_microphones()
    history = [
    {"role": "system", "content": "Ты — участник диалога. Отвечай кратко и естественно."}
    ]

    print("Бот запущен!")

    with open(os.path.join(get_script_dir(), 'Settings.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
        mic_index = data["Settings"]["MicrophoneIndex"] or 0
    while True:
        try:
            words = Get_Words(engine, mic_index).lower()
            if len(words) < 3 or not words.startswith("бот"):
                print("Игнорирую")
            else:
                answer, commandIndex = get_answer(words, engine)
                if commandIndex == 2:

                    words_list = words.lower().split()
                    if "открой" in words_list:
                        idx = words_list.index("открой") 
                        appSite = " ".join(words_list[idx+1:]) 
                    else:
                        appSite = ""

                    try:
                        if appSite in config["apps"]:
                            app = config["apps"][appSite]
                            print(f"BOT: Открываю: {appSite}")
                            engine.speak(f"Открываю: {appSite}")
                            print(f"{app}")
                            os.startfile(app)
                        else:
                            print(f"BOT: Открываю: {appSite}")
                            engine.speak(f"Открываю: {appSite}")
                            try:
                                os.startfile(str.lower(appSite) + "://")
                            except Exception as e:
                                print(f"BOT: Неизвестное приложение или сайт: {appSite}")
                                engine.speak(f"BOT: Неизвестное приложение или сайт: {appSite}")

                    except Exception as e:
                        print(f"Ошибка: {e}")
                        engine.speak(f"Ошибка: {e}")
                elif commandIndex == 3:
                    print("BOT: Смена микрофона")
                    engine.speak("Смена микрофона")
                    for i, mic in enumerate(microphones):
                        print(f"{i}: {mic.name}")
                    try:
                        mic_index = int(input("Введите индекс микрофона: "))
                        with open(os.path.join(get_script_dir(), 'Settings.json'), 'r+', encoding='utf-8') as f:
                            data = json.load(f)
                            data["Settings"]["MicrophoneIndex"] = mic_index
                            f.seek(0)
                            json.dump(data, f, indent=4)
                            f.truncate()
                        print(f"Микрофон успешно изменён на: {microphones[mic_index].name}")
                        engine.speak(f"Микрофон успешно изменён на: {microphones[mic_index].name}")
                    except Exception as e:
                        print(f"Ошибка: {e}")
                        engine.speak(f"Ошибка: {e}")
                elif commandIndex == 4:
                    pyautogui.hotkey('alt', 'f4')
                    print(f"BOT: Закрываю открытое окно")
                    engine.speak(f"Закрываю открытое окно")
                elif commandIndex == 5:
                    ai_history_path = os.path.join(get_script_dir(), 'AiHistory.json')
                    try:
                        if not os.path.exists(ai_history_path) or os.path.getsize(ai_history_path) == 0:
                            history = [{"role": "system", "content": "Ты — участник диалога. Отвечай кратко и естественно."}]
                            with open(ai_history_path, 'w', encoding='utf-8') as f:
                                json.dump(history, f, ensure_ascii=False, indent=2)
                        else:
                            with open(ai_history_path, 'r', encoding='utf-8') as f:
                                try:
                                    history = json.load(f)
                                except json.JSONDecodeError:
                                    print("История повреждена, создаю новую...")
                                    engine.speak("История повреждена, создаю новую...")
                                    history = [{"role": "system", "content": "Ты — участник диалога. Отвечай кратко и естественно."}]
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
                        engine.speak(assistant_reply)

                    except Exception as e:
                        print(f"Ошибка API: {e}")
                        engine.speak("Произошла ошибка при обращении к нейросети")


                if answer == False:
                    break
        except Exception as e:
            if not isinstance(e, speech_recognition.UnknownValueError):
                print(f"Ошибка: {e}")
                engine.speak(f"Ошибка: {e}")