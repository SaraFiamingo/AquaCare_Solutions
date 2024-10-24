import paho.mqtt.client as mqtt
import random
import time
import json

# Configurazione MQTT
BROKER = "localhost"  
PORT = 1884
TOPIC_DATA = "sensori/dati"
TOPIC_COMMAND = "sensori/comandi/Tank_2"
TOPIC_ALERT = "sensori/avvisi"
CLIENT_ID = "Sensore_Campo"

#stato iniziale dei sensori 
soil_moisture = 70 #umidità del terreno iniziale fissata al 70%
irrigation_active = False  #stato dell'irrigazione inizialmente disattivata
total_water_used = 0  # acqua totale utilizzata

# Costanti
FLOW_THRESHOLD = 50  # soglia di flusso d'acqua
FLOW_MONITOR_DURATION = 10  # durata in secondi per monitorare il flusso elevato

# Variabili per monitorare il flusso d'acqua
high_flow_time = 0  # tempo in cui il flusso è sopra la soglia

# Funzione per simulare i dati dai sensori
def get_sensor_data():

    global soil_moisture, irrigation_active, total_water_used, high_flow_time

    #aggiorna l'umidità del terreno in base allo stato dell'irrigazione
    if soil_moisture < 70: 
        irrigation_active = True
        soil_moisture = soil_moisture + 5  #aumenta l'umidità di 5 se l'irrigazione è attiva
        print(f"[{CLIENT_ID}] Irrigazione attivata. Umidità terreno: {soil_moisture}%")
    else:
        soil_moisture -= 5
        irrigation_active = False  #diminusce l'umidità di 5 se l'irrigazione è disattivata
        print(f"[{CLIENT_ID}] Irrigazione disattivata. Umidità terreno: {soil_moisture}%")
    
    # Simula il flusso d'acqua
    water_flow = round(random.uniform(0.0, 150.0), 2)  # Simula il flusso d'acqua in litri al minuto
    total_water_used += water_flow * 5 / 60  # Aggiungi il consumo basato su 5 secondi
    
    # Controlla il flusso elevato
    if water_flow > FLOW_THRESHOLD:
        high_flow_time += 1  # Incrementa il contatore di tempo
        if high_flow_time >= FLOW_MONITOR_DURATION:
            alert_message = {
                "sensor_id": CLIENT_ID,
                "message": "ATTENZIONE: Flusso d'acqua elevato! Possibile guasto o malfunzionamento."
            }
            client.publish(TOPIC_ALERT, json.dumps(alert_message))
            print(f"[{CLIENT_ID}] Avviso inviato: {alert_message['message']}")
    else:
        high_flow_time = 0  # Resetta il contatore se il flusso è normale

    # Simula la presenza di perdite
    water_leak = random.choice([True, False])  # simula la presenza di perdite
    if water_leak:
        alert_message = {
            "sensor_id": CLIENT_ID,
            "message": "ATTENZIONE: Perdita d'acqua rilevata! Intervento immediato richiesto."
        }
        client.publish(TOPIC_ALERT, json.dumps(alert_message))
        print(f"[{CLIENT_ID}] Avviso inviato: {alert_message['message']}")
    
    #ritorna i dati del sensore
    return {
        "sensor_id": CLIENT_ID,
        "water_flow": round(random.uniform(0.0, 150.0), 2),  # Simula il flusso d'acqua in litri al minuto
        "soil_moisture": soil_moisture,  #usa il valore attuale di umidità del terreno
        "water_leak": water_leak  #simula la rilevazione di perdite d'acqua
    }

#Callback per gestire i messaggi di comando dal server
def on_message(client, userdata, msg):
    global irrigation_active
    command = msg.payload.decode()
    print(f"[{CLIENT_ID}] Comando ricevuto dal server: {command}")

    if command == "ATTIVA IRRIGAZIONE":
        irrigation_active = True
        print(f"[{CLIENT_ID}] irrigazione attivata")
    elif command == "DISATTIVA IRRIGAZIONE":
        irrigation_active = False
        print(f"[{CLIENT_ID}] irrigazione disattivata.")
    elif command == "CONTROLLA FLUSSO":
        print(f"[{CLIENT_ID}] Controllo del flusso d'acqua in corso...")
    elif command == "CONTROLLA PERDITA":
        print(f"[{CLIENT_ID}] verifica delle perdite d'acqua in corso...")

# Connessione al broker MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, CLIENT_ID)
client.on_message = on_message
client.connect(BROKER, PORT, 60)
#Sottoscrizione per ricevere comandi dal server
client.subscribe(TOPIC_COMMAND)

# Loop principale per inviare dati periodici e ascoltare i comandi
try:
    client.loop_start() #Avvia il loop per gestire i messaggi in background

    while True:
        # Simula la raccolta dei dati dai sensori
        sensor_data = get_sensor_data()

        # Converte i dati in formato JSON
        sensor_data_json = json.dumps(sensor_data)

        # Pubblica i dati al server MQTT
        client.publish(TOPIC_DATA, sensor_data_json)
        print(f"[{CLIENT_ID}] Dati inviati: {sensor_data_json}")

        # Attende 5 secondi prima di inviare i nuovi dati
        time.sleep(5)

except KeyboardInterrupt:
    print(f"[{CLIENT_ID}] Chiusura del client MQTT.")
    client.loop_stop()
    client.disconnect()