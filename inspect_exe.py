import json
import os
import sys

MARKER = b'<<PROPAGATION_DATA>>'

def inspect_exe(file_path):
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        return

    try:
        with open(file_path, 'rb') as f:
            content = f.read()

        parts = content.split(MARKER)

        print(f"=== 分析文件: {os.path.basename(file_path)} ===")
        print(f"文件大小: {len(content) / 1024 / 1024:.2f} MB")

        if len(parts) == 1:
            print("[-] 未发现传播数据标记 (这是原始生成的 EXE 吗？)")
            return

        print("[+] 发现传播数据标记！")
        print(f"    数据段数量: {len(parts) - 1}")

        last_part = parts[-1]
        try:
            # 尝试清理可能存在的空字节
            json_str = last_part.decode('utf-8', errors='ignore').strip().strip('\0')
            if not json_str:
                print("[-] 数据段为空")
                return

            data = json.loads(json_str)
            print("\n[+] 读取到的传播路径数据:")
            print(json.dumps(data, indent=4, ensure_ascii=False))

        except json.JSONDecodeError:
            print("[-] 数据段不是有效的 JSON 格式")
            print(f"    原始内容片段: {last_part[:100]!r}...")
        except Exception as e:
            print(f"[-] 解析数据时出错: {e}")

    except Exception as e:
        print(f"读取文件失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python inspect_exe.py <exe文件路径>")
        # 方便直接双击运行测试（如果目录下有名为 恶搞.exe 的文件）
        default_exe = "恶搞.exe"
        if os.path.exists(default_exe):
            print(f"\n未指定参数，尝试默认分析当前目录下的: {default_exe}")
            inspect_exe(default_exe)
        else:
            input("\n按回车键退出...")
    else:
        inspect_exe(sys.argv[1])
