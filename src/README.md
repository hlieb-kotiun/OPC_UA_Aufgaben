# DHT22 als OPC-UA-Sensor

**Fach:** LF07  
**Thema:** Auslesen eines DHT22-Sensors mit Raspberry Pi und Bereitstellung der Messwerte über OPC UA

---

## 1. Ziel des Projekts

In diesem Projekt wird ein DHT22-Sensor an einem Raspberry Pi ausgelesen. Der Sensor liefert die Temperatur und die Luftfeuchtigkeit. Ein Python-Programm auf dem Raspberry Pi stellt diese Messwerte als OPC-UA-Server im Netzwerk bereit.

Ein zweites Gerät, hier ein Windows-PC, führt einen OPC-UA-Client aus. Der Client verbindet sich mit dem Raspberry Pi, liest Werte aus dem Address Space und erhält Temperaturänderungen über eine Subscription automatisch.

Zusätzlich ist eine LED angeschlossen. Der Server vergleicht die gemessene Temperatur mit einem Grenzwert. Wird dieser überschritten, schaltet der Raspberry Pi die LED ein und aktualisiert den zugehörigen OPC-UA-Wert.

## 2. Verwendete Hardware

| Hardware | Aufgabe im Projekt |
|---|---|
| Raspberry Pi | Führt `server.py` aus, liest den Sensor und steuert die LED. |
| DHT22 | Misst Temperatur und Luftfeuchtigkeit. |
| LED | Zeigt die Überschreitung der Maximaltemperatur an. |
| Widerstand | Begrenzt den Strom der LED. |
| Breadboard und Jumperkabel | Verbinden Sensor, LED und GPIO-Anschlüsse. |
| Windows-PC | Führt `client.py` als OPC-UA-Client aus. |

Der Raspberry-Pi-Typ ist im Code nicht genauer angegeben. Deshalb wird hier nur allgemein von einem Raspberry Pi gesprochen.

## 3. Schaltplan / Verkabelung

Die Anschlüsse sind im Projekt wie folgt vorgesehen:

| Bauteil | Anschluss | Verbindung |
|---|---|---|
| DHT22 | `+` | 3,3 V des Raspberry Pi |
| DHT22 | `-` | GND des Raspberry Pi |
| DHT22 | `OUT` | GPIO18 |
| LED | Anode | GPIO17 |
| LED | Kathode | über Vorwiderstand zu GND |

```text
Raspberry Pi                         DHT22
------------                         -----
3,3 V   ---------------------------> +
GND     ---------------------------> -
GPIO18  ---------------------------> OUT

Raspberry Pi                         LED-Schaltung
------------                         -------------
GPIO17  ----> LED ----> Widerstand ----> GND
```

### Hardwareaufbau mit leuchtender LED

![Hardwareaufbau mit DHT22, Breadboard und LED](assets/photo_2026-10-01_11-51-13.jpg)

*Abbildung: Der DHT22 ist am Raspberry Pi angeschlossen. Auf dem Breadboard ist die LED zu sehen; sie leuchtet auf dem Foto.*

## 4. Verwendete GPIOs

| Komponente | GPIO | Funktion |
|---|---:|---|
| DHT22 | GPIO18 (`board.D18`) | Digitale Sensordaten für Temperatur und Luftfeuchtigkeit lesen |
| LED | GPIO17 (`board.D17`) | LED als digitaler Ausgang ein- und ausschalten |

## 5. Verwendete Software und Bibliotheken

| Software / Bibliothek | Verwendung im Projekt |
|---|---|
| Python | Programmiersprache für Server und Client |
| `asyncio` | Führt die asynchronen Programmabläufe aus und wartet zwischen Messungen. |
| `asyncua` | Stellt den OPC-UA-Server bzw. den OPC-UA-Client bereit. |
| `board` | Stellt die Raspberry-Pi-Pin-Bezeichnungen wie `D17` und `D18` bereit. |
| `adafruit_dht` | Liest den DHT22-Sensor aus. |
| `digitalio` | Konfiguriert GPIO17 als digitalen Ausgang für die LED. |

## 6. Aufbau der Software

