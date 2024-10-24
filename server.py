import paho.mqtt.client as mqtt
import json
import time

# Configurazione MQTT
BROKER = "localhost"
PORT = 1884
TOPIC_DATA = "sensori/dati"
TOPIC_ALERT = "sensori/avvisi"  #topic per avvisi
CLIENT_ID = "Server_Centrale"

#Dizionario per memorizzare i dati e lo stato dei sensori
sensor_status = {}
total_water_saved = 0   #acqua risparmiata

# Costanti
FLOW_THRESHOLD = 50  # soglia di flusso d'acqua
FLOW_MONITOR_DURATION = 10  # durata in secondi per monitorare il flusso elevato

# Callback quando si riceve un messaggio MQTT con i dati dai sensori
def on_message(client, userdata, msg):
    global total_water_saved  #riferimento alla variabile globale
    # Decodifica il payload del messaggio
    sensor_data = json.loads(msg.payload)
    sensor_id = sensor_data["sensor_id"]
    water_flow = sensor_data.get("water_flow", None)
    soil_moisture = sensor_data.get("soil_moisture", 70)  #Inizialmente fissato a 70
    water_leak = sensor_data.get("water_leak", None)

#controlla se il sensore esiste già e aggiorna il valore di umidità
    if sensor_id not in sensor_status:
        sensor_status[sensor_id] = {
            'irrigation_active': False,
            'soil_moisture': soil_moisture,
            'high_flow_time': 0  # Tempo in cui il flusso d'acqua è sopra la soglia
        }

#memorizza i dati ricevuti nel dizionario 
    sensor_status[sensor_id].update({
        "water_flow": water_flow,
        "soil_moisture": soil_moisture,
        "water_leak": water_leak,
        "last_update": time.time()
    })

    print(f"[{CLIENT_ID}] Dati ricevuti dal sensore {sensor_id}: ")
    
    if water_flow is not None:
        print(f"Flusso d'acqua: {water_flow} litri/minuto")
        #esempio: se il flusso d'acqua è superiore a 50 per un periodo prolungato, genera avviso
        if water_flow > FLOW_THRESHOLD:
            sensor_status[sensor_id]['high_flow_time'] += 1  # Incrementa il contatore di tempo
            print(f"Avviso: flusso d'acqua elevato nella rete ({water_flow} litri/minuto)")
        else:
            sensor_status[sensor_id]['high_flow_time'] = 0  # Resetta il contatore
            # Se il flusso è elevato per un periodo prolungato, genera un avviso
        if sensor_status[sensor_id]['high_flow_time'] >= FLOW_MONITOR_DURATION:
            send_alert(sensor_id, "Possibile guasto o malfunzionamento rilevato!")

    if soil_moisture is not None:
        print(f"umidità del terreno: {soil_moisture} %")
        #esempio: se l'umidità del terreno è inferiore a 30% attiva irrigazione
        if soil_moisture < 30:
            send_command(sensor_id, "ATTIVA IRRIGAZIONE")
            sensor_status[sensor_id]["irrigation_active"] = True
            print(f"[{CLIENT_ID}] Irrigazione attivata. Umidità del terreno: {soil_moisture}%")
        
        elif soil_moisture > 70:
            send_command(sensor_id, "DISATTIVA IRRIGAZIONE")
            sensor_status[sensor_id]["irrigation_active"] = False

            # Calcolo del risparmio idrico
            total_water_saved += 5  # Simula un risparmio di acqua per ogni attivazione dell'irrigazione
            print(f"[{CLIENT_ID}] Acqua risparmiata finora: {total_water_saved} litri.")

    if water_leak is not None:
        leak_status = "Rilevata" if water_leak else "Non rilevata"
        print(f"Perdita d'acqua: {leak_status}")
        #esempio: se è rilevata una perdita d'acqua, invia un avviso 
        if water_leak:
            print(f"Avviso: perdita d'acqua rilevata nella rete!")
            send_alert(sensor_id, "Intervento immediato richiesto per perdita d'acqua.")
    
# Funzione per inviare un comando a un sensore
def send_command(sensor_id, command):
    command_topic = f"sensori/comandi/{sensor_id}"
    client.publish(command_topic, command)
    print(f"[{CLIENT_ID}] Comando inviato al sensore {sensor_id}: {command}")

# Funzione per inviare un avviso di manutenzione
def send_alert(sensor_id, message):
    alert_message = {
        "sensor_id": sensor_id,
        "message": message
    }
    client.publish(TOPIC_ALERT, json.dumps(alert_message))
    print(f"[{CLIENT_ID}] Avviso inviato: {message} per il sensore {sensor_id}")

#funzione per simulare la variazione dell'umidità 
def update_soil_moisture():
    for sensor_id, status in sensor_status.items():
        #se l'irrigazione è attiva, aumenta l'umidità, altrimenti diminuisce
        if status["irrigation_active"]:
            status["soil_moisture"] += 5
            print(f"Irrigazione attiva per il sensore {sensor_id}, umidità aumentata a {status["soil_moisture"]}")
        else:
            status["soil_moisture"] -= 5
            print(f"Irrigazione disattivata per il sensore {sensor_id}, umidità diminuita a {status["soil_moisture"]}")

#funzione per stampare lo stato della rete 
def print_status():
    print("\n---Stato attuale della rete idrica e del campo agricolo---")
    for sensor_id, status in sensor_status.items():
        print(f"Sensore {sensor_id}: ")
        print(f"Flusso d'acqua: {status.get("water_flow", "Non disponibile")} litri/minuto")
        print(f"Umidità del terreno: {status["soil_moisture"]} %")
        print(f"Perdita d'acqua: {"Rilevata" if status.get("water_leak") else "Non rilevata"}")
        print(f"Ultimo aggiornamento: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(status["last_update"]))}")
        print(f"[{CLIENT_ID}] Acqua risparmiata finora: {total_water_saved} litri.")

# Configurazione del client MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, CLIENT_ID)
client.on_message = on_message  

# Connessione al broker e sottoscrizione al topic dei dati sensori
client.connect(BROKER, PORT, 60)
client.subscribe(TOPIC_DATA)

try:
    print(f"[{CLIENT_ID}] Server in ascolto sui dati sensori...")
    client.loop_start()  #avvia il ciclo principale del server

    while True:
        #aggiorna lo stato dell'umidità ogni 5 secondi
        update_soil_moisture()
        #ogni 10 secondi stampa lo stato attuale della rete
        print_status()
        time.sleep(10)

except KeyboardInterrupt:
    print(f"[{CLIENT_ID}] Chiusura del server MQTT.")
    client.disconnect()