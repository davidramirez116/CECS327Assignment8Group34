import socket
from pymongo import MongoClient
from datetime import datetime, timedelta

client = MongoClient('mongodb+srv://ryangallagher01:FtTgpOQcUsDo01o7@cluster0.7mcrx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['test']
collection = db['IOT Devices_virtual'] 


def averageMoisture():
    # Calculate the timestamp for 3 hours ago
    three_hours_ago = datetime.now() - timedelta(hours=3)
    three_hours_ago_timestamp = int(three_hours_ago.timestamp())  # Convert to UNIX timestamp

    # Query to find documents from the last 3 hours
    cursor = collection.find(
        {"payload.timestamp": {"$gte": str(three_hours_ago_timestamp)}},  # Match timestamps >= 3 hours ago
        {"payload.Moisture Meter - Fridge Moisture Meter": 1, "payload.timestamp": 1}  # Only fetch relevant fields
    )

    # Calculate the average moisture level
    moisture_values = []

    for document in cursor:
        try:
            value = float(document["payload"]["Moisture Meter - Fridge Moisture Meter"])  # Extract and convert moisture values
            moisture_values.append(value)
        except (KeyError, ValueError):
            # Skip documents with missing or invalid values
            continue

    # Compute the average
    if moisture_values:
        average = sum(moisture_values) / len(moisture_values)
        return f"Average Moisture Level (Last 3 Hours): {average:.4f} % wfv"
    else:
        return "No valid moisture level readings found in the last 3 hours."

def averageWaterConsumption():
    cursor = collection.find({}, {"payload.Water Consumption Sensor"})
    consumptionVals = []

    for obj in cursor:
        try:
            value = float(obj["payload"]["Water Consumption Sensor"]) 
            consumptionVals.append(value)
        except (KeyError, ValueError):
            continue

    if consumptionVals:
        avg = sum(consumptionVals)/len(consumptionVals) #currently ml/s
        converted_avg = avg / 3785.41 * 1800 #converts mL/s to G/Cycle
        return f"Average Water Consumption: {converted_avg:.4f} G/Cycle"
    else:
        return "Error, no consumption values"

def electricityConsumption():
    max_value = float('-inf')
    max_device = None

    # Iterate through all documents in the collection
    cursor = collection.find({})
    for document in cursor:
        payload = document.get("payload", {})
        for key, value in payload.items():
            if "Ammeter" in key:  # Check if the field name contains 'Ammeter'
                try:
                    ammeter_value = float(value)  # Convert to float for comparison
                    if ammeter_value > max_value:
                        max_value = ammeter_value
                        if payload.get("board_name") == "Raspberry Pi 4 - Raspberry Pi 4 - DISHWASHER":
                            device = "Dishwasher"
                        elif payload.get("board_name") == "Raspberry Pi 4 - Raspberry Pi 4 - FRIDGE":
                            device = "Fridge 1"
                        else:
                            device = "Fridge 2"
                        max_device = {
                            "device_name": device,
                            "ammeter_value": ammeter_value
                        }
                except ValueError:
                    continue  # Skip invalid numeric values

    # Output the device with the highest Ammeter value
    if max_device:
        return f"Device with the highest Ammeter value: \nDevice Name: {max_device['device_name']}\nAmmeter Value: {max_device['ammeter_value']} A"
    else:
        return "No valid Ammeter values found."

def server():
    server_socket  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = input("Please input Server IP: ")
    server_port = int(input("Please input Server Port: "))
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)
    incoming_socket, incoming_address = server_socket.accept()

    while True:
        try:
            data = incoming_socket.recv(1024).decode('utf-8')
            if not data:
                break
            if data == "What is the average moisture inside my kitchen fridge in the past three hours?":
                response = averageMoisture()
                incoming_socket.sendall(response.encode('utf-8'))
            elif data == "What is the average water consumption per cycle in my smart dishwasher?":
                response = averageWaterConsumption()
                incoming_socket.sendall(response.encode('utf-8'))
            elif data == "Which device consumed more electricity among my three IoT devices?":
                response = electricityConsumption()
                incoming_socket.sendall(response.encode('utf-8'))
            elif data == "exit":
                response = "Exiting"
                incoming_socket.sendall(response.encode('utf-8'))
                break
            else:
                print("Sorry, this query cannot be processed.")

        except socket.error as e:
            print("Error: ", e)
            break

    incoming_socket.close()

if __name__ == "__main__":
    server()

