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

//Storing controller button values
float foreaft;
float strafe;
float lift;
float liftadj;
float turn;

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
boolean vslow;
boolean lslow;

//Buttons inputs for slowing
boolean lmspress = false;
boolean vmspress = false;

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
int camang = 90;


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
/*
Unassigned PWM Pins:
  esc: 6
  servo270: 2
  servo180: 44, 45, 46
  Other: 3, 5, 7, 15
*/

void setup () {
  
  //println(Arduino.list());    //Uncomment this to make the code print the COM ports available, then switch
                                //the information in the initialize line to the correct COM port list location
  
  //Initializes the Arduino
  ard0 = new Arduino(this, Arduino.list()[2], 57600);
  
  //Sets all the PWM pins to output PWM, this way it won't ever need to be changed later. 
  ard0.pinMode(4, Arduino.SERVO); 
  ard0.pinMode(8, Arduino.SERVO); 
  ard0.pinMode(9, Arduino.SERVO); 
  ard0.pinMode(10, Arduino.SERVO); 
  ard0.pinMode(11, Arduino.SERVO); 
  ard0.pinMode(12, Arduino.SERVO); 
  ard0.pinMode(13, Arduino.SERVO); 
 
  control = ControlIO.getInstance(this);
  
  //finds the controller map file
  cont = control.getMatchedDevice("rovcontrol");
  
  //sets the slowing variables to default to fast mode
  vslow = false;
  lslow = false;
  
  //sets the manipulators to default in the not actuated positions
  mainac = false;
  sideac = false;
  
  //Initializes a window for information
  //size(1366, 768); 
  //textSize(14);
  //fill(0, 100, 255);
  
}

public void getUserInput() {
  
  //toggles the lateral motion slowing
  if (lmspress == false) {
    if (cont.getButton("lslow").getValue() != 0) {
      lslow = !lslow;
      lmspress = true;
    }
  } else if (cont.getButton("lslow").getValue() == 0) {
    lmspress = false;
  }
  
  //toggles the vertical motion slowing
  if (vmspress == false) {
    if (cont.getButton("vslow").getValue() != 0) {
      vslow = !vslow;
      vmspress = true;
    }
  } else if (cont.getButton("vslow").getValue() == 0) {
    vmspress = false;
  }

  //gets the values of the controller's joystick positions
  foreaft = cont.getSlider("foreaft").getValue();
  mFLf = foreaft;
  mBLf = foreaft;
  mFRf = foreaft;
  mBRf = foreaft;
  strafe = cont.getSlider("strafe").getValue();
  mFLs = -strafe;
  mBLs = strafe;
  mFRs = strafe;
  mBRs = -strafe;
  turn = cont.getSlider("turn").getValue();
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
  if (lslow == true) {
    mFL = map(mFL, -1, 1, 44, 134);
    mBL = map(mBL, -1, 1, 44, 134);
    mFR = map(mFR, -1, 1, 44, 134);
    mBR = map(mBR, -1, 1, 44, 134);
  } else {  
    mFL = map(mFL, -1, 1, 0, 179);
    mBL = map(mBL, -1, 1, 0, 179);
    mFR = map(mFR, -1, 1, 0, 179);
    mBR = map(mBR, -1, 1, 0, 179);
  }
  
  //detects if vertical slow is toggled on or off, cuts speed 50%
  if (vslow == true) {
    lift = map(cont.getSlider("lift").getValue(),  -1, 1, 44, 134);
  }  else {
    lift = map(cont.getSlider("lift").getValue(),  -1, 1, 0, 179); 
  }  
  
  //Uses the dpad to get PH camera motion commands
  if (cont.getHat("hat").getValue() == 2) {
    if (camang < 179) {
      camang += 1;
    }
  }
  if (cont.getHat("hat").getValue() == 6) {
    if (camang > 0) {
      camang -= 1;
    }
  }  
  if (cont.getHat("hat").getValue() == 8) {
    camang = 90;
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
  ard0.servoWrite(camTip, (int)camang);
  
  
  //Populates the window with control information
  //background(141, 76, 34);


}  
