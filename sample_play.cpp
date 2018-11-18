/*
不推荐在Windows7以及更新版本的Windows系统玩beep音乐
因为Win7以上的Beep是用声卡模拟的(https://msdn.microsoft.com/zh-cn/library/windows/desktop/ms679277(v=vs.85).aspx)
和蜂鸣器声音相差大，而且播放太快会不发声
*/
#include <Windows.h>

struct Note {
    unsigned int frequency;
    unsigned int duration;
};

extern std::vector<Note> notes; // 定义在另一个cpp文件

int main() {
    for (auto [frequency, duration] : notes) {
        if (frequency == 0) // 延时
            Sleep(duration);
        else
            Beep(frequency, duration);
    }

    return 0;
}
