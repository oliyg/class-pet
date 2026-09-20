# HKCU：我们写开机自启动的那棵注册表树

## 它是什么

`HKEY_CURRENT_USER`（缩写 **HKCU**）是 Windows 注册表的根键之一，表示**当前登录用户的那棵注册表树**。

它不是独立存储，而是 `HKEY_USERS\<当前用户 SID>` 的别名。实测方式是从两个路径读同一个值：

```
HKCU\Volatile Environment\USERNAME             = 'YOUNGKONG'
HKEY_USERS\<当前用户 SID>\Volatile Environment\USERNAME = 'YOUNGKONG'
```

两处读到同一个值，说明是同一棵树。实体文件是用户目录下的 `%USERPROFILE%\NTUSER.DAT`，登录时由系统加载。

## 与 HKLM 的区别

|              | HKCU                                     | HKLM（HKEY_LOCAL_MACHINE）          |
| ------------ | ---------------------------------------- | ----------------------------------- |
| 生效范围     | 只对当前用户                             | 全机器、所有用户                    |
| 写权限       | 普通权限即可                             | 需要管理员                          |
| 实体文件     | `%USERPROFILE%\NTUSER.DAT`               | `%SystemRoot%\System32\config\...`  |
| 本项目       | ✅ 只写这里                               | ❌ 不用（会触发 UAC 提权）           |

## 本项目怎么用它

开机自启动只写一个值，实现在 `classpet/self_startup/win32.py`：

```
HKCU\Software\Microsoft\Windows\CurrentVersion\Run
    ClassPet = "C:\...\class-pet.exe" --autostart
```

由此推出的实际含义：

- **不需要管理员权限**，点开关即生效，不弹 UAC。
- **只对开启它的那个 Windows 用户生效**：同一台机器换个用户登录不会自启。对个人桌面助手这是正确行为。
- 归属跟着**当时登录的用户**走——"当前用户"取决于进程运行在谁的登录会话里。
- 系统在**登录时**扫这把键并执行其中的命令，所以值必须是完整可执行路径且带引号（路径可能含空格）。
- 在**任务管理器 → 启动**里能看到这条，名字就是值名 `ClassPet`；用户也可以在那里自行禁用它。
- 卸载 = 删掉这一个值。

同目录下还有个 `RunOnce`：系统执行完就把该条目删掉，只能自启一次。我们要每次登录都起，所以用 `Run`。

## 怎么查看

```bash
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
```

或在 `regedit` 地址栏粘贴 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`。

## 相关

- 自启动功能的行为约定、开关状态的唯一来源、失效检测：见 `AGENTS.md` 的「开机自启动注意点」。
- 面向使用者的操作说明：见 `README.md` 的「开机自启动」。
