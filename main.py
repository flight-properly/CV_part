import cv2
import mediapipe as mp
import json
import socket

HOST = "127.0.0.1"
PORT = 12325
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
print("Waiting for client to connect...")
server_socket.listen()

client_socket, addr = server_socket.accept()

print("Connected from", addr)

# define
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

cap = cv2.VideoCapture(0)

swt = 0
throttle = 0
init_width = 0
init_height_right = 0
init_height_left = 0

width = 1920
height = 1080
diff = width / 1920

with mp_hands.Hands(model_complexity=0, min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Camera failure")
            continue

        image.flags.writeable = True

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (width, height))
        results = hands.process(image)

        image_height, image_width, _ = image.shape

        try:
            if len(results.multi_hand_landmarks) == 2:
                # list import
                if results.multi_hand_landmarks[0].landmark[9].x * image_width < results.multi_hand_landmarks[1].landmark[9].x * image_width:
                    right_hand = results.multi_hand_landmarks[0]
                    left_hand = results.multi_hand_landmarks[1]
                else:
                    right_hand = results.multi_hand_landmarks[1]
                    left_hand = results.multi_hand_landmarks[0]

                # define
                right_5_x = right_hand.landmark[5].x * image_width
                left_5_x = left_hand.landmark[5].x * image_width
                right_5_y = right_hand.landmark[5].y * image_height
                left_5_y = left_hand.landmark[5].y * image_height

                right_17_x = right_hand.landmark[17].x * image_width
                left_17_x = left_hand.landmark[17].x * image_width
                right_17_y = right_hand.landmark[17].y * image_height
                left_17_y = left_hand.landmark[17].y * image_height

                right_6_x = right_hand.landmark[6].x * image_width
                left_6_x = left_hand.landmark[6].x * image_width
                right_6_y = right_hand.landmark[6].y * image_height
                left_6_y = left_hand.landmark[6].y * image_height

                right_4_x = right_hand.landmark[4].x * image_width
                left_4_x = left_hand.landmark[4].x * image_width
                right_4_y = right_hand.landmark[4].y * image_height
                left_4_y = left_hand.landmark[4].y * image_height

                right_9_y = right_hand.landmark[9].y * image_height
                left_9_y = left_hand.landmark[9].y * image_height

                # save initial value
                if (swt==0): 
                  init_width=(((left_5_x-left_17_x)**2+(left_5_y-left_17_y)**2)**0.5+((right_5_x-right_17_x)**2+(right_5_y-right_17_y)**2)**0.5)/2
                  init_height=(right_5_y +left_5_y)/2
                  init_throttle=(((left_4_x-left_6_x)**2+(left_4_y-left_6_y)**2)**0.5+((right_4_x-right_6_x)**2+(right_4_y-right_6_y)**2)**0.5)/2
                  swt=1

                #pitch 
                depth_avg = ((((left_5_x-left_17_x)**2+(left_5_y-left_17_y)**2)**0.5+((right_5_x-right_17_x)**2+(right_5_y-right_17_y)**2)**0.5)/2)/init_width-0.4
                if (depth_avg>1) : depth_avg=1.0
                elif (depth_avg<0) : depth_avg=0.0

                #roll&yaw
                rollyaw_left=init_height-left_5_y
                rollyaw_right=init_height-right_5_y

                if (rollyaw_left>60.0 or rollyaw_right<-60.0):#right+
                  real_height=(rollyaw_left+(rollyaw_right*-1))/init_height

                elif (rollyaw_left<-60.0 or rollyaw_right>60.0):#left-
                  real_height=(rollyaw_right+(rollyaw_left*-1))/init_height
                  real_height*=-1

                if (real_height>1) : real_height=1.0
                elif (real_height<-1) : real_height=-1.0

                #throttle
                throttle_left=((left_4_x-left_6_x)**2+(left_4_y-left_6_y)**2)**0.5
                throttle_right=((right_4_x-right_6_x)**2+(right_4_y-right_6_y)**2)**0.5
                if (depth_avg<0.5 and depth_avg>-0.5 and (init_throttle/throttle_right+init_throttle/throttle_right)/2 >1.5):
                    throttle = 1
                else:
                    throttle = 0

                body = json.dumps(
                    {
                        "pitch": depth_avg,
                        "roll": -real_height,
                        "yaw": real_height,
                        "throttle": throttle,
                    }
                )

                # display result
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(
                            image,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS,
                            mp_drawing_styles.get_default_hand_landmarks_style(),
                            mp_drawing_styles.get_default_hand_connections_style(),
                        )

                print(json.loads(body))
                client_socket.sendall(body.encode())
        except:
            print()
        cv2.imshow("MediaPipe Hands", cv2.flip(image, 1))
        if cv2.waitKey(5) & 0xFF == 27:
            break
cap.release()
cv2.destroyAllWindows()
client_socket.close()
server_socket.close()
