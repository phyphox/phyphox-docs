// randomNumbers, plus the library's own debug channel switched on.
// Identical stimulus to the test scenario (random 0..100 every 50 ms);
// the only additions are Serial and PhyphoxBLE::begin(&Serial), which
// the library declares "for debug purpose", plus a heartbeat so silence
// can be told apart from a hung board. Compiled with -DDEBUG, which is
// what gates the library's onConnect / onSubscribe / disconnected prints.
#include <phyphoxBle.h>

unsigned long lastBeat = 0;
unsigned long writes = 0;

void setup() {
    Serial.begin(115200);
    delay(300);
    Serial.println("=== boot");
    PhyphoxBLE::begin(&Serial);
    PhyphoxBLE::start("phyphox device");
    Serial.println("=== server started");
}

void loop() {
    float randomNumber = random(0, 100);
    PhyphoxBLE::write(randomNumber);
    writes++;
    delay(50);
    if (millis() - lastBeat > 2000) {
        lastBeat = millis();
        Serial.print("[beat] t=");
        Serial.print(millis() / 1000);
        Serial.print("s writes=");
        Serial.print(writes);
        Serial.print(" connections=");
        Serial.print(PhyphoxBLE::currentConnections);
        Serial.print(" subscribed=");
        Serial.println(PhyphoxBLE::isSubscribed ? 1 : 0);
    }
}
