import asyncio
from asyncua import Client


# Wird automatisch aufgerufen,
# wenn sich ein abonnierter Wert ändert
class SubscriptionHandler:

    def datachange_notification(self, node, val, data):
        print(f"Wert geändert: {val}")


async def main():

    # IP-Adresse des Raspberry Pi
    url = "opc.tcp://10.62.4.162:4840"

    # Verbindung mit dem OPC-UA-Server
    async with Client(url=url) as client:

        print("OPC-UA-Client gestartet")
        print("Mit Server verbunden")
        print("--------------------------")

        root = client.nodes.root


        # Temperatur-Variable finden
        temperatur = await root.get_child([
            "0:Objects",
            "2:RaspberryPi",
            "2:DHT22",
            "2:Temperatur"
        ])


        # Luftfeuchtigkeit-Variable finden
        luftfeuchtigkeit = await root.get_child([
            "0:Objects",
            "2:RaspberryPi",
            "2:DHT22",
            "2:Luftfeuchtigkeit"
        ])


        # MaxTemperatur finden
        max_temperatur = await root.get_child([
            "0:Objects",
            "2:RaspberryPi",
            "2:DHT22",
            "2:MaxTemperatur"
        ])


        # LED-Zustand finden
        led_zustand = await root.get_child([
            "0:Objects",
            "2:RaspberryPi",
            "2:LED",
            "2:Zustand"
        ])


        # -------------------------
        # Subscription erstellen
        # -------------------------

        handler = SubscriptionHandler()

        subscription = await client.create_subscription(
            500,
            handler
        )


        # Temperatur abonnieren
        await subscription.subscribe_data_change(
            temperatur
        )

        print("Subscription für Temperatur gestartet")
        print("--------------------------")


        # Aktuelle andere Werte einmal lesen
        humidity_value = await luftfeuchtigkeit.read_value()
        max_temp_value = await max_temperatur.read_value()
        led_value = await led_zustand.read_value()

        print(f"Luftfeuchtigkeit: {humidity_value:.1f} %")
        print(f"MaxTemperatur: {max_temp_value:.1f} °C")
        print(f"LED: {led_value}")
        print("--------------------------")


        # Client aktiv halten
        while True:
            await asyncio.sleep(1)


asyncio.run(main())