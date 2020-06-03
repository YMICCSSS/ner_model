# -*- coding: utf-8 -*-
"""HIHI.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/17yKQn6Q00m4vLX0HcsOVuVNcBcPsGx1_
"""

! pip install kashgari
! pip install pandas
! pip install tensorflow==1.15.0

# Commented out IPython magic to ensure Python compatibility.
# %tensorflow_version 1.x

from google.colab import drive
drive.mount("/content/drive", force_remount=True)

import kashgari
from kashgari.tasks.labeling import BiLSTM_CRF_Model
from kashgari.embeddings import BERTEmbedding
import codecs
import csv
import pandas as pd
import ast
# kashgari.config.use_cudnn_cell = True

import os
os.getcwd()
! ls

import zipfile
zfile = zipfile.ZipFile("drive/My Drive/albert.zip")
zfile.extractall("albert")
!ls

#引入問題跟答案
df_sen = pd.read_csv("result_2.csv",encoding="utf-8")

#建立問題與答案list以符合訓練格式
all_ans = []
all_sen = []
aspectTerm_t = []
for i in range(df_sen.shape[0]):
    a = str(df_sen.loc[i, "dish"]).split("?")
    s = str(df_sen.loc[i, "text"])
    # t = str(df_sen.loc[i,"ans"]).split("?")
    one_ans = []
    #  <aspectTerm> : from="4" polarity="positive" term="food" to="8"
    aspectTerm_i = []
    for i in range(len(s)):
        one_ans = one_ans + ["O"]
    # print(s)
    # print(a)
    for j in a:
        try:
            jj = j.split(",")
            j1 = jj[0]
            j2 = jj[1].replace(" a", "positive").replace("a豆干肉絲", "positive").replace("a", "positive").replace("b",
                                                                                                               "neutral").replace(
                "c", "negative")
        except:
            continue
        if j1 in s:
            j1_from = s.index(j1)
            j1_to = s.index(j1) + len(j1)
            aspectTerm_p = [j1, str(j1_from), str(j1_to), j2]
            # print(aspectTerm_p)
            aspectTerm_i = aspectTerm_i + [aspectTerm_p]
            one_ans[j1_from] = "B-1"
            for x in range(len(j1) - 1):
                one_ans[s.index(j1) + x + 1] = "I-1"
    all_ans = all_ans + [one_ans]
    all_sen = all_sen + [s]
    # print(one_ans)

    aspectTerm_t = aspectTerm_t + [aspectTerm_i]

all_sen_1 = []
for all in range(len(all_sen)):
    y=[]
    for i in all_sen[all]:
        y.append(i)
    all_sen_1.append(y)

#all_sen_1 =全部問題,all_ans=全部答案
print(all_sen_1)
print(all_ans)

train_x =all_sen_1[0:2600]
train_y =all_ans[0:2600]
valid_x =all_sen_1[2601:2700]
valid_y =all_ans[2601:2700]
test_x =all_sen_1[2701:2876]
test_y =all_ans[2701:2876]

#設定一層embedding，bert訓練模型會給進去的每一個詞一個index及向量(包含位置向量),每一批次訓練會丟最多128個字進去訓練
#所以輸出最多也128個字
bert_embed = BERTEmbedding('drive/My Drive/robert',
                           task=kashgari.LABELING,
                           sequence_length=128)


from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint,ReduceLROnPlateau
from tensorflow.keras.layers import Flatten, Dense, Dropout
from tensorflow.python import keras

#patience=3是看每一個epoch
stop_callback = EarlyStopping(patience=5, restore_best_weights=True)
# save_callback = ModelCheckpoint("530test1.h5",save_best_only=True,save_weights_only=True)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=3, verbose=1, min_lr=1e-6)


model = BiLSTM_CRF_Model(bert_embed)
model.fit(train_x,
          train_y,
          x_validate=valid_x,
          y_validate=valid_y,
          callbacks=[stop_callback,reduce_lr],
          batch_size=128,
          epochs=50)

# 驗證模型印出 precision、recall、f1
model.evaluate(test_x, test_y)

# 保存模型到 `use_this_model` 目錄下
model.save('ner_model')

# 加載保存模型
loaded_model = kashgari.utils.load_model('ner_model')

# 使用模進行預測
loaded.predict(test_x[0])

import pandas as pd
import kashgari
import re
import glob

#使用這個目錄下的模型
loaded_model = kashgari.utils.load_model('drive/Mydrive/final_model')

