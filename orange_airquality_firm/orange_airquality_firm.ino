#define  MSG_LEN  200
#define  HIST_LEN  600

unsigned long last_airsample = 0;
unsigned long last_airmsg = 0;
long sum;
int air_avg = 0;
int val;
int cksum = 0;
unsigned long histidx = 0;
char msg[MSG_LEN];
int history[HIST_LEN];

void setup() {
  Serial.begin(9600);
  Serial.println("$PUBX,41,1,0000,0003,9600,0*17");
  pinMode(A5, INPUT);
  //Serial.println("Helloworld");
}

void loop() {
  if (Serial.available()) {
    readLine(1);
    //Serial.write(Serial.read());
  } 
  if (millis() > last_airsample + 10) {
    val = analogRead(A5);
    history[histidx++%HIST_LEN] = val;
    last_airsample = millis();
  }
  if (millis() > last_airmsg + 1000) {
    sum = 0;
    for (int i=0;i<HIST_LEN;i++) {
      sum += history[i];
    }
    if (histidx < HIST_LEN) {
      air_avg = sum/histidx;
    } else {
      air_avg = sum/HIST_LEN;
    }
    Serial.println(val);
    memset(msg, '\0', MSG_LEN);
    sprintf(msg, "$GPOSD,%u*", air_avg);
    sendMsg(msg);
    last_airmsg = millis();
  }
}

void readLine(char echo) {
  int c = '\0';
  int idx = 0;
  
  memset(msg, '\0', MSG_LEN);
  while (c != '\n') {
    c = Serial.read();
    if (c > 31) {
      msg[idx] = c;
    }
    if (echo && c > 0) {
      Serial.write(c);
    }
  }
}

void sendMsg(char * pkt) {
  int len;
  
  cksum = 0;
  len = strlen(pkt);
  for (int i=1;i<len-1;i++){
    cksum ^= pkt[i];
  }
  sprintf(pkt+len, "%02X", cksum);
  Serial.println(msg);
}
