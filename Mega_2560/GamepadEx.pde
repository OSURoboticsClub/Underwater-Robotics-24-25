public class GamepadEx {
   //declares the internal variables
   private boolean gamepadInput;
   private boolean wasPressed;
   private boolean isToggled;
   private boolean pressedOnce;
   
   //basic constructor, initializes variables
   public GamepadEx() {
     wasPressed = false;
     isToggled = false;
   }
   
   //Call this function once per object in your main loop and pass it the value from the gamepad
   //updates variables based on the given input
   public void updateButton(boolean gamepadInput) {
     this.gamepadInput = gamepadInput;
     if(gamepadInput && !wasPressed) {
       wasPressed = true;
       pressedOnce = true;
       isToggled = !isToggled;
     } else if(!gamepadInput && wasPressed) {
       wasPressed = false;
       pressedOnce = false;
     }
   }
   
   //Use if you need something to occur for the duration that a button is held
   //returns the raw button input. 
   public boolean isHeld() {
     return gamepadInput;
   }
   
   //Use if you want something to happen once only when a button is pressed.
   //returns true the first time it is called while a button is pressed. Is false on subsequent presses while still being held. 
   public boolean isPressed() {
     boolean wasPressedOnce = pressedOnce;
     pressedOnce = false;
     return wasPressedOnce;
   }
   
   //Use if you want the state of something to change upon a button press and remain changed afterwards
   //returns the value of the toggle. The toggle changes once every time the button is pressed. 
   public boolean isToggled() {
     return isToggled;
   } 
   
   //Use if you want to set a starting value for the toggle
   //sets the toggle to the given value
   public void setToggle(boolean newToggleValue) {
     this.isToggled = newToggleValue;
   }
}