| Datei | Aufgabe |
|---|---|
| `server.py` | Läuft auf dem Raspberry Pi. Die Datei liest den DHT22, erstellt den OPC-UA-Address-Space, aktualisiert die Werte und steuert die LED anhand des Grenzwerts. |
| `client.py` | Läuft auf dem Windows-PC. Die Datei verbindet sich mit dem Server, sucht die gewünschten Nodes, liest aktuelle Werte und abonniert Temperaturänderungen. |

## 7. Systemarchitektur

```text
                 +------------------+
                 |      DHT22       |
                 | Temperatur / rF  |
                 +--------+---------+
                          |
                       GPIO18
                          |
                          v
 +------------------ Raspberry Pi ------------------+
 |                    server.py                      |
 |  Sensor auslesen -> OPC-UA-Werte aktualisieren    |
 |  Temperatur > MaxTemperatur?                      |
 |                    |                              |
 |                 GPIO17                            |
 +-------------------+-------------------------------+
                     |
                     v
                   [ LED ]

        OPC UA über TCP, Port 4840
                     |
                     v
          Windows-PC / client.py
          Werte lesen und Temperatur abonnieren
```

## 8. OPC-UA-Server

Der OPC-UA-Server wird in `server.py` erzeugt. Er verwendet folgenden Endpoint und Namespace:

| Einstellung | Wert |
|---|---|
| Endpoint | `opc.tcp://0.0.0.0:4840` |
| Port | `4840` |
| Eigener Namespace | `http://raspberrypi/dht22` |

`0.0.0.0` bedeutet, dass der Server auf den Netzwerkschnittstellen des Raspberry Pi lauscht. Der Client verwendet für die Verbindung die IP-Adresse des Raspberry Pi.

Die wichtigsten Einstellungen im Code sind:

```python
server.set_endpoint("opc.tcp://0.0.0.0:4840")

uri = "http://raspberrypi/dht22"
idx = await server.register_namespace(uri)
```

Der Server liest den Sensor in einer Endlosschleife aus. Danach aktualisiert er die OPC-UA-Variablen und prüft den Grenzwert. Zwischen zwei Durchläufen wartet das Programm zwei Sekunden.

```python
temperature = dht_sensor.temperature
humidity = dht_sensor.humidity

await temperatur.write_value(temperature)
await luftfeuchtigkeit.write_value(humidity)

max_temp_value = await max_temperatur.read_value()
await asyncio.sleep(2)
```

Bei einem Sensorfehler fängt das Programm die Exception ab und gibt `Sensorfehler` mit Fehlertyp und Meldung aus. Danach läuft die Schleife weiter.

## 9. OPC-UA Address Space

Der Server legt im Standardbereich `Objects` folgende Nodes an. Die Kennzeichnung `2:` wird im Client verwendet, weil der eigene Namespace beim Ausführen als Namespace-Index 2 angesprochen wird.

```text
Root
└── Objects (0:Objects)
    └── RaspberryPi (2:RaspberryPi)
        ├── DHT22 (2:DHT22)
        │   ├── Temperatur (2:Temperatur)
        │   ├── Luftfeuchtigkeit (2:Luftfeuchtigkeit)
        │   └── MaxTemperatur (2:MaxTemperatur)
        └── LED (2:LED)
            └── Zustand (2:Zustand)
```

## 10. Verwendete Nodes

| Node | Bedeutung | Beispielwert |
|---|---|---|
| `RaspberryPi` | Objekt für das Raspberry-Pi-System | Objekt, kein Messwert |
| `DHT22` | Objekt für den Sensor | Objekt, kein Messwert |
| `Temperatur` | Aktuell gemessene Temperatur in °C | `24.2` |
| `Luftfeuchtigkeit` | Aktuell gemessene relative Luftfeuchtigkeit in % | `56.0` |
| `MaxTemperatur` | Grenzwert für die LED-Steuerung | `25.0` |
| `LED` | Objekt für die LED | Objekt, kein Messwert |
| `Zustand` | Aktueller LED-Zustand | `False` oder `True` |

Die genannten Zahlenwerte sind Beispiele aus dem Code bzw. aus dem Client-Foto. Die tatsächlichen Sensorwerte können sich bei jeder Messung ändern.

## 11. Verwendete Datentypen

