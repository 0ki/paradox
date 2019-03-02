#include <M5Stack.h>

// (C) Kirils Solovjovs

// Paradox COMBUS code interception program for M5Stack
// NB! Signals on COMBUS are way higher than 3.3V! Take care to use a voltage divider or other suitable technique!

#define pin_clock 2 //yellow
#define pin_data 5 //green

#define MASTER 1
#define SLAVE 0

int clock_previous=0;
unsigned long int timer=0;

int bit_cnt[2]={0,0};
int byte_cnt[2]={0,0};
int hex_nibble_cnt[2]={0,0};

byte incoming[2][64];
char incoming_hex[2][200]; // 64x3
int counts[1000];
byte clock_current;
String code;
String lastokcode="XXXX";
int code_ok=9;
int distance=0;
int clearcounter=0;

char hexmap[0x10]={
	'0','1','2','3','4','5','6','7','8','9',
	'A','B','C','D','E','F'};


void storeBit(byte source,byte bitvalue){
  incoming[source][byte_cnt[source]]<<=1;
  incoming[source][byte_cnt[source]]+=bitvalue;

  if(++bit_cnt[source]%4 == 0) // two nibbles stored
    incoming_hex[source][hex_nibble_cnt[source]++]=hexmap[incoming[source][byte_cnt[source]] & 0xf];

  if(bit_cnt[source] == 8)
    incoming_hex[source][hex_nibble_cnt[source]++]=' ';

  if(bit_cnt[source]==8){
    byte_cnt[source]++;
    if(byte_cnt[source]>=64) //crude overflow protection
      byte_cnt[source]=0;
      
    bit_cnt[source]=0;
  }  

}


void setup() { 
  M5.begin();
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.setTextSize(5);
  pinMode(pin_clock, INPUT);
  pinMode(pin_data, INPUT);
  Serial.begin(115200);
}


void loop() {
    clock_current=digitalRead(pin_clock);
    if (clock_current!=clock_previous){ //new bit being sent on data line
      delayMicroseconds(50); //add tolerance
      timer=micros();
      if(clock_previous==HIGH)
        storeBit(MASTER,digitalRead(pin_data) & 1);
      else
        storeBit(SLAVE,1 - digitalRead(pin_data) & 1);
  
      clock_previous=clock_current;
    } else if(abs(micros()-timer)>2000 && byte_cnt[MASTER]){ // no clock change for some time and there is data collected
      if(distance>-2)
        distance--;

      if (clearcounter > 0){
        clearcounter--;
        if (clearcounter == 0)
          M5.Lcd.fillScreen(BLACK);
      }

      M5.update();
      if (M5.BtnA.wasReleased()) {
        distance = -1;
      } else if (M5.BtnB.wasReleased()) {
        // nothing
      } else if (M5.BtnC.wasReleased()) {
          clearcounter=0;
          M5.Lcd.fillScreen(GREEN);
          M5.Lcd.setTextColor(BLACK); 
          M5.Lcd.drawCentreString(lastokcode,50,60,4);
      }
        
      for(int i=SLAVE;i<=MASTER;i++){ // ;)
        incoming_hex[i][hex_nibble_cnt[i]++]='\0';
        if (i==SLAVE && incoming[i][0]==0x00 && incoming[i][1]==0x02 && incoming[i][2]==0x20 && byte_cnt[i] > 14 ){
          code = String(incoming_hex[i]).substring(21,33);
          code = code.substring(0,code.indexOf("0"));
          code.replace("A","0");
          code.replace(" ","");
          distance=5;
          code_ok=9;
        }
        
        if (distance>=0 && i==MASTER && ( incoming[i][0]==0x40 || incoming[i][0]==0x80 ) && byte_cnt[i] > 14 ){
           if(incoming[i][3] & 0x80 and not (incoming[i][0]==0x80) )
            code_ok=0;
           else
            code_ok=1;
        }
        if (distance == -1){
          M5.Lcd.fillScreen(BLACK);
          if (code_ok==0)
            M5.Lcd.setTextColor(RED);
          else if (code_ok==1){
            M5.Lcd.setTextColor(GREEN);
            lastokcode = code;
          } else
            M5.Lcd.setTextColor(BLUE);

          
          M5.Lcd.drawCentreString(code,50,60,4);
          clearcounter=20;
        }

        
        Serial.println(incoming_hex[i]);
        bit_cnt[i]=byte_cnt[i]=hex_nibble_cnt[i]=0; // reset counters between frames
      }
  
  
    }
}
