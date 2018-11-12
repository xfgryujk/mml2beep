# mml2beep
Converts MML to beep music score. 转换MML乐谱到beep谱

MML(Music Macro Language)是一些在线游戏（如洛奇）的乐谱代码

beep谱指以`[频率, 持续时间]`表示一个音符的乐谱，用于蜂鸣器播放音乐

## 用法
```
usage: mml2beep.py [-h] [-t TRACK] mml_file beep_file

转换MML乐谱到beep谱

positional arguments:
  mml_file              输入的MML文件，格式为txt
  beep_file             输出的beep文件路径，格式为JSON。其中第一个数为频率(Hz)，如果为0则表示延时。第二个数为持续时间(
                        ms)

optional arguments:
  -h, --help            show this help message and exit
  -t TRACK, --track TRACK
                        输出第几个音轨，默认为1
```

## 链接
* [MML语法参考](https://mabinogi.fws.tw/ac_com_annzyral.php)
* [获取MML乐谱](https://mabinogi.fws.tw/ac_comproser.php)
