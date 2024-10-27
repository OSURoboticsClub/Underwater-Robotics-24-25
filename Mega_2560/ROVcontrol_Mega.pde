import processing.serial.*;

import net.java.games.input.*;
import org.gamecontrolplus.*;
import org.gamecontrolplus.gui.*;

import cc.arduino.*;
import org.firmata.*;

//declare a lot of variables
ControlDevice cont;
ControlIO control;

Arduino ard0;


int dPad;
GamepadEx lStickYActivity = new GamepadEx(new Button(){boolean inputCode(){return Math.abs(cont.getSlider("lStickY").getValue())>0.05;}});
GamepadEx lStickXActivity = new GamepadEx(new Button(){boolean inputCode(){return Math.abs(cont.getSlider("lStickX").getValue())>0.05;}});
GamepadEx rStickYActivity = new GamepadEx(new Button(){boolean inputCode(){return Math.abs(cont.getSlider("rStickY").getValue())>0.05;}});
GamepadEx rStickXActivity = new GamepadEx(new Button(){boolean inputCode(){return Math.abs(cont.getSlider("rStickX").getValue())>0.05;}});

GamepadEx a = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("a").getValue()!=0;}});
GamepadEx b = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("b").getValue()!=0;}});
GamepadEx x = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("x").getValue()!=0;}});
GamepadEx y = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("y").getValue()!=0;}});

GamepadEx lStickB = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("lStickB").getValue()!=0;}});
GamepadEx rStickB = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("rStickB").getValue()!=0;}});

GamepadEx lT = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("lT").getValue()!=0;}});
GamepadEx rT = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("rT").getValue()!=0;}});
GamepadEx lB = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("lB").getValue()!=0;}});
GamepadEx rB = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("rB").getValue()!=0;}});

GamepadEx dPadLeft  = new GamepadEx(new Button(){boolean inputCode(){return dPad==1 || dPad==8 || dPad==7;}});
GamepadEx dPadRight = new GamepadEx(new Button(){boolean inputCode(){return dPad==3 || dPad==4 || dPad==5;}});
GamepadEx dPadUp    = new GamepadEx(new Button(){boolean inputCode(){return dPad==1 || dPad==2 || dPad==3;}});
GamepadEx dPadDown  = new GamepadEx(new Button(){boolean inputCode(){return dPad==5 || dPad==6 || dPad==7;}});




//Storing controller button values
float foreaft;
float strafe;
float lift;
float turn;
//float liftadj;

//Final motor speed calculations
float mFL;  //Motor Front-Left
float mBL;  //Motor Back-Left
float mFR;  //Motor Front-Right
float mBR;  //Motor Back-Right

//Fore-Aft motor speed command
float mFLf; //Motor Front-Left fore-aft
float mBLf; //Motor Back-Left fore-aft
float mFRf; //Motor Front-Right fore-aft
float mBRf; //Motor Back-Right fore-aft

//Strafe motor speed command
float mFLs; //Motor Front-Left strafe
float mBLs; //Motor Back-Left strafe
float mFRs; //Motor Front-Right strafe
float mBRs; //Motor Back-Right strafe

//Turn motor speed command
float mFLt; //Motor Front-Left turn
float mBLt; //Motor Back-Left turn
float mFRt; //Motor Front-Right turn
float mBRt; //Motor Back-Right turn

//Toggle for whether or not motors are slow
int vslow;//vertical slowdown
int lslow;//lateral slowdown

//Actuator toggles
boolean mainac;
boolean sideac;

//Actuator inputs
boolean mainacpress = false;
boolean sideacpress = false;

//Motion of manipulators
int mainRot;
int mainTip;
int sidepos;

//Motion of camera
int camAng = 90;


