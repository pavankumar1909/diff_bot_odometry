#include <Arduino.h>

/* ---------- Encoder pins (PCINT) ---------- */
#define ENC_A 12      // PCINT4
#define ENC_B 13      // PCINT5

/* ---------- Motor driver pins ---------- */
#define ENA  9
#define IN1  7
#define IN2  8

/* ---------- Encoder parameters ---------- */
#define ENCODER_PPR 385.0    // pulses per revolution (after gearbox)
#define SAMPLE_TIME 100     // ms

/* ---------- Globals ---------- */
volatile long encoder_ticks = 0;
volatile int  encoder_dir = 1;
volatile uint8_t lastA = 0;

unsigned long last_time = 0;

/* ---------- Setup ---------- */
void setup() {

  pinMode(ENC_A, INPUT_PULLUP);
  pinMode(ENC_B, INPUT_PULLUP);

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  /* Enable Pin Change Interrupts for D12 & D13 */
  PCICR  |= (1 << PCIE0);     // Enable PCINT for PORTB
  PCMSK0 |= (1 << PCINT4);    // D12
  PCMSK0 |= (1 << PCINT5);    // D13

  lastA = digitalRead(ENC_A);

  Serial.begin(115200);
}

/* ---------- Pin Change ISR (D8–D13) ---------- */
ISR(PCINT0_vect) {

  uint8_t A = digitalRead(ENC_A);
  uint8_t B = digitalRead(ENC_B);

  if (A != lastA) {   // edge on channel A
    if (A == B)
      encoder_dir = 1;
    else
      encoder_dir = -1;

    encoder_ticks++;
    lastA = A;
  }
}

/* ---------- Motor control ---------- */
void setMotor(int pwm) {

  pwm = constrain(pwm, -255, 255);

  if (pwm >= 0) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    analogWrite(ENA, pwm);
  } else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    analogWrite(ENA, -pwm);
  }
}

/* ---------- Main loop ---------- */
void loop() {

  setMotor(180);   // run motor forward

  unsigned long now = millis();

  if (now - last_time >= SAMPLE_TIME) {

    noInterrupts();
    long ticks = encoder_ticks;
    int dir = encoder_dir;
    encoder_ticks = 0;
    interrupts();

    /* Angular velocity (rad/s) */
    double omega =
        (ticks * (1000.0 / SAMPLE_TIME)) *
        (2.0 * PI / ENCODER_PPR);

    omega *= dir;

    Serial.print("Motor velocity (rad/s): ");
    Serial.println(omega, 4);

    last_time = now;
  }
}
