import glob
import cv2
import mediapipe as mp
import pandas as pd
import base64
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA

image_path = 'handDetection/model/original_images/'
IMAGE_FILES = glob.glob(image_path+'*.jpg')


mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=2,
    min_detection_confidence=0.5)


base64_list = []
img_list = []

angle_data = pd.DataFrame(columns=['angle'+str(x) for x in range(0,18,1)])


# image base64 encode (이미지를  base64 형식으로 인코딩)
for img_name in IMAGE_FILES:
    with open(img_name,'rb') as img:
        base64_string = base64.b64encode(img.read())
        base64_list.append(base64_string)

# image decode (서버에서 base64 형식으로 packet이 오면, 형태를 이미지화 해줌)
for img64 in base64_list:
    decoded = np.asarray(bytearray(base64.b64decode(img64)), dtype=np.uint8)
    img = cv2.imdecode(decoded, cv2.IMREAD_COLOR)
    img_list.append(img)

# =======================================================================================
# Custom Unsupervised Learning Algorithm
# =======================================================================================

def fit_predict(df, limit=1):
    distance = pd.DataFrame(columns=['x','y', 'value'])
    predict = pd.Series(data=[0 for x in range(0,len(df),1)], index=df.index)
    count=1
    for i in range(0,len(df.index),1):
        for j in range(i+1,len(df.index),1):
            row1=np.array(df.iloc[i,:])
            row2=np.array(df.iloc[j,:])
            distance=distance.append({'x': df.index[i], 'y': df.index[j],'value':((row1-row2)**2).sum()}, ignore_index=True)
    
    distance=distance[distance.value<limit].sort_values(by=['value'], axis=0) # 거리 제한
    try:
        for k in range(0,distance.shape[0],1):
            x = distance.loc[distance.value.idxmin()]
            predict[str(int(x.x))]=count
            predict[str(int(x.y))]=count
            count += 1
            distance = distance[distance['x'] != x.x]
            distance = distance[distance['x'] != x.y]
            distance = distance[distance['y'] != x.x]
            distance = distance[distance['y'] != x.y]
    except:
        pass
    return predict

# =======================================================================================
# Compute Angles
# =======================================================================================

for idx, file in enumerate(IMAGE_FILES):
    # img detection & preprocessing
    img = cv2.flip(cv2.imread(file), 1)
    img2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img2)

    # result save
    if result.multi_hand_landmarks is not None:
        for res in result.multi_hand_landmarks:
            joint = np.zeros((21, 3))
            for j, lm in enumerate(res.landmark):
                joint[j] = [lm.x, lm.y, lm.z]

            # Compute angles between joints
            v1 = joint[[0,1,2,3,0,5,6,7,0, 9,10,11, 0,13,14,15, 0,17,18,19],:] # Parent joint
            v2 = joint[[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],:] # Child joint
            v = v2 - v1 # [20,3]

            # Normalize v
            v = v / np.linalg.norm(v, axis=1)[:, np.newaxis]

            # Get angle using arcos of dot product
            angle = np.arccos(np.einsum('nt,nt->n',
                v[[0,5, 9,13],:], 
                v[[3,9,13,17],:]))
            angle2 = np.arccos(np.einsum('nt,nt->n',
                -v[[1,2,4,5,6,8, 9,10,12,13,14,16,17,18],:], 
                v[[2,3,5,6,7,9,10,11,13,14,15,17,18,19],:]))

            angle = np.concatenate((angle, angle2),axis=0)

            # angle = np.degrees(angle) # Convert radian to degree
            angle_data.loc[file.replace('handDetection/model/original_images\\','').replace('.jpg','')] = angle

# =======================================================================================
#%%

thumb_false=angle_data[angle_data['angle0']*180/np.pi<90].iloc[:]
thumb_false.iloc[:,:4] *= 2
predict = fit_predict(thumb_false, limit=1.5)

print(predict)

pca = PCA(n_components=2)
val = pca.fit_transform(thumb_false)
df = pd.DataFrame(val, columns=['x','y'])


plt.title('clustering')
plt.scatter(df.x, df.y,c=predict, cmap='tab20')
plt.colorbar()
plt.show()