/*
The ESCs and the servos take different PWM ranges. In order for this program to work properly,
go into the Firmata file that accompanies this and change the variables: 
  servo180_upper,  servo180_lower            pins: 44, 45, 46
  servo270_upper,  servo270_lower            pins: 2, 3, 4, 5
  esc_upper,  esc_lower                      pins: 6, 7, 8, 9, 10, 11, 12, 13
By modifying these variables, the code will automatically map the 0-180 degree range the 
servo.write() command in Processing uses to the proper PWM values. Not changing these would
make the devices move incorrectly. The code refers to pins on the Arduino Mega 2560 Rev3.

The PWM ranges on the pins are set in the Firmata program, and can be modified to accommodate
more of a type of device or an entirely new device being used.

More Pin Documentation:

  /‾‾/  Front  \‾‾\
 /13/           \12\
/__/             \__\

|‾‾|     ROV     |‾‾|
|11|  Thrusters  |10|
|__|             |__|

\‾‾\             /‾‾/
 \9 \           /8 /
  \__\   Back  /__/
*/
int frontLeftThruster = 13;
int midLeftThruster = 11;
int backLeftThruster = 9;
int frontRightThruster = 12;
int midRightThruster = 10;
int backRightThruster = 8;

int camTip = 4;

PImage clawCl;
PImage clawOp;
PImage iso;
PImage side;
int lIndent = 25;

/*
Unassigned PWM Pins:
  esc: 6
  servo270: 2
  servo180: 44, 45, 46
  Other: 3, 5, 7, 15
*/

void setup () {
  
  //sets the size of the window that pops up when you press run
  size(600,600);
  textSize(25);
  //loads the wireframe images to the variable names
  clawCl = loadImage("RobotWireframeClawClosed.PNG");
  clawOp = loadImage("RobotWireframeClawOpen.PNG");
  iso = loadImage("RobotWireframeIso.PNG");
  side = loadImage("RobotWireframeSide.PNG");
      
  //println(Arduino.list());    //Uncomment this to make the code print the COM ports available, then switch
                                //the information in the initialize line to the correct COM port list location
  
  //Initializes the Arduino
  ard0 = new Arduino(this, Arduino.list()[2], 57600);
  
  //Sets all the PWM pins to output PWM, this way it won't ever need to be changed later. 
  ard0.pinMode(camTip, Arduino.SERVO); 
  ard0.pinMode(backRightThruster, Arduino.SERVO); 
  ard0.pinMode(backLeftThruster, Arduino.SERVO); 
  ard0.pinMode(midRightThruster, Arduino.SERVO); 
  ard0.pinMode(midLeftThruster, Arduino.SERVO); 
  ard0.pinMode(frontRightThruster, Arduino.SERVO); 
  ard0.pinMode(frontLeftThruster, Arduino.SERVO); 
 
  control = ControlIO.getInstance(this);
  
  //finds the controller map file
  cont = control.getMatchedDevice("lgcontrol");
  
  //sets the slowing variables to default to fast mode
  vslow = 0;
  lslow = 0;
  
  //sets the manipulators to default in the not actuated positions
  mainac = false;
  sideac = false;
  
  //Initializes a window for information
  //size(1366, 768); 
  //textSize(14);
  //fill(0, 100, 255);
  
}

//makes an entry in the window
void addEntry(String title, int info, int x, int y) {
  text(title + info, x, y);
}
 
 void addEntry(String title, boolean info, int x, int y) {
  text(title + info, x, y);
}
  
void addEntry(String title, float info, int x, int y) {
  text(title + info, x, y);
}