#定義函式取得預測的結果
class get_menu:

    def cut_text(text, lenth):
        textArr = re.findall('.{' + str(lenth) + '}', text)
        textArr.append(text[(len(textArr) * lenth):])
        return textArr


    def extract_labels(text, ners):
        ner_reg_list = []
        if ners:
            new_ners = []
            for ner in ners:
                new_ners += ner;
            for word, tag in zip([char for char in text], new_ners):
                if tag != 'O':
                    ner_reg_list.append((word, tag))

# 输出模型的NER识别结果
        labels = {}
        if ner_reg_list:
            for i, item in enumerate(ner_reg_list):
                if item[1].startswith('B'):
                    label = ""
                    end = i + 1
                    while end <= len(ner_reg_list) - 1 and ner_reg_list[end][1].startswith('I'):
                        end += 1

                    ner_type = item[1].split('-')[1]

                    if ner_type not in labels.keys():
                        labels[ner_type] = []

                    label += ''.join([item[0] for item in ner_reg_list[i:end]])
                    labels[ner_type].append(label)

        return labels

#建立一個能讓dataframe中的評論欄位,能預測菜單的函式
def get_name(sentence):

    text_1 = get_menu.cut_text(sentence, 100)
    ners = loaded_model.predict([[char for char in text] for text in text_1])
    labels = get_menu.extract_labels(sentence, ners)
    x = labels.get("1","")
    return ",".join(x)

import time

#取得所有檔案
get_filename = glob.glob("drive/My Drive/all_file/*")
trans = []
print(get_filename)

#轉換檔案加入tag欄位預測菜名
for i in get_filename:
    start = time.time()
    b = i
    a = i.replace("drive/My Drive/all_file/","")
    print(a," 讀取成功")
    df_sen = pd.read_csv(f"{b}",encoding="utf-8")
    print(df_sen.iloc[0:1,:])
    df_sen["tag"] = df_sen["text"].apply(get_name)
    print(df_sen.iloc[0:1,:])
    df_sen.to_csv("add_tag/{}+{}".format("T",a),index= False)
    print("T"+a," 寫入成功")
    end = time.time()
    running_time = (end-start)
    print('time cost : %.5f sec' %running_time)

import glob
import time
import re

#使用這個目錄下的模型
loaded_model = kashgari.utils.load_model('drive/My Drive/rbt3_model')

#定義函式取得預測的結果
class get_dishes:

    global loaded_model

    def __init__(self,df):
        self.D = df

    def cut_text(self,text, lenth):
        textArr = re.findall('.{' + str(lenth) + '}', text)
        textArr.append(text[(len(textArr) * lenth):])
        return textArr


    def extract_labels(self,text, ners):
        ner_reg_list = []
        if ners:
            new_ners = []
            for ner in ners:
                new_ners += ner;
            for word, tag in zip([char for char in text], new_ners):
                if tag != 'O':
                    ner_reg_list.append((word, tag))

# 输出模型的NER识别结果
        labels = {}
        if ner_reg_list:
            for i, item in enumerate(ner_reg_list):
                if item[1].startswith('B'):
                    label = ""
                    end = i + 1
                    while end <= len(ner_reg_list) - 1 and ner_reg_list[end][1].startswith('I'):
                        end += 1

                    ner_type = item[1].split('-')[1]
                    if ner_type not in labels.keys():
                        labels[ner_type] = []

                    label += ''.join([item[0] for item in ner_reg_list[i:end]])
                    labels[ner_type].append(label)

        return labels

#建立一個能讓dataframe中的評論欄位,能預測菜單的函式
    def get_name(self,sentence):

        text_1 = self.cut_text(sentence, 100)
        ners = loaded_model.predict([[char for char in text] for text in text_1])
        labels = self.extract_labels(sentence, ners)
        x = labels.get("1","")
        return ",".join(x)

#新增一個tag欄位，放入預測的菜單
    def Get(self):
        self.D = self.D.drop(["dish"],axis=1)
        self.D["dish"] = self.D["text"].apply(self.get_name)
        self.D = self.D[self.D["dish"].str.len()>0]
        return self.D

df_sen = pd.read_csv("阿文川味熱炒_review.csv",encoding="utf-8")
start = time.time()

data_frame = get_dishes(df_sen)
print(data_frame.Get())

data_frame.Get().to_csv("RoBERTa_阿文")
end = time.time()
running_time = (end-start)
print('time cost : %.5f sec' %running_time)