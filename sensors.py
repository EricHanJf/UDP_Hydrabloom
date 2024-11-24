import time
import adafruit_dht
import board

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from dotenv import load_dotenv
from pubnub.callbacks import SubscribeCallback


load_dotenv()
config = PNConfiguration()
config.subscribe_key = "sub-c-ccf0e37c-5f9b-4d4e-8455-af8f49720443"
config.publish_key = "pub-c-75d6d309-722b-419e-b589-e4f425b00fcb"
# from generator uuid // https://www.uuidgenerator.net/
# config.uuid = "2d2163c0-d89d-4c67-b25f-a7dfe60a4e14"
config.user_id = "Hydrabloom_IOT"

MY_CHANNEL = "Hydrabloom_SD3_iot"
pubnub = PubNub(config)


class Listener(SubscribeListener):
    def status(self, pubnub, status):
        print(f"Status: \n{status.category.name}")


pubnub.add_listener(Listener())

subscription = pubnub.channel(MY_CHANNEL).subscription()
subscription.on_message = lambda message: print(
    f"Message from {message.publisher}: {message.message}"
)
subscription.subscribe()


def my_publish_callback(envelope, status):
    if not status.is_error():
        pass
    else:
        pass


time.sleep(1)
publish_result = pubnub.publish().channel(MY_CHANNEL).message("device connected").sync()


dht_device = adafruit_dht.DHT22(board.D4)

print("Starting DHT22 Sensor Test. Press Ctrl+C to exit.\n")

while True:
    try:
        temperature_c = dht_device.temperature
        temperature_f = temperature_c * (9 / 5) + 32

        humidity = dht_device.humidity

        if temperature_c is not None and humidity is not None:
            print(
                f"Temperature: {temperature_c:.1f}°C / {temperature_f:.1f}°F, Humidity: {humidity:.1f}%"
            )
        else:
            print("Failed to read data from the sensor. Retrying...")

    except RuntimeError as error:
        print(f"RuntimeError: {error.args[0]}")

    except Exception as error:
        print(f"An error occurred: {error}")
        dht_device.exit()
        break

    time.sleep(2.0)
