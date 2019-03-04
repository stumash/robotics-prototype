#ifndef STEPPERMOTOR_H
#define STEPPERMOTOR_H

#include <Arduino.h>
#include "PinSetup.h"
#include "RobotMotor.h"

#define MIN_STEP_INTERVAL 3000
#define MAX_STEP_INTERVAL 50000

// multipliers for how bit of an angle the stepper moves each step
#define FULL_STEP 1
#define HALF_STEP 0.5
#define QUARTER_STEP 0.25
#define EIGHTH_STEP 0.125
#define SIXTEENTH_STEP 0.0625

class StepperMotor: public RobotMotor {
  public:
    static int numStepperMotors;
    float stepResolution; // the smallest angle increment attainable by the shaft once the stepping mode is known
    
    StepperMotor(int enablePin, int dirPin, int stepPin, float stepRes, float stepMode, float gearRatio);
    
    /* movement helper functions */
    bool calcNumSteps(float angle); // calculates how many steps to take to get to the desired position, assuming no slipping
    bool calcCurrentAngle(void);
    void enablePower(void);
    void disablePower(void);
    /* movement functions */
    void stopRotation(void);
    void singleStep();
    void setVelocity(int motorDir, float motorSpeed);
    void goToCommandedAngle(void);
    void budge(void);

    // stuff for open loop control
    float openLoopError; // public variable for open loop control
    int openLoopSpeed; // angular speed (degrees/second)
    float startAngle; // used in angle esimation
    int numSteps; // how many steps to take for stepper to reach desired position
    volatile int stepCount; // how many steps the stepper has taken since it started moving
    volatile int nextInterval; // how long to wait until the next step

  private:
    int enablePin, directionPin, stepPin;
    float fullStepResolution, steppingMode;
};

int StepperMotor::numStepperMotors = 0; // must initialize variable outside of class
StepperMotor::StepperMotor(int enablePin, int dirPin, int stepPin, float stepRes, float stepMode, float gearRatio):// if no encoder
  enablePin(enablePin), directionPin(dirPin), stepPin(stepPin), fullStepResolution(stepRes), steppingMode(stepMode)
{
  numStepperMotors++;
  // variables declared in RobotMotor require the this-> operator
  this -> gearRatio = gearRatio;
  this -> gearRatioReciprocal = 1 / gearRatio; // preemptively reduce floating point calculation time
  this -> motorType = STEPPER_MOTOR;
  hasEncoder = false; // by default the motor has no encoder
  stepResolution = fullStepResolution * steppingMode;
  openLoopSpeed = 0; // no speed by default;
}

bool StepperMotor::calcNumSteps(float angle) {
  // if the error is big enough to justify movement
  if (fabs(angle) > pidController.getJointAngleTolerance()) {
    // here we have to multiply by the gear ratio to find the angle actually traversed by the motor shaft
    numSteps = fabs(angle) * gearRatio / stepResolution; // calculate the number of steps to take
    return true;
  }
  else {
    return false;
  }
}

bool StepperMotor::calcCurrentAngle(void) {
  if (isBudging) {
    imaginedAngle = startAngle + (float)rotationDirection * (float)stepCount * stepResolution * gearRatioReciprocal;
    return true;
  }
  else if (isOpenLoop) {
    if (movementDone) {
      // imaginedAngle hasn't changed since motor hasn't moved and encoder isn't working
    }
    else if (stepCount < numSteps) {
      // if the motor is moving, calculate the angle based on how long it's been turning for
      imaginedAngle = startAngle + (desiredAngle - startAngle) * ((float)stepCount / (float)numSteps);
    }
    return true;
  }
  else if (hasEncoder) {
    currentAngle = (float) encoderCount * 360.0 * gearRatioReciprocal * encoderResolutionReciprocal;
    imaginedAngle = currentAngle;
    return true;
  }
  else {
    return false;
  }
}

void StepperMotor::enablePower(void) {
  digitalWriteFast(enablePin, LOW);
}

void StepperMotor::disablePower(void) {
  digitalWriteFast(enablePin, HIGH);
}

void StepperMotor::stopRotation(void) {
  disablePower();
  movementDone = true;
  isBudging = false;
}

void StepperMotor::singleStep() {
  digitalWriteFast(stepPin, HIGH);
  digitalWriteFast(stepPin, LOW);
}

void StepperMotor::setVelocity(int motorDir, float motorSpeed) {
  static int oldDir = CLOCKWISE;
  if (!isOpenLoop) {
    motorSpeed = fabs(motorSpeed);
  }
  // makes sure the speed is within the limits set in the pid during setup
  if (motorSpeed * motorDir > pidController.getMaxOutputValue()) {
    motorSpeed = pidController.getMaxOutputValue();
  }
  if (motorSpeed * motorDir < pidController.getMinOutputValue()) {
    motorSpeed = pidController.getMinOutputValue();
  }
  if (motorDir != oldDir) {
  switch (motorDir) {
    case CLOCKWISE:
      digitalWriteFast(directionPin, LOW);
      break;
    case COUNTER_CLOCKWISE:
      digitalWriteFast(directionPin, HIGH);
      break;
  }
  oldDir = motorDir;
  //Serial.println("dir change");
  }
  singleStep();
  // slowest is STEP_INTERVAL1, fastest is STEP_INTERVAL4
  // the following equation converts from range 0-100 to range stepinterval1-4
  nextInterval = motorSpeed * ((MIN_STEP_INTERVAL - MAX_STEP_INTERVAL) / 100) + MAX_STEP_INTERVAL;
}

void StepperMotor::goToCommandedAngle() {
  if (isOpenLoop) {
    calcCurrentAngle();
    startAngle = getImaginedAngle();
    openLoopError = getDesiredAngle() - getImaginedAngle(); // find the angle difference
    calcDirection(openLoopError);
    // calculates how many steps to take to get to the desired position, assuming no slipping
    if (calcNumSteps(openLoopError)) { // returns false if the open loop error is too small
      stepCount = 0;
      enablePower(); // give power to the stepper finally
      movementDone = false;
#if defined(DEVEL_MODE_1) || defined(DEVEL_MODE_2)
      UART_PORT.print("$S,Success: motor ");
      //UART_PORT.print(3);
      UART_PORT.print(" to turn ");
      UART_PORT.print(numSteps);
      UART_PORT.println(" steps");
#endif
    }
    else {
#if defined(DEVEL_MODE_1) || defined(DEVEL_MODE_2)
      UART_PORT.println("$E,Error: requested angle is too close to current angle. Motor not changing course.");
#endif
    }
  }
  else if (!isOpenLoop) {
    enablePower();
    movementDone = false;
  }
}

void StepperMotor::budge(void) {
  isBudging = true;
  movementDone = false;
  stepCount = 0;
  sinceBudgeCommand = 0;
  enablePower(); // give power to the stepper finally
  if (isOpenLoop) {
    startAngle = getImaginedAngle();
  }
  else if (!isOpenLoop) {
    startAngle = getCurrentAngle();
  }
}

#endif