| Variable | Datentyp | Bedeutung | Beispiel |
|---|---|---|---|
| `temperature` / Node `Temperatur` | Zahl mit Nachkommastellen (`float`) | Temperatur des DHT22 in °C | `24.2` |
| `humidity` / Node `Luftfeuchtigkeit` | Zahl mit Nachkommastellen (`float`) | Luftfeuchtigkeit des DHT22 in % | `56.0` |
| `max_temp_value` / Node `MaxTemperatur` | Zahl mit Nachkommastellen (`float`) | Gelesener Temperaturgrenzwert | `25.0` |
| `led_gpio.value` / Node `Zustand` | Wahrheitswert (`bool`) | Physischer und veröffentlichter LED-Zustand | `True` / `False` |
| `idx` | Ganzzahl (`int`) | Namespace-Index des registrierten Namespace | z. B. `2` |

Die OPC-UA-Variablen werden im Server mit `0.0`, `25.0` und `False` angelegt. Daraus ergeben sich für die Mess- und Grenzwerte Zahlen mit Nachkommastellen und für die LED ein Boolean-Wert.

## 12. OPC-UA-Client

In `client.py` ist die Serveradresse fest eingetragen:

```python
url = "opc.tcp://10.62.4.162:4840"

async with Client(url=url) as client:
```

Nach dem Aufbau der Verbindung verwendet der Client den Root-Node und sucht die benötigten Nodes über ihren Pfad. Zum Beispiel wird die Temperatur so gesucht:

```python
temperatur = await root.get_child([
    "0:Objects",
    "2:RaspberryPi",
    "2:DHT22",
    "2:Temperatur"
])
```

Auf dieselbe Weise findet der Client `Luftfeuchtigkeit`, `MaxTemperatur` und `LED/Zustand`. Diese drei Werte liest er anschließend einmal mit `read_value()` aus und gibt sie aus. Die Temperatur wird nicht in einer eigenen Abfrageschleife gelesen, sondern über eine Subscription empfangen.

## 13. Netzwerkverbindung

Der Raspberry Pi arbeitet als OPC-UA-Server, der Windows-PC als OPC-UA-Client. Die Kommunikation erfolgt über TCP mit OPC UA auf Port `4840`.

Die im Client eingetragene Adresse `10.62.4.162` ist die IP-Adresse des Raspberry Pi im verwendeten Netzwerk. Sie ist nur ein Beispiel aus diesem Projekt und kann sich bei einem anderen Netzwerk oder nach einer neuen Netzwerkverbindung ändern. In diesem Fall muss die URL in `client.py` angepasst werden.

```text
Windows-PC (Client)  --- TCP / OPC UA :4840 --->  Raspberry Pi (Server)
```

## 14. Erweiterung 1 – LED

Die LED ist an GPIO17 angeschlossen. Der Server konfiguriert diesen Pin als Ausgang und setzt ihn beim Start zunächst auf `False`.

```python
led_gpio = digitalio.DigitalInOut(board.D17)
led_gpio.direction = digitalio.Direction.OUTPUT
led_gpio.value = False
```

Im OPC-UA-Address-Space gehört die Variable `Zustand` zum Objekt `LED`. Ihr Boolean-Wert beschreibt den aktuellen Zustand: `True` bedeutet LED an, `False` bedeutet LED aus.

## 15. Erweiterung 2 – LED über OPC UA steuern

In der vorliegenden Endversion wird die LED **nicht direkt vom Client geschrieben**. `client.py` sucht `LED/Zustand` und liest den Wert einmal aus:

```python
led_value = await led_zustand.read_value()
print(f"LED: {led_value}")
```

Die Entscheidung über die LED trifft ausschließlich `server.py`. Dort wird der Zustand sowohl am GPIO als auch im OPC-UA-Node gesetzt. Damit bildet der Node `LED/Zustand` den durch die Grenzwertlogik gesteuerten Zustand ab.

```python
if temperature > max_temp_value:
    led_gpio.value = True
    await led_zustand.write_value(True)
else:
    led_gpio.value = False
    await led_zustand.write_value(False)
```

## 16. Erweiterung 3 – Grenzwert

Die Variable `MaxTemperatur` wird beim Start mit dem Standardwert `25.0` angelegt. Der Server liest diesen Wert in jedem Messdurchlauf und vergleicht ihn mit der aktuellen Temperatur.

```python
max_temperatur = await dht22.add_variable(idx, "MaxTemperatur", 25.0)
```

Die Bedingung ist bewusst strikt: Die LED schaltet nur ein, wenn `Temperatur > MaxTemperatur` gilt. Bei gleicher oder niedriger Temperatur bleibt sie aus.

