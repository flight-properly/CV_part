import cv2
import mediapipe as mp
import time

#define
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

cap = cv2.VideoCapture(0)

swt=0
init_width=0
init_height_right=0
init_height_left=0

with mp_hands.Hands(

    model_complexity=0,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7) as hands:

  while cap.isOpened():
    success, image = cap.read()
    if not success:
      print("Camera failure")
      continue

    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image)

    image_height, image_width, _ = image.shape
    
    
    try:
      if len(results.multi_hand_landmarks)==2:

        #list import
        if results.multi_hand_landmarks[0].landmark[9].x * image_width < results.multi_hand_landmarks[1].landmark[9].x * image_width :
          right_hand=results.multi_hand_landmarks[0]
          left_hand=results.multi_hand_landmarks[1]
        else :
          right_hand=results.multi_hand_landmarks[1]
          left_hand=results.multi_hand_landmarks[0]

        #define
        right_5_y = right_hand.landmark[5].y * image_height
        left_5_y = left_hand.landmark[5].y * image_height

        right_17_y = right_hand.landmark[17].y * image_height
        left_17_y = left_hand.landmark[17].y * image_height
        
        #save initial width 
        if (swt==0): 
          init_width=((right_17_y - right_5_y) + (left_17_y - left_5_y))/2
          init_height_right=right_5_y
          init_height_left=left_5_y
          swt=1

        #pitch 
        depth_avg = round(((((right_17_y - right_5_y) + (left_17_y - left_5_y))/2)/init_width-1)*-2,8)
        if (depth_avg>1) : depth_avg=1.0
        elif (depth_avg<-1) : depth_avg=-1.0

        #roll&yaw
        if (left_5_y-right_5_y > 20.0 or left_5_y-right_5_y < -20.0):
          real_height = (left_5_y-right_5_y / 400 - 200) / -200
        else: real_height=0.0
        if (real_height>1) : real_height=1.0
        elif (real_height<-1) : real_height=-1.0

        #output
        print(depth_avg, real_height)
        
    except:
      print()
