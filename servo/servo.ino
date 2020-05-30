#include <Servo.h>
#include <LiquidCrystal.h>

int D7_pin = 7;
int D6_pin = 6;
int D5_pin = 5;
int D4_pin = 4;
int EN_pin = 3;
int RS_pin = 2;

int LED1_pin = 9;
int LED2_pin = 10;
int LED3_pin = 11;
int LED4_pin = 12;
int LED5_pin = 13;

int i = 1;

Servo myservo;  // create servo object to control a servo

LiquidCrystal lcd(RS_pin, EN_pin, D4_pin, D5_pin, D6_pin, D7_pin);

int potpin = 0;  // analog pin used to connect the potentiometer
int val;    // variable to read the value from the analog pin
int val_pr = -1;
int val_set;
int rpm100;
int rpm10;
int rpm1;
float volt;
int ser = 0;

void setup() {
  myservo.attach(8);  // attaches the servo on pin 8 to the servo object
  Serial.begin(9600);
  lcd.begin(16, 2);
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(LED1_pin, OUTPUT);
  pinMode(LED2_pin, OUTPUT);
  pinMode(LED3_pin, OUTPUT);
  pinMode(LED4_pin, OUTPUT);
  pinMode(LED5_pin, OUTPUT);
}

float mapfloat(long x, long in_min, long in_max, long out_min, long out_max)
{
  return (float)(x - in_min) * (out_max - out_min) / (float)(in_max - in_min) + out_min;
}

void loop() {
  val = analogRead(potpin);            // reads the value of the potentiometer (value between 0 and 1023)
  volt = mapfloat(val, 0, 1023, 0, 5);
  val = map(val, 0, 1023, 0, 181);     // scale it to use it with the servo (value between 0 and 180)
  if(val!=val_pr){
	val_set = val;
  }
  else if(Serial.available() > 0){
    rpm100 = Serial.read() - '0';
    rpm10 = Serial.read() - '0';
    rpm1 = Serial.read() - '0';
    val_set = (100*rpm100) + (10*rpm10) + rpm1;
  }
  if (val_set == 181){
    val_set = val;
    ser = 1;
  }
  else if (val_set == 182){
    val_set = val;
    ser = 0;
  }
  else if (val_set >= 0 && val_set <= 180){
    ;
  }
  else{
    val_set = val;
  }
  myservo.write(val_set);                  // sets the servo position according to the scaled value
  val_pr=val;
  lcd.setCursor(0, 0);
  lcd.print("Poloha serva: ");
  if(i == 20){
    if(ser == 1){
      Serial.println(val_set);
      Serial.println(volt, 3);
    }
    i = 0;
  }
  i++;
  if(val_set >= 0 && val_set < 10){    
    lcd.setCursor(0, 1);
    lcd.print("00"); 
    lcd.setCursor(2, 1);
    lcd.print(val_set);   
  }
  else if(val_set >= 10 && val_set < 100){ 
    lcd.setCursor(0, 1);
    lcd.print("0");    
    lcd.setCursor(1, 1);
    lcd.print(val_set); 
  }
  else if(val_set >= 100){    
    lcd.setCursor(0, 1);
    lcd.print(val_set);
  }
  if(val_set >= 0 && val_set < 30){
   digitalWrite(LED_BUILTIN, HIGH);
   digitalWrite(LED1_pin, LOW);
   digitalWrite(LED2_pin, LOW);
   digitalWrite(LED3_pin, LOW);
   digitalWrite(LED4_pin, LOW);
   digitalWrite(LED5_pin, LOW);
  }
  else if(val_set >= 30 && val_set < 60){
   digitalWrite(LED_BUILTIN, LOW);
   digitalWrite(LED1_pin, HIGH);
   digitalWrite(LED2_pin, LOW);
   digitalWrite(LED3_pin, LOW);
   digitalWrite(LED4_pin, LOW);
   digitalWrite(LED5_pin, LOW);
  }
  else if(val_set >= 60 && val_set < 90){
   digitalWrite(LED_BUILTIN, LOW);
   digitalWrite(LED1_pin, HIGH);
   digitalWrite(LED2_pin, HIGH);
   digitalWrite(LED3_pin, LOW);
   digitalWrite(LED4_pin, LOW);
   digitalWrite(LED5_pin, LOW);
  }
  else if(val_set >= 90 && val_set < 120){
   digitalWrite(LED_BUILTIN, LOW);
   digitalWrite(LED1_pin, HIGH);
   digitalWrite(LED2_pin, HIGH);
   digitalWrite(LED3_pin, HIGH);
   digitalWrite(LED4_pin, LOW);
   digitalWrite(LED5_pin, LOW);
  }
  else if(val_set >= 120 && val_set < 150){
   digitalWrite(LED_BUILTIN, LOW);
   digitalWrite(LED1_pin, HIGH);
   digitalWrite(LED2_pin, HIGH);
   digitalWrite(LED3_pin, HIGH);
   digitalWrite(LED4_pin, HIGH);
   digitalWrite(LED5_pin, LOW);
  }
  else if(val_set >= 150){
   digitalWrite(LED_BUILTIN, LOW);
   digitalWrite(LED1_pin, HIGH);
   digitalWrite(LED2_pin, HIGH);
   digitalWrite(LED3_pin, HIGH);
   digitalWrite(LED4_pin, HIGH);
   digitalWrite(LED5_pin, HIGH);
  }
  delay(50);                           // waits for the servo to get there
}

