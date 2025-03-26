# 命令输入窗口
import sys
import win32pipe, win32file
import os

PIPE_NAME = r'\\.\pipe\simulation_command_pipe'

def main():
    os.system("cls")
    print("========= 模拟命令输入窗口 =========")
    print("可在此窗口输入命令，不会被模拟输出干扰")
    print("常用命令：")
    print("  pause - 暂停模拟")
    print("  resume - 继续模拟")
    print("  save - 保存当前模拟状态")
    print("  save <名称> - 保存当前模拟状态到指定名称")
    print("  quit/q - 停止模拟")
    print("  interview <角色名> - 与角色对话")
    print("  whisper <角色名> - 对角色进行whisper")
    print("  order <角色名> <指令内容> <有效时间> - 下达指令")
    print("  action <角色名> <动作内容> <持续时间> - 指定动作")
    print("  whisper load <文件名> - 加载whisper文件")
    print("====================================")
    
    # 连接到命名管道
    try:
        print("正在连接到模拟进程...")
        # 等待管道可用（最多等待10秒）
        for _ in range(10):
            try:
                pipe = win32file.CreateFile(
                    PIPE_NAME,
                    win32file.GENERIC_WRITE,
                    0, None,
                    win32file.OPEN_EXISTING,
                    0, None
                )
                break
            except:
                print("等待连接中...")
                import time
                time.sleep(1)
        else:
            print("无法连接到模拟进程，请确保模拟已启动")
            input("按Enter键退出...")
            return
            
        print("连接成功！可以开始输入命令")
        
        while True:
            command = input(">> ").strip()
            if not command:
                continue
                
            # 发送命令到模拟进程
            win32file.WriteFile(pipe, command.encode('utf-8'))
            
            if command.lower() in ["q", "quit"]:
                print("命令窗口关闭中...")
                break
                
    except Exception as e:
        print(f"错误: {e}")
        input("按Enter键退出...")
    finally:
        try:
            win32file.CloseHandle(pipe)
        except:
            pass
        
if __name__ == "__main__":
    main()
