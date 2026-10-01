import asyncio
import board
import adafruit_dht
import digitalio

from asyncua import Server


# -------------------------
# Hardware
# -------------------------

# DHT22 an GPIO18
dht_sensor = adafruit_dht.DHT22(board.D18)

# LED an GPIO17
led_gpio = digitalio.DigitalInOut(board.D17)
led_gpio.direction = digitalio.Direction.OUTPUT
led_gpio.value = False


async def main():

    # -------------------------
    # OPC-UA-Server
    # -------------------------

    server = Server()
    await server.init()

    # OPC-UA Endpoint
    server.set_endpoint("opc.tcp://0.0.0.0:4840")

    # Eigenen Namespace registrieren
    uri = "http://raspberrypi/dht22"
    idx = await server.register_namespace(uri)


    # -------------------------
    # Address Space
    # -------------------------

    objects = server.nodes.objects

    # RaspberryPi-Objekt
    raspberry_pi = await objects.add_object(
        idx,
        "RaspberryPi"
    )

    # DHT22-Objekt
    dht22 = await raspberry_pi.add_object(
        idx,
        "DHT22"
    )

    # LED-Objekt
    led = await raspberry_pi.add_object(
        idx,
        "LED"
    )


    # -------------------------
    # DHT22 Variablen
    # -------------------------

    temperatur = await dht22.add_variable(
        idx,
        "Temperatur",
        0.0
    )

    luftfeuchtigkeit = await dht22.add_variable(
        idx,
        "Luftfeuchtigkeit",
        0.0
    )


    # -------------------------
    # Erweiterung 3:
    # MaxTemperatur
    # -------------------------

    max_temperatur = await dht22.add_variable(
        idx,
        "MaxTemperatur",
        25.0
    )


    # -------------------------
    # LED Variable
    # -------------------------

    led_zustand = await led.add_variable(
        idx,
        "Zustand",
        False
    )


    # -------------------------
    # Server starten
    # -------------------------

    print("OPC-UA-Server gestartet!")
    print("MaxTemperatur: 25.0 °C")
    print("--------------------------")


    async with server:

        while True:

            try:

                # -------------------------
                # DHT22 auslesen
                # -------------------------

                temperature = dht_sensor.temperature
                humidity = dht_sensor.humidity


                # -------------------------
                # OPC-UA-Werte aktualisieren
                # -------------------------

                await temperatur.write_value(temperature)
                await luftfeuchtigkeit.write_value(humidity)


                # -------------------------
                # Grenzwert lesen
                # -------------------------

                max_temp_value = await max_temperatur.read_value()


                # -------------------------
                # Grenzwert prüfen
                # -------------------------

                if temperature > max_temp_value:

                    # Temperatur über Grenzwert
                    led_gpio.value = True
                    await led_zustand.write_value(True)

                else:

                    # Temperatur unter Grenzwert
                    led_gpio.value = False
                    await led_zustand.write_value(False)


                # -------------------------
                # Ausgabe
                # -------------------------

                led_value = await led_zustand.read_value()

                print(f"Temperatur: {temperature:.1f} °C")
                print(f"Luftfeuchtigkeit: {humidity:.1f} %")
                print(f"MaxTemperatur: {max_temp_value:.1f} °C")
                print(f"LED: {led_value}")
                print("--------------------------")


            except Exception as error:

                print("Sensorfehler:", type(error).__name__, error)


            # Alle 2 Sekunden neue Messung
            await asyncio.sleep(2)


# Programm starten
asyncio.run(main())