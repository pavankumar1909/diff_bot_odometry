#include <PID_v1_bc.h>

/* ---------------- Motor Driver Pins (L298N) ---------------- */
#define L298N_enA  9
#define L298N_enB 10
#define L298N_in1  7
#define L298N_in2  8
#define L298N_in3 12
#define L298N_in4 13

/* ---------------- Encoder Pins ---------------- */
#define RIGHT_ENC_A 3   // Interrupt
#define RIGHT_ENC_B 5
#define LEFT_ENC_A  2   // Interrupt
#define LEFT_ENC_B  4

/* ---------------- Encoder Parameters ---------------- */
#define ENCODER_CPR_MOTOR 48.0
#define GEAR_RATIO        47.0
#define ENCODER_PPR       (ENCODER_CPR_MOTOR * GEAR_RATIO)  // 2256
#define SAMPLE_TIME_MS    100
#define SAMPLE_TIME_S     0.1

/* ---------------- Encoder Counters ---------------- */
volatile long right_ticks = 0;
volatile long left_ticks  = 0;

/* ---------------- PID Variables ---------------- */
// Setpoints (rad/s)
double right_cmd_vel = 0.0;
double left_cmd_vel  = 0.0;

// Measurements (rad/s)
double right_meas_vel = 0.0;
double left_meas_vel  = 0.0;

// Outputs (PWM)
double right_pwm = 0.0;
double left_pwm  = 0.0;

/* ---------------- PID Gains (TUNED FOR GM25-47) ---------------- */
double Kp_r = 6.0, Ki_r = 1.5, Kd_r = 0.1;
double Kp_l = 6.5, Ki_l = 1.5, Kd_l = 0.1;

PID rightPID(&right_meas_vel, &right_pwm, &right_cmd_vel, Kp_r, Ki_r, Kd_r, DIRECT);
PID leftPID (&left_meas_vel,  &left_pwm,  &left_cmd_vel,  Kp_l, Ki_l, Kd_l, DIRECT);

/* ---------------- Serial Parsing ---------------- */
bool right_cmd = false;
bool left_cmd  = false;
bool right_forward = true;
bool left_forward  = true;

char value[8] = "0.0";
uint8_t value_idx = 0;

/* ---------------- Timing ---------------- */
unsigned long last_time = 0;

/* ================= ENCODER ISRs ================= */
void rightEncoderISR() {
  if (digitalRead(RIGHT_ENC_B)) right_ticks++;
  else right_ticks--;
}

void leftEncoderISR() {
  if (digitalRead(LEFT_ENC_B)) left_ticks++;
  else left_ticks--;
}

/* ================= SETUP ================= */
void setup() {
  pinMode(L298N_enA, OUTPUT);
  pinMode(L298N_enB, OUTPUT);
  pinMode(L298N_in1, OUTPUT);
  pinMode(L298N_in2, OUTPUT);
  pinMode(L298N_in3, OUTPUT);
  pinMode(L298N_in4, OUTPUT);

  pinMode(RIGHT_ENC_A, INPUT_PULLUP);
  pinMode(RIGHT_ENC_B, INPUT_PULLUP);
  pinMode(LEFT_ENC_A,  INPUT_PULLUP);
  pinMode(LEFT_ENC_B,  INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(RIGHT_ENC_A), rightEncoderISR, RISING);
  attachInterrupt(digitalPinToInterrupt(LEFT_ENC_A),  leftEncoderISR,  RISING);

  rightPID.SetMode(AUTOMATIC);
  leftPID.SetMode(AUTOMATIC);

  rightPID.SetOutputLimits(0, 255);
  leftPID.SetOutputLimits(0, 255);

  Serial.begin(115200);
}

/* ================= LOOP ================= */
void loop() {

  /* -------- Serial Command Parsing -------- */
  while (Serial.available()) {
    char c = Serial.read();

    if (c == 'r') { right_cmd = true; left_cmd = false; value_idx = 0; }
    else if (c == 'l') { left_cmd = true; right_cmd = false; value_idx = 0; }

    else if (c == 'p') {
      if (right_cmd && !right_forward) {
        digitalWrite(L298N_in1, HIGH); digitalWrite(L298N_in2, LOW);
        right_forward = true;
      }
      if (left_cmd && !left_forward) {
        digitalWrite(L298N_in3, HIGH); digitalWrite(L298N_in4, LOW);
        left_forward = true;
      }
    }

    else if (c == 'n') {
      if (right_cmd && right_forward) {
        digitalWrite(L298N_in1, LOW); digitalWrite(L298N_in2, HIGH);
        right_forward = false;
      }
      if (left_cmd && left_forward) {
        digitalWrite(L298N_in3, LOW); digitalWrite(L298N_in4, HIGH);
        left_forward = false;
      }
    }

    else if (c == ',') {
      if (right_cmd) right_cmd_vel = atof(value);
      else if (left_cmd) left_cmd_vel = atof(value);
      value_idx = 0;
      strcpy(value, "0.0");
    }

    else if (value_idx < sizeof(value) - 1) {
      value[value_idx++] = c;
      value[value_idx] = '\0';
    }
  }

  /* -------- Velocity Calculation -------- */
  unsigned long now = millis();
  if (now - last_time >= SAMPLE_TIME_MS) {

    noInterrupts();
    long rt = right_ticks;
    long lt = left_ticks;
    right_ticks = 0;
    left_ticks = 0;
    interrupts();

    right_meas_vel = (2.0 * PI * rt) / (ENCODER_PPR * SAMPLE_TIME_S);
    left_meas_vel  = (2.0 * PI * lt) / (ENCODER_PPR * SAMPLE_TIME_S);

    rightPID.Compute();
    leftPID.Compute();

    if (right_cmd_vel == 0.0) right_pwm = 0;
    if (left_cmd_vel  == 0.0) left_pwm  = 0;

    analogWrite(L298N_enA, (int)right_pwm);
    analogWrite(L298N_enB, (int)left_pwm);

    /* -------- ROS-Friendly Feedback -------- */
    Serial.print("r:");
    Serial.print(right_meas_vel, 4);
    Serial.print(",l:");
    Serial.println(left_meas_vel, 4);

    last_time = now;
  }
}
