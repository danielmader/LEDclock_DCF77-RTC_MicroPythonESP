# dcf77.py
# https://de.wikipedia.org/wiki/DCF77
from machine import Pin, Timer
from time import ticks_us, ticks_diff, sleep, sleep_ms
from array import array
from sys import exit

class DCF77():

    def __init__(self,dcf=18,sec=4,wait=19):
        self.seconds =array("B",0 for _ in range(60))
        self.start = 0
        self.ende = 0
        self.delay = 0
        self.counter = 0
        self.triggered = False
        self.flash=False
        self.sec59=False
        self.secLed=Pin(sec,Pin.OUT, value=0)
        self.waitLed=Pin(wait,Pin.OUT,value=0)
        self.dcf=Pin(dcf, Pin.IN)
        self.dcf.irq(handler = None, trigger=Pin.IRQ_RISING)
        print("DCF77 initialisiert")


    def blink(self,puls,pause,led):
        led.on()
        sleep_ms(puls)
        led.off()
        sleep_ms(pause)

    def stopwatch(self,pin):
        if pin.value()==1:
            self.dcf.irq(handler = None)
            self.start=ticks_us()
            self.secLed.on()
            sleep_ms(10)
            self.dcf.irq(handler = self.stopwatch, trigger=Pin.IRQ_FALLING)
        else:
            self.dcf.irq(handler = None)
            self.ende=ticks_us()
            self.delay=ticks_diff(self.ende,self.start)
            sleep_ms(10)
            self.dcf.irq(handler = self.stopwatch, trigger=Pin.IRQ_RISING)
            self.triggered=True
            self.secLed.off()
 
    def wait(self,pin):
        self.start=ticks_us()
        self.triggered=True
        self.flash=True

    def waitForStart(self):
        self.dcf.irq(handler = None)
        self.dcf.irq(handler = self.wait, trigger=Pin.IRQ_FALLING)
        print("Warte auf Minutenstart")
        self.flash=False
        while 1:
            if self.triggered and ticks_diff(ticks_us(),self.start) > 1200000:
                self.dcf.irq(handler = None)
                self.counter = 0
                self.dcf.irq(handler = self.stopwatch, trigger=Pin.IRQ_RISING)
                break
            if self.triggered and ticks_diff(ticks_us(),self.start) < 300000 and self.flash:
                self.dcf.irq(handler = None)
                self.flash = False
                sleep_ms(50)
                if self.dcf.value()==0:
                    self.blink(20,1,self.waitLed)
                self.dcf.irq(handler = self.wait, trigger=Pin.IRQ_FALLING)
    
    def checkParity(self):
        minuten=0
        for i in range(21,29):
            minuten += self.seconds[i]
        minuten %= 2
        stunden=0
        for i in range(29,36):
            stunden += self.seconds[i]
        stunden %= 2
        datum = 0
        for i in range(36,59):
            datum += self.seconds[i]
            datum %= 2
        return (minuten,stunden,datum)
    
    def calcDateTime(self):
        def bcd2dec(c,n,cc,m): 
            x,xx=0,0
            for i in range(n):
                x += self.seconds[c+i]*(2**i)
            for i in range(m):
                xx += self.seconds[cc+i]*(2**i)
            x=x+xx*10
            return x
        
        m=bcd2dec(21,4,25,3)
        h=bcd2dec(29,4,33,2)
        d=bcd2dec(36,4,40,2)
        dow=0
        for i in range(3):
            dow += self.seconds[42+i]*(2**i)
        M=bcd2dec(45,4,49,1)
        y=bcd2dec(50,4,54,4)
        return y,M,d,dow,h,m

    def synchronize(self):
        self.waitForStart()
        self.dcf.irq(handler = self.stopwatch, trigger=Pin.IRQ_RISING)

        while 1:
            if self.triggered and self.delay > 20000:
                self.triggered=False
                code=(((self.delay//1000) + 20 ) // 100) - 1
                print(self.counter,code)
                self.seconds[self.counter]=code
                self.counter =(self.counter +1) % 59
                if self.counter == 0:
                    sleep(0.95)
                    self.sec59=True
        #         if counter == 0: break
            if self.counter == 0 and self.dcf.value() == 0 and self.sec59:
                self.sec59=False
                parity = self.checkParity()
                if parity == (0,0,0):
                    y,M,d,dow,h,m=self.calcDateTime()
                    dt=(y+2000,M,d,dow,h,m,0)
                    print(dt)
                    # rtc-Zählung startet ,mit 0 am Montag, Sonntag=6
                    # rtc berechnet den Wochentag nach dem Datum
                    # dcf startet mit 1 am Montag, Sonntag=7
                    self.dcf.irq(handler = None)
                    return dt
                else:
                    print("Parity-Error:",parity)
                    self.dcf.irq(handler = None)
                    sleep(2)
                    self.waitForStart()
                    

if __name__ == "__main__":
    from machine import Pin,SoftI2C
    from ds3231 import DS3231
    from machine import Pin,SoftI2C
    i2c=SoftI2C(scl=Pin(22),sda=Pin(23),freq=100000)
    rtc=DS3231(i2c)
    dc=DCF77()
    dt=dc.synchronize()
    rtc.DateTime(dt)

# array('B', [0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0])