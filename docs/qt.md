# Qt / qfluentwidgets 机制与实测记录

本页是 `AGENTS.md` 那几条 Qt 规则的**依据**：机制是什么、当时实测到什么。改相关代码前读一遍。

## `@Slot` 到底做什么

实测（PySide6 6.11.2）：

```python
class Demo(QObject):
    @Slot(str, int)
    def decorated(self, a, b): ...
    def plain(self, a, b): ...

Demo.staticMetaObject.methodCount()                      # 5
[mo.method(i).name() for i in range(...)]                # 含 'decorated'，不含 'plain'
```

- `@Slot` 的唯一作用就是**把方法登记进宿主类的元对象**，所以只对 QObject 子类的方法有意义。
- **排队连接（跨线程）靠这份签名做参数转换**——签名写错比不写更糟，错配会让投递失败。
- 在自由函数上装饰它不报错，但拿到的仍是普通函数（没有宿主对象可登记）。入口里的 `apply_autostart` 就是这种情况，别去"补"一个无效装饰。
- 信号转发连接两边都是信号，Qt 自己处理，不需要 `@Slot`。
- 枚举类型是合法参数（`@Slot(ActivationReason)` 实测被接受），不必退化成 `object`。

本项目已有的 `@Slot` 清单（新增时对着抄）：`StatusPage.show_activity(str, int)`、`StatusPage._refresh_idle()`、
`AppWindow.show_and_raise()`、`NotificationService.show(str, str)`、`NotificationService._on_activated(ActivationReason)`、
`InputMonitor.stop()`、`SchedulerWorker.shutdown()`、`GeneralPage._on_autostart_toggled(bool)`。

## 窗口与托盘的生命周期

**默认配置下，关掉最后一个窗口会结束进程。** `quitOnLastWindowClosed` 默认 `True`，实测关窗立刻触发 `aboutToQuit`、`exec()` 返回；而 `QSystemTrayIcon` 不算"窗口"，所以托盘会陪着进程一起消失。入口因此必须写 `app.setQuitOnLastWindowClosed(False)`。

**关窗收起必须显式写 `closeEvent`**（`event.ignore()` + `hide()`）。同一个 `closeEvent`，两个环境行为不同：

| 环境 | 交给 Qt 默认路径点 X | 显式 `closeEvent` |
|---|---|---|
| 开发版（`uv run`） | 窗口隐藏、对象存活、可再唤出 | 收起，可再唤出 |
| 打包版（PyInstaller） | **窗口对象被销毁**：同级窗口与进程都还在，但那个窗口再也唤不回来 | 收起，可再唤出 |

所以"默认路径看起来没问题"在开发版成立、在打包版不成立——只有显式收起才两边一致。

**从托盘唤出要先还原最小化**：实测对被最小化的 `FluentWindow` 调 `show()` / `raise_()` / `activateWindow()`，`isMinimized()` 仍为 `True`、窗口不弹；必须先 `showNormal()`。

## 托盘与系统通知

- `QSystemTrayIcon` 必须 `show()` 出来，否则 `showMessage` 什么都不弹。
- `setContextMenu()` 只挂指针、不做父子关系：菜单必须用属性存引用，否则被回收。
- 通知里显示的应用名来自进程默认的 AppUserModelID：开发态是 "Python"、打包后是 "class-pet.exe"，都不是"课小宠"。要改成中文名得调 `SetCurrentProcessExplicitAppUserModelID`，目前未做。
- 托盘只能用原生 `QSystemTrayIcon` / `QMenu`——qfluentwidgets 没有托盘实现，它的 `RoundMenu` 是窗口内菜单。

## qfluentwidgets 使用细节

- `addSubInterface(interface, ...)` 要求 `interface.objectName()` 非空，否则抛 `ValueError`——新增页面先 `setObjectName(...)`。
- 1.11.3 的控件构造函数只接 `parent`，文本用 `setText()`；网上旧文档里的 `PushButton("确定", self)` 在本版本不成立。
- `QApplication.setHighDpiScaleFactorRoundingPolicy(...)` 必须在构造 `QApplication` **之前**调用，之后调用不生效。
- `import qfluentwidgets` 会向 stdout 打印一行 Pro 版推广横幅，属上游行为，不要屏蔽。
