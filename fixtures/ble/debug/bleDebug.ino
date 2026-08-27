// randomNumbers, plus a debug channel - see fixtures/ble/debug/README.md.
//
// The heartbeat deliberately prints the STACK's state, not the library's.
// PhyphoxBLE::currentConnections and ::isSubscribed are the library's own
// bookkeeping: isSubscribed is never cleared on disconnect, and write()
// notifies unconditionally without consulting either, so "subscribed=1
// writes=1212" says nothing about whether a single packet left the board.
// What decides that is what BLECharacteristic::notify() itself checks:
// the server's connected count and the 0x2902 descriptor on the data
// characteristic. Both are readable from a sketch, so both are printed,
// with the library's flags alongside for comparison.
#include <phyphoxBle.h>
#include <BLEDevice.h>

static const char *DATA_SERVICE = "cddf1001-30f7-4671-8b43-5e40ba53514a";
static const char *DATA_CHAR    = "cddf1002-30f7-4671-8b43-5e40ba53514a";

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

// The CCCD as the stack holds it: 0x0001 = notifications enabled for a
// subscribed client, 0x0000 or absent = notify() will not send.
static void printCccd() {
    BLEServer *server = BLEDevice::getServer();
    if (!server) { Serial.print(" cccd=<no server>"); return; }
    Serial.print(" connected=");
    Serial.print(server->getConnectedCount());
    BLEService *svc = server->getServiceByUUID(BLEUUID(DATA_SERVICE));
    if (!svc) { Serial.print(" cccd=<no service>"); return; }
    BLECharacteristic *ch = svc->getCharacteristic(BLEUUID(DATA_CHAR));
    if (!ch) { Serial.print(" cccd=<no characteristic>"); return; }
    BLEDescriptor *d = ch->getDescriptorByUUID(BLEUUID((uint16_t)0x2902));
    if (!d) { Serial.print(" cccd=<none>"); return; }
    uint8_t *v = d->getValue();
    Serial.print(" cccd=0x");
    for (size_t i = 0; i < d->getLength(); i++) {
        if (v[i] < 16) Serial.print("0");
        Serial.print(v[i], HEX);
    }
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
        printCccd();
        Serial.print("  (library says connections=");
        Serial.print(PhyphoxBLE::currentConnections);
        Serial.print(" subscribed=");
        Serial.print(PhyphoxBLE::isSubscribed ? 1 : 0);
        Serial.println(")");
    }
}