public void getUserInput() {
  dPad = (int) cont.getHat("d_Pad").getValue();
  GamepadExManager.updateAll();
  
  //toggles the lateral motion slowing
  if(lStickB.isToggled()) {
    lslow = 44;
  } else {
    lslow = 0;
  }
  
  //toggles the vertical motion slowing
  if(rStickB.isToggled()) {
    vslow = 45;
  } else {
    vslow = 0;
  }

  //gets the values of the controller's joystick positions
  
  //deadzone implementation
  if(lStickYActivity.isHeld()) {
    foreaft = cont.getSlider("lStickY").getValue();
  } else {
    foreaft = 0;
  }
  
  mFLf = foreaft;
  mBLf = foreaft;
  mFRf = foreaft;
  mBRf = foreaft;
  
  //deadzone implementation
  if(lStickXActivity.isHeld()) {
    strafe = cont.getSlider("lStickX").getValue();
  } else {
    strafe = 0;
  }
  
  mFLs = -strafe;
  mBLs = strafe;
  mFRs = strafe;
  mBRs = -strafe;
  
  //deadzone implementation
  if(rStickXActivity.isHeld()) {
    turn = cont.getSlider("rStickX").getValue();
  } else {
    turn = 0;
  }
  
  mFLt = -turn;
  mBLt = -turn;
  mFRt = turn;
  mBRt = turn;
  
  //sums the commands to each thruster to determine final direction command
  mFL = (mFLf + mFLs + mFLt);
  mBL = (mBLf + mBLs + mBLt);
  mFR = (mFRf + mFRs + mFRt);
  mBR = (mBRf + mBRs + mBRt);
  
  //lowers the commands to the correct range
  if (mFL > 1) {
    mFL = 1;
  }  else if (mFL < -1) {
    mFL = -1;
  }  
  
  if (mBL > 1) {
    mBL = 1;
  }  else if (mBL < -1) {
    mBL = -1;
  }  
  
  if (mFR > 1) {
    mFR = 1;
  }  else if (mFR < -1) {
    mFR = -1;
  }  
  
  if (mBR > 1) {
    mBR = 1;
  }  else if (mBR < -1) {
    mBR = -1;
  }  
  
  //maps the commands to servo angle values
  //detects if the lateral slow is toggled on or off, cuts speed 50%
  mFL = map(mFL, -1, 1, 0 + lslow - lslow/45, 179 - lslow);
  mBL = map(mBL, -1, 1, 0 + lslow - lslow/45, 179 - lslow);
  mFR = map(mFR, -1, 1, 0 + lslow - lslow/45, 179 - lslow);
  mBR = map(mBR, -1, 1, 0 + lslow - lslow/45, 179 - lslow);

  //checks to see if the activity level is high enough, if so it sets the lift motor power to the appropriate value and otherwise sets it to 0 power
  if (rStickYActivity.isHeld()) {  
    //detects if vertical slow is toggled on or off, cuts speed 50%
    lift = map(cont.getSlider("rStickY").getValue(),  -1, 1, 0 + vslow - vslow/45, 179 - vslow);
  }  else {
    lift = map(0,  -1, 1, 0 + vslow - vslow/45, 179 - vslow);
  }  
  
  //Uses the dpad to get PH camera motion commands
  if (dPadUp.isHeld()) {
    if (camAng < 179) {
      camAng += 1;
    }
  }
  if (dPadDown.isHeld()) {
    if (camAng > 0) {
      camAng -= 1;
    }
  }
  if (dPadLeft.isPressed()) {
    camAng = 90;
  }
}

void draw() {
 
  getUserInput();
  
  //Writes the vertical motion command to the middle thrusters
  ard0.servoWrite(midRightThruster, (int)lift);
  ard0.servoWrite(midLeftThruster, (int)lift);

  //Writes the lateral motion command to the corner thrusters
  ard0.servoWrite(backLeftThruster, (int)mBL);
  ard0.servoWrite(frontRightThruster, (int)mFR);
  ard0.servoWrite(frontLeftThruster, (int)mFL);
  ard0.servoWrite(backRightThruster, (int)mBR);
  
  //Writes the camera angle
  ard0.servoWrite(camTip, (int)camAng);
  
  //Populates the window with control information
    //color of the backround in rgb
  background(100, 200, 255);
  addEntry("Left stick Y values: ", foreaft, lIndent, 50);
  addEntry("Left stick X values: ", strafe, lIndent, 75);
  addEntry("Camera Angle: ", camAng, lIndent, 100);
  //addEntry("Thruster _ Value: ", , lIndent, 125);
  //addEntry("Gyroscope: ", , lIndent, 100);
  
  //adds the wireframe images and applies them when applicable
  //if(int(time%4) == 0){
  //    image(side, 50, 175);
  //  }else if(int(time%5) == 0) {
  //    image(clawOp,50, 175);
  //  }else if(int(time%6) == 0){
  //    image(clawCl, 50, 175);
  //  }else{
  //    image(iso,50,175);
  //  }
    
  //background(141, 76, 34);
  ////println("Hello world!");
  //print(camAng);
  //print("   ");
  //print(lStickYActivity.isHeld());
  //print("   ");
  //print(rStickXActivity.isHeld());
  //print("   ");
  //print(rStickYActivity.isHeld());
  //print("   ");
  //println(millis());
   //<>//
} 
