# force_override
音素レベルの強制オーバーライドを行うスクリプト

```
from force_override.module import Force_override as fo
a=fo("empath_dict2.csv")
text="えー今日は、森がジャムロルのEmpath reacoderを使ってみます。"
text=a.force_override(text=text)
'''
えー今日は、森がJamRollのEmpath Recoderを使ってみます。
