
// (C) Kirils Solovjovs

// Paradox COMBUS signal level processing program
// Should work with any arduino

// NB! Signals on COMBUS are way higher than 3.3V! Take care to use a voltage divider or other suitable technique!


#define pin_clock 8 //yellow
#define pin_data 12 //green

#define MASTER 1
#define SLAVE 0

int clock_previous=0;
unsigned long int timer=0;

int bit_cnt[2]={0,0};
int byte_cnt[2]={0,0};
int hex_nibble_cnt[2]={0,0};

byte incoming[2][64];
char incoming_hex[2][200]; // 64x3

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
	pinMode(pin_clock, INPUT);
	pinMode(pin_data, INPUT);
	Serial.begin(115200);
}

void loop() {
	byte clock_current=digitalRead(pin_clock);

	if (clock_current!=clock_previous){ //new bit being sent on data line
		delayMicroseconds(50); //add tolerance
		timer=micros();

		if(clock_previous==HIGH)
			storeBit(MASTER,digitalRead(pin_data) & 1);
		else
			storeBit(SLAVE,1 - digitalRead(pin_data) & 1);

		clock_previous=clock_current;
		
	} else if(abs(micros()-timer)>2000 && byte_cnt[MASTER]){ // no clock change for some time and there is data collected

    // do pre-processing here if needed
    
    for(int i=SLAVE;i<=MASTER;i++){ // ;)
			incoming_hex[i][hex_nibble_cnt[i]++]='\0';
			Serial.println(incoming_hex[i]);

			bit_cnt[i]=byte_cnt[i]=hex_nibble_cnt[i]=0; // reset counters between frames
		}


	}

}
