import csv
import pyopenjtalk 
import re
from g2p_en import G2p

from simstring.feature_extractor.character_ngram import CharacterNgramFeatureExtractor
from simstring.measure.cosine import CosineMeasure
from simstring.database.dict import DictDatabase
from simstring.searcher import Searcher

from sudachipy import tokenizer
from sudachipy import dictionary
import sudachipy

#標準化されたレーベンシュタイン距離を求める関数の定義
import Levenshtein

class Force_override:
    def __init__(self, csvfile_for_dic):
        self.csvfile_for_dic=csvfile_for_dic
        self.g2p=G2p()
        self.empath_dict, self.empath_dbsearcher=self.create_dictionary()
        self.dict = sudachipy.Dictionary() 
        self.tokenizer_obj = self.dict.create(mode=sudachipy.SplitMode.A)
        print(self.empath_dict)
        #print(self.empath_dbsearcher)

    def create_dictionary(self):
        #g2p = G2p() 

        #固有表現リストからオーバーライド用の辞書を作成 (key:音素列, value:正式名称)
        #ex. key : eNpasu, value : Empath
        empath_dict={}

        with open(self.csvfile_for_dic, encoding='utf8', newline='') as f:
            csvreader = csv.reader(f)
            first_row_flag=0 #固有表現リストの1行目を無視するための変数

            for idx, val in enumerate(csvreader):
                #固有表現リストの1行目はラベル行であるため無視する
                if idx !=0:
                    #属性ラベルが"組織名","製品名","その他"を検出 (今回は"人名"や"地名"は使っていない)
                    if val[4]=="組織名" or val[4]=="製品名" or val[4]=="その他":
                        word_phoneme =pyopenjtalk.g2p(val[2]) #振り仮名での音素列を取得
                        word_phoneme_ori =pyopenjtalk.g2p(val[1]) #正式名称での音素列を取得
                        empath_dict[word_phoneme]=val[1]
                        empath_dict[word_phoneme_ori]=val[1]

                        word_en=re.sub('([a-zA-Z])\s+((?=[a-zA-Z]))', r'\1\2', val[1]) #アルファベット単語間のスペースの削除(のちに邪魔になるため)
                        if re.fullmatch('[a-zA-Z]+', word_en):  # アルファベットのみで構成されている単語の検知
                            word_phoneme_en="".join(self.g2p(word_en)) #アルファベット単語用のG2Pモデルの使用
                            empath_dict[word_phoneme_en]=val[1] #アルファベット単語用のG2Pでの音素列を取得


                    #固有表現リストが2段組構成になっているため, 2段目にも上記と同じ処理を行う          
                    if val[10]=="組織名" or val[10]=="製品名" or val[10]=="その他":
                        word_phoneme=pyopenjtalk.g2p(val[8])
                        word_phoneme_ori =pyopenjtalk.g2p(val[7])
                        empath_dict[word_phoneme]=val[7]
                        empath_dict[word_phoneme_ori]=val[7]

                        word_en=re.sub('([a-zA-Z])\s+((?=[a-zA-Z]))', r'\1\2', val[7])
                        if re.fullmatch('[a-zA-Z]+', word_en):  # re.match('^[a-zA-Z]+$', 'deep')
                            word_phoneme_en="".join(self.g2p(word_en))
                            empath_dict[word_phoneme_en]=val[7]

        
        #データベースの作成
        empath_db = DictDatabase(CharacterNgramFeatureExtractor(2))
        #上で作ったempath辞書ベースに、探索用のデータベースを作成
        for key in empath_dict:
            empath_db.add(key)
    
        #データベースの設定
        empath_dbsearcher = Searcher(empath_db, CosineMeasure())

        return empath_dict, empath_dbsearcher
        #Empath辞書の中身の確認
        #ex. key : eNpasu, value : Empath
        #for key, value in empath_dict.items():
        #    print(key, value)
    
    def normalized_distance(self,text0, text1):
        dist = Levenshtein.distance(text0, text1)
        max_len = max(len(text0), len(text1))
        return dist / max_len


        #強制オーバーライドを行う関数
    def force_override(self, text="", simstring_en_threshold=0.4, simstring_ja_threshold=0.9, Levenshtein_en_threshold=0.6, Levenshtein_ja_threshold=0.25):
    
        #英単語間の空白を一度削除する
        text=re.sub('([a-zA-Z])\s+((?=[a-zA-Z]))', r'\1\2', text)
    
        #sudachipyのトークナイザを用いてテキストを形態素で分割する
        tokens = self.tokenizer_obj.tokenize(text)
    

        noun_word_seq="" #名詞列を一時格納するための変数 
        final_replace_word_seq="" #オーバーライド処理における最終候補を格納する変数
        pre_noun_flag=0 #複合名詞に対処するための変数 (分かりにくくてすみません)
        text_override="" #オーバーライド後のテキストの格納する変数

        #各トークンの品詞を確認, 名詞or 名詞列ならオーバーライド処理をかける
        for token in tokens:
            token_word=token.surface() #単語
            token_info=token.part_of_speech()[0] #単語の品詞
            token_info_full=token.part_of_speech() #単語の品詞などの詳細情報
        
            if token_info!="名詞":
                if pre_noun_flag==1:
                    #print("noun_word_seq_確定:",noun_word_seq)
                    #print(pyopenjtalk.g2p(noun_word_seq))

                    replace_text="" #
                    Levenshtein_final_score=0
                    if re.fullmatch('[a-zA-Z]+', noun_word_seq): ##英語のみ
                        noun_phoneme="".join(self.g2p(noun_word_seq))
                        #print("noun_phoneme:",noun_phoneme)
                        results = self.empath_dbsearcher.search(noun_phoneme, simstring_en_threshold)

                        #レーベンシュタイン距離の計算
                        Levenshtein_min=10
                        Levenshtein_min_text=""

                        for noun_result in results:
                            Levenshtein_score=self.normalized_distance(noun_phoneme, noun_result)
                            if Levenshtein_score < Levenshtein_min:
                                Levenshtein_min=Levenshtein_score
                                #print("Levenshtein_min_log:",Levenshtein_min)
                                Levenshtein_min_text=noun_result
                                #print("Levenshtein_min_text_log:",Levenshtein_min_text)
                            
                        if Levenshtein_min < Levenshtein_en_threshold:
                            replace_text=Levenshtein_min_text
                            Levenshtein_final_score=Levenshtein_min
                        

                    else: ##日本語, 数字を含む
                        noun_phoneme=pyopenjtalk.g2p(noun_word_seq)
                        #print("noun_phoneme:",noun_phoneme)
                        results = self.empath_dbsearcher.search(noun_phoneme, simstring_ja_threshold)
                        #print(results)

                        #レーベンシュタイン距離の計算
                        Levenshtein_min=10
                        Levenshtein_min_text=""

                        for noun_result in results:
                            Levenshtein_score=self.normalized_distance(noun_phoneme, noun_result)
                            if Levenshtein_score < Levenshtein_min:
                                Levenshtein_min=Levenshtein_score
                                #print("Levenshtein_min_log:",Levenshtein_min)
                                Levenshtein_min_text=noun_result
                                #print("Levenshtein_min_text_log:",Levenshtein_min_text)

                        if Levenshtein_min < Levenshtein_ja_threshold:
                            replace_text=Levenshtein_min_text
                            Levenshtein_final_score=Levenshtein_min

                
                    #print("noun_seq_確定:",noun_word_seq)
                    #print("置換用単語:",final_replace_text)
                    #print("Levenshtein_final_score:",Levenshtein_min)
                

                    if replace_text !="":
                        #print("置換用単語:",final_replace_text)
                        final_replace_word_seq=self.empath_dict[replace_text]
                        #print("final_replace_sym:",final_replace_text)
                        text_override=text_override+final_replace_word_seq

                    if replace_text=="":
                        #print("null:",noun_word_seq)
                        text_override=text_override+noun_word_seq
                    
                    noun_word_seq=""

                #print("token_sym_名詞以外:",token_sym)
                text_override=text_override+token_word

                pre_noun_flag=0

            elif token_info=="名詞":
                #print("token_sym_名詞:",token_info)
                #print("token_sym_名詞:",token_sym)
                noun_word_seq=noun_word_seq+str(token_word)
                pre_noun_flag=1

        #print(text_override)
        return text_override



        
        




