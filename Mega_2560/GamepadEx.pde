public class GamepadEx {
   private boolean gamepadInput;
   private boolean wasPressed;
   private boolean isToggled;
   
   public GamepadEx() {
     wasPressed = false;
     isToggled = false;
   }
   
   public void updateButton(boolean  gamepadInput) {
     this.gamepadInput = gamepadInput;
     if(gamepadInput && !wasPressed) {
       wasPressed = true;
       isToggled = !isToggled;
     } else if(!gamepadInput && wasPressed) {
       wasPressed = false;
     }
   }
   
   public boolean isHeld() {
     return gamepadInput;
   }
   
   public boolean isPressed() {
     return wasPressed;
   }
   
   public boolean isToggled() {
     return isToggled;
   } 
   
   public void setToggle(boolean newToggleValue) {
     this.isToggled = newToggleValue;
   }
}