```text
Sensorwert Temperatur
          |
          v
Temperatur > MaxTemperatur?
      |                 |
    Ja                  Nein
      |                 |
      v                 v
LED an / Zustand=True  LED aus / Zustand=False
```

## 17. Erweiterung 4 – Subscription

Beim **Polling** würde der Client in festen Abständen selbst nach einem neuen Wert fragen. Bei einer **Subscription** überwacht der OPC-UA-Server eine Variable und meldet Änderungen automatisch an den Client. Das reduziert unnötige Abfragen und passt gut zu sich ändernden Messwerten.

Der Client definiert dafür einen `SubscriptionHandler`. Die Methode `datachange_notification()` wird beim Eintreffen einer Änderung ausgeführt und gibt den neuen Wert aus.

```python
class SubscriptionHandler:
    def datachange_notification(self, node, val, data):
        print(f"Wert geändert: {val}")
```

Danach erstellt der Client eine Subscription mit einem Veröffentlichungsintervall von `500` und abonniert ausschließlich die Temperatur-Node:

```python
subscription = await client.create_subscription(500, handler)
await subscription.subscribe_data_change(temperatur)
```

Temperaturänderungen werden dadurch automatisch an den Client gemeldet. Für Luftfeuchtigkeit, Maximaltemperatur und LED-Zustand ist im aktuellen Client keine Subscription eingerichtet.

## 18. Ablauf des Gesamtsystems

1. `server.py` startet auf dem Raspberry Pi den OPC-UA-Server auf Port 4840.
2. Der Server erstellt die Objekte und Variablen im OPC-UA-Address-Space.
3. Der DHT22 misst Temperatur und Luftfeuchtigkeit; der Raspberry Pi liest beide Werte über GPIO18 aus.
4. Der Server schreibt die aktuellen Messwerte in `Temperatur` und `Luftfeuchtigkeit`.
5. Der Server liest `MaxTemperatur` und vergleicht sie mit der aktuellen Temperatur.
6. Bei Überschreitung schaltet der Server die LED an GPIO17 ein; ansonsten schaltet er sie aus. Gleichzeitig aktualisiert er `LED/Zustand`.
7. Nach zwei Sekunden beginnt der nächste Messdurchlauf.
8. `client.py` verbindet sich vom Windows-PC aus mit dem Raspberry Pi, sucht die Nodes und liest Luftfeuchtigkeit, Maximaltemperatur sowie LED-Zustand.
9. Änderungen der Temperatur meldet der OPC-UA-Server über die Subscription an den Client.

## 19. Screenshots / Funktionstest

### Ausgabe des OPC-UA-Servers und Grenzwertreaktion

![Konsolenausgabe des OPC-UA-Servers](assets/photo_2026-10-01_11-51-42.jpg)

*Abbildung: Die Konsolenausgabe zeigt Temperatur, Luftfeuchtigkeit, den Grenzwert von 25,0 °C und den LED-Zustand. Im sichtbaren Verlauf wechselt der LED-Zustand bei einer Temperatur über 25,0 °C von `False` zu `True`. Außerdem ist ein einzelner Sensorfehler (`RuntimeError`) zu sehen; die nachfolgenden Messausgaben laufen weiter.*

### OPC-UA-Client mit aktiver Temperatur-Subscription

![Konsolenausgabe des OPC-UA-Clients](assets/photo_2026-10-01_11-51-59.jpg)

*Abbildung: Der Client meldet die erfolgreiche Verbindung, den Start der Temperatur-Subscription sowie empfangene Änderungen wie 24,2, 24,4 und 24,7. Zusätzlich werden Luftfeuchtigkeit, MaxTemperatur und LED-Zustand einmal ausgegeben.*

## 20. Ergebnis / Fazit

Der DHT22 wird vom Raspberry Pi erfolgreich ausgelesen und die Messwerte werden über einen OPC-UA-Server bereitgestellt. Ein Windows-PC kann als Client über das Netzwerk darauf zugreifen. Die LED ist über GPIO17 integriert und reagiert automatisch auf die Überschreitung des Grenzwerts `MaxTemperatur`. Die vorhandene Client-Ausgabe belegt außerdem, dass Temperaturänderungen über eine OPC-UA-Subscription empfangen werden.
