# Подивитись список аудіопристроїв (Windows)
import sounddevice as sd

print("\n=== Аудіопристрої ===")
for i, device in enumerate(sd.query_devices()):
    print(f"[{i}] {device['name']} ({device['hostapi']})")


print("\n=== Перевірити, які sample rates підтримує device_id=31 ===")
sd.check_input_settings(device=31, samplerate=48000)  # або 44100, 48000

print("\n=== [PaErrorCode -9997] тоді перебирай  samplerate ===")
